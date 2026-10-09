# 군산 밸브제어 도입 — 착안점 정리 및 결정 대기 항목

> **목적**: "군산에서 펌프조합 결과를 바탕으로 밸브제어를 실행한다" 는 요구에 대해,
> 코드에 이미 무엇이 있고 무엇을 새로 만들어야 하는지를 사실로 정리한다.
> **성격**: 설계 확정 전 단계. 담당자 확인이 필요한 항목은 6장에 **기입란**으로 비워 두었다.
> 6장이 채워지면 7장 매트릭스를 따라 바로 착수할 수 있다.
> **조사 기준**: `master` / `51577c7` 시점 소스 직접 확인. 모든 단언에 `파일:라인` 근거를 붙였다.
> **관련 문서**: `docs/gunsan-epa-mode-analysis.md` (군산 EPAMODE),
> `inpEditor/BE/editor/doc/reference/legacy-ems-pump-control-summary.md` (자율제어 주기·제어이력).

---

## 1. 결론 요약

밸브제어를 **처음부터 만들 필요가 없다.** 배관은 이미 다 깔려 있고, 부안(`ba`)에서
**명령 생성부만 주석 처리**된 상태다.

1. 발행(Kafka 전송)과 상태확인 로직은 구현되어 동작한다.
2. 명령을 만들어 대기열에 넣는 부분(`ins／ertPumpControlData(..., "VVK", ...)`)이 전부 주석 처리돼 있다.
3. 군산이 이미 타고 있는 `pumpCommand()` 안, 주석이 있던 바로 그 자리가 삽입 지점이다.

남은 것은 **① 군산 밸브 태그 확보 ② 생성 조건 정의 ③ 하드코딩 2곳의 사이트 일반화** 다.

---

## 2. 현행 밸브 제어 파이프라인

### 2.1 명령 생명주기 (3단계)

모든 제어 명령(펌프·주파수·밸브)이 같은 대기열 `TB_HMI_CTR_TAG` 를 공유한다.
`ANLY_CD` 가 명령 종류를, `FLAG` 가 진행 상태를 나타낸다.

```
[생성]  insertPumpControlData(optIdx, 명칭, 태그, ANLY_CD, value)      PumpService:2575
          → INSERT TB_HMI_CTR_TAG (FLAG=0)                             pump_mssql.xml:271-276

[발행]  PumpScheduler.pumpTask()               1분 주기                 PumpScheduler:59-61
          → selectCtrTagList(FLAG=0) → pumpCommandTask(ctrReadyList)    PumpScheduler:81, :104
          → ANLY_CD 별 디스패치                                          PumpService:310-360
              · ANLY_CD="VVK" && FLAG="0"  → sendCtrTagVVKItem()        PumpService:355-357
          → Kafka 토픽 'ems_result' 전송, FLAG=1, 이력 적재              PumpService:1236-1250

[확인]  PumpScheduler.pumpStatusTask()         30초 주기                PumpScheduler:183-184
          → selectCtrTagList(ANLY_CD="VVK", FLAG=1)
          → VVKStatusTask() → 실측 태그 조회 → FLAG=2 + 이력             PumpService:521-568
```

`TB_HMI_CTR_TAG` 컬럼: `CTR_NM`, `OPT_IDX`, `TAG`, `TIME`, `VALUE`, `ANLY_CD`, `AI_STATUS`, `FLAG`
(`pump_mssql.xml:273`). `FLAG` 는 `0`=미전송 / `1`=전송 / `2`=확인완료.

### 2.2 구현 상태

| 조각 | 위치 | 상태 |
|---|---|---|
| 발행 `sendCtrTagVVKItem()` | `PumpService:1236` | ✅ 구현됨. 사이트 무관 |
| 대기열 디스패치 | `PumpService:355-357` | ✅ 구현됨. 사이트 무관 |
| 상태확인 `VVKStatusTask()` | `PumpService:521` | ✅ 구현됨 |
| 상태확인 SQL `selectVVKStatusCheck` | `pump_mssql.xml:840-860` | ⚠️ **부안 태그 하드코딩** (`892-482-VVB-8025`), 파라미터 없음 |
| 스케줄러 훅 | `PumpScheduler:222-231` | ⚠️ **`if(wpp_code.equals("ba"))` 부안 한정** |
| **명령 생성** | `PumpService:1599`, `:1615`, `:1651`, `:1734` | ❌ **전부 주석 처리** |

### 2.3 부안 선례 (주석 처리된 원본)

