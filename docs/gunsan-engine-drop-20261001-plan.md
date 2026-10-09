# 군산 엔진 2026-10-01 벤더 드롭(main_5min.py · main_epa_gs.py) — 무엇이 바뀌었고 어떻게 적용하나

- 대상: `epa/epanet_gunsan/main_5min.py`(5분 제어 판단), `epa/epanet_gunsan/main_epa_gs.py`(PRE 관망해석)
- 드롭 시각: 2026-10-01 11:23 / 11:24 (작업 사본 수정 시각). 커밋 전 상태(`git status` M 2건)
- 기준 HEAD: `b0af26f` (main_epa_gs 직전 재적용 `docs/gunsan-predict-1min-drop-review.md` §9.4, main_5min 직전 재적용 `docs/gunsan-ctrl-5min-drop-review.md`)
- 계획(§6)은 2026-10-01 오후 사용자 지시("운영 테이블 컬럼은 추가해 놨다. 대문자·스케줄링 적용하고 테스트 없이 착수, 끝나면 운영 반출본")로 착수했다. 적용 결과는 §8.
- 모든 라인 번호는 드롭 작업 사본 기준. HEAD 라인은 `HEAD:` 로 표기.

---

## 1. 결론 요약

1. **두 파일은 한 묶음이다.** main_5min 의 새 펌프 Hz 결정(EPA 모드)이 main_epa_gs 가 새로 쓰는 `_1MIN/_5MIN/_15MIN/_30MIN` 컬럼을 읽는다. 하나만 올리면 EPA 모드는 매 사이클 펌프 HOLD.
2. **DB 선행조건이 새로 생겼다 — 결과 테이블 3개에 컬럼 20개.** `TB_FP_VAL` 4개, `TB_FR_VAL` 8개, `TB_TOT_ALG` 8개. 리포 어디에도 DDL 이 없다. 섀도우 `_SH` 테이블도 같다. 컬럼 없이 올리면 PRE 저장 INSERT 가 매 회차 실패한다.
3. **우리 수정은 전부 되돌아갔다(예상대로).** main_epa_gs 는 메모리 체크리스트 1·2·4·5·6 + 함열 `SS.` 태그, main_5min 은 7번(섀도우 테이블 옵션). 그대로 반출하면 **운영 `ems-pre`·섀도우 PRE·섀도우 `ems-ctrl` 셋이 인자 오류로 기동 실패**한다.
4. **5·6번은 HEAD 코드를 그대로 못 붙인다.** `run_once` 가 horizon 4회 루프로, `save_results_db` 가 wide INSERT 3종으로 바뀌었다. 드롭 구조 위에 다시 얹어야 한다(§6 단계 3).
5. **벤더 코드에 실질 버그 하나 — 고쳤다.** `TB_PUMP_CAL` 조회가 `WHERE USE_YN = 'Y'` 인데 컬럼은 `int(1)` 이다(§4.1). MariaDB 가 `'Y'`→0 으로 캐스팅해 비활성 곡선만 뽑거나 0건 → 성능곡선 매칭 실패 → 펌프 HOLD. 사용자가 2026-10-01 "int 가 맞고 1 로 들어가야 한다" 고 확정해 `main_5min.py:487` 을 `USE_YN = 1` 로 바꿨다. 벤더 드롭마다 되돌아올 항목이라 메모리 체크리스트에 올렸다.
6. **Q/P 산정 실패는 전부 삼켜져 WARNING 한 줄 + HOLD 다**(§4.3). 선행조건이 빠져도 오류로 죽지 않아 "조용히 펌프 미제어" 가 된다. 적용 뒤 첫 사이클 로그에서 `PUMP_QP_SOURCE_CHECK` 가 없는지 꼭 봐야 한다.

---

## 2. 새로 들어온 것

### 2.1 main_epa_gs.py — PRE 다중 horizon(1/5/15/30분) 해석

| 항목 | 위치 | 내용 |
|---|---|---|
| horizon 상수 | `:128-135` | `PREDICTION_HORIZONS=(1,5,15,30)`, 컬럼 후보 `VALUE_1MIN`(없으면 `PRDCT_VALUE`)·`VALUE_5MIN`·`VALUE_15MIN`·`VALUE_30MIN` |
| 수요예측 읽기 | `:634-664`, `:667-760` | `SELECT *` 로 바뀜(HEAD 는 명시 컬럼). 행에 horizon 별 값을 붙인다. **네 컬럼 중 하나라도 없거나 NULL 이면 묶음 전체 "not ready" → 그 회차 SKIP** (`:710-715`) |
| 해석 | `:1076`, `:1847-2075` | horizon 마다 INP 로드·펌프/밸브 설정·EPANET 실행을 반복(4회). 회차 소요시간 약 4배 |
| 결과 병합 | `:1566-1610` | NODE/LINK 별 wide 한 행. legacy 컬럼(`FP_ALG_RST_VAL`·`HH_LOSS_VAL`·`FLW_ALG_RST_VAL`·`HH_LOSS_VAL_TOT`)에는 **1분 결과** |
| 저장 | `:1613-1700` | `INSERT IGNORE` → `INSERT … ON DUPLICATE KEY UPDATE`. 같은 `RGSTR_TIME` 재실행 시 덮어쓴다(기존은 무시). 시그니처 `save_results_db(conn, node_rows, link_rows, total_row, *, cur_source_ts, cur_target_ts)` |
| MO 원본 선택 | `:787-850` | `latest_complete_mo_source_ts` · `--mo-max-age-min` **유지**(로직 동일, 테이블명만 소문자화) |
| CUR 복사 | `:868-930` | 로직 동일(테이블명 소문자화 · `result_table()` 제거만) |
| 모듈 docstring | HEAD `:3-53` | 전부 삭제됨. 운영 메모(슬롯·DB 정책)가 코드에서 사라짐 |
| 출력 라벨 | 여러 곳 | `[PREDICT {h}m]`·`[RESULT +{h}m]`·`[OK] PRE 1/5/15/30분 DB 저장 완료` |

