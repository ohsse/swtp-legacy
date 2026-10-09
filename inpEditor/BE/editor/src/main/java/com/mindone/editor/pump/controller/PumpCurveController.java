package com.mindone.editor.pump.controller;

import com.mindone.editor.common.controller.CommonController;
import com.mindone.editor.common.response.ResponseObject;
import com.mindone.editor.pump.dto.PumpCurveManualRequest;
import com.mindone.editor.pump.dto.PumpCurveRenewResponse;
import com.mindone.editor.pump.dto.PumpCurveResponse;
import com.mindone.editor.pump.dto.PumpCurveSaveRequest;
import com.mindone.editor.pump.service.PumpCurveManualService;
import com.mindone.editor.pump.service.PumpCurveRenewService;
import com.mindone.editor.pump.service.PumpCurveSaveService;
import com.mindone.editor.pump.service.PumpCurveService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;

/**
 * 펌프 성능곡선 표본 조회 명세.
 *
 * <p>{@code TB_PUMP_CAL} 의 한 펌프조합 회귀 계수(P_ADD_VAL/P_MUL_VAL/P_SQRT_MUL_VAL)를 기반으로,
 * 유량 구간 {@code [minFlow, maxFlow]} 에 대해 N 개의 (유량, 양정) 표본점을 산출해 프론트 차트 데이터로 제공한다.
 * 성능곡선의 표준 축은 X축 유량(Q, m³/h)·Y축 양정(H, m) 이며,
 * 회귀식은 {@code H(Q) = P_ADD_VAL·Q² + P_MUL_VAL·Q + P_SQRT_MUL_VAL} (레거시 {@code DrvnConfig.pressureCalValue} 의 2차식 구조 계승, Y축만 양정으로 정정).</p>
 *
 * <p>{@code TB_PUMP_CAL} 은 대리키가 없어 조합을 <b>({@code PUMP_GRP}, {@code C_IDX})</b> 로 식별한다.
 * 따라서 모든 엔드포인트가 두 값을 경로 변수로 받는다.</p>
 */
@RestController
@RequiredArgsConstructor
@Tag(name = "펌프 성능곡선", description = "펌프조합 성능곡선 표본 조회")
public class PumpCurveController extends CommonController {

    private final PumpCurveService pumpCurveService;
    private final PumpCurveRenewService pumpCurveRenewService;
    private final PumpCurveManualService pumpCurveManualService;
    private final PumpCurveSaveService pumpCurveSaveService;

