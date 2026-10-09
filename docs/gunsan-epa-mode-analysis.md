# 군산 EPAMODE 적용 — 현황 분석 및 설계

> **성격**: 착수 전 사실 확인 문서다. 모든 단언에 `파일:라인` 근거를 붙였고, 확인하지 못한 것은
> "미확정"으로 남겼다. 코드 변경은 포함하지 않는다.
> **조사 기준**: `master` / `51577c7` 시점 소스 직접 확인.
> **관련 문서**: `inpEditor/BE/editor/doc/reference/legacy-ems-pump-control-summary.md`
> (자율제어 주기·유지시간·제어이력), `deploy/gunsan/README.md` (군산 배포 스택).

---

## 1. 결론 요약

군산은 **EPAMODE UI와 API가 이미 붙어 있으나 실제로는 아무 동작도 하지 않는 "데드 UI"** 상태다.

1. 프론트 토글은 커밋 `d47d534`("feat : 수요예측 버튼")로 군산 화면에 이미 장착돼 있고, API도 호출된다.
2. 그러나 백엔드의 EPAMODE 분기가 `wpp_code.equals("gs")` **고산 전용 블록 안쪽**에 있어
   군산(`gu`)은 도달하지 못한다.
3. 도달하더라도 읽을 데이터(`TB_FP_VAL`/`TB_FR_VAL`의 `FLG='PRE'`)를 **군산에서는 아무도 생산하지 않는다.**

따라서 군산 적용은 플래그 추가가 아니라 **① 예측 관망해석 데이터 공급 파이프라인 구축(선결)
② 백엔드 사이트 일반화** 두 갈래 과제다.

---

## 2. 현행 EPAMODE 구조

### 2.1 스위치의 실체

EPAMODE는 설정 파일이나 코드 상수가 **아니다**. DB의 단일 행 하나다.

| 항목 | 사실 | 근거 |
|---|---|---|
| 저장 위치 | `TB_WPP_TAG_CODE.DEFAULT_VALUE WHERE FUNC_TYP = 'EPA_PUMP'` | `be/src/main/resources/sqlmapper/mysql/epa_mssql.xml:6-22` |
| 조회 API | `GET /epa/getEpaModeInfo` → `int` | `EpaController.java:20-23` |
| 변경 API | `PUT /epa/setEpaMode/{mode}` | `EpaController.java:26-30` |
| UI | `EpaMode.vue` — `0`=수요예측 / `1`=관망분석 토글 | `fe/src/views/Common/EpaMode.vue:1-36` |
| 캐시 | 없음. 30초 스케줄러가 매 tick 재조회하므로 토글 즉시 반영 | `DrvnConfig.java:141`, `:178` |

사이트 구분 컬럼이 없지만, 고산·군산이 **물리적으로 다른 DB 인스턴스**(고산 `<internal-host>/EMS_DB`,
군산 `<internal-host>/EMS_DB` — `application-gs.properties:9`, `application-gu.properties:9`)이므로
플래그 자체는 사이트별로 이미 독립적이다.

### 2.2 유일한 판별 지점

전체 리포지토리에서 `epaMode`를 실제로 **사용**하는 곳은 한 군데뿐이다.

```java
// DrvnConfig.java:176-185
int epaMode;
try { epaMode = epaService.getEpaModeInfo(); }
catch (Exception e) { epaMode = 0; }   // 실패 시 무조건 수요예측 모드로 폴백
logger.info("최종적으로 결정된 epaMode: {}", epaMode);
```

```
DrvnConfig.schedulePumpTask()                    30초 주기   :141
  └ setInsertPumpComn()                          @Async      :152
      ├ epaMode 조회                                          :178
      ├ for i in -4..0  (최근 5분치 시각 루프)                  :187
      │   └ 펌프그룹별 예측 유량·압력 조회 → getCorrectedValue()
      │       · wpp_code=="gs"  → gosanDataMap 에 적재만        :226-228
      │       · 그 외(군산 포함) → 즉시 insertPumpComb(...)     :229-233   ← epaMode 미사용
      └ if (wpp_code.equals("gs"))                             :239        ← 고산 전용 게이트
          ├ 키 4개·값 0.0 검증 (미달 시 return)                  :241-250
          ├ gosanFlow     = flow1 + flow2                       :252
          ├ gosanPressure = 0.025268·p1 + 0.968549·p2 + 0.064324 :253
          ├─[epaMode==1] insertPumpComb(epaFlow, epaPressure, 0, ts)    :255-266
          └─[else      ] insertPumpComb(gosanFlow, gosanPressure, 0, ts) :273
```

