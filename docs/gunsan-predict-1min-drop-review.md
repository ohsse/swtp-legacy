# 군산 수요예측(ems_gu_predict) 1분 주기 교체본 — 무엇이 바뀌었고 무엇이 되돌아갔나

- **대상**: 2026-09-28 작업 트리에 들어온 `ems_gu_predict/` 교체본 (수정 22건 + 신규 `configs/gu_db_1min_h30.yaml` 스테이징)
- **비교 기준**: `HEAD`(eea2c8a). `ems_gu_predict` 를 마지막으로 건드린 커밋은 6241aa5 → 39c9d88 → 1bb2682 → 8178bc1 이다.
- **성격**: 사실 확인 문서다. 코드는 고치지 않았다. 되돌릴지·재적용할지는 이 문서를 보고 정한다.
- 이 문서의 파일 경로는 따로 적지 않으면 `ems_gu_predict/` 기준이다. 라인 번호는 교체본(작업 트리) 기준이다.

---

## 1. 결론 요약

교체의 목적은 개발사 요구(2026-09-28)에 따라 **운영 주기를 5분에서 1분으로, 예측 horizon을 6시간에서 30분으로** 바꾸는 것이다.
업로드 컬럼은 `VALUE_1min / 5min / 15min / 30min` 네 개만 남는다(`scripts/harness/upload.py:101-103`).

그런데 이 교체본은 **우리 커밋 39c9d88·1bb2682·8178bc1 이전 코드**를 바탕으로 만들어졌다. 그래서 1분 기능이 들어오면서 우리가 고쳐 둔 부분이 함께 사라졌다.
지금 상태 그대로 운영 번들에 넣으면 아래 문제가 코드상 예상된다.

| # | 현상 | 영향 | 근거 |
|---|---|---|---|
| A | 함열가압장 태그가 `SS.740-914-FRI-1001.F_CV` 표기로 돌아갔다 | 개발서버 최근 구간에서 압력은 `SS.` 표기 행이 없다. `P_Ham` 이 전부 NaN이 되어 **매 사이클 예측이 실패**할 것으로 예상된다 (§9에서 조치) | §3.1 |
| B | `PRDCT_VALUE` 를 채우지 않는다 | REPLACE INTO라 매 사이클 0으로 덮인다. **PRE 관망해석과 BE 운전현황이 수요 0을 읽는다** | §3.2, §4.1 |
| C | 새 컬럼 `VALUE_1min`·`VALUE_15min` 에 INSERT한다 | 운영 테이블에 이 컬럼이 없으면 **업로드가 매번 실패**한다. 이 경우 B보다 먼저 드러난다 | §4.2 |
| D | 태그리스트의 V2/V4 태그가 서로 바뀌었다(정정) | 교체본의 매핑은 저장소의 다른 문서와 일치한다. 하지만 배포 중인 5분 모델(09-14 학습)은 **바뀌기 전 매핑으로 학습**됐으므로, 추론 때 V2/V4 입력이 뒤바뀌어 들어간다 | §2.3 |
| E | prod 기본 주기가 60초로 바뀌었고, 벽시계 정렬과 격자 고정이 빠졌다 | 배포 compose는 여전히 5분 모델이다. 같은 5분 버킷을 1분마다 다시 계산하고, origin이 흔들릴 수 있다 | §3.3, §5 |

---

## 2. 새로 들어온 것

### 2.1 1분 주기 config — `configs/gu_db_1min_h30.yaml` (신규)

| 키 | 값 | 이전(`gu_db_noq8_h6.yaml`) |
|---|---|---|
| `data.freq` | `1min` | `5min` |
| `window.window_size / horizon / stride` | 360 / 30 / 30 (스텝 = 분) | 288 / 72 / 6 (스텝 = 5분) |
| `data.lever_diff_steps` | `[5, 15, 30]` | `[1, 3, 6]` |
| `data.exclude_vars` | `[Q8, P9]` | `[Q8]` |
| `data.target_exclude_vars` | `[H7_3 … H7_8, P6]` (`:102`) | 없음 |
| `data.end_date` | `"2026-09-01"`로 고정(A/B 비교용, 주석에 "운영 재학습 때 갱신"이라고 적혀 있음) | — |
| `output.dir` | `./runs/gu_db_1min_h30` | `./runs/gu_db_noq8_h6` |

yaml 머리 주석에는 **"Stage3 정수장 추천의 리드타임이 최대 30분으로 줄어든다는 걸 알고 쓰는 설정"**이라고 명시돼 있다.

**학습 산출물과 yaml의 차이**: `runs/gu_db_1min_h30/config.json` 의 `data.end_date` 는 `null` 이다. 학습을 마친 뒤 yaml만 `2026-09-01` 로 고정한 것으로 보인다. `data.cache_dir` 은 `./Data` 이며 이 저장소에는 없다(개발사 로컬 캐시로 추정, **미확정**).

1분 모델 메타(`runs/gu_db_1min_h30/meta.json`): feature 38개, target 16개. `runs/`·`models/` 는 git 밖(`.gitignore`)에 있다.

### 2.2 코드 기능 추가

| 기능 | 위치 | 비고 |
|---|---|---|
| `DataConfig.target_exclude_vars` — target에서만 빼고 feature로는 남긴다 | `src/deepems/config.py:111`, `src/deepems/pipeline.py:82-95` | target이 아닌 이름을 넣으면 ValueError가 난다 |
| `OutlierConfig.scaler_type`·`column_scaler_overrides` (minmax / robust / standard) | `config.py:324`, `src/deepems/data.py:28, 463` | 기본값은 minmax(기존 동작). **어떤 yaml도 설정하지 않는다** |
| `TrainConfig.sample_time_decay_halflife_days` + `compute_time_decay_weights` | `config.py:398`, `src/deepems/windows.py:72`, `src/deepems/train.py:99` | 기본값 None(끔). **어떤 yaml도 설정하지 않는다** |
| `WindowDataset` 이 `(X, y, w)` 3-튜플을 반환한다 | `windows.py:107`, `train.py:64` | 저장소에서 `WindowDataset` 을 쓰는 곳은 `train.py` 한 곳뿐이다 |
| 잔차모델 스텝을 config에서 파생 (horizon / 60분 추세 / 5분 stride) | `scripts/harness/train.py:109-113` | 5분 config에서는 72/12/1로 기존 값과 같다 |
| 짧은 지평은 origin 값(persistence)으로 대체 | `upload.py:238-252`, `schedule.py:324-329` | 기본 `--persistence-max-offset-minutes 1`, 예외 target `H3` |
| H3 제어 추천 함수 5종 | `src/deepems/recommend.py:449, 748, 842, 866, 968` | **`recommend.py` 밖에서 호출하는 곳이 없다**(Grep 확인). 지금은 운영 경로와 무관하다 |
| stuck 보간 대상에 P9 추가 | `configs/*.yaml` 6개 (`gu_db_noq8_h6.yaml:49` 등) | 1분 config는 P9를 `exclude_vars` 로 빼므로 보간 대상에 있어도 건너뛴다(`data.py:354`) |

