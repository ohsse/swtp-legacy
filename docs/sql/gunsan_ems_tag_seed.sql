-- =============================================================================
-- 군산 EPANET 분기점/배수지 태그 매핑 시드 (EMS 공유 DB)
--
-- 출처 : docs/군산_epanet_분기점 추가.xlsx
-- 대상 : 관망해석 시뮬레이션(epa/ Flask)과 inpEditor 분기점 표가 함께 쓰는
--        EMS 공유 테이블 4종
--          TB_EPA_TAG_INFO       : 화면 표시 지점(분기점/정수장)
--          TB_NODE_TAG           : 절점별 압력태그(FP) / 수요유량태그(FR)
--                                  + PRE 관망해석용 수요예측ID(DSTRB_Q_ID, 2-1절)
--          TB_LINK_GRP           : 관로별 유량태그
--          TB_EPA_SIM_RESV_FLOW  : 배수지 수요량 설정 목록
--
-- 전제 : 군산 INP 에서 배수지 4곳(나운(배)/오식도(배)공업/군장에너지/28)이
--        RESERVOIR -> JUNCTION 으로 변경된 리비전을 사용한다.
--
-- 실행 : 전 구문이 ON DUPLICATE KEY UPDATE 로 멱등하다. 반복 실행해도 안전하다.
--        DDL 변경은 없다.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 0. 선행 확인 (실행 전 눈으로 확인할 것)
-- -----------------------------------------------------------------------------
-- (a) TB_LINK_GRP.GRP_NM 에 쓸 그룹 코드가 TB_AVL_GRP 에 존재하는지.
--     compute_group_loss_total() 이 TB_AVL_GRP 의 GRP_{그룹명}_YN 컬럼을 보고
--     손실 합산 대상을 고르므로, 아래 DML 의 A 가 실제 컬럼과 맞아야 한다.
--         SELECT * FROM TB_AVL_GRP LIMIT 5;
--         SHOW COLUMNS FROM TB_AVL_GRP;
--
-- (b) 아래 절점/관로 ID 가 현재 INP 에 실재하는지.
--     특히 나운(배)/오식도(배)공업/군장에너지/28 이 [RESERVOIRS] 가 아니라
--     [JUNCTIONS] 에 있어야 수요량 주입이 동작한다.


-- -----------------------------------------------------------------------------
-- 1. TB_EPA_TAG_INFO  — 표시 지점 9건 (엑셀 시트2 "모니터링. 분기점, 정수장")
--
--    PIPE_ID 는 유량태그가 없는 지점(개정/신관/옥석)에도 인접 유입관을 넣어
--    실측유량은 비고 해석유량은 표시되도록 한다.
--    내초도(103) 만 유출관이고 나머지는 유입관이다 — 유량 부호 해석 시 주의.
-- -----------------------------------------------------------------------------
INSERT INTO TB_EPA_TAG_INFO
  (LOCATION_NM, JUNCTION_ID, PIPE_ID, PRI_TAG, FRI_TAG, DISPLAY_ORDER, IS_DISPLAY)
VALUES
  -- 정수장
  ('군산(정)',   'Bks-2496',  '45',       '891-365-PRI-4000', '891-365-FRI-8950', 1, 1),
  -- 분기점
  ('개정',       '개정',      '74',       '891-365-PRI-8700', NULL,               2, 1),
  ('덕암',       '덕암',      '62',       '701-367-PRI-9322', '891-365-FRI-8850', 3, 1),
  ('국가산단',   '국가산단',  '88',       '891-365-PRI-8601', '891-365-FRI-8602', 4, 1),
  ('군산관말',   '군산관말',  'Bks-1984', '891-365-PRI-8800', '891-365-FRI-8800', 5, 1),
  ('내초도',     'Bkj-1460',  '103',      '891-365-PRI-8301', '891-365-FRI-8303', 6, 1),
  ('신관',       '신관',      'Bkj-1900', '701-367-PRI-9160', NULL,               7, 1),
  ('옥석',       '옥석',      '140',      '701-367-PRI-9300', NULL,               8, 1),
  ('최호장군',   '14',        '16',       '891-365-PRI-9010', '891-365-FRI-9010', 9, 1)
