package com.mindone.editor.pump.repository;

import com.mindone.editor.pump.dto.PumpCombStatResponse;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.Tuple;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 펌프조합별 운영 현황 / 전력 원단위 조회 저장소.
 *
 * <p>대상 테이블은 Flyway/JPA 엔티티 관리 대상이 아닌 <b>레거시 EMS 공유 테이블 {@code TB_PUMP_CAL}</b> 이라,
 * 엔티티 매핑({@code ddl-auto: validate}) 대신 {@link EntityManager} 네이티브 쿼리로 조회한다.</p>
 *
 * <p><b>테이블명 대소문자 주의</b>: 군산 운영은 Linux MariaDB({@code lower_case_table_names=0})라 테이블명이
 * 대소문자를 구분한다. 반드시 {@code TB_PUMP_CAL} 대문자로 표기해야 한다(컬럼명은 어떤 플랫폼에서도 구분되지 않음).</p>
 *
 * <p>운영건수(분)·전력원단위 등 통계값은 조회 시점에 {@code TB_RAWDATA} 를 집계하지 않고
 * (과거에는 기간 집계로 무거웠음) {@code TB_PUMP_CAL} 에 저장된 값을 단순 SELECT 해 표출한다.</p>
 *
 * <p><b>주파수 조합</b>: 같은 조합의 {@code C_ORD=2} 행 {@code PUMP_COMB} 은 가변속 펌프의 목표 주파수 목록이며
 * ({@code TB_CTR_PRF_PUMPMST_INF.PUMP_TYP} 와 짝지어 읽는다), 성능곡선 산출 시 파이썬에 함께 넘겨 해당 주파수로
 * 운전한 구간만 회귀에 쓰게 한다. 이 값은 <b>지우면 안 된다</b> — 조립 규칙과 근거는 {@code buildPumpHz} 참조.</p>
 */
@Repository
public class PumpCombStatRepository {

    @PersistenceContext
    private EntityManager em;

    /**
     * 펌프조합별 운영 현황 조회 SQL.
     *
     * <p>한 조합(PUMP_GRP, C_IDX)은 {@code C_ORD} 가 다른 2행으로 구성되며, {@code C_ORD=1} 행이 펌프조합 문자열과
     * 유량 하한을, {@code C_ORD=2} 행이 유량 상한을 갖는다. 나머지 컬럼은 두 행이 동일하므로 <b>{@code C_ORD='1'}</b>
     * 행만 읽어 조합 1건 = 1행으로 만든다. 사용 중인 조합만 표출하도록 {@code USE_YN = 1} 도 함께 건다
     * (레거시 EMS {@code selectPumpCombCal} 과 동일한 기준).</p>
     *
     * <p>다만 {@code C_ORD=2} 행의 {@code PUMP_COMB} 은 <b>가변속 펌프의 목표 주파수 조합</b>이므로 함께 읽는다
     * ({@code freq_comb}). 상세는 {@link #buildPumpHz} 참조.</p>
     *
     * <p>프론트가 운영 현황 외에 성능곡선·평가지표 등 다른 화면도 그릴 수 있도록 <b>전체 컬럼</b>을 그대로 표출한다.
     * 회귀 계수는 코드베이스 규약대로 별칭을 quad/linear/const 로 둔다.</p>
     */
    private static final String COMB_STAT_SQL = """
            SELECT
                c1.PUMP_GRP        AS pump_grp,
                c1.C_IDX           AS comb_idx,
                c1.PUMP_COMB       AS pump_comb,
                c1.PUMP_COUNT      AS pump_count,
                c1.PUMP_PRIORITY   AS pump_priority,
                c1.P_ADD_VAL       AS quad_coef,
                c1.P_MUL_VAL       AS linear_coef,
                c1.P_SQRT_MUL_VAL  AS const_coef,
                c1.FC_MIN_VAL      AS fc_min,
                c1.FC_MAX_VAL      AS fc_max,
                c1.CS_OP           AS cs_op,
                c1.SS_OP           AS ss_op,
                c1.run_minutes     AS run_minutes,
                c1.data_count      AS data_count,
                c1.avg_error_rate  AS avg_error_rate,
                c1.power_unit      AS power_unit,
                c1.power_cost_unit AS power_cost_unit,
                (SELECT c2.PUMP_COMB FROM TB_PUMP_CAL c2
                  WHERE c2.PUMP_GRP = c1.PUMP_GRP
                    AND c2.C_IDX = c1.C_IDX
                    AND c2.C_ORD = '2') AS freq_comb
            FROM TB_PUMP_CAL c1
            WHERE c1.C_ORD = '1'
              AND c1.USE_YN = 1
            ORDER BY c1.PUMP_COUNT, c1.PUMP_COMB, c1.PUMP_GRP, c1.C_IDX
            """;

