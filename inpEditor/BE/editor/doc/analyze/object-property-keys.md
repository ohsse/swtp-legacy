# 객체 프로퍼티 키 ↔ 한글 키값 매핑

> EPANET INP 에디터 백엔드가 상세조회 응답(`NetworkDetailResponse`)으로 내보내는 **객체별 프로퍼티 키**와
> 그에 대응하는 **한글 키값(UI 라벨)** 을 정리한 문서다.
>
> - **근거**
>   - 코드: `com.mindone.editor.inp.network.combiner` 패키지
>     (`NetworkAssembler`, `GeoJsonCombiner`, `NonVisualSectionCombiner`, `OptionsCombiner`)
>   - 사양: `doc/manual/06_objects.md`(속성편집기 6.4 / 비가시 편집기 6.5),
>     `doc/manual/appendix_back_matter.md`(부록 C — INP 섹션 명세)
> - **프로퍼티 키**: 코드가 응답 JSON 에 실제로 넣는 키(camelCase). 프론트가 폼/지도 바인딩에 쓰는 키다.
> - **한글 키값**: 화면에 표시할 라벨. 매뉴얼의 영문 라벨(`*PROPERTY*`)을 한국어로 옮긴 것.
> - **영문 라벨**: 매뉴얼 6.4/6.5 표의 원문 라벨(번역 근거).
> - **INP 섹션**: 해당 값의 1차 출처 섹션. 한 객체의 속성이 여러 섹션에 흩어져 있으며,
>   `NetworkAssembler` 가 ID 로 join 해 한 객체의 `properties` 로 병합한다(역방향은 `InpComposer`).

---

## 0. 분류 개요

EPANET 객체는 **지도에 표시되는 가시(Visual) 객체**와 **설계·운영 정보를 담는 비가시(Non-Visual) 객체**로 나뉜다
(매뉴얼 6.1).

| 구분 | 객체 | 응답 위치 |
| --- | --- | --- |
| **가시 객체** | 절점 / 저수지 / 탱크 / 관로 / 펌프 / 밸브 / 지도 라벨 | `layers.nodeLayer` · `layers.linkLayer` · `layers.labelLayer` (GeoJSON Feature `properties`) |
| **비가시 객체** | 곡선 / 시간패턴 / 단순 제어 / 규칙 기반 제어 / 제목 / 보고 옵션 | `sections.{CURVES, PATTERNS, CONTROLS, RULES, TITLE, REPORT, …}` |
| **해석 옵션** | 수리 / 수질 / 반응 / 시간 / 에너지 설정 | `options.{hydraulics, quality, reactions, times, energy}` |

> 객체 속성은 **EPANET 속성편집기(매뉴얼 6.4)** 처럼 여러 섹션(`TAGS`/`DEMANDS`/`STATUS`/`EMITTERS`/
> `QUALITY`/`SOURCES`/`MIXING`/`REACTIONS`/`ENERGY`)에 분산돼 있다. 백엔드가 이를 ID 로 모아 한 객체로 보여준다.

---

## 1. 가시 객체 (Visual Objects)

### 1.0 모든 가시 객체 공통 키 (GeoJSON Feature)

`GeoJsonCombiner` 가 모든 Feature 에 기본으로 넣는 키.

| 프로퍼티 키 | 한글 키값 | 설명 |
| --- | --- | --- |
| `id` | ID | 객체 고유 식별자(라벨은 `label-0`처럼 자동 생성) |
| `objectType` | 객체 유형 | `junction`/`reservoir`/`tank`/`pipe`/`pump`/`valve`/`label` (소문자) |
| `layer` | 레이어 | 표출 레이어 구분 키 |

