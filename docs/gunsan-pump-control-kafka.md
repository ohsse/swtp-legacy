# 군산 펌프제어 — 어떤 태그를 언제 Kafka 로 보내는가

> **목적**: "군산이 펌프제어 명령을 **어떤 태그로**, **어떤 조건일 때** Kafka 로 내보내는가" 에 답한다.
> **성격**: 사실 확인 문서다. 모든 단언에 `파일:라인` 근거를 붙였고, 확인하지 못한 것은 "미확정"으로 남겼다.
> 코드 변경은 포함하지 않는다. 8장의 관찰 기록도 본 문서에서 수정하지 않는다.
> **조사 기준**: `master` / `021dc43` 시점 소스 직접 확인.
> **관련 문서**: `docs/gunsan-valve-control-plan.md` (명령 생명주기 3단계·밸브),
> `docs/tag-ingestion-pipeline.md` (반대 방향 — SCADA → EMS 수신),
> `inpEditor/BE/editor/doc/reference/legacy-ems-pump-control-summary.md` (주기·유지시간·이력 테이블 일반론).

---

## 1. 결론 요약

1. **토픽은 `ems_result` 하나뿐이다.** 하드코딩이며 설정 프로퍼티가 없다. 전 리포지토리의 발행 지점 3개 파일
   40건이 전부 이 문자열을 쓴다 (`grep -rn "new ProducerRecord" be/src/main/java`).
2. **payload 는 `{"tag","value","time"}` 3필드뿐이다** (`PumpService.java:3262-3270`).
   사이트·명령ID·시퀀스가 없어 **명령 식별이 태그명 하나에 전적으로 의존**한다.
3. **제어 태그 문자열은 소스에 없다.** `TB_CTR_PRF_PUMPMST_INF` 의 컬럼 4종이 SSOT 이고,
   코드는 `ANLY_CD` 로 "어느 컬럼을 쓸지"만 고른다. → **소스만 읽어서는 실제 태그명을 알 수 없다**(7장 SQL).
4. **군산 전용 제어 메서드는 없다.** 고산(`pumpCommandGS`)·운문(`pumpCommandWM`)만 전용 분기이고
   군산은 부안·고령과 함께 공용 `pumpCommand()` 를 탄다 (`PumpScheduler.java:165-172`).
5. **발행을 실제로 막는 스위치는 프로파일이 아니라 DB 두 줄**이다 — `TB_WPP_TAG_CODE` 의
   `TestMode` 와 `CtrTestMode`(4.1절). 후자가 `0` 이면 조합 계산과 대기열 적재는 그대로 돌고
   **Kafka 송신만 멈춘다.** 로그만 보면 정상 동작처럼 보인다.

---

## 2. 전송 경로 3단

명령 생명주기(생성 → 발행 → 확인)의 일반 구조와 `TB_HMI_CTR_TAG` 컬럼 정의는
`docs/gunsan-valve-control-plan.md:28-50` 에 이미 정리돼 있다. 여기서는 **펌프에서 달라지는 점**만 적는다.

```
[생성] PumpScheduler.pumpAiControlTask()   cron "20 */5 * * * *"  (5분)   PumpScheduler.java:114-116
         → 대상 사이트 gs|gu|ba|wm|gr + checkTestMode()                    :125
         → aiControlStatus()                                              :126
         → 군산은 else 분기 → PumpService.pumpCommand(pumpGrpStr)          :170-172
             → insertPumpControlData(optIdx, 펌프명, 태그, ANLY_CD, value) PumpService.java:2575
             → INSERT TB_HMI_CTR_TAG (FLAG=0)                             pump_mssql.xml:271-276

[발행] PumpScheduler.pumpTask()            cron "0 * * * * *"    (1분)    PumpScheduler.java:59-61
         → selectCtrTagList(FLAG=0) → pumpCommandTask(ctrReadyList)        :74, :81 / :92, :104
             → ANLY_CD 디스패치                                            PumpService.java:316-358
             → producer.send(new ProducerRecord<>("ems_result", …))

[확인] PumpScheduler.pumpStatusTask()      cron "0,30 * * * * *" (30초)   PumpScheduler.java:183-184
         → 군산은 else 분기 → pumpStatusTask()  (밸브+펌프 동시 확인)       :213-215
             → FLAG 1 → 2, TB_HMI_CTR_LOG 적재                            PumpService.java:379-447
```

