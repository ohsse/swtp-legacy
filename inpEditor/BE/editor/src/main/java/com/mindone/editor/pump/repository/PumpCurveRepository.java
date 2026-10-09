package com.mindone.editor.pump.repository;

import com.mindone.editor.pump.dto.PumpCurveCoef;
import com.mindone.editor.pump.dto.PumpCurveSaveRequest;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.Tuple;
import org.hibernate.query.TypedParameterValue;
import org.hibernate.type.StandardBasicTypes;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.Optional;

/**
 * 펌프 성능곡선 계수 조회/저장 저장소 (레거시 EMS 공유 테이블 {@code TB_PUMP_CAL} 직접 접근).
 *
 * <p>{@code TB_PUMP_CAL} 은 Flyway/JPA 엔티티 관리 대상이 아닌 공유 EMS 테이블이라
 * ({@code ddl-auto: validate}) {@link EntityManager} 네이티브 쿼리로 접근한다
 * ({@link PumpCombStatRepository} 와 동일한 방침). 군산 운영은 Linux MariaDB 라 테이블명 대소문자를 구분하므로
 * {@code TB_PUMP_CAL} 대문자 표기를 유지해야 한다.</p>
 *
 * <h3>한 조합 = 2행 구조</h3>
 * <p>한 조합({@code PUMP_GRP}, {@code C_IDX})은 {@code C_ORD} 가 다른 2행으로 구성된다.</p>
 * <table border="1">
 *   <caption>C_ORD 별 행 구성</caption>
 *   <tr><th>컬럼</th><th>{@code C_ORD=1} (최소)</th><th>{@code C_ORD=2} (최대)</th></tr>
 *   <tr><td>{@code FC_VAL}</td><td>{@code FC_MIN_VAL} 과 같은 값</td><td>{@code FC_MAX_VAL} 과 같은 값</td></tr>
 *   <tr><td>{@code PUMP_COMB}</td><td>조합식(예: {@code "2,3"})</td><td>{@code ''}(빈 문자열, 원칙)</td></tr>
 *   <tr><td>그 외 전 컬럼</td><td colspan="2">두 행 동일</td></tr>
 * </table>
 *
 * <p>따라서 <b>조회는 {@code C_ORD='1'} 한 행</b>만 읽고, <b>저장은 두 행을 함께 갱신</b>한다. 유량 구간이
 * {@code FC_VAL}(레거시 EMS 자율제어 {@code DrvnConfig} 가 읽음)과 {@code FC_MIN_VAL}/{@code FC_MAX_VAL}
 * (EPA 파이썬이 읽음) 두 곳에 중복 보관되므로, 한쪽만 갱신하면 두 소비자가 서로 다른 유량 구간으로 동작한다.</p>
 *
 * <p><b>{@code PUMP_COMB} 은 읽기 전용이다.</b> 이 애플리케이션은 어떤 기능에서도 조합식을 쓰지 않는다
 * ({@link #updateCurve} SET 절에서 제외). 조합의 생성·구성 변경은 EMS 쪽 관리 기능의 책임이다.</p>
 */
@Repository
public class PumpCurveRepository {

    @PersistenceContext
    private EntityManager em;

    /**
     * 펌프조합 1건의 성능곡선 계수 + 유효 유량 구간 조회 SQL.
     *
     * <p>파라미터: {@code :pumpGrp} 펌프그룹, {@code :combIdx} 조합인덱스. 계수는 두 행이 동일하므로
     * 펌프조합 문자열이 살아있는 {@code C_ORD='1'} 행을 읽는다.</p>
     */
    private static final String CURVE_COEF_SQL = """
            SELECT PUMP_GRP          AS pump_grp,
                   C_IDX             AS comb_idx,
                   PUMP_COMB         AS pump_comb,
                   P_ADD_VAL         AS quad_coef,
                   P_MUL_VAL         AS linear_coef,
                   P_SQRT_MUL_VAL    AS const_coef,
                   FC_MIN_VAL        AS fc_min,
                   FC_MAX_VAL        AS fc_max
            FROM TB_PUMP_CAL
            WHERE PUMP_GRP = :pumpGrp
              AND C_IDX    = :combIdx
              AND C_ORD    = '1'
            """;