### 1.1 절점 (Junction) — `doc/manual` Table 6.1

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 섹션 | 비고 |
| --- | --- | --- | --- | --- |
| `description` | 설명 | Description | 인라인 주석 | 객체 라인의 `;` 주석 |
| `tag` | 태그 | Tag | `[TAGS]` | 압력대 등 분류용 |
| `elevation` | 표고(고도) | Elevation | `[JUNCTIONS]` | 필수. 압력 계산용 |
| `baseDemand` | 기준 수요량 | Base Demand | `[JUNCTIONS]` | 음수=외부 유입원 |
| `demandPattern` | 수요 패턴 | Demand Pattern | `[JUNCTIONS]` | 시간패턴 ID |
| `demandCategories` | 수요 카테고리 | Demand Categories | `[DEMANDS]` | 객체 배열(§1.8) |
| `emitterCoefficient` | 이미터 계수 | Emitter Coefficient | `[EMITTERS]` | 스프링클러/노즐 토출 계수 |
| `initialQuality` | 초기 수질 | Initial Quality | `[QUALITY]` | |
| `sourceQuality` | 소스 수질 | Source Quality | `[SOURCES]` | 객체(§1.9) |

### 1.2 저수지 (Reservoir) — Table 6.2

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 섹션 | 비고 |
| --- | --- | --- | --- | --- |
| `description` | 설명 | Description | 인라인 주석 | |
| `tag` | 태그 | Tag | `[TAGS]` | |
| `totalHead` | 총 수두 | Total Head | `[RESERVOIRS]` | 필수. 표고+압력수두 |
| `headPattern` | 수두 패턴 | Head Pattern | `[RESERVOIRS]` | 수두 시간 변동 패턴 ID |
| `initialQuality` | 초기 수질 | Initial Quality | `[QUALITY]` | |
| `sourceQuality` | 소스 수질 | Source Quality | `[SOURCES]` | 객체(§1.9) |

### 1.3 탱크 (Tank) — Table 6.3

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 섹션 | 비고 |
| --- | --- | --- | --- | --- |
| `description` | 설명 | Description | 인라인 주석 | |
| `tag` | 태그 | Tag | `[TAGS]` | |
| `elevation` | 표고(고도) | Elevation | `[TANKS]` | 필수. 탱크 바닥 표고 |
| `initialLevel` | 초기 수위 | Initial Level | `[TANKS]` | 필수 |
| `minimumLevel` | 최소 수위 | Minimum Level | `[TANKS]` | 필수 |
| `maximumLevel` | 최대 수위 | Maximum Level | `[TANKS]` | 필수 |
| `diameter` | 직경 | Diameter | `[TANKS]` | 필수 |
| `minimumVolume` | 최소 부피 | Minimum Volume | `[TANKS]` | 선택 |
| `volumeCurve` | 부피 곡선 | Volume Curve | `[TANKS]` | 곡선 ID(없으면 원통형) |
| `canOverflow` | 월류 허용 여부 | Can Overflow | `[TANKS]` | EPANET 2.2 추가 |
| `mixingModel` | 혼합 모델 | Mixing Model | `[MIXING]` | MIXED/2COMP/FIFO/LIFO |
| `mixingFraction` | 혼합 비율 | Mixing Fraction | `[MIXING]` | 2COMP 전용 |
| `reactionCoefficient` | 반응 계수 | Reaction Coefficient | `[REACTIONS]` TANK | 벌크 반응 계수(1/days) |
| `initialQuality` | 초기 수질 | Initial Quality | `[QUALITY]` | |
| `sourceQuality` | 소스 수질 | Source Quality | `[SOURCES]` | 객체(§1.9) |

### 1.4 관로 (Pipe) — Table 6.4