`upload.py:238-252` 의 "origin 실측값"은 `schedule.py:187, 234, 279` 에서 넘기는 `filled.iloc[-1]` 이다.
이 값은 ffill·선형보간을 **거친 뒤**의 값이라, 최대 `ffill_limit_minutes`(10분) 전 값일 수 있다.

### 2.3 태그리스트·토폴로지

`taglist/GU_taglist.xlsx` 를 HEAD와 행 단위로 비교했다(읽기 전용, pandas).

| 변수 | HEAD | 교체본 |
|---|---|---|
| `Q_Ham` | `740-914-FRI-1001` | **`SS.740-914-FRI-1001.F_CV`** |
| `P_Ham` | `740-914-PRI-1009` | **`SS.740-914-PRI-1009.F_CV`** |
| `V2` | `891-365-POI-8601` | `891-365-POI-8600` |
| `V4` | `891-365-POI-8600` | `891-365-POI-8601` |
| `H7_3`~`H7_8` | NU | target |
| `O8`(`FRI-8802`), `O9`(`FRI-8500`), `P9`(`PRI-8500`) | 없음 | target (신규) |
| `Q8`(`FRI-8802`) | target | 삭제(같은 태그가 `O8` 로 이름만 바뀜) |
| `Q37`, `H37_1~3`, `Q/P_GS_OLD/NEW` | NU | 삭제 |

target 수: HEAD 18 → 교체본 26 (combine 전 기준).

**V2/V4**: 교체본의 매핑(`POI-8600` = 지방산단 = V2, `POI-8601` = 국가산단 = V4)은 저장소의 다른 문서와 일치한다.
`docs/gunsan-si-valve-opening-analysis.md:21, 116` 과 `.claude/skills/gunsan-epa-dummy/references/engine-inputs.md:15` 가 모두 `POI-8601` 을 국가산단밸브로 적는다.
`src/deepems/taglist.py:297-299` 의 `LEVER_PHYSICAL_BOUNDS` 도 같은 이유로 V2/V4 값을 맞교환했다.
**즉 HEAD 쪽이 틀렸던 정정이다.** 문제는 이미 학습된 5분 모델이다. `runs/gu_db_noq8_h6`(2026-09-14 11:48 학습)는 HEAD 매핑으로 학습됐으므로, 교체본 태그리스트로 추론하면 V2/V4 입력이 뒤바뀐다(`V2` scaler는 13~64 분포로 fit됐는데 98.5 부근 값이 들어간다).
예측 품질에 얼마나 영향이 있는지는 **미확정**이다.

**관망 토폴로지**(`taglist.py:182-200`, 참고용 오버레이, 학습에는 쓰지 않음):
- 함열가압장 → 개정분기 연결을 추가했다.
- 군산정수장/함열 → 내초도분기 직결과, 내초도분기 → 오식도 유입(Q7)을 삭제했다.
- 군산관말 → 내초도분기(종단)를 추가했다.
- 이름을 관암에서 관말로, 내조도에서 내초도로 바꿨다.

---

## 3. 되돌아간 것 (우리 커밋 회귀)

### 3.1 함열가압장 태그 `SS.` 접두 — 1bb2682

1bb2682 의 커밋 메시지는 "함열가압장 유량태그가 실제 TB_RAWDATA 에는 `SS.` 접두 없이 `740-914-FRI-1001` 로 들어온다"이다.
dev DB 실측(`docs/gunsan-si-valve-opening-analysis.md:246`)으로도 `740-914-FRI-1001` 이 1,891,308행 있다.

교체본은 이 태그를 태그리스트(엑셀)에서 `SS.…F_CV` 로 되돌렸다. 주석의 예시(`src/deepems/analyze.py:1300`, `taglist.py:308-309`)도 같이 되돌아갔다.
수요예측은 태그명 그대로 `TAGNAME IN (...)` 으로 조회하므로(`src/deepems/db_source.py:140, 218-221`), 이름이 다르면 그 태그 컬럼이 전부 NaN이 된다.
`Q_Ham`·`P_Ham` 은 5분·1분 두 모델 모두의 feature다(각 `meta.json`). 그리고 `infer.predict_next_horizon` 은 윈도우 안에 결측이 하나라도 있으면 예외를 던진다(`src/deepems/infer.py:88-95`).
따라서 **우리 DB에서는 매 사이클 예측 실패**가 예상된다.

**군산 개발서버 DB 실측 (2026-09-28, `<internal-host> / ems_db`)** — 태그별로 기간을 지정한 직접 조회(`TAGNAME = ? AND TS >= '2026-07-25'`):

| TAGNAME | 행 수 (7/25~) | MAX(TS) |
|---|--:|---|
| `740-914-FRI-1001` | 47,216 | 2026-09-28 13:47 |
| `SS.740-914-FRI-1001.F_CV` | 46,994 | 2026-08-26 15:32 |
| `740-914-PRI-1009` | 46,993 | 2026-08-26 15:31 |
| `SS.740-914-PRI-1009.F_CV` | **0** | — |

**최근 구간에서 살아 있는 표기는 접두 없는 쪽이다**(압력은 `SS.` 표기 행이 아예 없다). 수요예측은 최근 구간만 조회하므로 이 결과가 운영 경로와 같은 조건이다.

정정: 처음에는 `GROUP BY TAGNAME` 집계 조회(전체 기간)로 "접두 없는 압력 태그 0행, `SS.` 표기 1,891,396행"이라고 기록했다. 그러나 태그별 직접 조회와 맞지 않는다. 집계 결과가 왜 다른 이름에 붙었는지는 전체 기간 조회가 계속 시간 초과로 끝나 **미확정**이다.
`740-914-FRI-1001` 의 8/26 이후 행은 더미 스킬(`gunsan-epa-dummy`)이 넣은 것으로 보인다(**미확정**).
운영 DB(`<internal-host>`)의 표기는 **미확정**이다.

**같은 조회에서 발견한 것**: 개발서버에는 1분 모델의 입력 태그 `O9`(`FRI-8500`), `H7_3`~`H7_8` 의 최근 30일 데이터가 **하나도 없다**. 그래서 태그 표기와 무관하게 개발서버에서는 1분 모델이 유효한 입력 윈도우를 만들 수 없다(매 사이클 결측으로 실패).
`taglist/GU_network_topology.md:61-62` 도 `SS.` 표기이다(이 파일은 이번 diff에 없다. HEAD부터 그랬다).

