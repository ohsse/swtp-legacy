# 군산 SI "기준 시각이 없습니다" — 원인 분석

> **성격**: 사실 확인 문서다. 모든 단언에 `파일:라인` 근거를 붙였고, 확인하지 못한 것은
> "미확정"으로 남겼다. **코드 변경은 포함하지 않는다.**
> **조사 기준**: `master` / `c0703e5` 시점 소스 직접 확인 + 개발 DB 실측(§4).
> **재현 환경**: 로컬 `docker-compose.gunsan-dev.yml` 스택
> → `maria-ems-db-gu-test` = `<internal-host> / ems_db` (`epa/connections.gunsan.json`).
> **관련 문서**: `docs/sql/gunsan_ems_tag_seed.sql` (배수지 시드),
> `docs/gunsan-epa-mode-analysis.md` (EPAMODE), `docs/tenant-bundle-guide.md` (현장별 config 마운트),
> `docs/gunsan-si-valve-opening-analysis.md` (**같은 버튼의 다음 단계 오류** — 이 문서의 원인을
> 넘기면 밸브 개도율 실측 부재로 막힌다).

---

## 1. 결론 요약

관망해석 시뮬레이션 화면에서 "펌프 적용 및 실행"을 누르면 아래 문구가 뜬다.

> 오류가 발생했습니다: TB_EPA_SIM_RESV_FLOW 에 기준 시각이 없습니다.
> 관망해석 화면에서 배수지 유량을 먼저 저장하세요.

**이 안내는 실제 원인을 잘못 지목하고 있다.** 기억해야 할 세 가지:

1. **테이블도 저장도 정상이다.** 실측 결과 행은 5건 있고(§4.1), `UPDT_TIME` 은 사용자가 실행
   버튼을 누른 바로 그 시각으로 갱신돼 있었다. 저장은 성공했다. 그러니 "먼저 저장하세요"를
   아무리 반복해도 이 에러는 사라지지 않는다.

2. **원인은 두 개의 서로 다른 시계를 맞대는 한 줄이다** (`epa_service_gunsan.py:200`).
   `UPDT_TIME` 은 **DB 서버**가 `NOW()` 로 찍고, 그것을 거르는 `WHERE UPDT_TIME <= %s` 의 `%s` 는
   **epa 프로세스**의 `datetime.now()` 다. epa 쪽 시계가 DB 쪽보다 뒤처지면, 방금 저장한 행이
   "미래"로 판정돼 조건에서 탈락한다.

3. **이 테이블에는 이력이 없어 스큐 한 번이 5행 전부를 날린다.** PK 가 `NODE_ID` 단일이고
   저장 SQL 이 5개 행의 `UPDT_TIME` 을 한꺼번에 같은 값으로 덮어쓰기 때문에(§5.2),
   물러설 과거 행이 하나도 남지 않는다. 결과 집합이 통째로 비고 `MAX` 는 `NULL` 이 된다.

> **이것은 가끔 터지는 경합이 아니다.** 프런트가 저장 직후에 곧바로 해석을 호출하는 구조라,
> 스큐가 §5.3 의 1초 여유를 넘는 순간부터 **매번** 실패한다(§5.4).

남은 미확정 항목은 하나다 — **epa 컨테이너의 실제 시계를 직접 관측하지 못했다**(§5.5).
확정 절차는 §6.3 에 있다.

---

## 2. 증상과 재현 경로

### 2.1 호출 사슬

```
[FE] AnalysisSettings.vue:133-134  "펌프 적용 및 실행" 버튼
  → executeAnalysis()                      AnalysisSettings.vue:444
  → $emit('execute', {pumps:[…]})          AnalysisSettings.vue:454
  → handleExecuteAnalysis(settings)        EpaAnalysisSimulation.vue:192
       ① POST /api/web/updateRate          EpaAnalysisSimulation.vue:205   ← 배수지 유량 저장
         └ 성공하면 alert("유량 정보가 성공적으로 저장되었습니다")  :215
       ② POST /api/simulations/si          EpaAnalysisSimulation.vue:218   ← 해석 실행
[BE] SimulationSIView.post                 epa_routes.py:75
  → get_engine().run_si_simulation(ts=None, …)   epa_routes.py:139-144
  → (EPA_ENGINE='gunsan') epa_service_gunsan.run_si_simulation   engine.py:37-52
  → _latest_si_ts()  →  None               epa_service_gunsan.py:245
  → ValueError                             epa_service_gunsan.py:246-250
  → except Exception → HTTP 500 + 원문     epa_routes.py:153-155
[FE] alert(`오류가 발생했습니다: ${error.message}`)   EpaAnalysisSimulation.vue:227,238
```

