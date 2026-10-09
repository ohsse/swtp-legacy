# AI운전 / AI추천 모드 — 펌프 제어 명령은 누가 언제 만드는가

> **목적**: 펌프 그룹의 AI 모드(0 운전 / 1 추천 / 2 분석)에 따라 제어 명령의 **생성 → 발행 → 확인**이
> 누구에 의해, 어떤 주기로, 어떤 게이트를 거쳐 일어나는지에 답한다.
> **성격**: 사실 확인 문서다. 모든 단언에 `파일:라인` 근거를 붙였고, 확인하지 못한 것은 "미확정"으로 남겼다.
> 코드 변경은 포함하지 않는다. 7장의 관찰 기록도 본 문서에서 수정하지 않는다.
> **조사 기준**: `master` / `021dc43` 시점 소스 + 워킹트리. 워킹트리 수정분(`AiService.java` 1752행 이하,
> `PumpService.java` 3696행 이하)은 본 문서가 인용하는 구간과 겹치지 않는다 — 단 7장 #4 는 워킹트리 변경을 언급한다.
> **관련 문서**: `docs/gunsan-pump-control-kafka.md` (태그·payload·발행 게이트·3Hz 램프 — 본 문서는 이를 반복하지 않는다),
> `docs/gunsan-valve-control-plan.md` (명령 생명주기 3단계·`TB_HMI_CTR_TAG` 컬럼).

---

## 1. 결론 요약

1. **모드는 `TB_WPP_TAG_CODE` 에 있다.** `FUNC_TYP='PumpStatus'` 행의 `DEFAULT_VALUE` 가 펌프 그룹(`TAG_GRP`)별
   모드다 (`ai_mssql.xml:2734-2743`, `pump_mssql.xml:901-910`). 그룹마다 다른 모드를 가질 수 있다.
2. **두 모드는 명령 내용이 완전히 같고, 생성 트리거만 다르다.** 자동(`PumpScheduler.java:171`)도 수동(`AiService.java:1911`)도
   결국 `PumpService.pumpCommand()` 를 부른다. 태그·값·펄스·3Hz 램프에 모드별 차이는 없다.
3. **발행(`pumpTask`, 1분)과 확인(`pumpStatusTask`, 30초)은 두 모드 공통**이다 (`PumpScheduler.java:61`, `:184`).
   AI운전 분기와 AI추천 분기의 발행 코드는 글자까지 같다 (`:71-84` vs `:86-106`).
4. **쿨다운이 비대칭이다.** 수동 승인 경로만 `pumpCommandStatus()` 의 5분 쿨다운을 타고(`PumpService.java:140`, `:3439-3444`),
   자동운전 경로는 `pumpCommandStatusMin()` 이라 쿨다운이 없다 (`PumpScheduler.java:143`).
5. **모드 전환은 어느 방향이든 대기열을 비운다.** `updateAiStatus()` 가 0/1/2 모든 분기에서 `initCtrTag()` 를 호출해
   `FLAG` 0·1 명령을 전부 `3`(폐기)으로 바꾼다 (`AiService.java:1424`, `:1456`, `:1483`, `pump_mssql.xml:101-107`).

---

## 2. 모드 값과 판정

### 2.1 값·상수·라벨

| 값 | 상수 (`PumpService.java:71-79`) | 화면 라벨 (`AiMode.vue:26`) | 제어 |
|---|---|---|---|
| `0` | `AI_CONTROL` | **AI** (AI운전) | 스케줄러가 자동 생성 |
| `1` | `AI_RECOMMEND` | **AI 추천** | 사용자 승인 후 생성 |
| `2` | `AI_ANALYZE` | AI 분석 | 생성 없음 |

### 2.2 저장 위치

```sql
-- ai_mssql.xml:2734-2743 (selectAiStatus), pump_mssql.xml:901-910 동일
SELECT TAG_GRP AS PUMP_GRP, DEFAULT_VALUE AS AI_STATUS
FROM   TB_WPP_TAG_CODE
WHERE  FUNC_TYP = 'PumpStatus'
ORDER  BY PUMP_GRP
```

