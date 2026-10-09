# 군산 5분 제어 판단(main_5min.py) 2026-09-30 벤더 드롭 — 무엇이 바뀌었고 무엇이 되돌아갔나

- **대상**: 2026-09-30 작업 트리에 들어온 `epa/epanet_gunsan/main_5min.py` 교체본(+357 / −51, HEAD f708416 대비).
- **비교 기준**: HEAD `1b13a11`(2026-09-29, 섀도우 테이블 옵션 추가). 이 파일을 건드린 우리 커밋은 `f5523b4` → `1b13a11` 둘이다.
- **성격**: 사실 확인 + 재적용 기록. 벤더 변경분은 그대로 두고(§3), 사라진 우리 옵션만 다시 얹었다(§6.1). 지방산단 밸브를 다시 제어 대상으로 넣는 결정과 BE 확장은 `docs/gunsan-ctrl-cmd-consumer.md` 결정 9 에 있다.
- 라인 번호는 **재적용 뒤 작업 트리** 기준이다(재적용으로 `:26` 이후가 HEAD 대비 +19줄 밀렸다). 따로 적지 않으면 `epa/epanet_gunsan/main_5min.py` 다.

---

## 1. 결론 요약

이 드롭은 패치가 아니라 **파일 통째 교체**다. 우리 커밋 `1b13a11` 이전 코드를 바탕으로 만들어져, 벤더 신기능이 들어오면서 우리가 넣은 섀도우 테이블 옵션이 함께 사라졌다(메모리에 적어 둔 회귀 패턴 7번이 그대로 재현됐다).

| # | 현상 | 영향 | 근거 |
|---|---|---|---|
| A | **지방산단 분기밸브(`891-365-POI-8600`) fallback 제어 부활** | 판단 행에 `LOCAL_*` 5컬럼을 다시 쓴다. BE 가 처리하지 않으면 영원히 `READY` 다 → BE 확장으로 해결(결정 9) | §2.1, §4.1 |
| B | **`TB_CTRL_RULE_CFG` 필수 키 8개 추가** | 하나라도 없으면 `RuntimeError` 로 **매 사이클 실패**. 규칙은 섀도우도 운영 테이블을 읽으므로 운영·섀도우 동시 영향 | §2.3 `:226-237` |
| C | **`TB_CTRL_CMD_RST` INSERT 에 `LOCAL_*` 5컬럼** | 컬럼이 없으면 INSERT 실패. `_SH` 는 `LIKE` 로 만들었으니 운영에 있으면 같이 있다 | §2.4 `:1820-1824`, `:1854-1858` |
| D | **오식도 유출유량 `891-365-FRI-8653` 신규 입력** | 결측이면 `OSIK_OUTFLOW_MISSING` 만 남기고 폴백. 실패 원인은 아니다. 리포 어디에도 이 태그가 없고 더미 시더도 만들지 않는다 | §2.2 `:1152-1153` |
| E | **섀도우 테이블 옵션 회귀**(`--prediction-table`/`--cmd-table`/`configure_tables`/잠금 분리/기동 로그) | 섀도우 compose `ems-ctrl` 이 인자 오류로 재시작만 반복(운영 행은 안전). 누가 인자를 지우면 섀도우 추천이 운영 `TB_CTRL_CMD_RST` 로 들어가 운영 BE 가 실제 제어로 보낸다 → **재적용 완료**(§6.1) | §3 |
| F | 회귀 grep 4종은 깨끗 | `—`(U+2014) 0건, `701-365` 0건, 소문자 테이블명 0건, `98.0` 0건. `py_compile` OK | §7 |

**미확정(개발 DB `<internal-host>` 연결 시간 초과로 확인 못 함)**: B 의 규칙 키 존재 여부, C 의 컬럼 존재 여부(워크플로 HTML P14 는 "DDL 에 남아 있다", `docs/gunsan-ctrl-cmd-consumer.md:261-266` 의 `SELECT *` 결과에는 없었음 → 서로 어긋난다), D 의 태그 적재 여부. §5 의 SQL 로 현장에서 확인한다.