**차이는 `insertPumpComb()` 에 넘기는 유량·압력의 출처뿐**이다. 그 이후 조합 계산 로직은 완전히 동일하다.

### 2.3 EPA 모드 ON일 때 읽는 값

| | 조회 대상 | 고산 하드코딩 | 근거 |
|---|---|---|---|
| 유량 | `TB_FR_VAL.FLW_ALG_RST_VAL` | `link_id="10"`, `opt_idx="PRE"` | `EpaService.java:43-66` |
| 압력 | `TB_FP_VAL.FP_ALG_RST_VAL`, 결과를 **`/10`** | `node_id="고산(정)유출"` | `EpaService.java:94-100` |
| 시각 | `startDate` 기준 **최근 3분 내** 최대 `RGSTR_TIME` 1건 | — | `drvn_mssql.xml:319-355` |

두 메서드는 전달받은 인자(`gosanFlow` / `gosanPressure` / `pump_grp`)를 **전혀 사용하지 않는다.**
수두손실 그룹 기반의 원래 구현은 `EpaService.java:41-65`, `:71-92` 에 전부 주석 처리돼 있고,
현재는 DB 조회 결과만 그대로 반환한다.

압력의 `/10` 은 단위 환산이다. EPANET 절점 압력은 수두(m)로 나오고 EMS는 kgf/cm² 를 쓴다
(1 kgf/cm² ≈ 10.197 m).

### 2.4 `FLG='PRE'` 데이터는 누가 만드는가

**`al/pump3` 고산 전용 파이썬만 생산한다.**

```python
# al/pump3/main_e.py:464-465
exec0 = f"python /home/app/pump3/epanet/test.py --startDt '{prdct_time}' --endDt '{prdct_time}' --pre False"
exec1 = f"python /home/app/pump3/epanet/test.py --startDt '{test_timestamp}' --endDt '{test_timestamp}' --pre True"
```

`--pre True` 경로가 `TB_FR_VAL`/`TB_FP_VAL` 에 `'PRE'` 로 INSERT 한다
(`al/pump3/epanet/test.py:154`, `:163`). `main_e.py` 는 고산 전용이다
(`Predict_5min_test('Gosan', ...)` — `main_e.py:342`, `:364`, 태그 `GS_taglist.xlsx`).
운영 실행 대상에도 `main_e.py` 만 들어 있다 (`al/Dockerfile:24`).

> ### 흔한 오해 — "관망해석이 돌고 있으니 데이터는 있다"
>
> **성립하지 않는다.** `epa/` Flask 모듈은 `FLG='PRE'` 를 쓰지 않는다.
> `mo`(5분 주기 모니터링) / `si`(단발 시나리오)만 쓰며, 대상 테이블도
> `TB_FP_SI_VAL` / `TB_FR_SI_VAL` 로 **다르다** (`epa/config.py:29-31`).
> 제공 엔드포인트도 `POST /simulations/si` 와 `POST /simulations/mo/batch` 둘뿐이다
> (`epa/app/routes/epa_routes.py:123`, `:126`).
> 즉 **테이블도 플래그도 달라서 EPAMODE는 `epa/` 의 결과를 볼 수 없다.**

### 2.5 EPAMODE 의 적용 경계 — 어디까지 보고 어디부터 안 보는가

고산에서도 EPAMODE 확인은 **조합 생성 직전의 "입력값 선택" 단계 한 곳뿐**이다.
조합 계산 알고리즘 자체는 EPAMODE 를 모른다.

```
epaMode 조회  →  유량·압력의 "출처" 결정  →  insertPumpComb(flow, pressure, grp, ts)
   :178                :255-274                        :338  ← 여기부터 EPA 를 모름
```