    @Operation(
            summary = "펌프조합 성능곡선 표본 조회",
            description = "TB_PUMP_CAL 의 펌프조합(PUMP_GRP, C_IDX) 회귀 계수로 성능곡선을 그릴 (유량 Q, 양정 H) 표본점을 반환한다. "
                    + "응답은 조회한 유량 구간(minFlow=FC_MIN_VAL, maxFlow=FC_MAX_VAL)과 그 구간을 균등 분할한 표본점 목록(data)으로 구성된다. "
                    + "표본 개수는 10000개로 고정한다. "
                    + "회귀식: H(Q) = quadCoef·Q² + linearCoef·Q + constCoef (X축 유량 m³/h, Y축 양정 m)."
    )
    @ApiResponses(value = {
            @ApiResponse(description = "성공", responseCode = "200")
    })
    @GetMapping(value = "/pump-combinations/{pumpGrp}/{combIdx}/performance-curve", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<ResponseObject<PumpCurveResponse>> getPerformanceCurve(
            @Parameter(description = "펌프그룹 (TB_PUMP_CAL.PUMP_GRP)", example = "1")
            @PathVariable("pumpGrp") Integer pumpGrp,
            @Parameter(description = "조합인덱스 (TB_PUMP_CAL.C_IDX)", example = "12")
            @PathVariable("combIdx") Integer combIdx) {
        return getResponseEntity(pumpCurveService.sampleCurve(pumpGrp, combIdx));
    }

    @Operation(
            summary = "펌프조합 성능곡선 갱신",
            description = "조회기간(from~to) 동안 펌프조합이 실제 운전한 실측 곡선(currCurve)과, 같은 기간 실측값으로 "
                    + "파이썬이 새로 회귀분석한 계수로 그린 새 곡선(newCurve)을 함께 반환한다. "
                    + "실측 곡선은 TB_RAWDATA 의 분별 (유량 합, 양정)이고, 새 곡선은 회귀식 H(Q)=a·Q²+b·Q+c "
                    + "(a=P_ADD_VAL, b=P_MUL_VAL, c=P_SQRT_MUL_VAL)를 실측 유량에 1:1 적용한 (유량, 회귀 양정)이다. "
                    + "함께 평균오차(avgError)·전력 원단위(powerUnit)·전력비 원단위(powerCostUnit)·우선순위(priority)를 담는다. "
                    + "from/to 형식은 yyyy-MM-dd(날짜 단위)이며 미지정 시 오늘 하루. 조회/계산만 하고 TB_PUMP_CAL 은 갱신하지 않는다. "
                    + "pumpHz 를 주면 그 목표 주파수로 운전한 구간만 회귀에 쓴다(가변속 펌프 현장). "
                    + "운영 현황 조회(/pump-combinations/operation-stats)가 내려준 pumpHz 를 그대로 되돌려 보내면 된다."
    )
    @ApiResponses(value = {
            @ApiResponse(description = "성공", responseCode = "200")
    })
    @GetMapping(value = "/pump-combinations/{pumpGrp}/{combIdx}/performance-curve/renewal", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<ResponseObject<PumpCurveRenewResponse>> renewPerformanceCurve(
            @Parameter(description = "펌프그룹 (TB_PUMP_CAL.PUMP_GRP)", example = "1")
            @PathVariable("pumpGrp") Integer pumpGrp,
            @Parameter(description = "조합인덱스 (TB_PUMP_CAL.C_IDX)", example = "1")
            @PathVariable("combIdx") Integer combIdx,
            @Parameter(description = "조회 시작일 (yyyy-MM-dd, 미지정 시 오늘) — 그날 00:00:00 부터", example = "2026-04-09")
            @RequestParam(value = "from", required = false)
            @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate from,
            @Parameter(description = "조회 종료일 (yyyy-MM-dd, 미지정 시 오늘) — 그날 23:59:59 까지", example = "2026-04-09")
            @RequestParam(value = "to", required = false)
            @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate to,
            @Parameter(description = "목표 주파수 조합 (펌프IDX:Hz 콤마 문자열, 미지정 시 주파수 조건 없이 회귀)", example = "2:27,3:29")
            @RequestParam(value = "pumpHz", required = false) String pumpHz) {
        return getResponseEntity(pumpCurveRenewService.renew(pumpGrp, combIdx, from, to, pumpHz));
    }

    @Operation(
            summary = "펌프조합 성능곡선 추출 (수동 입력 점 → 회귀)",
            description = "사용자가 차트에 직접 입력한 (유량, 양정) 점(points)을 회귀 입력으로 파이썬에 전달해 새 회귀 계수를 받고, "
                    + "조회기간(from~to) 동안의 실측 유량에 그 회귀식을 적용한 새 곡선(newCurve)을 반환한다. "
                    + "실측값만으로 회귀하는 갱신(renewal)과 달리 회귀 입력이 사용자 입력 점이라는 점만 다르다. "
                    + "응답은 갱신과 동일한 구조로, 실측 곡선(currCurve)·새 회귀 곡선(newCurve)과 함께 "
                    + "평균오차(avgError)·전력 원단위(powerUnit)·전력비 원단위(powerCostUnit)·우선순위(priority)를 담는다. "
                    + "새 곡선은 회귀식 H(Q)=a·Q²+b·Q+c (a=P_ADD_VAL, b=P_MUL_VAL, c=P_SQRT_MUL_VAL)를 실측 유량에 1:1 적용한다. "
                    + "from/to 는 본문에 담되 yyyy-MM-dd(날짜 단위)이며 미지정 시 오늘 하루. 조회/계산만 하고 TB_PUMP_CAL 은 갱신하지 않는다. "
                    + "갱신(renewal)과 마찬가지로 본문 pumpHz 를 주면 그 목표 주파수로 운전한 구간만 지표 계산에 쓴다."
    )
    @ApiResponses(value = {
            @ApiResponse(description = "성공", responseCode = "200")
    })
    @PostMapping(value = "/pump-combinations/{pumpGrp}/{combIdx}/performance-curve/extraction",
            consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<ResponseObject<PumpCurveRenewResponse>> extractPerformanceCurve(
            @Parameter(description = "펌프그룹 (TB_PUMP_CAL.PUMP_GRP)", example = "1")
            @PathVariable("pumpGrp") Integer pumpGrp,
            @Parameter(description = "조합인덱스 (TB_PUMP_CAL.C_IDX)", example = "1")
            @PathVariable("combIdx") Integer combIdx,
            @RequestBody PumpCurveManualRequest request) {
        return getResponseEntity(pumpCurveManualService.extract(pumpGrp, combIdx, request));
    }

    @Operation(
            summary = "펌프조합 성능곡선 저장",
            description = "갱신(renewal)·추출(extraction) 미리보기로 검토한 성능곡선 회귀 계수(quadCoef=P_ADD_VAL, "
                    + "linearCoef=P_MUL_VAL, constCoef=P_SQRT_MUL_VAL)와 유효 유량 구간(fcMin=FC_MIN_VAL, fcMax=FC_MAX_VAL), "
                    + "평가지표(평균오차·전력원단위·전력비원단위·우선순위·데이터수)를 TB_PUMP_CAL 의 해당 조합(PUMP_GRP, C_IDX)에 저장한다. "
                    + "한 조합은 C_ORD=1(유량 하한)·C_ORD=2(유량 상한) 두 행으로 구성되므로 두 행을 함께 갱신하며, "
                    + "FC_VAL 은 C_ORD=1 에 fcMin, C_ORD=2 에 fcMax 가 들어간다. PUMP_COMB 은 갱신하지 않는다. "
                    + "프론트가 보낸 값을 그대로 반영하며(passthrough) 저장 시점에 파이썬을 재호출하지 않는다. "
                    + "주의: TB_PUMP_CAL 은 EMS 자율제어·EPA 파이썬이 함께 읽는 공유 운영 테이블이며, "
                    + "이 프로젝트에서 그 테이블에 쓰는 유일한 엔드포인트다(그 외는 모두 조회/계산만 한다). "
                    + "응답 data 는 저장된 combIdx 다. 유량 구간이 뒤집히면(fcMin>=fcMax) INVALID_FLOW_RANGE, "
                    + "대상 조합이 없으면 CURVE_NOT_FOUND 로 실패한다."
    )
    @ApiResponses(value = {
            @ApiResponse(description = "성공", responseCode = "200")
    })
    @PutMapping(value = "/pump-combinations/{pumpGrp}/{combIdx}/performance-curve",
            consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<ResponseObject<Integer>> savePerformanceCurve(
            @Parameter(description = "펌프그룹 (TB_PUMP_CAL.PUMP_GRP)", example = "1")
            @PathVariable("pumpGrp") Integer pumpGrp,
            @Parameter(description = "조합인덱스 (TB_PUMP_CAL.C_IDX)", example = "1")
            @PathVariable("combIdx") Integer combIdx,
            @RequestBody PumpCurveSaveRequest request) {
        return getResponseEntity(pumpCurveSaveService.save(pumpGrp, combIdx, request));
    }
}
