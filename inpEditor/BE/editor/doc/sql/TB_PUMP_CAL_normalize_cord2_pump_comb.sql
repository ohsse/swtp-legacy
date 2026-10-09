-- ############################################################################
-- ## 실행 금지 — 이 스크립트의 전제가 틀렸다. 아래 [정정] 을 반드시 읽을 것.  ##
-- ############################################################################
--
-- [정정] C_ORD=2 행의 PUMP_COMB 은 "잔재 값" 이 아니라 **가변속 펌프의 목표 주파수 조합** 이다.
--   레거시 EMS DrvnService.getPumpCombCal 이 그렇게 읽는다
--   (be/src/main/java/kr/co/mindone/ems/drvn/DrvnService.java 의 c_ord != 1 분기:
--    "TB_PUMP_CAL 의 C_ORD=2 행(주파수 조합)은 미입력 시 빈 문자열이다").
--   주파수 값은 조합에 든 모든 펌프가 아니라 가변속(TB_CTR_PRF_PUMPMST_INF.PUMP_TYP=2) 펌프에만
--   순서대로 대응하며, 정속 펌프는 자리를 차지하지 않는다.
--
--   아래 원본 배경 설명이 근거로 든 군산 개발 DB 실측값 '27,27' · '29,29' · '31,31' 도
--   펌프IDX 가 아니라 27Hz · 29Hz · 31Hz 로 읽는 것이 정합적이다.
--
-- [영향] 이 UPDATE 를 돌리면 펌프 성능곡선 산출이 쓰는 주파수 입력이 사라진다.
--   inp-opt 파이썬의 군산 엔진(pump_curve_update_gunsan.py)은 이 주파수로 회귀 대상 구간을
--   걸러내며, 값이 없으면 주파수 조건 없이(= 서로 다른 주파수의 운전점이 섞인 채) 회귀한다.
--   곡선이 뭉개지지만 에러는 나지 않으므로 결과 숫자만 보고는 알아채기 어렵다.
--   BE 조립 경로: PumpCombStatRepository.buildPumpHz → pumpHz → 파이썬 pumpHz 파라미터.
--
-- [그래서 남은 일] C_ORD=2 의 PUMP_COMB 은 지우지 않는다. 아래 UPDATE 는 주석 처리해 둔다.
--   실제 잔재(주파수로 해석되지 않는 값)가 있는지는 조회 쿼리로 확인하되, 정리는 현장의
--   가변속 펌프 구성과 대조한 뒤에만 개별적으로 판단한다.
--
-- ---------------------------------------------------------------------------
-- 이하 원본 기록 (판단 근거가 틀렸음이 확인되어 보존만 한다)
-- ---------------------------------------------------------------------------
-- [원본 배경] 한 조합(PUMP_GRP, C_IDX)은 C_ORD=1(유량 하한)·C_ORD=2(유량 상한) 두 행으로 구성되며,
--   펌프조합 문자열(PUMP_COMB)은 C_ORD=1 행만 갖는 것이 규칙이다.
--   그러나 레거시 데이터의 C_ORD=2 행에는 펌프IDX 가 아닌 잔재 값이 남아 있다
--   (군산 개발 DB 실측: '27,27', '29,29', '31,31', ... — 실제 펌프는 2·3번뿐).
--   → 이 관찰은 맞지만 해석이 틀렸다. 위 [정정] 참조.
--
-- [원본 안전성 주장] 레거시 EMS 자율제어(DrvnConfig)는 c_ord == 1 일 때만 PUMP_COMB 을 읽고,
--   EPA 파이썬(epa_models.fetch_fc_range_by_comb)은 PUMP_COMB 으로 검색하되 C_ORD 순으로 정렬해
--   C_ORD=1 행을 우선 취한다.
--   → DrvnService(자율제어 조합 목록)와 성능곡선 산출 경로를 빠뜨린 주장이다.

-- 현재 값 확인 (지우지 말고 내용만 본다)
SELECT PUMP_GRP, C_IDX, C_ORD, PUMP_COMB
FROM TB_PUMP_CAL
WHERE C_ORD = '2' AND PUMP_COMB <> ''
ORDER BY PUMP_GRP, C_IDX;

-- 조합의 가변속 펌프 구성과 대조 (주파수 개수가 가변속 펌프 수와 맞는지 본다)
SELECT c1.PUMP_GRP, c1.C_IDX, c1.PUMP_COMB AS pump_comb, c2.PUMP_COMB AS freq_comb
FROM TB_PUMP_CAL c1
JOIN TB_PUMP_CAL c2
  ON c2.PUMP_GRP = c1.PUMP_GRP AND c2.C_IDX = c1.C_IDX AND c2.C_ORD = '2'
WHERE c1.C_ORD = '1' AND c1.USE_YN = 1
ORDER BY c1.PUMP_GRP, c1.C_IDX;

SELECT PUMP_IDX, PUMP_NM, PUMP_TYP   -- PUMP_TYP: 1=정속, 2=가변속
FROM TB_CTR_PRF_PUMPMST_INF
WHERE USE_YN = 1
ORDER BY PUMP_IDX;

-- ############################################################################
-- ## 아래 정리 쿼리는 주파수 데이터를 삭제한다. 실행하지 말 것.                ##
-- ############################################################################
-- UPDATE TB_PUMP_CAL
--    SET PUMP_COMB = ''
--  WHERE C_ORD = '2'
--    AND PUMP_COMB <> '';
