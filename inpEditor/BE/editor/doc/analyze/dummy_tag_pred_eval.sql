-- =============================================================================
-- tag_pred_eval_l 더미 예측통계 생성 프로시저 (수동 실행용, Flyway 대상 아님)
-- =============================================================================
-- [목적] 「알고리즘 예측 정확도 모니터링」 화면 시연/검증용으로, 지정 구간의
--   예측-실측 페어(tag_pred_eval_l)를 실제 실측값(TB_RAWDATA) 기반으로 채운다.
--
-- [대상 태그] 4종 (유량 FRI / 압력 PRI)
--   701-367-FRI-4004, 701-367-PRI-4019, 701-367-FRI-4001, 701-367-PRI-4010
--
-- [동작] 시작일 00:00 ~ 종료일 23:50 을 10분 간격으로 순회하며, 각 예측시각마다
--   4태그 × 5구간(10M/30M/1H/3H/6H)의 행을 만든다.
--     · actual_avg = 실측 [crt_dttm, pred_dttm] 윈도 평균 (V13 EVENT 과 동일식)
--     · pred_value = actual_avg × (1 + e),  e = (RAND()*2-1) × thr  (실측 기준 ±균등난수)
--       thr(오차 상한): 10M/30M/1H = 0.069(≈7% 미만), 3H/6H = 0.199(≈20% 미만)
--   → 오차지표(abs_err/sq_err/ape/sape)는 tag_pred_eval_l 의 STORED 생성컬럼이
--     actual_avg·pred_value 로부터 자동 계산하므로 여기서는 넣지 않는다.
--       ape = |a-p|/a*100 = |e|*100  이라, 위 thr 이 곧 오차율 상한이 된다.
--
-- [성능 전략 — 경량 스테이징] TB_RAWDATA 가 매우 무거워, 예측시각마다 이 큰 테이블을
--   여러 번(구간별 서브쿼리) 훑으면 느리다. 그래서 각 예측시각에서:
--     (1) 이번 시각에 필요한 '최대 윈도(6H=360분)' 만큼만, 대상 4태그·QUALITY='100'
--         raw 를 경량 테이블 tb_rawdata_eval 로 1회 추출(무거운 TB_RAWDATA 는 이 한 번만 스캔).
--     (2) 구간별 실측 집계 서브쿼리는 소량 스테이징(tb_rawdata_eval)에서만 돈다 → 매우 빠름.
--     (3) 집계 후 스테이징을 비우고 다음 예측시각으로.
--   TB_RAWDATA 접근이 '예측시각당 1회'로 줄어드는 게 핵심.
--
-- [규약]
--   · duration_cd 는 파이썬 예측모듈 SSOT 코드값(10M/30M/1H/3H/6H)을 그대로 쓴다.
--     (BE 조회 필터 PredictionDuration.MONITORED 와 일치해야 화면에 표출됨)
--   · actual_avg 가 NULL(윈도에 유효 raw 없음)인 예측점은 건너뛴다(pred_value 는 NOT NULL).
--   · UNIQUE(tag_no, pred_dttm, duration_cd) 충돌 시 INSERT IGNORE 로 기존행 유지.
--
-- [선행 조건] 스테이징 테이블 tb_rawdata_eval 이 존재해야 한다(사용자 생성 완료).
--   프로시저는 최소한 아래 컬럼을 사용한다: TAGNAME, TS, VALUE.
--   빠른 서브쿼리를 위해 인덱스 (TAGNAME, TS) 를 권장한다. 참고 정의:
--     CREATE TABLE IF NOT EXISTS tb_rawdata_eval (
--         TAGNAME VARCHAR(255) NOT NULL,
--         TS      DATETIME     NOT NULL,
--         VALUE   VARCHAR(255) NULL,
--         PRIMARY KEY (TAGNAME, TS)
--     );
--
-- [사용법]
--   CALL sp_fill_tag_pred_eval_dummy('2026-06-01', '2026-06-30');
-- =============================================================================

DROP PROCEDURE IF EXISTS sp_fill_tag_pred_eval_dummy;

DELIMITER $$