ON DUPLICATE KEY UPDATE
  JUNCTION_ID   = VALUES(JUNCTION_ID),
  PIPE_ID       = VALUES(PIPE_ID),
  PRI_TAG       = VALUES(PRI_TAG),
  FRI_TAG       = VALUES(FRI_TAG),
  DISPLAY_ORDER = VALUES(DISPLAY_ORDER),
  IS_DISPLAY    = VALUES(IS_DISPLAY);


-- -----------------------------------------------------------------------------
-- 2. TB_NODE_TAG  — 절점 태그 14건
--
--    FP_TAGNAME : 해석압력과 나란히 저장할 실측 압력 태그 (시트2)
--    FR_TAGNAME : build_demands_from_rawdata() / build_demands_merged() 의
--                 수요량 입력 태그 (시트1 두 번째 표)
--    두 용도가 겹치는 절점은 없으므로 각각 한쪽만 채운다.
--    UPDATE 절에 COALESCE 를 쓰는 이유: 이미 반대쪽 태그가 들어 있는 행을
--    NULL 로 덮어쓰지 않기 위함.
-- -----------------------------------------------------------------------------
INSERT INTO TB_NODE_TAG (NODE_ID, FP_TAGNAME, FR_TAGNAME) VALUES
  -- 압력 모니터링 (시트2)
  ('Bks-2496',       '891-365-PRI-4000', NULL),   -- 군산(정) 송수 메인 토출 압력
  ('개정',           '891-365-PRI-8700', NULL),   -- 군산(정) 개정 압력
  ('덕암',           '701-367-PRI-9322', NULL),   -- 덕암(분) 전단압력(공업)
  ('국가산단',       '891-365-PRI-8601', NULL),   -- 국가산단분기 1200mm 전단압력
  ('군산관말',       '891-365-PRI-8800', NULL),   -- 군산(정) 군산관말 압력
  ('Bkj-1460',       '891-365-PRI-8301', NULL),   -- 내초도분기 공업 압력
  ('신관',           '701-367-PRI-9160', NULL),   -- 신관(분) 전단압력(공업)
  ('옥석',           '701-367-PRI-9300', NULL),   -- 옥석#2(분) 전단압력(공업)
  ('14',             '891-365-PRI-9010', NULL),   -- 최호장군(공) 전단압력
  -- 수요량 입력 (시트1 두 번째 표) — 배수지 -> 절점 변경분 포함
  ('함열가압장',     NULL, '740-914-FRI-1001'), -- 함열가압장 유량
  ('28',             NULL, '891-365-FRI-8851'),    -- 장항산단관말 유량순시
  ('오식도(배)공업', NULL, '891-365-FRI-8652'),    -- 오식도(배) 공업 유입유량
  ('군장에너지',     NULL, '891-365-FRI-8802'),    -- 군장에너지 순시유량(국산-관말)
  ('나운(배)',       NULL, '891-365-FRI-8601')     -- 지방산단 유량 순시(통신)
ON DUPLICATE KEY UPDATE
  FP_TAGNAME = COALESCE(VALUES(FP_TAGNAME), FP_TAGNAME),
  FR_TAGNAME = COALESCE(VALUES(FR_TAGNAME), FR_TAGNAME);


