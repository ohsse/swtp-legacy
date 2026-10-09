package com.mindone.editor.pump.dto;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * 펌프조합별 운영 현황 / 전력 원단위 한 행 ({@code TB_PUMP_CAL} 의 {@code C_ORD=1} 행).
 *
 * <p>레거시 EMS 테이블 {@code TB_PUMP_CAL}(펌프가동조건조합식상수)에서 조합 1건을 읽어 담는다. 프론트가 운영 현황 표
 * 외에도 성능곡선(회귀 계수 + 유효 유량 구간)·평가지표 등 다른 화면을 함께 그릴 수 있도록 카탈로그 전체를 노출한다.</p>
 *
 * <h3>조합 식별자</h3>
 * <p>{@code TB_PUMP_CAL} 은 대리키가 없고 <b>({@code PUMP_GRP}, {@code C_IDX})</b> 가 조합을 식별한다. 프론트는 이 두 값을
 * 성능곡선 조회/저장 API 의 경로 변수로 되돌려 보낸다.</p>
 *
 * <h3>한 조합 = 2행 구조</h3>
 * <p>한 조합은 {@code C_ORD} 가 다른 2행으로 구성된다. {@code C_ORD=1} 행이 유량 하한({@code FC_VAL})과 펌프조합
 * 문자열({@code PUMP_COMB})을 갖고, {@code C_ORD=2} 행은 유량 상한({@code FC_VAL})과 <b>가변속 펌프의 목표 주파수
 * 조합</b>({@code PUMP_COMB} 자리를 재사용)을 갖는다. 나머지 컬럼은 두 행이 동일하므로 이 응답은 {@code C_ORD=1}
 * 행을 읽고, 주파수만 {@code C_ORD=2} 에서 가져와 {@code pumpHz} 에 담는다.</p>
 *
 * <h3>회귀 계수 명명</h3>
 * <p>성능곡선 회귀식은 {@code H(Q) = quadCoef·Q² + linearCoef·Q + constCoef} 이다. 레거시 컬럼명(add/mul/sqrt_mul)은
 * 실제 수학적 역할과 일치하지 않아, 코드베이스 공통 규약({@link PumpCurveCoef})대로 역할이 드러나는 이름으로 재명명한다:
 * {@code quadCoef=P_ADD_VAL}, {@code linearCoef=P_MUL_VAL}, {@code constCoef=P_SQRT_MUL_VAL}.</p>
 *
 * <h3>평가지표</h3>
 * <p>{@code avgErrorRate}·{@code powerUnit}·{@code powerCostUnit}·{@code dataCount} 는 성능곡선 저장 시 함께 적재되고,
 * {@code runMinutes} 는 외부 EMS/AI 프로세스가 적재한다. 모두 미적재 시 {@code null} 이다.</p>
 */
@Schema(description = "펌프조합별 운영 현황 (TB_PUMP_CAL 의 C_ORD=1 행)")
public record PumpCombStatResponse(

        @Schema(description = "펌프그룹 (TB_PUMP_CAL.PUMP_GRP) — 조합 식별자의 앞부분", example = "1")
        Integer pumpGrp,

        @Schema(description = "조합인덱스 (TB_PUMP_CAL.C_IDX) — 조합 식별자의 뒷부분", example = "12")
        Integer combIdx,

        @Schema(description = "펌프조합 (펌프IDX를 ','로 이어붙인 문자열)", example = "2,3")
        String pumpComb,

        @Schema(description = "운영대수 (TB_PUMP_CAL.PUMP_COUNT, 가중값 가능)", example = "3.5")
        Double pumpCount,

        @Schema(description = "우선순위 (TB_PUMP_CAL.PUMP_PRIORITY, 미지정 시 null)", example = "1")
        Integer pumpPriority,

        @Schema(description = "성능곡선 2차항 계수 a (TB_PUMP_CAL.P_ADD_VAL)", example = "-0.00012")
        Double quadCoef,

        @Schema(description = "성능곡선 1차항 계수 b (TB_PUMP_CAL.P_MUL_VAL)", example = "0.85")
        Double linearCoef,

        @Schema(description = "성능곡선 상수항 c (TB_PUMP_CAL.P_SQRT_MUL_VAL)", example = "120.0")
        Double constCoef,

        @Schema(description = "유효 유량 구간 최소 (m³/h, TB_PUMP_CAL.FC_MIN_VAL)", example = "18000.0")
        Double fcMin,

        @Schema(description = "유효 유량 구간 최대 (m³/h, TB_PUMP_CAL.FC_MAX_VAL)", example = "20500.0")
        Double fcMax,

        @Schema(description = "배율및추가연산자 (TB_PUMP_CAL.CS_OP, 압력 계산식 미사용 레거시)", example = "*")
        String csOp,

        @Schema(description = "배율및제곱연산자 (TB_PUMP_CAL.SS_OP, 압력 계산식 미사용 레거시)", example = "*")
        String ssOp,

        @Schema(description = "운영건수(분) (TB_PUMP_CAL.run_minutes, 미적재 시 null)", example = "556")
        Long runMinutes,

        @Schema(description = "데이터수 — 회귀에 쓰인 실측 표본 수 (TB_PUMP_CAL.data_count, 미적재 시 null)", example = "9132")
        Long dataCount,

        @Schema(description = "평균오차(율) (TB_PUMP_CAL.avg_error_rate, 미적재 시 null)", example = "0.3755")
        Double avgErrorRate,

        @Schema(description = "전력 원단위 (TB_PUMP_CAL.power_unit, 미적재 시 null)", example = "0.1796")
        Double powerUnit,

        @Schema(description = "전력비 원단위 (TB_PUMP_CAL.power_cost_unit, 미적재 시 null)", example = "30.5442")
        Double powerCostUnit,

        @Schema(
                description = "목표 주파수 조합 (가변속 펌프만, 펌프IDX:Hz 콤마 문자열). "
                        + "TB_PUMP_CAL 의 C_ORD=2 행 주파수 조합을 펌프번호와 짝지어 만든 값이며, "
                        + "성능곡선 갱신/추출 호출 시 pumpHz 파라미터로 그대로 되돌려 보내면 된다. "
                        + "주파수 미입력 조합이거나 가변속 펌프가 없으면 null.",
                example = "2:27,3:29")
        String pumpHz
) {
}