**①이 성공한 뒤 ②가 실패한다.** 그래서 "저장되었습니다" alert 과 "기준 시각이 없습니다" alert 이
연달아 뜬다. 이 순서가 원인 판정의 출발점이다 — 저장이 실패했다면 ②에 도달하지도 못한다
(`EpaAnalysisSimulation.vue:210-212` 가 먼저 던진다).

### 2.2 에러 문구의 유일한 출처

리포지토리 전체에서 이 문구가 나오는 곳은 `epa/app/services/epa_service_gunsan.py:245-250` 한 곳뿐이다.

```python
target_ts = ts or _latest_si_ts()                       # :245
if target_ts is None:                                   # :246
    raise ValueError(
        "TB_EPA_SIM_RESV_FLOW 에 기준 시각이 없습니다. "  # :248
        "관망해석 화면에서 배수지 유량을 먼저 저장하세요."  # :249
    )
```

프런트는 `ts` 를 보내지 않으므로(`epa_routes.py:101,125-130` — `settings.ts` 가 없으면 `None`)
**항상 `_latest_si_ts()` 가 호출된다.**

### 2.3 판정 한 줄

`epa/app/services/epa_service_gunsan.py:188-206`

```python
def _latest_si_ts() -> Optional[datetime]:
    row = db.fetchone(
        "SELECT MAX(UPDT_TIME) AS UPDT_TIME FROM TB_EPA_SIM_RESV_FLOW WHERE UPDT_TIME <= %s",
        (datetime.now(),),                               # :201  ← epa 프로세스의 시계
    )
    return row.get("UPDT_TIME") if row and row.get("UPDT_TIME") else None
```

`None` 이 되는 경우는 셋뿐이다.

| # | 조건 | 이번 건 해당 여부 |
|---|---|:--:|
| a | 테이블에 행이 0건 | **아니다** — 5건 확인(§4.1), 모달에도 5곳이 보인다 |
| b | 모든 행의 `UPDT_TIME` 이 `NULL` | **아니다** — 전부 값이 있다(§4.1) |
| c | 모든 행의 `UPDT_TIME` 이 **인자로 넘긴 시각보다 미래** | **이것이다**(§5) |

> a·b 가 배제되므로 c 말고는 설명이 없다. 참고로 격리수준(`REPEATABLE READ`)에 의한 stale read 도
> 원인이 될 수 없다 — 행은 `2026-08-31` 부터 존재했으므로(§4.2) 낡은 스냅샷을 읽었더라도
> **더 오래된 타임스탬프**가 나올 뿐 `NULL` 이 되지는 않는다.
> (커넥션은 `app/__init__.py` 의 `before_request`/`teardown_request` 로 요청마다 풀에서
> 꺼내고 되돌린다. `db.py:46-59` 의 `PooledDB` 는 반납 시 롤백한다.)

---

## 3. "SI 기준 시각"이란 무엇인가

이 설계를 모르면 에러 문구가 엉뚱해 보인다. **군산 SI 해석의 기준 시각은 실측 시각이 아니라
"운영자가 배수지 유량을 마지막으로 저장한 시각"이다.**

| 해석/조회 | 기준 시각의 원천 | 코드 |
|---|---|---|
| **SI**(운영자 시나리오) | `TB_EPA_SIM_RESV_FLOW.UPDT_TIME` 의 `MAX` | `epa_service_gunsan.py:188-206` |
| MO(5분 주기 모니터링) | 현재 시각을 5분 경계로 내림 | `epa_service_gunsan.py:283-284` |
| 결과 조회(화면 표시) | `TB_FP_SI_VAL`/`TB_FR_SI_VAL` 의 `RGSTR_TIME` `MAX` 중 더 오래된 쪽 | `web_models.py:26-43` |

`base_time` / `std_time` 같은 **컬럼은 존재하지 않는다.** 런타임 개념이며 위 세 컬럼에서 도출된다.

그래서 프런트가 "① 저장 → ② 해석" 순서로 호출하는 것은 편의가 아니라 **필수**다.
①이 `UPDT_TIME = NOW()` 를 찍어야 그 시각이 곧 ②의 기준 시각이 된다
(`web_models.py:123-127`, `EpaAnalysisSimulation.vue:205,218`).