```sql
-- ai_mssql.xml:2745-2754 (updateAiStatus)
UPDATE TB_WPP_TAG_CODE SET DEFAULT_VALUE = #{STATUS}
WHERE  TAG_GRP = #{PUMP_GRP} AND FUNC_TYP = 'PumpStatus'
```

> **기존 문서 정정**: `docs/gunsan-pump-control-kafka.md:169` 는 모드 저장처를 `TB_CTR_AI_INF.AI_STATUS` 로 적고 있으나
> 실제 SQL 은 위와 같이 `TB_WPP_TAG_CODE` 다. 본 문서에서는 기존 문서를 고치지 않고 여기에만 기록한다.

### 2.3 판정 함수는 "하나라도" 기준이다

| 함수 | 위치 | 반환 |
|---|---|---|
| `AiService.aiRecommendStatus()` | `AiService.java:1989-2002` | 어느 그룹이든 `1` 이면 `true` |
| `AiService.aiControlStatus()` | `:2007-2020` | 어느 그룹이든 `0` 이면 `true` |
| `PumpService.aiControlStatus()` | `PumpService.java:3513-3526` | 위와 동일 (별도 구현) |
| `PumpService.getAiControlStatus()` | `:3533-3550` | 순회 중 첫 `0` → 0, 첫 `1` → 1, 없으면 2 |

그룹별로 다른 모드가 섞여 있으면 두 판정이 동시에 `true` 일 수 있다. 다만 **명령 생성 대상은 모드별로 따로 골라내므로**
서로 침범하지 않는다:

```sql
-- pump_mssql.xml:747-753 (selectAiPumpGrpList) — PumpService.selectAiPumpGrpListStr(모드) :3278
SELECT TAG_GRP AS 'PUMP_GRP' FROM TB_WPP_TAG_CODE
WHERE  FUNC_TYP = 'PumpStatus' AND DISPLAY_ID = 'EMSPumpControl'
AND    DEFAULT_VALUE = #{default_value}
```

`selectAiStatus`(2.2) 에는 없는 `DISPLAY_ID='EMSPumpControl'` 조건이 여기엔 있다. `PumpStatus` 행이 다른 `DISPLAY_ID` 로도
존재한다면 "모드 판정"과 "대상 그룹 선별"이 어긋날 수 있다 — 운영 DB 에서 그런 행이 있는지는 **미확정**.

---

## 3. 두 모드에 공통인 것 — 발행과 확인

명령 생명주기 3단 중 **생성만** 모드에 따라 갈린다. 나머지 둘은 같다.

```
[발행] PumpScheduler.pumpTask()        cron "0 * * * * *" (1분)        PumpScheduler.java:60-61
         → 사이트 화이트리스트 + checkTestMode()                        :64-65
         → aiRecommendStatus() 이면 :71-84 분기
           else if aiControlStatus() 이면 :86-106 분기                   ← 두 분기 코드 동일
             → FLAG=0 있고, FLAG=1 없고, checkCtrTestMode() 이면          :79 / :97
             → pumpCommandTask(ctrReadyList)                            :81 / :104

[확인] PumpScheduler.pumpStatusTask()  cron "0,30 * * * * *" (30초)     :183-184
         → aiRecommendStatus() || aiControlStatus()                     :188
         → FLAG=1 & ANLY_CD LIKE 'STATUS' → 사이트별 상태확인             :190-215
```

`pumpTask` 가 `aiRecommendStatus` 를 먼저 보므로 한 그룹이라도 `1` 이면 "추천" 분기의 로그(`#pumpTask-Recommend`)가 찍히지만,
두 분기가 하는 일은 같아 실질 영향은 없다.

발행 이후의 태그·payload·게이트·3Hz 램프·펄스 방식은 `docs/gunsan-pump-control-kafka.md` 2~4장에 있다.

---

