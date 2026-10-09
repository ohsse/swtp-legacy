# 펌프 성능곡선 표본 조회 API — 설계서

> **상태**: 설계 초안 (구현 전 사전 설계). 본 문서는 `swtp/backend` 코드를 변경하지 않으며, 데이터 모델·표준 어휘 확정은 별도 `/dev:analyze` 5인 회의를 전제로 한다.
> **작성일**: 2026-06-29 (rev2 — Y축을 압력→양정으로 정정)
> **근거 레거시**: `legacy/ems` — `DrvnConfig.pressureCalValue()` (`DrvnConfig.java:4944`), 성능곡선 생성 루프 (`DrvnConfig.java:579`)
> **대상 스택**: Java 21 / Spring Boot 4.0.5 / JPA / PostgreSQL (swtp backend)

---

## 0. 개정 이력 (rev1 → rev2): Y축을 양정으로 정정

펌프 성능곡선(제조사 특성곡선)의 표준 축은 **유량(Q) vs 양정(Head, m)** 이다. rev1 은 레거시 `pressureCalValue` 를 그대로 옮겨 Y축을 **압력(prsr)** 으로 두었으나 다음 근거로 **양정(head)** 으로 정정한다.

| 근거 | 내용 |
|------|------|
| swtp 모델 일관성 | swtp 는 펌프 정격 사양을 `rated_head`(정격 양정, m) · `rated_flwrt`(정격 유량) 로 정의한다. 펌프에 `rated_prsr` 은 없다. 따라서 그 펌프의 성능곡선 Y축도 **양정(head)** 이어야 `rated_head` 와 축이 일치한다. |
| 표준 단어 분리 | swtp 사전은 `head`(양정, m) 와 `prsr`(압력, kgf/cm²) 를 별개 단어로 구분한다. 성능곡선은 `head` 사용이 맞다. |
| 물리적 동치 | 양정·압력은 `P = ρ·g·H` (물: 1 kgf/cm² ≈ 10 m) 로 단위만 다른 동일 정보. **2차식 샘플링 수학은 Y축이 무엇이든 동일**하며, 바뀌는 것은 라벨·단위·표준 단어뿐이다. |
| 레거시 정합성 | 레거시는 곡선 전체를 `calPressure`/`pressSum`/`targetpressList` 로 다루고 `head`/양정 처리는 0건 — 제조사 H–Q 특성곡선이 아니라 **현장 토출압력(PRI) 실측 피팅 곡선**일 가능성. 그렇다면 명칭이 "성능곡선"이 아니라 "유량-토출압력 곡선"이어야 정직하므로, 본 설계는 명칭에 맞게 **양정 기준 성능곡선**으로 재정의한다. |

> 곡선 원천이 (a) 제조사 H–Q 특성곡선인지 (b) 현장 토출압력 실측 피팅인지는 `/dev:analyze` 결정 사항(§9 Q4). (b)일 경우 `H = P/(ρg)` 변환 정책을 함께 확정한다.

---

## 1. 목적

특정 펌프(조합)의 성능곡선 회귀식을 기반으로, **운전원이 지정한 유량 구간 `[minFlow, maxFlow]` 에 대해 N개의 (유량, 양정) 표본점을 산출**하여 프론트엔드 차트에 그릴 수 있는 데이터를 제공한다.

핵심 수식 (레거시 `pressureCalValue` 의 2차식 구조 계승, Y축만 양정으로 정정):

```
H(Q) = a·Q² + b·Q + c          (Q: 유량 m³/h, H: 양정 m)
```

| 계수 | 레거시 컬럼 | 실제 수학적 역할 |
|------|------------|----------------|
| `a` | `P_ADD_VAL` | 2차항 계수 (quadratic) |
| `b` | `P_MUL_VAL` | 1차항 계수 (linear) |
| `c` | `P_SQRT_MUL_VAL` | 상수항 (constant) |

> ⚠️ **레거시 라벨 부채 2건**:
> 1. `add`/`mul`/`sqrt_mul` 이름은 실제 수식 역할(2차항/1차항/상수항)과 불일치 → swtp 는 `quadCoef`/`linearCoef`/`constCoef` 로 재명명.
> 2. 레거시 산출물을 "압력(pressure)"으로 라벨링했으나 성능곡선의 표준 종속변수는 **양정(head)** → swtp 는 `head` 로 정정 (위 §0).

---

## 2. 설계 범위