같은 규칙이 엔진 스크립트에도 한 벌 더 있다 — `epanet_si_gs.py:498-507 pick_latest_si_ts()`.
앱이 `--ts` 를 항상 넘기므로(`epa_service_gunsan.py:253`) 평소엔 타지 않는다(§8-3).

---

## 4. 실측 기록

**대상**: `<internal-host> / ems_db` (로컬 gunsan-dev 스택이 보는 DB)
**조회 시각**: `2026-09-14 13:44` 무렵. 사용자가 오류를 재현한 직후다.

### 4.1 `TB_EPA_SIM_RESV_FLOW` 현재 내용

| DISPLAY_ORDER | NODE_ID | TNK_NM | FLOW_RATE | UPDT_TIME |
|--:|---|---|--:|---|
| 1 | 함열가압장 | 함열가압장 | 1000 | 2026-09-14 13:33:23 |
| 2 | 28 | 장항배수지 | 1000 | 2026-09-14 13:33:23 |
| 3 | 오식도(배)공업 | 오식도배수지 | 1000 | 2026-09-14 13:33:23 |
| 4 | 군장에너지 | 군장에너지 | 1000 | 2026-09-14 13:33:23 |
| 5 | 나운(배) | 나운배수지 | 1000 | 2026-09-14 13:33:23 |

여기서 읽어야 할 것 네 가지:

1. **행은 5건 있다.** §2.3 의 (a) 가 배제된다. 화면 모달에 배수지 5곳이 보이는 것과도 일치한다
   (`MultiInflowModal.vue:83-90` 은 `tanks` prop 으로만 표를 그린다).
2. **`UPDT_TIME` 이 전부 같고, 사용자가 실행을 누른 시각이다.** ①의 `updateRate` 가
   정상 동작했다는 직접 증거다. 5건이 같은 값인 이유는 §5.2.
3. **DB 시계로 판정하면 통과한다.** `SELECT MAX(UPDT_TIME) ... WHERE UPDT_TIME <= NOW()` 는
   `2026-09-14 13:33:23` 을 돌려준다. 같은 질의가 앱에서만 `NULL` 이었다는 뜻이다 — §5 의 근거.
4. **`FLOW_RATE` 가 5건 모두 `1000`** 이다. 이는 실측이 아니라 컬럼 DEFAULT 값이다
   (`ems_schema.md:436` — `FLOW_RATE double NOT NULL DEFAULT 1000`). §8-4 참조.

### 4.2 시드 적용 여부 — **`gunsan_ems_tag_seed.sql` 의 §4 블록은 적용된 적이 없다**

`docs/sql/gunsan_ems_tag_seed.sql:123-132` 은 `DISPLAY_ORDER` 를
나운=1, 오식도=2, 28=3, 군장=4, 함열=5 로 넣고 `ON DUPLICATE KEY UPDATE` 로 그 값을 강제한다.
실제 DB 는 함열=1, 28=2, 오식도=3, 군장=4, 나운=5 로 **순서가 다르다.**
시드가 한 번이라도 돌았다면 이 값이 남아 있을 수 없다.

즉 지금의 5건은 **군산 덤프(`ems_db`)에 원래 있던 행**이다
(`information_schema` 기준 테이블 생성 `2026-08-31 10:13:46`).

### 4.3 오늘 SI 는 한 번도 성공하지 못했다

| 항목 | 값 |
|---|---|
| `TB_FP_SI_VAL` 마지막 DML (`information_schema.TABLES.UPDATE_TIME`) | `2026-09-11 16:24:52` |
| `TB_FP_SI_VAL` 의 `MAX(RGSTR_TIME)` (`FLG='si'`) | `2025-05-08 10:00` (덤프 원본 데이터) |

SI 가 성공했다면 `TB_FP_SI_VAL` 에 `FLG='si'` 결과가 기록된다. 오늘 쓰기가 전혀 없다
= 실행 시도가 전부 `_latest_si_ts()` 단계에서 죽었다.

### 4.4 두 시계 대조 (참고 — 이 PC 기준)

```
DB NOW(3) : 2026-09-14 13:44:54.019
PC now()  : 2026-09-14 13:44:56.561
왕복(ms)  : 0.8
스큐(DB − PC): -2.542 초
```

약 9분 간격으로 두 번 측정했고 두 번 다 `-2.542` 로 동일했다 — **지터가 아니라 고정 오프셋**이다.
왕복 지연이 1ms 미만이므로 네트워크 요인도 아니다.