    /**
     * 펌프별 구동 방식 조회 SQL — 주파수 값을 펌프번호에 붙이는 데 쓴다.
     *
     * <p>{@code PUMP_TYP} 은 1=정속, 2=가변속이다(레거시 EMS {@code DrvnConfig}·{@code DrvnService} 공통 규약).</p>
     */
    private static final String PUMP_TYPE_SQL = """
            SELECT PUMP_IDX AS pump_idx, PUMP_TYP AS pump_typ
            FROM TB_CTR_PRF_PUMPMST_INF
            WHERE USE_YN = 1
            """;

    /** 가변속 펌프 구분값 ({@code TB_CTR_PRF_PUMPMST_INF.PUMP_TYP}). */
    private static final int PUMP_TYP_VARIABLE_SPEED = 2;

    /**
     * 펌프조합별 운영 현황 / 전력 원단위를 조회한다.
     *
     * @return 조합별 행 목록 (운영대수→조합 순, 사용 중인 조합 전체)
     */
    public List<PumpCombStatResponse> findCombStats() {
        Map<Integer, Integer> pumpTypes = findPumpTypes();

        List<Tuple> rows = em.createNativeQuery(COMB_STAT_SQL, Tuple.class)
                .getResultList();

        return rows.stream().map(row -> toResponse(row, pumpTypes)).toList();
    }

    /** 펌프IDX → 구동 방식(PUMP_TYP) 사전. 조합마다 다시 조회하지 않도록 한 번만 읽는다. */
    private Map<Integer, Integer> findPumpTypes() {
        List<Tuple> rows = em.createNativeQuery(PUMP_TYPE_SQL, Tuple.class)
                .getResultList();

        Map<Integer, Integer> types = new LinkedHashMap<>();
        for (Tuple t : rows) {
            Integer idx = toInteger(t.get("pump_idx"));
            Integer typ = toInteger(t.get("pump_typ"));
            if (idx != null) {
                types.put(idx, typ);
            }
        }
        return types;
    }

