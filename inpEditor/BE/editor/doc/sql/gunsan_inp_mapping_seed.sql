-- =============================================================================
-- 군산 INP 분기점 매핑 시드 (inpEditor DB)
--
-- 출처 : docs/군산_epanet_분기점 추가.xlsx
-- 대상 : inp_vis_mapping   (결과 비교표/result_snap 표시용)
--        inp_anal_mapping  (GA 조도계수 최적화의 관측점 + 수요 주입점)
--
-- 전제 : 군산 INP 에서 배수지 4곳(나운(배)/오식도(배)공업/군장에너지/28)이
--        RESERVOIR -> JUNCTION 으로 변경된 리비전을 사용한다.
--        (RESERVOIR 인 채로는 apply_demand_overrides() 가 조용히 skip 한다)
--
-- 실행 : 전 구문이 ON DUPLICATE KEY UPDATE 로 멱등하다. 반복 실행해도 안전하다.
--        DDL 변경 없음 — 스키마 SSOT 는 Flyway(V4/V6/V9/V10/V11)다.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 0. 대상 INP 파일 확정
--    배수지 -> 절점 변경본의 마스터 ID 를 넣는다.
-- -----------------------------------------------------------------------------
-- SELECT inp_file_id, orgnl_file_nm, curr_rev_no, mdf_dttm
--   FROM inp_file_m ORDER BY mdf_dttm DESC;

SET @INP_FILE_ID = 'fb324b31-f3a2-4e96-97df-106b38cf6c75';  -- ← 위 조회 결과로 교체할 것


-- =============================================================================
-- ⚠ 반드시 알고 넘어가야 할 제약
--
--   군산 INP 는 절점 ID 와 링크 ID 가 같은 숫자를 공유한다.
--     pipe 67  = 45 -> 28        이므로 "45" 는 절점이면서 관로다
--     pipe 140 = 88 -> 옥석      이므로 "88" 은 절점이면서 관로다
--     "62", "16" 도 마찬가지
--
--   inp_anal_mapping 은 node_id 컬럼 하나로만 대상을 식별한다.
--   따라서 시트2의 유량 관로(45/62/88/103/16/Bks-1984)를 이 테이블에
--   data_type='FLOW' 로 넣으면, apply_demand_overrides() 가 관로가 아니라
--   같은 이름의 절점을 찾아 수요량을 덮어쓴다.
--
--   → 유량 관로는 inp_vis_mapping(과 EMS 쪽 TB_LINK_GRP)에만 넣는다.
--     inp_anal_mapping 의 FLOW 는 배수지/가압장 5곳 전용이다.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. inp_vis_mapping — 표시/비교용 지점 9건 (엑셀 시트2)
--
--    pipe_id 가 NOT NULL 이라, 유량태그가 없는 지점(개정/신관/옥석)도
--    인접 유입관을 넣어 해석유량만이라도 표시되게 한다.
--    UNIQUE(inp_file_id, junction_id) 로 중복이 차단된다.
--
--    내초도(pipe 103, Bkj-1460 -> 56) 만 유출관이고 나머지는 유입관이다.
--    비교표에서 유량 부호가 반대로 보이면 이 때문이다.
-- -----------------------------------------------------------------------------
INSERT INTO inp_vis_mapping
  (inp_file_id, junction_id, pipe_id, flow_tag_no, pressure_tag_no, point_nm,
   sort_ord, disp_yn, rgst_dttm, mdf_dttm)
VALUES
  (@INP_FILE_ID, 'Bks-2496', '45',       '891-365-FRI-8950', '891-365-PRI-4000', '군산(정)', 1, 'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '개정',     '74',       NULL,               '891-365-PRI-8700', '개정',     2, 'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '덕암',     '62',       '891-365-FRI-8850', '701-367-PRI-9322', '덕암',     3, 'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '국가산단', '88',       '891-365-FRI-8602', '891-365-PRI-8601', '국가산단', 4, 'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '군산관말', 'Bks-1984', '891-365-FRI-8800', '891-365-PRI-8800', '군산관말', 5, 'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, 'Bkj-1460', '103',      '891-365-FRI-8303', '891-365-PRI-8301', '내초도',   6, 'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '신관',     'Bkj-1900', NULL,               '701-367-PRI-9160', '신관',     7, 'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '옥석',     '140',      NULL,               '701-367-PRI-9300', '옥석',     8, 'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '14',       '16',       '891-365-FRI-9010', '891-365-PRI-9010', '최호장군', 9, 'Y', NOW(6), NOW(6))