> **주의 — 이 수치는 원인의 직접 증거가 아니다.** 여기서 비교한 것은 DB 와 **Windows 호스트**의
> 시계다. 정작 필요한 것은 DB 와 **epa 컨테이너**의 시계 차인데, 컨테이너가 떠 있지 않아
> (`docker ps` 무결과) 측정하지 못했다. §5.5·§6.3 참조.

---

## 5. 원인

### 5.1 한 줄 안에 두 기계의 시계가 들어 있다

```
UPDT_TIME  ←  MariaDB 서버(<internal-host>)의 NOW()        …… web_models.py:125 이 기록
    ^
    │  WHERE UPDT_TIME <= %s
    v
    %s     ←  epa 컨테이너 프로세스의 datetime.now()      …… epa_service_gunsan.py:201 이 비교
```

두 값이 같은 시계에서 왔다는 보장이 코드 어디에도 없다.
`epa 시계 < DB 시계` 이면 방금 저장한 행이 "미래"가 되어 조건에서 탈락한다.

시간대 문제는 아니다 — DB 는 `@@system_time_zone = Asia/Seoul`, 컨테이너는
`epa/Dockerfile:7-16` 이 `tzdata` 설치와 `/etc/localtime` 링크를 모두 하고
compose 가 `TZ: "Asia/Seoul"` 을 준다(`docker-compose.gunsan-dev.yml`). **양쪽 다 KST 다.**
따라서 9시간 같은 큰 어긋남이 아니라 **초 단위 드리프트**가 문제다.

### 5.2 왜 5행이 한꺼번에 죽는가 — 이 테이블에는 이력이 없다

`ems_schema.md:429-441`

```sql
CREATE TABLE `TB_EPA_SIM_RESV_FLOW` (
  `NODE_ID`   varchar(50) NOT NULL,
  ...
  `FLOW_RATE` double   NOT NULL DEFAULT 1000,
  `UPDT_TIME` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`NODE_ID`)                       -- ← 노드당 행이 딱 하나
)
```

`web_models.py:123-127` 의 저장 SQL 은 `executemany` 로 5행을 한 번에 갱신한다.

```sql
UPDATE TB_EPA_SIM_RESV_FLOW SET FLOW_RATE = %s, UPDT_TIME = NOW() WHERE NODE_ID = %s
```

**한 번의 저장이 5개 행의 `UPDT_TIME` 을 전부 같은 값으로 덮어쓴다**(§4.1 이 그 결과다).
과거 시각을 가진 행이 하나도 남지 않으므로, 그 값 하나가 "미래"로 판정되는 순간
`WHERE UPDT_TIME <= now` 의 결과 집합이 **통째로 비고** `MAX` 가 `NULL` 이 된다.

이력 테이블이었다면 직전 저장분으로 물러설 수 있었겠지만, 이 구조에는 그럴 여지가 없다.

### 5.3 여유는 최대 1초뿐

`UPDT_TIME` 은 `datetime`(초 정밀도)이라 `NOW()` 의 소수점 이하가 잘려 나간다.
반면 `datetime.now()` 는 마이크로초까지 갖는다. 이 절삭이 최대 1초의 여유를 준다.

| epa 시계가 DB 시계보다 | 결과 |
|---|---|
| 앞서 있거나 같음 | 정상 |
| 1초 미만 뒤처짐 | 절삭 여유로 대개 통과 |
| **1초 이상 뒤처짐** | **매번 이 에러** |

### 5.4 가끔이 아니라 매번이다

프런트가 저장(①) 직후에 해석(②)을 호출하므로, `UPDT_TIME` 은 **항상 방금 찍힌 DB 시각**이다.
따라서 스큐가 §5.3 의 문턱을 넘으면 클릭할 때마다 재현된다. §4.3 의 "오늘 쓰기 0건"이 이를 뒷받침한다.

반대로 말하면, **"어제는 됐는데 오늘 안 된다"는 증상은 스큐가 문턱을 넘은 시점과 일치한다.**
로컬 스택은 Docker Desktop(WSL2) 위에서 도는데, 호스트 절전·최대 절전 후 WSL2 VM 시계가
뒤처지는 것은 알려진 현상이다. 짚어 볼 첫 후보다.

### 5.5 미확정

- **epa 컨테이너의 실제 시계를 관측하지 못했다.** 조사 시점에 컨테이너가 떠 있지 않았다
  (`docker ps` 무결과). §5 는 §2.3 의 (a)(b) 를 실측으로 배제해 (c) 만 남긴 소거법이며,
  스큐의 존재와 크기는 §6.3 으로 확정해야 한다.