### 3.2 `PRDCT_VALUE` 채우기 — 39c9d88

| 사라진 것 | HEAD 위치(39c9d88) | 교체본 |
|---|---|---|
| `LEGACY_VALUE_COLUMN`, `DEFAULT_PRDCT_VALUE_FROM`, `UploadConfig.prdct_value_from` | `upload.py` | 없음 |
| 접속정보 `prdct_value_from` 검증(잘못된 키면 기동 시 거부) | `load_upload_config` | 없음. 키가 있어도 **무시**한다(`upload.py:148` 부근) |
| INSERT 컬럼을 행 키에서 끌어내고, 행마다 키가 같은지 검사 | `upload_target_forecasts` | 고정 목록 `upload.py:267` |
| readme "PRDCT_VALUE 지우지 말 것 / DROP 말고 ALTER" | `readme.txt` | "기존 테이블 지우고 새로 만듦" 안내로 돌아감. CREATE 문에도 `PRDCT_VALUE` 가 없다 |
| dev 미리보기 CSV의 `PRDCT_VALUE` 열 | `schedule.py` | 없음 |

교체본 `readme.txt` 에는 "schedule.py가 CREATE TABLE IF NOT EXISTS로 자동 생성"이라고 적혀 있다. 그러나 2026-09-15에 `ensure_table` 이 제거됐고, 교체본 `upload.py` docstring도 "CREATE/ALTER/DROP 코드는 넣지 않는다"라고 적는다. **readme와 코드가 서로 모순된다.**

### 3.3 prod 루프 격자 고정 — 6241aa5·8178bc1

교체본 `run_prod`(`scripts/harness/schedule.py:246-289`)에서 사라진 것:

- `_seconds_until_next_slot` 벽시계 정렬 → `time.sleep(args.interval_seconds)`(`:289`)로 돌아갔다. 사이클 소요시간만큼 주기가 계속 뒤로 밀린다.
- `window_end = now.floor(freq) + freq` 격자 고정 → `now` 를 그대로 넘긴다(`:266-268`).
- `--cycle-lag-seconds`, "격자 어긋남" WARNING, 사이클 소요시간 로그.
- prod 기본 주기가 300초에서 60초로 바뀌었다(`:376`).

### 3.4 입력 결측 진단 — 8178bc1

- `data.missing_tag_report` 가 삭제됐다.
- `preprocess.fetch_window` 의 `logger`/`recent_steps` 인자와 `_format_missing_report`·`_tag_names_by_var` 가 삭제됐다(`scripts/harness/preprocess.py:60, 95`).
- `infer.predict_next_horizon` 의 예외 메시지에서 결측 **태그 목록**과 스텝/분 구분이 빠졌다(`infer.py:87, 93`). 메시지가 "…분뿐입니다"로 돌아갔는데, 5분 모델에서는 단위가 틀린 표기다.

§3.1의 함열 태그 문제가 실제로 일어나면, 이 진단이 없어서 로그에는 **시각 목록만** 찍힌다. 어느 태그 때문인지 로그에서 바로 보이지 않는다.

### 3.5 문서

`README.md` 의 "Docker 실행" 절이 통째로 삭제됐다. README 준비 항목 4는 여전히 `VALUE_5min..VALUE_6h` 를 적고 있어 교체본 코드와 맞지 않는다.

---

## 4. 외부 소비자 영향

### 4.1 `PRDCT_VALUE` 를 읽는 곳

| 소비자 | 위치 |
|---|---|
| 군산 PRE 관망해석(EPANET 수요) | `epa/epanet_gunsan/main_epa_gs.py:644, 653, 673, 1030` |
| BE 운전현황 | `be/src/main/resources/sqlmapper/mysql/drvn_mssql.xml:397, 431, 465, 485, 643, 677, 746, 798-804, 863, 889, 1116, 1266, 1282-1285` |

`drvn_mssql.xml:798-804` 는 `PRDCT_VALUE != 0` 조건으로 거른다. 0으로 덮이면 이 쿼리는 행을 못 찾는다.

### 4.2 `VALUE_*` 컬럼 구성

교체본은 `VALUE_1min, VALUE_5min, VALUE_15min, VALUE_30min` 으로 REPLACE INTO한다(`upload.py:267-269`).
배포 문서가 안내하는 운영 스키마(`deploy/gunsan/README.md:118-124`)에는 `VALUE_1min`·`VALUE_15min` 이 없다.
필요한 DDL은 `upload.py:70` docstring에만 있고, 배포 README·readme.txt에는 없다.
기존 `VALUE_10min`, `VALUE_1h`~`VALUE_6h` 는 더 이상 쓰지 않으므로 새 행에서는 NULL(또는 DDL 기본값)이 된다. 저장소 안에서 이 컬럼을 읽는 코드는 찾지 못했다(Grep).

### 4.3 제어 판단 엔진은 영향 없음

`epa/epanet_gunsan/main_5min.py:353-387` 은 `TB_CTR_TNK_RST` 에서 `PRED_IDS` 행의 **`RGSTR_TIME` 나이**(stale 여부)만 본다. 값 컬럼은 읽지 않는다.
컬럼 변경의 영향은 없고, 1분 주기가 되면 신선도가 오히려 좋아진다. 다만 §3.1 때문에 예측이 실패하면 stale 판정이 난다.

### 4.4 배포 번들과의 어긋남

| 파일 | 내용 |
|---|---|
| `deploy/gunsan/docker-compose.prod.yml:262-265` | `runs/gu_db_noq8_h6` + `configs/gu_db_noq8_h6.yaml`(5분 모델)이 고정돼 있다 |
| `deploy/gunsan/conf/predict/db_upload_connections.json:4, 13` | `prdct_value_from` 과 그 주석. 교체본은 이 키를 무시한다 |
| `deploy/gunsan/load-and-up.sh:128-135, 199` | `prdct_value_from` 점검, "5분마다 갱신" 확인 안내 |
| `deploy/gunsan/README.md:109-147, 408, 447` | 5분 주기, `VALUE_5min~6h` + `PRDCT_VALUE` 스키마 |
| `deploy/gunsan-shadow/…` | 같은 구조(`TB_CTR_TNK_RST_SH`) |

기본 테이블명이 `TB_CTR_TNK_RST` 에서 `tb_ctr_tnk_rst` 로 바뀌었다(`upload.py:148`). 배포 JSON이 `"table"` 을 대문자로 명시하므로 지금은 영향이 없다. 키를 뺄 때 동작이 달라지는지는 DB의 `lower_case_table_names` 설정에 달려 있다(**미확정**).

