-- =============================================================================
-- 군산 5분 제어 판단 → 제어명령 연계 (EMS 공유 DB)
--
-- 설계 : docs/gunsan-ctrl-workflow.html (15장 현장 반영 절차)
-- 코드 : be/.../pump/CtrlCmdService.java, sqlmapper/mysql/ctrl_cmd_mssql.xml
--
-- 구성
--   1. TB_CTRL_CMD_TRACE  : 우리 소유 추적 테이블 (DDL)
--   2. TB_WPP_TAG_CODE    : 밸브 제어 태그 행 (빈 값으로 생성)
--   3. 현장 반영 UPDATE   : 태그 확인 후 값을 채운다 (주석 해제해 실행)
--      켜기·끄기는 화면의 AI 운전모드(FUNC_TYP='PumpStatus')로 한다
--   4. 확인 쿼리
--
-- 실행 : 1·2 는 멱등하다. 배포 시 한 번 실행한다.
--        3 은 현장에서 태그를 확인한 뒤에만 실행한다.
--        벤더 테이블(TB_CTRL_CMD_RST, TB_CTRL_RULE_CFG)은 벤더 소유라 여기서 만들지 않는다.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. 추적 테이블
--    적재·승인·거절·만료·반영·실패 판정마다 1행. 벤더 테이블에 처리자·처리시각이 없어 따로 둔다.
--    이 테이블이 없어도 제어 흐름은 멈추지 않는다(추적 기록만 실패 로그).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS TB_CTRL_CMD_TRACE (
    TRACE_ID   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '추적 고유번호',
    CTRL_ID    BIGINT UNSIGNED NOT NULL                COMMENT 'TB_CTRL_CMD_RST.CTRL_ID',
    DEVICE     VARCHAR(20)     NOT NULL                COMMENT 'PUMP / NATIONAL / LOCAL',
    ACTION     VARCHAR(20)     NOT NULL                COMMENT 'ENQUEUE / APPROVE / REJECT / EXPIRE / APPLY / FAIL',
    REASON     VARCHAR(50)     DEFAULT NULL            COMMENT '게이트·처리 사유 코드',
    TGT_VALUE  DECIMAL(6,2)    DEFAULT NULL            COMMENT '판단 목표값(Hz 또는 %)',
    USER_ID    VARCHAR(50)     DEFAULT NULL            COMMENT '승인·거절한 사용자',
    DETAIL     VARCHAR(500)    DEFAULT NULL            COMMENT '적재 태그·값, 되읽기 값 등',
    TS         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '기록 시각',
    PRIMARY KEY (TRACE_ID),
    KEY IDX_CTRL_CMD_TRACE_CTRL (CTRL_ID),
    KEY IDX_CTRL_CMD_TRACE_TS (TS)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='군산 5분 제어 판단 처리 추적';


-- -----------------------------------------------------------------------------
-- 2. 밸브 제어 태그 (TB_WPP_TAG_CODE)
--    TB_WPP_TAG_CODE 는 기본키가 없으므로 NOT EXISTS 로 중복 생성을 막는다.
--    TAG_DSC 가 키다.
--      NATIONAL_OPEN        TAG = 목표 개도 설정 태그   891-365-POC-8603
--      NATIONAL_PULSE       TAG = OPENC 펄스 태그(상향) 891-365-VVK-8606
--      NATIONAL_CLOSE_PULSE TAG = CLOSEC 펄스 태그(하향) 891-365-VVK-8607
--      LOCAL_OPEN           TAG = 지방산단 목표 개도 설정   891-365-POC-8602  (2026-09-30 확정)
--      LOCAL_PULSE          TAG = 지방산단 OPENC 펄스(상향) 891-365-VVK-8601
--      LOCAL_CLOSE_PULSE    TAG = 지방산단 CLOSEC 펄스(하향) 891-365-VVK-8602
--    지방산단 밸브는 2026-09-30 벤더 드롭(main_5min.py)에서 나운 고수위 최종(fallback) 제어로 부활했고
--    같은 날 제어 대상으로 확정했다. 송신 방식은 국가산단과 같다.
--    송신 순서: 목표 개도 → (목표 > 현재 이면 OPENC, 작으면 CLOSEC) 1 → 3초 → 0
--    펌프 주파수 쓰기 태그는 기존 TB_CTR_PRF_PUMPMST_INF.CTR_AUTO_FREQ_TAG 를 쓴다.
--    운전·추천·분석은 AI 운전모드(FUNC_TYP='PumpStatus') 하나로 정한다. 장치별 스위치는 없다.
-- -----------------------------------------------------------------------------
INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, DISPLAY_ID, DISPLAY_NM, TAG_GRP, TAG, TAG_KOR_NM, TAG_UNIT, TAG_DSC, DEFAULT_VALUE)
SELECT 'GSSCADA', 'CtrlCmdTag', NULL, NULL, '1', NULL, '국가산단 밸브 개도 설정', '%', 'NATIONAL_OPEN', NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'NATIONAL_OPEN');

INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, DISPLAY_ID, DISPLAY_NM, TAG_GRP, TAG, TAG_KOR_NM, TAG_UNIT, TAG_DSC, DEFAULT_VALUE)
SELECT 'GSSCADA', 'CtrlCmdTag', NULL, NULL, '1', NULL, '국가산단 밸브 OPENC 펄스(상향)', NULL, 'NATIONAL_PULSE', NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'NATIONAL_PULSE');

INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, DISPLAY_ID, DISPLAY_NM, TAG_GRP, TAG, TAG_KOR_NM, TAG_UNIT, TAG_DSC, DEFAULT_VALUE)
SELECT 'GSSCADA', 'CtrlCmdTag', NULL, NULL, '1', NULL, '국가산단 밸브 CLOSEC 펄스(하향)', NULL, 'NATIONAL_CLOSE_PULSE', NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'NATIONAL_CLOSE_PULSE');

INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, DISPLAY_ID, DISPLAY_NM, TAG_GRP, TAG, TAG_KOR_NM, TAG_UNIT, TAG_DSC, DEFAULT_VALUE)
SELECT 'GSSCADA', 'CtrlCmdTag', NULL, NULL, '1', NULL, '지방산단 밸브 개도 설정', '%', 'LOCAL_OPEN', NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'LOCAL_OPEN');

INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, DISPLAY_ID, DISPLAY_NM, TAG_GRP, TAG, TAG_KOR_NM, TAG_UNIT, TAG_DSC, DEFAULT_VALUE)
SELECT 'GSSCADA', 'CtrlCmdTag', NULL, NULL, '1', NULL, '지방산단 밸브 OPENC 펄스(상향)', NULL, 'LOCAL_PULSE', NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'LOCAL_PULSE');

INSERT INTO TB_WPP_TAG_CODE (WPP_CODE, FUNC_TYP, DISPLAY_ID, DISPLAY_NM, TAG_GRP, TAG, TAG_KOR_NM, TAG_UNIT, TAG_DSC, DEFAULT_VALUE)
SELECT 'GSSCADA', 'CtrlCmdTag', NULL, NULL, '1', NULL, '지방산단 밸브 CLOSEC 펄스(하향)', NULL, 'LOCAL_CLOSE_PULSE', NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'LOCAL_CLOSE_PULSE');


-- -----------------------------------------------------------------------------
-- 3. 현장 반영 (태그 확인 후 주석을 풀고 실행)
--    태그는 기존 마스터처럼 'Fix32.GSSCADA.' 접두와 '.F_CV' 접미를 뺀 형태로 넣는다.
--    기존 FREQ 송신 이력(4-b)의 TAG 형식과 같아야 한다.
-- -----------------------------------------------------------------------------
-- 펌프 주파수 쓰기 태그가 틀린 경우에만
-- UPDATE TB_CTR_PRF_PUMPMST_INF SET CTR_AUTO_FREQ_TAG = '<태그>' WHERE PUMP_GRP = 1 AND PUMP_IDX = 1;

-- 국가산단 밸브 태그 (2026-09-30 확정). CLOSEC 가 비어 있으면 하향 명령만 TAG_NOT_CONFIGURED 로 거절된다.
-- UPDATE TB_WPP_TAG_CODE SET TAG = '891-365-POC-8603' WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'NATIONAL_OPEN';
-- UPDATE TB_WPP_TAG_CODE SET TAG = '891-365-VVK-8606' WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'NATIONAL_PULSE';
-- UPDATE TB_WPP_TAG_CODE SET TAG = '891-365-VVK-8607' WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'NATIONAL_CLOSE_PULSE';