-- -----------------------------------------------------------------------------
-- 2-1. TB_NODE_TAG.DSTRB_Q_ID  — PRE 관망해석 수요예측 매핑 2건
--
--    위 2절(FP/FR)은 "실측" 태그다. 이건 "예측" 연계라 용도가 달라 문장을 나눈다.
--    epa/epanet_gunsan/main_epa_gs.py 의 load_prediction_mapping() 이 읽는다:
--      NODE_ID -> DSTRB_Q_ID -> TB_CTR_TNK_RST.DSTRB_ID -> PRDCT_VALUE
--    이 값이 비어 있으면 PRE 루프가 기동 직후 "나운(배): DSTRB_Q_ID 없음" 으로
--    죽는다. 노드당 정확히 1건이어야 하며(중복도 예외), 대상 노드는
--    main_epa_gs.py:158 의 PREDICTION_NODE_IDS 가 정한다.
--
--    값의 출처는 ems_gu_predict 의 업로드 규칙 "{var_name}_Predict" 이다
--    (scripts/harness/upload.py). 태그↔변수명 대응은
--    ems_gu_predict/taglist/GU_network_topology.md 의 "지점별 태그 목록" 표.
--
--    ※ 배수지가 RESERVOIR -> JUNCTION 으로 바뀐 모델이라(위 선행확인 (b)),
--      그 절점의 "수요"는 배수지로 들어가는 유량이다. 그래서 오식도는
--      유출(O7)이 아니라 유입(Q7) 을 쓴다 — 위 2절의 FR_TAGNAME(FRI-8652)과도 일치.
--
--    ※ [확인 필요] 나운(배) 의 FR_TAGNAME 은 891-365-FRI-8601 인데 예측 쪽
--      taglist 에는 이 태그가 없다. 설명이 같은("지방산단 유량") 891-365-FRI-8600
--      = Q2 를 대용으로 연결한다. 관망 구조상으로도 지방산단 -> 나운배수지라
--      타당하지만, 두 태그가 같은 지점인지는 현장 확인 전까지 미확정이다.
--      다른 지점으로 밝혀지면 나운 일대 압력 해석이 통째로 틀어진다.
-- -----------------------------------------------------------------------------
INSERT INTO TB_NODE_TAG (NODE_ID, DSTRB_Q_ID) VALUES
  ('오식도(배)공업', 'Q7_Predict'),   -- 오식도배수지 유입유량 (FRI-8652)
  ('나운(배)',       'Q2_Predict')    -- 지방산단 유량 (FRI-8600) — 위 확인 필요 참고
ON DUPLICATE KEY UPDATE
  DSTRB_Q_ID = VALUES(DSTRB_Q_ID);


-- -----------------------------------------------------------------------------
-- 3. TB_LINK_GRP  — 관로 유량태그 6건 (시트2 유량 표)
--
--    PK 가 (LINK_ID, GRP_NM) 이라 GRP_NM 이 필수다.
--    ※ 군산 그룹 체계가 아직 정해지지 않아 임시로 'A' 를 쓴다.
--      선행 확인 (a) 에서 TB_AVL_GRP 의 실제 그룹 코드를 확인한 뒤,
--      필요하면 아래 'A' 를 일괄 치환할 것.
-- -----------------------------------------------------------------------------
INSERT INTO TB_LINK_GRP (LINK_ID, GRP_NM, FLW_TAGNAME) VALUES
  ('45',       'A', '891-365-FRI-8950'),   -- 군산(정) 송수 유량
  ('62',       'A', '891-365-FRI-8850'),   -- 장항산단 유출 유량순시
  ('88',       'A', '891-365-FRI-8602'),   -- 국가산단분기 1200mm 순시유량
  ('Bks-1984', 'A', '891-365-FRI-8800'),   -- 군산(정) 군산관말 유량
  ('103',      'A', '891-365-FRI-8303'),   -- 내초도분기 공업 순시유량(통신)
  ('16',       'A', '891-365-FRI-9010')    -- 최호장군(공) 유량(통신)
ON DUPLICATE KEY UPDATE
  FLW_TAGNAME = VALUES(FLW_TAGNAME);