---

## 5. 조합별 동작 예측 (코드 근거, 실행 검증 아님)

### 5.1 교체본 코드 + 현재 compose(5분 모델) 그대로

- 60초마다 사이클이 돈다(`schedule.py:376`). 입력 격자는 5분이라 같은 origin을 최대 5번 계산한다. REPLACE로 덮어쓰므로 행이 중복되지는 않는다.
- `VALUE_1min`: 5분 모델에는 1분 앞 스텝이 없다(`_value_at_offset` 의 `pos = round(1/5)-1 = -1`, `upload.py:171-173`). persistence 대체로 origin 값이 들어간다. **예외 target인 H3는 None**이 된다.
- `VALUE_15min`: 5분 격자의 3번째 스텝.
- 실제로는 §3.1(태그)이나 §4.2(컬럼) 중 먼저 걸리는 쪽에서 사이클이 실패한다.
- 태그 문제가 없더라도 §2.3의 V2/V4 입력 뒤바뀜이 남는다.

### 5.2 1분 모델로 전환

- `runs/gu_db_1min_h30/`, `models/offline_artifacts_1min.joblib` 이 로컬에 있다(둘 다 2026-09-28 14:52, git 밖).
- compose의 `--stage1-run-dir`/`--source-cfg`/`--offline-artifacts` 인자와 반출 스크립트의 복사 대상을 바꿔야 한다.
- 60초 안에 사이클이 끝나는지: 개발서버에서 더미 계측값으로 돌려 보니 **10사이클 모두 1.0~5.3초**였다(§9.2). 운영 DB에서의 실측은 아직 없다.

---

## 6. 참조 문서 부재

교체본 주석이 근거로 드는 아래 문서와 경로는 저장소에 **없다**:

- `docs/DEVNOTES.md` (persistence 대체 근거 "1분 시점 23개 중 2개만 이김")
- `docs/model_results.md` (8/3 저수위 사태, V2 운영 방식 변경)
- `docs/network_control_simulation_design.md` (규칙 2/3/5/11)
- `docs/GU_network_topology.md` — 실제로는 `taglist/GU_network_topology.md` 만 있다. 교체본이 주석 경로를 `taglist/` 에서 `docs/` 로 바꿨다(`analyze.py`, `recommend.py`, `taglist.py`).
- `scripts/network_app` (`recommend.py` 의 `hourlyBand()`·`resolveEdgeArray` 참조)

---

## 7. 현장 DB 확인용 SQL

```sql
-- §4.2 새 컬럼 존재 여부 / §3.2 PRDCT_VALUE 존재 여부
SHOW COLUMNS FROM TB_CTR_TNK_RST;

-- §3.1 함열 태그 표기 — 어느 쪽 이름으로 행이 쌓이는가
SELECT TAGNAME, COUNT(*), MAX(TS) FROM TB_RAWDATA
 WHERE TAGNAME IN ('740-914-FRI-1001', 'SS.740-914-FRI-1001.F_CV',
                   '740-914-PRI-1009', 'SS.740-914-PRI-1009.F_CV')
 GROUP BY TAGNAME;

-- §3.2 적용 후 확인 — PRDCT_VALUE 가 0 이면 레거시 소비자가 0 을 읽고 있다
SELECT DSTRB_ID, RGSTR_TIME, PRDCT_VALUE, VALUE_5min
  FROM TB_CTR_TNK_RST ORDER BY RGSTR_TIME DESC LIMIT 10;
```

---

## 8. V2/V4 매핑 변경 상세

### 8.1 무엇이 바뀌었나

| 변수 | 의미(코드상) | HEAD 태그리스트 | 교체본 태그리스트 |
|---|---|---|---|
| `V2` | 지방산단밸브 개도. `Q2`·`P2` 와 같은 지점(`taglist.py` REFERENCE_SAME_SITE_GROUPS) | `891-365-POI-8601` | `891-365-POI-8600` |
| `V4` | 국가산단밸브 개도. `Q4`·`P4` 와 같은 지점 | `891-365-POI-8600` | `891-365-POI-8601` |

### 8.2 교체본 쪽이 맞다는 근거

- **태그 번호가 같은 지점끼리 짝이 맞는다.** 교체본 엑셀에서 지방산단분기는 `FRI-8600`(Q2)·`PRI-8600`(P2)·`POI-8600`(V2)이다. 국가산단분기는 `PRI-8601`(P4)·`POI-8601`(V4)이다. HEAD는 V2/V4만 번호가 엇갈려 있었다.
- 엑셀의 설명 열도 `POI-8601` = "국가산단밸브 개도", `POI-8600` = "지방산단밸브 개도"이다.
- 제어 판단 엔진이 `"national_valve": "891-365-POI-8601"` 로 쓴다(`epa/epanet_gunsan/main_5min.py:47`).
- SI 관망해석의 오류 메시지가 "국가산단밸브: … (891-365-POI-8601)"이다(`docs/gunsan-si-valve-opening-analysis.md:21`).
- 교체본 `taglist.py:297-299` 주석에 "태그리스트에 V2/V4가 서로 뒤바뀌어 등록돼 있었다(사용자 확인, 2026-09-17)"라고 적혀 있다.

### 8.3 이미 학습된 모델에 미치는 영향

모델은 태그명이 아니라 **변수명(V2/V4)** 으로 입력을 받는다. 태그리스트가 "V2 = 어느 태그"를 정하므로, 매핑이 바뀌면 같은 모델에 다른 물리량이 들어간다.

| 모델 | 학습 시점 | 학습 때 V2에 들어간 값 | 교체본 태그리스트로 추론할 때 V2에 들어가는 값 |
|---|---|---|---|
| `runs/gu_db_noq8_h6`(5분) | 2026-09-14 | `POI-8601`(국가산단, 13~64%대로 움직임) | `POI-8600`(지방산단, 98.5~99% 부근 고정) |
| `runs/gu_db_1min_h30`(1분) | 2026-09-28 | **새 매핑**(`POI-8600`). `feature_pipeline.joblib` 의 V2 scaler 범위가 98.49~98.99, V4 는 11.2~60.4 다(§9.2에서 컨테이너 안에서 로드해 확인) | 새 매핑 |

5분 모델에 교체본 태그리스트를 쓰면 V2·V4 입력이 서로 바뀌어 들어간다. V2·V4에서 파생되는 `V2_diff*`·`V4_diff*` feature도 함께 바뀐다.
이번 조치(§9 E)로 배포 모델을 1분 모델로 바꿨으므로 운영 경로에서는 이 문제가 없어진다. 5분 모델을 다시 쓸 경우에만 해당한다.
1분 모델은 V2/V4 scaler 범위로 볼 때 교체본 매핑으로 학습됐다(위 표). 배포 태그리스트와 일치한다.