입력 쪽은 맞는다: 우리 수요예측 `ems_gu_predict/scripts/harness/upload.py:32,121` 가 `VALUE_1min/5min/15min/30min` 을 REPLACE INTO 한다. 단, 운영 DB `TB_CTR_TNK_RST` 에 `VALUE_1min`·`VALUE_15min` 컬럼이 실제로 있는지는 **미확정**(§7-(1)). 배포 README 의 DDL(`deploy/gunsan/README.md:122`)에는 둘이 없고, 개발 덤프 스냅샷(`.idea/dataSources/…xml`, 2026-09-22)에도 `PRDCT_VALUE` 만 있다.

### 2.2 main_5min.py — 펌프 Hz 결정을 "수위 방향" 에서 "Q/P 성능곡선 매칭" 으로

| 항목 | 위치 | 내용 |
|---|---|---|
| Q/P 출처 스위치 | `:584-603` | `TB_WPP_TAG_CODE.FUNC_TYP='EPA_PUMP'` 의 `DEFAULT_VALUE`. 0=AI(`TB_CTR_TNK_RST` 의 `Q_GunS_Predict`/`P_GunS_Predict` 행), 1=EPANET PRE. 없거나 0/1 외면 RuntimeError. 이 행은 BE 관망분석 모드 토글(`epa_mssql.xml:12,20`)이 쓰는 것과 같아 운영에 존재한다 |
| AI 경로 | `:604-631` | `VALUE_1MIN`(없으면 `PRDCT_VALUE`)·`VALUE_5MIN`·`VALUE_15MIN`·`VALUE_30MIN` 읽기(대소문자 무시). 값 None/0 이하면 RuntimeError |
| EPA 경로 | `:634-690` | `TB_TOT_ALG.FP_ALG_RST_VAL_{h}MIN` + `TB_FR_VAL.FLW_ALG_RST_VAL_{h}MIN`(**`LINK_ID='45'` 하드코딩** `:28`). `[ctrl_ts, ctrl_ts+5분)` 의 최신 PRE 1건, `0 ≤ delay < 5분` 아니면 RuntimeError. 직전 회차 PRE 재사용 안 함 |
| 단위 환산 규칙 | `:243-244` | `EPA_Q_SCALE`·`EPA_P_SCALE`(기본 1.0, setdefault 라 없어도 무해) |
| 성능곡선 후보 | `:476-500` | `TB_PUMP_CAL` 에서 `avg_error_rate, data_count` 포함 SELECT, **`WHERE USE_YN = 'Y'`** (§4.1) |
| Base Hz | `:1641-1720` | 5분 Q/P 를 곡선 201점 샘플과 정규화 유클리드 거리로 매칭 → 가장 가까운 조합의 Hz. 현재 Hz 와 0.5Hz 불감대(`hz_direction` `:717`) |
| 방향 지속성 | 같은 블록 | 1/15/30분 Q/P 로 검증. 2개 이상 반대 → `PUMP_HORIZON_REVERSAL_HOLD`, 2개 이상 동의 → `CONFIRMED`, 그 외 `MIXED`(fine step) |
| 수위 피드백 | `:1704-1715` | 나운·오식도 동방향이면 `PUMP_COARSE_STEP` 가산. 둘 다 위험수위면 예측 무시, 수위 방향 우선(`PUMP_RESERVOIR_DANGER_OVERRIDE`) |
| step 적용 | `:1926` | `applied_step = min(step, remaining)` — Base 까지 남은 차이만 |
| 국가산단 축소 | `:1729-1743` | 분기 안 "나운 위험이면 펌프도 올림" 삭제, else 분기 펌프 결정 삭제 |
| 응답 확인 | `:726-745` | 수위 피드백·override 때만 기존 `response_ok_for_pump`, 그 외 새 `response_ok_for_pump_base`(송수유량이 명령 방향으로 변했는가) |
| 실행 오프셋 | `:2318-2330`, `:2359-2364` | `--schedule-offset-min`(0~4, **기본 2**). 루프가 `:02/:07/…` 에 돈다. CTRL_TS 는 여전히 :00 기준 |
| 사유 JSON | `:2200-2207` | `pump_source_mode/pump_source/pump_source_ts/pump_reference_hz/pump_horizon_hold/pump_qp{1,5,15,30}` 추가. INSERT 컬럼 자체는 불변 |
| 새 사유코드 | — | `PUMP_SRC_AI/EPA`, `PUMP_HORIZON_REVERSAL_HOLD/CONFIRMED/MIXED`, `PUMP_QP_SOURCE_CHECK`, `PUMP_RESERVOIR_DANGER_OVERRIDE` → BE 사유 한글 사전 확장 대상(§5.3) |

