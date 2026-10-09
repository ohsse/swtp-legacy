# 군산 해석 엔진이 DB 에서 읽는 것

해석이 더미를 넣고도 실패할 때, 또는 엔진 코드가 바뀌어 스크립트를 고쳐야 할 때 읽는다.
라인 번호는 작성 시점(2026-09-28) 기준이다. 어긋나면 함수명으로 찾는다.

## MO — 5분 모니터링 (`epa/epanet_gunsan/epanet_mo_gs.py`)

- 호출: `epa/app/scheduler.py` (cron `*/5` 분 `:30` 초, `SCHEDULER_ENABLED` 가 켜져 있어야 함)
  → `epa_service_gunsan.run_mo_simulation` → `main(["--snapshot", "--ts", floor5(now), ...])`
- 읽는 테이블: **`TB_RAWDATA` 하나** (`fetch_readings`).
  `TS ∈ [T − fallback, T]` 에서 태그별 `MAX(TS)` 행 1개. 과거 이력은 필요 없다.
- 태그 목록: `all_tags()` = `NODE_META` + `LINK_META` + `PUMPS` + `VALVE_META` (코드 하드코딩).
- 필수 (`validate_inputs`): 수요 5개(`FRI-8851`, `FRI-8802`, `FRI-8600`, `FRI-8652`, `740-914-FRI-1001`),
  가동 4개(`PMB-4017/4022/4027/4032`), 운전 중인 펌프의 주파수 `SPI-4000~4003`(1~60Hz).
  `valve-mode=opening` 이면 `POI-8601`(0 이거나 11.07~51.43), `POI-8600`(0~100).
- 선택: 압력 11개·유량 7개. 없으면 `[WARN]` 만 남고 결과의 비교값이 빈다.
- 함정: 태그의 **최신 행**이 숫자가 아니면 그 태그는 "없음"이 된다. 이전 정상값으로 대체하지 않는다.
- fallback: CLI 기본 600초, dev 설정(`epa/config.gunsan.py`) 86400초, 운영 600초.
- 결과: `TB_FP_SI_VAL`(14노드) / `TB_FR_SI_VAL`(6관로) / `TB_TOT_ALG`(1행), 모두 `FLG='mo'`.
  로그 `epa/epanet_gunsan/logs/mo_YYYYMMDD.txt`.

## PRE — 수요예측 기반 해석 (`epa/epanet_gunsan/main_epa_gs.py`)

- 운영에서는 compose 서비스 `ems-epa-pre` 가 루프로 돈다. **dev 서버 compose 에는 없다.**
- `TB_NODE_TAG` (`load_prediction_mapping`): `PREDICTION_NODE_IDS = ("나운(배)", "오식도(배)공업")`
  각각에 `DSTRB_Q_ID` 정확히 1개. 루프 시작 시 없으면 프로세스가 죽는다.
- `TB_CTR_TNK_RST` (`fetch_prediction_bundle`): DSTRB_ID 별 최신 1행(snapshot 이면 `RGSTR_TIME <= ts`).
  `PRDCT_VALUE` ≥0 유한값, 두 행의 RGSTR_TIME 차 ≤120초. 루프 모드는 추가로 두 행 모두 이번 5분
  경계 이후에 생성돼야 한다.
- `TB_RAWDATA` (`runtime_tags`): 함열 `740-914-FRI-1001`, PMB 4개, 운전 펌프 SPI, `POI-8601`, `POI-8600`.
  기준시각은 예측 묶음의 `batch_ts`, 창 600초.
- 루프 모드 저장 조건 (`verify_mo_source`, `copy_mo_to_cur`): 같은 5분 경계의 MO 결과
  (`TB_TOT_ALG`·`TB_FP_SI_VAL`·`TB_FR_SI_VAL` 의 `FLG='mo'`)가 있어야 한다.
  → `--snapshot --ts ... --no-save-db` 는 이 조건을 보지 않는다.
- 결과: `TB_FP_VAL`/`TB_FR_VAL`/`TB_TOT_ALG` `FLG='PRE'`(전 노드·전 관로), 그리고 MO 복사본 `FLG='CUR'`.

## 테이블 형태

- `TB_RAWDATA(TS timestamp, TAGNAME varchar(45), VALUE varchar(45), QUALITY varchar(3), SERVER varchar(45))`
  PK `(TS, TAGNAME)`, 보조 인덱스 `(TAGNAME, TS)`, 월 단위 RANGE 파티션. (`docs/tag-ingestion-pipeline.md`)
- `TB_CTR_TNK_RST(DSTRB_ID, RGSTR_TIME, PRDCT_VALUE, VALUE_5min … VALUE_6h)` PK `(DSTRB_ID, RGSTR_TIME)`.
  (`ems_gu_predict/readme.txt`) 운영에서는 `ems_gu_predict` 가 5분마다 `REPLACE INTO` 한다.
- `TB_NODE_TAG` 시드: `docs/sql/gunsan_ems_tag_seed.sql`.

## 범위 밖

- SI(화면 버튼 해석)는 `TB_EPA_SIM_RESV_FLOW`(5개 노드의 FLOW_RATE, UPDT_TIME 기준 창)를 읽는다.
  화면에서 값을 저장하면 채워지므로 이 스킬은 건드리지 않는다. SI 가 쓰는 `TB_RAWDATA` 태그는 채워진다.
- `epa/epanet_gunsan/main_5min.py` 는 해석이 아니라 제어 판단 코드다(`TB_CTRL_RULE_CFG`, `TB_RT_RATE_INF` 등).