### 8.4 아직 옛 매핑으로 남아 있는 곳

`taglist/GU_network_topology.md:28-29, 64, 69` 는 여전히 V2 = `POI-8601`, V4 = `POI-8600` 이다. `taglist.py` 주석은 이 문서를 "사람이 읽고 고치는 원본"이라고 적고 있어서, 엑셀과 문서가 서로 어긋난 상태다(동작에는 영향 없음).

---

## 9. 후속 조치 (2026-09-28)

| 항목 | 조치 | 위치 |
|---|---|---|
| A | 함열 태그 접두·접미 제거: 엑셀 B5·B6 (`740-914-FRI-1001`, `740-914-PRI-1009`), 주석 예시, 토폴로지 문서 표. 개발서버 최근 구간은 접두 없는 표기가 살아 있다(§3.1) | `taglist/GU_taglist.xlsx`, `src/deepems/{analyze,taglist}.py`, `taglist/GU_network_topology.md` |
| B | 39c9d88 재적용. `prdct_value_from` 기본값은 `VALUE_1min` 으로 변경. 행 키 일관성 검사, 미리보기 CSV 열, 로그 포함 | `scripts/harness/upload.py`, `scripts/harness/schedule.py`, 배포 JSON 2개 |
| C | 군산 개발서버 `TB_CTR_TNK_RST` 에 `VALUE_1min/5min/15min/30min FLOAT NULL` 추가(`ALGORITHM=INSTANT`, 행 수 2,987,053 변동 없음) | DB `<internal-host> / ems_db` |
| E | 배포 모델을 1분 모델로 교체: `runs/gu_db_1min_h30`, `configs/gu_db_1min_h30.yaml`, `models/offline_artifacts_1min.joblib`. 반출 스크립트에 아티팩트 이름 대조 추가 | `deploy/gunsan/docker-compose.prod.yml`, `deploy/gunsan-shadow/docker-compose.shadow.yml`, `deploy/gunsan/build-and-save.ps1`, `deploy/gunsan/load-and-up.sh` |
| 문서 | readme의 DROP 후 재생성 안내를 ALTER 방식으로 되돌리고 `PRDCT_VALUE` 를 포함. 실행 예시를 1분 모델로 변경 | `readme.txt` |

`PRDCT_VALUE` = `VALUE_1min` 이 무엇을 담는지: 교체본의 persistence 대체(§2.2) 때문에 **H3를 뺀 target은 origin 시점 값(보간 후)** 이고, `Q_GunS` 는 여기에 Stage3 추천 조정값을 더한 값이다. H3만 모델 예측값이다.

아직 반영하지 않은 것: 입력 결측 진단(§3.4), 운영 DB 컬럼 추가.

### 9.1 조회 분할과 주기 고정 (2026-09-28)

**조회 분할** — 사이클에서 21일 이력이 필요한 건 H7 목표범위(`analysis.py` `compute_target_band`) 하나뿐인데, 그 때문에 모든 태그를 22일치씩 받고 있었다. 지금은 두 번에 나눠 받는다.
- 전체 태그: `preprocess.feature_lookback_minutes()` = (입력 360 + 레버 변화량 30 스텝) × 1분 + ffill 10분 + 여유 60분 = **460분**
- H7 원본 태그(H7_1/H7_2)만: 목표범위 21일 + 1일 (`preprocess.fetch_level_history()`)
- `analysis.run_cycle(level_history=...)` 가 목표범위를 이 시계열로 계산한다.
- `--lookback-days` 를 주면 예전처럼 한 번에 받는다(되돌리기 스위치).

조회 시작점에 영향받는 처리는 셋이다. 입력 윈도우, `diff(30)`(앞에 과거가 없으면 0으로 채움, `data.py:204`), ffill/보간(10스텝)이다. 그래서 최소 길이는 400분이다.

**동일성 검증** (개발서버 실데이터, 2026-08-17~08-24):

| 비교 | 결과 |
|---|---|
| 360분만 조회 (입력 길이만) | 20개 origin **모두 불일치** — `Q_GunS_diff30` 최대 386 차이 등 레버 변화량 입력이 달라짐 |
| 400분 / 460분 조회 | 20개 origin **모두 일치** — Stage1 입력 360스텝, 유효 판정, origin, 목표범위(하한·상한·표본수), H7/Q7/O7 최근 61스텝, 현재 시점 값 |
| 실제 구현(`preprocess.fetch_window` + `fetch_level_history`) | 3개 시점 모두 일치. 받은 행 **696,926 → 73,478**, 조회+전처리 **4.5~5.7초 → 0.6초** (이 PC → 개발서버) |

개발서버에서 데이터가 전혀 없는 입력 태그 7개(§3.1)는 비교에서 뺐다. 레버가 크게 움직인 origin 5개를 일부러 포함했다.

**주기 고정** (`schedule.py`) — 되돌아갔던 6241aa5·8178bc1 의 벽시계 정렬(`_seconds_until_next_slot`), 조회 끝 격자 고정(`window_end = floor(freq) + freq`), "격자 어긋남" 경고, 사이클 소요시간 로그, `--cycle-lag-seconds`(기본 30초)를 되살렸다. prod와 dev-server에 모두 적용했다.
예전 식 `interval - now % interval + lag` 에는 구멍이 있었다. 사이클이 경계를 넘긴 뒤 lag 안에 끝나면 이번 슬롯을 건너뛴다. 1분 주기에서는 사이클이 30초만 넘어도 한 칸씩 빠지므로, "지금 이후 가장 가까운 `경계 + lag`"로 바꿨다.
`--cycle-lag-seconds` 가 0 미만이거나 주기 이상이면 기동 시 거부한다. 5분 모델을 60초로 돌리는 경우처럼 주기가 모델 freq보다 짧으면 격자 경고를 끈다.

가짜 시계 시뮬레이션 (600사이클, 60초 주기, lag 30초) — 빠진 분 수:

| 사이클 소요 | 새 식 | 예전 식 | 교체본 `sleep(60)` |
|---|--:|--:|--:|
| 5초 | 0 | 0 | 50 |
| 40초 · 55초 | 0 | 598 | — |
| 5~50초 무작위 | 0 | 267 | — |
| 100회 중 1회 75초 | 5 | 5 | — |

주기(60초)보다 긴 사이클은 어느 식으로도 한 칸이 빠진다. 그때는 "격자 어긋남" 경고가 남는다.

