# TAG 데이터 수집 파이프라인 — `TB_RAWDATA` 적재 구조

> **성격**: 사실 확인 문서다. 모든 단언에 `파일:라인` 근거를 붙였고, 확인하지 못한 것은
> "미확정"으로 남겼다. 코드 변경은 포함하지 않는다.
> **조사 기준**: `master` / `c0703e5` 시점 소스 직접 확인.
> **관련 문서**: `docs/sql/gunsan_ems_tag_seed.sql` (태그 명명 규칙·군산 태그 매핑),
> `docs/tenant-bundle-guide.md` (현장별 반출·프로파일), `docs/gunsan-epa-mode-analysis.md` (소비 측 EPAMODE).

---

## 1. 결론 요약

SCADA 태그 데이터를 `TB_RAWDATA` 계열에 넣는 주체는 **EMS API(`be/`)의 Kafka 컨슈머 단 하나**다.
전용 Collector 모듈은 없고, MQTT·OPC-UA·Modbus·REST 폴링·FTP·파일 감시·DB 링크 경로도 전무하다
(전역 검색 무결과).

기억해야 할 세 가지:

1. **`TB_RAWDATA` 는 매분 해상도다** — 초 값이 `00` 인 메시지는 분과 무관하게 전부 들어간다(§4.2).
   나머지 초 단위 메시지는 컨슈머에서 조용히 버려지므로, 이름과 달리 원시 데이터가 아니다.
2. **롤업 3종은 배치 산출물이 아니다.** 수신 시점에 같은 메시지를 여러 테이블로 동시 삽입(fan-out)한다.
   따라서 **재계산 경로가 없다** — 메시지가 누락되면 그 시각의 집계 행은 영구히 빈다.
3. **`dev` 프로파일에서는 수집이 아예 돌지 않는다.** 장애가 아니라 프로파일 게이트에 의한 의도된 동작이다.

---

## 2. 테이블

### 2.1 DDL 위치

`TB_RAWDATA` 계열은 EMS 공유 DB 의 테이블이라 이 리포지토리의 마이그레이션 대상이 아니다.
**DDL 전문은 레거시 스키마 덤프 문서에 있다.**

| 테이블 | DDL |
|---|---|
| `TB_RAWDATA` | `inpEditor/BE/editor/doc/legacy/ems/docs/ems_schema.md:1474` |
| `TB_RAWDATA_15MIN` | `ems_schema.md:1603` |
| `TB_RAWDATA_HOUR` | `ems_schema.md:1765` |
| `TB_RAWDATA_HOUR_INGRT` | `ems_schema.md:1896` |

같은 내용이 IDE 스냅샷 `.idea/dataSources/3876a754-f242-4eb8-bf43-07c343747e89.xml`
(`parent="650"` ~ `parent="653"`)에도 있으나, 한글 주석이 인코딩 깨짐 상태이고 IDE 전용 파일이므로
**`ems_schema.md` 를 정본으로 본다.**

### 2.2 적재 대상 4종

```sql
-- ems_schema.md:1474
CREATE TABLE `TB_RAWDATA` (
  `TS`      timestamp   NOT NULL DEFAULT current_timestamp() COMMENT '일시',
  `TAGNAME` varchar(45) NOT NULL                             COMMENT '태그 이름',
  `VALUE`   varchar(45) DEFAULT NULL                         COMMENT '값',
  `QUALITY` varchar(3)  DEFAULT NULL                         COMMENT '품질',
  `SERVER`  varchar(45) DEFAULT NULL                         COMMENT '서버 출처',
  PRIMARY KEY (`TS`,`TAGNAME`),
  KEY `TB_RAWDATA_TAGNAME_IDX` (`TAGNAME`,`TS`) USING BTREE
) ENGINE=InnoDB COMMENT='분단위 SCADA 태그 데이터'
 PARTITION BY RANGE (unix_timestamp(`TS`))
(PARTITION `p202108` VALUES LESS THAN (1630422000) ENGINE = InnoDB,
 -- ... 월 단위로 p202108 ~ p203012
 PARTITION `p_future` VALUES LESS THAN MAXVALUE   ENGINE = InnoDB)
```

**컬럼 5개·PK·월 단위 RANGE 파티션은 네 테이블이 동일하다. 다만 보조 인덱스는 제각각이다.**

| 테이블 | 주석 | 해상도 | PK 외 인덱스 | 보존 |
|---|---|---|---|---|
| `TB_RAWDATA` | 분단위 SCADA 태그 데이터 | 1분 | `(TAGNAME,TS)` | **20주** (§6) |
| `TB_RAWDATA_15MIN` | 15분단위 SCADA 태그 데이터 | 15분 + 정시 | **없음** | 무기한 |
| `TB_RAWDATA_HOUR` | 1시간 단위 SCADA 태그 데이터 | 정시 | `(TAGNAME,TS)`, `(TAGNAME)`, `(TS)` | 무기한 |
| `TB_RAWDATA_HOUR_INGRT` | 1시간 단위 적산 SCADA 태그 데이터 | 정시, **차분값** | **없음** | 무기한 |