### 포함 (In scope)
- 계수 3개 + 유량 구간 → (유량, 양정) 표본점 리스트 산출하는 **조회(read) API**
- 표본 개수(N) 고정 방식 샘플링 알고리즘 (레거시의 "간격 1 또는 10" 방식 개선)
- 요청 검증·에러 응답 계약

### 비범위 (Out of scope) — 별도 작업
- **계수 산출(회귀 피팅) 로직** — 레거시도 `TB_PUMP_CAL` 에 저장된 계수를 *읽기만* 한다. 계수를 만들어 내는 회귀분석은 AI 서버 또는 별도 배치의 책임이며 본 API 범위 밖이다.
- **계수 저장 테이블의 신규 설계** — 데이터 모델은 §6 에서 후보만 제시하고 `/dev:analyze` 로 위임.
- **펌프 조합(`pump_cmbn`) 도메인 재설계** — swtp 에서 백지화(2026-05-12)되어 재설계 예정 영역. 본 API 는 그 결과에 의존.
- **양정↔압력 단위 변환** — 곡선 원천이 압력 실측일 경우의 `H = P/(ρg)` 변환은 §9 Q4 결정 후 별도 처리.

---

## 3. 아키텍처 결정 — 계수 공급 방식

핵심 분기점: **계수를 어디서 가져오는가.** 두 안을 비교한다.

### 안 A — 저장 계수 조회형 (레거시 동형, 권장)
백엔드가 펌프 조합별 계수를 DB(신규 테이블)에서 조회한 뒤 샘플링.

- 요청: `곡선 식별자(조합 등) + (선택) 구간 override + N`
- 장점: 레거시 흐름과 동일, 클라이언트가 계수를 몰라도 됨, 계수 SSOT 가 DB
- 단점: 계수 저장 테이블 신규 설계 필요 (`/dev:analyze` 의존)

### 안 B — 무상태 계산형 (계수 직접 전달)
클라이언트가 계수 3개와 구간을 직접 넘기면 백엔드는 순수 계산만.

- 요청: `a, b, c, minFlow, maxFlow, N`
- 장점: DB 의존 0, 즉시 구현 가능, 테스트 용이
- 단점: 계수 출처/신뢰성을 클라이언트가 책임, 곡선 메타(조합명 등) 표현 불가

### 권장
**안 A 를 최종 목표로 하되, 1차는 안 B(무상태 계산형)로 분리 출시.**

근거:
- 안 B 는 계수 저장 테이블이 확정되기 전에도 **샘플링 엔진(Service)을 먼저 검증**할 수 있다 (계산 로직과 데이터 모델의 디커플링 — `coding-discipline.md §2` 단순성 우선).
- 안 A 는 안 B 의 샘플링 Service 를 그대로 재사용하고, 앞단에 "조합 → 계수 조회" 어댑터만 추가하면 된다. 즉 두 안은 경쟁이 아니라 **단계**다.

본 문서의 §4·§5 는 안 B(무상태 계산형) 기준으로 상세화하고, 안 A 의 데이터 모델은 §6 에서 후보로 제시한다.

---

## 4. API 명세 (1차 — 안 B 기준)

### 엔드포인트

```
POST /api/{도메인}/pump-curve/samples
```

> 메서드 POST 채택 근거: 계수·구간·N 을 담은 요청 바디가 있고, 향후 계수 배열(다중 곡선 동시 산출)로 확장 가능. 단일 곡선 GET(쿼리스트링) 방식도 가능하나 확장성·가독성에서 POST 우위.
> `{도메인}` 은 `/dev:analyze` 에서 비즈니스 도메인 약어 확정 후 결정 (§6 참조).

### 요청 바디 — `PumpCurveSampleRequestDto`