전체 사이클 실행은 §9.2에서 확인했다(ems-predict 이미지 + 개발서버 + 더미 계측값).

### 9.2 1분 사이클 소요시간 시나리오 테스트 (2026-09-28)

**질문**: 조회 → Stage1 추론 → Stage3 추천 → `TB_CTR_TNK_RST` 업로드까지 한 사이클이 60초 주기 안에 끝나는가.

**조건**

| 항목 | 값 |
|---|---|
| 실행 | `swtp-gunsan/ems-predict:20260928` 이미지. 이미지는 조회 분할 이전(09:37) 빌드라 현재 `src/ scripts/ configs/ taglist/` 를 마운트해 덮었다 |
| 인자 | `--mode dev-server --stage1-run-dir runs/gu_db_1min_h30 --source-cfg configs/gu_db_1min_h30.yaml --offline-artifacts models/offline_artifacts_1min.joblib --device cpu --cycles 10 --interval-seconds 60` (lag 기본 30초) |
| 자원 | `--cpus 1`, `OPENBLAS/OMP/MKL/NUMEXPR_NUM_THREADS=1`, `seccomp=unconfined` — 운영 compose(`deploy/gunsan/docker-compose.prod.yml:223-238`)와 같은 스레드 설정에 CPU 1개 제한을 더했다 |
| DB | 원본 읽기·업로드 모두 군산 개발서버 `<internal-host> / ems_db`. 업로드 테이블 `TB_CTR_TNK_RST`, `prdct_value_from=VALUE_1min` |
| 접속정보 | `epa/connections.gunsan.json` 의 `maria-ems-db-gu-test` 로 임시 JSON 을 만들어 마운트했고, 끝난 뒤 지웠다 |

**더미 계측값** (`TB_RAWDATA`, `SERVER='DUMMY_PRED'`, `INSERT IGNORE` 라 기존 행은 보존)

| 대상 | 방법 | 구간 | 행 수 |
|---|---|---|--:|
| 입력 태그 20개 (H7_1/H7_2, 합성 7개 제외) | 개발서버 실측을 **정확히 36일 뒤로 옮겨** 서버 쪽 `INSERT … SELECT` 로 복사했다. 날짜 단위로 옮겨 `hour_sin/cos` 와 하루 주기가 맞는다 | 09-28 07:50 ~ 18:10 | 8,784 |
| `H7_1`, `H7_2` | 같은 방식. 목표범위 조회량(22일)을 운영과 같게 하려고 넣었다 | 09-06 00:00 ~ 09-28 18:10 | 65,538 |
| `H7_3`~`H7_8` | 개발서버에 실측 없음. 재생한 `H7_1` 에 태그별 오프셋(−0.03~+0.03)과 노이즈(σ 0.004)를 더했다 | 09-28 07:50 ~ 18:10 | 3,720 |
| `O9` | 개발서버에 실측 없음. 학습 범위(0~178.9) 안에서 90 ± 35 하루 주기 + 노이즈(σ 3)로 합성했다 | 같음 | 620 |

값이 일정한 합성값은 쓰지 않았다. stuck 보간에 걸리면 NaN이 되어 추론이 예외로 끝나기 때문이다.
입력 태그 20개 중 16개는 10:02~13:47 구간에 이미 `DUMMY_SIM`·`DUMMY_DEV` 행이 있었고, 이 행들이 그대로 남았다(`INSERT IGNORE`). 적재 뒤 29개 태그 모두 `[지금 − 460분, 지금)` 구간이 460/460 이었다.

**결과**

| 사이클 | origin | 업로드 행 | 소요 |
|--:|---|--:|--:|
| 1 | 16:52 | 18 | 2.7초 |
| 2 | 16:53 | 18 | 5.3초 |
| 3 | 16:54 | 18 | 2.1초 |
| 4 | 16:55 | 18 | 1.1초 |
| 5 | 16:56 | 18 | 1.1초 |
| 6 | 16:57 | 18 | 2.0초 |
| 7 | 16:58 | 18 | 1.1초 |
| 8 | 16:59 | 18 | 1.0초 |
| 9 | 17:00 | 18 | 1.0초 |
| 10 | 17:01 | 18 | 1.0초 |

- 최대 5.3초, 평균 1.8초(합 18.4초 / 10회). 60초 주기에서 사용률은 10% 미만이다. 모델 로드는 루프 밖이라 포함되지 않는다(운영도 같다).
- 사이클 실패 0회. 컨테이너는 exit 0으로 끝났다.
- 격자: 18개 DSTRB_ID마다 `RGSTR_TIME` 16:52~17:01이 10행씩 있다. 빠진 분이 없다.
- 업로드 값: 180행 모두 `PRDCT_VALUE` = `VALUE_1min` 이고, 0이나 NULL은 없다. `VALUE_30min` NULL도 0행이다.
- 매 사이클 Stage3 결과는 "lower, achievable=False" 였다. 더미의 H7(4.22)이 목표범위 상한(4.18)보다 높기 때문이다. 판단 품질은 이 테스트의 범위가 아니다.

**한계**
- 개발서버 `TB_RAWDATA` 는 운영보다 작고, 네트워크도 사무실 PC → 개발서버 경로다. 운영에서는 첫 기동 로그의 `[prod] 업로드 완료 … 초 소요` 로 다시 확인해야 한다.
- PK가 `(TS, TAGNAME)` 순서라 조회 성능은 TS 범위 조건에 달려 있다. 사이클 조회는 항상 TS 범위를 거므로 해당하지 않는다. 다만 TS 조건 없이 `TAGNAME` 만으로 조회하면 개발서버에서도 시간 초과가 났다(이번 준비 작업 중).

**정리**: 더미 78,662행은 태그·시각 조건으로 지웠다(남은 행 0). 업로드된 예측 180행(`RGSTR_TIME` 09-28 16:52~17:01)은 확인용으로 남겨 두었다. 지우려면 다음을 실행한다.
`DELETE FROM TB_CTR_TNK_RST WHERE RGSTR_TIME BETWEEN '2026-09-28 16:52' AND '2026-09-28 17:01' AND DSTRB_ID LIKE '%\_Predict';`
Q2·Q7은 gunsan-epa-dummy 더미와 DSTRB_ID가 같다. 하지만 그 더미는 13:47까지만 있어서 이 구간과 겹치지 않는다.

### 9.3 수요예측 → PRE 관망해석 1분 연계 (2026-09-28)

**배경**: 고객은 수요예측뿐 아니라 PRE 관망해석(`epa/epanet_gunsan/main_epa_gs.py`)도 1분마다 결과를 쌓기를 원한다.
그런데 PRE 루프는 5분으로 고정돼 있었다. 슬롯은 `% 5`로 계산했고, 다음 슬롯은 `+5분`, 예측 기준은 `floor_to_5min` 이었다.