PK 가 `(TS, TAGNAME)` 순이므로 **태그 하나의 시계열을 훑는 조회는 PK 를 못 탄다.** `TB_RAWDATA` 와
`TB_RAWDATA_HOUR` 에만 `(TAGNAME, TS)` 보조 인덱스가 있고, `_15MIN` 과 `_HOUR_INGRT` 에는 없다.

> **리포지토리 내 서술 충돌 — 현장 DB 에서 확인 필요.**
> `inpEditor/BE/editor/src/main/resources/db/migration/V13__create_tag_pred_eval_table.sql:53-54` 는
> *"TB_RAWDATA PK 는 (TS, TAGNAME) 이라 태그별 윈도 조회가 비효율적일 수 있다 … 보조 인덱스
> (TAGNAME, TS) 추가를 검토한다"* 라고 적고 있다. 그러나 `ems_schema.md:1481` 의 DDL 에는
> 그 인덱스(`TB_RAWDATA_TAGNAME_IDX`)가 **이미 존재한다.** 스키마 덤프 시점과 마이그레이션 작성 시점의
> 차이일 수 있으나 어느 쪽이 현행인지는 확인하지 못했다(미확정). 성능 판단 전에
> 실제 DB 에서 `SHOW INDEX FROM TB_RAWDATA` 로 확인할 것.

`VALUE` 가 숫자형이 아니라 `varchar(45)` 인 점에 유의한다. 적산 계산 등에서 매번
`Double.parseDouble()` 로 변환하며, 변환 실패는 예외로 이어진다.

### 2.3 적재되지 않는 동명 계열 5종 (주의)

이름이 `TB_RAWDATA_` 로 시작하지만 **이 리포지토리의 어떤 코드도 읽지도 쓰지도 않는** 테이블이 5개 더 있다
(`git grep` 무결과 확인). 스키마 덤프에만 존재한다.

| 테이블 | 주석 | DDL | 구조 차이 |
|---|---|---|---|
| `TB_RAWDATA_DAY` | 1일 단위 합계 | `ems_schema.md:1731` | `VALUE double`, `QUALITY`·`SERVER` 없음, **연 단위** 파티션 |
| `TB_RAWDATA_DAY_INGRT` | 1일 단위 합계 | `:1748` | 〃 |
| `TB_RAWDATA_MONTH` | 1개월 단위 합계 | `:2024` | 〃 |
| `TB_RAWDATA_MONTH_INGRT` | 1개월 단위 합계 | `:2041` | 〃 |
| `TB_RAWDATA_PMB_HOUR` | 펌프 가동상태(PMB) 태그 전용 | `:2058` | `VALUE` 는 `'0'`/`'1'`, 파티션 없음 |

일·월 집계 테이블은 컬럼 구성부터 다르다(`VALUE` 가 `double`, 품질·출처 컬럼 없음).

전역 검색 결과 이 5개 이름은 **스키마 DDL 과 분석 문서에만 등장하며, 쓰기는 물론 `SELECT` 참조조차
0건이다.** `be/` 의 mapper XML 7개 파일 어디에도 나오지 않고(mapper 내 rawdata 참조 224건은 전부
`TB_RAWDATA`/`_15MIN`/`_HOUR`/`_HOUR_INGRT`), `insertRawData` 의 `type` 분기 대상도 그 4개뿐이다.
**이 리포지토리 안에는 채우는 주체도 읽는 주체도 없다.** 외부 배치가 채울 가능성은 리포지토리 밖의
일이라 확인할 수 없다 — **미확정**.

태그 명명 규칙(`891-365-PRI-4000` 형태)과 군산 현장 태그 매핑은 `docs/sql/gunsan_ems_tag_seed.sql:38-56` 참고.

---

## 3. 진입점 — `@KafkaListener` 4개

`be/src/main/java/kr/co/mindone/ems/kafka/consumer/KafkaConsumerService.java`

| 메서드 | 라인 | 클러스터 | 토픽 |
|---|---|---|---|
| `scadaFirstListen` | `:129` | 1 (`kafkaListenerContainerFactory1`) | `${kafka.topic.scada1.name}` |
| `scadaSecondListen` | `:169` | 1 | `${kafka.topic.scada2.name}` |
| `scadaFirstListen2` | `:197` | 2 (`kafkaListenerContainerFactory2`) | `${kafka.topic.scada1.name}` |
| `scadaSecondListen2` | `:237` | 2 | `${kafka.topic.scada2.name}` |

**클러스터 2대 × 토픽 2개 = 리스너 4개**이며 네 개 모두 `autoStartup = "true"` 로 동일한
`insertMsgHashMap()` 으로 수렴한다. 이중화된 SCADA 브로커에서 같은 태그가 중복 수신될 수 있는데,
이는 `INSERT IGNORE`(§5)로 흡수된다.