## 4. AI운전 모드 (`0`) — 스케줄러가 생성한다

```
PumpScheduler.pumpAiControlTask()      cron "20 */5 * * * *" (5분)      PumpScheduler.java:114-116
  → 사이트 gs|gu|ba|wm|gr + checkTestMode()                              :125
  → pumpService.aiControlStatus()          ← 한 그룹이라도 0              :126
  → selectAiPumpGrpListStr(AI_CONTROL)     ← 0 인 그룹만 대상            :127
  → FLAG 0·1 이 모두 비어야 pumpRunningStatus = true                     :129-140
  → pumpCommandStatusMin(pumpGrpStr)       ← 쿨다운 없음 (4.1)           :143
  → isChange && pumpRunningStatus                                        :146
  → changePumpList(true, pumpGrpStr) 가 비어있지 않으면                    :151
  → gs: pumpCommandGS / wm: pumpCommandWM / 그외: pumpCommand             :165-172
```

사람 개입이 없다. 대기열(`TB_HMI_CTR_TAG`, `FLAG=0`)에 적재되면 다음 `pumpTask`(최대 1분 뒤)가 발행한다.
`changePumpList()` 가 무엇을 비교하는지는 `docs/gunsan-pump-control-kafka.md` 4.2절.

### 4.1 `pumpCommandStatus` 와 `pumpCommandStatusMin` 의 차이

둘 다 `PumpService.java` 에 있고 구조가 같다. **다른 점은 한 블록뿐이다.**

| | `pumpCommandStatus()` `:95-160` | `pumpCommandStatusMin()` `:167-217` |
|---|---|---|
| FLAG=1 있을 때 | `isRunning=true` `:110-119` | 동일 `:182-190` |
| FLAG=0 있을 때 | `isRunning=false`, `isChange`=변경유무 `:120-130` | 동일 `:191-201` |
| 둘 다 없을 때 | **마지막 완료 명령과 5분 미만이면 `isRunning=true`** `:134-146` | 이 블록 없음 `:202-212` |
| 호출처 | 웹 승인 경로 (`AiService.java:1956`, `:1958`, `:1973`) | 자동운전 스케줄러 (`PumpScheduler.java:143`) |

쿨다운 상수는 `checkTimeDifference()` `:3439-3444` — 기본 30분, **군산만 5분**. `PumpScheduler.java:144` 에
`pumpCommandStatus` 호출이 주석으로 남아 있어, 자동운전에서도 쿨다운을 쓰던 시기가 있었음을 짐작할 수 있으나 경위는 **미확정**.

---

## 5. AI추천 모드 (`1`) — 사용자가 승인한다

이 모드에서 `pumpAiControlTask` 는 `:126` 에서 `false` 를 받아 **아무것도 하지 않는다.** 대신 프론트가 감시하고 사람이 승인한다.

### 5.1 프론트 감시 — 10분마다 예측 vs 실측

```
App.vue startInterval()                                                  App.vue:464-518
  → 다음 10분 경계 + 10초에 첫 실행, 이후 10분 간격                         :470-471, :515
  → changePumpOnOff()                                                    :266-311
      → GET /ai/selectPumpPrdctOnOffStatus?pump_grp=1, =2                :275-276  (그룹 3~5 는 주석 :277-279)
      → GET /ai/selectAiStatus → store.mode0~4                           :282, :305-309
      → 차이 추출                                                        :289-291
          nowUseData : value ≠ nowUse           (가동 여부)
          nowHzData  : FREQ.toFixed(0) ≠ nowFreq.toFixed(0)  (주파수)
          nowPriData : TUBE_PRSR_PRDCT.toFixed(1) ≠ nowPri.toFixed(1)  (압력)
      → errChecker()                                                     :312-382
          → GET /ai/pumpCommandStatus                                    :313
          → 차이 있음 && isRunning==false && data.length>0               :314-315
              → 알람음 재생 + OnOffEvent=true (팝업)                       :317-320
              → 그룹별 메시지 조립 (고령 4·7번 펌프는 압력으로 판정)         :322-373
          → isRunning==true || data 비어있음 → 팝업 닫음                   :376-380
```