---

## 2. 새로 들어온 것

### 2.1 지방산단 분기밸브 fallback 제어

판단 우선순위가 "펌프 Hz → 국가산단 밸브 → **지방산단 밸브(최종)**" 로 바뀌었다(`--help` 설명 `:1923`). 지방산단은 나운 배수지 고수위를 다른 수단으로 못 잡을 때만 닫는다.

| 단계 | 조건 | 방향 | REASON | 근거 |
|---|---|---|---|---|
| 조건부 CLOSE | 나운 > `LOCAL_TRIGGER_LEVEL`(주석 4.30m) 이고 ≤ 강제선, 상승 추세, **선행제어 완료** | −`LOCAL_VALVE_STEP` | `LOCAL_FALLBACK_CLOSE` | `:1436-1441` |
| 강제 CLOSE | 나운 > `LOCAL_FORCE_CLOSE_LEVEL`(주석 4.35m) | −STEP, 10분 시퀀스 우회 | `LOCAL_FORCE_CLOSE` | `:1435`, `:1472-1474` |
| 원복 OPEN | 지방산단 제어 이력이 있고 개도 < MAX−0.5, 나운 ≤ `LOCAL_RECOVERY_LEVEL`(주석 4.25m) 이 `LOCAL_RECOVERY_STABLE_MIN`(주석 10분) 동안 안정/하강 | +STEP | `LOCAL_RECOVERY_OPEN` | `:1445-1468`, `naun_recovery_stable` `:909-931` |

- **선행제어 완료**(`naun_relief_control_completed` `:882-906`): 펌프 Hz DOWN(−1) 또는 국가산단 OPEN(+1) 명령이 **`APPLIED`** 이고 `OBSERVE_UNTIL` 이 지났으며, 그 뒤 `CONTROL_CYCLE_MIN×2` 분 안이어야 한다. `APPLIED` 만 보는 근거 조회는 `get_last_applied_device_command` `:709-731` 이다.
- **원복 판단의 "제어 이력"** 은 마지막 `APPLIED` 지방산단 행의 `REASON_CODE` 에 `LOCAL_FALLBACK_CLOSE`/`LOCAL_FORCE_CLOSE`/`LOCAL_RECOVERY_OPEN` 토큰이 있는지로 본다(`:1443-1451`). 그래서 이 토큰은 `prepend_reason` 으로 앞에 보존한다(`:1710`, 100자 절단 `:1731`).
- 시퀀스·반응 확인은 국가산단과 같은 뼈대다: `sequence_allows_control(device="local")`, `response_ok_for_local_valve` `:836-862`(나운 유입유량 `FRI-8600` + 나운 수위 추세), `LOCAL_WAIT_OPEN/CLOSE/HOLD` 토큰, `LOCAL_POST_CONTROL_HOLD` `:1720`.
- 게이트 사유: `LOCAL_OBSERVE`/`LOCAL_FORCE_OBSERVE`(관찰 중, `:1653`), `LOCAL_DATA_CHECK`(개도 결측), `LOCAL_RANGE_CHECK`(`LOCAL_VALVE_MIN~MAX` 밖, `:1661`), `LOCAL_NO_RESPONSE`/`LOCAL_RESPONSE_CHECK`, `LOCAL_LIMIT`.
- `local_danger`(`:1472-1474`) = 강제 CLOSE, 또는 원복 OPEN 인데 나운이 DANGER_LOW 방향인 경우. 이때만 10분 방향확인 시퀀스를 우회한다.

### 2.2 오식도 유량수지 보조지표

`FRI-8652`(유입) − `FRI-8653`(유출) 을 `osik_flow_balance` 로 계산한다(`:1269-1275`).