각 리스너가 하는 일은 동일하다 — Gson 으로 JSON → `HashMap` 파싱 후 **자기 토픽명을 `server` 키에 심는다**:

```java
// :141-146 (scadaFirstListen)
Type type = new TypeToken<HashMap<String, Object>>() {}.getType();
messageMap = gson.fromJson(jsonString, type);
messageMap.put("server", kafka_topic_scada1);   // → SERVER 컬럼. 출처 구분용
insertMsgHashMap(messageMap);
```

메시지 JSON 은 `tagname` / `timestamp` / `value` / `quality` 네 키를 가진다 (`:316-317`, `:598-600`).

### 3.1 사이트별 접속 설정

| 항목 | 군산 `gu` (`application-gu.properties:23-39`) | 고산 `gs` (`application-gs.properties:22-42`) |
|---|---|---|
| 토픽 1 / 2 | `DGUWGS1_data` / `DGUWGS2_data` | `DGSWGS1_data` / `DGSWGS2_data` |
| 브로커 1 | `<internal-host>:9092` | `<internal-host>:9092` |
| 브로커 2 | `<internal-host>:9092` | `<internal-host>:9092` |
| groupId | `DGUWGS{1,2}_ems_api_20240926_{1,2}_S{1,2}` | `DGSWGS{1,2}_ems_api_20241218_{1,2}_S{1,2}` |
| offset reset | `earliest` | `earliest` |

**`auto-offset-reset=earliest` 가 전 사이트 공통이다.** 따라서 groupId 를 바꿔서 기동하면
토픽을 처음부터 전량 재소비한다. groupId 에 날짜(`_20240926_`, `_20241218_`)를 박아 두는 것은
이 재적재를 의도적으로 트리거하기 위한 운용 관행으로 보이나, 정식 절차 문서는 확인하지 못했다(미확정).

---

## 4. 적재 본체 `insertMsgHashMap()` (`:315-425`)

```
Kafka JSON { tagname, timestamp, value, quality }
  │
  ├─ (1) 시각 정규화                                            :318-327
  │      "yyyy-MM-dd HH:mm:ss" 파싱 → Asia/Seoul 로 지정 → 동일 포맷으로 재출력
  │
  ├─ (2) 태그 화이트리스트 대조  → §4.1                          :328-337
  │      TB_WPP_TAG_INF 목록에 없으면 여기서 종료 — 이후 로직 전부 건너뜀
  │
  ├─ (3) 특수 태그 가로채기 (적재와 별개로 부수효과 발생)
  │      · "-EMS-" 포함        → FUNC_TYP 조회 후 pumpAnlyOptStop 긴급제어    :338-347
  │      · wpp_code=="wm"      → 운문 인버터/동기화실패/연동운전 판별          :349-366
  │      · wpp_code=="gs"      → 전력·전력량 합산 → processTagData() (§4.4)   :368-377
  │
  └─ (4) checkMsgTime(msgTs) 판정 후 fan-out 적재                :379-422
```

### 4.1 적재 대상 태그 판별 — `TB_WPP_TAG_INF` 화이트리스트

**어떤 태그를 적재할지는 코드가 아니라 DB 테이블 한 개가 정한다.** 태그 목록이 소스에 박혀 있지 않고,
패턴 매칭도 아니다.

```sql
-- common_mssql.xml:8-18
SELECT TAG FROM TB_WPP_TAG_INF
WHERE USE_YN = '1'
-- <if test="tag_grp != ..."> AND TAG_GRP = #{tag_grp} </if>
--   ↑ 적재 경로에서는 빈 params 를 넘겨 이 <if> 가 타지 않는다
```

```sql
-- ems_schema.md:2293-2298 — 테이블 주석이 'Kafka Consumer 사용 태그 정의'
CREATE TABLE `TB_WPP_TAG_INF` (
  `WPP_CODE` varchar(7)  DEFAULT NULL COMMENT '정수장 코드',
  `TAG_GRP`  varchar(5)  DEFAULT NULL COMMENT '태그 그룹',
  `TAG`      varchar(45) DEFAULT NULL COMMENT '태그',
  `USE_YN`   varchar(1)  DEFAULT '1'  COMMENT '사용 여부'
)   -- PK·인덱스 없음, 전 컬럼 nullable
```

**매칭은 문자열 완전 일치다.** 접두어·와일드카드·정규식이 아니다.

```java
// KafkaConsumerService.java:333-337
boolean tagValueExists = wppTagList.stream()
        .map(map -> map.get("TAG"))
        .anyMatch(msgTag::equals);
if (tagValueExists) { /* 이후 전부 */ }
```

목록에 없으면 **메시지가 통째로 폐기된다.** 적재뿐 아니라 긴급제어(`:338-347`)·사이트 전용 판별
(`:349-377`)까지 전부 건너뛴다.