ON DUPLICATE KEY UPDATE
  pipe_id         = VALUES(pipe_id),
  flow_tag_no     = VALUES(flow_tag_no),
  pressure_tag_no = VALUES(pressure_tag_no),
  point_nm        = VALUES(point_nm),
  sort_ord        = VALUES(sort_ord),
  disp_yn         = VALUES(disp_yn),
  mdf_dttm        = NOW(6);


-- -----------------------------------------------------------------------------
-- 2. inp_anal_mapping — GA 분석 매핑 14건
--
--    PRESSURE 9건 : GA 적합도(RMSE)의 비교 대상.
--                   load_analysis_pressure_points_from_option_snap() 이 읽는다.
--    FLOW     5건 : 절점 수요량 주입값.
--                   load_demand_points_from_option_snap() → apply_demand_overrides()
--
--    UNIQUE(inp_file_id, node_id, data_type) 로 중복이 차단된다.
--    anal_yn='N' 으로 두면 해당 지점만 GA 에서 제외된다(행 삭제 불필요).
-- -----------------------------------------------------------------------------
INSERT INTO inp_anal_mapping
  (inp_file_id, node_id, tag_no, data_type, anal_yn, rgst_dttm, mdf_dttm)
VALUES
  -- PRESSURE : GA 적합도 비교 대상 (9점)
  (@INP_FILE_ID, 'Bks-2496',       '891-365-PRI-4000',    'PRESSURE', 'Y', NOW(6), NOW(6)),  -- 군산(정) 송수 메인 토출
  (@INP_FILE_ID, '개정',           '891-365-PRI-8700',    'PRESSURE', 'Y', NOW(6), NOW(6)),  -- 개정 분기
  (@INP_FILE_ID, '덕암',           '701-367-PRI-9322',    'PRESSURE', 'Y', NOW(6), NOW(6)),  -- 덕암(분) 전단
  (@INP_FILE_ID, '국가산단',       '891-365-PRI-8601',    'PRESSURE', 'Y', NOW(6), NOW(6)),  -- 국가산단분기 전단
  (@INP_FILE_ID, '군산관말',       '891-365-PRI-8800',    'PRESSURE', 'Y', NOW(6), NOW(6)),  -- 군산관말
  (@INP_FILE_ID, 'Bkj-1460',       '891-365-PRI-8301',    'PRESSURE', 'Y', NOW(6), NOW(6)),  -- 내초도분기 공업
  (@INP_FILE_ID, '신관',           '701-367-PRI-9160',    'PRESSURE', 'Y', NOW(6), NOW(6)),  -- 신관(분) 전단
  (@INP_FILE_ID, '옥석',           '701-367-PRI-9300',    'PRESSURE', 'Y', NOW(6), NOW(6)),  -- 옥석#2(분) 전단
  (@INP_FILE_ID, '14',             '891-365-PRI-9010',    'PRESSURE', 'Y', NOW(6), NOW(6)),  -- 최호장군(공) 전단
  -- FLOW : 절점 수요 주입 (5점) — 배수지 -> 절점 변경 반영
  (@INP_FILE_ID, '함열가압장',     '740-914-FRI-1001', 'FLOW',     'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '28',             '891-365-FRI-8851',    'FLOW',     'Y', NOW(6), NOW(6)),  -- 장항배수지
  (@INP_FILE_ID, '오식도(배)공업', '891-365-FRI-8652',    'FLOW',     'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '군장에너지',     '891-365-FRI-8802',    'FLOW',     'Y', NOW(6), NOW(6)),
  (@INP_FILE_ID, '나운(배)',       '891-365-FRI-8601',    'FLOW',     'Y', NOW(6), NOW(6))
ON DUPLICATE KEY UPDATE
  tag_no   = VALUES(tag_no),
  anal_yn  = VALUES(anal_yn),
  mdf_dttm = NOW(6);


-- -----------------------------------------------------------------------------
-- 3. 적용 후 확인
-- -----------------------------------------------------------------------------
-- SELECT * FROM inp_vis_mapping  WHERE inp_file_id = @INP_FILE_ID ORDER BY sort_ord;
-- SELECT data_type, COUNT(*) FROM inp_anal_mapping
--   WHERE inp_file_id = @INP_FILE_ID GROUP BY data_type;   -- PRESSURE 9 / FLOW 5
--
-- GA 1회 실행(GET http://<py>:30092/optimize/{histId}) 후 로그에서
--   demand_override_nodes_not_found  → 비어 있어야 한다
--                                      (비어 있지 않으면 해당 노드가 아직
--                                       RESERVOIR 이거나 INP 에 없다는 뜻)
--   observation 개수                 → 9 여야 한다
--                                      (적으면 TB_RAWDATA 에 fallback_sec(600초)
--                                       내 값이 없는 태그가 있다는 뜻)