    /**
     * 펌프조합 1건의 성능곡선 계수·유량 구간·평가지표 저장(UPDATE) SQL — {@code C_ORD=1·2} 두 행을 함께 갱신한다.
     *
     * <p>계수·유량 구간·평가지표는 조합 단위 값이라 두 행에 동일하게 쓰고, {@code FC_VAL} 만 행별로 갈라
     * {@code C_ORD=1} 에는 하한을, {@code C_ORD=2} 에는 상한을 넣는다. {@code FC_VAL} 이 {@code NOT NULL} 이지만
     * WHERE 절이 {@code C_ORD IN ('1','2')} 로 제한하므로 CASE 가 NULL 을 만들 일은 없다.</p>
     *
     * <p><b>{@code PUMP_COMB} 은 절대 쓰지 않는다.</b> 조합식은 조합의 정체성 자체이며 EMS 자율제어
     * ({@code DrvnConfig})·EPA 파이썬({@code epa_models.fetch_fc_range_by_comb})이 조합을 식별하는 키다.
     * 성능곡선 저장은 <b>기존 조합의 계수·유량 구간·지표만</b> 갱신하는 기능이므로, 이 애플리케이션 어느
     * 경로에서도 {@code PUMP_COMB} 값이 바뀌는 상황이 있어서는 안 된다. 따라서 SET 절에서 이 컬럼을 제외한다
     * (레거시 데이터의 {@code C_ORD=2} 행 잔재 값 정리는 애플리케이션이 아니라 DBA 일회성 스크립트
     * {@code doc/sql/TB_PUMP_CAL_normalize_cord2_pump_comb.sql} 의 몫이다).</p>
     *
     * <p>지표 5종 컬럼({@code avg_error_rate}/{@code power_unit}/{@code power_cost_unit}/{@code data_count}/
     * {@code run_minutes})은 {@code doc/sql/V_TB_PUMP_CAL_add_metric_columns.sql} 로 별도 추가한 컬럼이다
     * (Flyway 미관리, 수작업 DDL). {@code run_minutes} 는 외부 프로세스가 적재하므로 여기서 쓰지 않는다.</p>
     */
    private static final String UPDATE_CURVE_SQL = """
            UPDATE TB_PUMP_CAL
            SET P_ADD_VAL       = :quadCoef,
                P_MUL_VAL       = :linearCoef,
                P_SQRT_MUL_VAL  = :constCoef,
                FC_MIN_VAL      = :fcMin,
                FC_MAX_VAL      = :fcMax,
                FC_VAL          = CASE C_ORD WHEN 1 THEN :fcMin WHEN 2 THEN :fcMax END,
                PUMP_PRIORITY   = :priority,
                avg_error_rate  = :avgErrorRate,
                power_unit      = :powerUnit,
                power_cost_unit = :powerCostUnit,
                data_count      = :dataCount
            WHERE PUMP_GRP = :pumpGrp
              AND C_IDX    = :combIdx
              AND C_ORD IN ('1','2')
            """;

    /**
     * 펌프조합 식별자로 성능곡선 계수를 조회한다.
     *
     * @param pumpGrp 펌프그룹 ({@code TB_PUMP_CAL.PUMP_GRP})
     * @param combIdx 조합인덱스 ({@code TB_PUMP_CAL.C_IDX})
     * @return 계수 + 유효 유량 구간 (없으면 {@link Optional#empty()})
     */
    public Optional<PumpCurveCoef> findCoef(Integer pumpGrp, Integer combIdx) {
        return em.createNativeQuery(CURVE_COEF_SQL, Tuple.class)
                .setParameter("pumpGrp", pumpGrp)
                .setParameter("combIdx", combIdx)
                .getResultList()
                .stream()
                .findFirst()
                .map(row -> toCoef((Tuple) row));
    }