CREATE PROCEDURE sp_fill_tag_pred_eval_dummy(
    IN p_start_date VARCHAR(10),   -- 시작일 'YYYY-MM-DD'
    IN p_end_date   VARCHAR(10)    -- 종료일 'YYYY-MM-DD' (해당일 23:50 까지 포함)
)
BEGIN
    DECLARE v_ts  DATETIME;        -- 현재 예측시각(pred_dttm), 10분씩 전진
    DECLARE v_end DATETIME;        -- 순회 종료 경계(종료일 23:50:00)

    -- [락 회피] 격리수준을 READ COMMITTED 로 낮춰 INSERT IGNORE 의 UNIQUE 갭락
    --   경합을 줄인다(같은 테이블에 쓰는 EVENT ev_tag_pred_eval 과의 대기 완화).
    SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
    -- [락 회피] 자동커밋을 켜서, 아래 루프의 각 배치가 독립 트랜잭션으로 즉시 커밋되게
    --   한다(호출 클라이언트가 수동커밋이어도 트랜잭션이 루프 전체로 커지지 않음).
    SET autocommit = 1;

    -- 문자열 일자 → 경계 시각. 시작일 00:00 ~ 종료일 23:50(마지막 10분 슬롯).
    SET v_ts  = CAST(CONCAT(p_start_date, ' 00:00:00') AS DATETIME);
    SET v_end = CAST(CONCAT(p_end_date,   ' 23:50:00') AS DATETIME);

    -- 이전 실행 잔여물 정리(클린 스타트).
    DELETE FROM tb_rawdata_eval;

    WHILE v_ts <= v_end DO
        -- (1) 이번 예측시각의 최대 윈도(6H=360분) 만큼만 대상 4태그·QUALITY='100' raw 를
        --     경량 스테이징으로 추출. 무거운 TB_RAWDATA 는 이 1회 범위스캔만 탄다.
        INSERT INTO tb_rawdata_eval (TAGNAME, TS, VALUE)
        SELECT r.TAGNAME, r.TS, r.VALUE
          FROM TB_RAWDATA r
         WHERE r.TAGNAME IN ('701-367-FRI-4004', '701-367-PRI-4019',
                             '701-367-FRI-4001', '701-367-PRI-4010')
           AND r.TS >= (v_ts - INTERVAL 360 MINUTE)   -- 6H = 가장 긴 구간 윈도 시작
           AND r.TS <= v_ts
           AND r.QUALITY = '100';

        -- (2) 스테이징(tb_rawdata_eval)에서 구간별 실측 집계를 서브쿼리로 계산해 적재.
        --     4태그 × 5구간 = 20행. 소량 테이블이라 서브쿼리가 매우 빠르다.
        INSERT IGNORE INTO tag_pred_eval_l
(
    tag_no,
    pred_dttm,
    duration_cd,
    crt_dttm,
    pred_value,
    actual_avg,
    sample_cnt,
    eval_dttm
)
SELECT
    t.tag_no,
    v_ts AS pred_dttm,
    d.code AS duration_cd,
    DATE_SUB(v_ts, INTERVAL d.mins MINUTE) AS crt_dttm,

    ROUND(
        AVG(CAST(e.`VALUE` AS DECIMAL(18, 4)))
        * (1 + (RAND() * 2 - 1) * d.thr),
        4
    ) AS pred_value,

    AVG(CAST(e.`VALUE` AS DECIMAL(18, 4))) AS actual_avg,

    COUNT(e.TAGNAME) AS sample_cnt,

    NOW(6) AS eval_dttm

FROM (
              SELECT '701-367-FRI-4004' AS tag_no
    UNION ALL SELECT '701-367-PRI-4019'
    UNION ALL SELECT '701-367-FRI-4001'
    UNION ALL SELECT '701-367-PRI-4010'
) AS t

CROSS JOIN (
              SELECT '10M' AS code,  10 AS mins, 0.069 AS thr
    UNION ALL SELECT '30M',          30,         0.069
    UNION ALL SELECT '1H',           60,         0.069
    UNION ALL SELECT '3H',          180,         0.199
    UNION ALL SELECT '6H',          360,         0.199
) AS d

INNER JOIN tb_rawdata_eval AS e
        ON e.TAGNAME = t.tag_no
       AND e.TS >= DATE_SUB(v_ts, INTERVAL d.mins MINUTE)
       AND e.TS <= v_ts

GROUP BY
    t.tag_no,
    d.code,
    d.mins,
    d.thr;   -- 실측 없는 예측점은 skip

        -- (3) 스테이징 비우기(다음 예측시각에서 다시 채운다).
        DELETE FROM tb_rawdata_eval;

        -- [락 회피] 이번 배치 확정(autocommit 이면 no-op, 수동커밋 클라이언트에선 안전망).
        COMMIT;

        SET v_ts = v_ts + INTERVAL 10 MINUTE;
    END WHILE;
END $$

DELIMITER ;

-- =============================================================================
-- [성능 참고]
-- =============================================================================
-- · 스테이징 tb_rawdata_eval 에 인덱스 (TAGNAME, TS) 가 있으면 (2) 서브쿼리가
--   인덱스 스캔이 된다(행 수가 적어 없어도 무방하지만 권장).
-- · (1) 추출은 TB_RAWDATA 를 예측시각당 1회, TS 범위 360분 + TAGNAME IN(4) 로 읽는다.
--   TB_RAWDATA 에 인덱스 (TAGNAME, TS) 가 있으면 이 추출도 인덱스 레인지 스캔이 되어
--   더 빨라진다(선택). 없으면 TS 범위 PK 스캔으로 동작(그래도 '예측시각당 1회'라 이전보다 개선).
--     CREATE INDEX idx_rawdata_tag_ts ON TB_RAWDATA (TAGNAME, TS);   -- 공유 테이블, 선택
--
-- [테스트 팁] 처음엔 하루만 돌려 소요시간·결과를 확인한 뒤 전체 구간을 돌린다.
--   CALL sp_fill_tag_pred_eval_dummy('2026-06-01', '2026-06-01');
--
-- [검증 예시] 구간별 오차율 상한이 지켜졌는지 확인:
--   SELECT duration_cd, COUNT(*) n, ROUND(MAX(ape),3) max_ape, ROUND(AVG(ape),3) avg_ape
--     FROM tag_pred_eval_l
--    WHERE tag_no IN ('701-367-FRI-4004','701-367-PRI-4019','701-367-FRI-4001','701-367-PRI-4010')
--    GROUP BY duration_cd;   -- 10M/30M/1H max_ape<7, 3H/6H max_ape<20 이면 정상
-- =============================================================================