> **운영 주의 — 목록은 기동 시 한 번만 읽는다.**
> `onApplicationEvent(ApplicationReadyEvent)`(`:266-275`)에서 `wppTagList` 필드로 올리고,
> `:328-331` 의 `null` 체크는 그 적재가 실패했을 때를 위한 방어일 뿐이다.
> `selectWppTagList` 호출부는 이 둘뿐이며(`CommonMapper.java:25`·`CommonService.java:41` 선언 외),
> **갱신 API 도 스케줄러도 없다.**
> → DB 에 태그를 추가하거나 `USE_YN` 을 바꿔도 **EMS API 를 재기동하기 전까지 반영되지 않는다.**
> "태그를 등록했는데 데이터가 안 쌓인다"는 여기부터 확인할 것.

`WPP_CODE` 컬럼이 있으나 **쿼리가 쓰지 않는다.** 사이트 구분 없이 `USE_YN='1'` 전부를 가져온다.
현장별로 DB 인스턴스가 분리돼 있어(고산 `<internal-host>`, 군산 `<internal-host>`) 드러나지 않을 뿐,
한 DB 에 여러 현장을 담으면 즉시 깨진다.

#### 판별은 2단 구조다

| 단계 | 테이블 | 조건 | 용도 |
|---|---|---|---|
| 1 | `TB_WPP_TAG_INF` | `USE_YN='1'` | **적재 여부** — 통과 못하면 끝 |
| 2 | `TB_WPP_TAG_CODE` | `TAG_GRP='EMS'`, `DISPLAY_ID='ConsumerTag'` | `-EMS-` 태그의 제어 기능(`FUNC_TYP`) 판별 |

2단은 적재 대상 판별이 **아니라** 기능 판별이다. 1단을 통과한 태그 중 이름에 `-EMS-` 가 들어가면
`findEMSFunctionType()`(`:432-442`)이 `FUNC_TYP` 을 찾고, `pumpAnlyOptStop` 이면 펌프 긴급정지를 태운다.
쿼리는 `common_mssql.xml:229-239`, 캐싱 방식은 1단과 동일하게 기동 시 1회다(`:274`, `:433-435`).

### 4.2 `checkMsgTime()` — 적재 대상 테이블 판별 (`:486-509`)

1단을 통과한 메시지가 **어느 테이블에 몇 건** 들어가는지는 메시지의 **초·분 값만으로** 결정된다.

> **초가 `00` 이기만 하면 분과 무관하게 전부 `TB_RAWDATA` 에 들어간다.
> 즉 `TB_RAWDATA` 는 태그당 매분 1행이다.**

| 메시지 시각 예 | `TB_RAWDATA` | `_15MIN` | `_HOUR` | `_HOUR_INGRT` | INSERT 횟수 |
|---|:--:|:--:|:--:|:--:|:--:|
| `10:07:23` (초 ≠ 00) | — | — | — | — | 0 |
| `10:07:00` | ● | — | — | — | 1 |
| `10:15:00` | ● | ● | — | — | 2 |
| `11:00:00` | ● | ● | ● | ● (조건부) | 3~4 |

구현은 `checkMsgTime()` 이 반환하는 네 유형으로 갈린다. 상수는 `KafkaConfig.java:57-60`
(`TIME_ALL="all"`, `TIME_HOUR="hour"`, `TIME_MIN="min"`, `TIME_SEC="sec"`).

| 조건 | 반환 | `TB_RAWDATA` | `_15MIN` | `_HOUR` | `_HOUR_INGRT` |
|---|---|:--:|:--:|:--:|:--:|
| `ss != 00` | `sec` | — | — | — | — |
| `ss == 00`, `mm == 00` | `hour` | ● | ● | ● | ● (조건부) |
| `ss == 00`, `mm ∈ {15,30,45}` | `min` | ● | ● | — | — |
| `ss == 00`, 그 외 분 | `all` | ● | — | — | — |

두 표가 어긋나 보이지 않는 이유는 적재 코드가 `if` 세 개의 **누적 구조**이기 때문이다
(`else if` 가 아니다). `hour` 인 메시지도 `:381` 의 `!TIME_SEC` 조건에 먼저 걸려 `TB_RAWDATA` 에
들어가고, 이어서 `:392-396` 에서 `_HOUR` 와 `_15MIN` 에도 들어간다.
**반환값이 `"all"` 이 아니어도 `TB_RAWDATA` 에는 적재된다** — 상수 이름만 보고 판단하면 틀린다.

```java
// :381-396
if (!TIME_SEC.equals(resultTimeType)) { messageMap.put("type", "all");  insertRawData(...); }
if (TIME_MIN.equals(resultTimeType))  { messageMap.put("type", "min");  insertRawData(...); }
if (TIME_HOUR.equals(resultTimeType)) { messageMap.put("type", "hour"); insertRawData(...);
                                        messageMap.put("type", "min");  insertRawData(...); }
```