지방산단 fallback(`LOCAL_*` 50건)·오식도 유량수지는 2026-09-30 드롭과 동일하게 유지됐다.

### 2.3 선행조건 정리

| # | 대상 | 필요한 것 | 없으면 |
|---|---|---|---|
| P1 | `TB_FP_VAL` | `FP_ALG_RST_VAL_1MIN/_5MIN/_15MIN/_30MIN` | PRE 저장 INSERT 실패(매 회차) |
| P2 | `TB_FR_VAL` | `HH_LOSS_VAL_{h}MIN` 4 + `FLW_ALG_RST_VAL_{h}MIN` 4 | 같음 |
| P3 | `TB_TOT_ALG` | `HH_LOSS_VAL_TOT_{h}MIN` 4 + `FP_ALG_RST_VAL_{h}MIN` 4 | 같음 |
| P4 | `TB_FP_VAL_SH`·`TB_FR_VAL_SH`·`TB_TOT_ALG_SH` | P1~P3 동일 | 섀도우 PRE 저장 실패 |
| P5 | `TB_CTR_TNK_RST`(및 `_SH`) | `VALUE_1min`·`VALUE_5min`·`VALUE_15min`·`VALUE_30min` | PRE 매 회차 SKIP, 5min AI 모드 매 사이클 HOLD |
| P6 | `TB_PUMP_CAL` | `avg_error_rate`, `data_count` 컬럼 | 5min SQL 오류 → HOLD. 개발 덤프 스냅샷엔 있음(`.idea/dataSources` id 753·757) |
| P7 | `TB_WPP_TAG_CODE` | `FUNC_TYP='EPA_PUMP'` 1행, 값 0 또는 1 | 5min RuntimeError → HOLD. BE 토글이 쓰는 행이라 있을 것 |
| P8 | `TB_PUMP_CAL.USE_YN` 비교 | ~~`'Y'` vs `int(1)` 불일치~~ **해소**: `main_5min.py:487` 을 `= 1` 로 수정(사용자 확정 2026-10-01) | (수정 전) 곡선 0건 또는 비활성만 → HOLD |

DDL(P1~P5)은 전부 **벤더에 요청**한다(타입·기본값·인덱스는 벤더 설계). 우리가 추측해 ALTER 하지 않는다. P8 은 코드 쪽 수정으로 끝났고, 벤더에는 "USE_YN 은 int, 다음 드롭부터 `= 1` 로" 를 전달한다.

---

## 3. 되돌아간 것

### 3.1 main_epa_gs.py (메모리 체크리스트 기준)

| # | 항목 | 드롭 상태 | HEAD 위치(재적용 소스) | 드롭 쪽 대응 지점 |
|---|---|---|---|---|
| 1 | 소문자 테이블명 | **41건** 9종(`tb_tot_alg` 11, `tb_fp_val` 5, `tb_fp_si_val` 5, `tb_fr_si_val` 5, `tb_fr_val` 4, `tb_node_tag` 4, `tb_rawdata` 4, `tb_ctr_tnk_rst` 2, `tb_link_grp` 1). 주석·오류문구·print 포함 | — | 전체. `(?<![A-Za-z0-9_])tb_…(?![A-Za-z0-9_])` 치환 |
| 2 | `--inp` 기본값 | `gs_0909.inp` `:1741` | HEAD `:1726` `epa_model.inp` | `:1741` |
| 4 | 지방산단 임계 | `98.0`/`98~100%` `:1310-1314` | HEAD `:1363-1370` (95.0) | 3줄 |
| 5 | PRE 주기 옵션 | **삭제**(0건). 5분 고정 `scheduled_slot_at_or_after(dt, offset_min)` `:769-784`, `--schedule-offset-min choices 0~4` `:1762-1767`, `next_slot = slot_ts + 5분` `:2153`, `floor_to_5min` `:763` | 상수 `:205-213`, `floor_to_interval` `:800-808`, `schedule_offset_seconds` `:811-816`, `scheduled_slot_at_or_after` `:818-843`, argparse `:1747-1770`, `run_loop` 검증 `:2130-2137`·LOOP print `:2158-2161`·`result_ts` `:2206` 이후 11곳, docstring `:9,31-33` | 상수 `:143` 뒤, `:763`(위임), `:769-784` 교체, `:1762-1767` 옆, `run_loop` `:2093-2094`·`:2114-2118`·`:2150-2153`·`:2156-2251`(`slot_ts`→`result_ts` 분리), `:2163` `floor_to_5min(slot_ts)`→`floor_to_interval(slot_ts, interval_min)` |
| 6 | 섀도우 테이블 옵션 | **삭제**(0건) | 상수·`result_table`·`configure_tables` `:176-203`, `latest_processed_pre_ts` `:683-690`, `fetch_prediction_bundle` SQL `:710-724`, `copy_mo_to_cur` INSERT 3곳 `:952-984`, `save_results_db` INSERT 3곳 `:1633-1647`, argparse `:1811-1821`, LOOP print `:2175-2179`, 완료 print `:2097-2101`, `main` `:2317-2320`, docstring `:48-50` | `:138` 뒤 상수, `:617-622`, `:680-696`(두 SQL 의 `tb_ctr_tnk_rst`), `:894-926`(CUR INSERT 의 대상 3개만. `FROM tb_fp_si_val` 등 MO 원본은 운영 그대로), **`:1615-1665` 새 wide INSERT 3개의 테이블명** → `result_table("TB_…")`, `:1811` 뒤 argparse, `:2114` LOOP print, `:2065-2069` 완료 print, `main` `:2261` |
| 8 | `latest_complete_mo_source_ts` | 유지 | — | 대문자 복원만 |
| 9 | `701-365` | 0건(깨끗) | — | — |
| 10 | em dash | 0건(깨끗). `--help` 정상 | — | — |
| 함열 | `HAMYEOL_FLOW_TAG` | `"SS.740-914-FRI-1001"` `:138` | HEAD `:172` `740-914-FRI-1001`(1bb2682) | 1줄. si/mo·`NODE_META`(`:48`)는 접두 없음. `SS.` 태그가 `TB_RAWDATA` 에 없으면 함열 실측 결측 → 매 회차 PRE 실패 |