- **오늘 13:33:23 의 저장이 몇 번째 시도였는지**는 알 수 없다. 이 테이블은 이력이 없어
  덮어쓰기만 남는다(§5.2).

---

## 6. 확인 절차

### 6.1 테이블 상태 — "비어서 나는 에러"가 아님을 보인다

```sql
SELECT NODE_ID, TNK_NM, FLOW_RATE, UPDT_TIME, DISPLAY_ORDER
FROM TB_EPA_SIM_RESV_FLOW ORDER BY DISPLAY_ORDER;

-- 앱과 같은 판정을 DB 시계로 재현한다. 행이 나오면 (a)(b) 는 배제된다.
SELECT MAX(UPDT_TIME) FROM TB_EPA_SIM_RESV_FLOW WHERE UPDT_TIME <= NOW();
```

### 6.2 두 시계 대조 (DB ↔ 임의 클라이언트)

왕복 지연을 함께 출력해 스큐와 네트워크 지연을 구분한다.

```python
import pymysql, datetime, time
c = pymysql.connect(host='<internal-host>', port=3306, user='root', password='...',
                    db='ems_db', cursorclass=pymysql.cursors.DictCursor)
with c.cursor() as cur:
    t0 = time.time(); cur.execute('SELECT NOW(3) AS db_now'); r = cur.fetchone(); t1 = time.time()
    local = datetime.datetime.now()
    print('DB :', r['db_now'], '/ client :', local)
    print('왕복(ms):', round((t1 - t0) * 1000, 1))
    print('스큐(DB-client, 초):', round((r['db_now'] - local).total_seconds(), 3))
```

### 6.3 컨테이너 시계 — **미확정을 확정으로 바꾸는 단계**

스택을 띄운 상태에서 두 시각을 나란히 본다.

```bash
docker compose -f docker-compose.gunsan-dev.yml exec ems-py-api \
  date '+%Y-%m-%d %H:%M:%S.%3N %Z'
```

이 값이 §6.2 의 `DB NOW(3)` 보다 **1초 이상 뒤처져 있으면 §5 의 결론이 확정된다.**

앱이 실제로 쓰는 값과 완전히 같게 보려면 프로세스 안에서 확인한다.

```bash
docker compose -f docker-compose.gunsan-dev.yml exec ems-py-api \
  python -c "import datetime; print(datetime.datetime.now())"
```

### 6.4 앱 로그로 교차 확인

`epa_routes.py:132-135` 가 요청마다 남기는 줄에서 기준 시각을 볼 수 있다.

```
SI 시뮬레이션 요청 - ts: 최신 시각, pump_comb: …, pump_hz: …
```

`ts:` 가 `최신 시각` 인데 곧바로 `SI 시뮬레이션 실행 중 오류`(`:154`)가 이어지면 이 경로다.

---

## 7. 해소 방법

### 7.1 즉시 — 시계를 맞춘다 (근본 원인)

epa 컨테이너의 시계를 DB 서버에 맞춘다. 로컬 스택이면 WSL2 VM 시계부터 본다.
컨테이너는 호스트(WSL2) 커널 시계를 그대로 쓰므로, **컨테이너를 재시작해도 호스트가 어긋나 있으면
그대로다.** 호스트 쪽을 맞춘 뒤 확인은 §6.3.

### 7.2 데이터 — 배수지 유량을 실값으로 채운다

§7.1 로 에러를 넘기더라도, `FLOW_RATE` 가 5건 모두 컬럼 DEFAULT `1000` 인 상태에서는
**해석 결과가 의미를 갖지 않는다**(§4.1-4, §8-4).

- `docs/sql/gunsan_ems_tag_seed.sql` §4 블록(`:123-132`)이 아직 적용되지 않았다(§4.2).
  이 블록은 `INFLOW_TAG`·`TNK_NM`·`DISPLAY_ORDER` 를 정본으로 맞추고 `FLOW_RATE` 는 건드리지 않는다
  (`:133` 주석 — "화면에서 갱신되는 운영값이므로 재실행 시 덮어쓰지 않는다").
- 유량 값 자체는 화면에서 넣는다: "배수지 수요량 설정" 모달 → 저장 → "펌프 적용 및 실행".

### 7.3 손대지 않은 것