> 링크 공통으로 `startNode`/`endNode` 가 추가된다(`GeoJsonCombiner`).

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 섹션 | 비고 |
| --- | --- | --- | --- | --- |
| `startNode` | 시작 노드 | Start Node | `[PIPES]` | 필수 |
| `endNode` | 끝 노드 | End Node | `[PIPES]` | 필수 |
| `description` | 설명 | Description | 인라인 주석 | |
| `tag` | 태그 | Tag | `[TAGS]` | |
| `length` | 길이 | Length | `[PIPES]` | 필수 |
| `diameter` | 직경 | Diameter | `[PIPES]` | 필수 |
| `roughness` | 조도 계수 | Roughness | `[PIPES]` | 필수 |
| `lossCoefficient` | 미소손실 계수 | Loss Coefficient | `[PIPES]` | 기본 0 |
| `initialStatus` | 초기 상태 | Initial Status | `[PIPES]`/`[STATUS]` | OPEN/CLOSED/CV |
| `bulkCoefficient` | 벌크 반응 계수 | Bulk Coefficient | `[REACTIONS]` BULK | 1/days |
| `wallCoefficient` | 벽면 반응 계수 | Wall Coefficient | `[REACTIONS]` WALL | 1/days |

### 1.5 펌프 (Pump) — Table 6.5

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 섹션 | 비고 |
| --- | --- | --- | --- | --- |
| `startNode` | 시작 노드(흡입측) | Start Node | `[PUMPS]` | 필수 |
| `endNode` | 끝 노드(토출측) | End Node | `[PUMPS]` | 필수 |
| `description` | 설명 | Description | 인라인 주석 | |
| `tag` | 태그 | Tag | `[TAGS]` | |
| `pumpCurve` | 펌프 곡선 | Pump Curve | `[PUMPS]` HEAD | 곡선 ID |
| `power` | 출력(정전력) | Power | `[PUMPS]` POWER | hp/kw |
| `speed` | 상대 속도 | Speed | `[PUMPS]` SPEED | 무차원 |
| `pattern` | 속도 패턴 | Pattern | `[PUMPS]` PATTERN | 작동 제어 패턴 ID |
| `initialStatus` | 초기 상태 | Initial Status | `[STATUS]` | OPEN/CLOSED |
| `efficiencyCurve` | 효율 곡선 | Efficiency Curve | `[ENERGY]` EFFIC | 곡선 ID |
| `energyPrice` | 에너지 단가 | Energy Price | `[ENERGY]` PRICE | kw-hr 당 |
| `pricePattern` | 단가 패턴 | Price Pattern | `[ENERGY]` PATTERN | 시간대별 단가 패턴 ID |

### 1.6 밸브 (Valve) — Table 6.6

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 섹션 | 비고 |
| --- | --- | --- | --- | --- |
| `startNode` | 시작 노드(유입측) | Start Node | `[VALVES]` | 필수 |
| `endNode` | 끝 노드(토출측) | End Node | `[VALVES]` | 필수 |
| `description` | 설명 | Description | 인라인 주석 | |
| `tag` | 태그 | Tag | `[TAGS]` | |
| `diameter` | 직경 | Diameter | `[VALVES]` | 필수 |
| `type` | 밸브 유형 | Type | `[VALVES]` | PRV/PSV/PBV/FCV/TCV/GPV |
| `setting` | 설정값 | Setting | `[VALVES]` | 유형별 의미 상이 |
| `lossCoefficient` | 미소손실 계수 | Loss Coefficient | `[VALVES]` | 완전 개방 시, 기본 0 |
| `fixedStatus` | 고정 상태 | Fixed Status | `[STATUS]` | OPEN/CLOSED/NONE |

> **밸브 Setting 의미**: PRV/PSV/PBV=압력, FCV=유량, TCV=손실계수, GPV=수두손실 곡선 ID.

### 1.7 지도 라벨 (Map Label) — Table 6.7

> `layers.labelLayer` 의 Feature. 좌표는 GeoJSON geometry 로 표현되어 별도 키로 두지 않는다.
> (Meter Type/Meter ID/Font 는 EPANET GUI 전용으로 INP 에 없어 노출하지 않음.)

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 섹션 | 비고 |
| --- | --- | --- | --- | --- |
| `text` | 텍스트 | Text | `[LABELS]` | 라벨 문자열 |
| `anchorNode` | 앵커 노드 | Anchor Node | `[LABELS]` | 앵커 기준 노드 ID(없으면 null) |