#### (A) 가능성 측정 — 코드 수정 없이

수요예측을 1분 주기(§9.2와 같은 조건)로 돌리면서, 매분 :45초에 PRE를 한 번씩 실행했다(`--snapshot --ts <그 분 :45> --no-save-db`, 이 PC의 로컬 파이썬, 12회).

| 항목 | 결과 |
|---|---|
| 성공 | 12/12 |
| 입력 예측 | 매회 **같은 분에 올라온 예측**(`Q2_Predict`·`Q7_Predict` RGSTR_TIME = 그 분)을 잡았다 |
| PRE 소요, 프로세스 기동 포함 | 평균 7.2초 (5.3~11.3초) |
| PRE 소요, 엔진 내부(`ELAPSED`) | 평균 5.8초 (4.1~9.9초) |
| 같은 시간대 수요예측 사이클 | 0.9~2.7초 (15회) |

수요예측(매분 :30초 기동, 약 1~3초)과 PRE(:45초 기동, 약 2~11초)는 둘 다 1분 안에 끝난다.

#### 주기 조정 옵션 추가

`main_epa_gs.py` 에 다음을 넣었다. **기본값은 예전 동작과 같다.**

| 옵션/상수 | 내용 |
|---|---|
| `--interval-min` | PRE 주기. 1/2/3/5/10/15 중 하나, 기본 5. 60의 약수만 받는다. 경계를 "분 % 주기"로 잡기 때문이다 |
| `--schedule-offset-sec` | 주기 경계 뒤 실행 시점(초). 주면 `--schedule-offset-min` 대신 쓴다. 1분 주기에서는 필수다. 오프셋이 0 이상 주기 미만이 아니면 기동 시 거부한다 |
| `--schedule-offset-min` | 기본 1은 그대로다. `choices 0~4` 제한 대신 "주기 미만" 검사로 바꿨다 |
| `MO_INTERVAL_MIN = 5` | CUR 원본 MO의 격자. MO 루프(`epanet_mo_gs.py`)는 5분 고정이다 |
| 결과시각 | 실행 슬롯의 분(`result_ts`)이다. :45초에 깨어나도 결과는 그 분으로 쌓인다. 분 오프셋이면 예전과 같다 |

기본값 동일성: 하루치 시각 61,715개(7초 간격 × 오프셋 0~4분)를 넣어 보니, 슬롯·MO 원본 시각·예측 기준 모두 예전 식과 **전부 일치**했다.

1분 운영 예: `python main_epa_gs.py --interval-min 1 --schedule-offset-sec 45`.
배포 compose(`deploy/gunsan/docker-compose.prod.yml` 의 `ems-epa-pre`)는 바꾸지 않았다. 지금은 `--schedule-offset-min 2`(5분 주기)이다.

**주의**: `main_epa_gs.py` 는 벤더가 파일째 새로 주는 엔진이다. 드롭을 받을 때마다 이 옵션을 다시 적용해야 한다.

#### (B) 저장 모드 1분 루프 — 사용자 요청으로 도중 종료

세 프로세스를 함께 돌렸다. 수요예측 1분(컨테이너), MO 5분 루프(저장), PRE `--interval-min 1 --schedule-offset-sec 45`(저장)이다.
PRE 12회를 계획했으나, 3회 저장 뒤 사용자 요청으로 모두 멈췄다.

| 결과시각 | PRE `ELAPSED` | `TB_TOT_ALG` | `TB_FP_VAL` / `TB_FR_VAL` |
|---|--:|---|---|
| 17:51 | 10.5초 (첫 회차) | PRE + CUR(MO 17:50 복사) | PRE 236 / 229, CUR 14 / 6 |
| 17:52 | 1.9초 | PRE + CUR(MO 17:50 복사) | 같음 |
| 17:53 | 1.9초 | PRE + CUR(MO 17:50 복사) | 같음 |

- 결과가 1분마다 빠짐없이 쌓였다. 17:51·17:52·17:53에 SKIP이나 실패가 없었다.
- 상주 루프에서는 두 번째 회차부터 1.9초였다. snapshot 단발 실행(A)보다 빠르다. 매번 파이썬·wntr을 새로 띄우지 않기 때문으로 보인다.
- CUR은 세 회차 모두 같은 MO(17:50) 값이다. MO가 5분 격자이기 때문이며, 설계대로다. CUR을 1분 단위로 새로 계산하려면 MO 루프도 바꿔야 한다(`epanet_mo_gs.py`, 이번 범위 밖).
- PRE 수요로 들어간 `PRDCT_VALUE` 는 `VALUE_1min` 이다. §9 끝의 설명대로 H3를 뺀 target은 origin 시점 실측값(persistence)이다. 그래서 1분 PRE는 "예측 해석"보다 "현재 상태 해석"에 가깝다. 예측 기반을 원하면 `prdct_value_from` 을 `VALUE_5min` 등으로 바꿀지 정해야 한다(**미결정**).

**정리**
- 더미 `TB_RAWDATA` 는 이번에 넣은 것만 지웠다. `DUMMY_PRED` 80,782행 전부, `DUMMY_SIM` 7,921행이다. 이전 세션의 `DUMMY_SIM`(10:02~13:47)은 남아 있다.
- 결과 행은 확인용으로 개발서버에 남겨 두었다.
  - `TB_CTR_TNK_RST` 예측: 17:36~17:54
  - `TB_TOT_ALG`·`TB_FP_VAL`·`TB_FR_VAL`: PRE·CUR 17:51~17:53
  - `TB_TOT_ALG`·`TB_FP_SI_VAL`·`TB_FR_SI_VAL`: mo 17:50
- 지우려면 테이블별로 `RGSTR_TIME BETWEEN '2026-09-28 17:50' AND '2026-09-28 17:54' AND FLG IN ('PRE','CUR','mo')` 조건을 쓴다. 예측은 §9.2와 같은 조건에 구간만 바꾼다.
- 로컬 엔진 로그 `epa/epanet_gunsan/logs/{pre,mo}_20260928.txt` 가 새로 생겼다(추적 대상 아님).

### 9.4 `main_epa_gs.py` 벤더 드롭 재적용 (2026-09-30)

2026-09-30 10:19 에 `epa/epanet_gunsan/main_epa_gs.py` 가 통째로 바뀌었다(348+/331-). 우리 커밋 위의 패치가
아니라 벤더 기준본 덮어쓰기라, 새 기능 하나를 빼면 나머지 차이는 전부 우리 수정의 회귀였다.

**벤더가 새로 넣은 것 (유지)**