### 2.1 한 사이클에 **1건만** 나간다

```java
// PumpService.java:314-318
if (!ctrList.isEmpty()) {
    HashMap<String, Object> nowCtrItem = ctrList.get(0);   // ← 리스트 첫 건만
    String ANLY_CD = nowCtrItem.get("ANLY_CD").toString();
```

`pumpCommandTask` 는 넘겨받은 대기 목록 전체를 순회하지 않고 **첫 건만 처리한다.**
따라서 명령 N 건이 쌓이면 발행에 최소 N 분이 걸린다. 4.3절의 주파수 램프가 이 제약과 맞물린다.

또한 `pumpTask` 는 **진행중(`FLAG=1`) 명령이 하나라도 있으면 아무것도 보내지 않는다**
(`PumpScheduler.java:79`, `:97`) — 직렬 처리다.

### 2.2 주기 — 군산 30초 설정은 주석 상태다

```java
// PumpScheduler.java:59-60
//@Scheduled(cron = "0,30 * * * * *") //군산, 부안 30초 주기
@Scheduled(cron = "0 * * * * *") //그외 정수장 1분
```

주석이 "군산 30초"라고 적혀 있으나 **현재 활성 라인은 1분**이다. 주기를 바꾸려면 소스 수정 + 주석 토글이다.

### 2.3 군산은 밸브 상태확인에 묶여 있다

`pumpStatusTask` 는 사이트에 따라 갈리는데(`PumpScheduler.java:208-215`), 군산은 `gr/ba/wm` 목록에
없으므로 **밸브까지 확인하는** `pumpStatusTask()` 를 탄다.

```java
// PumpService.java:389-393
List<...> valveStatusList = selectValveStatusCheck(ctrItem);   // TB_CTR_PUMP_REQ_OPT 조인
List<...> pumpStatusList  = selectPumpStatusCheck(ctrItem);    // PMB_TAG
if (valveStatusList.size() == 1 && pumpStatusList.size() == 1) { ... }
```

→ **군산 `TB_CTR_PUMP_REQ_OPT` 에 행이 없으면 `RUN_STATUS`/`STOP_STATUS` 가 영원히 `FLAG=2` 로 넘어가지
않는다.** 2.1 의 직렬 제약과 겹치면 이후 모든 명령이 막힌다. 확인 SQL 은 7장.
(같은 지적이 `docs/gunsan-valve-control-plan.md:127-149` 에도 있다.)

---

## 3. 어떤 태그를 보내는가

### 3.1 태그의 출처는 DB 컬럼이다

| `ANLY_CD` | value | 태그 출처 컬럼 (`TB_CTR_PRF_PUMPMST_INF`) | 생성 라인 (`PumpService.java`) | 전송 메서드 |
|---|---|---|---|---|
| `RUN` | `1` | `CTR_AUTO_TAG` | `:1591`, `:1726` | `sendCtrTagItem` `:1056` |
| `STOP` | `1` | `CTR_AUTO_STOP_TAG` | `:1620`, `:1656` | `sendCtrTagItem` `:1056` |
| `FREQ` | Hz(int) | `CTR_AUTO_FREQ_TAG` | `:1570`, `:1705` | `sendCtrFreqTagItem` `:823` |
| `CTR` | `1`/`0` | `CTR_MANUAL_TAG` | `:1586`, `:1632` | `sendCtrModeTagItem` `:957` |
| `WAIT` | `180` | (전송 안 함 — 대기 상태 표시용) | `:1592`, `:1621` | — |
| `RUN_STATUS` / `STOP_STATUS` | `0` | (전송 안 함 — 결과 확인 대기) | `:1593`, `:1622` | — |
| `TPP` | 실수 | `CTR_AUTO_FREQ_TAG` | `:1566`, `:1701` | **고령 전용** — `wpp_code.equals("gr")` 가드 |
| `SYNC` / `SYNC_STATUS` | `1`/`0` | `CTR_SYNC_TAG` | `:2229`, `:2232` | **운문 전용** |
| `VVK` | `1` | 자바 소스 하드코딩 | `:1599`, `:1615`, `:1651`, `:1734` | **부안 전용, 전부 주석 처리** |