### 1.8 수요 카테고리 (Demand Category) — Table 6.9 / Demand Editor

> 절점 `demandCategories` 배열의 각 원소. (`[DEMANDS]` 섹션)

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | 비고 |
| --- | --- | --- | --- |
| `baseDemand` | 기준 수요량 | Base Demand | 필수 |
| `timePattern` | 시간 패턴 | Time Pattern | 시간패턴 ID(선택) |
| `category` | 카테고리 | Category | 사용자 분류 라벨(선택) |

### 1.9 소스 수질 (Source Quality) — Table 6.10 / Source Quality Editor

> 노드 `sourceQuality` 객체. (`[SOURCES]` 섹션)

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | 비고 |
| --- | --- | --- | --- |
| `sourceType` | 소스 유형 | Source Type | CONCEN/MASS/FLOWPACED/SETPOINT |
| `sourceQuality` | 소스 수질 | Source Quality | 기준 농도 또는 질량유량 |
| `qualityPattern` | 수질 패턴 | Quality Pattern | 시간패턴 ID |

---

## 2. 비가시 객체 (Non-Visual Objects)

`sections` 아래에 섹션명(`CURVES`, `PATTERNS` …) 키로 들어간다.

### 2.1 곡선 (Curves) — Table 6.8 / Curve Editor

> `sections.CURVES` = 곡선 객체 배열.

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | 비고 |
| --- | --- | --- | --- |
| `id` | 곡선 ID | Curve ID | |
| `curveType` | 곡선 유형 | Curve Type | PUMP/EFFICIENCY/VOLUME/HEADLOSS — 사용처 기반 추론 |
| `description` | 설명 | Description | 직전 주석에서 추출 |
| `xyData` | X-Y 데이터 | X-Y Data | 점 배열 `[{x, y}]` |
| `xyData[].x` | X 값 | X | 숫자 |
| `xyData[].y` | Y 값 | Y | 숫자 |

### 2.2 시간패턴 (Time Patterns) — Table 6.9 / Pattern Editor

> `sections.PATTERNS` = 패턴 객체 배열.

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | 비고 |
| --- | --- | --- | --- |
| `id` | 패턴 ID | Pattern ID | |
| `description` | 설명 | Description | 직전 주석에서 추출 |
| `multipliers` | 배율 목록 | Multipliers | 시간대별 배율 숫자 배열 |

### 2.3 단순 제어 (Controls) — Controls Editor

> `sections.CONTROLS` = 제어문 원본 텍스트 라인 배열(문자열). 의미 필드로 분해하지 않음
> (EPANET Controls Editor 가 텍스트 편집기 창이므로). 프론트는 `join('\n')` 으로 바인딩.

### 2.4 규칙 기반 제어 (Rules) — Controls Editor

> `sections.RULES` = 규칙 블록 배열.

| 프로퍼티 키 | 한글 키값 | 비고 |
| --- | --- | --- |
| `id` | 규칙 ID | `RULE <id>` |
| `content` | 규칙 본문 | IF/AND/THEN/PRIORITY 절을 개행 구분 한 문자열로 |

### 2.5 기타 비가시 섹션

| 섹션 | 한글 키값 | 형태 | 비고 |
| --- | --- | --- | --- |
| `TITLE` | 제목 | 문자열 배열 | 자유 텍스트 라인 |
| `REPORT` | 보고 옵션 | 키-밸류 맵 | 파라미터→값 |
| `LABELS` | 라벨(데이터) | 객체 배열 | `{text, x, y, anchorNode}` (지도 표출은 §1.7) |
| `UNKNOWN:<원본헤더>` | 미지 섹션 | 원본 라인 배열 | 표준 외 섹션 무손실 보존 |