정확히는 **전처리를 바꾸는 것이 아니라 전처리 결과를 버리고 갈아끼우는 것**이다.
EPA 모드를 켜도 앞단은 그대로 다 돈다.

```
예측 유량·압력 조회 → getCorrectedValue() 보정 → gosanDataMap 적재     :198-233
  → [가드] 키 4개 검사 + 값 0.0/null 검사                              :241-250
  → gosanFlow = flow1+flow2,  gosanPressure = 회귀식                   :252-253
  → if (epaMode == 1)                                                  :255   ← 여기서 갈림
```

`epaMode` 판정은 회귀식 계산이 끝난 **뒤**에 온다. EPA 모드면 방금 구한 `gosanFlow`/`gosanPressure`
를 버린다 — `getEpaFlow(gosanFlow, ...)` 에 인자로 넘기긴 하나 그 메서드는 인자를 무시하고
DB 조회 결과만 반환한다 (`EpaService.java:39-68`).

> ### 중요 — EPA 모드에서도 예측 데이터가 게이트로 남는다
>
> 가드(`:241-250`)가 `epaMode` 분기(`:255`)보다 **먼저** 있다. 예측값이 4개 다 있고
> 하나도 0 이 아니어야 그 아래로 내려간다.
> → **관망해석 결과가 아무리 잘 쌓여 있어도, 예측 데이터가 비면 그 tick 은 `return` 되어
> 조합이 만들어지지 않는다.**
>
> 군산 설계에 직접 영향을 준다. "PRE 데이터만 만들면 EPA 모드가 된다" 가 아니라,
> **예측 파이프라인(`Q_GunS_PREDICT`/`P_GunS_PREDICT`)이 계속 살아 있어야 한다.**
> 관망해석은 예측을 대체하는 것이 아니라 그 위에 얹히는 구조다.
> (군산은 그룹이 1개라 위 4개 키 가드는 적용되지 않지만, `getCorrectedValue()` 보정 경로는
> 동일하게 거친다 — `:212-213`, `:229-233`.)

| 사실 | 근거 |
|---|---|
| `epaMode` 는 필드가 아니라 `setInsertPumpComn()` 의 **지역 변수** | `DrvnConfig.java:176` (메서드 시작 `:152`) |
| 조합 계산 본체 `insertPumpComb()` 는 `epaMode`/`epaService` 를 **참조하지 않는다** | `DrvnConfig.java:338` 이후 본문에 참조 0건 |
| `epaService` 참조는 리포 전체에서 3곳뿐이며 전부 `setInsertPumpComn()` 내부 | `:178`(조회), `:256`·`:257`(값 대체) |

**그리고 조합 생성 경로가 둘인데, 한쪽은 EPAMODE 를 보지 않는다.**

| 경로 | 진입점 | EPAMODE 확인 |
|---|---|---|
| 자동 (30초 스케줄러) | `DrvnConfig.setInsertPumpComn()` `:152` | **O** — `:255` |
| **수동 (사용자 API)** | `GET /dr/pumpCombInsert` (`DrvnController.java:182-191`) → `DrvnService.pumpCombInsert()` `:2254` | **X** |

수동 경로는 고산 합성식(`flow1+flow2`, 동일한 회귀식)까지 똑같이 복제해 두고
`insertPumpComb(gosanFlow, gosanPressure, 0, ts)` 를 그대로 호출한다 (`DrvnService.java:2260-2275`).
→ **관망분석 모드를 켜둔 상태에서 수동으로 조합을 재생성하면 수요예측 값으로 만들어진다.**
의도된 동작인지 확인이 필요하며, 군산 적용 시에도 같은 방침을 정해야 한다(7장 리스크 참조).

---

## 3. 고산 vs 군산 구조 차이