    /**
     * 펌프조합 1건의 성능곡선 회귀 계수·유효 유량 구간·평가지표를 저장(UPDATE)한다.
     *
     * <p>회귀 계수·상수(quadCoef/linearCoef/constCoef)는 정밀도 보존을 위해 {@link BigDecimal} 로 받으며
     * ({@link PumpCurveSaveRequest}), nullable 참조타입이라 {@link TypedParameterValue} 로 타입을 명시해
     * 바인딩한다(네이티브 쿼리의 null 타입 추론 실패 방지). 매핑 대상 컬럼은 {@code DOUBLE} 이라 저장 시
     * double 로 좁혀지지만 계수 원천이 이미 {@code float64} 라 저장 정보 손실은 없다. nullable 정수
     * 컬럼(PUMP_PRIORITY/data_count)도 같은 이유로 감싸며, 나머지 지표는 원시 {@code double} 이라 항상 값이 있다.</p>
     *
     * @param pumpGrp 펌프그룹 ({@code TB_PUMP_CAL.PUMP_GRP})
     * @param combIdx 조합인덱스 ({@code TB_PUMP_CAL.C_IDX})
     * @param request 저장할 계수·유량 구간·평가지표(passthrough)
     * @return 갱신된 행 수(2행 구조가 온전하면 2, 대상 조합이 없으면 0)
     */
    public int updateCurve(Integer pumpGrp, Integer combIdx, PumpCurveSaveRequest request) {
        return em.createNativeQuery(UPDATE_CURVE_SQL)
                .setParameter("quadCoef", new TypedParameterValue<>(StandardBasicTypes.BIG_DECIMAL, request.quadCoef()))
                .setParameter("linearCoef", new TypedParameterValue<>(StandardBasicTypes.BIG_DECIMAL, request.linearCoef()))
                .setParameter("constCoef", new TypedParameterValue<>(StandardBasicTypes.BIG_DECIMAL, request.constCoef()))
                .setParameter("fcMin", request.fcMin())
                .setParameter("fcMax", request.fcMax())
                .setParameter("avgErrorRate", request.avgErrorRate())
                .setParameter("powerUnit", request.powerUnit())
                .setParameter("powerCostUnit", request.powerCostUnit())
                .setParameter("priority", new TypedParameterValue<>(StandardBasicTypes.INTEGER, request.priority()))
                .setParameter("dataCount", new TypedParameterValue<>(StandardBasicTypes.INTEGER, request.dataCount()))
                .setParameter("pumpGrp", pumpGrp)
                .setParameter("combIdx", combIdx)
                .executeUpdate();
    }

    /** Tuple → 계수 DTO 매핑(숫자 컬럼은 DB 구현별 타입 차이를 흡수하기 위해 {@link Number} 로 변환). */
    private static PumpCurveCoef toCoef(Tuple t) {
        return new PumpCurveCoef(
                toInteger(t.get("pump_grp")),
                toInteger(t.get("comb_idx")),
                t.get("pump_comb", String.class),
                toDouble(t.get("quad_coef")),
                toDouble(t.get("linear_coef")),
                toDouble(t.get("const_coef")),
                toDouble(t.get("fc_min")),
                toDouble(t.get("fc_max"))
        );
    }

    /** 숫자형 Tuple 값을 double 로 변환(null 은 0.0). */
    private static double toDouble(Object value) {
        return (value == null) ? 0.0 : ((Number) value).doubleValue();
    }

    /** 숫자형 Tuple 값을 Integer 로 변환(null 보존). */
    private static Integer toInteger(Object value) {
        return (value == null) ? null : ((Number) value).intValue();
    }
}