### 3.2 main_5min.py

| # | 항목 | 드롭 상태 | HEAD 위치(재적용 소스) | 드롭 쪽 대응 지점 |
|---|---|---|---|---|
| 7 | 섀도우 테이블 옵션 | **삭제**. `main()` 이 `args = build_arg_parser().parse_args()` 한 줄 `:2373` | `import re` HEAD `:7`, 주석+`_TABLE_NAME_RE`+`configure_tables` HEAD `:26-44`, argparse HEAD `:1946-1955`, `main` 의 `configure_tables(args)`+`ap.error`+"테이블: …" 로그 HEAD `:1964-1979` | `:7`, `LOCK_NAME` 뒤, `:2359` 옆, `:2373`. **주의**: `--schedule-offset-min` 범위 오류도 `ValueError` 를 던지므로(`:2325`) `main` 의 except 분기를 합칠 때 두 메시지가 구분되게 |
| 1 | 소문자 테이블명 | **1건** `:653` 오류 문구 `"EPANET PRE tb_tot_alg 결과가 없습니다."`(SQL 식별자는 상수 대문자라 실행 무해) | — | 문구만 |
| 10 | em dash | 0건 | — | — |
| 11 | `LOCAL_*` 8규칙·5컬럼 | 유지(50건, HEAD 동일) | — | — |

---

## 4. 벤더 코드 의심 지점

### 4.1 `TB_PUMP_CAL` 조회 `WHERE USE_YN = 'Y'` (`main_5min.py:485`) — **`= 1` 로 수정함**

- 컬럼 타입은 `int(1)` 이다(개발 덤프 스냅샷 `.idea/dataSources/3876a754-….xml:6421` `StoredType int(1)`, 사용자 확정 2026-10-01). BE 매퍼도 전부 `USE_YN = 1`/`= 0` 숫자 비교(`drvn_mssql.xml:791,793,837,851`).
- MariaDB 는 `int = 'Y'` 비교에서 `'Y'` 를 0 으로 캐스팅한다 → **비활성 곡선만** 후보가 되거나(USE_YN=0 행이 있으면) 0건 → "성능곡선을 찾지 못했습니다" → §4.3 의 except → 펌프 HOLD.
- 조치: `main_5min.py:485-488` 을 `WHERE USE_YN = 1` 로 바꾸고 SQL 주석으로 이유를 남겼다. 벤더 드롭마다 `'Y'` 로 되돌아올 것이므로 메모리 체크리스트 12번에 올렸다. 벤더에는 컬럼 타입을 알려 다음 드롭부터 맞춰 오도록 요청한다.
- 같은 파일 `:205` 의 규칙 테이블(`TB_CTRL_RULE_CFG`) 조회도 `USE_YN = 'Y'` 지만 **그대로 둔다.** HEAD(2026-09-30 드롭)에도 같은 조건이었고 운영에서 규칙 8키가 정상 로드됐으므로 그 테이블은 문자형이다. 2026-09-22 스냅샷에는 이 테이블이 없어(그 뒤 생성) 타입을 직접 보진 못했다 — 미확정이면 §7-(4) 두 번째 쿼리로 확인.

### 4.2 `EPA_PUMP_FLOW_LINK_ID = "45"` 하드코딩 (`main_5min.py:28`)

군산정수장 송수 링크를 `TB_FR_VAL.LINK_ID='45'` 로 가정한다. 현장 INP 의 송수관 LINK_ID 가 45 인지 §7-(5) 로 확인. 다르면 EPA 모드가 매 사이클 "송수 LINK_ID=45 결과가 없습니다" → HOLD.

### 4.3 Q/P 산정 실패를 전부 삼킨다 (`main_5min.py:1531-1535`, 사유 `PUMP_QP_SOURCE_CHECK` `:1697`)

`except Exception` 으로 받아 `pump_direction=0`, `pump_reference_hz=pump_cur_hz`, WARNING 한 줄. P5~P8 중 하나라도 빠지면 **프로세스는 정상인데 펌프만 영원히 HOLD** 다. 위험수위 override(`:1715`)는 이 except 뒤라 그때만 펌프가 움직인다. 적용 후 검증 항목에 "첫 3사이클 로그에 `PUMP_QP_SOURCE_CHECK` 없음" 을 넣는다.