- 배분 판단 강화(`:1324-1337`): 나운↓ 이고 (오식도 수위 상승 **또는** 오식도 고수위 방향(`direction=-1`)+수지 흑자) 이면 국가산단 CLOSE. 반대로 나운↑ 이고 (오식도 하강 **또는** 저수위 방향(`direction=1`)+수지 적자) 이면 OPEN. 수지 **단독으로는 제어하지 않는다**(주석 `:1322`, docstring `:804`).
- 반응 확인(`response_ok_for_national_valve` `:793-833`): 유입·유출이 모두 있으면 수지 변화로, 유출이 없으면 예전처럼 유입 변화로 판단한다.
- 결측 처리: `must_have` 에는 넣지 않았다(`:1136-1143`). 없으면 `OSIK_OUTFLOW_MISSING` 만 남기고 계속 간다(`:1152-1153`).
- 사유 토큰 `OSIK_BALANCE_SURPLUS`/`OSIK_BALANCE_DEFICIT` 가 배분 사유에 덧붙는다(`:1343`, `:1353`). `result` JSON 에도 `osik_*` 6개 항목이 늘었다(`:1790-1799`).

### 2.3 규칙 키 8개 (`TB_CTRL_RULE_CFG`, 필수)

`load_rules` 의 `required` 목록(`:217-234`)에 추가됐다. 없으면 `RuntimeError("… 필수 설정값 누락: …")` (`:237`).

| 키 | 쓰는 곳 | 코드 주석의 의도값 |
|---|---|---|
| `LOCAL_VALVE_MIN`, `LOCAL_VALVE_MAX` | 범위 검사 `:1657-1661`, 목표 클램프 `:1697-1700`, 원복 허용 조건 `MAX−0.5` `:1450` | 미확정 |
| `LOCAL_VALVE_STEP` | 1회 이동량 `:1696` | 주석 "5%p" |
| `LOCAL_VALVE_OBSERVE_MIN` | `LOCAL_OBSERVE_UNTIL` `:1701-1703` | 미확정(국가산단은 `VALVE_OBSERVE_MIN`) |
| `LOCAL_TRIGGER_LEVEL` | 조건부 CLOSE 하한 `:1437` | 주석 4.30m |
| `LOCAL_FORCE_CLOSE_LEVEL` | 강제 CLOSE `:1435` | 주석 4.35m |
| `LOCAL_RECOVERY_LEVEL` | 원복 `:1428` | 주석 4.25m |
| `LOCAL_RECOVERY_STABLE_MIN` | 원복 안정 시간 `:1429` | 주석 10분 |

값은 벤더가 넣어야 한다(리포에 규칙 시드가 없다. `docs/sql/gunsan_ctrl_cmd.sql:16` 이 벤더 소유로 명시). `LOCAL_VALVE_MIN/MAX` 가 실측 개도 범위(2026-08-24 실측 95.37 %, 더미 96~100)를 포함하지 않으면 매번 `LOCAL_RANGE_CHECK` 로 끝난다.

### 2.4 결과 행·로그

- INSERT 컬럼 `LOCAL_CMD_YN, LOCAL_CMD_STATUS, LOCAL_CUR_OPEN, LOCAL_TGT_OPEN, LOCAL_OBSERVE_UNTIL` 추가(`:1820-1824`, 값 `:1854-1858`, 플레이스홀더 한 줄 `:1836`).
- 행 단위 `CMD_YN` 은 세 장치 중 하나라도 `Y` 면 `Y` (`:1723-1727`).
- 로그 한 줄이 `CTRL_TS=… CMD=… PUMP=… LOCAL=… NATIONAL=… REASON=…` 로 바뀌었다(`:1761`). 운영·섀도우 README 의 로그 예시를 맞췄다.
- 새 태그 2개: `osik_outflow` `891-365-FRI-8653` (`:64`), `local_valve` `891-365-POI-8600` (`:69`). 둘 다 `latest_readings` 조회 대상(`TAGS.values()` 전체 `:1132-1133`)이지만 `must_have` 는 아니다.

---

## 3. 되돌아간 것 (우리 커밋 `1b13a11` 회귀)