`pumpCommand()` 안, 펌프를 켜고 끄는 지점에 나란히 있다.

```java
// PumpService.java:1591-1600  — 펌프 켤 때
insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN", 1);
insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "WAIT", 180);
insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN_STATUS", 0);
//  부안 무장B(17) 밸브 닫기, 펌프 켤때 키고 닫기
//  if (wpp_code.equals("ba") && pumpIdx.equals("17")) {
//      insertPumpControlData(nowOptIdx, "무장(가) 바이패스 밸브#2 닫힘", "892-482-VVK-8026", "VVK", 1);
//  }

// PumpService.java:1650-1656  — 펌프 끌 때 (밸브를 먼저 연다)
//  if (wpp_code.equals("ba") && offItem.get("PUMP_IDX").toString().equals("17")) {
//      insertPumpControlData(nowOptIdx, "무장(가) 바이패스 밸브#2 열림", "892-482-VVK-8025", "VVK", 1);
//  }
insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "STOP", 1);
```

읽어낼 수 있는 설계 의도:

- **밸브는 특정 펌프(IDX 17)에 종속**되어 있었다. 조합 전체가 아니라 개별 펌프 on/off 에 반응한다.
- **열기와 닫기가 서로 다른 태그**다 (`VVK-8025` 열림 / `VVK-8026` 닫힘). 각각에 `1` 을 쓴다.
- **순서가 비대칭**이다 — 켤 때는 펌프 명령 뒤, 끌 때는 펌프 명령 **앞**에 밸브를 넣는다.
- 제어 태그(`VVK-…`)와 상태확인 태그(`VVB-8025`, `pump_mssql.xml:855`)가 **다르다.**

> ⚠️ 주석 처리된 이유는 코드·커밋 메시지 어디에도 없다. 되살리기 전에 **왜 껐는지** 확인이 필요하다
> (6장 D7).

---

## 3. 밸브 태그를 관리할 수 있는 자리

코드에 태그를 박은 부안 방식 말고, **DB 로 관리하는 자리가 이미 두 곳 있다.**

| | 위치 | 컬럼 | 사이트 분리 | 현재 용도 |
|---|---|---|---|---|
| **A** | `TB_CTR_PUMP_REQ_OPT` "펌프 동작 선행조건" | `REQ_TAG`(상태), `REQ_CTR_TAG`(제어 시작), `REQ_CTR_STOP_TAG`(제어 종료), `STD_VALUE`(기준값), `USE_YN` | ✅ **`WPP_CODE` 가 PK 첫 컬럼** | 상태 판정에만 사용 (`selectValveStatusCheck`, `pump_mssql.xml:763`) |
| **B** | `TB_CTR_PRF_PUMPMST_INF` 펌프 마스터 | `VVB_D_TAG`("토출밸브 연동"), `VVB_D_TAG_USE_YN` | ✅ `WPP_CODE` PK | 코드에서 참조하는 곳 없음 |
| C | 자바 소스 하드코딩 | — | ❌ `wpp_code` if 문 | 부안 (주석 처리됨) |

**A 의 `REQ_CTR_TAG` / `REQ_CTR_STOP_TAG` 는 "선행조건 제어 시작/종료 태그" 라는 이름과 컬럼이
이미 있는데, 현재 아무도 제어에 쓰지 않는다.** `selectValveStatusCheck` 가 SELECT 목록에 담아
오지만(`pump_mssql.xml:772-773`) 소비하는 코드가 없다. → **제어 발행 자리가 설계상 비어 있는 셈**이며,
군산 밸브제어를 여기에 채우는 것이 가장 자연스럽다.

---

## 4. 군산의 현재 위치

### 4.1 군산이 타는 제어 경로

```
PumpScheduler.pumpAiControlTask()  5분 주기                    :113-116
  └ 대상 사이트 gs/gu/ba/wm/gr 이고 AI 운전 모드일 때            :125
      └ gs → pumpCommandGS() / wm → pumpCommandWM()
        그 외(군산 포함) → pumpCommand()                        :165-172
                            └ PumpService:1416  ← 밸브 생성 삽입 지점
```

즉 **군산은 부안과 같은 `pumpCommand()` 를 이미 쓰고 있다.** 주석 처리된 밸브 코드가 있던
바로 그 메서드다. 새 메서드를 만들 필요가 없다.

### 4.2 ⚠ 군산은 이미 밸브 상태확인에 의존하고 있다

`pumpStatusTask` 는 사이트에 따라 두 갈래로 나뉜다 (`PumpScheduler:207-216`).