### 4.4 실행 오프셋 기본 2분과 PRE 완료 전제 (`main_5min.py:2318-2330`)

5min 이 `:02` 에 `[ctrl_ts, ctrl_ts+5분)` 의 최신 PRE 를 찾는다. 운영 `.env` 는 `PRE_INTERVAL_MIN=1`/`PRE_OFFSET_SEC=50`(`deploy/gunsan/.env:48-49`)이라 `:01:50` 에 PRE 가 끝나 조건을 만족한다(여유 약 10초 + 해석 4배 소요 고려 필요, §6 단계 8). **PRE 를 5분 주기/120초로 돌리면** PRE 와 5min 이 같은 `:02` 에 시작해 경합 → 매번 HOLD. compose(prod·shadow) 는 이 인자를 안 주므로 기본 2 가 적용된다.

### 4.5 `INSERT … ON DUPLICATE KEY UPDATE` (`main_epa_gs.py:1624` 이하)

`TB_FP_VAL`·`TB_FR_VAL`·`TB_TOT_ALG` 에 `(ID, RGSTR_TIME, FLG)` 유니크 키가 없으면 재실행 시 중복 행이 쌓인다(HEAD 의 `INSERT IGNORE` 도 같은 전제였으므로 새 위험은 아님). §7-(6).

---

## 5. 외부 소비자 영향

### 5.1 compose · 반출본

| 서비스 | 파일 | 넘기는 인자 | 드롭 상태 |
|---|---|---|---|
| 운영 `ems-pre` | `deploy/gunsan/docker-compose.prod.yml:159-170` | `--interval-min`, `--schedule-offset-sec` | **둘 다 없음 → 기동 실패·재시작 반복** |
| 섀도우 PRE | `deploy/gunsan-shadow/docker-compose.shadow.yml:136-152` | 위 둘 + `--prediction-table TB_CTR_TNK_RST_SH`, `--result-table-suffix _SH` | **넷 다 없음 → 기동 실패** |
| 운영 `ems-ctrl` | `deploy/gunsan/docker-compose.prod.yml:222-229` | `--conn`, `--conn-key` | 유효 |
| 섀도우 `ems-ctrl` | `deploy/gunsan-shadow/docker-compose.shadow.yml:199-208` | 위 + `--prediction-table`, `--cmd-table` | **둘 없음 → 기동 실패**. 인자를 지워서 "고치면" 섀도우 추천이 운영 `TB_CTRL_CMD_RST` 로 들어가 운영 BE 가 Kafka 로 보낸다 |
| `deploy/gunsan-dev` | — | PRE/ctrl 서비스 없음 | 영향 없음 |

섀도우 compose 주석 "5분 경계(:00)마다"(`docker-compose.shadow.yml:176` 근처)는 `:02` 로 수정 대상. 운영 README·섀도우 README 의 기동 확인 로그 예시도 새 출력 라벨에 맞춘다.

### 5.2 BE · 화면

- PRE 결과를 읽는 BE 매퍼는 legacy 컬럼(`FP_ALG_RST_VAL`, `drvn_mssql.xml:255,299,321,358,981`)만 쓴다. 드롭이 legacy 컬럼에 1분 결과를 넣으므로 **화면은 그대로 1분 결과를 보인다.** 5/15/30분을 화면에 쓰려면 별도 작업(이 드롭 범위 밖).
- `TB_CTRL_CMD_RST` INSERT 컬럼은 불변 → BE `CtrlCmdService` 3장치 처리 영향 없음. 사유 JSON 에 새 코드 7종이 들어가므로 사유 한글 사전(`docs/gunsan-ctrl-cmd-consumer.md` 결정 9 의 사전) 확장은 **선택**(없으면 코드 그대로 표출).

### 5.3 더미 시더 (`.claude/skills/gunsan-epa-dummy`)

`TB_CTR_TNK_RST` 더미가 `PRDCT_VALUE` 만 채우면 드롭 PRE 는 `VALUE_5MIN/15MIN/30MIN` 결측으로 매 회차 SKIP. 시더가 네 컬럼을 채우도록 손봐야 개발서버에서 PRE 가 돈다(스킬 수정은 별건).

---

## 6. 적용 계획 (순서대로)

원칙: **드롭을 기준으로 두고 우리 항목을 얹는다.** `git checkout HEAD --` 로 되돌리면 벤더 신기능(§2)이 사라진다. 벤더 코드는 한 줄도 바꾸지 않고(§4 는 보고만), 우리 블록은 `git show HEAD:…` 원문을 옮긴다.