| | 고산 (`gs`) | 군산 (`gu`) |
|---|---|---|
| 펌프 그룹 | **2개** (1=구정수지, 2=신정수지) → 합성해 `pump_grp=0` 1건 생성 | **1개** (`pump_grp=1`) |
| 예측 태그 | `Q_GS_OLD_Predict`/`P_GS_OLD_Predict`, `Q_GS_NEW_Predict`/`P_GS_NEW_Predict` | `Q_GunS_PREDICT`/`P_GunS_PREDICT` |
| 압력 산출 | 회귀 합성식 `0.025268·p1 + 0.968549·p2 + 0.064324` | 예측값 그대로 |
| 코드 경로 | `DrvnConfig.java:239-275` 전용 블록 | `:229-233` else 경로 |
| 근거 | `application-gs.properties:240-249` | `application-gu.properties:145-150` |

**군산이 오히려 단순하다.** 그룹 합성도 회귀식도 없이, 그룹 1건의 flow/pressure만
EPANET 결과로 치환하면 된다.

### 참고 — 사이트 분기의 축

레거시 EMS는 Spring 프로파일명을 그대로 사이트 코드로 쓴다.

```java
// DrvnConfig.java:83-84
@Value("${spring.profiles.active}")
private String wpp_code;
```

> **네이밍 주의**: 코드의 `gs`/`GS` 는 **고산(GoSan)** 이다. 군산은 `gu` 이고 파이썬 쪽 표기는 `GunS` 다.
> `GS_taglist.xlsx`, `gs_inp.inp`, `GSSource`, `pumpCommandGS`, `maria-ems-db-gs` 는 전부 고산이다.

---

## 4. 군산 격차 (G1~G4)

### G1. 백엔드가 분기하지 않는다

`epaMode` 분기(`DrvnConfig.java:255`)가 `if (wpp_code.equals("gs"))`(`:239`) 블록 **안쪽**에 있다.
군산은 `:229-233` else 경로에서 예측값을 그대로 `insertPumpComb()` 에 넘기고 끝난다.

- 스케줄러 빈 자체는 군산에서도 살아 있다 — `@Profile("!gm & !hp & !ji & !hy & !ss & !gm2 & !hp2 & !hy2 & !ji2")`
  (`DrvnConfig.java:43`)에 `gu`/`dev` 는 **제외되어 있지 않다.** 막힌 것은 239행 게이트 하나뿐이다.

### G2. `FLG='PRE'` 데이터 생산자가 없다 (가장 큰 과제)

2.4 항 참조. 군산에는 예측 관망해석 결과를 쓰는 주체가 없다.

**미완의 이식 시도가 하나 남아 있다** — `al/pump/main_guns_v1.py`:

| 사실 | 근거 |
|---|---|
| 군산 태그리스트를 읽는다 | `:29`, `:313` — `GunS_taglist.xlsx` |
| EPANET PRE 실행 호출이 들어 있다 | `:279`, `:284` 정의 → `:289`, `:291` 스레드 실행 — `epanet_ks/test.py --pre True` |
| 그러나 참조 경로 `epanet_ks/` 가 리포에 **없다** | `ls al/pump*/epanet_ks` 무결과 |
| DB 접속 키가 **고산** 그대로다 | `:70` — `maria-ems-db-gs` |
| 운영 실행 대상이 **아니다** | `al/Dockerfile:24` CMD 에 `main_gm.py`, `power/predictpower_Gosan_main.py`, `pump3/main_e.py` 만 |

→ 참고 자료로는 가치가 있으나, **현재 동작하지 않는 미완본**이다.

### G3. 조회 파라미터가 고산 하드코딩이다

`EpaService.java:47` (`link_id="10"`), `:98` (`node_id="고산(정)유출"`), `:100` (`/10`).
사이트 전환 수단이 없다.

EPANET 결과 테이블에는 사이트 구분 컬럼이 없으므로(별도 DB 인스턴스 전제) 조회 SQL에
사이트 조건을 넣을 수 없다. **LINK_ID / NODE_ID 를 바꾸는 것이 유일한 이식 수단이다.**

군산 대응 값은 이미 확정돼 있다 (`docs/sql/gunsan_ems_tag_seed.sql:45`, `:76`, `:105`):

| | 고산 | 군산 |
|---|---|---|
| LINK_ID | `10` | **`45`** — 군산(정) 송수 유량 (태그 `891-365-FRI-8950`) |
| NODE_ID | `고산(정)유출` | **`Bks-2496`** — 군산(정) 송수 메인 토출 (태그 `891-365-PRI-4000`) |