| 항목 | HEAD 위치 | 드롭 상태 | 재적용 위치 |
|---|---|---|---|
| `import re` | `:7` | 삭제 | `:7` |
| 주석 블록 + `_TABLE_NAME_RE` + `configure_tables()` | `:28-47` | 삭제 | `:28-45` |
| `--prediction-table` / `--cmd-table` 인자 | `:1600-1609` | 삭제 | `:1946-1955` |
| `main()` 의 `configure_tables` 호출·`ap.error`·기동 로그 "테이블: …" | `:1618-1633` | `args = build_arg_parser().parse_args()` 한 줄로 | `:1965-1979` |

영향: 섀도우 compose `deploy/gunsan-shadow/docker-compose.shadow.yml:200-203` 가 두 인자를 넘긴다. 드롭 그대로 이미지를 말면 `ems-ctrl` 이 인자 오류로 재시작만 반복한다(운영 행은 안전). 인자를 지워서 "고치면" 섀도우 추천이 운영 `TB_CTRL_CMD_RST` 로 들어가 운영 BE 가 AI 운전모드 0 에서 승인 없이 Kafka 로 보낸다. 재적용은 `git show HEAD:… ` 의 원문을 그대로 옮겼고 벤더 코드는 한 줄도 바꾸지 않았다(`git diff` 의 `-` 줄 11개는 전부 벤더가 바꾼 줄이다 — docstring, 유입유량 변수명, 배분 조건 2줄, 로그 포맷, `--help` 설명).

---

## 4. 외부 소비자 영향

### 4.1 BE (`CtrlCmdService`) — 드롭 시점에는 LOCAL 을 모른다

- `DEVICES = [PUMP, NATIONAL]`(`CtrlCmdService.java:44`, 변경 전), 매퍼 `selectReadyCmdList` 도 PUMP/NATIONAL `READY` 만 집는다(`ctrl_cmd_mssql.xml:35-36`, 변경 전).
- 따라서 `LOCAL_CMD_YN='Y'` 행은 BE 가 처리하지 않아 `LOCAL_CMD_STATUS` 가 영원히 `READY` 다. Python 은 선행제어·원복 근거로 `APPLIED` 만 본다(`:709-731`, `:882-906`). 결과: 원복 OPEN 은 발동하지 않고, 강제/조건부 CLOSE 조건이 유지되는 동안 `sequence_allows_control` 이 `INITIAL_CONTROL` 을 반복해 5분마다 `READY` 행이 새로 쌓인다. 행 단위 `CMD_YN=Y` 라 이력 화면 `CMD_ONLY` 필터에도 잡힌다.
- **조치**: 사용자가 2026-09-30 지방산단도 제어 대상으로 확정 → BE·FE 를 3장치로 확장했다. 내용은 `docs/gunsan-ctrl-cmd-consumer.md` 결정 9 와 변경 내역표. 태그는 `LOCAL_OPEN=891-365-POC-8602`, `LOCAL_PULSE=891-365-VVK-8601`, `LOCAL_CLOSE_PULSE=891-365-VVK-8602`(`docs/sql/gunsan_ctrl_cmd.sql` 2·3절).

### 4.2 DDL

- 운영 `TB_CTRL_CMD_RST` 에 `LOCAL_*` 5컬럼이 있어야 INSERT 가 된다. 워크플로 HTML 은 "DDL 에 남아 있다"(P14) 고 적었지만 2026-09-23 개발 덤프의 `SELECT *` 결과행에는 `LOCAL_*` 이 없었다(`docs/gunsan-ctrl-cmd-consumer.md:261-266`). **어느 쪽이 맞는지 미확정** — §5 의 `SHOW COLUMNS` 로 본다.
- 섀도우 `TB_CTRL_CMD_RST_SH` 는 `CREATE TABLE … LIKE` 로 만들었다(`deploy/gunsan-shadow/README.md:292`). 운영 DDL 이 나중에 바뀌었으면 `_SH` 도 `ALTER` 로 맞춰야 한다.

### 4.3 규칙 테이블

