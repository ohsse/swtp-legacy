package kr.co.mindone.ems.energy;
/**
 * packageName    : kr.co.mindone.ems.energy
 * fileName       : EnerSpendController
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import io.swagger.v3.oas.annotations.Operation;
import kr.co.mindone.ems.ai.AiService;
import kr.co.mindone.ems.common.SavingService;
import kr.co.mindone.ems.config.base.BaseController;
import kr.co.mindone.ems.config.response.ResponseMessage;
import kr.co.mindone.ems.config.response.ResponseObject;
import org.apache.ibatis.annotations.Param;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static kr.co.mindone.ems.common.SavingService.*;

@RequestMapping("es")
@RestController
public class EnerSpendController extends BaseController {
	@Autowired
	private EnerSpendService enerSpendService;

	@Autowired
	private SavingService savingService;

	@Autowired
	private AiService aiService;

	/**
	 * 설비 순시 시간대별 값을 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 설비 순시 시간대별 값 리스트
	 */
	@Operation(summary = "설비 순시 시간대별 값", description = "selectFacUseList?start_date=2023-07-18&end_date=2023-07-19&zone_code=송수펌프동&fac_code=&time_type=h")
	@GetMapping("/selectFacUseList")
	public ResponseObject<List<HashMap<String, Object>>>  selectFacUseList(@RequestParam HashMap<String, Object> map){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectFacUseList(map));
	}

	/**
	 * 설비 순시 합계를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 설비 순시 합계 리스트
	 */
	@Operation(summary = "설비 순시 합", description = "selectFacUseList_sum?start_date=2023-07-18&end_date=2023-07-19&zone_code=송수펌프동&fac_code=MV-P2&time_type=h")
	@GetMapping("/selectFacUseList_sum")
	public ResponseObject<List<HashMap<String, Object>>>  selectFacUseList_sum(@RequestParam HashMap<String, Object> map){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectFacUseList_sum(map));
	}

	/**
	 * 시설 순시 시간대별 값을 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 순시 시간대별 값 리스트
	 */
	@Operation(summary = "시설 순시 시간대별 값", description = "selectZoneUseList?start_date=2023-03-10&end_date=2023-03-30&time_type=h")
	@GetMapping("/selectZoneUseList")
	public ResponseObject<List<HashMap<String, Object>>> selectZoneUseList(@RequestParam HashMap<String, Object> map){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectZoneUseList(map));
	}

	/**
	 * 시설 순시 합계를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 순시 합계 리스트
	 */
	@Operation(summary = "시설 순시 합", description = "selectZoneUseList_sum?start_date=2023-03-13&end_date=2023-03-30&time_type=h")
	@GetMapping("/selectZoneUseList_sum")
	public ResponseObject<List<HashMap<String, Object>>> selectZoneUseList_sum(@RequestParam HashMap<String, Object> map){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectZoneUseList_sum(map));
	}

	/**
	 * 현시각 시설 순시 데이터를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 현시각 시설 순시 데이터 리스트
	 */
	@Operation(summary = "현시각 시설 순시", description = "/sisul_sunsi")
	@GetMapping("/sisul_sunsi")
	public ResponseObject<List<HashMap<String, Object>>> sisul_sunsi(@RequestParam HashMap<String, Object> map){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.sisul_sunsi(map));
	}

	/**
	 * 펌프 TAG 별 정보를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 펌프 TAG 별 정보 리스트
	 */
	@Operation(summary = "펌프 TAG 별 정보", description = "selectPumpPerformList?start_date=2023-08-03&end_date=2023-08-04&time_type=h")
	@GetMapping("/selectPumpPerformList")
	public ResponseObject<Map<String,Object>> selectPumpPerformList(@RequestParam HashMap<String, Object> map) {
		//return enerSpendService.selectPumpPerformList(map);
		Map<String, Object> returnMap = new HashMap<>();
		map.put("tag_type","PMB_TAG");
		returnMap.put("PMB_TAG", enerSpendService.selectPumpPerformList(map));
		map.put("tag_type","PWI_TAG");
//		returnMap.put("PWI_TAG", enerSpendService.selectPumpPerformList_ss_pwi(map));
		returnMap.put("PWI_TAG", enerSpendService.selectPumpPerformList(map));
		map.put("tag_type","PRI_TAG");
		returnMap.put("PRI_TAG", enerSpendService.selectPumpPerformList(map));
		map.put("tag_type","SPI_TAG");
		returnMap.put("SPI_TAG", enerSpendService.selectPumpPerformList(map));
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnMap);
	}

	/**
	 * 펌프 TAG 별 정보를 알고리즘 없이 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 펌프 TAG 별 정보 리스트
	 */
	@Operation(summary = "펌프 TAG 별 정보(알고리즘X)", description = "selectPumpPerformList?start_date=2023-08-03&end_date=2023-08-04&time_type=h")
	@GetMapping("/selectPumpPerformList_new")
	public ResponseObject<Map<String,Object>> selectPumpPerformList_new(@RequestParam HashMap<String, Object> map) {
		//return enerSpendService.selectPumpPerformList(map);
		Map<String, Object> returnMap = new HashMap<>();
		map.put("tag_type","PMB_TAG");
		returnMap.put("PMB_TAG", enerSpendService.selectPumpPerformList(map));
		map.put("tag_type","PWI_TAG");
		returnMap.put("PWI_TAG", enerSpendService.selectPumpPerformList_ss_pwi(map));
//		returnMap.put("PWI_TAG", enerSpendService.selectPumpPerformList(map));
		map.put("tag_type","PRI_TAG");
		returnMap.put("PRI_TAG", enerSpendService.selectPumpPerformList(map));
		map.put("tag_type","SPI_TAG");
		returnMap.put("SPI_TAG", enerSpendService.selectPumpPerformList(map));
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnMap);
	}

	/**
	 * 설비 정보를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 설비 정보 리스트
	 */
	@Operation(summary = "설비정보", description = "selectFac?zone_code=약품동")
	@GetMapping("/selectFac")
	ResponseObject<List<HashMap<String, Object>>> selectFac(@RequestParam HashMap<String, Object> map){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectFac(map));
	}

	/**
	 * 시설 순시 차트를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 순시 차트 리스트
	 */
	@Operation(summary = "시설 순시 차트", description = "sunsiChart?zone_code=송수펌프동")
	@GetMapping("/sunsiChart")
	public ResponseObject<List<HashMap<String, Object>>>  sunsiChart(@RequestParam HashMap<String, Object> map){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.sunsiChart(map));
	}

	/**
	 * 시설 순시 값을 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 순시 값 리스트
	 */
	@Operation(summary = "시설순시값", description = "selectFacSunsi?date=2023-01-10&zone_code=약품동")
	@GetMapping("/selectFacSunsi")
	public ResponseObject<List<HashMap<String, Object>>> selectFacSunsi(@RequestParam HashMap<String, Object> map){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectFacSunsi(map));
	}

	/**
	 * 정수장 현재 전력 사용량을 조회하는 메서드
	 * @return 정수장의 현재 전력 사용량 리스트
	 */
	@Operation(summary = "정수장 현재 전력사용량", description = "selectNowElec")
	@GetMapping("/selectNowElec")
	public ResponseObject<List<HashMap<String, Object>>> selectNowElec() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectNowElec());
	}

	/**
	 * 정수장 현재 피크 목표치를 조회하는 메서드
	 * @return 정수장의 현재 피크 목표치 리스트
	 */
	@Operation(summary = "정수장 현재 피크 목표치", description = "selectNowPeak")
	@GetMapping("/selectNowPeak")
	public ResponseObject<List<HashMap<String, Object>>> selectNowPeak() {


		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectNowPeak());
	}

	/**
	 * 정수장의 일, 월, 년 전기 사용량을 조회하는 메서드
	 * @return 정수장의 일, 월, 년 전기 사용량 리스트
	 */
	@Operation(summary = "정수장 일,월,년 전기사용량", description = "selectNowPeak")
	@GetMapping("/selectYMD")
	public ResponseObject<List<HashMap<String, Object>>> selectYMD() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectYMD());
	}

	/**
	 * 절감 결과를 조회하는 메서드
	 * @return 절감 결과 리스트
	 */
	@Operation(summary = "절감 결과", description = "baseElec")
	@GetMapping("/baseElec")
	public ResponseObject<List<HashMap<String, Object>>> baseElec() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.baseElec());
	}

	/**
	 * 금년 절감량을 조회하는 메서드
	 * @return 금년 절감량 리스트
	 */
	@Operation(summary = "금년 절감량", description = "rstSavingTargetSum")
	@GetMapping("/rstSavingTargetSum")
	public ResponseObject<List<HashMap<String, Object>>> rstSavingTargetSum() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.rstSavingTargetSum());
	}

	/**
	 * 요금제 상세 정보를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 요금제 상세 정보 리스트
	 */
	@Operation(summary = "요금제 상세정보", description = "selectRateInfo")
	@GetMapping("/selectRateInfo")
	public ResponseObject<List<HashMap<String, Object>>> selectRateInfo(@RequestParam HashMap<String, Object> map) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.selectRateInfo(map));
	}

	/**
	 * 시설 피크 값을 조회하는 메서드
	 * @param search 검색어
	 * @return 시설 피크 값 리스트
	 */
	@Operation(summary = "시설 피크값", description = "peakFac")
	@GetMapping("/peakFac")
	public ResponseObject<List<HashMap<String, Object>>> peakFac(@Param("search") String search) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.peakFac(search));
	}

	/**
	 * 정수장의 현재 피크 값을 조회하는 메서드
	 * @return 현재 피크 값 리스트
	 * @throws Exception 예외 발생 시
	 */
	@GetMapping("/nowPeak")
	public ResponseObject<List<HashMap<String, Object>>> nowPeak() throws Exception {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, enerSpendService.nowPeak());
	}


	/**
	 * 절감 결과를 조회하는 메서드
	 * @return 절감 결과 리스트
	 * @throws Exception 예외 발생 시
	 */
	@GetMapping("/saverst")
	public ResponseObject<List<HashMap<String, Object>>> savingRst() throws Exception {
		List<HashMap<String, Object>> savingResultList = aiService.selectSavingResult();
		//SavingService
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, savingResultList);
	}




}