**군산에서 실제로 Kafka 로 나가는 것은 `RUN` / `STOP` / `FREQ` 세 종류다.**
`CTR`(원격모드 전환)은 생성 지점이 `wpp_code.equals("ba") && pumpIdx.equals("10")` 로 부안 한정이라
군산에서는 만들어지지 않는다(`PumpService.java:1579`, `:1625`, `:1661`, `:1714`).

`WAIT`·`*_STATUS` 는 대기열에 행으로는 남지만 `pumpCommandTask` 의 디스패치 분기
(`PumpService.java:316-358`)에 해당 `ANLY_CD` 가 없어 **발행되지 않는다.** 상태 추적용이다.

### 3.2 `ANLY_CD` 는 enum 이 아니다

정의처가 없는 **문자열 리터럴**이며, 생산지(`insertPumpControlData` 호출부)와 소비지 두 곳에 흩어져 있다.

- 소비지 ①: `PumpService.pumpCommandTask()` 의 `if/else if` 체인 `:316-358`
- 소비지 ②: `pump_mssql.xml:45-65` 의 MyBatis `<if>` 화이트리스트 (`selectCtrTagList`)

새 `ANLY_CD` 를 추가하면 **두 곳을 모두** 고쳐야 한다. 한쪽만 고치면 조용히 무시된다.

### 3.3 혼동 주의 — `docs/sql/gunsan_ems_tag_seed.sql` 의 태그는 제어용이 아니다

시드 SQL 의 `891-365-PRI-*`(압력) / `891-365-FRI-*`(유량) 은 **EPANET 분기점 표시·해석 입력용**이며
`TB_EPA_TAG_INFO` / `TB_NODE_TAG` / `TB_LINK_GRP` 에 들어간다. 제어 태그는 여기에 한 건도 없다.

**군산 제어 태그 행을 넣는 seed SQL 은 리포지토리에 존재하지 않는다.**
운영 DB(`<internal-host>/EMS_DB`, `application-gu.properties:9`)에만 있다.

### 3.4 payload 스키마

```java
// PumpService.java:3262-3270
sb.append("{");
sb.append("\"tag\":").append("\"").append(item.get("TAG").toString()).append("\"").append(",");
sb.append("\"value\":").append(item.get("VALUE").toString()).append(",");   // ← 따옴표 없음
sb.append("\"time\":").append("\"").append(item.get("TIME").toString()).append("\"");
sb.append("}");
```

→ `{"tag":"891-365-XXX-9999","value":1,"time":"2026-09-21 14:01:00"}`

`time` 은 현재시각이 아니라 **현재시각 − 2분**이다.

```java
// PumpService.java:3235-3241
ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId).minusMinutes(TIME_DIFF_MIN);
```
`TIME_DIFF_MIN` 은 `time.diff.min` 프로퍼티이며 `application.properties:42` 에 `2` 로 전 사이트 공통이다
(`application-gu.properties` 에 오버라이드 없음).

---

## 4. 언제 보내는가

### 4.1 게이트 — 전부 통과해야 발행된다