§2.3. 섀도우도 규칙은 운영 `TB_CTRL_RULE_CFG` 를 읽으므로(`deploy/gunsan-shadow/README.md:279`) 키가 없으면 운영·섀도우가 같은 시각에 함께 실패한다.

### 4.4 더미 시더 (`.claude/skills/gunsan-epa-dummy`)

`seed_dummy.py` 의 태그 목록에 `891-365-POI-8600` 은 있고(`:63`, 96~100 %) `891-365-FRI-8653` 은 없다. 개발서버에서 더미로 돌리면 매 사이클 `OSIK_OUTFLOW_MISSING` 이 붙고 유입유량 로직으로 폴백한다(동작에는 문제 없음). 지방산단 fallback 을 더미로 재현하려면 나운 수위 더미가 4.30 m 를 넘어야 하는데, 이는 시더 파라미터 변경이 필요하다(이번 작업 범위 밖).

### 4.5 compose·반출본

- 운영 `deploy/gunsan/docker-compose.prod.yml` 의 `ems-ctrl` 은 테이블 인자를 주지 않는다(`:210` 주석). 변경 없음.
- 섀도우 compose 의 인자 4개는 재적용으로 다시 유효하다. 주석에 선행조건·한계 두 줄을 더했다(`docker-compose.shadow.yml`, `README.md`).
- `main_5min.py` 는 `ems-py-api` 이미지에 박힌다(2-1 유형). 반출본을 다시 말아야 서버에 반영된다(`build-and-save.ps1`, `docs/tenant-bundle-guide.md`). 이번 작업에서는 말지 않았다.

### 4.6 문서

`docs/gunsan-ctrl-workflow.html` 의 "장치는 둘"(`:227`), 4.5 결과 행(`:368`), P14(`:613`), 14장 대조표 1·7행(`:720`, `:726`) 은 이번 드롭으로 틀려졌다. 각 줄 끝에 09-30 갱신 문구를 덧붙였다(원문은 남김). `deploy/gunsan/README.md` §10, `deploy/gunsan-shadow/README.md` ems-ctrl 절도 맞췼다.

---

## 5. 현장 DB 확인용 SQL

```sql
-- (1) 규칙 키 8개 — 8행이 아니면 Python 이 매 사이클 "필수 설정값 누락" 으로 실패한다
SELECT PARAM_KEY, VALUE_NUM, VALUE_TEXT, DESCRIPTION
FROM TB_CTRL_RULE_CFG WHERE PARAM_KEY LIKE 'LOCAL_%' ORDER BY PARAM_KEY;

-- (2) 결과 컬럼 5개 — 운영과 섀도우 둘 다 5행이어야 INSERT 가 된다
SHOW COLUMNS FROM TB_CTRL_CMD_RST    LIKE 'LOCAL_%';
SHOW COLUMNS FROM TB_CTRL_CMD_RST_SH LIKE 'LOCAL_%';
-- 섀도우만 비면:  ALTER TABLE TB_CTRL_CMD_RST_SH ADD COLUMN ... (운영 DDL 그대로)

-- (3) 새 입력 태그 적재 — TS 범위 없이 TAGNAME 만으로 조회하면 시간 초과다(PK 가 TS 우선)
SELECT TAGNAME, COUNT(*) AS N, MAX(TS) AS LAST_TS
FROM TB_RAWDATA
WHERE TS >= DATE_SUB(NOW(), INTERVAL 3 DAY)
  AND TAGNAME IN ('891-365-FRI-8653', '891-365-POI-8600', '891-365-FRI-8652')
GROUP BY TAGNAME;

-- (4) 지방산단 제어 태그 3행 (docs/sql/gunsan_ctrl_cmd.sql 2·3절 실행 뒤)
SELECT TAG_DSC, TAG FROM TB_WPP_TAG_CODE
WHERE FUNC_TYP = 'CtrlCmdTag' AND TAG_DSC LIKE 'LOCAL_%' ORDER BY TAG_DSC;
```

---

## 6. 조치

### 6.1 이번에 한 것