```java
if (wpp_code.equals("gr") || wpp_code.equals("ba") || wpp_code.equals("wm")) {
    pumpService.pumpStatusTaskPumpOnly(ctrRunningList);   // 펌프만 확인
} else {
    pumpService.pumpStatusTask(ctrRunningList);           // 밸브 + 펌프 확인  ← 군산
}
```

`pumpStatusTask` 는 **밸브 상태와 펌프 상태가 둘 다 정확히 1건씩 조회되어야** 제어를
완료(`FLAG=2`) 처리한다 (`PumpService:389-393`).

```java
List<...> valveStatusList = selectValveStatusCheck(ctrItem);   // TB_CTR_PUMP_REQ_OPT 조인
List<...> pumpStatusList  = selectPumpStatusCheck(ctrItem);    // PMB_TAG
if (valveStatusList.size() == 1 && pumpStatusList.size() == 1) { ... }
```

→ **군산 `TB_CTR_PUMP_REQ_OPT` 에 행이 없으면 밸브 목록이 비어 `RUN_STATUS`/`STOP_STATUS` 가
영원히 `FLAG=2` 로 넘어가지 않는다.** 밸브제어 도입 이전에 현재 상태를 확인해야 한다 (6장 D0).

### 4.3 군산 밸브 태그는 아직 없다

`docs/sql/gunsan_ems_tag_seed.sql` 의 군산 태그(`891-365-*`)는 `FRI`(유량)·`PRI`(압력)·`LEI`(수위)
뿐이고 **`VVB`/`VVK` 계열이 하나도 없다.** 태그 확보가 선결 조건이다 (6장 D4).

---

## 5. "펌프조합이 끝나면" 의 코드상 위치

요구사항의 "펌프조합이 끝나면" 이 가리킬 수 있는 지점이 둘이라, 먼저 구분해 둔다.

| 후보 | 위치 | 성격 | 밸브제어 적합성 |
|---|---|---|---|
| ① 조합 **계산** 완료 | `DrvnConfig.insertPumpComb()` 30초 주기 `:338` | 추천 조합을 만들어 DB 에 쌓을 뿐. AI 운전 여부와 무관 | ❌ 이 시점엔 제어 의사결정이 없다 |
| ② 조합 **제어 발행** | `PumpService.pumpCommand()` 5분 주기 `:1416` | AI 운전 모드에서 실제 펌프 명령이 확정되는 지점. `onList`/`offList` 가 여기서 정해진다 | ✅ **부안 선례도 여기** |

**②를 기준으로 설계한다.** ①에서 밸브를 움직이면 AI 운전이 꺼져 있어도 밸브가 동작하게 되어 위험하다.

---

## 6. 결정 대기 항목 — 담당자 확인 후 기입

> 아래 표의 **[ 기입 ]** 칸을 채우면 7장 매트릭스로 착수 범위가 확정된다.
> 확인 일자·확인자도 함께 남길 것.

| 확인 일자 | 확인자 | 비고 |
|---|---|---|
| [ 기입 ] | [ 기입 ] | |

### D0. (현황) 군산 `TB_CTR_PUMP_REQ_OPT` 에 행이 있는가

밸브제어와 별개로 **지금 군산 펌프 제어가 정상 완료 처리되고 있는지**를 가르는 항목이다(4.2 참조).

```sql
SELECT * FROM TB_CTR_PUMP_REQ_OPT WHERE WPP_CODE = 'gu';
-- 행이 없다면: 최근 제어가 FLAG=2 로 넘어갔는지 확인
SELECT ANLY_CD, FLAG, COUNT(*) FROM TB_HMI_CTR_TAG
WHERE  TIME >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY ANLY_CD, FLAG;
```

- 결과: **[ 기입 ]**

### D1. 밸브의 성격 — 무엇에 연동되는가

| 선택 | 의미 | 태그 관리 위치 |
|---|---|---|
| ☐ 펌프별 토출밸브 | 펌프 1대 : 밸브 1개. 조합의 on/off 목록을 그대로 따라간다 | 3장 B (`VVB_D_TAG`) 또는 A |
| ☐ 계통 공용 밸브 | 계통에 1~2개. 특정 펌프/조건에서만 여닫는다 (부안 바이패스 방식) | 3장 A 또는 C |
| ☐ 분기점 제어밸브 | 조합의 산출 유량·압력을 근거로 여닫는다. 펌프 on/off 와 무관 | 별도 판단 로직 필요 |