| # | 게이트 | 근거 | 비고 |
|---|---|---|---|
| 1 | 프로파일 `gu` | `deploy/gunsan/docker-compose.prod.yml:35` | `dev` 는 `PumpScheduler` 빈 자체가 안 뜬다 (`PumpScheduler.java:38`) |
| 2 | `@EnableScheduling` 활성 | `SchedulerConfig.java:18` `@Profile("!gu2")` | 섀도우(`gu2`) 차단이 **이 한 곳에만** 의존 |
| 3 | 사이트 화이트리스트 | `PumpScheduler.java:64-65`, `:125`, `:186-187` | `gu` 포함 |
| 4 | `checkTestMode()` | `PumpService.java:3777-3785`, `pump_mssql.xml:912-919` | `TB_WPP_TAG_CODE.FUNC_TYP='TestMode'` = `'1'` — AI 마스터 스위치 |
| 5 | AI 모드 | `AiService.java:1945-1957`(운전=`0`) / `:1927-1939`(추천=`1`) | `TB_CTR_AI_INF.AI_STATUS` |
| 6 | 진행중 명령 없음 | `PumpScheduler.java:79`, `:97`, `:137-140` | `FLAG` 0·1 이 **모두** 비어야 생성·발행 |
| 7 | `checkCtrTestMode()` | `PumpService.java:3792-3800`, `pump_mssql.xml:921-928` | `FUNC_TYP='CtrTestMode'` = `'1'` — **송신 전용 스위치** |
| 8 | 변경 건수 < 20 | `PumpService.java:2864-2866`, `:3006-3015` | 초과 시 `result.clear()` 로 **전량 폐기** |

게이트 4·7 이 별개인 점이 중요하다. 7이 `0` 이면 1~6 은 전부 통과해 대기열(`TB_HMI_CTR_TAG`)에 명령이
쌓이지만 `pumpCommandTask` 호출 자체가 일어나지 않아 **Kafka 로는 한 건도 나가지 않는다.**

게이트 8 은 안전장치다 — 한 번에 20건 이상이 바뀌어야 한다고 계산되면 이상 상황으로 보고 통째로 버린다.

> **⚠ 자동운전에는 시간 쿨다운이 없다.**
> `checkTimeDifference()` 는 군산만 5분으로 짧게 잡혀 있으나(`PumpService.java:3439-3444`),
> 호출처는 `pumpCommandStatus()` `:140` **한 곳뿐**이다. 5분 스케줄러가 쓰는 것은
> `pumpCommandStatusMin()`(`:167-217`)이고 **여기에는 그 호출이 없다**
> (`PumpScheduler.java:143`, 144행의 `pumpCommandStatus` 는 주석 처리).
> → 군산 자동제어를 막는 것은 **오직 게이트 6**(진행중 명령 없음)이다.
> `pumpCommandStatus()` 는 `AiService.java:1888` 을 통해 **UI 상태조회/승인 팝업**이 부르므로,
> 5분 쿨다운은 수동 승인 경로에만 걸린다(5장).

### 4.2 무엇을 켜고 끌지 — 군산은 배수지 수위로 조합을 보정한다

명령 생성(`pumpCommand()`)은 스스로 판단하지 않는다. 30초 주기 `DrvnConfig` 가 미리 계산해
`TB_CTR_PUMPYN_RST` / `TB_CTR_PUMPYN_INQUIRY` 에 넣어둔 **목표 조합**과, `PMB_TAG` 실측으로 읽은
**현재 조합**을 `changePumpList()` 가 비교해 차이만 명령으로 만든다
(`PumpService.java:2620-2673`, 조회 SQL `pump_mssql.xml:340-399`).

목표 조합의 베이스는 예측 유량·압력에 대한 유클리드 최근접 조합이다(`DrvnConfig.java:625-662`).
**군산은 그 위에 배수지 수위 보정을 얹는다** (`DrvnConfig.java:748-973`). 감시 태그 2개:

```java
// DrvnConfig.java:775-778
waterLevelParam.put("tagname", "891-365-LEI-8652");
Double oshikdoBaesuji = drvnMapper.selectRawData(waterLevelParam);   // 오식도 배수지
waterLevelParam.put("tagname", "891-365-LEI-8600");
Double naunbaeSuji = drvnMapper.selectRawData(waterLevelParam);      // 나운 배수지
```

시간대 구분은 `DrvnConfig.java:751-768`. 일요일·공휴일은 경부하(`L`), 토요일은 최대부하(`H`)를
중간부하(`M`)로 낮춘다.