> **① `TB_RAWDATA` 는 매분 적재된다.**
> `:381` 의 `!TIME_SEC` 가드는 "초 ≠ 00 만 제외"라는 뜻이므로 `hour`·`min`·`all` 세 유형이 모두 통과한다.
> 별도의 "매분 적재 스케줄러" 같은 것은 없다 — 이 `if` 한 개가 그 역할을 한다.
>
> **② 반대로 초 단위 데이터는 저장되지 않는다.**
> `ss != 00` 이면 `TIME_SEC` 이 되어 같은 가드에서 전부 탈락한다. SCADA 가 초 단위로 송신하더라도
> DB 에는 1분 해상도만 남는다. 테이블 주석 "분단위 SCADA 태그 데이터"가 이 동작을 정확히 서술한다.
>
> **③ 단, EMS 가 매분 스냅샷을 "만드는" 것은 아니다.**
> 들어온 메시지를 거르는 **수동 필터**일 뿐이라, SCADA 가 그 시각 그 태그를 보내지 않으면 행이 생기지
> 않는다. EMS 는 결측을 메꾸지 않는다. **따라서 태그당 매분 1행이 보장되지는 않는다.**

③ 의 근거는 소비 측 코드에 남아 있다. EPA 는 정확한 시각의 행을 집는 게 아니라
**`FALLBACK_SEC`(600초, `epa/config.py:40`) 윈도 안에서 가장 최신 행**을 찾는다.

```python
# epa/app/models/epa_models.py:56-65
fallback_sec = current_app.config['FALLBACK_SEC']
SELECT r.TAGNAME, r.VALUE FROM TB_RAWDATA r JOIN (
    SELECT TAGNAME, MAX(ts) AS ts FROM TB_RAWDATA
    WHERE ts <= %s AND ts >= DATE_SUB(%s, INTERVAL %s SECOND) AND TAGNAME IN (...)
    GROUP BY TAGNAME
) x ON x.TAGNAME = r.TAGNAME AND x.ts = r.ts
```

매분 데이터가 확실히 존재한다면 이런 10분 fallback 은 필요 없다.

### 4.3 적산(`_HOUR_INGRT`) 계산 (`:398-420`)

정시 메시지 중 **태그명이 `.*-(PWQ|PWI|VOI|FRQ|SWI|FIQ)-.*` 에 맞는 것만** 대상이다(`:404`).
1시간 전 값을 조회해 차분을 저장하며, **음수는 0으로 클램프**한다 — 계기 롤오버·리셋 방어다.

```java
// :405-418
for (HashMap<String, Object> maps : oneHourBeforeList) {
    if (nowTagName.equals(maps.get("tagname").toString())) {
        double tempSumValue = nowValue - Double.parseDouble(maps.get("value").toString());
        if (tempSumValue < 0) tempSumValue = 0.0;      // 롤오버 방어
        messageMap.put("value", tempSumValue);
        messageMap.put("type", "sum");
        commonService.insertRawData(messageMap);
    }
}
```

조회 쿼리 `oneHourBeforeList` (`common_mssql.xml:216-226`):

```sql
SELECT DATE_FORMAT(ts,'%Y-%m-%d %H:%i:%s') AS ts, tagname, value, quality
FROM TB_RAWDATA_HOUR
WHERE ts >= DATE_SUB(#{date}, INTERVAL 1 HOUR) AND ts <= #{date}
  AND tagname IN (SELECT TAG FROM TB_WPP_TAG_INF
                  WHERE USE_YN='1' AND TAG_GRP IN ('PWQ','FRQ','PWI','VOI','SWI'))
```

이 구간에서 확인된 사실 두 가지:

- **조회 범위가 현재 시각을 포함한다** (`ts <= #{date}`). 그런데 `:394` 에서 현재 정시 행을
  `TB_RAWDATA_HOUR` 에 **먼저 넣은 뒤** 이 쿼리를 호출하므로, 결과에는 **직전 시각 행과 방금 넣은 현재 행이
  둘 다** 들어온다. 결과적으로 루프가 2회 돌며 같은 PK(`ts`, `tagname`)로 두 번 삽입을 시도한다 —
  하나는 정상 차분, 다른 하나는 자기 자신과의 차분이라 `0.0` 이다.
  쿼리에 `ORDER BY` 가 없고 `INSERT IGNORE` 는 **먼저 들어온 값이 이기므로**(§5), 어느 쪽이 저장될지는
  DB 의 행 반환 순서에 달려 있다. 실무상 PK 오름차순 스캔이면 직전 시각 행이 먼저 와서 정상 차분이
  저장되지만, **코드가 이를 보장하지는 않는다.**
- **`TAG_GRP` 필터와 Java 정규식이 불일치한다.** 정규식(`:404`)에는 `FIQ` 가 있으나 SQL 의
  `TAG_GRP IN (...)` 목록에는 없다. `FIQ` 태그는 매칭 행을 못 받아 `_HOUR_INGRT` 행이 생성되지 않는다.

### 4.4 고산 전용 합성 태그 `processTagData()` (`:596-698`)

`insertRawData` 를 호출하는 **두 번째 경로**다. 고산(`gs`)에서만 동작하며, 흩어진 전력 태그를
합산해 실제로 존재하지 않는 가상 태그를 만들어 같은 테이블에 넣는다.