`data` 는 `pumpCommandStatus` 가 돌려주는 변경 대상 문자열이다. **차이가 있어도 `isRunning==true` 면 팝업이 뜨지 않는다** —
진행중 명령이 있거나(FLAG=1) 마지막 명령 후 5분 미만이면(4.1) 조용히 지나간다.

### 5.2 팝업 — `OnOffAlarm.vue`

- 그룹별 체크박스와 모드 토글은 **`store.modeN == 1` 인 그룹만** 노출되며 기본 체크 상태다 (`:15-63`, `:138-142`).
- 모든 그룹이 `1` 이 아니면 `isAnly=true` 로 "닫기" 버튼만 보인다 (`:132-137`, `:97-101`).
- 팝업 안 `AiMode` 토글은 `isPopup=true` 라 클릭 핸들러가 없다 — 표시 전용 (`AiMode.vue:11-15`).
- "적용" → `handleCloseBtn(pump_grp)` → 부모 `closeBtn` emit, 중복 클릭은 `isLoading` 으로 막는다 (`:85-91`, `:145-158`).

### 5.3 승인 → 명령 생성

```
App.vue closeBtn(pump_grp)                                               App.vue:384-410
  → OnOffEvent=false, alert('펌프 상태 변경 요청이 전송되었습니다.')          :386-388   ← API 호출 전
  → 어느 그룹이든 mode==1 이면                                             :389
      → GET /ai/pumpCommandStatus 재확인                                   :390
      → isRunning==false && data.length>0 일 때만                          :391
          → GET /ai/pumpCommand?pump_grp=1,2                               :393
          → alert(response.data)  ("펌프 제어 명령 전송 성공")               :395
      → 아니면 OnOffAlready 팝업 ("이전 작업이 실행중입니다.")                 :403, OnOffAlready.vue:7

AiController.pumpCommand                                                 AiController.java:750-766
  → 부안은 pump_grp 에 4 가 있으면 ",5" 를 붙임                              :753-761
  → AiService.pumpCommand(map)                                           :764

AiService.pumpCommand()                                                  AiService.java:1893-1918
  → 요청 그룹이 현재 AI_RECOMMEND 그룹에 전부 포함되는지 검사                  :1899-1901
  → gr|gu|ba|dev: PumpService.pumpCommand / wm: WM / gs: GS                :1910-1916
```

`pump_grp` 는 체크된 그룹 배열이 쿼리스트링에서 `1,2` 로 직렬화되고 서버가 `split(",")` 한다 (`:1894`).

### 5.4 `pumpCommandStatus` 응답

`AiService.pumpCommandStatus()` `:1950-1963` → `PumpService.pumpCommandStatus(AI_RECOMMEND 그룹)` `:95-160`.
반환 필드: `isRunning`, `isChange`, `data`, `testMode`, `ctrTestMode`, `rangeStatus`, `changeListSize`,
그리고 쿨다운 판정 시 `lastCtrTime` / `nowDateTime` / `timeDiff(m)` (`:137-139`).

### 5.5 팝업 자동 닫힘

`startInterval` 은 `changePumpOnOff()` 뒤에 `closetime` 분 후 `checkIsRunning()` 을 호출해 `false` 면 팝업을 닫는다
(`:476-479`, `:497-500`). `closetime` 은 모든 그룹이 `2`(또는 미정의)면 1분, 아니면 5분 (`:480-491`, `:501-512`).

### 5.6 있지만 쓰이지 않는 경로