| 항목 | 내용 |
|---|---|
| `latest_complete_mo_source_ts()` | CUR 원본 MO 를 "슬롯을 5분으로 내림한 정확한 시각"이 아니라 **슬롯 이전의 가장 최근 완성 MO** 로 고른다. 완성 = `TB_TOT_ALG`·`TB_FP_SI_VAL`·`TB_FR_SI_VAL` 세 곳에 같은 `RGSTR_TIME` 의 `FLG='mo'` 행이 있는 것 |
| `--mo-max-age-min` (기본 10) | 그 MO 가 슬롯보다 이만큼 오래됐으면 예외 → 그 회차 SKIP. MO 가 멈췄을 때 옛 결과를 계속 CUR 로 복사하는 것을 막는다 |

예전 `expected_mo_ts_for_slot()`(5분 내림)은 이 함수로 대체했다. 1분 주기에서도 "슬롯 이전 최근 MO" 가 5분 격자
값으로 수렴하므로 `--interval-min` 과 충돌하지 않는다. MO 원본 조회이므로 `--result-table-suffix` 를 씌우지 않는다.

**되돌아간 것과 재적용**

| # | 항목 | 드롭 상태 | 근거 | 재적용 |
|---|---|---|---|---|
| A | 테이블명 | 소문자 9종 39곳 | 800e9d5 | 대문자. 주석·`--help`·출력 라벨 포함 |
| B | `--interval-min` / `--schedule-offset-sec` / `floor_to_interval` / `MO_INTERVAL_MIN` / `result_ts` | 삭제, 5분 고정 | 92bde50, §9.3 | 복원. `--schedule-offset-min` 의 `choices 0~4` 는 다시 "주기 미만" 검사로 |
| C | `--prediction-table` / `--result-table-suffix` / `configure_tables` / `result_table()` | 삭제 | 1b13a11 | 복원. 저장 SQL 6곳 + `latest_processed_pre_ts` f-string |
| D | 함열 유량 태그 | `SS.740-914-FRI-1001` | 1bb2682, §3.1 | `740-914-FRI-1001` |
| E | 지방산단밸브 임계값 | 98 | 5e5705a | 95 |
| F | `--inp` 기본값 | `gs_0909.inp`(리포에 없음) | — | `epa_model.inp` |
| G | 덕암·신관·옥석 압력 태그 | `701-365-PRI-*` | 8178bc1, 사용자 확정 2026-09-30 | `701-367-PRI-*`. PRE 는 이 태그를 읽지 않아(`fetch_readings` 호출처 없음) 동작 영향은 없다 |

드롭 자체의 사소한 문제: `run_once()` 의 docstring 이 첫 문장 뒤에 있어 그냥 문자열 식이었다. 첫 줄로 올렸다.
`--schedule-offset-sec` help 의 `—`(U+2014)는 cp949 콘솔에서 `UnicodeEncodeError` 를 내므로(`logs/pre_20260929.txt`
의 FAIL 원인) `,` 로 바꿨다. 컨테이너(UTF-8)에서는 무관하다.

**검증**

| 항목 | 결과 |
|---|---|
| 회귀 grep(`98\.0`, `SS\.740`, `701-365`, `gs_0909`, `\btb_[a-z_]*\b`) | 0건 |
| `ast.parse` | 통과 |
| `--help` | compose 가 넘기는 인자 6종(`--interval-min`, `--schedule-offset-sec`, `--schedule-offset-min`, `--prediction-table`, `--result-table-suffix`, `--mo-max-age-min`) 모두 인식 |
| 인자 검증 | `--prediction-table 'bad;name'` 거부, `--interval-min 4` 거부 |
| 슬롯 함수 | 하루치 7초 간격 × (5분/60초, 1분/45초, 5분/120초, 1분/50초) = 49,372건, HEAD 와 불일치 0 |
| 개발 DB 스냅샷 1회 | **미검증** — 2026-09-30 오전 `<internal-host>` 가 ping·3306 모두 무응답 |
| `latest_complete_mo_source_ts` EXPLAIN | **미검증** — 같은 이유. `TB_FP_SI_VAL`/`TB_FR_SI_VAL` 에 `(RGSTR_TIME, FLG)` 인덱스가 없으면 매 회차 풀스캔이 될 수 있다. DB 가 열리면 `SHOW INDEX` 와 `EXPLAIN` 으로 확인할 것 |

반출본 재빌드는 하지 않았다. 다음 빌드부터 이 파일이 들어간다.

---

## 10. 관찰 기록 (본 문서에서 수정하지 않음)

| 위험 | 위치 | 사실 |
|---|---|---|
| 높음 | `taglist/GU_taglist.xlsx` (Q_Ham, P_Ham) | `SS.…F_CV` 표기로 돌아갔다. 우리 DB 실측은 접두 없는 이름이다 |
| 높음 | `scripts/harness/upload.py:267` | INSERT 컬럼에 `PRDCT_VALUE` 가 없고 REPLACE INTO이다 |
| 높음 | `scripts/harness/upload.py:101-103` | `VALUE_1min`·`VALUE_15min` 이 필요하다. 운영 DDL 안내는 docstring에만 있다 |
| 중간 | `taglist/GU_taglist.xlsx` (V2, V4) + `runs/gu_db_noq8_h6` | 매핑 정정은 맞지만, 배포 모델은 옛 매핑으로 학습됐다 |
| 중간 | `scripts/harness/schedule.py:266-289, 376` | 벽시계 정렬과 격자 고정이 사라졌고, prod 기본 주기는 60초 |
| 중간 | `deploy/gunsan/docker-compose.prod.yml:262-265` | 5분 모델이 고정돼 있어 교체본의 1분 전제와 어긋난다 |
| 낮음 | `src/deepems/infer.py:87, 93`, `scripts/harness/preprocess.py` | 결측 태그 진단이 사라졌다 |
| 낮음 | `readme.txt` | "CREATE TABLE IF NOT EXISTS로 자동 생성" 안내가 코드와 모순된다. DROP 후 재생성을 안내한다 |
| 낮음 | `README.md` | Docker 절이 삭제됐고, 준비 항목의 스키마가 옛 것이다 |
| 낮음 | `configs/gu_db_1min_h30.yaml` vs `runs/gu_db_1min_h30/config.json` | `end_date` 가 다르다(yaml `2026-09-01`, 학습 `null`) |
| 정보 | `src/deepems/recommend.py:449-1017` | 새 H3 추천 함수는 호출처가 없다 |
| 정보 | `src/deepems/config.py:324, 398` | scaler_type·time-decay는 기본값이 꺼져 있고, 어떤 yaml도 켜지 않는다 |