| 단계 | 작업 | 산출 · 검증 |
|---|---|---|
| 0 | **벤더에 §2.3 P1~P4 DDL 과 §4.2 확인 요청, §4.1(USE_YN int) 통보.** 현장 DB 에서 §7 SQL 실행 결과를 첨부 | 회신 전까지 1~6 은 진행 가능, 7 이후는 보류 |
| 0-1 | `main_5min.py:487` `USE_YN = 'Y'` → `= 1` (**완료**, 사용자 확정 2026-10-01). 규칙 테이블 `:205` 는 그대로 | `grep -n "USE_YN" main_5min.py` 가 `:205 'Y'`, `:487 1` 두 줄 |
| 1 | `main_epa_gs.py` 1번: 소문자 9종 41건 → 대문자. 파이썬 `re` 로 `(?<![A-Za-z0-9_])tb_(tot_alg|fp_val|…)(?![A-Za-z0-9_])` 치환(`\b` 는 한글 조사에 실패). 주석·print·오류문구 포함 | `python -c` 재검 0건 |
| 2 | `main_epa_gs.py` 2·4·함열: `:1741` → `epa_model.inp`, `:1310-1314` 98→95(조건·문구·note), `:138` `SS.` 제거 | `grep "gs_0909\|98\.0\|98~100\|98% 미만\|SS\.740"` 0건 |
| 3 | `main_epa_gs.py` 5·6번 재적용(드롭 구조 위에). (a) 상수·`floor_to_interval`·`schedule_offset_seconds`·`scheduled_slot_at_or_after`·`result_table`·`configure_tables` 를 HEAD 원문으로 복원. (b) argparse 4개 복원, `--schedule-offset-min` 은 `choices` 대신 "주기 미만" 검사로. (c) `run_loop`: `slot_ts`/`result_ts` 분리, `next_slot` 를 interval 로, LOOP·완료 print 에 테이블명. (d) **드롭의 wide INSERT 3개(`:1615-1665`)와 CUR INSERT 대상 3개(`:894-926`)·수요예측 SQL 2개(`:680-696`)·`latest_processed_pre_ts` 에 `result_table()`/`PREDICTION_TABLE` 적용.** MO 원본(`FROM TB_FP_SI_VAL` 등, `latest_complete_mo_source_ts`)은 운영 그대로. (e) 모듈 docstring HEAD `:3-53` 복원 + horizon 한 단락 추가 | `--help` 에 `--interval-min --schedule-offset-sec --schedule-offset-min --prediction-table --result-table-suffix --mo-max-age-min` 6종. `--prediction-table 'bad;name'` 거부, `--interval-min 4` 거부. **슬롯 함수 HEAD 대비 하루치 비교**(7초 간격 × 4조합, §9.4 와 같은 방식) 불일치 0 |
| 4 | `main_5min.py` 7번: HEAD `:7`·`:26-44`·`:1946-1955`·`:1964-1979` 를 `:7`·`LOCK_NAME` 뒤·`:2359` 옆·`:2373` 에 이식. `main` 의 `ValueError` except 가 `configure_tables` 와 `--schedule-offset-min` 범위 오류를 함께 받으므로 `ap.error(str(e))` 로 메시지 그대로 노출 | `--help` 에 `--prediction-table --cmd-table --schedule-offset-min`. 기동 로그 "테이블: 예측 조회=…, 추천 저장=…, 잠금=GUNSAN_CTRL_5MIN:…" |
| 5 | `main_5min.py` 1번: `:653` 문구 `TB_TOT_ALG` | grep 0건 |
| 6 | 양 파일 `ast.parse`, 회귀 grep 전체(`98\.0`, `SS\.740`, `701-365`, `gs_0909`, 소문자 `tb_`, `—`), 두 파일 `--help` | 전부 통과 |
| 7 | **현장 DB 선행조건 확인**(§7). P1~P8 전부 OK 가 아니면 반출 보류 | §7 결과를 이 문서 §8 관찰 기록에 기입 |
| 8 | **PRE 소요시간 측정.** 해석 4회라 1분 주기 안에 끝나는지. 개발서버가 열리면 `--once --ts` 로 1회 측정. 운영 서버 기록(2026-09-28 §9.2 는 수요예측만)과 비교. 60초 근접이면 `PRE_OFFSET_SEC` 를 당기거나(`PREDICT_OFFSET_SEC=20` + 예측 소요 뒤여야 함) 5min 의 `--schedule-offset-min` 을 3 으로 | 1회차 소요 초 기록 |
| 9 | compose·README 문서 갱신: 섀도우 주석 `:00`→`:02`, 기동 확인 로그 예시, 운영 README 의 `TB_CTR_TNK_RST` DDL 에 `VALUE_1min`·`VALUE_15min` 추가(upload.py:89 와 동일 ALTER) | `deploy/<현장>/` 변경이라 **사용자 확인 후** |
| 10 | 커밋 2개로 분리: (가) 벤더 드롭 + 재적용(두 파일), (나) compose·문서 | 커밋 메시지에 §1 요약 |
| 11 | 반출본 재빌드(prod·shadow). `build-and-save.ps1 -Target prod -Tag 20261001`, shadow 동일. 백그라운드, 출력 리다이렉트 금지 | 이미지 내 `--help` 6종(PowerShell 로), `load-and-up.sh` 사전검사 블록 실행, `images.txt`·`.env` 태그 |
| 12 | 현장 적용 순서: DDL(P1~P5) → 수요예측이 네 컬럼을 채우는지 1분 확인 → PRE 기동·첫 회차 `[OK] PRE 1/5/15/30분 DB 저장 완료` → `ems-ctrl` 기동·첫 3사이클 로그에 `PUMP_QP_SOURCE_CHECK` 없음·`PUMP_SRC_AI/EPA` 중 의도한 모드 | AI 운전모드는 분석(2)으로 시작 |

단계 1~6 은 네트워크 없이 가능하다. 7·8 은 DB 가 열려야 한다(2026-10-01 현재 `<internal-host>`·`<internal-host>` 모두 3306 무응답).

---

## 7. 현장 DB 확인용 SQL