| 경로 | 근거 | 상태 |
|---|---|---|
| 팝업에서 분석모드로 전환 (`OnOffAlarm.changeMode` → `AiMode.changeTabForPopUp`) | `OnOffAlarm.vue:159-176`, `App.vue:445-447` 주석 | 호출처 없음 |
| 헤더 "테스트 팝업" (`test=true` → `OnOffAlarm.testApi`) | `App.vue:3` 이 `@testPopup` 을 듣지만 emit 하는 컴포넌트 없음 (`fe/src` 전체 grep) | 진입 불가 |
| AI운전 그룹 수동 명령 `GET /ai/pumpCommandAI` | `AiController.java:768-784`, `AiService.java:1920-1945` | 프론트 호출처 없음 |
| 상태조회 `GET /ai/pumpCommandAiControlStatus` | `AiController.java:797-800` | 프론트 호출처 없음 |

---

## 6. 모드 전환과 강제 강등

### 6.1 사용자 전환 — `POST /ai/updateAiStatus`

```
AiMode.vue changeTab(index)                                              AiMode.vue:48-85
  → 확인 다이얼로그 → POST /ai/updateAiStatus {PUMP_GRP, STATUS}            :59-62
  → 성공 시 location.reload()                                            :71

AiController.updateAiStatus → AiService.updateAiStatus(map)              AiController.java:698-700
AiService.updateAiStatus()                                               AiService.java:1416-1509
  STATUS=0 :1423-1446 | STATUS=1 :1448-1477 | 그외(2) :1478-1508
  → 세 분기 모두:
      pumpService.initCtrTag()          ← FLAG 0·1 → 3 전량 폐기           :1424 / :1456 / :1483
      TB_HMI_CTR_LOG 에 TAG='AiMode' 기록                                  :1425-1430 / :1457-1462 / :1484-1489
        VALUE = 'AI Control Start' | 'AI Recommend Start' | 'AI Mode End'
      aiMapper.updateAiStatus(map)
  → 사이트별 묶음:
      gs: 그룹 1·2 를 항상 함께 갱신                                       :1431-1435 등
      ba: 그룹 4·5 요청은 4 로 통일                                        :1436-1442 등
      그외(gu 포함): 요청 그룹 하나만                                       :1443-1445 등
```

**보내다 만 명령은 버려진다.** 3Hz 램프 중간 스텝이 대기열에 남아 있어도 모드를 바꾸면 사라진다.

### 6.2 시스템에 의한 `2`(분석) 강등

| 트리거 | 위치 | 조건 | 동작 여부 |
|---|---|---|---|
| SCADA 비상정지 버튼 (`FUNC_TYP` 에 `Btn`) | `kafka/consumer/KafkaConsumerService.java:450-467` | `value==1` | 동작 — `updateEmergencyStatus`(`common_mssql.xml:241-249`, `TAG_GRP='EMS'/TAG_DSC='emerStatus'` 행) + `STATUS=2` |
| SCADA 비상정지 해제 (`Off`) | `:468-476` | `value==1` | `updateEmergencyStatus(0)` 만. `map` 은 만들고 `updateAiStatus` 는 **부르지 않음** |
| 운문 동기화 실패 | `:548-566` | `value==1` | 동작 — 그룹 1 을 `2` 로 |
| 운문 제어모드 해제 | `:573-586` | `value==0` | 동작 — 그룹 1 을 `2` 로 |
| 로그인 시 | `LoginController.java:119-131` → `:244-290` | `ss` 제외 전 사이트 | **동작 안 함** — 실제 POST 가 주석 (`:284-288`) |

로그인 강등은 원격 서버(`:10013/updateAiStatus`, 군산은 `.152/.153/.154` `:257-260`)로 보내는 구조였으나 송신부가 주석이라
`updateAiStatus(2, "2", "1")` 호출은 요청 객체만 만들고 끝난다. 주석 처리 경위는 **미확정**.

### 6.3 이력 화면의 모드 라벨

`AiService.selectPumpCtrHistoryList()` `:2026-2074` 는 명령 시각을 분 단위로 자르고 그룹과 합쳐 `selectAiModeList` 결과와 맞춘 뒤
`AI_MODE` 0/1/그외 를 "AI운전 / AI추천 / AI분석" 으로 붙인다. 같은 분에 모드 기록이 없으면 "AI정보없음" 이다 (`:2051`).