### G4. `TB_WPP_TAG_CODE` 의 `EPA_PUMP` 행 시드가 리포에 없다

`docs/sql/`, `deploy/` 어디에도 해당 행의 INSERT 문이 없다. 행이 없을 때의 증상:

- `getEpaModeInfo()` 가 `null` 반환 → `int epaMode = ...` 언박싱 NPE →
  `DrvnConfig.java:180-183` catch 에서 `epaMode = 0` 폴백. (조용히 수요예측으로 동작)
- `PUT /epa/setEpaMode` 는 **0행 UPDATE 로 조용히 실패**하는데, 프론트는 응답이 `'ok'` 면
  "적용 완료" 를 띄운다 (`PumpDrvnAnlyForGunsan.vue:821-825`).
  → 사용자는 모드를 바꿨다고 믿지만 아무것도 바뀌지 않는다.

**군산 DB에 이 행이 있는지 먼저 확인해야 한다.**

```sql
SELECT * FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'EPA_PUMP';
```

---

## 5. 적용 설계안

### 5.1 데이터 공급 (선결 과제)

| | 방식 | 장점 | 단점 |
|---|---|---|---|
| **A안 (권고)** | `epa/` Flask 에 `pre` 모드 추가. 예측 유량을 수요로 주입해 EPANET 실행 후 `TB_FR_VAL`/`TB_FP_VAL` 에 `FLG='PRE'` 저장 | `run_mo_simulation`(`epa/app/services/epa_service.py:419`) 구조 재사용. 군산 태그 시드(`docs/sql/gunsan_ems_tag_seed.sql`)가 이미 준비됨. 운영 스택에 `ems-py-api` 로 이미 떠 있음 | 저장 대상 테이블이 기존 `NODE_TABLE`/`LINK_TABLE`(SI 계열)과 달라 설정 분리 필요 |
| B안 | `al/pump3` 고산 파이프라인을 군산용으로 이식 (`main_guns_v1.py` 완성) | 고산과 동일 동작 보장 | 수요예측 모듈까지 딸려오고, `epanet_ks/` 부재·DB키 오류 등 미완 상태. wntr 벤더링 사본이 하나 더 늘어남 |
| C안 | `mo` 결과(`TB_FP_SI_VAL`/`TB_FR_SI_VAL`)를 EPAMODE 입력으로 사용 | 데이터가 이미 있음(군산은 현재 꺼져 있음) | **"예측"이 아니라 "현재 상태"** 라 의미가 달라진다. 펌프조합은 미래 시각용이므로 부적절 |

> A안의 선결 조건: 군산 관망 INP 확정. 6장 참조.

### 5.2 백엔드 일반화 (G1 · G3)

**분기 위치 이동** — `epaMode` 판정을 고산 블록 밖으로 빼서 비-`gs` 경로(`DrvnConfig.java:229-233`)에도
적용한다. 군산은 그룹 1건이므로 루프 안에서 flow/pressure만 교체하면 된다.

```java
// 개념 스케치 (DrvnConfig.java:229-233 자리)
} else {
    if (ts != null) {
        double f = flowDb, p = pressureDb;
        if (epaMode == 1) {
            Double ef = epaService.getEpaFlow(flowDb, ts, id);
            Double ep = epaService.getEpaPressure(pressureDb, ts, id);
            if (ef != null && ep != null) { f = ef; p = ep; }   // 5.3 폴백
        }
        insertPumpComb(f, p, id, ts);
    }
}
```

**하드코딩 외부화** — 기존 `dstrb.*` 관례를 따라 프로퍼티로 뺀다.

```properties
# application-gs.properties (현재 하드코딩과 동일한 값)
dstrb.epa.linkId=10
dstrb.epa.nodeId=고산(정)유출
dstrb.epa.pressureDivisor=10

# application-gu.properties
dstrb.epa.linkId=45
dstrb.epa.nodeId=Bks-2496
dstrb.epa.pressureDivisor=10
```

`EpaService` 는 `@Value` 로 주입받아 쓴다. `DrvnConfig` 가 이미
`@PropertySource("classpath:application-${spring.profiles.active}.properties")`(`:42`)를 쓰므로
관례가 일치한다.