    /**
     * {@code C_ORD=2} 행의 주파수 조합을 파이썬이 받는 {@code 펌프번호:주파수} 형식으로 조립한다.
     *
     * <p><b>왜 그냥 넘기면 안 되는가</b>: {@code C_ORD=2} 의 {@code PUMP_COMB} 은 조합에 든 모든 펌프가 아니라
     * <b>가변속({@code PUMP_TYP=2}) 펌프에만 순서대로</b> 대응하는 주파수 목록이다. 정속 펌프는 자리를 차지하지 않는다.
     * 예를 들어 조합이 {@code "1,2,3"} 이고 2·3번만 가변속이며 주파수 조합이 {@code "27,29"} 면
     * 2번=27Hz, 3번=29Hz 다. 이 규칙의 근거는 레거시 EMS {@code DrvnService.getPumpCombCal} 이다.</p>
     *
     * <p><b>방어</b>: 주파수 조합은 미입력 시 빈 문자열이고, 값이 펌프 수보다 모자라거나 숫자가 아닐 수 있다
     * (레거시도 같은 상황을 0=미지정으로 흘려보낸다). 그런 자리는 건너뛰며, 결과가 하나도 없으면 {@code null} 을
     * 돌려 파이썬이 주파수 조건 없이 분석하게 한다 — 주파수 미입력은 오류가 아니라 정상 상태다.</p>
     *
     * @param pumpComb  {@code C_ORD=1} 의 펌프조합(펌프IDX 콤마 문자열)
     * @param freqComb  {@code C_ORD=2} 의 주파수 조합(가변속 펌프 순서대로)
     * @param pumpTypes 펌프IDX → PUMP_TYP 사전
     * @return {@code "2:27,3:29"} 형식 문자열(해당 없으면 {@code null})
     */
    // 매핑이 한 칸만 밀려도 엉뚱한 펌프의 주파수로 회귀하게 되므로 단위 테스트로 고정한다
    // (PumpCombStatFreqTest). 그래서 private 이 아니라 패키지 공개다.
    static String buildPumpHz(String pumpComb, String freqComb, Map<Integer, Integer> pumpTypes) {
        if (pumpComb == null || pumpComb.isBlank() || freqComb == null || freqComb.isBlank()) {
            return null;
        }

        String[] freqValues = freqComb.split(",");
        List<String> pairs = new ArrayList<>();
        int freqPos = 0;

        for (String part : pumpComb.split(",")) {
            String idxText = part.trim();
            if (idxText.isEmpty()) {
                continue;
            }
            Integer pumpIdx;
            try {
                pumpIdx = Integer.valueOf(idxText);
            } catch (NumberFormatException e) {
                continue;   // 조합 문자열에 숫자가 아닌 잔재가 있어도 표출 자체는 계속한다
            }

            Integer typ = pumpTypes.get(pumpIdx);
            if (typ == null || typ != PUMP_TYP_VARIABLE_SPEED) {
                continue;   // 정속 펌프는 주파수 목록에서 자리를 차지하지 않는다
            }

            // 가변속 펌프 수보다 주파수 값이 모자라면 나머지는 미지정으로 둔다
            String hzText = (freqPos < freqValues.length) ? freqValues[freqPos].trim() : "";
            freqPos++;

            Double hz = parseHzOrNull(hzText);
            if (hz != null) {
                pairs.add(pumpIdx + ":" + trimTrailingZero(hz));
            }
        }

        return pairs.isEmpty() ? null : String.join(",", pairs);
    }

    /** 주파수 문자열을 양수 실수로 읽는다. 빈 값·0·숫자 아님은 모두 미지정({@code null})으로 본다. */
    private static Double parseHzOrNull(String text) {
        if (text == null || text.isBlank()) {
            return null;
        }
        try {
            double hz = Double.parseDouble(text);
            return (hz > 0) ? hz : null;
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /** 45.0 → "45" 처럼 불필요한 소수점을 떼어 파이썬에 보낼 문자열을 줄인다(45.5 는 그대로). */
    private static String trimTrailingZero(double hz) {
        return (hz == Math.rint(hz)) ? String.valueOf((long) hz) : String.valueOf(hz);
    }

    /** Tuple → 응답 DTO 매핑(숫자 컬럼은 DB 구현별 타입 차이를 흡수하기 위해 {@link Number} 로 변환). */
    private static PumpCombStatResponse toResponse(Tuple t, Map<Integer, Integer> pumpTypes) {
        String pumpComb = t.get("pump_comb", String.class);
        return new PumpCombStatResponse(
                toInteger(t.get("pump_grp")),
                toInteger(t.get("comb_idx")),
                pumpComb,
                toDouble(t.get("pump_count")),
                toInteger(t.get("pump_priority")),
                toDouble(t.get("quad_coef")),
                toDouble(t.get("linear_coef")),
                toDouble(t.get("const_coef")),
                toDouble(t.get("fc_min")),
                toDouble(t.get("fc_max")),
                t.get("cs_op", String.class),
                t.get("ss_op", String.class),
                toLong(t.get("run_minutes")),
                toLong(t.get("data_count")),
                toDouble(t.get("avg_error_rate")),
                toDouble(t.get("power_unit")),
                toDouble(t.get("power_cost_unit")),
                buildPumpHz(pumpComb, t.get("freq_comb", String.class), pumpTypes)
        );
    }

    /** 숫자형 Tuple 값을 Double 로 변환(null 보존). */
    private static Double toDouble(Object value) {
        return (value == null) ? null : ((Number) value).doubleValue();
    }

    /** 숫자형 Tuple 값을 Long 으로 변환(null 보존). */
    private static Long toLong(Object value) {
        return (value == null) ? null : ((Number) value).longValue();
    }

    /** 숫자형 Tuple 값을 Integer 로 변환(null 보존). */
    private static Integer toInteger(Object value) {
        return (value == null) ? null : ((Number) value).intValue();
    }
}