- `POWER_TAGS_TO_SUM`(`701-367-PWI-*`) 이 한 시각에 모두 모이면 → 단위계수 `PWI_UNIT_VALUES` 적용 후
  합산 → **`301-367-PWI-0000`** 으로 적재 (`:612-653`)
- `ENERGY_TAGS_TO_SUM`(`701-367-PWQ-*`) → 정시에만, 직전 1시간 `301-367-PWI-0000` 의 **평균**을
  구해 **`301-367-PWQ-0000`** 을 `type="sum"` 으로 적재 (`:654-695`)

태그 목록과 단위 환산 계수는 클래스 상수로 **하드코딩**되어 있다 (`:94-123`).

이 경로의 fan-out 규칙은 §4.2 와 미묘하게 다르다 — `TIME_HOUR` 일 때 `_HOUR` 에만 넣고 `_15MIN` 에는
넣지 않는다(`:640-651`). 본류(`:392-396`)는 둘 다 넣는다. 의도된 차이인지는 확인하지 못했다(미확정).

---

## 5. SQL — `common_mssql.xml:19-48`

테이블 선택은 애플리케이션이 넘긴 `type` 값으로 MyBatis `<if>` 가 결정한다.

```xml
<insert id="insertRawData" parameterType="hashMap">
  INSERT IGNORE INTO
  <if test='type == "all"'>  TB_RAWDATA            </if>
  <if test='type == "hour"'> TB_RAWDATA_HOUR       </if>
  <if test='type == "min"'>  TB_RAWDATA_15MIN      </if>
  <if test='type == "sum"'>  TB_RAWDATA_HOUR_INGRT </if>
  ( ts, tagname, value, quality, server )
  VALUES ( #{timestamp}, #{tagname}, #{value}, #{quality}, #{server} )
</insert>
```

두 가지가 중요하다.

- **`INSERT IGNORE` = 선착순 승리.** `ON DUPLICATE KEY UPDATE` 가 아니다. PK `(TS, TAGNAME)` 가
  충돌하면 새 값은 조용히 버려진다. 이중 클러스터 중복 수신을 흡수해 주는 장치이자,
  **나중에 도착한 정정값이 반영되지 않는 원인**이기도 하다.
- **배치가 없다.** `<foreach>` 없는 단건 `VALUES` 이므로 메시지 1건 = SQL 왕복 1회다.
  정시 메시지 한 건은 최대 4회(`all`/`hour`/`min`/`sum`)를 유발한다.

---

## 6. 보존 정책

`be/src/main/java/kr/co/mindone/ems/common/SchedulerService.java:114-122`

```java
@Scheduled(cron = "0 0 0 * * *")     // 매일 자정
public void oldDataDeleteTask(){
    commonService.deleteRawData(nowDateTime);
}
```

`common_mssql.xml:301-308`

```sql
DELETE FROM TB_RAWDATA WHERE TS <= DATE_SUB(#{nowDateTime}, INTERVAL 20 WEEK);
```

- 대상은 **`TB_RAWDATA` 뿐**이다. `_15MIN` / `_HOUR` / `_HOUR_INGRT` 는 삭제 대상이 아니며 무기한 누적된다.
- 월 단위 파티션이 있는데도 `DROP PARTITION` 이 아니라 **행 단위 `DELETE`** 를 쓴다.
- 같은 스케줄러가 `00:00:10` 에 `deleteEpanetFP`, `00:00:20` 에 `deleteEpanetFR` 을 이어서 돌린다
  (`:124-140`, 대상은 `TB_FP_VAL`/`TB_FR_VAL` 로 본 문서 범위 밖).

---

## 7. 언제 켜지는가 — 프로파일 게이트

**수집이 도는지 여부는 Spring 프로파일 하나로 결정된다.**

```java
// be/src/main/java/kr/co/mindone/ems/kafka/consumer/KafkaConfig.java:32-47
@Profile({ "gm2", "hy2", "hp2", "ji2", "gr", "wm", "gs", "gu", "ba", "ss" })
@Configuration
@EnableKafka
@PropertySource("classpath:application-${spring.profiles.active}.properties")
public class KafkaConfig { ... }
```

`dev` 가 목록에 없다. 따라서 dev 에서는 컨테이너 팩토리 빈 자체가 생성되지 않고 리스너도 뜨지 않는다.
`application-dev.properties` 에 kafka 키가 전혀 없어도 기동에 실패하지 않는 이유가 이것이다 —
`@Value("${spring.kafka.bootstrap-servers-1}")` 가 평가될 일 자체가 없다.

| 구성 파일 | 프로파일 | 수집 | 자정 삭제 |
|---|---|:--:|:--:|
| `docker-compose.yml:12` | `dev` | ✗ | ✗ |
| `docker-compose.gunsan-dev.yml:46` | `dev` | ✗ | ✗ |
| `deploy/gunsan/docker-compose.prod.yml:35` | `gu` | **✓** | **✓** |

`docker-compose.gunsan-dev.yml:44-45` 의 주석이 의도를 명시한다:

> dev 프로파일 유지: Kafka·SchedulerService(자정 삭제 3종)·PumpScheduler가 모두 비활성이라
> 군산 덤프에 쓰기/삭제가 발생하지 않는다. 운영은 gu 프로파일(포트 10014 + Kafka)을 쓴다.

**어느 compose 파일에도 Kafka 브로커·Zookeeper 서비스가 없다.** 브로커는 현장 SCADA 측 외부 인프라이고
컨테이너가 위 IP 로 직접 붙는다. 따라서 개발 PC 에서 운영 프로파일을 띄워도 현장망 밖에서는 연결되지 않는다.

---

## 8. 소비 측 (읽기 전용 — 개요)

적재된 데이터를 읽는 쪽은 전부 **DB 폴링**이다. 브로커에 직접 붙는 소비자는 없다.

| 주체 | 방식 | 근거 |
|---|---|---|
| `epa` (Flask) | `MAX(ts)` 기준 최신값 조회, APScheduler 5분 주기 관망 시뮬 | `epa/app/models/epa_models.py:16,31,59-60,182-197,263-278,533,613` |
| `be` (EMS API) | `@Scheduled` 다수 — 절감량·CO2·펌프조합 계산. `ai_mssql.xml` 에서 `TB_RAWDATA*` 를 대량 SELECT | `SchedulerService.java`, `pump/PumpScheduler.java`, `sqlmapper/mysql/ai_mssql.xml` |
| `inpEditor` (BE) | 최신 실측 조회 — **조회 전용임이 코드에 명시** | `inpEditor/BE/editor/src/main/java/com/mindone/editor/rawdata/repository/RawDataRepository.java:17,37` |
| MariaDB **EVENT** | `ev_tag_pred_eval` — 매 10분 `HH:x0:30` 에 `TB_RAWDATA` 윈도 평균을 읽어 `tag_pred_eval_l` 에 UPSERT. **`TB_RAWDATA` 에는 쓰지 않는다** | `inpEditor/BE/editor/src/main/resources/db/migration/V13__create_tag_pred_eval_table.sql:56-60` |
| `al` (Python) | 수요·전력 예측 학습/추론용 직접 조회 | `al/pump3/main_e.py:104`, `al/power/predictpower_Gosan_main.py:86` |

읽기 측 중 유일하게 **DB 안에서 도는 것**이 `ev_tag_pred_eval` EVENT 다. 애플리케이션 로그에 흔적이
남지 않으므로, 부하나 락을 추적할 때 이 존재를 놓치기 쉽다.

### 8.1 `pms-back` 은 `TB_RAWDATA` 와 무관하다 (혼동 주의)

`pms-back` 에도 Kafka 컨슈머(`kafka/comsumer/KafkaConsumerService2.java`, 디렉터리명 오타 `comsumer`)가 있고
`insertMsgHashMap()` / `insertRawData()` 라는 **똑같은 이름의 메서드**를 가지고 있다. 그러나
**대상 테이블이 완전히 다르다.**

```xml
<!-- pms-back/src/main/resources/mapper/CommonMapper.xml:23-24 -->
<insert id="insertRawData" parameterType="hashmap">
  INSERT INTO TB_PUMP_SCADA
    ( PUMP_SCADA_ID, CENTER_ID, ACQ_DATE, ... )
```

`pms-back` 의 `insertRawData` 는 `TB_PUMP_SCADA` 에 쓴다 — 태그값을 `targetKey`
(`EQ_ON_TAG` / `FREQUENCY_TAG` / `FLOW_RATE_TAG` …) 로 판별해 펌프별 **컬럼**에 꽂는 구조다
(`KafkaConsumerService2.java:288-301`). `TB_RAWDATA` 계열에는 한 줄도 쓰지 않는다.

게다가 그 `insertMsgHashMap()` 은 **현재 호출되지 않는다.** scada1/scada2 리스너 4곳 모두
호출이 주석 처리되고 그 자리에 `processMessage()` 가 들어가 있다:

```java
// KafkaConsumerService2.java:64-65 (:95-96, :120-121, :151-152 도 동일)
//insertMsgHashMap(messageMap);
processMessage(messageMap);
```

`pms-back` 의 실제 적재 경로는 두 갈래이며 **둘 다 `TB_RAWDATA` 와 무관**하다.

| 경로 | 흐름 | 대상 테이블 |
|---|---|---|
| scada1 / scada2 | `processMessage()`(`:387`) → `insertScadaDto()`(`:435-439`) | 펌프 SCADA 계열 |
| scada3 (IPC) | `commonService.msgInsert()`(`:178`, `:202`) | `TB_MOTOR` (`CommonMapper.xml:5-16`) |

**scada3 토픽 이름이 `DGSWGS_PMS_rawdata` 지만 `TB_RAWDATA` 와는 관계가 없다.**

### 8.2 매분 `@Scheduled` 는 적재가 아니다 (혼동 주의)