> 고산 값은 현재 하드코딩과 **동일하게** 두어 회귀를 막는다.

### 5.3 견고성 — 결과 부재 시 폴백

현재 `selectGsAllNodeFirst` / `selectGsAllLinkFirst` 는 `Double` 을 반환하는데
`EpaService` 는 `double` 로 받는다 (`EpaService.java:66`, `:100`). 관망해석 결과가 없으면
**언박싱 NPE** 가 나고, `DrvnConfig.java:188-278` 의 try 에 걸려 **그 tick 의 펌프조합 생성이 통째로 스킵**된다.

군산은 PRE 생산이 새로 붙는 만큼 결측이 잦을 수 있다. **결과가 없으면 수요예측 값으로 폴백**하도록
`Double` 반환 + null 체크로 바꾸고, 폴백 발생을 WARN 로그로 남기는 설계를 권한다.

### 5.4 DB 시드 (G4)

`docs/sql/gunsan_ems_tag_seed.sql` 의 관례(멱등 · `ON DUPLICATE KEY UPDATE`)를 따른다.
`TB_WPP_TAG_CODE` 의 실제 PK/컬럼 구성을 확인한 뒤 확정할 것.

```sql
-- 개념. 실제 컬럼 구성 확인 후 확정
INSERT INTO TB_WPP_TAG_CODE (FUNC_TYP, DEFAULT_VALUE) VALUES ('EPA_PUMP', 0)
ON DUPLICATE KEY UPDATE FUNC_TYP = VALUES(FUNC_TYP);   -- 기존 운영값은 덮지 않는다
```

초기값은 `0`(수요예측)이 안전하다. 관망해석 데이터가 쌓이는 것을 확인한 뒤 UI 에서 켠다.

### 5.5 프론트 — 변경 불필요

군산 화면에 이미 완비돼 있다 (커밋 `d47d534`).

| 기능 | 위치 |
|---|---|
| 토글 배치 | `PumpDrvnAnlyForGunsan.vue:59` |
| 초기 조회 | `:352`, `:383-385` |
| 변경 + 확인 다이얼로그 | `:807-834` |

단, G4 미해결 상태에서는 "적용 완료" 를 띄우고도 실제로는 저장되지 않는다(4장 참조).

---

## 6. 선결 조건 · 미확정 항목

착수 전 반드시 확정해야 할 항목이다.

| # | 항목 | 현재 상태 | 확인 방법 |
|---|---|---|---|
| 1 | **군산 관망 INP 확정** | 문서가 서로 어긋난다. `deploy/gunsan/conf/epa/config.py:23-27` 은 여전히 고산 `gs_inp.inp` 를 가리키고 `SCHEDULER_ENABLED=False`(`:46`). 반면 `docs/sql/gunsan_ems_tag_seed.sql:12-13` 은 "군산 INP 의 배수지 4곳이 RESERVOIR→JUNCTION 으로 변경된 리비전" 존재를 전제한다 | inpEditor 에 등록된 군산 INP 파일 UUID 확인 (`inpEditor/BE/editor/doc/sql/gunsan_inp_mapping_seed.sql` 의 `@INP_FILE_ID`) |
| 2 | **`EPA_PUMP` 행 존재 여부** | 리포에 시드 없음 | 군산 DB 에 `SELECT ... WHERE FUNC_TYP='EPA_PUMP'` |
| 3 | **압력 `/10` 의 군산 적용성** | 고산 기준 단위 환산(m → kgf/cm²). 군산 INP 단위계 확인 필요 | 군산 INP 의 `[OPTIONS] UNITS`, 그리고 실측 태그 `891-365-PRI-4000` 의 단위와 대조 |
| 4 | **PRE 생산 주기 vs 조회 윈도** | 조회는 `startDate` 기준 **최근 3분** (`drvn_mssql.xml:330`, `:349`). 생산이 5분 주기면 조회 실패가 상시 발생 | 생산 주기 확정 후 윈도 조정 여부 판단 |
| 5 | **군산 운영 프로파일** | 운영은 `gu`(`deploy/gunsan/docker-compose.prod.yml:35`), dev 스택은 `dev`(`docker-compose.gunsan-dev.yml:46`) | **dev 로 띄우면 `gu` 분기도 타지 않는다.** 검증 시 프로파일 확인 필수 |
| 6 | **`dstrb.optidx` 이식 잔재** | `application-gu.properties:91` 이 고산과 동일한 `865-337-FRI-` | 군산 태그체계(`891-365-*`)와 대조. EPAMODE 와 직접 관계는 없으나 인접 설정 |