| 구간 | 라인 | 오식도 min / max | 나운 min / max |
|---|---|---|---|
| 평일 07~10시 | `:780-801` | 3.8 / 4.1 | 4.05 / 4.0 |
| 평일 12시대 | `:802-807` | 둘 중 하나라도 `< 4.1` 이면 up | 〃 |
| 최대부하 `H` | `:808-828` | 3.8 / 3.9 | 3.7 / 4.0 |
| 그 외 시간대 | `:829-850` | 3.8 / 4.1 | 3.8 / 4.0 |

`min` 미만이면 `plusCondition`(한 단계 up), `max` 이상이면 `minusCondition`(한 단계 down)이다.
이후 판정 순서:

1. **`+` 가 `-` 보다 우선** — 둘 다 걸리면 up (`:852-858`)
2. **나운 > 4.15 면 무조건 down** — 위 결과를 덮어쓴다 (`:859-864`)
3. **수위 조건이 하나도 안 걸렸을 때만** 정수지 `891-365-LEI-4000` / `-4001` 2차 판정 —
   `< 2.7 && >= 0.4` 면 down, `> 3.6` 이면 up (`:867-893`)
4. **직전 10건 이력이 전부 같은 방향이면 2단 증감** (`:895-973`).
   단 평일 12시대(`weekdayLunch`)와 나운 고수위(`naunHighLevel`)는 제외

전력 요금제 기반 보정(`getLoadCheck`)은 **위 수위 조건이 하나도 안 걸렸을 때만** 동작한다
(`DrvnConfig.java:3754` 의 `&& !gu_bool`). 목표치는 `application-gu.properties:70-79` 의
`dstrb.prdct.pumpComb.target.max.up`(3.9) / `.max.down`(4.15) 이다.

### 4.3 주파수는 3Hz 씩 쪼개서 나간다 — 군산 전용

```java
// PumpService.java:2748-2810
if (wpp_code.equals("gu")) {
    int useFreq = Integer.parseInt(usePumpFreq); // 실주파수
    int nowFreq = Integer.parseInt(nowPumpFreq); // 예측 주파수
    int freqDiff = Math.abs(useFreq - nowFreq);
    if (freqDiff >= 3) {
        if (nowFreq > useFreq) {                       // 늘릴 때
            while (useFreq + 3 <= nowFreq) { useFreq += 3; scadaResult.add(tempPrdctItem); }
        } else {                                       // 줄일 때
            while (useFreq - 3 >= nowFreq) { useFreq -= 3; scadaResult.add(tempPrdctItem); }
        }
        // 마지막에 목표 주파수 1건 추가
    } else { scadaResult.add(tempPrdctItem); }         // 3Hz 미만 차이는 1회
}
```

중간 스텝이 전부 별도 명령으로 만들어지므로, **2.1 의 "한 사이클 1건" 제약과 맞물려 1분에 3Hz 씩
올라가거나 내려간다.** 12Hz 차이면 발행 완료까지 4~5분이 걸린다.

발행 하한이 따로 있다 — `value >= 25.0` 미만이면 디스패치 자체가 안 된다.

```java
// PumpService.java:346
} else if (ANLY_CD.equals("FREQ") && FLAG.equals("0") && value >= 25.0) {
```

이 조건을 못 넘긴 `FREQ` 행은 `FLAG=0` 으로 대기열에 남고, 게이트 6 때문에 **다음 명령까지 막는다.**
실제로 풀리는 것은 `initCtrTag()`(`pump_mssql.xml:101-107`)가 `FLAG=3` 으로 폐기할 때다 —
`pumpCommand()` 진입 시 매번 호출된다(`PumpService.java:1418`).

### 4.4 명령은 펄스다

```java
// PumpService.java:1062-1077  (sendCtrTagItem, RUN/STOP 공용)
producer.send(new ProducerRecord<>("ems_result", makeProducerJsonValue(sendItem)));  // value=1
...
Thread.sleep(INIT_TIME);            // 5초  (:49  INIT_TIME = 5000)
sendItem.put("VALUE", 0);
producer.send(new ProducerRecord<>("ems_result", makeProducerJsonValue(sendItem)));  // value=0
```