---

## 3. 해석 옵션 (Analysis Options)

`options` 아래에 5범주로 묶인다. 키는 매뉴얼 8.1(Analysis Options) 라벨을 camelCase 로 옮긴 것
(`OptionsCombiner`). INP 에 없는 항목은 키를 만들지 않는다(프론트가 기본값 표시).

### 3.1 수리 (Hydraulics) — `options.hydraulics`

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 키워드 |
| --- | --- | --- | --- |
| `flowUnits` | 유량 단위 | Flow Units | `UNITS` |
| `headlossFormula` | 손실수두 공식 | Headloss Formula | `HEADLOSS` |
| `specificGravity` | 비중 | Specific Gravity | `SPECIFIC GRAVITY` |
| `relativeViscosity` | 상대 점성 | Relative Viscosity | `VISCOSITY` |
| `maximumTrials` | 최대 시행 횟수 | Maximum Trials | `TRIALS` |
| `accuracy` | 정확도 | Accuracy | `ACCURACY` |
| `ifUnbalanced` | 불균형 시 처리 | If Unbalanced | `UNBALANCED` |
| `defaultPattern` | 기본 패턴 | Default Pattern | `PATTERN` |
| `demandMultiplier` | 수요 배율 | Demand Multiplier | `DEMAND MULTIPLIER` |
| `emitterExponent` | 이미터 지수 | Emitter Exponent | `EMITTER EXPONENT` |
| `demandModel` | 수요 모델 | Demand Model | `DEMAND MODEL` (DDA/PDA) |
| `minimumPressure` | 최소 압력 | Minimum Pressure | `MINIMUM PRESSURE` |
| `requiredPressure` | 필요 압력 | Required Pressure | `REQUIRED PRESSURE` |
| `pressureExponent` | 압력 지수 | Pressure Exponent | `PRESSURE EXPONENT` |
| `checkFreq` | 상태 점검 빈도 | Check Frequency | `CHECKFREQ` |
| `maxCheck` | 최대 점검 횟수 | Max Check | `MAXCHECK` |
| `dampLimit` | 감쇠 한계 | Damp Limit | `DAMPLIMIT` |
| `maxHeadError` | 최대 수두 오차 | Max Head Error | `HEADERROR` |
| `maxFlowChange` | 최대 유량 변화 | Max Flow Change | `FLOWCHANGE` |

### 3.2 수질 (Quality) — `options.quality`

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 키워드 |
| --- | --- | --- | --- |
| `parameter` | 수질 항목 | Parameter | `QUALITY` (NONE/CHEMICAL/AGE/TRACE) |
| `massUnits` | 질량 단위 | Mass Units | `QUALITY CHEMICAL <단위>` |
| `traceNode` | 추적 노드 | Trace Node | `QUALITY TRACE <노드>` |
| `relativeDiffusivity` | 상대 확산도 | Relative Diffusivity | `DIFFUSIVITY` |
| `qualityTolerance` | 수질 허용오차 | Quality Tolerance | `TOLERANCE` |

### 3.3 반응 (Reactions) — `options.reactions`

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 키워드 |
| --- | --- | --- | --- |
| `bulkReactionOrder` | 벌크 반응 차수 | Bulk Reaction Order | `ORDER BULK` |
| `wallReactionOrder` | 벽면 반응 차수 | Wall Reaction Order | `ORDER WALL` |
| `tankReactionOrder` | 탱크 반응 차수 | (INP 전용) | `ORDER TANK` |
| `globalBulkCoefficient` | 전역 벌크 계수 | Global Bulk Coefficient | `GLOBAL BULK` |
| `globalWallCoefficient` | 전역 벽면 계수 | Global Wall Coefficient | `GLOBAL WALL` |
| `limitingConcentration` | 제한 농도 | Limiting Concentration | `LIMITING` |
| `wallCoefficientCorrelation` | 벽면 계수 상관관계 | Wall Coefficient Correlation | `ROUGHNESS` |