```sql
-- (1) P5: 수요예측 테이블 horizon 컬럼
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'TB_CTR_TNK_RST'
   AND COLUMN_NAME IN ('PRDCT_VALUE','VALUE_1min','VALUE_5min','VALUE_15min','VALUE_30min');
-- 다섯 줄이 나와야 한다. 최신 행에 NULL 이 없는지:
SELECT DSTRB_ID, RGSTR_TIME, PRDCT_VALUE, VALUE_1min, VALUE_5min, VALUE_15min, VALUE_30min
  FROM TB_CTR_TNK_RST ORDER BY RGSTR_TIME DESC LIMIT 5;

-- (2) P1~P3: 결과 테이블 horizon 컬럼(없어야 정상 — 있으면 벤더가 이미 넣은 것)
SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
   AND TABLE_NAME IN ('TB_FP_VAL','TB_FR_VAL','TB_TOT_ALG','TB_FP_VAL_SH','TB_FR_VAL_SH','TB_TOT_ALG_SH')
   AND COLUMN_NAME REGEXP '_(1|5|15|30)MIN$'
 ORDER BY TABLE_NAME, COLUMN_NAME;

-- (3) P6: TB_PUMP_CAL 추가 컬럼
SELECT COLUMN_NAME, COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'TB_PUMP_CAL'
   AND COLUMN_NAME IN ('USE_YN','avg_error_rate','data_count','run_minutes');

-- (4) P8(확정됨, 기록용): TB_PUMP_CAL.USE_YN 은 int. 활성 곡선 개수만 확인
SELECT USE_YN, COUNT(*) FROM TB_PUMP_CAL GROUP BY USE_YN;      -- USE_YN=1 이 0건이면 매칭 후보가 없다
-- 규칙 테이블 USE_YN 타입(:205 의 'Y' 비교가 맞는지)
SELECT COLUMN_NAME, COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'TB_CTRL_RULE_CFG' AND COLUMN_NAME = 'USE_YN';

-- (5) §4.2: 송수 링크 45 존재
SELECT LINK_ID, COUNT(*) FROM TB_FR_VAL WHERE LINK_ID = '45' AND FLG = 'PRE'
   AND RGSTR_TIME >= NOW() - INTERVAL 1 DAY GROUP BY LINK_ID;

-- (6) §4.5: 결과 테이블 유니크 키
SHOW INDEX FROM TB_FP_VAL WHERE Non_unique = 0;
SHOW INDEX FROM TB_FR_VAL WHERE Non_unique = 0;
SHOW INDEX FROM TB_TOT_ALG WHERE Non_unique = 0;

-- (7) P7: 모드 스위치
SELECT FUNC_TYP, DEFAULT_VALUE FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'EPA_PUMP';
```

---

## 8. 적용 기록 (2026-10-01)

사용자 지시로 §6 단계 1~6 을 수행했다. 긴 검증(슬롯 함수 하루치 비교, DB 스냅샷)은 사용자 지시로 생략. §7 현장 SQL 은
사용자가 "운영 테이블에 컬럼을 신규 추가했다" 고 확인해 P1~P5 완료로 간주했다(직접 조회는 안 함).

| 단계 | 결과 |
|---|---|
| 0-1 | `main_5min.py` `TB_PUMP_CAL` 조회 `USE_YN = 1`(SQL 주석 2줄 포함). 규칙 테이블 `:227` 의 `'Y'` 는 그대로 |
| 1 | `main_epa_gs.py` 소문자 9종 **41건** → 대문자(파이썬 `re`, `(?<![A-Za-z0-9_])` 경계). 재검 0건 |
| 2 | `--inp` 기본값 `epa_model.inp`, 지방산단 임계 95(조건·문구·note), `HAMYEOL_FLOW_TAG` `SS.` 제거 |
| 3 | 5·6번: 상수 블록(`PREDICTION_TABLE`·`RESULT_TABLE_SUFFIX`·`result_table`·`configure_tables`·`DEFAULT_INTERVAL_MIN`·`ALLOWED_INTERVAL_MIN`·`MO_INTERVAL_MIN`), `floor_to_interval`·`schedule_offset_seconds`·`scheduled_slot_at_or_after`(HEAD 원문), argparse 4개, `run_loop` 의 interval/offset 검증·LOOP print 2줄·`slot_ts`/`result_ts` 분리(`next_slot`, SKIP 비교, print, `run_once(result_ts=)`, FAIL 로그, `last_processed`)·`expected_prediction_from = floor_to_interval(slot_ts, interval_min)`, `main` 의 `configure_tables`. **드롭의 wide INSERT 3개와 CUR INSERT 3개의 대상 테이블만 `result_table()`** 로 감쌌고 컬럼 목록·`ON DUPLICATE KEY UPDATE` 는 벤더 원문 그대로. 수요예측 SQL 2개와 `latest_processed_pre_ts` 는 `{PREDICTION_TABLE}`/`result_table("TB_TOT_ALG")`. 모듈 docstring 을 HEAD 원문으로 복원하고 다중 horizon 단락을 추가 |
| 4 | `main_5min.py` 7번: `import re`, `configure_tables` 블록(주석에 성능곡선·EPA PRE 결과 테이블도 읽기 전용임을 추가), argparse 2개, `main` 의 `configure_tables`+`ap.error`+기동 로그(실행 오프셋도 함께 출력) |
| 5 | `main_5min.py:653` 문구 `TB_TOT_ALG` |
| 6 | `ast.parse` 두 파일 통과. `--help`: epa_gs 24종(HEAD 와 동일 집합), 5min 9종(HEAD 8종 + 벤더 `--schedule-offset-min`). `--prediction-table 'bad;name'`·`--cmd-table 'bad;x'` 거부, `--interval-min 4` 거부. 회귀 grep(`98\.0`, `SS\.740`, `701-365`, `gs_0909`, 소문자 `tb_`) 0건. 운영 compose 가 넘기는 `--interval-min`·`--schedule-offset-sec` 인식 |