**군산은 재전송 분기에 해당하지 않는다.** 2회 재전송은 부안(`:1085` `wpp_code.equals("ba")`),
3회는 고산(`:1114` `wpp_code.equals("gs")`) 한정이다. 군산은 `1 → 5초 → 0` 펄스 **1회**로 끝난다.

이어서 대기 처리가 붙는다. 군산은 `else` 분기라 **10초**(`RESEND_TIME`, `:51`)만 쉬고
`WAIT` 를 `FLAG=2` 로 닫은 뒤 `RUN_STATUS`/`STOP_STATUS` 를 `FLAG=1` 로 올려 확인 단계로 넘긴다
(`PumpService.java:1201-1224`). 고산만 6분/3분 대기가 따로 있다(`:1177-1200`).

---

## 5. 수동(웹) 제어 경로

### 5.1 군산이 실제로 쓰는 것은 "조합 변경 승인" 팝업이다

```
fe  App.vue errChecker()
  → GET /ai/pumpCommandStatus            AiController.java:791
      → AiService.pumpCommandStatus()    AiService.java:1888-1900   ← AI_RECOMMEND 그룹만 대상
          → PumpService.pumpCommandStatus()  :95        ← checkTimeDifference(5분) 은 여기 :140
  → (사용자 승인)
  → GET /ai/pumpCommand?pump_grp=N       AiController.java:750-766
      → AiService.pumpCommand()          AiService.java:1831-1856
          → 군산은 :1848 분기 → PumpService.pumpCommand(pumpGrpList)
```

**명령 생성 코드는 자동과 완전히 동일하다.** 수동이라고 다른 태그나 다른 값이 나가지 않는다.
차이는 트리거가 스케줄러냐 사용자 클릭이냐뿐이다.

두 API 모두 **`AI_RECOMMEND`(AI추천, `AI_STATUS=1`) 그룹만** 대상으로 한다
(`AiService.java:1836`, `:1889`). AI운전 모드용은 `/ai/pumpCommandAI`(`AiController.java:768`)로 분리돼 있다.
`pumpCommand` 는 요청한 그룹이 현재 AI추천 그룹에 전부 포함되는지 검사한 뒤에만 실행한다:

```java
// AiService.java:1838
checkAiModeStr = new HashSet<>(nowPumpGrpList).containsAll(pumpGrpList);
```

### 5.2 수동 증감 API 는 군산에서 사실상 쓰이지 않는다

`GET /dr/pumpManualOperation/{pump_grp}/{oper}`(`DrvnController.java:259-308`)의 30분 유지시간 가드는
군산도 `else` 분기라 적용된다(`:275-277`, 위반 시 HTTP 400).
그러나 **군산 화면에 이 버튼이 없고**, 수동 로그를 조합 계산에 되먹이는 코드도
`wpp_code.equals("ba")` 부안 한정이라(`DrvnConfig.java:2760-2769`) API 를 직접 호출해도 조합에 반영되지 않는다.

### 5.3 모드 전환은 대기열을 비운다

`POST /ai/updateAiStatus` → `AiService.updateAiStatus()` 가 `initCtrTag()` 를 호출해
대기·진행중 명령을 전부 `FLAG=3` 으로 폐기한다(`pump_mssql.xml:101-107`).
즉 **모드를 바꾸면 보내다 만 명령은 버려진다.**

---

## 6. 혼동 주의 — 같은 토픽을 쓰는 비(非)제어 송신

### 6.1 작화 화면 송신도 `ems_result` 로 나간다

`be/src/main/java/kr/co/mindone/ems/kafka/producer/KafkaProducerTasks.java:49`
— `@Profile({…,"gu",…})` + `@Scheduled(cron = "0 * * * * ?")`, **군산에서 활성**이다.
전력 예측 결과·펌프 사용 정보를 **같은 `ems_result` 토픽**으로 보낸다(`:342`, `:349`, `:361`, `:368`).
제어 명령이 아니라 SCADA 작화 표출용 데이터다.

토픽이 같아 브로커 쪽 로그만으로는 제어와 표출을 구분할 수 없다. **구분 기준은 태그명뿐이다.**

