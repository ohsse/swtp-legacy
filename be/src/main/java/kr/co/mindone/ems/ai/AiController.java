package kr.co.mindone.ems.ai;
/**
 * packageName    : kr.co.mindone.ems.ai
 * fileName       : AiController
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import com.google.gson.Gson;
import io.swagger.annotations.Api;
import io.swagger.v3.oas.annotations.Operation;
import kr.co.mindone.ems.common.CommonService;
import kr.co.mindone.ems.config.base.BaseController;
import kr.co.mindone.ems.config.response.ResponseMessage;
import kr.co.mindone.ems.config.response.ResponseObject;
import kr.co.mindone.ems.energy.EnerSpendService;
import kr.co.mindone.ems.setting.SettingService;
import lombok.extern.slf4j.Slf4j;
import org.apache.catalina.mbeans.SparseUserDatabaseMBean;
import org.apache.ibatis.annotations.DeleteProvider;
import org.apache.ibatis.annotations.Param;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import java.io.UnsupportedEncodingException;
import java.text.DecimalFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

@Slf4j
@Api(tags = "AiSystem")
@RequestMapping("ai")
@RestController
public class AiController extends BaseController {

	@Autowired
	private AiService aiService;
	@Autowired
	private SettingService settingService;

	@Autowired
	private EnerSpendService enerSpendService;

	@Autowired
	private CommonService commonService;

	private final AtomicBoolean isRunning = new AtomicBoolean(false);

	@Value("${spring.profiles.active}")
	private String wpp_code;
	/**
	 * 펌프 전력사용량 예측값 호출
	 * @param map 펌프 그룹에 대한 필터 조건
	 * @return 펌프 예측 전력 데이터
	 */
	@Operation(summary = "펌프 전력사용량 예측값 호출", description = "pumpSelect?pump_grp=2")
	@GetMapping("/pumpSelect")
	public ResponseObject < Map < String, Object >> pumpSelect(@RequestParam HashMap < String, Object > map) {
		//CommonVO Object에 대입

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpSelect(map));
	}
	/**
	 * 펌프 전력사용량 예측값 그래프 데이터 호출
	 * @param map 펌프 그룹에 대한 필터 조건
	 * @return 펌프 예측 전력 그래프 데이터
	 */
	@Operation(summary = "펌프 전력사용량 예측값 그래프 데이터 호출", description = "pumpGrpSelect?pump_grp=2")
	@GetMapping("/pumpGrpSelect")
	public ResponseObject < Map < String, Object >> pumpGrpSelect(@RequestParam HashMap < String, Object > map) {
		//CommonVO Object에 대입
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpGrpSelect(map));
	}

	/**
	 * 펌프 전력사용량 예측값 호출(알고리즘 데이터 없음)
	 * @param map 펌프 그룹에 대한 필터 조건
	 * @return 펌프 예측 전력 데이터
	 */
	@Operation(summary = "펌프 전력사용량 예측값 호출(알고리즘데이터X)", description = "pumpSelect_new?pump_grp=2")
	@GetMapping("/pumpSelect_new")
	public ResponseObject < Map < String, Object >> pumpSelect_new(@RequestParam HashMap < String, Object > map) {
		//CommonVO Object에 대입
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpSelect_new(map));
	}
	/**
	 * 펌프 전력사용량 예측값 목록 호출
	 * @param map 펌프 그룹에 대한 필터 조건
	 * @return 펌프 예측 전력 데이터 목록
	 */
	@Operation(summary = "펌프 전력사용량 예측값 호출", description = "pumpSelectList?pump_grp=2")
	@GetMapping("/pumpSelectList")
	public ResponseObject < Map < String, Object >> pumpSelectList(@RequestParam HashMap < String, Object > map) {
		//CommonVO Object에 대입
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpSelectList(map));
	}
	/**
	 * 펌프 전력사용량 예측값 목록 호출(알고리즘 데이터 없음)
	 * @param map 펌프 그룹에 대한 필터 조건
	 * @return 펌프 예측 전력 데이터 목록
	 */
	@Operation(summary = "펌프 전력사용량 예측값 호출(알고리즘데이터X)", description = "pumpSelectList_new?pump_grp=2")
	@GetMapping("/pumpSelectList_new")
	public ResponseObject < Map < String, Object >> pumpSelectList_new(@RequestParam HashMap < String, Object > map) {
		//CommonVO Object에 대입

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpSelectList_new(map));
	}
	/**
	 * 펌프 정보 및 관압 데이터 호출
	 * @param map 펌프 데이터에 대한 필터 조건
	 * @return 펌프 및 관압 관련 데이터
	 */
	@Operation(summary = "펌프 정보 및 관압 데이터 호출", description = "selectPumpPrdct")
	@GetMapping("/selectPumpPrdct")
	public ResponseObject < Map < String, Object >> selectPumpPrdct(@RequestParam HashMap < String, Object > map) {

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectPumpPrdct());
	}
	/**
	 * 배수지(정수지) 정보 조회
	 * @param map 배수지 또는 정수지에 대한 필터 조건
	 * @return 배수지 또는 정수지 관련 데이터 목록
	 */
	@Operation(summary = "배수지(정수지) 정보 조회(구:sujiCombo)", description = "selectTankList?tnk_typ=1(배수지)2(정수지)")
	@GetMapping("/selectTankList")
	public ResponseObject < List < HashMap < String, Object >>> selectTankList(@RequestParam HashMap < String, Object > map) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectTankList(map));
	}

	/**
	 * 배수지 시간단위 수위 호출
	 * @param map 배수지의 시간별 수위 데이터 필터 조건
	 * @return 배수지 시간별 수위 및 합계 데이터
	 */
	@Operation(summary = "배수지 시간단위 수위 호출(구 baeSuji)", description = "selectTankDataHourList?TNK_TYP=1&date=2023-08-11")
	@GetMapping("/selectTankDataHourList")
	public ResponseObject < Map < String, Object >> selectTankDataHourList(@RequestParam HashMap < String, Object > map) {
		Map < String, Object > returnMap = new HashMap < > ();
		returnMap.put("hour_list", aiService.selectTankDataHourList(map));
		returnMap.put("sum_list", aiService.selectTankDataHourSumList(map));
		returnMap.put("tank_instn", aiService.tankInstantaneous(map));
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnMap);
	}
	/**
	 * 배수지 TAG 정보 호출
	 * @param map 배수지 및 펌프 태그 데이터에 대한 필터 조건
	 * @return 배수지 및 펌프 태그 관련 데이터
	 */
	@Operation(summary = "배수지 TAG 정보 호출(구:songsuSelect)", description = "selectSongsuTagValueList")
	@GetMapping("/selectSongsuTagValueList")
	public ResponseObject < Map < String, Object >> selectTnkTagValueList(@RequestParam HashMap < String, Object > map) {
		Map < String, Object > returnMap = new HashMap < > ();

		List < HashMap < String, Object >> pumpList = aiService.selectPumpList(map);
		List < HashMap < String, Object >> pumpTagValueList = aiService.selectPumpTagValueList(map);
		List < HashMap < String, Object >> pumpTagValueTempList = new ArrayList < > ();
		returnMap.put("tnkList", aiService.selectTnkTagValueList(map));

		for (HashMap < String, Object > pItem: pumpList) {
			HashMap < String, Object > newItem = new HashMap < > (pItem);
			for (HashMap < String, Object > cItem: pumpTagValueList) {
				if (newItem.get("PUMP_IDX").toString().equals(cItem.get("PUMP_IDX").toString())) {
					if (cItem.get("tag_typ").toString().equals("PMB")) {
						newItem.put("PMB_VALUE", cItem.get("value"));
					} else if (cItem.get("tag_typ").toString().equals("SPI")) {
						newItem.put("SPI_VALUE", cItem.get("value"));
					} else if (cItem.get("tag_typ").toString().equals("CTI")) {
						newItem.put("CTI_VALUE", cItem.get("value"));
					} else if (cItem.get("tag_typ").toString().equals("PRI")) {
						newItem.put("PRI_VALUE", cItem.get("value"));
					} else if (cItem.get("tag_typ").toString().equals("FRI")) {
						newItem.put("FRI_VALUE", cItem.get("value"));
					} else if (cItem.get("tag_typ").toString().equals("PWI")) {
						newItem.put("PWI_VALUE", cItem.get("value"));
					}
					newItem.put("ts", cItem.get("ts"));
				}
			}
			pumpTagValueTempList.add(newItem);
		}
		returnMap.put("pumpList", pumpTagValueTempList);
		returnMap.put("aiOnOffList", aiService.aiOnOffList(map)); //HMI 추가 태그(EMS)로 정의필요

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnMap);
	}

	/**
	 * 배수지 TAG 정보 범위 호출
	 * @param map 배수지 및 펌프 태그 범위 데이터 필터 조건
	 * @return 배수지 및 펌프 태그 범위 데이터
	 */
	@Operation(summary = "배수지 TAG 정보 호출(구:sujiSelect)", description = "selectWpTnkTagRangeList?tnk_grp_idx=1&time_type=h&start_date=2023-09-12&end_date=2023-09-13")
	@GetMapping("/selectWpTnkTagRangeList")
	public ResponseObject < Map < String, Object >> selectWpTnkTagRangeList(@RequestParam HashMap < String, Object > map) {
		Map < String, Object > returnMap = new HashMap < > ();
		map.put("value_type", "tnk");
		map.put("tag_type", "LEI");
		List < HashMap < String, Object >> temp = aiService.selectWpTnkTagRangeList(map);
		returnMap.put("LEI", temp); //수위 LEI
		//System.out.println("selectWpTnkTagRangeList(map) LEI "+temp.toString());
		map.put("tag_type", "IN_FLW");
		returnMap.put("IN_FLW", aiService.selectWpTnkTagRangeList(map)); //유입유량 IN_FLW
		map.put("tag_type", "OUT_FLW");
		returnMap.put("OUT_FLW", aiService.selectWpTnkTagRangeList(map)); //유출유량 OUT_FLW

		map.put("tag_type", "IN_FC");
		returnMap.put("IN_FC", aiService.selectWpTnkTagRangeList(map)); //밸브상태 FC
		map.put("tag_type", "OUT_FC");
		returnMap.put("OUT_FC", aiService.selectWpTnkTagRangeList(map)); //밸브상태 FO
		map.put("tag_type", "IN_FO");
		returnMap.put("IN_FO", aiService.selectWpTnkTagRangeList(map)); //밸브상태 FC
		map.put("tag_type", "OUT_FO");
		returnMap.put("OUT_FO", aiService.selectWpTnkTagRangeList(map)); //밸브상태 FO

        /*map.put("value_type", "pump");
        map.put("tag_type", "PRI");
        returnMap.put("PRI", aiService.selectWpTnkTagRangeList(map)); //정속 토출관압 PRI
        map.put("tag_type", "PMB");*/

		//정속가동대수
		/*returnMap.put("PMB", aiService.selectWpTnkTagRangeList(map)); //정속 펌프대수 PMB*/
		//returnMap.put("data_right", aiService.selectWpTnkInstnTagList(map));

		//TagDcs
		map.put("tag_typ", "TNK");
		returnMap.put("info", commonService.selectTagInfo(map)); //태그 설정

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnMap);
	}
	/**
	 * 펌프 목록 호출
	 * @param map 펌프 그룹에 대한 필터 조건
	 * @return 펌프 목록
	 */
	@GetMapping("/selectPumpList")
	public ResponseObject < List < HashMap < String, Object >>> selectPumpList(@RequestParam HashMap < String, Object > map) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectPumpList(map));
	}
	/**
	 * 사용량 트렌드 목록 호출
	 * @param map 시간 단위와 시작 및 종료 날짜에 대한 필터 조건
	 * @return 사용량 트렌드 목록
	 */
	@Operation(summary = "사용량 트랜드 목록", description = "selectUseTrandList?time_type=h&start_date=2023-08-07&end_date=2023-08-08")
	@GetMapping("/selectUseTrandList")
	public ResponseObject < Map < String, Object >> selectUseTrandList(@RequestParam HashMap < String, Object > map) {
		Map < String, Object > returnMap = new HashMap < > ();

		returnMap.put("trand_list", aiService.selectElcPwqList(map)); //전체 전력샤용 트랜드
		returnMap.put("peak_max", aiService.peak_max());

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnMap);
	}
	/**
	 * 사용량 트렌드 목록 호출 (기간별 요금)
	 * @param map 시간 범위와 요금 관련 필터 조건
	 * @return 기간별 요금 데이터
	 */
	@Operation(summary = "사용량 트랜드 목록 - 기간별 요금", description = "selectUseTrandRangeCostList")
	@GetMapping("/selectUseTrandRangeCostList")
	public ResponseObject < List < HashMap < String, Object >>> selectUseTrandRangeCostList(@RequestParam HashMap < String, Object > map) {
		Map < String, Object > returnMap = new HashMap < > ();
		List < HashMap < String, Object >> tempPwrSumList = new ArrayList < > ();
		DecimalFormat df = new DecimalFormat("0.00");
		double dayTcost = 0.0, monthTcost = 0.0, yearTcost = 0.0;
		double dayTvalue = 0.0, monthTvalue = 0.0, yearTvalue = 0.0;
		double dayTrate = 0.0, monthTrate = 0.0, yearTrate = 0.0;

		//map.put("range","dayAgo");
		//tempPwrSumList.addAll(aiService.selectPwrSumList(map));
		map.put("range", "day");
		tempPwrSumList.addAll(aiService.selectPwrSumList(map));
		//map.put("range","week");
		//tempPwrSumList.addAll(aiService.selectPwrSumList(map));
		map.put("range", "month");
		tempPwrSumList.addAll(aiService.selectPwrSumList(map));
		map.put("range", "year");
		tempPwrSumList.addAll(aiService.selectPwrSumList(map));

		for (HashMap < String, Object > item: tempPwrSumList) {
			if (item.get("range").equals("day")) {
				dayTvalue += Double.parseDouble(item.get("value").toString());
				dayTrate = Double.parseDouble(item.get("rate").toString());
				dayTcost += Double.parseDouble(item.get("value").toString()) * dayTrate;
			} else if (item.get("range").equals("month")) {
				monthTvalue += Double.parseDouble(item.get("value").toString());
				monthTrate = Double.parseDouble(item.get("rate").toString());
				monthTcost += Double.parseDouble(item.get("value").toString()) * monthTrate;
			} else if (item.get("range").equals("year")) {
				yearTvalue += Double.parseDouble(item.get("value").toString());
				yearTrate = Double.parseDouble(item.get("rate").toString());
				yearTcost += Double.parseDouble(item.get("value").toString()) * yearTrate;
			}
		}

		HashMap < String, Object > dayItem = new HashMap < > ();
		dayItem.put("value", Double.parseDouble(df.format(dayTvalue)));
		dayItem.put("rate", 0);
		dayItem.put("cost", Double.parseDouble(df.format(dayTcost)));
		dayItem.put("timezone", "T");
		dayItem.put("range", "day");
		tempPwrSumList.add(dayItem);

		HashMap < String, Object > weekItem = new HashMap < > ();
		weekItem.put("value", Double.parseDouble(df.format(monthTvalue)));
		weekItem.put("rate", 0);
		weekItem.put("cost", Double.parseDouble(df.format(monthTcost)));
		weekItem.put("timezone", "T");
		weekItem.put("range", "month");
		tempPwrSumList.add(weekItem);

		HashMap < String, Object > yearItem = new HashMap < > ();
		yearItem.put("value", Double.parseDouble(df.format(yearTvalue)));
		yearItem.put("rate", 0);
		yearItem.put("cost", Double.parseDouble(df.format(yearTcost)));
		yearItem.put("timezone", "T");
		yearItem.put("range", "year");
		tempPwrSumList.add(yearItem);

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, tempPwrSumList);
	}
	/**
	 * 펌프 가동 상태 및 제어 정보 호출
	 * @return 펌프 가동 상태 및 관압, 유량, 주파수 정보
	 */
	@GetMapping("/selectPumpStatus")
	public ResponseObject < Map < String, Object >> selectPumpStatus() throws Exception {
		Map < String, Object > returnMap = new HashMap < > ();
		//펌프 가동 상태, 가동 대수
		List < HashMap < String, Object >> tempList = aiService.selectPumpOnOffStatus();
		int runCount = (int) tempList.stream()
				.map(item -> item.get("value"))
				.filter("On"::equals)
				.count();
		tempList.forEach(item -> item.put("runCount", runCount));

		returnMap.put("pumpStatus", tempList); //펌프 가동 상태, 가동 대수
		returnMap.put("PRI", aiService.selectPumpPRITagStatus()); // 관압
		returnMap.put("FRI", aiService.selectPumpFRITagStatus()); // 유량
		returnMap.put("SPI", aiService.selectPumpSPITagStatus()); // 주파수
		returnMap.put("pwiStatus", aiService.selectPumpPwiStatus()); //펌프 각자 전력
		//returnMap.put("PWI", aiService.selectPumpPwiStatus());//펌프 각자 전력

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnMap);
	}
	/**
	 * 펌프 사용 여부 예측 결과 호출
	 * @param map 펌프 그룹에 대한 필터 조건
	 * @return 펌프 가동 상태, 가동 대수 예측 결과
	 */
	@Operation(summary = "펌프 사용여부 예측 결과", description = "/selectPumpPrdctOnOffStatus?pump_grp=1")
	@GetMapping("/selectPumpPrdctOnOffStatus")
	public ResponseObject < List < HashMap < String, Object >>> selectPumpPrdctOnOffStatus(@RequestParam HashMap < String, Object > map) throws Exception {
		//펌프 가동 상태, 가동 대수
		List < HashMap < String, Object >> tempList = aiService.selectPumpPrdctOnOffStatus(map);
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, tempList);
	}
	/**
	 * 송수펌프 제어 분석 - 밸브 관련 정보 호출
	 * @param map 펌프 그룹에 대한 필터 조건
	 * @return 밸브 관련 정보
	 */
	//송수펌프 제어 분석 - 벨브
	@GetMapping("/selectValve")
	public ResponseObject < List < HashMap < String, Object >>> selectValve(@RequestParam HashMap < String, Object > map) throws Exception {
		//벨브관련 정보
		if (map.containsKey("pump_grp") && wpp_code.equals("gs")) {
			int pump_grp = Integer.parseInt(map.get("pump_grp").toString());
			if (pump_grp > 1) {
				map.put("pump_grp", 1);
			}
		}
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectValve(map));
	}

	/**
	 * 피크 제어 정보 호출
	 * @return 피크 제어 데이터 목록
	 */
	@Operation(summary = "총,펌프 순시전력/요금 적용전력", description = "selectPeakControl")
	@GetMapping("/selectPeakControl")
	public ResponseObject < List < HashMap < String, Object >>> selectPeakControl() throws Exception {
		//벨브관련 정보
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectPeakControl());
	}
	/**
	 * 알람 정보 호출
	 * @return 알람 목록 데이터
	 */
	@GetMapping("/selectAlarm")
	public ResponseObject < List < HashMap < String, Object >>> selectAlarm() throws Exception {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectAlarm());
	}
	/**
	 * 시설 상위 전력소모량 상위 3개 호출
	 * @param map 날짜 및 구역 정보 필터 조건
	 * @return 상위 3개 전력소모량 데이터
	 */
	@Operation(summary = "시설 상위 설비 3개 전력소모량", description = "getTop3?date=2023-08-16&zone_code=송수펌프동")
	@GetMapping("/getTop3")
	public ResponseObject < List < HashMap < String, Object >>> getTop3(@RequestParam HashMap < String, Object > map) throws UnsupportedEncodingException {
		DecimalFormat df = new DecimalFormat("0.00");

		map.put("time_type", "d");
		map.put("start_date", map.get("date").toString());
		map.put("end_date", map.get("date").toString());

		List < HashMap < String, Object >> top3List = aiService.getTop3(map);

		double sumValue = 0.0;

		//System.out.println("top3List:"+top3List.toString());

		List < HashMap < String, Object >> top3SumList = new ArrayList < > ();

		for (int i = 0; i < top3List.size(); i++) {
			//System.out.println("top3Item:"+top3List.get(i).toString());
			if (i < 3) {
				HashMap < String, Object > top3Item = new HashMap < > ();
				top3Item.put("dcs", top3List.get(i).get("dcs").toString());
				top3Item.put("value", top3List.get(i).get("value"));
				top3SumList.add(top3Item);
			}
			sumValue += Double.parseDouble(top3List.get(i).get("value").toString());
		}

		Collections.sort(top3SumList, new Comparator < HashMap < String, Object >> () {
			public int compare(HashMap < String, Object > map1, HashMap < String, Object > map2) {
				return ((Double) map2.get("value")).compareTo((Double) map1.get("value"));
			}
		});

		HashMap < String, Object > top3SumItem = new HashMap < > ();
		top3SumItem.put("total", Double.parseDouble(df.format(sumValue)));
		top3SumList.add(top3SumItem);
		//System.out.println("top3SumList:"+top3SumList.toString());
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, top3SumList);
	}
	/**
	 * 피크 결과 및 예측값 조회
	 * @param map 날짜 조건 필터
	 * @return 피크 결과 및 예측값 데이터
	 */
	@Operation(summary = "피크결과, 예측값 조회", description = "peakSelect?date=2023-03-15")
	@GetMapping("/peakSelect")
	public ResponseObject < List < HashMap < String, Object >>> peakSelect(@RequestParam HashMap < String, Object > map) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.peakSelect(map));
	}

	/**
	 * 정수장 전력 사용 요금정보 조회
	 * @param map 날짜 조회 조건
	 * @return 정수장 전력 사용 요금정보
	 */
	@Operation(summary = "정수장 전력사용 요금정보", description = "selectRtRate?ymnth=202307")
	@GetMapping("/selectRtRate")
	public ResponseObject < List < HashMap < String, Object >>> selectRtRate(@RequestParam HashMap < String, Object > map) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectRtRate(map));
	}
	/**
	 * 정수장 펌프 목록 호출
	 * @return 정수장 펌프 목록 데이터
	 */
	@Operation(summary = "정수장 펌프 목록", description = "selectPumpMaster")
	@GetMapping("/selectPumpMaster")
	public ResponseObject < List < HashMap < String, Object >>> selectPumpMaster() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectPumpMaster());
	}
	/**
	 * 정수장 운전현황 펌프 목록 호출
	 * @return 정수장 운전현황 펌프 목록 데이터
	 */
	@Operation(summary = "정수장 운전현황 펌프 목록", description = "selectDrvnPumpMaster")
	@GetMapping("/selectDrvnPumpMaster")
	public ResponseObject < List < HashMap < String, Object >>> selectDrvnPumpMaster() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectDrvnPumpMaster());
	}
	/**
	 * 전력 사용량 및 예측값 조회 (쿼리 기반)
	 * @param map 필터 조건
	 * @return 전력 사용량 및 예측값 데이터
	 */
	@Operation(summary = "전력 사용량, 예측값 조회(쿼리버전) PUMP_CTR_TYP 필요", description = "pumpPrdctSelectList")
	@GetMapping("/selectPwrPrdctList")
	public ResponseObject < List < HashMap < String, Object >>> selectPwrPrdctList(@RequestParam HashMap < String, Object > map) {

		//		if(wpp_code.matches("hy|ji")){
		//			return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpPrdctSelectList(map)); //LSTM
		//		}else{
		//		}

		if(wpp_code.equals("gs"))
		{
			return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpPrdctCalSelectListPwi()); //cal Ver
		}
		else {
			return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpPrdctCalSelectList()); //cal Ver
		}


		//return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectPwrPrdctList(map, 6)); // INIT Ver
	}

    /*
    	@Operation(summary = "전력 사용량, 예측값 조회", description = "peakSelect?date=2023-03-15")
    		@GetMapping("/selectPwrPrdctList_org")
    		public ResponseObject<List<HashMap<String, Object>>> selectPwrPrdctList_org(@RequestParam HashMap<String, Object> map) {
    			//List<HashMap<String, Object>> tempPrdctList = aiService.peakSelect(map);

    			List<HashMap<String, Object>> tempPrdctPumpList = aiService.pumpUsageList();

    			HashMap<String, Object> pumpPrdctPwrSumMap = new HashMap<>();

    			for(HashMap<String, Object> pumpItem : tempPrdctPumpList) {
    				HashMap<String, Object> param = new HashMap<>();
    				System.out.println("PUMP_GRP:" + pumpItem.get("PUMP_GRP"));
    				param.put("pump_grp", pumpItem.get("PUMP_GRP"));
    				System.out.println("param:" + param.toString());
    				List<HashMap<String, Object>> tempPumpList = aiService.pumpPrdctSelect(param);
    				System.out.println("tempPumpList:" + tempPumpList.toString());

    				for (HashMap<String, Object> pumpPrdctItem : tempPumpList) {
    					double nowPrdctPumpPwr = Double.parseDouble(pumpPrdctItem.get("PWR_PRDCT").toString());
    					System.out.println("pumpPrdctItem.get(\"PRDCT_TIME\").toString():"+pumpPrdctItem.get("PRDCT_TIME").toString());
    					if (pumpPrdctPwrSumMap.containsKey(pumpPrdctItem.get("PRDCT_TIME").toString())) {
    						double all = Double.parseDouble(pumpPrdctPwrSumMap.get(pumpPrdctItem.get("PRDCT_TIME").toString()).toString());
    						pumpPrdctPwrSumMap.put(pumpPrdctItem.get("PRDCT_TIME").toString(), all + nowPrdctPumpPwr);
    					} else {
    						pumpPrdctPwrSumMap.put(pumpPrdctItem.get("PRDCT_TIME").toString(), nowPrdctPumpPwr);
    					}
    				}
    			}


    			System.out.println("pumpPrdctPwrSumMap:"+pumpPrdctPwrSumMap.toString());

    			//selectHourPwrList
    			List<HashMap<String, Object>> tempPwrAvgHourList = aiService.selectHourAvgPwrList(map);
    			List<HashMap<String, Object>> tempPwrHourList = aiService.selectHourPwrList(map);

    			List<HashMap<String, Object>> tempResultList = new ArrayList<>();

    			System.out.println("tempPwrAvgHourList:"+tempPwrAvgHourList.toString());
    			System.out.println("tempPwrHourList:"+tempPwrHourList.toString());

    			for(int i=0; i < tempPwrAvgHourList.size(); i++)
    			{
    				for (String key : pumpPrdctPwrSumMap.keySet()) {
    					if(tempPwrAvgHourList.get(i).containsKey(key))
    					{
    						double nowPwr = Double.parseDouble(tempPwrAvgHourList.get(i).get("PWR").toString());
    						double pumpPwr = Double.parseDouble(pumpPrdctPwrSumMap.get(key).toString());
    						double pwr = nowPwr - pumpPwr;
    						tempPwrAvgHourList.get(i).put("PRDCT_PWR", ( pwr * 0.75)  + pumpPwr);
    					}
    				}
    			}

    			for(HashMap<String, Object> item : tempPwrHourList)
    			{
    				for(HashMap<String, Object> prdct_item : tempPwrAvgHourList)
    				{
    					String[] tempTimeStr = item.get("DATE").toString().split(" ");
    					if(tempTimeStr[1].equals(prdct_item.get("DATE").toString()))
    					{
    						HashMap<String, Object> resultItem = new HashMap<>();
    						resultItem.put("DATE", item.get("DATE"));
    						resultItem.put("PWR", Double.parseDouble(item.get("PWR").toString()));
    						resultItem.put("PRDCT_PWR", Double.parseDouble(prdct_item.get("PWR").toString()));
    						tempResultList.add(resultItem);
    					}
    				}
    			}

    			return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, tempResultList);
    		}

    */
	/**
	 * 전력 사용량 및 예측값 조회 (알고리즘 X)
	 * @param map 필터 조건
	 * @return 전력 사용량 및 예측값 데이터
	 */
	@Operation(summary = "전력 사용량, 예측값 조회(알고리즘X)", description = "peakSelect?date=2023-03-15")
	@GetMapping("/selectPwrPrdctList_new")
	public ResponseObject < List < HashMap < String, Object >>> selectPwrPrdctList_new(@RequestParam HashMap < String, Object > map) {
		List < HashMap < String, Object >> tempPrdctList = aiService.selectHourPwrPrdctList(map);
		List < HashMap < String, Object >> tempPwrHourList = aiService.selectHourPwrList(map, 6);

		List < HashMap < String, Object >> tempResultList = new ArrayList < > ();

		for (HashMap < String, Object > prdctItem: tempPrdctList) {
			System.out.println("before prdctItem " + prdctItem.toString());
			double pOrgPWR = Double.parseDouble(prdctItem.get("PWR").toString());

			prdctItem.put("PRDCT_PWR", String.valueOf(pOrgPWR * 0.88));
			prdctItem.put("GNRTD_PWR", String.valueOf(pOrgPWR * 0.98));
			prdctItem.remove("PWR");
			for (HashMap < String, Object > pwrItem: tempPwrHourList) {
				String prdctTime = prdctItem.get("DATE").toString();
				String pwrTime = pwrItem.get("DATE").toString();
				double orgPWR = Double.parseDouble(pwrItem.get("PWR").toString());
				//System.out.println("orgPWR:"+orgPWR);
				String nowTime = pwrTime.split(" ")[1];
				double prdctTemp = 0.88;
				double gntrdTemp = 0.98;
				if (prdctTime.equals(pwrTime)) {
					if (nowTime.equals("13:00") || nowTime.equals("15:00") ||
							nowTime.equals("06:00") || nowTime.equals("18:00")) {
						prdctTemp = 1.06;
						gntrdTemp = 1.02;
					} else if (nowTime.equals("02:00") || nowTime.equals("04:00") ||
							nowTime.equals("10:00") || nowTime.equals("23:00")) {
						prdctTemp = 0.93;
						gntrdTemp = 0.95;
					}

					prdctItem.put("DATE", pwrItem.get("DATE").toString());
					prdctItem.put("PWR", pwrItem.get("PWR").toString());
					prdctItem.put("PRDCT_PWR", String.valueOf(orgPWR * prdctTemp));
					prdctItem.put("GNRTD_PWR", String.valueOf(orgPWR * gntrdTemp));
					prdctItem.put("PEAK_YN", 0);
				}
			}
			tempResultList.add(prdctItem);
			System.out.println("after prdctItem " + prdctItem.toString());
		}
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, tempResultList);
	}
	/**
	 * 용소수요 예측 펌프 그룹 데이터 호출
	 * @return 예측 펌프 그룹 데이터
	 */
	@Operation(summary = "용소수요 예측 펌프 그룹 데이터", description = "ai/pumpUsageList")
	@GetMapping("/pumpUsageList")
	public ResponseObject < List < HashMap < String, Object >>> pumpUsageList() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpUsageList());
	}
	/**
	 * 펌프 가동 조합 예측 펌프 그룹 데이터 호출
	 * @return 가동 조합 예측 펌프 그룹 데이터
	 */
	@Operation(summary = "펌프가동조합 예측 펌프 그룹 데이터", description = "ai/pumpUsageList")
	@GetMapping("/pumpUsageYnList")
	public ResponseObject < List < HashMap < String, Object >>> pumpUsageYnList() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpUsageYnList());
	}

	/**
	 * AI 상태 펌프 그룹 데이터 호출
	 * @return AI 상태 펌프 그룹 데이터
	 */
	@Operation(summary = "AI상태 펌프 그룹 데이터", description = "ai/selectAiStatus")
	@GetMapping("/selectAiStatus")
	public ResponseObject < List < HashMap < String, Object >>> selectAiStatus() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectAiStatus());
	}
	/**
	 * AI 상태 펌프 그룹 업데이트 요청
	 * @param map 업데이트 요청 데이터
	 * @return 업데이트 요청 성공 여부
	 */
	@Operation(summary = "AI상태 펌프 그룹 업데이트", description = "ai/updateAiStatus")
	@PostMapping("/updateAiStatusTemp")
	public ResponseObject < String > updateAiStatusTemp(@RequestBody HashMap < String, Object > map) {
		if (isRunning.compareAndSet(false, true)) {
			aiService.updateAiStatusTemp(map).thenAccept(status -> {
				if (status == 0) {
					System.out.println("AI 상태 업데이트 성공");
				} else {
					System.out.println("AI 상태 업데이트 실패 - " + status);
				}
				isRunning.set(false);
			});
			return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "AI 상태 업데이트 요청 수신됨");
		} else {
			return makeSuccessObj(ResponseMessage.INSERT_FAILURE, "AI 상태 업데이트 실패 - 지난 요청이 실행중");
		}
	}
	/**
	 * AI 상태 펌프 그룹 업데이트
	 * @param map 업데이트 데이터
	 * @return 업데이트 성공 여부
	 */
	@PostMapping("/updateAiStatus")
	public ResponseObject < String > updateAiStatus(@RequestBody HashMap < String, Object > map) {
		aiService.updateAiStatus(map);
		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "AI 상태 업데이트 요청 수신됨");
	}
	/**
	 * 비상 사용 데이터 호출
	 * @return 비상 사용 데이터
	 */
	@GetMapping("/getEmergencyUse")
	public ResponseObject < List < HashMap < String, Object >>> getEmergencyUse() {
		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, aiService.getEmergencyUse());
	}
	/**
	 * AI 펌프 EMS 데이터 호출
	 * @param map 요청 데이터 필터
	 * @return AI 펌프 EMS 데이터
	 */
	@GetMapping("/aiPumpEMSData")
	public ResponseObject < List < HashMap < String, Object >>> aiPumpEMSData(@RequestParam HashMap < String, Object > map) {
		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, aiService.aiPumpEMSData(map));
	}
	/**
	 * 배수지 최소관압 데이터 호출
	 * @return 배수지 최소관압 데이터
	 */
	@GetMapping("/getTnkMinPri")
	public ResponseObject < List < HashMap < String, Object >>> getTnkMinPri() {
		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, aiService.getTnkMinPri());
	}
	/**
	 * 펌프 AI 사용량 데이터 호출
	 * @return 펌프 AI 사용량 데이터
	 */
	@GetMapping("/getPumpAiUsage")
	public ResponseObject < List < HashMap < String, Object >>> getPumpAiUsage() {
		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, aiService.getPumpAiUsage());
	}
	/**
	 * AI 펌프 데이터 호출
	 * @param map 요청 데이터 필터
	 * @return AI 펌프 데이터
	 */
	@GetMapping("/selectAIPumpData")
	public ResponseObject < List < HashMap < String, Object >>> selectAIPumpData(@RequestParam HashMap < String, Object > map) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectAIPumpData(map));
	}
	/**
	 * 펌프 제어 명령 전송
	 * @param map 제어 명령 데이터
	 * @return 명령 전송 성공 여부
	 */
	@GetMapping("/pumpCommand")
	public ResponseObject < String > pumpCommand(@RequestParam HashMap < String, Object > map) {
		//System.out.println("pumpCommand map:"+map.toString());
		if (wpp_code.equals("ba")) {
			if (map.containsKey("pump_grp")) {
				String str = map.get("pump_grp").toString();
				//System.out.println("str:"+str);
				if (str.contains("4")) {
					str += ",5";
					map.put("pump_grp", str);
				}
			}
		}
		//System.out.println("map:"+map.toString());
		aiService.pumpCommand(map);
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, "펌프 제어 명령 전송 성공");
	}

	@GetMapping("/pumpCommandAI")
	public ResponseObject < String > pumpCommandAI(@RequestParam HashMap < String, Object > map) {
		//System.out.println("pumpCommand map:"+map.toString());
		if (wpp_code.equals("ba")) {
			if (map.containsKey("pump_grp")) {
				String str = map.get("pump_grp").toString();
				//System.out.println("str:"+str);
				if (str.contains("4")) {
					str += ",5";
					map.put("pump_grp", str);
				}
			}
		}
		//System.out.println("map:"+map.toString());
		aiService.pumpCommandAI(map);
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, "펌프 제어 명령 전송 성공");
	}
	/**
	 * 펌프 제어 상태 조회
	 * @return 펌프 제어 상태 데이터
	 */
	@GetMapping("/pumpCommandStatus")
	public ResponseObject < HashMap < String, Object >> pumpCommandStatus() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpCommandStatus());
	}
	/**
	 * AI 제어 상태 조회
	 * @return AI 제어 상태 데이터
	 */
	@GetMapping("/pumpCommandAiControlStatus")
	public ResponseObject < HashMap < String, Object >> pumpCommandAiControlStatus() {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpCommandAiControlStatus());
	}
	/**
	 * 펌프 변경 상태 조회
	 * @param map 펌프 변경 상태 조건
	 * @return 펌프 변경 상태 데이터
	 */
	@GetMapping("/pumpChangeStatus")
	public ResponseObject < HashMap < String, Object >> pumpChangeStatus(@RequestParam HashMap < String, Object > map) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpChangeStatus(map));
	}
	/**
	 * 실제 AI 모드에서 펌프 변경 상태 조회
	 * @param map 펌프 변경 상태 조건
	 * @return 펌프 변경 상태 데이터
	 */
	@GetMapping("/pumpChangeStatusAIMode")
	public ResponseObject < HashMap < String, Object >> pumpChangeStatusAIMode(@RequestParam HashMap < String, Object > map) {
		map.put("mode", "real");
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpChangeStatusAIModeGs(map));
	}
	/**
	 * 테스트 AI 모드에서 펌프 변경 상태 조회
	 * @param map 펌프 변경 상태 조건
	 * @return 펌프 변경 상태 데이터
	 */
	@GetMapping("/pumpChangeStatusAIModeTest")
	public ResponseObject < HashMap < String, Object >> pumpChangeStatusAIModeTest(@RequestParam HashMap < String, Object > map) {
		map.put("mode", "test");
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.pumpChangeStatusAIModeGs(map));
	}
	/**
	 * 펌프 제어 이력 목록 호출
	 * @param map 필터 조건
	 * @return 펌프 제어 이력 목록
	 */
	@GetMapping("/selectPumpCtrHistoryList")
	public ResponseObject < List < HashMap < String, Object >>> selectPumpCtrHistoryList(@RequestParam HashMap < String, Object > map) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectPumpCtrHistoryList(map));
	}
	/**
	 * 펌프 제어 이력 전체 개수 조회
	 * @param map 필터 조건
	 * @return 펌프 제어 이력 개수
	 */
	@GetMapping("/selectPumpCtrHistoryListAllCount")
	public ResponseObject < HashMap < String, Object >> selectPumpCtrHistoryListAllCount(@RequestParam HashMap < String, Object > map) {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.selectPumpCtrHistoryListAllCount(map));
	}
	/**
	 * 특정 시점의 예측 전력 계산
	 * @param map 날짜와 시간 조건
	 * @return 계산된 예측 전력 데이터
	 */
	@GetMapping("/calPrdctPwr")
	public ResponseObject < List < HashMap < String, Object >>> calPrdctPwr(@RequestParam HashMap < String, Object > map) {

		String dateText = map.get("date").toString();
		String hour = map.get("hour").toString();
		String hourText = hour;
		if (hour.length() == 1) {
			hourText = "0" + hour;
		}
		String date = dateText + " " + hourText + ":00:00";
		aiService.CalPrdctPwr(date);

		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, null);
	}
	/**
	 * 특정 범위의 예측 전력 계산
	 * @param map 시작 날짜, 종료 날짜 조건
	 * @return 계산된 예측 전력 데이터
	 * @throws ParseException 파싱 예외 처리
	 */
	@GetMapping("/calPrdctPwrRange")
	public ResponseObject < List < HashMap < String, Object >>> calPrdctPwrRange(@RequestParam HashMap < String, Object > map) throws ParseException {

		String sdate = map.get("sdate").toString();
		String edate = map.get("edate").toString();

		SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd");
		SimpleDateFormat dateTimeFormat = new SimpleDateFormat("yyyy-MM-dd HH");

		Date startDate = dateFormat.parse(sdate);
		Date endDate = dateFormat.parse(edate);

		// sdate가 edate보다 큰 경우 서로 교환
		if (startDate.after(endDate)) {
			Date temp = startDate;
			startDate = endDate;
			endDate = temp;
		}

		// 현재 날짜와 시간을 가져옴
		Date now = new Date();

		Calendar calendar = Calendar.getInstance();
		calendar.setTime(startDate);

		Calendar endCalendar = Calendar.getInstance();
		endCalendar.setTime(endDate);

		Calendar nowCalendar = Calendar.getInstance(); // 현재 시스템 시간을 사용

		// 만약 edate가 현재 시스템 날짜와 동일하다면 nowHour를 현재 시간으로 설정
		int nowHour = 23; // 기본값으로 하루의 마지막 시간 설정
		if (dateFormat.format(endDate).equals(dateFormat.format(now))) {
			nowHour = nowCalendar.get(Calendar.HOUR_OF_DAY);
		}

		List < String > dateTimeList = new ArrayList < > ();

		while (!calendar.getTime().after(endDate)) {
			String currentDateStr = dateFormat.format(calendar.getTime());
			for (int hour = 0; hour < 24; hour++) {
				// 날짜가 같고 시간이 넘어가면 루프를 종료
				if (currentDateStr.equals(dateFormat.format(endDate)) && hour > nowHour) {
					break; // 현재 날짜이면서 현재 시간보다 크면 중단
				}
				calendar.set(Calendar.HOUR_OF_DAY, hour);
				dateTimeList.add(dateTimeFormat.format(calendar.getTime()) + ":00:00");
			}
			calendar.add(Calendar.DATE, 1);
			calendar.set(Calendar.HOUR_OF_DAY, 0); // 다음 날로 넘어갈 때 시간을 00:00으로 설정
		}

		for (String dateTime: dateTimeList) {
			System.out.println(dateTime);
			aiService.CalPrdctPwr(dateTime);
		}
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, null);
	}

	@GetMapping("/calPrdctPwrRangePwi")
	public ResponseObject < List < HashMap < String, Object >>> calPrdctPwrRangePwi(@RequestParam HashMap < String, Object > map) throws ParseException {

		String sdate = map.get("sdate").toString();
		String edate = map.get("edate").toString();

		SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd");
		SimpleDateFormat dateTimeFormat = new SimpleDateFormat("yyyy-MM-dd HH");

		Date startDate = dateFormat.parse(sdate);
		Date endDate = dateFormat.parse(edate);

		// sdate가 edate보다 큰 경우 서로 교환
		if (startDate.after(endDate)) {
			Date temp = startDate;
			startDate = endDate;
			endDate = temp;
		}

		// 현재 날짜와 시간을 가져옴
		Date now = new Date();

		Calendar calendar = Calendar.getInstance();
		calendar.setTime(startDate);

		Calendar endCalendar = Calendar.getInstance();
		endCalendar.setTime(endDate);

		Calendar nowCalendar = Calendar.getInstance(); // 현재 시스템 시간을 사용

		// 만약 edate가 현재 시스템 날짜와 동일하다면 nowHour를 현재 시간으로 설정
		int nowHour = 23; // 기본값으로 하루의 마지막 시간 설정
		if (dateFormat.format(endDate).equals(dateFormat.format(now))) {
			nowHour = nowCalendar.get(Calendar.HOUR_OF_DAY);
		}

		List < String > dateTimeList = new ArrayList < > ();

		while (!calendar.getTime().after(endDate)) {
			String currentDateStr = dateFormat.format(calendar.getTime());
			for (int hour = 0; hour < 24; hour++) {
				// 날짜가 같고 시간이 넘어가면 루프를 종료
				if (currentDateStr.equals(dateFormat.format(endDate)) && hour > nowHour) {
					break; // 현재 날짜이면서 현재 시간보다 크면 중단
				}
				calendar.set(Calendar.HOUR_OF_DAY, hour);
				dateTimeList.add(dateTimeFormat.format(calendar.getTime()) + ":00:00");
			}
			calendar.add(Calendar.DATE, 1);
			calendar.set(Calendar.HOUR_OF_DAY, 0); // 다음 날로 넘어갈 때 시간을 00:00으로 설정
		}

		for (String dateTime: dateTimeList) {
			System.out.println(dateTime);
			aiService.CalPrdctPwrPwi(dateTime);
		}
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, null);
	}

	/**
	 * 펌프 중단
	 * @param map 중단 조건
	 * @return 중단 성공 여부
	 * @throws ParseException 파싱 예외 처리
	 */
	@GetMapping("/pumpStop")
	public ResponseObject < List < HashMap < String, Object >>> pumpStop(@RequestParam HashMap < String, Object > map) throws ParseException {

		aiService.pumpStop();
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, null);
	}
	/**
	 * 펌프 시작
	 * @param map 시작 조건
	 * @return 시작 성공 여부
	 * @throws ParseException 파싱 예외 처리
	 */
	@GetMapping("/pumpStart")
	public ResponseObject < List < HashMap < String, Object >>> pumpStart(@RequestParam HashMap < String, Object > map) throws ParseException {

		aiService.pumpStart(map);
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, null);
	}

	@GetMapping("/aiModeRecordUpdate")
	public ResponseObject < List < HashMap < String, Object >>> aiModeRecordUpdate(@RequestParam HashMap < String, Object > map) throws ParseException {

		String pump_grp = map.get("pump_grp").toString();
		String runDate = map.get("date").toString();

		int updateCount = 0;
		int insertCount = 0;

		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");

		// LocalDateTime 설정
		LocalDate startDate = LocalDate.parse(runDate, formatter);
		LocalDateTime startDateTime = startDate.atStartOfDay();

		LocalDateTime currentTime = LocalDateTime.now();
		HashMap<String,String> recordLastItem = new HashMap<>();
		for (LocalDateTime date = startDateTime; date.isBefore(currentTime) || date.isEqual(currentTime); date = date.plusMinutes(1)) {
			String CheckDateTime = date.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:00.000"));
			HashMap<String, String> itemParam = new HashMap<>();
			itemParam.put("pump_grp", pump_grp);
			itemParam.put("#aiModeRecordUpdate date", CheckDateTime);

			HashMap<String,String> recordItem = aiService.selectAiModeRstItem(itemParam);

			if(recordItem != null)
			{
				//System.out.println("#CheckDateTime:"+CheckDateTime +" => "+recordItem.toString());
				HashMap<String, String> drvnParam = new HashMap<>();
				drvnParam.put("NOW_DATE", recordItem.get("RGSTR_TIME").toString());
				drvnParam.put("PUMP_GRP", pump_grp);
				drvnParam.put("nowDate", runDate);
				drvnParam.put("pump_grp", pump_grp);
				HashMap<String, String> pumpDrvnMap = aiService.pumpDrvnMinute(drvnParam);

				HashMap<String, String> aiStatusPumpComb = aiService.createPumpCombStatus(pumpDrvnMap, pump_grp);

				String curPumpStr = aiStatusPumpComb.get("curPump");
				String prePumpStr = aiStatusPumpComb.get("prePump");
				if(curPumpStr.equals(prePumpStr))
				{
					drvnParam.put("IS_WORK", "1");
				}
				else {
					drvnParam.put("IS_WORK", "0");
				}
				drvnParam.put("PRE_PUMP", prePumpStr);
				drvnParam.put("CUR_PUMP", curPumpStr);
				drvnParam.put("prePump", prePumpStr);
				drvnParam.put("curPump", curPumpStr);
				drvnParam.put("AI_MODE", recordItem.get("AI_MODE"));
				drvnParam.put("flow_ctr", recordItem.get("FLOW_CTR"));

				aiService.updateAiModeRst(drvnParam);
				recordLastItem = new HashMap<>(drvnParam);
				updateCount++;
			}
			else {
				if(!recordLastItem.isEmpty())
				{
					//System.out.println("#CheckDateTime:"+CheckDateTime+" INSERT" + recordLastItem.toString());
					recordLastItem.put("RGSTR_TIME", CheckDateTime);
					recordLastItem.put("flow_ctr", "None2");
					//commonService.insertAiStatusRST(recordLastItem);
					insertCount++;
				}
			}
		}

		map.put("u_count", updateCount);
		map.put("i_count", insertCount);

		List<HashMap<String,Object>> result = new ArrayList<>();
		result.add(map);
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, result);
	}

	@Operation(summary = "송수펌프 제어이력 모드별 카운팅", description = "전체 및 각 모드(ai, 추천, 분석) 별 기간내 갯수 반환")
	@GetMapping("/getAiModeCount")
	public ResponseObject<HashMap<String, Integer>> getAiModeCount(@RequestParam HashMap<String, Object> param){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, aiService.getAiModeCount(param));
	}
}