EMS 에서 "매분"을 검색하면 가장 먼저 걸리는 것이 아래다.

```java
// be/src/main/java/kr/co/mindone/ems/kafka/producer/KafkaProducerTasks.java:78
@Scheduled(cron = "0 * * * * ?") // 매분마다 실행
public void producerStart() { ... }
```

주석이 "매분마다 실행"이라 적재 스케줄러로 오인하기 쉬우나, **전력 예측 결과와 펌프 사용 정보를
SCADA 작화 화면으로 내보내는 송신(producer)** 이다(`:74-76`). `TB_RAWDATA` 를 읽지도 쓰지도 않는다.

`TB_RAWDATA` 에 관여하는 `@Scheduled` 는 **자정 20주 삭제 하나뿐**이다(§6, `SchedulerService.java:114-122`).
적재는 전부 Kafka 컨슈머가 메시지를 받은 그 순간에 일어난다.

---

## 9. 알려진 이슈 (관찰 기록 — 본 문서에서 수정하지 않음)

> **전제 — 적재 경로는 하나뿐이다.**
> `TB_RAWDATA` 계열에 행을 추가하는 경로는 **Kafka 컨슈머 → `insertRawData` 단 하나**다.
> 전역 검색으로 확인한 결과 스케줄러 쓰기 0건, DB `EVENT`/`TRIGGER`/`PROCEDURE` 쓰기 0건
> (§8 의 `ev_tag_pred_eval` 포함 3개 모두 읽기 전용이거나 무관), Python 쓰기 0건,
> `LOAD DATA`·덤프 복원 0건이다. `TB_RAWDATA` 에 대한 **유일한 다른 쓰기 연산은 `deleteRawData`**
> 이며 이는 삭제다(§6). 따라서 아래 이슈를 검토할 때 "다른 경로가 있을 것"이라는 가정은 필요 없다.

수집 경로는 현장 운영 중이므로 아래는 **사실 기록**일 뿐이며, 손대기 전 별도 합의가 필요하다.

| # | 내용 | 근거 |
|---|---|---|
| 1 | 초 단위 데이터 전량 폐기 — 테이블명(`RAWDATA`)과 실제 해상도(1분) 불일치 | `:381`, `:486-509` |
| 2 | 단건 INSERT — 배치 없음. 메시지 1건당 SQL 1~4회 왕복 | `common_mssql.xml:19-48` |
| 3 | 화이트리스트가 `wppTagList` 필드에 **최초 1회만** 캐싱 — 태그를 DB 에 추가해도 **재기동 전까지 반영 안 됨**. 갱신 API·스케줄러 없음 (§4.1) | `:266-275`, `:328-331` |
| 3-2 | 화이트리스트 매칭이 `List` 선형 스캔 — 메시지 1건당 O(N). 결국 폐기될 초 단위 메시지도 스캔을 전부 거친다. `HashSet<String>` 이면 O(1) | `:333-337` |
| 3-3 | `TB_WPP_TAG_INF` 에 PK·인덱스 없고 전 컬럼 nullable. `WPP_CODE` 가 있으나 조회 쿼리가 쓰지 않아 사이트 분리를 DB 인스턴스 분리에만 의존 | `ems_schema.md:2293-2298`, `common_mssql.xml:8-18` |
| 4 | `INSERT IGNORE` 로 정정값 무시 | `common_mssql.xml:20` |
| 5 | 적산 조회 범위에 현재 시각 포함 + `ORDER BY` 부재 → 저장값이 DB 행 반환 순서에 의존 | `common_mssql.xml:224`, `:405-418` |
| 6 | 적산 대상 정규식(`FIQ` 포함)과 SQL `TAG_GRP` 필터(`FIQ` 누락) 불일치 | `:404` vs `common_mssql.xml:225` |
| 7 | 파티션이 있으나 `DROP PARTITION` 대신 행 단위 `DELETE` | `common_mssql.xml:301-308` |
| 8 | 롤업 3종에 보존 정책 없음 — 무기한 누적 | `SchedulerService.java:114-122` |
| 9 | `be/.../kafka/` 루트에 구버전 중복본이 남아 있음. 헤더에 *"kafka 2중화 구성변경으로 미사용"* 이라 적혀 있고 `@Profile("!dev & !gm2 & … & !ss")` 로 **운영 프로파일 전부에서 배제**되므로 동작하지는 않으나, 같은 클래스명이 두 벌이라 탐색 시 혼동 | `kafka/KafkaConsumerService.java:1-3,31`(408줄) vs `kafka/consumer/KafkaConsumerService.java`(699줄) |
| 10 | 합성 태그 목록·단위 환산 계수가 클래스 상수로 하드코딩 (고산 전용) | `:94-123` |

> §9 의 `파일:라인` 중 경로가 생략된 것은 모두
> `be/src/main/java/kr/co/mindone/ems/kafka/consumer/KafkaConsumerService.java` 기준이고,
> `common_mssql.xml` 은 `be/src/main/resources/sqlmapper/mysql/common_mssql.xml` 이다.