- 선택: **[ 기입 ]**
- 부연(대상 밸브 이름·개수): **[ 기입 ]**

### D2. 제어 방식

| 선택 | 의미 | 기존 코드 재사용성 |
|---|---|---|
| ☐ 열기/닫기 2태그 | 태그가 둘, 각각에 `1` 을 쓴다 (부안 `VVK-8025`/`8026` 방식) | ✅ 그대로. `TB_CTR_PUMP_REQ_OPT` 의 `REQ_CTR_TAG`/`REQ_CTR_STOP_TAG` 구조와 일치 |
| ☐ 단일 태그 0/1 | 한 태그에 `1`=열기, `0`=닫기 | ⚠️ `sendCtrTagVVKItem` 이 전송 5초 뒤 자동으로 `VALUE=0` 을 재전송한다(`PumpService:1251-1252`). 충돌 여부 확인 필요 |
| ☐ 개도율(비례) | 0~100 % 를 쓴다 | ❌ `insertPumpControlData` 는 `int`(`:2575`). `insertPumpControlDataDouble`(`:2598`) 경로 + 새 `ANLY_CD` 필요 |

- 선택: **[ 기입 ]**

### D3. 실행 타이밍

| 선택 | 의미 | 변경 범위 |
|---|---|---|
| ☐ 펌프 명령과 동시 | `pumpCommand()` 에서 RUN/STOP 과 함께 대기열에 넣는다 (부안 방식) | 작음 |
| ☐ 펌프 기동 확인 후 | `pumpStatusTask` 가 `FLAG=2` 를 찍은 뒤 밸브 명령 생성 | 중간. 새 훅 + 상태 추적 필요 |
| ☐ 밸브 먼저, 펌프 나중 | 밸브 열림 확인 후 펌프 기동 | 큼. 대기열을 순서 의존적으로 바꿔야 함 |

- 선택: **[ 기입 ]**
- 켤 때와 끌 때 순서가 다른가(부안은 비대칭 — 2.3 참조): **[ 기입 ]**

### D4. 군산 밸브 태그 목록

확보되는 대로 아래 표를 채운다. `TB_CTR_PUMP_REQ_OPT` 시드의 원본이 된다.

| 밸브 명칭 | 대상 펌프 IDX | 열기 제어 태그 | 닫기 제어 태그 | 상태 확인 태그 | 기준값(STD_VALUE) |
|---|---|---|---|---|---|
| [ 기입 ] | [ 기입 ] | [ 기입 ] | [ 기입 ] | [ 기입 ] | [ 기입 ] |
| | | | | | |

> 참고: 군산 태그 접두는 `891-365-*` 다. 제어 태그와 상태 태그는 부안처럼 다를 수 있다.

### D5. 실패·타임아웃 처리

- 밸브가 지정 시간 내에 열리/닫히지 않으면? (부안은 `WAIT` 180초 패턴을 펌프에 씀)
  → **[ 기입 ]**
- 밸브 실패 시 펌프 제어를 되돌리는가, 그대로 두는가, 알람만 내는가?
  → **[ 기입 ]**

### D6. 수동 개입·안전조건

- 운전원이 밸브를 수동으로 만졌을 때 자동제어가 덮어써도 되는가? → **[ 기입 ]**
- 절대 닫으면 안 되는 조건(최소 유로 확보 등)이 있는가? → **[ 기입 ]**
  > 고산 `pumpCommandGS()` 에는 "신정수장 펌프가 전부 정지되는 명령이면 중단 + 알람" 안전장치가
  > 있다(`PumpService:1789-1825`). 밸브에도 대응물이 필요한지 확인.

### D7. 부안 밸브 코드를 왜 껐는가

주석 처리 사유가 코드·커밋 어디에도 없다. 군산에 같은 문제가 재현될 수 있다.

- 사유: **[ 기입 ]**

---

## 7. 결정 → 작업 매트릭스

D1~D3 이 정해지면 아래에서 착수 범위가 나온다. **공통** 항목은 어떤 선택이든 필요하다.

### 공통 (선택 무관)

| # | 작업 | 대상 |
|---|---|---|
| C1 | 군산 밸브 태그 확보 및 시드 SQL 작성 | `docs/sql/` (기존 `gunsan_ems_tag_seed.sql` 관례 — 멱등 `ON DUPLICATE KEY UPDATE`) |
| C2 | 스케줄러 훅에 `gu` 추가 | `PumpScheduler:222` `if(wpp_code.equals("ba"))` |
| C3 | 상태확인 SQL 의 부안 태그 하드코딩 제거 → 파라미터화 | `pump_mssql.xml:840-860` (`selectVVKStatusCheck`), `PumpService:4068` |
| C4 | D0 결과에 따라 `TB_CTR_PUMP_REQ_OPT` 군산 행 정비 | DB |

