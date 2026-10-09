package kr.co.mindone.ems.drvn;
/**
 * packageName    : kr.co.mindone.ems.drvn
 * fileName       : DrvnController
 * author         : geunwon
 * date           : 24. 9. 9.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 9.        geunwon       최초 생성
 */
import io.swagger.annotations.Api;
import io.swagger.v3.oas.annotations.Operation;
import kr.co.mindone.ems.common.ExcelService;
import kr.co.mindone.ems.common.holiday.HolidayChecker;
import kr.co.mindone.ems.config.base.BaseController;
import kr.co.mindone.ems.config.response.ResponseMessage;
import kr.co.mindone.ems.config.response.ResponseObject;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.HashMap;
import java.util.List;


@Slf4j
@Api(tags = "DrvnSystem")
@RequestMapping("dr")
@RestController
@Profile("!gm & !hp & !ji & !hy & !ss & !gm2 & !hp2 & !hy2 & !ji2" )
public class DrvnController extends BaseController {
	@Autowired
	private DrvnService drvnService;
	@Autowired
	private ExcelService excelService;
	@Value("${spring.profiles.active}")
	private String wpp_code;

	/**
	 * [GET] 운전현황 페이지의 최신조합 시간 정보를 반환하는 API
	 * @return DB에 저장된 가장 최신의 조합 데이터의 시간데이터 yyyy-mm-dd hh24:mm:00
	 */
	@GetMapping("/getServerTime")
	public ResponseObject<String> getServerTime(){
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:00");
		String dateTime = LocalDateTime.now().format(formatter);

		String returnString;

		String combString = drvnService.getPumpCombTime();
		if(combString == null){
			returnString = LocalDateTime.now().format(formatter);
		}else{
			returnString = combString;
		}


		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnString);
	}

	/**
	 * [POST] 운전형황 시스템 성능공선 데이터 호출 api
	 * @param map
	 * cycle : 주기 [5 ~ 60]
	 * opt_idx : 예측 및 실측 ["pre": 예측 or "cur": 실측]
	 * pump_grp : 펌프 그룹 [1 or 2 or 3...]
	 * range: 조회 범위(시간) [4 or 8 or 12...]
	 * startDate: 조회 기준 날짜(yyyy-mm-dd hh24:mm:00) ["2024-09-09 21:53:00"]
	 * @return 성능곡선 차트 데이터
	 */
	@Operation(summary = "운전형황 시스템 성능공선 데이터 호출 api",
			description = "interval : 주기"
	)
	@PostMapping("/systemResistanceCurves")
	public ResponseObject<List<HashMap<String, Object>>> systemResistanceCurves(@RequestBody HashMap<String, Object> map){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.systemResistanceCurves(map));
	}
	
	@GetMapping("pump")
	public ResponseObject<HashMap<String, Object>> getPumpComb() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.getPumpComb());
	}

	/**
	 * [GET] 운전현황 분기 및 유량 차트데이터 반환 API
	 * @param param
	 * opt_idx : 예측 및 실측 ["pre": 예측 or "cur": 실측]
	 * startDate: 조회 기준 날짜(yyyy-mm-dd hh24:mm:00) ["2024-09-09 21:53:00"]
	 * @return 예측 및 실측에 해당하는 유량, 압력 차트 데이터
	 */
	@GetMapping("/selectIntradotion")
	public ResponseObject<HashMap<String, Object>> selectIntradotion(@RequestParam HashMap<String, Object> param){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.selectIntradotion(param));
	}

	/**
	 * [GET] 운전현황 성능곡선 회기식 데이터 반환 API
	 * @return 성능곡선 회기식 데이터
	 */
	@GetMapping("/selectPumpCombCal")
	public ResponseObject<List<HashMap<String, Object>>> selectPumpCombCal(){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.selectPumpCombCal());
	}

	/**
	 * [GET] 운전현황 분석이력 및 예측조회 CSV 다운로드 API
	 * @param response
	 * @param map
	 * @throws IOException
	 */
	@GetMapping("/download")
	public void downloadExcel(HttpServletResponse response, @RequestParam HashMap<String, Object> map) throws IOException {
		String startDate = (String) map.get("startDate");
		String adjustedDateString = drvnService.increaseByMinutes(startDate, -1);
		map.put("startDate", adjustedDateString);
		DateTimeFormatter idxFormatter = DateTimeFormatter.ofPattern("yyMMddHHmmss");
		LocalDateTime currentTime = LocalDateTime.now();
		String nowDateTime = currentTime.format(idxFormatter);
		String fileName = "";
		String findStr = (String) map.get("findIdx");
		int find = Integer.parseInt(findStr);
		if (find == 1) {
			fileName = "운전현황예측조회" + nowDateTime + ".xlsx";
		} else if (find == 2) {
			fileName = "운전현황분석이력" + nowDateTime + ".xlsx";
		}

		try {
			String encodedFileName = URLEncoder.encode(fileName, StandardCharsets.UTF_8);
			response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
			response.setHeader("Content-Disposition", "attachment; filename=" + encodedFileName);

			try (SXSSFWorkbook workbook = drvnService.xlsxCreate(map)) {
				workbook.getSheetAt(0).trackAllColumnsForAutoSizing(); // 또는 trackColumnForAutoSizing(columnIndex)
				// HTTP 응답으로 엑셀 파일 다운로드
				workbook.write(response.getOutputStream());
			}
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
		}
	}

	/**
	 * 운전현황 페이지 실측 펌프조합 차트 데이터 반환 API
	 * @param param
	 * @return 실측 펌프조합 차트 데이터
	 */
	@GetMapping("/getPumpUse")
	public ResponseObject<HashMap<String, Object>> getPumpUse(@RequestParam HashMap<String, Object> param){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.getPumpUse(param));
	}

	/**
	 * 운전현황 페이지 예측 펌프조합 차트 데이터 반환 API
	 * @param param
	 * @return 에측 펌프조합 차트 데이터
	 */
	@GetMapping("/predictionPumpCombination")
	public ResponseObject<HashMap<String,Object>> predictionPumpCombination(@RequestParam HashMap<String, Object> param){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.predictionPumpCombination(param));
	}

	/**
	 * 예측 펌프조합 수동 삽인 API
	 * @param map
	 * @return 펌프조합 생성과정 로그
	 */
	@GetMapping("/pumpCombInsert")
	public ResponseObject<StringBuffer> pumpCombInsert(@RequestParam HashMap<String, String> map){
		String startDate = map.get("startDate");
		String startTime = map.get("startTime");
		String endDate = map.get("endDate");
		String endTime = map.get("endTime");
		HashMap<String, Object> param = new HashMap<>();
		param.put("startDate", startDate+" "+startTime);
		param.put("endDate", endDate+" "+endTime);
		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, drvnService.pumpCombInsert(param));
	}

	/**
	 * 송수펌프 가동이력 페이지 펌프 가동 조합 csv 다운로드 API
	 * @param response
	 * @param map
	 * @return 펌프 가동조합(예측, 실측) csv
	 */
	@GetMapping("/pumpCombinationExcel")
	public ResponseEntity<String> pumpCombinationExcel(HttpServletResponse response, @RequestParam HashMap<String, Object> map) {
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
		String startDate = (String) map.get("startDate");
		String endDate = (String) map.get("endDate");
		LocalDate stDate = LocalDate.parse(startDate, formatter);
		LocalDate edDate = LocalDate.parse(endDate, formatter);

		// Calculating the number of days between the two dates
		long daysBetween = ChronoUnit.DAYS.between(stDate, edDate);

		// Checking if the difference exceeds 30 days
		if (daysBetween > 30) {
			return ResponseEntity.badRequest().body("30일을 초과하는 기간 조회입니다.");
		}

		// If the difference is within 30 days, proceed with generating the file
		DateTimeFormatter idxFormatter = DateTimeFormatter.ofPattern("yyMMddHHmmss");
		LocalDateTime currentTime = LocalDateTime.now();
		String nowDateTime = currentTime.format(idxFormatter);
		String fileName = "펌프운전조합" + nowDateTime + ".xlsx";

		try {
			String encodedFileName = URLEncoder.encode(fileName, StandardCharsets.UTF_8);
			response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
			response.setHeader("Content-Disposition", "attachment; filename=" + encodedFileName);

			try (SXSSFWorkbook workbook = drvnService.pumpDrvnCombExcelCreate(map)) {
				workbook.getSheetAt(0).trackAllColumnsForAutoSizing(); // 또는 trackColumnForAutoSizing(columnIndex)
				// HTTP 응답으로 엑셀 파일 다운로드
				workbook.write(response.getOutputStream());
			}
		} catch (IOException e) {
			e.printStackTrace();
			return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("An error occurred while generating the Excel file.");
		}

		return ResponseEntity.ok().build();
	}

	/**
	 * 운전현황 페이지 송수펌프 전력 전력원단위 및 펌프 가동 대수 차트 데이터 반환 API
	 * @param param
	 * @return 전력원단위 및 펌프 가동 대수 차트 데이터
	 */
	@GetMapping("/pumpPwrSrcUnitData")
	public ResponseObject<HashMap<String, Object>> pumpPwrSrcUnitData(@RequestParam HashMap<String, Object> param){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.pumpPwrSrcUnitData(param));
	}

	/**
	 * 운전현황 페이지 고령정수장 제어 압력 데이터 반환 API
	 * @return 주파수 제어 압력 반환 데이터
	 */
	@GetMapping("/getGrLifePre")
	public ResponseObject<HashMap<String, Double>> getGrLifePre(){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.getGrLifePre());
	}

	@GetMapping("/pumpManualOperation/{pump_grp}/{oper}")
	public ResponseEntity<ResponseObject<String>> pumpManualOperation(@PathVariable int pump_grp, @PathVariable String oper) {
		String serverTime = drvnService.getPumpCombLogTime();
		HashMap<String, Object> checkLogParam = new HashMap<>();
		checkLogParam.put("serverTime", serverTime);
		if(!oper.equals("up") && !oper.equals("down") && !oper.equals("stop")){
			ResponseObject<String> responseObject = makeSuccessObj(400, "유효하지 않는 요청입니다.", "유효하지 않는 요청입니다.");
			return new ResponseEntity<>(responseObject, HttpStatus.BAD_REQUEST); // 400 상태 코드를 사용
		}

		if(wpp_code.equals("gs")){
			checkLogParam.put("pump_grp", 0);
			checkLogParam.put("interval", 30);
		}else if(wpp_code.equals("ba") || wpp_code.equals("gr")){
			checkLogParam.put("pump_grp", pump_grp);
			checkLogParam.put("interval", 5);
		}else{
			checkLogParam.put("pump_grp", pump_grp);
			checkLogParam.put("interval", 30);
		}

		int checkLog = drvnService.checkManualOperLog(checkLogParam);
		String errMinute;
		if(wpp_code.equals("ba") || wpp_code.equals("gr")) {
			errMinute = "5";
		}else{
			errMinute = "30";
		}

		if(checkLog != 0) {
			ResponseObject<String> responseObject = makeSuccessObj(400, "마지막 제어 후 "+errMinute+"분이 지나지 않았습니다.", "마지막 제어 후 "+errMinute+"분이 지나지 않았습니다.");
			return new ResponseEntity<>(responseObject, HttpStatus.BAD_REQUEST); // 400 상태 코드를 사용
		}
		String returnMessage = drvnService.pumpManualOperation(serverTime, pump_grp, oper);
		if(returnMessage.equals("success")){
			ResponseObject<String> successResponse = makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "적용되었습니다.");
			return new ResponseEntity<>(successResponse, HttpStatus.OK); // 성공 시 200 반환
		}else{
			String message = "알 수 없음";
			if(oper.equals("up")){
				message = "증가";
			}else if(oper.equals("down")){
				message = "감소";
			}else if(oper.equals("stop")){
				message = "종료";
			}
			ResponseObject<String> responseObject = makeSuccessObj(400, "더 이상 조합을 "+message+"시킬 수 없습니다.", "더 이상 조합을 "+message+"시킬 수 없습니다.");
			return new ResponseEntity<>(responseObject, HttpStatus.BAD_REQUEST); // 400 상태 코
		}
	}
	@GetMapping("pumpManualOperFreq/{pump_grp}/{freq}")
	public ResponseEntity<ResponseObject<String>> pumpManualOperFreq(@PathVariable int pump_grp, @PathVariable double freq) {
		String serverTime = drvnService.getPumpCombLogTime();

		String returnMessage = drvnService.pumpManualOperFreq(serverTime, pump_grp, freq);


			ResponseObject<String> successResponse = makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "적용되었습니다.");
			return new ResponseEntity<>(successResponse, HttpStatus.OK); // 성공 시 200 반환

	}

	@GetMapping("grOptLevel")
	public ResponseObject<HashMap<String, Object>> grOptLevel(@RequestParam int pump_grp){
		LocalDateTime dateTime = LocalDateTime.now(ZoneId.of("Asia/Seoul"));
		int hour = dateTime.getHour();
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");

		//날짜 치환
		// 포맷에 맞춰 문자열로 변환
		String serverTime = dateTime.format(formatter);
		HashMap<String, Object> returnMap = new HashMap<>();
		if(pump_grp == 1){
			if (hour < 6) {
				returnMap.put("다산산단", 2.8);
				returnMap.put("다산면", 2.8);
			} else if (hour < 8){
				returnMap.put("다산산단", 3.0);
				returnMap.put("다산면", 3.0);
			}else{
				returnMap.put("다산산단", 3.0);
				returnMap.put("다산면", 3.0);
			}
		}else if(pump_grp == 3){
			DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
			int week =  dayOfWeek.getValue();
			HolidayChecker holidayChecker = new HolidayChecker();
			boolean passDayBool = holidayChecker.isPassDay(serverTime);

			if(!passDayBool && week <= 5){
				if(hour < 2){
					returnMap.put("선남", 3.0);
					returnMap.put("성주통합", 3.0);
				}else if(hour < 4){
					returnMap.put("선남", 3.2);
					returnMap.put("성주통합", 3.4);
				}else if(hour < 6) {
					returnMap.put("선남", 3.4);
					returnMap.put("성주통합", 3.9);

				}else if(hour < 8){
					returnMap.put("선남", 3.5);
					returnMap.put("성주통합", 4.1);
				}else{
					returnMap.put("선남", 3.5);
					returnMap.put("성주통합", 4.1);
				}
			}else{
				if(hour < 2){
					returnMap.put("선남", 3.0);
					returnMap.put("성주통합", 3.0);
				}else if(hour < 4){
					returnMap.put("선남", 3.2);
					returnMap.put("성주통합", 3.3);
				}else if(hour < 6) {
					returnMap.put("선남", 3.3);
					returnMap.put("성주통합", 3.7);

				}else if(hour < 8){
					returnMap.put("선남", 3.5);
					returnMap.put("성주통합", 4.0);
				}else{
					returnMap.put("선남", 3.5);
					returnMap.put("성주통합", 4.1);
				}

			}
		}
		if(!returnMap.isEmpty()){
			if(hour < 2){
				returnMap.put("time", "00:00 ~ 01:59");
			}else if(hour < 4){
				returnMap.put("time", "02:00 ~ 03:59");

			}else if(hour < 6){
				returnMap.put("time", "04:00 ~ 05:59");

			}else if(hour < 8){
				returnMap.put("time", "06:00 ~ 07:59");

			}else{
				returnMap.put("time", serverTime);
			}



		}
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnMap);
	}
	@Operation(summary = "그룹 별 조합 회기식", description = "getGroupPumpCal")
	@GetMapping("/getGroupPumpCal/{pump_grp}/{pump_count}/{pump_priority}")
	public ResponseObject<List<HashMap<String, Object>>> getGroupPumpCal(@PathVariable int pump_grp, @PathVariable double pump_count, @PathVariable int pump_priority){
		HashMap<String, Object> map = new HashMap<>();
		map.put("pump_grp", pump_grp);
		map.put("pump_count", pump_count);
		map.put("pump_priority", pump_priority);
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.getGroupPumpCal(map));
	}

	@GetMapping("/getGrpFlowPressure/{pump_grp}")
	public ResponseObject<HashMap<Integer, HashMap<String, Double>>> getGrpFlowPressure(@PathVariable int pump_grp){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.getGrpFlowPressure(pump_grp));
	}




	/**
	 *  펌프 조합 정의 목록
	 * @param pump_grp 펌프 그룹
	 * @return 펌프 조합 정의 목록
	 */
	@Operation(summary = "펌프 조합 정의 목록", description = "selectPumpCombList")
	@GetMapping("/selectPumpCombList/{pump_grp}")
	public ResponseObject<List<HashMap<String, Object>>>  selectPumpCombList(@PathVariable int pump_grp){

		HashMap<String, Object> map = new HashMap<>();
		map.put("pump_grp", pump_grp);

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.selectPumpCombList(map));
	}

	/**
	 * 조합정보 업데이트
	 * @param updateMap 업데이트할 요금제 정보
	 * @return 업데이트 성공 메시지
	 */
	@Operation(summary = "조합 상세정보 업데이트", description = "setRateCost")
	@PostMapping("/savePumpComb")
	public ResponseObject<String> savePumpComb(@RequestBody List<HashMap<String, Object>> updateMap){
		drvnService.savePumpComb(updateMap);
		drvnService.changePumpCal(updateMap);
		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "조합 상세정보 업데이트");
	}

	@Operation(summary = "조합정보 업데이트", description = "savePumpComb")
	@PostMapping("/updatePumpCombItem")
	public ResponseObject<String> updatePumpCombItem(@RequestBody HashMap<String, Object> updateMap){
		drvnService.updatePumpCombItem(updateMap);

		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "조합정보 업데이트");
	}

	@Operation(summary = "조합정보 상세", description = "getPumpCombinationItem")
	@GetMapping("/getPumpCombinationItem/{pump_grp}/{pump_count}/{pump_priority}")
	public ResponseObject<List<HashMap<String, Object>>> getPumpCombinationItem(@PathVariable int pump_grp, @PathVariable String pump_count, @PathVariable int pump_priority){
		HashMap<String, Object> map = new HashMap<>();
		map.put("pump_grp", pump_grp);
		map.put("pump_count", pump_count);
		map.put("pump_priority", pump_priority);
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.getPumpCombinationItem(map));
	}
	@PostMapping("/setPumpListYn")
	public  ResponseObject<String> setPumpListYn(@RequestBody List<HashMap<String, Object>> updateList){
		drvnService.setPumpListYn(updateList);
		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "조합정보 업데이트");
	}

	@GetMapping("/getPumpPwrVal")
	public  ResponseObject<HashMap<Integer, HashMap<Integer, Double>>> getPumpPwrVal(){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.getPrdctPwrIdxValMap());
	}
	@GetMapping("/getPumpPwrCal")
	public  ResponseObject<HashMap<Integer, HashMap<String, Double>>> getPumpPwrCal() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, drvnService.getPrdctPwrCalValMap());
	}
	@PostMapping("/trigger-pump")
	public ResponseEntity<String> triggerPumpSchedule() {
		drvnService.setInsertPumpComn(); // 비동기이므로 바로 리턴됨
		return ResponseEntity.ok("Pump schedule task triggered.");
	}
}