```json
{
  "quadCoef": -0.0000098,
  "linearCoef": 0.0042,
  "constCoef": 55.0,
  "minFlow": 100.0,
  "maxFlow": 2000.0,
  "sampleCount": 50
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `quadCoef` | number | ✅ | — | 2차항 계수 a (레거시 `P_ADD_VAL`) |
| `linearCoef` | number | ✅ | — | 1차항 계수 b (레거시 `P_MUL_VAL`) |
| `constCoef` | number | ✅ | — | 상수항 c (레거시 `P_SQRT_MUL_VAL`) |
| `minFlow` | number | ✅ | — | 구간 시작 유량 (m³/h) |
| `maxFlow` | number | ✅ | — | 구간 끝 유량 (m³/h) |
| `sampleCount` | int | ❌ | 50 | 표본 개수 N (2 ≤ N ≤ 500) |

> 펌프 성능곡선은 통상 우하향(유량↑ → 양정↓) 이라 `quadCoef` 가 음수가 되는 경우가 많다. 계수 부호 제약은 두지 않는다(원천 피팅 결과 그대로 수용).

### 응답 — `CommonResponseDto<PumpCurveSampleDto>`

```json
{
  "code": "SUCCESS",
  "data": {
    "quadCoef": -0.0000098,
    "linearCoef": 0.0042,
    "constCoef": 55.0,
    "minFlow": 100.0,
    "maxFlow": 2000.0,
    "sampleCount": 50,
    "samples": [
      { "flow": 100.0,  "head": 55.32 },
      { "flow": 138.78, "head": 55.39 },
      { "flow": 2000.0, "head": 24.20 }
    ]
  }
}
```

- 표본점은 `(flow, head)` — **X축 유량(m³/h), Y축 양정(m)**.
- 응답에 **계수도 함께 반환**한다 → 프론트가 차트 줌/리샘플 시 백엔드 재호출 없이 자체 계산 가능 (안 B 의 무상태 특성을 클라이언트에 그대로 노출).
- `samples` 의 첫 점 `flow == minFlow`, 마지막 점 `flow == maxFlow` 를 **부동소수 오차 없이 정확히** 보장 (§5 알고리즘).

---

## 5. Service 샘플링 알고리즘

### 핵심 개선 — 간격 고정(레거시) → 표본 개수 고정(신규)

| 구분 | 레거시 | 신규 |
|------|--------|------|
| 방식 | 간격 `flusFlow` = 1, 구간 1000 초과 시 10 | 표본 개수 N 고정 |
| 좁은 구간 (5~12) | 7점 → 곡선이 각짐 | 항상 N점 → 매끄러움 일정 |
| 넓은 구간 (0~2000) | 200점 → 과잉 | 항상 N점 → 일정 |
| 간격 계산 | 고정 상수 | `step = (max − min) / (N − 1)` |

### 의사 코드

```
입력: a, b, c, minFlow, maxFlow, N
검증:
  - minFlow < maxFlow            아니면 INVALID_FLOW_RANGE
  - 2 ≤ N ≤ 500                  아니면 INVALID_SAMPLE_COUNT

step = (maxFlow - minFlow) / (N - 1)
samples = []
for i in 0 .. N-1:
    flow = (i < N-1) ? (minFlow + i * step) : maxFlow   # 마지막 점은 정확히 maxFlow
    head = a * flow^2 + b * flow + c                    # 양정(m)
    samples.add({ flow, head })