---

## 7. 관찰 기록 (본 문서에서 수정하지 않음)

현장 운영 중인 경로이므로 아래는 **사실 기록**일 뿐이며, 손대기 전 별도 합의가 필요하다.

| # | 내용 | 근거 |
|---|---|---|
| 1 | 자동운전 경로에는 시간 쿨다운이 없다. `pumpCommandStatusMin` 을 쓰고, 쿨다운 있는 `pumpCommandStatus` 호출은 주석 | `PumpScheduler.java:143-144` |
| 2 | 승인 alert("전송되었습니다")가 실제 API 호출보다 먼저 뜬다. 이후 `isRunning` 이면 "이전 작업 실행중" 팝업이 따로 뜬다 | `App.vue:388` vs `:393`, `:403` |
| 3 | `prevDatas` 는 저장만 하고 비교하지 않는다. 차이가 유지되면 10분마다 같은 팝업·알람음이 반복된다 | `App.vue:45`, `:310` |
| 4 | (워킹트리) `AiService` 수정분이 `nowDataValid` 를 새로 내려주지만 프론트 비교는 이를 보지 않는다. 계측 결측 시 `nowFreq=0.0` 기본값과 비교돼 팝업이 뜰 수 있다 | `AiService.java` diff (`nowDataValid`), `App.vue:289-291` |
| 5 | 프론트 감시는 그룹 1·2 만이다. 그룹 3~5 조회가 주석이라 해당 그룹이 `1` 이어도 팝업이 뜨지 않는다 | `App.vue:275-279` |
| 6 | 비상정지 해제(`Off`) 분기는 `map` 을 만들고 `updateAiStatus` 를 부르지 않는다. 해제 후 모드는 `2` 에 머문다 (의도인지 누락인지 불명) | `KafkaConsumerService.java:468-476` |
| 7 | 로그인 시 분석모드 강등 코드는 송신부가 주석이라 동작하지 않는다 | `LoginController.java:284-288` |
| 8 | 모드 판정(`selectAiStatus`)과 대상 선별(`selectAiPumpGrpList`)의 WHERE 가 다르다 — 후자만 `DISPLAY_ID='EMSPumpControl'` | `pump_mssql.xml:901-910` vs `:747-753` |
| 9 | 기존 문서 `gunsan-pump-control-kafka.md:169` 의 `TB_CTR_AI_INF` 는 오기. 실제는 `TB_WPP_TAG_CODE` | `ai_mssql.xml:2734-2743` |

---

## 8. 현장 DB 확인용 SQL

```sql
-- 그룹별 현재 모드 (0 운전 / 1 추천 / 2 분석). DISPLAY_ID 도 같이 본다 (7장 #8)
SELECT TAG_GRP AS PUMP_GRP, DISPLAY_ID, DEFAULT_VALUE AS AI_STATUS
FROM   TB_WPP_TAG_CODE
WHERE  FUNC_TYP = 'PumpStatus'
ORDER  BY TAG_GRP;

-- 모드 전환 이력 (6.1 의 AiMode 로그)
SELECT TIME, VALUE, ANLY_CD, FLAG
FROM   TB_HMI_CTR_LOG
WHERE  TAG = 'AiMode'
ORDER  BY TIME DESC LIMIT 20;

-- 전환으로 폐기된 명령 (FLAG=3)
SELECT TIME, CTR_NM, TAG, VALUE, ANLY_CD, FLAG
FROM   TB_HMI_CTR_TAG
WHERE  FLAG = 3
ORDER  BY TIME DESC LIMIT 30;

-- 비상정지 상태 (common_mssql.xml:241-249 updateEmergencyStatus 가 갱신하는 행)
SELECT TAG_GRP, TAG_DSC, DEFAULT_VALUE
FROM   TB_WPP_TAG_CODE
WHERE  TAG_GRP = 'EMS' AND TAG_DSC = 'emerStatus';
```