벤더 코드에서 바꾼 것은 `USE_YN = 1` 한 줄(사용자 확정)이다. 그 외 `git diff` 의 벤더 줄은 손대지 않았다.
`—`(U+2014)는 주석·docstring 에만 있고 출력 문자열에는 없다(HEAD 와 동일).

**운영 반출본 `dist/swtp-gunsan-20261001.tar.gz` (1,832 MB, 2026-10-01 12:10)** — 커밋 `4237981`(드롭 반영) + `dd54844`(성능곡선관리
주파수 열·CommonTable 복원) 기준. 1차 빌드는 원격 커밋 `e83d98a` 가 지운 `CommonTable.jsx` 때문에 `inp-editor-fe` 의 `yarn build` 에서
실패했고, 복원 후 2차 빌드가 exit 0. 검증:

| 항목 | 결과 |
|---|---|
| `images.txt` 7종 태그 `20261001`, LF·BOM 없음 / `.env` `TAG=20261001`, `TILE_TAG=latest` 유지 | OK |
| ems-py-api 이미지 안 `main_epa_gs.py --help` | `--interval-min --schedule-offset-sec --prediction-table --result-table-suffix --mo-max-age-min` 인식 |
| ems-py-api 이미지 안 `main_5min.py --help` | `--prediction-table --cmd-table --schedule-offset-min` 인식 |
| 이미지 안 소스 | `TB_PUMP_CAL` `USE_YN = 1`, 소문자 `tb_` 0건, 함열 `740-914-FRI-1001`, 임계 95.0, `--inp` 기본 `epa_model.inp`, 회귀 패턴(98/SS.740/701-365/gs_0909) 0건, `result_table(` 14곳·`configure_tables` 2곳·`interval_min` 17곳 |
| inp-editor-fe 이미지 번들 JS | `펌프 주파수`·`pumpHzLabel` 문자열 포함 |
| 자바 이미지 glibc | ems-java-api 2.31(focal), inp-editor-be 2.35(compose `seccomp:unconfined` 전제) |
| 번들 `load-and-up.sh` 2절(INP 4개)·3절(수요예측 자산, `VALUE_1min`) | exit 0 |

서버 적용은 `tar xzf swtp-gunsan-20261001.tar.gz && cd swtp-gunsan-20261001 && ./load-and-up.sh`. 적용 뒤 §6 단계 12 의 로그 확인
(`[OK] PRE 1/5/15/30분 DB 저장 완료`, `ems-ctrl` 첫 3사이클에 `PUMP_QP_SOURCE_CHECK` 없음)을 할 것.

compose·README 갱신(§6 단계 9)은 `deploy/` 변경이라 이번에 하지 않았다. 섀도우 compose 주석 ":00" 과 운영 README 의
`TB_CTR_TNK_RST` DDL 은 다음에 사용자 확인 후 반영.

---

## 9. 관찰 기록 (본 문서에서 수정하지 않음)

| 시각 | 관찰 | 근거 |
|---|---|---|
| 2026-10-01 11:23-11:24 | 두 파일 통째 교체. `main_5min.py` 596 변경(+/-), `main_epa_gs.py` 863 변경 | `git diff --stat` |
| 2026-10-01 | `ast.parse` 두 파일 통과. `--help` 두 파일 정상 출력(em dash 0건) | 로컬 실행 |
| 2026-10-01 | 드롭 `main_epa_gs --help` 인자 20종, HEAD 24종. 차이 4종이 전부 우리 5·6번 | 로컬 실행 비교 |
| 2026-10-01 | 드롭 `main_5min --help` 인자 7종, HEAD 8종. `--prediction-table --cmd-table` 사라지고 `--schedule-offset-min` 추가 | 로컬 실행 비교 |
| 2026-10-01 | 소문자 테이블명: epa_gs 41건 9종, 5min 1건(문구) | 파이썬 `re` 집계 |
| 2026-10-01 | 개발 덤프 스냅샷(2026-09-22): `tb_pump_cal.USE_YN int(1)`, `avg_error_rate double`, `data_count` 존재. `tb_fp_val`·`tb_tot_alg` 에 `_MIN` 컬럼 없음. `tb_ctr_tnk_rst` 는 `PRDCT_VALUE` 만 | `.idea/dataSources/3876a754-….xml:2400-2420, 6419-6421` |
| 2026-10-01 | 개발 DB `<internal-host>`·`<internal-host>` 3306 접속 시간 초과 → §7 미실행 | pymysql 접속 시도 |
| 2026-10-01 | 운영 `.env` PRE 1분/50초, 수요예측 60초/20초 | `deploy/gunsan/.env:46-49` |