return samples
```

### Java 스케치 (swtp 패턴 정렬 — 확정 아님)

```java
@Service
@Slf4j
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class PumpCurveService {

    private static final int MIN_SAMPLE = 2;
    private static final int MAX_SAMPLE = 500;

    /**
     * 성능곡선 회귀식을 유량 구간 [minFlow, maxFlow] 에서 N개 표본점(유량, 양정)으로 산출한다.
     * H(Q) = quadCoef·Q² + linearCoef·Q + constCoef   (Q: 유량 m³/h, H: 양정 m)
     */
    public PumpCurveSampleDto sampleCurve(PumpCurveSampleRequestDto req) {
        int n = (req.getSampleCount() == null) ? 50 : req.getSampleCount();
        validate(req.getMinFlow(), req.getMaxFlow(), n);

        double step = (req.getMaxFlow() - req.getMinFlow()) / (n - 1);
        List<PumpCurvePointDto> points = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            // 마지막 점은 부동소수 누적 오차 없이 정확히 maxFlow 고정
            double flow = (i < n - 1) ? req.getMinFlow() + i * step : req.getMaxFlow();
            double head = req.getQuadCoef() * flow * flow
                        + req.getLinearCoef() * flow
                        + req.getConstCoef();
            points.add(PumpCurvePointDto.of(flow, head));   // 양정(m)
        }
        return PumpCurveSampleDto.of(req, n, points);
    }

    private void validate(Double minFlow, Double maxFlow, int n) {
        if (minFlow == null || maxFlow == null || minFlow >= maxFlow) {
            throw new RestApiException(PumpCurveErrorCode.INVALID_FLOW_RANGE);
        }
        if (n < MIN_SAMPLE || n > MAX_SAMPLE) {
            throw new RestApiException(PumpCurveErrorCode.INVALID_SAMPLE_COUNT);
        }
    }
}
```

> 메서드 본문 ~25줄 — `coding-discipline.md §2.1` 50줄 임계 이내. 면책 조항(§2.5) 불필요.

### 정밀도 정책
- 내부 계산은 `double`. 응답 직렬화 시 자릿수는 프론트 표시 정책에 위임(백엔드가 반올림으로 정밀도 손실 금지 — `api-patterns.md` 직렬화 정책 정렬).
- `BigDecimal` 미사용 근거: 차트 표시용 곡선 좌표(양정 m)는 회계 정밀도가 불필요하며, N×(곱셈 2회) 계산에 `BigDecimal` 은 과한 비용.

---

## 6. 데이터 모델 후보 (안 A — ⚠️ `/dev:analyze` 위임 필수)

> 본 절은 **확정이 아니다.** 신규 비즈니스 도메인 약어·테이블·컬럼·표준 데이터 도메인 등록은 모두 5인 회의(`wtp-glossary-manager` · `wtp-dba-reviewer` 등) + 사용자 승인을 거쳐야 한다. 아래는 회의 입력용 후보일 뿐이다.

### 6.1 레거시 → swtp 컬럼 매핑 후보

| 레거시 (`TB_PUMP_CAL`) | 의미 | swtp 후보 컬럼 | 후보 데이터 도메인 |
|----------------------|------|---------------|------------------|
| `P_ADD_VAL` | 2차항 계수 | `quad_coef` | 정밀도 재검토 (§6.2-3) |
| `P_MUL_VAL` | 1차항 계수 | `linear_coef` | 정밀도 재검토 |
| `P_SQRT_MUL_VAL` | 상수항 | `const_coef` | 정밀도 재검토 |
| `FC_MIN_VAL` | 곡선 유효 최소 유량 | `min_flwrt` (`flwrt` 재사용) | `DOM_QTY_15_4` |
| `FC_MAX_VAL` | 곡선 유효 최대 유량 | `max_flwrt` | `DOM_QTY_15_4` |
| `PUMP_COMB` | 펌프 조합 식별 | (조합 도메인 재설계 결과 의존) | — |

> **DTO 필드 명명**: 응답 표본점은 `head`(양정)·`flwrt`(유량) 표준 단어와 정렬한다. 본 문서 JSON 예시의 `flow`/`head` 키 최종 확정(`flwrt` vs `flow`)은 ANALYZE 에서 결정.

### 6.2 ANALYZE 가 결정해야 할 항목
1. **비즈니스 도메인 약어** — 성능곡선/펌프조합이 `opt`(AI 최적화) 산하인가, `instrument`(펌프) 산하인가, 신규 약어인가. (예: `pump_cmbn` 재도입 여부 — 백지화된 자산이므로 자동 원용 금지)
2. **신규 표준 단어** — `coef`(계수, coefficient), `quad`/`linear`/`const` 등 미등록 단어. `wtp-glossary-manager` 충돌 분류 필요. (`head`·`flwrt` 는 기등록 — 신규 부담 없음)
3. **계수 데이터 도메인** — 2차항 계수는 매우 작은 값(예: −9.8e-6)일 수 있어 `DOM_QTY_15_4`(NUMERIC(15,4))로는 유효숫자 손실 가능. `wtp-dba-reviewer` 2차 승인으로 정밀도 전용 도메인(예: `DOM_COEF_18_10`) 신설 여부 결정.
4. **곡선 원천·Y축 정의** — (a) 제조사 H–Q 특성곡선(양정 직접) vs (b) 현장 토출압력 실측 피팅(압력 → 양정 변환 필요). (b)이면 `H = P/(ρg)` 변환 계수(물 밀도·중력·단위) 와 변환 위치(피팅 단계 vs 조회 단계) 결정.
5. **테이블 suffix** — 계수 저장 테이블이 마스터(`_m`)인가 명세(`_p`)인가. (가동조건 조합식 상수 → 설정값 성격이면 `_p` 후보)
6. **곡선 유효 구간 정책** — 사용자가 `minFlow/maxFlow` 를 `FC_MIN_VAL/FC_MAX_VAL` 밖으로 지정했을 때 외삽(extrapolation) 허용/경고/차단 중 무엇인가 (도메인 안전 — 유효 구간 밖 양정 추정의 신뢰성).

---

## 7. 예외·검증 계약

### ErrorCode enum 후보 — `PumpCurveErrorCode`

```java
@Getter
@RequiredArgsConstructor
public enum PumpCurveErrorCode implements ErrorCode {
    INVALID_FLOW_RANGE(400),      // minFlow >= maxFlow
    INVALID_SAMPLE_COUNT(400),    // N 범위 위반
    CURVE_NOT_FOUND(404);         // (안 A) 조합에 해당하는 계수 없음
    private final int httpStatus;
}
```

> `exception-patterns.md §2` 준수 — `httpStatus(int)` 만 보유, `String message` 필드 금지(자동 차단 훅 대상). 사용자 표기 문자열은 프론트가 `code` 로 매핑.

### 검증 규칙
| 조건 | 결과 |
|------|------|
| `minFlow >= maxFlow` | `INVALID_FLOW_RANGE` (400) |
| `sampleCount < 2` 또는 `> 500` | `INVALID_SAMPLE_COUNT` (400) |
| (안 A) 조합 계수 미존재 | `CURVE_NOT_FOUND` (404) |
| 음수 양정 산출 | **차단하지 않음** — raw 값 반환 + 프론트 표시 정책 위임 (외삽 구간에서 물리적으로 음수가 나올 수 있으며, 이는 §6.2-6 외삽 정책 결정 사항) |

---

## 8. 레거시 대비 개선 요약

| 항목 | 레거시 (`DrvnConfig`) | 신규 설계 |
|------|---------------------|----------|
| Y축 정의 | 압력(`calPressure`) — 성능곡선 명칭과 불일치 | **양정(head, m)** — `rated_head` 와 축 일치 |
| 계수 변수명 | `add/mul/sqrt_mul` (역할 불일치) | `quad/linear/const` (역할 일치) |
| 샘플 간격 | 1 또는 10 고정 | 표본 개수 N 고정, `step=(max−min)/(N−1)` |
| 끝점 정확도 | `i += flusFlow` 누적 → maxFlow 미도달 가능 | 마지막 점 maxFlow 정확 고정 |
| 계산/데이터 결합 | `HashMap<String,Object>` 한 메서드에 혼재 | Service 순수 계산 + (안 A) 조회 어댑터 분리 |
| 타입 안전성 | `(double) map.get("P_ADD_VAL")` 캐스팅 | DTO 강타입 |
| 입력 검증 | 없음 | 구간·N 검증 + ErrorCode |

---

## 9. 미해결 질문 (ANALYZE 입력)

| # | 질문 | 분류 |
|---|------|------|
| Q1 | 계수 공급 방식 — 안 B(무상태) 선출시 후 안 A(저장형) 확장 단계 채택 여부 | 미해결 |
| Q2 | 비즈니스 도메인 약어 — `opt` 산하 / 신규 / `pump_cmbn` 재도입 | 미해결 |
| Q3 | 계수 정밀도 — `DOM_QTY_15_4` 재사용 vs 고정밀 신규 데이터 도메인 | 미해결 (DBA 승인) |
| Q4 | 곡선 원천·Y축 — (a) 제조사 H–Q 양정 직접 vs (b) 현장 토출압력 피팅 → 양정 변환(`H=P/ρg`) | 미해결 (도메인 안전) |
| Q5 | 유효구간 외 유량 지정 시 외삽 정책 (허용/경고/차단) | 미해결 (도메인 안전) |
| Q6 | 응답에 계수 동봉 여부 — 프론트 자체 리샘플 허용 vs 백엔드 단일 SSOT | 가정(동봉 권장) |
| Q7 | N 기본값(50)·상한(500) 적정성 | 가정 |

---

## 10. 다음 단계

1. 본 설계서를 입력으로 `/dev:analyze {슬러그}` 호출 → 5인 회의에서 §6·§9 결정 (특히 Q4 곡선 원천·양정 변환).
2. ANALYZE 산출물(표준 어휘 카탈로그 + 룰 갱신 지시서) 승인 후 `/dev:plan`.
3. 1차 구현은 **안 B(무상태 계산형 Service + Controller + DTO + ErrorCode)** 로 한정 — DB 의존 없이 샘플링 엔진 검증.
4. 계수 저장 테이블 확정 후 안 A 어댑터를 별도 사이클로 증분.

> 본 설계서는 `swtp/backend/docs/` 하네스 산출물이 아니며(바탕화면 임시 메모), 실제 작업 착수 시 `/dev` 워크플로우의 ANALYZE 단계에서 정식 문서로 재작성한다.