> 요소별 계수(`BULK/WALL/TANK <id> <c>`)는 이 범주에 없다 — 관로 `bulkCoefficient`/`wallCoefficient`,
> 탱크 `reactionCoefficient` 로 객체 properties 에 병합되며 저장도 그쪽이 단일 출처다.

### 3.4 시간 (Times) — `options.times`

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 키워드 |
| --- | --- | --- | --- |
| `totalDuration` | 총 모의 기간 | Total Duration | `DURATION` |
| `hydraulicTimeStep` | 수리 시간 간격 | Hydraulic Time Step | `HYDRAULIC TIMESTEP` |
| `qualityTimeStep` | 수질 시간 간격 | Quality Time Step | `QUALITY TIMESTEP` |
| `patternTimeStep` | 패턴 시간 간격 | Pattern Time Step | `PATTERN TIMESTEP` |
| `patternStartTime` | 패턴 시작 시각 | Pattern Start Time | `PATTERN START` |
| `reportingTimeStep` | 보고 시간 간격 | Reporting Time Step | `REPORT TIMESTEP` |
| `reportStartTime` | 보고 시작 시각 | Report Start Time | `REPORT START` |
| `startingTimeOfDay` | 시작 시각(시계) | Starting Time of Day | `START CLOCKTIME` |
| `ruleTimeStep` | 규칙 시간 간격 | (INP 전용) | `RULE TIMESTEP` |
| `statistic` | 통계 | Statistic | `STATISTIC` |

### 3.5 에너지 (Energy) — `options.energy`

| 프로퍼티 키 | 한글 키값 | 영문 라벨 | INP 키워드 |
| --- | --- | --- | --- |
| `pumpEfficiency` | 펌프 효율 | Pump Efficiency | `GLOBAL EFFICIENCY` |
| `energyPrice` | 에너지 단가 | Energy Price | `GLOBAL PRICE` |
| `pricePattern` | 단가 패턴 | Price Pattern | `GLOBAL PATTERN` |
| `demandCharge` | 수요 요금 | Demand Charge | `DEMAND CHARGE` |
| `pumps` | 펌프별 항목 목록 | — | `PUMP <id> …` |
| `pumps[].id` | 펌프 ID | — | |
| `pumps[].efficiencyCurve` | 효율 곡선 | Efficiency Curve | `PUMP <id> EFFIC` |
| `pumps[].energyPrice` | 에너지 단가 | Energy Price | `PUMP <id> PRICE` |
| `pumps[].pricePattern` | 단가 패턴 | Price Pattern | `PUMP <id> PATTERN` |

---

## 부록. 참고 사항

- **값 타입**: 숫자로 파싱되는 값은 `Double`, 아니면 원본 문자열. 옵션·시각 값은 표시/편집용 문자열 그대로 둔다
  (시각 `01:00:00`, 차수 `1` 등 UI 변환은 프론트 몫).
- **누락 키 정책**:
  - 가시 객체(절점/저수지/탱크/관로/펌프/밸브)는 6.4 **전체 스키마를 미리 `null` 로 깔아** 둔다 →
    프론트가 키 유무 검사 없이 폼을 그릴 수 있다.
  - 비가시 섹션·옵션은 INP 에 **없으면 키를 만들지 않는다** → 프론트가 기본값 표시.
- **라운드트립**: 위 키 매핑의 정확한 역연산이 `InpComposer`(역방향 저장)에 있다. 키를 추가/변경할 때는
  Combiner(정방향)와 `InpComposer`(역방향)를 항상 짝으로 수정해야 라운드트립이 보존된다.
- **단위계**: 모든 수치 단위는 `options.hydraulics.flowUnits`(UNITS) 선택에 따라 US/SI 가 결정된다
  (부록 A 측정 단위 참조).