1. `main_5min.py` 섀도우 테이블 옵션 재적용(§3). 벤더 변경분 유지.
2. BE·FE 를 3장치(PUMP·NATIONAL·LOCAL)로 확장, 태그 시드·확정 UPDATE, 사유 한글 사전(`LOCAL_*` 12종, `OSIK_*` 3종) — `docs/gunsan-ctrl-cmd-consumer.md` 결정 9.
3. 문서: 이 문서, 운영·섀도우 README, 섀도우 compose 주석, 워크플로 HTML 5곳.

### 6.2 현장·벤더가 해야 하는 것 (순서대로)

1. §5-(1)(2) 확인. 규칙 키·컬럼이 없으면 **벤더에 시드 값과 DDL 요청**. 이게 없으면 새 스크립트는 켜는 즉시 매 사이클 실패한다.
2. `docs/sql/gunsan_ctrl_cmd.sql` 2절(멱등) 실행 → 3절의 `LOCAL_*` UPDATE 3줄 실행.
3. BE 배포(`ems-java-api`) → Python 포함 반출본 재빌드·배포. **순서 주의**: Python 만 먼저 올리면 `LOCAL READY` 행이 처리되지 않고 쌓인다(§4.1). BE 만 먼저 올리면 `LOCAL_*` 컬럼이 매퍼 SELECT 에 들어가므로 컬럼이 없는 DB 에서는 `selectReadyCmdList` 가 SQL 오류를 낸다 → §5-(2) 가 먼저다.
4. AI 운전모드 분석(2)에서 로그의 `LOCAL=` 값과 `LOCAL_RANGE_CHECK` 여부 확인 → 추천(1)에서 지방산단 1건 승인 → 운전(0).

---

## 7. 관찰 기록 (본 문서에서 수정하지 않음)

```
$ git diff --stat epa/epanet_gunsan/main_5min.py            (드롭 원본, 재적용 전)
 epa/epanet_gunsan/main_5min.py | 408 +++++++++++++++++++++++++++++++++++------
 1 file changed, 357 insertions(+), 51 deletions(-)

$ git diff --stat epa/epanet_gunsan/main_5min.py            (재적용 후)
 1 file changed, 357 insertions(+), 11 deletions(-)

$ python -m py_compile epa/epanet_gunsan/main_5min.py       → COMPILE_OK
$ python epa/epanet_gunsan/main_5min.py --help              → 인자 8종 표시, HELP_EXIT=0 (cp949 콘솔에서 정상)
   [--conn] [--conn-key] [--once] [--ts] [--dry-run] [--prediction-table] [--cmd-table] [--log-level]
$ python epa/epanet_gunsan/main_5min.py --cmd-table 'bad;name' --once --dry-run
   main_5min.py: error: --cmd-table 테이블명이 올바르지 않습니다: 'bad;name'   BADNAME_EXIT=2

회귀 grep (전부 0건): U+2014 / 701-365 / \btb_[a-z_]+\b / 98.0|98~100|98% 미만

$ python epa/epanet_gunsan/main_5min.py --conn epa/connections.gunsan.json --conn-key maria-ems-db-gu-test \
    --ts "2024-11-12 10:00:00" --dry-run
   pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on '<internal-host>' (timed out)")
   → 개발 DB 연결 불가. §1 의 미확정 3건은 이 때문이다.

BE: compileJava + compileTestJava (JDK 11) COMPILE_EXIT=0
FE: vue-cli-service lint --no-fix (2파일) → DONE  No lint errors found!
CtrlCmdServiceIT: DB 연결 불가로 실행 못 함(15케이스 = 기존 11 + LOCAL 4).
```

작업 트리의 미추적 파일 `epa/epanet_gunsan/logs/pre_20260929.txt`, `pre_20260930.txt` 는 PRE(`main_epa_gs.py`) 드롭 작업의 실패 로그다(cp949 `—` 오류, `--schedule-offset-sec` 범위 오류). 이 작업과 무관해 건드리지 않았다.