-- -----------------------------------------------------------------------------
-- 4. TB_EPA_SIM_RESV_FLOW  — 배수지 수요량 설정 목록 5건 (시트1 두 번째 표)
--
--    화면(MultiInflowModal.vue)에서 사용자가 입력하는 값이며,
--    si 해석에서 build_demands_merged() 가 TB_RAWDATA 보다 우선 적용한다.
--    초기값 FLOW_RATE = 0 으로 두고 /api/web/updateRate 로 실측을 채운다.
--    (컬럼 기본값은 1000 이지만, 임의 유량으로 해석이 도는 것을 막기 위해 0 을 명시)
-- -----------------------------------------------------------------------------
INSERT INTO TB_EPA_SIM_RESV_FLOW (NODE_ID, INFLOW_TAG, TNK_NM, FLOW_RATE, DISPLAY_ORDER) VALUES
  ('나운(배)',       '891-365-FRI-8601',    '나운배수지',   0, 1),
  ('오식도(배)공업', '891-365-FRI-8652',    '오식도배수지', 0, 2),
  ('28',             '891-365-FRI-8851',    '장항배수지',   0, 3),
  ('군장에너지',     '891-365-FRI-8802',    '군장에너지',   0, 4),
  ('함열가압장',     '740-914-FRI-1001', '함열가압장',   0, 5)
ON DUPLICATE KEY UPDATE
  INFLOW_TAG    = VALUES(INFLOW_TAG),
  TNK_NM        = VALUES(TNK_NM),
  DISPLAY_ORDER = VALUES(DISPLAY_ORDER);
  -- FLOW_RATE 는 화면에서 갱신되는 운영값이므로 재실행 시 덮어쓰지 않는다.


-- -----------------------------------------------------------------------------
-- 5. 적용 후 확인
-- -----------------------------------------------------------------------------
-- SELECT * FROM TB_EPA_TAG_INFO      ORDER BY DISPLAY_ORDER;
-- SELECT * FROM TB_NODE_TAG          WHERE FP_TAGNAME IS NOT NULL OR FR_TAGNAME IS NOT NULL;
-- SELECT NODE_ID, DSTRB_Q_ID FROM TB_NODE_TAG WHERE DSTRB_Q_ID IS NOT NULL;  -- PRE 매핑 2건
-- SELECT * FROM TB_LINK_GRP          WHERE FLW_TAGNAME IS NOT NULL;
-- SELECT * FROM TB_EPA_SIM_RESV_FLOW ORDER BY DISPLAY_ORDER;
--
-- si 해석 1회 실행 후 실측값이 붙었는지:
-- SELECT * FROM TB_FP_SI_VAL WHERE FLG='si'
--   AND NODE_ID IN ('Bks-2496','개정','덕암','국가산단','군산관말','Bkj-1460','신관','옥석','14');
-- SELECT * FROM TB_FR_SI_VAL WHERE FLG='si'
--   AND LINK_ID IN ('45','62','88','Bks-1984','103','16');
-- -> FP_VAL / LINK_VAL(실측)이 NULL 이나 0 이 아니어야 매핑이 붙은 것이다.


-- -----------------------------------------------------------------------------
-- 6. 이 스크립트에 넣지 않은 것 (코드 변경이 필요해 별도 처리)
-- -----------------------------------------------------------------------------
-- epa/config.gunsan.py 의 TOT_* 3개 값이 아직 고산(701-367-*) 기준이다.
-- TB_TOT_ALG 저장에 쓰이며, 군산 후보는 아래와 같으나 TOT_NODE_ID(통합 대표 절점)
-- 의 정의를 확인한 뒤 반영해야 한다.
--     TOT_NODE_ID        = "Bks-2496"           # 군산(정) 송수 메인 토출
--     TOT_SUM_FLOW_TAGS  = "891-365-FRI-8950"   # 군산(정) 송수 유량
--     TOT_SUM_PRESS_TAGS = "891-365-PRI-4000"   # 군산(정) 송수 메인 토출 압력