-- 지방산단 밸브 태그 (2026-09-30 확정). 세 행이 다 있어야 상향·하향 모두 송신된다.
-- UPDATE TB_WPP_TAG_CODE SET TAG = '891-365-POC-8602' WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'LOCAL_OPEN';
-- UPDATE TB_WPP_TAG_CODE SET TAG = '891-365-VVK-8601' WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'LOCAL_PULSE';
-- UPDATE TB_WPP_TAG_CODE SET TAG = '891-365-VVK-8602' WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC = 'LOCAL_CLOSE_PULSE';

-- 2026-09-30 벤더 드롭(main_5min.py) 선행 조건. 규칙 키 8개와 컬럼 5개가 없으면 Python 이 매 사이클 실패한다.
-- SELECT PARAM_KEY, VALUE_NUM FROM TB_CTRL_RULE_CFG WHERE PARAM_KEY LIKE 'LOCAL_%' ORDER BY PARAM_KEY;
--   → LOCAL_VALVE_MIN, LOCAL_VALVE_MAX, LOCAL_VALVE_STEP, LOCAL_VALVE_OBSERVE_MIN,
--     LOCAL_TRIGGER_LEVEL, LOCAL_FORCE_CLOSE_LEVEL, LOCAL_RECOVERY_LEVEL, LOCAL_RECOVERY_STABLE_MIN (8행)
-- SHOW COLUMNS FROM TB_CTRL_CMD_RST LIKE 'LOCAL_%';      -- 5행 (섀도우 TB_CTRL_CMD_RST_SH 도 같이)

-- 운전·추천·분석 전환은 화면의 AI 운전모드 토글로 한다 (TB_WPP_TAG_CODE FUNC_TYP='PumpStatus', 0 AI / 1 AI 추천 / 2 AI 분석).
-- 현장 확인은 추천(1)에서 1건씩 승인한 뒤 운전(0)으로 바꾼다. 멈출 때는 분석(2)으로 바꾼다.


-- -----------------------------------------------------------------------------
-- 4. 확인 쿼리
-- -----------------------------------------------------------------------------
-- (a) 밸브 제어 태그와 AI 운전모드
SELECT TAG_DSC, TAG, TAG_KOR_NM FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'CtrlCmdTag' ORDER BY TAG_DSC;
SELECT TAG_GRP, DEFAULT_VALUE AS AI_MODE FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'PumpStatus';

-- (b) 펌프 주파수 쓰기 태그와 기존 FREQ 송신 이력의 태그 형식
SELECT PUMP_IDX, PUMP_NM, PMB_TAG, SPI_TAG, CTR_AUTO_FREQ_TAG, USE_YN FROM TB_CTR_PRF_PUMPMST_INF WHERE PUMP_GRP = 1 ORDER BY PUMP_IDX;
SELECT TIME, TAG, VALUE, ANLY_CD, FLAG FROM TB_HMI_CTR_LOG WHERE ANLY_CD = 'FREQ' AND TAG <> 'DEBUG' ORDER BY TIME DESC LIMIT 10;

-- (c) 모드·테스트모드 (PumpStatus 0 운전 / 1 추천 / 2 분석)
SELECT FUNC_TYP, TAG_GRP, DEFAULT_VALUE FROM TB_WPP_TAG_CODE WHERE FUNC_TYP IN ('PumpStatus', 'TestMode', 'CtrTestMode');

-- (d) 최근 판단과 처리 상태
SELECT CTRL_ID, CTRL_TS, PUMP_COMB, PUMP_CMD_YN, PUMP_CMD_STATUS, PUMP_CUR_HZ, PUMP_TGT_HZ,
       NATIONAL_CMD_YN, NATIONAL_CMD_STATUS, NATIONAL_CUR_OPEN, NATIONAL_TGT_OPEN,
       LOCAL_CMD_YN, LOCAL_CMD_STATUS, LOCAL_CUR_OPEN, LOCAL_TGT_OPEN, REASON_CODE
FROM TB_CTRL_CMD_RST ORDER BY CTRL_TS DESC LIMIT 12;

-- (e) 대기열과 추적
SELECT CTR_IDX, CTR_NM, OPT_IDX, TAG, VALUE, ANLY_CD, FLAG, UPDT_TIME FROM TB_HMI_CTR_TAG WHERE OPT_IDX LIKE 'CTRL:%' ORDER BY CTR_IDX DESC LIMIT 20;
SELECT * FROM TB_CTRL_CMD_TRACE ORDER BY TRACE_ID DESC LIMIT 20;