### 6.2 브로커가 비대칭이다

```properties
# application-gu.properties:33-35
spring.kafka.bootstrap-servers=<internal-host>:9092      # PumpService(제어)가 쓰는 값
spring.kafka.bootstrap-servers-1=<internal-host>:9092    # KafkaProducerTasks(표출) 1번
spring.kafka.bootstrap-servers-2=<internal-host>:9092    # KafkaProducerTasks(표출) 2번
```

제어 명령은 `kafkaProperties.getBootstrapServers()`(`KafkaProperties.java:28`)를 쓰므로 **`.153` 단일
브로커**로만 나가고, 표출 데이터는 `.153`+`.154` **양쪽**으로 나간다(`KafkaProducerTasks.java:338`, `:357`).
**수신(컨슈머)은 이중화돼 있다**(`docs/tag-ingestion-pipeline.md:139-147`).
이 비대칭이 의도인지 누락인지는 코드·주석 어디에도 근거가 없다 — **미확정**.

### 6.3 동명 클래스 2벌

`be/.../kafka/KafkaProducerTasks.java`(루트, 구버전)와 `be/.../kafka/producer/KafkaProducerTasks.java`
(현행)가 둘 다 있다. 구버전은 `@Profile` 로 군산이 배제돼 동작하지 않지만 탐색 시 혼동된다.
같은 문제가 `KafkaConsumerService` 에도 있다(`docs/tag-ingestion-pipeline.md:528`).

### 6.4 비상정지는 Kafka 로 명령을 되쏘지 않는다

SCADA 가 태그명에 `-EMS-` 가 들어간 메시지를 보내면
`be/.../kafka/consumer/KafkaConsumerService.java:338-347` 이 `TB_WPP_TAG_CODE` 에서 `FUNC_TYP` 을 찾아
`pumpAnlyOptStop` 이면 `emsEmergency()` 를 태운다.

```java
// KafkaConsumerService.java:459-467  (emsEmergency)
if (funcTyp.contains("Btn")) {
    if (statusValue == 1) {
        updateMap.put("statusValue", "1");
        commonService.updateEmergencyStatus(updateMap);
        map.put("STATUS", "2");
        aiService.updateAiStatus(map);        // AI 분석 모드로 강등
    }
}
```

**하는 일은 `AI_STATUS` 를 `2`(분석)로 내려 자동제어를 멈추는 것이고, Kafka 로 정지 명령을 보내지 않는다.**
정지는 SCADA 측에서 물리적으로 수행된다는 전제로 보이나, 그 전제를 명시한 문서는 확인하지 못했다 — **미확정**.

`PumpService.pumpStop()`(`:3831`) / `pumpStart()`(`:3911`)는 Kafka 로 직접 쏘지만
`780-379-PMC-*` 선남(고령) 태그 하드코딩이고, 진입점도 고령 화면
(`fe/src/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/Goryeong/PumpDrvnAnlyForGoryeong.vue`)뿐이라
**군산 경로가 아니다.**

### 6.5 `ems_gu_predict` 는 Kafka 를 쓰지 않는다

수요예측 모듈은 결과를 `TB_CTR_TNK_RST` 에 DB 로만 올린다(`ems_gu_predict/scripts/harness/upload.py`).
예측값이 제어로 변환되는 접점은 `DrvnConfig.setInsertPumpComn()` `:206-213` 이며,
매핑은 `application-gu.properties:149-154` 의 `dstrb.prdct.pumpDstrbId`
(`Q_GunS_PREDICT` / `P_GunS_PREDICT`)다.

---

## 7. 현장 DB 확인용 SQL

소스에 태그가 없으므로 실제 값은 운영 DB 에서 확인해야 한다.