---

## 7. 리스크

| 리스크 | 내용 | 완화 |
|---|---|---|
| **고산 회귀** | `DrvnConfig` · `EpaService` 는 고산 운영 코드다. 분기 이동 시 고산 동작이 바뀌면 실제 펌프 제어에 영향 | 고산 프로퍼티 값을 현재 하드코딩과 동일하게 두고, 고산 경로는 코드 구조만 유지 |
| **결과 혼입** | EPANET 결과 테이블에 사이트 구분 컬럼이 없다. 군산에서 고산 INP 로 해석을 돌리면 군산 DB 에 고산 기준 결과가 쌓인다 | 선결 조건 1 해결 전에는 PRE 생산을 켜지 않는다 (현재 `SCHEDULER_ENABLED=False` 와 같은 취지) |
| **조합 생성 중단** | PRE 결과 결측 시 현재 구조는 NPE 로 해당 tick 전체를 스킵 | 5.3 폴백 도입 |
| **조용한 실패** | `EPA_PUMP` 행 부재 시 UI 는 성공을 알리고 백엔드는 0 으로 동작 | 5.4 시드 + `setEpaMode` 의 UPDATE 영향 행 수 검사 |
| **수동 조합 생성 경로 누락** | `DrvnService.pumpCombInsert()`(`:2254-2276`)는 고산 합성식을 쓰면서 **`epaMode` 를 보지 않는다.** 수동 생성 시에는 EPA 모드가 무시된다 | 의도된 동작인지 확인. 군산 적용 시 동일 경로 처리 방침 결정 |

---

## 8. 작업 순서

### 의존 관계

```
P0 사실 확인 ─┬─→ P1 스위치 정상화 (SQL 1건)
              ├─→ P2 백엔드 일반화 (코드)        ─┐
              └─→ P3 PRE 데이터 생산 (임계경로)  ─┴─→ P4 통합 검증 → P5 수동 경로(선택)
```

P2 와 P3 는 **병렬 가능**하다. P2 는 모드가 `0` 인 한 동작이 바뀌지 않아 단독 배포해도 무해하고,
P3 는 군산 INP 확정에 묶여 있어 리드타임이 길다. **임계경로는 P3 다.**

---

### P0. 사실 확인 — 코드 무변경

군산 운영 DB(`<internal-host>/EMS_DB`)에서 확인한다.

```sql
-- ① EPAMODE 스위치 행이 존재하는가 (G4)
SELECT * FROM TB_WPP_TAG_CODE WHERE FUNC_TYP = 'EPA_PUMP';

-- ② 예측 데이터가 살아 있는가 (EPA 모드에서도 실행 게이트로 남는다 — 2.5 참조)
SELECT DSTRB_ID, COUNT(*) AS cnt, MAX(RGSTR_TIME) AS last_ts
FROM   TB_CTR_TNK_RST
WHERE  DSTRB_ID IN ('Q_GunS_PREDICT', 'P_GunS_PREDICT')
       AND RGSTR_TIME >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY DSTRB_ID;

-- ③ PRE 관망해석 결과가 있는가 (없을 것으로 예상 = G2 확증)
SELECT FLG, COUNT(*), MAX(RGSTR_TIME) FROM TB_FR_VAL GROUP BY FLG;
SELECT FLG, COUNT(*), MAX(RGSTR_TIME) FROM TB_FP_VAL GROUP BY FLG;

-- ④ 군산 태그 시드가 적용됐는가
SELECT * FROM TB_EPA_TAG_INFO WHERE LOCATION_NM = '군산(정)';
```

코드 밖 확인 2건 (6장 선결조건 1·3):