### D1 별

| 선택 | 추가 작업 |
|---|---|
| 펌프별 토출밸브 | `pumpCommand()` 의 on/off 루프에서 펌프별 밸브 태그를 조회해 생성. 태그는 `TB_CTR_PUMP_REQ_OPT`(A) 또는 `VVB_D_TAG`(B) 에서 읽는다 |
| 계통 공용 밸브 | 조건 판정(어느 펌프/조합일 때 여닫는가)을 별도 정의. 부안처럼 특정 `PUMP_IDX` 종속이면 구현이 가장 작다 |
| 분기점 제어밸브 | 조합 산출값(유량·압력)에 대한 판단 로직을 새로 설계. `pumpCommand()` 밖 별도 컴포넌트가 적절할 수 있다 |

### D2 별

| 선택 | 추가 작업 |
|---|---|
| 열기/닫기 2태그 | 없음. `insertPumpControlData(..., "VVK", 1)` 두 번 호출로 끝 |
| 단일 태그 0/1 | `sendCtrTagVVKItem` 의 5초 후 `VALUE=0` 재전송(`:1251-1252`)과의 충돌 검토 후 분기 |
| 개도율 | 새 `ANLY_CD`(예: `VVP`) 정의 + `insertPumpControlDataDouble` 경로 + 디스패치(`:355`) 추가 + 상태확인 비교 로직 신규 |

### D3 별

| 선택 | 추가 작업 |
|---|---|
| 펌프 명령과 동시 | `pumpCommand()` 의 주석 자리에 생성 코드 삽입 (`:1598`, `:1650`) |
| 펌프 기동 확인 후 | `pumpStatusTask` 의 `FLAG=2` 처리부(`:404-424`)에 밸브 생성 훅 추가 |
| 밸브 먼저, 펌프 나중 | 대기열에 선후 의존을 도입해야 함. `WAIT`/`*_STATUS` 패턴 확장 검토 |

---

## 8. 검증 계획 (착수 후)

1. **`gu` 프로파일로 기동한다.** dev 프로파일은 `PumpScheduler` 자체가 `@Profile("!dev && …")`
   (`PumpScheduler:38`)로 **빈이 생성되지 않아** 제어가 전혀 돌지 않는다.
2. `TB_HMI_CTR_TAG` 에 `ANLY_CD='VVK'` 행이 `FLAG` 0 → 1 → 2 로 진행하는지 확인
   ```sql
   SELECT TIME, CTR_NM, TAG, VALUE, ANLY_CD, FLAG FROM TB_HMI_CTR_TAG
   WHERE  ANLY_CD = 'VVK' ORDER BY TIME DESC LIMIT 20;
   ```
3. `TB_HMI_CTR_LOG` 에 이력이 남는지, 밸브 실측 태그가 실제로 변하는지 대조
4. 펌프 제어 완료(`RUN_STATUS`/`STOP_STATUS` → `FLAG=2`)가 밸브 도입 전후로 회귀하지 않는지 확인 (4.2)

---

## 9. 리스크

| 리스크 | 내용 | 완화 |
|---|---|---|
| **실제 설비 동작** | 밸브는 물리 설비다. 잘못된 명령이 관로 차단으로 이어질 수 있다 | D6 안전조건 확정 전 운영 반영 금지. 테스트 모드(`checkTestMode()`, `PumpScheduler:65`) 활용 |
| **부안 회귀** | `pumpCommand()` 는 부안·고령·군산이 공유한다. 사이트 조건 없이 넣으면 부안이 함께 동작한다 | 생성 코드에 반드시 `wpp_code` 조건을 건다 |
| **끈 이유 미상** | 부안 밸브 코드를 왜 주석 처리했는지 불명 (D7) | 확인 전에는 같은 구조를 그대로 되살리지 않는다 |
| **상태확인 하드코딩** | `selectVVKStatusCheck` 가 부안 태그 고정이라, 군산에서 켜면 **부안 태그를 조회한다** | C3 를 C2 보다 먼저 하거나 동시에 반영 |
| **제어 완료 미처리** | 군산 `TB_CTR_PUMP_REQ_OPT` 가 비어 있으면 펌프 제어가 `FLAG=2` 로 안 넘어간다 | D0 로 현황부터 확인 |