```sql
-- 군산 펌프별 실제 제어 태그 (3장 표의 컬럼들)
SELECT PUMP_IDX, PUMP_GRP, PUMP_NM, PUMP_TYP, USE_YN,
       CTR_AUTO_TAG, CTR_AUTO_STOP_TAG, CTR_AUTO_FREQ_TAG, CTR_MANUAL_TAG,
       PMB_TAG, SPI_TAG
FROM   TB_CTR_PRF_PUMPMST_INF
WHERE  WPP_CODE = 'gu'
ORDER  BY PUMP_IDX;

-- 발행 스위치 2종 — 둘 다 '1' 이어야 실제 송신된다 (4.1절 게이트 4·7)
SELECT FUNC_TYP, DEFAULT_VALUE
FROM   TB_WPP_TAG_CODE
WHERE  FUNC_TYP IN ('TestMode', 'CtrTestMode');

-- 최근 명령 흐름
SELECT TIME, CTR_NM, TAG, VALUE, ANLY_CD, FLAG
FROM   TB_HMI_CTR_TAG
ORDER  BY TIME DESC LIMIT 30;

-- ANLY_CD 별로 어느 FLAG 에서 멈춰 있는지 (1에 고여 있으면 2.3절 확인)
SELECT ANLY_CD, FLAG, COUNT(*)
FROM   TB_HMI_CTR_TAG
WHERE  TIME >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP  BY ANLY_CD, FLAG;

-- 상태확인이 막혀 FLAG=2 로 못 넘어가는지 (2.3절 — 비어 있으면 영원히 대기)
SELECT * FROM TB_CTR_PUMP_REQ_OPT WHERE WPP_CODE = 'gu';
```

---

## 8. 관찰 기록 (본 문서에서 수정하지 않음)

현장 운영 중인 경로이므로 아래는 **사실 기록**일 뿐이며, 손대기 전 별도 합의가 필요하다.

| # | 내용 | 근거 |
|---|---|---|
| 1 | `naunbaeSuji > 4.15` 에 **null 검사가 없다.** 바로 위 블록들(`:795`, `:822`, `:843`)은 `!= null` 로 감싸는데 이 줄만 빠져 있어, 나운 수위 태그가 결측이면 `Double` 언박싱 NPE 로 해당 tick 의 조합 계산이 통째로 죽는다. `weekdayLunch` 분기(`:805`)도 동일 | `DrvnConfig.java:860`, `:805` |
| 2 | 평일 07~10시 나운 임계값이 `MIN(4.05) > MAX(4.0)` 으로 역전돼 있다. `if/else if` 라 `[4.0, 4.05)` 구간이 `plusCondition` 으로 먼저 흡수되고 `minus` 는 4.05 이상에서만 발동한다. 주석("오식도 배수지 수위 4.05m 미만…")도 실제 상수(3.8)와 불일치 | `DrvnConfig.java:784-786` |
| 3 | payload JSON 을 라이브러리 없이 `StringBuffer` 로 조립하며 `value` 에 따옴표를 붙이지 않는다. 숫자가 아닌 값이 들어오면 깨진 JSON 이 발행된다 | `PumpService.java:3262-3270` |
| 4 | 제어 명령만 단일 브로커(`.153`)로 나가고 표출 송신·수신은 이중화. 의도/누락 불명 (6.2) | `application-gu.properties:33-35` vs `KafkaProducerTasks.java:338`, `:357` |
| 5 | 섀도우(`gu2`) 발행 차단이 `SchedulerConfig` 한 곳에만 의존한다. `PumpService` 의 send 메서드들은 `@Profile` 가드가 없어 HTTP 경로(5장)로 불리면 프로파일과 무관하게 발행된다 | `SchedulerConfig.java:18`, `EmsApplication.java:8-9` |
| 6 | `FREQ` 가 25 미만이면 디스패치에서 탈락해 `FLAG=0` 으로 남고, 게이트 6 때문에 이후 명령을 막는다. 타임아웃·폐기 로직이 없어 `initCtrTag()` 가 도는 다음 `pumpCommand()` 까지 대기 (4.3) | `PumpService.java:346`, `:1418` |
| 7 | 매 사이클 1건 발행(2.1) + 3Hz 램프(4.3) + 진행중 명령 직렬 대기(게이트 6)가 겹쳐, 주파수 변화가 클수록 반영이 분 단위로 지연된다 | `PumpService.java:315`, `:2766-2804` |