- **군산 관망 INP 확정 여부** — inpEditor 등록본과 `deploy/gunsan/conf/epa/config.py:23-27` 의 불일치 해소
- **압력 단위** — 군산 INP `[OPTIONS] UNITS` ↔ 실측 태그 `891-365-PRI-4000` 대조 → `pressureDivisor` 확정

> **분기 판단**
> - ② 가 비어 있으면 → EPA 모드 이전에 **군산 예측 파이프라인부터** 손봐야 한다. 여기서 멈춘다.
> - ① 이 없으면 → 지금 UI 토글이 조용히 실패 중이다(4장 G4). P1 을 즉시 진행한다.
> - 군산 INP 가 없으면 → P3 착수 불가. INP 확보가 최우선 과제가 된다.

### P1. 스위치 정상화 (G4) — SQL 1건, 리스크 없음

`TB_WPP_TAG_CODE` 에 `EPA_PUMP` 행을 초기값 `0` 으로 시드한다 (5.4).

- **완료 기준**: UI 에서 토글 → 새로고침 후에도 값이 유지된다.
- 백엔드 동작은 아직 없다. **UI 의 거짓 성공 메시지만 제거**하는 단계다.

### P2. 백엔드 일반화 (G1 · G3 + 폴백)

- `EpaService` 하드코딩 3종 → `dstrb.epa.*` 프로퍼티 (5.2). **고산 값은 현행과 동일하게** 둔다
- `DrvnConfig` 의 `epaMode` 분기를 `wpp_code.equals("gs")` 게이트 밖으로 (5.2)
- `Double` 반환 + null 폴백 + WARN 로그 (5.3)

- **완료 기준 (2가지 모두)**
  1. **고산 회귀 없음** — `epaMode=0`/`1` 양쪽에서 변경 전과 조합 결과가 동일
  2. 군산에서 `epaMode=1` 로 켜도 폴백 WARN 만 남고 **조합은 정상 생성**된다
- 이 단계까지는 PRE 데이터 없이 안전하게 배포할 수 있다. 모드는 `0` 으로 둔 채 둔다.

### P3. PRE 데이터 생산 (G2) — 임계경로

**선결**: P0 의 군산 INP 확정. 방식은 5.1 A안 권고.

- `epa/` 에 `pre` 모드 추가. 저장 대상 테이블을 `TB_FP_VAL`/`TB_FR_VAL` 로 분리
  (기존 `NODE_TABLE`/`LINK_TABLE` 은 SI 계열이므로 설정 키를 새로 둘 것)
- 입력 수요는 예측값(`TB_CTR_TNK_RST`)에서 취한다
- **주기를 조회 윈도(3분, `drvn_mssql.xml:330`·`:349`)와 맞춘다.** 5분 주기면 상시 조회 실패한다
  → 생산 주기를 줄이거나 윈도를 넓히거나, 둘 중 하나를 P0 단계에서 결정

- **완료 기준**: 아래가 주기적으로 갱신된다
  ```sql
  SELECT MAX(RGSTR_TIME) FROM TB_FR_VAL WHERE LINK_ID = '45'       AND FLG = 'PRE';
  SELECT MAX(RGSTR_TIME) FROM TB_FP_VAL WHERE NODE_ID = 'Bks-2496' AND FLG = 'PRE';
  ```

### P4. 통합 검증

- **`gu` 프로파일로 기동한다.** dev 로 띄우면 분기를 타지 않는다 (6장 선결조건 5)
- 모드 `0` → 조합 A, 모드 `1` → 조합 B 가 서로 다른지 확인
- 로그의 `--- [DEBUG] EPA Mode (epaMode=1) ---` (`DrvnConfig.java:260`) 로 경로 진입 확인
- 폴백 WARN 발생 빈도를 관찰해 P3 의 주기 설정을 재조정

### P5. 수동 조합 생성 경로 (선택)

`DrvnService.pumpCombInsert()` 가 `epaMode` 를 보지 않는 문제(2.5). 고산에도 이미 존재하는
불일치이므로, 의도된 동작인지 확인한 뒤 군산 방침과 함께 결정한다.