이 문서는 진단만 한다. 코드 수정안은 제시하지 않으며, 관찰된 문제는 §8 에 기록만 남긴다.

---

## 8. 알려진 이슈 (관찰 기록 — 본 문서에서 수정하지 않음)

아래는 이번 조사에서 함께 확인된 사실이다. 손대기 전 별도 합의가 필요하다.

| # | 내용 | 근거 |
|---|---|---|
| 1 | **"저장 성공" alert 이 저장을 보장하지 않는다.** 저장 경로가 `UPDATE ... WHERE NODE_ID=%s` **UPDATE 전용**이라 INSERT 가 없다. 행이 없거나 `NODE_ID` 가 어긋나면 0건 갱신하고도 200/`SAVE_SUCCESS` 를 준다. 프런트는 `code!==200` 만 보므로 그대로 해석으로 넘어간다 → **§1 과 똑같은 에러를 만드는 두 번째 경로** | `web_models.py:109-131`, `web_routes.py:82-85`, `EpaAnalysisSimulation.vue:210-212` |
| 2 | **에러 문구가 지목하는 조치가 무효인 경우가 있다.** 모달 표는 `tanks` prop 으로만 그려지고 그 `tanks` 는 같은 테이블에서 온다. 테이블이 비면 모달도 비어 **입력할 칸 자체가 없다.** "먼저 저장하세요"를 물리적으로 따를 수 없다 | `MultiInflowModal.vue:83-90`, `web_models.py:16-24`, `AnalysisSettings.vue:240` 주석이 과거 이 상태를 겪은 흔적 |
| 3 | **같은 판정이 엔진 스크립트에도 한 벌 더 있다.** 앱이 `--ts` 를 항상 넘겨 지금은 타지 않으나, CLI 로 직접 돌리면 같은 스큐에 같은 문구로 죽는다 | `epanet_si_gs.py:498-507`, `:1279-1283` |
| 4 | **`FLOW_RATE` 가 컬럼 DEFAULT `1000` 인 채로 방치돼 있다.** 시드가 *"임의 유량으로 해석이 도는 것을 막기 위해 0 을 명시"* 한 의도와 정반대다. 함열가압장은 공급 지점이라 엔진이 음수 부호를 적용한다 | `ems_schema.md:436`, `gunsan_ems_tag_seed.sql:120-121`, `epanet_si_gs.py:14` |
| 5 | **HTTP 코드가 성격과 어긋난다.** 데이터 상태 문제인데 `EngineBusyError` 외 전부가 500 으로 나간다(400 이 맞다). 운영 로그에서 서버 장애로 오인된다 | `epa_routes.py:148-155` |
| 6 | **프런트가 `fetchFunc` 를 시그니처와 다르게 부른다.** 2번째 인자는 `data` 인데 `{method, body}` 를 넘겨, 서버가 `{"method":…,"body":"<JSON 문자열>"}` 를 받는다. 서버 양쪽이 이 이중 인코딩을 알고 되풀어 동작은 하지만, 규약이 코드에 드러나 있지 않다 | `fetchFunc.js:8,28-30`, `EpaAnalysisSimulation.vue:205-208,218-221`, `web_service.py:154-156`, `epa_routes.py:79-93` |
| 7 | **`tanks` 가 빈 배열이어도 저장이 성공으로 처리된다.** `[]` 를 보내면 갱신 0건에 200 이 나가고 해석으로 진행한다 | `EpaAnalysisSimulation.vue:198-212`, `web_service.py:150-176` |
| 8 | **기준 시각 윈도 규칙이 두 엔진에서 다르다.** 고산은 기준시각 **전·후** 양쪽에서 가까운 값을 고르고(`fetch_reservoir_flow_by_node_nearest`, `SI_RESV_WINDOW_SEC=120`), 군산은 **과거 방향만** 본다(`fetch_si_demands`, `GUNSAN_FALLBACK_SEC=600`). 군산 경로는 `SI_RESV_WINDOW_SEC` 를 읽지 않는다 — `config.gunsan.py:86` 에 값이 남아 있으나 사문이다 | `epa_models.py:307-357` (호출부는 `epa_service.py:703` 뿐), `epanet_si_gs.py:510-525`, `config.gunsan.py:78,86` |

> §8 의 경로가 생략된 파일은 각각
> `epa/app/models/`, `epa/app/routes/`, `epa/app/services/`, `epa/epanet_gunsan/`,
> `fe/src/views/EpaAnalysis/`, `fe/src/util/` 아래에 있다.
