package kr.co.mindone.ems.drvn;
/**
 * packageName    : kr.co.mindone.ems.drvn
 * fileName       : DrvnService
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import kr.co.mindone.ems.ai.AiMapper;
import kr.co.mindone.ems.ai.AiService;
import kr.co.mindone.ems.common.holiday.HolidayChecker;
import kr.co.mindone.ems.pump.PumpService;
import kr.co.mindone.ems.setting.SettingMapper;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.ss.util.CellRangeAddress;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.lang.reflect.Type;
import java.math.BigDecimal;
import java.sql.Timestamp;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.DayOfWeek;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

import static kr.co.mindone.ems.drvn.DrvnConfig.*;

@Service
@Profile("!gm & !hp & !ji & !hy & !ss & !gm2 & !hp2 & !hy2 & !ji2" )
@Slf4j
public class DrvnService {
	private static final Logger logger = LoggerFactory.getLogger(DrvnService.class);

	@Autowired
	private DrvnMapper drvnMapper;

	@Autowired
	private PumpService pumpService;

	@Autowired
	private AiService aiervice;

	@Autowired
	private AiMapper aiMapper;

	@Autowired
	DrvnConfig drvnConfig;
	@Value("${dstrb.headLoss.cal}")
	private String headLossJson;
	@Value("${dstrb.headLoss.grp}")
	private String headLossGrp;
	@Value("${dstrb.prdct.pwrCal.idx}")
	private String prdctPwrIdxVal;
	@Value("${dstrb.pump.level}")
	private String pumpLevel;
	@Value("${dstrb.prdct.pumpDstrbId}")
	private String pumpDstrbId;
	@Value("${dstrb.prdct.pwrCal.calVal}")
	private String prdctPwrCalVal;
	@Value("${dstrb.prdct.dstrbId}")
	private String dstrbId;
	@Value("${dstrb.optidx}")
	String optIdxTag;
	@Value("${dstrb.headLoss.flow}")
	private String headLossFlow;
	@Value("${dstrb.excel.notSrttn}")
	private String notSrttn;

	@Value("${dstrb.prdct.pumpComb.target.max.down}")
	private String pumpCombTargetMax;
	@Value("${dstrb.prdct.pumpComb.target.max.up}")
	private String pumpCombTargetMaxUp;
	@Value("${dstrb.prdct.pumpComb.target.min}")
	private String pumpCombTargetMin;
	@Value("${dstrb.prdct.pumpComb.target.level}")
	private String pumpCombTargetLevel;

	// 운전현황 성능곡선이 참조하는 관망해석 링크/노드 ID (현장별로 다르다)
	// 기본값은 고산(link 10 / node 고산(정)유출). 군산은 45 / Bks-2496 이라
	// application-gu.properties 에서 덮어쓴다.
	@Value("${dstrb.resistance.linkId:10}")
	private String resistanceLinkId;
	@Value("${dstrb.resistance.nodeId:고산(정)유출}")
	private String resistanceNodeId;

	private HashMap<Integer, HashMap<String, Double>> headLossMap;
	@Getter
	private HashMap<Integer, HashMap<String, List<String>>> headLossGrpMap;
	private HashMap<Integer, HashMap<String, Double>> prdctPwrCalValMap;
	private HashMap<Integer, HashMap<Integer, Double>> prdctPwrIdxValMap;
	private HashMap<Integer, HashMap<Integer, Double>> pumpLevelInfoGrpMap;
	private LinkedHashMap<Integer, HashMap<String, String>> pumpDstrbIdMap;
	private HashMap<String, List<String>> dstrbIdMap;
	@Getter
	private HashMap<Integer, HashMap<String, List<String>>> headLossFlowIdMap;
	private HashMap<String, List<String>> notSrttnMap;


	private List<HashMap<String, Object>> calList;
	private List<HashMap<String, Object>> setPumpList;
	private HashMap<Integer, HashMap<String, Double>> pumpCombTargetMap;
	private HashMap<Integer, HashMap<String, Double>> pumpCombTargetMapUp;
	private HashMap<Integer, HashMap<String, Double>> pumpCombTargetMapMin;
	private HashMap<Integer, HashMap<String, Double>> pumpCombTargetLevelMap;
	private HashMap<Integer, HashMap<Integer, String>> reduceMap;
	private String opt_idx;
	@Value("${spring.profiles.active}")
	private String wpp_code;
	private int setMonth;

	/**
	 * 운전현황 properties 값
	 * Json -> HashMap 파싱 메서드
	 */
	@PostConstruct
	public void setIntegerDobleMap(){
		LocalDateTime currentTimeSetMonth = LocalDateTime.now();
		setMonth = currentTimeSetMonth.getMonthValue();
		reduceMap = drvnConfig.getMonthPwrReduc();
		Gson gson = new Gson();
		Type doubleType = new TypeToken<HashMap<Integer, HashMap<String, Double>>>(){}.getType();
		Type intStrDoubleType = new TypeToken<HashMap<Integer, HashMap<Integer, Double>>>(){}.getType();

		Type linkedStrType = new TypeToken<LinkedHashMap<Integer, HashMap<String, String>>>(){}.getType();
		Type arrType = new TypeToken<HashMap<Integer, HashMap<String, List<String>>>>(){}.getType();
		Type strArrType = new TypeToken<HashMap<String, List<String>>>(){}.getType();

		notSrttnMap = gson.fromJson(notSrttn, strArrType);
		headLossMap = gson.fromJson(headLossJson, doubleType);
		prdctPwrCalValMap = gson.fromJson(prdctPwrCalVal, doubleType);
		pumpLevelInfoGrpMap = gson.fromJson(pumpLevel, intStrDoubleType);
		pumpDstrbIdMap = gson.fromJson(pumpDstrbId, linkedStrType);
		dstrbIdMap = gson.fromJson(dstrbId, strArrType);
		headLossFlowIdMap = gson.fromJson(headLossFlow, arrType);
		headLossGrpMap = gson.fromJson(headLossGrp, arrType);
		prdctPwrIdxValMap = gson.fromJson(prdctPwrIdxVal, intStrDoubleType);
		calList = drvnMapper.selectPumpCombCal();
		setPumpList = aiMapper.selectPumpList();
		pumpCombTargetMap = gson.fromJson(pumpCombTargetMax, doubleType);
		pumpCombTargetMapUp = gson.fromJson(pumpCombTargetMaxUp, doubleType);
		pumpCombTargetMapMin = gson.fromJson(pumpCombTargetMin, doubleType);
		pumpCombTargetLevelMap = gson.fromJson(pumpCombTargetLevel, doubleType);
		opt_idx = optIdxTag;

	}

	@Autowired
	SettingMapper settingMapper;
	/**
	 * 수두손실저항 압력값 계산 메서드
	 * @param headLossVal 수두손실저항값
	 * @param pump_grp 펌프그룹
	 * @param grpStr 저항곡선그룹
	 * @return 저항압력값
	 */
	public double getH(Double headLossVal, int pump_grp, String grpStr){
		double getHeadLossCal = headLossMap.get(pump_grp).get(grpStr);

		return (headLossVal / 10) + getHeadLossCal;
	}

	/**
	 * 성능곡선 그래프 데이터 반환 API
	 * @param param 날짜 및 데이터 종류, 펌프 그룹
	 * @return 성능곡선 그래프 데이터
	 */
	public List<HashMap<String, Object>> systemResistanceCurves(HashMap<String, Object> param) {
		String opt_idx = (String) param.get("opt_idx");
		//펌프 그룹에 대응되는 수두손실 그룹 데이터 Map 호출
		List<HashMap<String, Object>> returnList = new ArrayList<>();
		param.put("link_id", resistanceLinkId);
		param.put("node_id", resistanceNodeId);
		if(opt_idx.equals("cur")){
			returnList.addAll(systemCurResistanceCurves(param));
		}else if(opt_idx.equals("pre")) {
			returnList.addAll(systemPreResistanceCurves(param));
		}

		return returnList;
	}
	
	public HashMap<String, Object> getPumpComb() {
		return drvnMapper.selectPumpComb();
	}

	/**
	 * 성능곡선 실측 그래프 데이터 반환 메서드
	 * @param param 날짜 및 데이터 종류, 펌프 그룹
	 * @return 성능곡선 실측 그래프 데이터
	 */
	public List<HashMap<String, Object>> systemCurResistanceCurves(HashMap<String, Object> param){
		param.put("intradotion", false);
		int pump_grp = (Integer) param.get("pump_grp");
		String opt_idx = (String) param.get("opt_idx");

		List<HashMap<String, Object>> returnList = new ArrayList<>();


		if(pump_grp !=0){

			param.put("first", false);
			List<HashMap<String, Object>> pressureList;


			pressureList = drvnMapper.selectPumpPressure(param);

			List<HashMap<String, Object>> flowList = drvnMapper.selectPumpFlow(param);
			int minSize = Math.min(pressureList.size(), flowList.size());
			for(int i = 0; i < minSize; i++){
				HashMap<String, Object> returnMap = new HashMap<>();
				HashMap<String, Object> pressureMap = pressureList.get(i);
				HashMap<String, Object> flowMap = flowList.get(i);
				String date = (String) pressureMap.get("ts");
				String pressureStr = (String) pressureMap.get("value");
				double pressure = Double.parseDouble(pressureStr);
				String flowStr = (String) flowMap.get("value");
				double flow = Double.parseDouble(flowStr);

				returnMap.put("flow", flow);
				returnMap.put("pressure", pressure);
				returnMap.put("date", date);
				returnList.add(returnMap);
			}

			if(headLossGrpMap.containsKey(pump_grp)){

				if(!headLossGrpMap.get(pump_grp).isEmpty()){

					Set<String> grp_nm = headLossGrpMap.get(pump_grp).keySet();
					for(String grp_str:grp_nm){
						List<String> headLossFlowId = headLossFlowIdMap.get(pump_grp).get(grp_str);

						List<Double> headLossFlow = new ArrayList<>();
						if(headLossFlowId != null && !headLossFlowId.isEmpty()){
							param.put("dstrbList", headLossFlowId);
							headLossFlow = drvnMapper.selectHeadLossTargetCurFlow(param);

						}

						//수두손실 그룹에 대응되는 수두그룹 리스트 할당
						List<String> grpList = headLossGrpMap.get(pump_grp).get(grp_str);
						param.put("grpList", grpList);


						//수두손실 그룹
						param.put("GRP_NM", grp_str);

						//과거데이터 데이터
//						List<Double> selectHeadLoss = drvnMapper.selectForHeadLoss(param);
						if(!returnList.isEmpty()){

							for(int i=0;i<returnList.size();i++){
//								Double headLossMap = selectHeadLoss.get(i);
								HashMap<String, Object> flowMap = flowList.get(i);
								String flowStr = (String) flowMap.get("value");
								double flow = Double.parseDouble(flowStr);
								double forHeadLossFlow = 0;
								if(!headLossFlow.isEmpty()){
									forHeadLossFlow = headLossFlow.get(i);
								}
//								Double forGetHeadLoss = headLossMap;
//								double forH = getH(forGetHeadLoss, pump_grp, grp_str);

//								returnList.get(i).put("flow_"+grp_str, flow - forHeadLossFlow);
//								returnList.get(i).put(grp_str, forH);
							}
						}

					}
				}
			}


			// 마지막 Data
			param.put("first", true);
			List<HashMap<String, Object>> pressureListFirst;

			pressureListFirst = drvnMapper.selectPumpPressure(param);

			List<HashMap<String, Object>> flowListFirst = drvnMapper.selectPumpFlow(param);

			// 기준시각 직전 1주기에 실측이 한 건도 없으면(수집 중단·덤프 DB 등) 현재값 구간을 건너뛴다.
			// 아래 firstMap 구성과 수두손실 보정이 모두 이 두 리스트의 0번을 전제로 하기 때문이다.
			if(pressureListFirst.isEmpty() || flowListFirst.isEmpty()){
				return returnList;
			}

			List<HashMap<String, Object>> selectNowPumpUse = drvnMapper.selectNowPumpUse(param);
			HashMap<Integer, Double> nowPwrMap = new HashMap<>();
			List<HashMap<String, Object>> selectNowPumpPwrUse = drvnMapper.selectNowPumpPwrUse(param);
			for (HashMap<String, Object> pwrMap : selectNowPumpPwrUse) {
				int pump_idx = (int) pwrMap.get("PUMP_GRP_IDX");
				double pumpPwr = (double) pwrMap.get("value");
				nowPwrMap.put(pump_idx, pumpPwr);
			}

			List<String> curPumpUse = new ArrayList<>();
			double returnNowPwr = 0;
			boolean freqWmPump = false;
			LinkedHashMap<String, Double> freqMap = new LinkedHashMap<>();
			if(wpp_code.equals("wm")){
				for (HashMap<String, Object> pumpUseMap : selectNowPumpUse){
					pumpUseMap.put("PUMP_TYP", 1);
				}
			}
			for (HashMap<String, Object> pumpUseMap : selectNowPumpUse) {
				String strPumpUse = (String) pumpUseMap.get("pump_use");
				double intPumpUse = Double.parseDouble(strPumpUse);
				int pump_typ = (int) pumpUseMap.get("PUMP_TYP");

				if (intPumpUse == 1) {
					int pump_idx = (int) pumpUseMap.get("PUMP_GRP_IDX");
					if(wpp_code.equals("wm") && !freqWmPump){
						if(pump_idx == 1 || pump_idx ==2){
							pump_typ = 2;
							freqWmPump = true;
						} else if (pump_idx == 4) {
							pump_typ = 2;
							freqWmPump = true;
						}
					}
					if(nowPwrMap.containsKey(pump_idx)){
						returnNowPwr += nowPwrMap.get(pump_idx);
					}
					String pump_name = "P#" + pump_idx;
					curPumpUse.add(pump_name);

					if(pump_typ == 2){
						String strFreq = (String) pumpUseMap.get("pump_freq");
						double freq = Double.parseDouble(strFreq);
						if(wpp_code.equals("gr") && pump_grp == 1){
							freqMap.put(pump_name, (double) Math.round(0.6 * freq));

						}else{
							freqMap.put(pump_name, (double) Math.round(freq));

						}
					}

				}
			}
			HashMap<String, Object> pressureFirst = pressureListFirst.get(0);
			HashMap<String, Object> flowFirst = flowListFirst.get(0);
			String date = (String) pressureFirst.get("ts");
			String pressureStr = (String) pressureFirst.get("value");
			String flowStr = (String) flowFirst.get("value");
			double pressure = Double.parseDouble(pressureStr);
			double flow = Double.parseDouble(flowStr);


			HashMap<String, Object> firstMap = new HashMap<>();
			firstMap.put("pumpUse", curPumpUse);
			firstMap.put("pwr", returnNowPwr);
			firstMap.put("flow", flow);
			firstMap.put("pressure", pressure);
			firstMap.put("date", date);
			if(!freqMap.isEmpty()){
				firstMap.put("freq", freqMap);
			}
			returnList.add(firstMap);
			if(headLossGrpMap.containsKey(pump_grp)){

				if(!headLossGrpMap.get(pump_grp).isEmpty()){
					Set<String> grp_nm = headLossGrpMap.get(pump_grp).keySet();
					for(String grp_str:grp_nm){
						List<String> headLossFlowId = headLossFlowIdMap.get(pump_grp).get(grp_str);

						List<Double> headLossFlow = new ArrayList<>();
						if(!headLossFlowId.isEmpty()){
							param.put("dstrbList", headLossFlowId);
							headLossFlow = drvnMapper.selectHeadLossTargetCurFlow(param);

						}

						//수두손실 그룹에 대응되는 수두그룹 리스트 할당
						List<String> grpList = headLossGrpMap.get(pump_grp).get(grp_str);
						param.put("grpList", grpList);


						//수두손실 그룹
						param.put("GRP_NM", grp_str);

						//과거데이터 데이터
						Double selectHeadLoss = drvnMapper.selectHeadLoss(param);

						if(selectHeadLoss != null){

							double forHeadLossFlow = 0;
							if(!headLossFlow.isEmpty()){
								forHeadLossFlow = headLossFlow.get(0);
							}
							double forH = getH(selectHeadLoss, pump_grp, grp_str);

							returnList.get(returnList.size() - 1).put("flow_"+grp_str, flow - forHeadLossFlow);
							returnList.get(returnList.size() -1).put(grp_str, forH);
						}

					}
				}
			}


		}else {
			Set<String> grp_nm = headLossGrpMap.get(pump_grp).keySet();
			param.put("first", false);

			Set<Integer> pumpGrpSet = pumpDstrbIdMap.keySet();


			LinkedHashMap<String, List<HashMap<String, Object>>> dataMap = new LinkedHashMap<>();
			List<String> dateList = new ArrayList<>();

			for(Integer id:pumpGrpSet){
				param.put("pump_grp", id);
				List<HashMap<String, Object>> flow = drvnMapper.selectPumpFlow(param);

				List<HashMap<String, Object>> pressure = drvnMapper.selectPumpPressure(param);

				dataMap.put("flow" + id, flow);
				dataMap.put("pressure" + id, pressure);
				for(HashMap<String, Object> maps : flow){
					dateList.add((String) maps.get("ts"));
				}
			}


			HashMap<String, List<Double>> totalData = drvnConfig.integrateFlowPressCalc(dataMap, "cur");
			List<Double> pressureList = totalData.get("pressure");
			List<Double> selectflowPressure = totalData.get("flow");


			int arrIdx = 1;
			for (String grp_str : grp_nm) {
				param.put("first", false);
				List<String> headLossFlowId = headLossFlowIdMap.get(pump_grp).get(grp_str);
				if (headLossFlowId == null) {
					headLossFlowId = new ArrayList<>();
				}

				List<Double> headLossFlow = new ArrayList<>();
				if (!headLossFlowId.isEmpty()) {
					param.put("dstrbList", headLossFlowId);
				}

				//수두손실 그룹에 대응되는 수두그룹 리스트 할당
				List<String> grpList = headLossGrpMap.get(pump_grp).get(grp_str);


				if (grpList == null) {
					grpList = new ArrayList<>();
				}
				param.put("grpList", grpList);
				param.put("GRP_NM", grp_str);




				// 원본 쿼리 결과 (시간대별 수두손실 값)
//				List<HashMap<String, Object>> rawHeadLossList = drvnMapper.selectForHeadLoss(param);


				List<HashMap<String, Object>> linkValList = drvnMapper.selectGsAllCurLinkRange(param);
				List<HashMap<String, Object>> nodeValList = drvnMapper.selectGsAllCurNodeRange(param);

				// 현황 데이터의 시간 축 길이
				int minSize = Math.min(pressureList.size(), selectflowPressure.size());
				int listToProcess = Math.min(dateList.size(), minSize);


				// 2. rawHeadLossList를 Map<String, Double> 형태로 변환 (빠른 검색용)
				//    dateList의 형식("yyyy-MM-dd HH:mm")에 맞춰 Key를 생성합니다.
				java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm");
				Map<String, Double> linkMap = linkValList.stream()
						.filter(map -> map.containsKey("ts") && map.containsKey("linkVal") && map.get("ts") != null)
						.collect(Collectors.toMap(
								map -> {
									// "ts" 객체를 "yyyy-MM-dd HH:mm" 형식의 문자열로 변환
									Object tsObj = map.get("ts");
									return sdf.format((java.util.Date) tsObj);
								},
								map -> {
									// lossVal을 Double로 안전하게 변환
									Object lossValue = map.get("linkVal");
									if (lossValue instanceof Number) {
										return ((Number) lossValue).doubleValue();
									}
									return 0.0; // 변환 실패 시 0.0
								},
								(existing, replacement) -> existing // 혹시 중복 키가 있다면 기존 값 유지
						));
				Map<String, Double> nodeMap = nodeValList.stream()
						.filter(map -> map.containsKey("ts") && map.containsKey("nodeVal") && map.get("ts") != null)
						.collect(Collectors.toMap(
								map -> {
									// "ts" 객체를 "yyyy-MM-dd HH:mm" 형식의 문자열로 변환
									Object tsObj = map.get("ts");
									return sdf.format((java.util.Date) tsObj);
								},
								map -> {
									// lossVal을 Double로 안전하게 변환
									Object lossValue = map.get("nodeVal");
									if (lossValue instanceof Number) {
										return ((Number) lossValue).doubleValue();
									}
									return 0.0; // 변환 실패 시 0.0
								},
								(existing, replacement) -> existing // 혹시 중복 키가 있다면 기존 값 유지
						));

				// 3. dateList의 순서에 맞춰 headLoss 값을 동기화
				List<Double> synchronizedLinkList = new ArrayList<>();

				for (int i = 0 ; i < listToProcess ; i++){
					// dateList의 날짜(예: "2025-08-08 11:40")를 가져옵니다.
					String dataDate = dateList.get(i);

					// 2번에서 만든 headLossMap에서 해당 날짜의 lossVal을 찾습니다.
					synchronizedLinkList.add(linkMap.getOrDefault(dataDate, 0.0));
				}

				List<Double> synchronizedNodeList = new ArrayList<>();

				for (int i = 0 ; i < listToProcess ; i++){
					// dateList의 날짜(예: "2025-08-08 11:40")를 가져옵니다.
					String dataDate = dateList.get(i);

					// 2번에서 만든 headLossMap에서 해당 날짜의 lossVal을 찾습니다.
					// ★ Map에 키가 없으면(데이터 누락) 0.0을, 있으면 실제 값을 추가합니다.
					synchronizedNodeList.add(nodeMap.getOrDefault(dataDate, 0.0));
				}

				// 최종적으로 동기화된 Double 리스트를 사용


				// 4. 최종 데이터 조합
				// (반드시 minSize가 아닌 listToProcess 만큼만 반복해야 합니다)
				for (int i = 0; i < listToProcess; i++) {
					HashMap<String, Object> returnMap = new HashMap<>();
					double link  = synchronizedLinkList.get(i);
					double node = synchronizedNodeList.get(i);
					double forPressure = pressureList.get(i);
					double forFlow = selectflowPressure.get(i);


//					double forH = getH(headLoss, pump_grp, grp_str);
					returnMap.put("date", dateList.get(i));
					returnMap.put("pressure", forPressure);
					returnMap.put("flow", forFlow);
					// (사용자님의 원본 로직)
					if (node != 0) {
						returnMap.put(grp_str, node);
						returnMap.put("flow_"+grp_str, link);

					}
					returnList.add(returnMap);
				}

				param.put("first", true);
				List<Double> headLossFlowFirst = new ArrayList<>();
				if (!headLossFlowId.isEmpty()) {
					param.put("dstrbList", headLossFlowId);
					headLossFlowFirst = drvnMapper.selectHeadLossTargetCurFlow(param);
				}

				LinkedHashMap<String, List<HashMap<String, Object>>> dataFirstMap = new LinkedHashMap<>();
				List<String> dateFirstList = new ArrayList<>();
				pumpGrpSet.forEach(id -> {
					param.put("pump_grp", id);
					List<HashMap<String, Object>> flow = drvnMapper.selectPumpFlow(param);
					List<HashMap<String, Object>> pressure = drvnMapper.selectPumpPressure(param);
					dataFirstMap.put("flow" + id, flow);
					dataFirstMap.put("pressure" + id, pressure);
					flow.forEach(maps -> dateFirstList.add((String) maps.get("ts")));
				});

				HashMap<String, List<Double>> totalFirstData = drvnConfig.integrateFlowPressCalc(dataFirstMap, "cur");

				param.put("pump_grp", 0);
				List<HashMap<String, Object>> selectNowPumpPwrUse = drvnMapper.selectNowPumpPwrUse(param);

				Map<Integer, Double> nowPwrMap = selectNowPumpPwrUse.stream()
						.collect(Collectors.toMap(pwrMap -> (Integer) pwrMap.get("PUMP_IDX"), pwrMap -> (Double) pwrMap.get("value")));

//				Double selectHeadLossFirst = drvnMapper.selectHeadLoss(param);
				Double linkFirst = drvnMapper.selectGsAllCurLinkFirst(param);
				Double nodeFirst = drvnMapper.selectGsAllCurNodeFirst(param);
				List<HashMap<String, Object>> selectNowPumpUse = drvnMapper.selectNowPumpUse(param);
				List<Double> pressureListFirst = totalFirstData.get("pressure");
				List<Double> selectflowPressureFirst = totalFirstData.get("flow");

				// 기준시각 직전 1주기에 실측이 없으면 이 수두손실 그룹의 현재값은 만들지 않고 넘어간다.
				if(pressureListFirst == null || pressureListFirst.isEmpty()
						|| selectflowPressureFirst == null || selectflowPressureFirst.isEmpty()
						|| dateFirstList.isEmpty()){
					continue;
				}

				HashMap<String, Object> firstMap = new HashMap<>();
				List<String> curPumpUse = new ArrayList<>();
				double returnNowPwr = selectNowPumpUse.stream()
						.filter(pumpUseMap -> Double.parseDouble((String) pumpUseMap.get("pump_use")) == 1)
						.mapToDouble(pumpUseMap -> {
							int pump_idx = (int) pumpUseMap.get("PUMP_IDX");
							curPumpUse.add("P#" + pump_idx);
							return nowPwrMap.get(pump_idx);
						})
						.sum();

				double headLossSumFlow = headLossFlowFirst.isEmpty() ? 0 : headLossFlowFirst.get(0);
				double pressure = pressureListFirst.get(0);
				double flow = selectflowPressureFirst.get(0);
//				Double h = linkFirst;
//				if(selectHeadLossFirst != null){
//
//					h = getH(selectHeadLossFirst,pump_grp, grp_str);
//				}

				if (arrIdx == 1) {
					firstMap.put("pumpUse", curPumpUse);
					firstMap.put("date", dateFirstList.get(0));
					firstMap.put("pwr", returnNowPwr);
					firstMap.put("Q", pressure);
					firstMap.put("pressure", pressure);
					firstMap.put("flow", flow);
					firstMap.put("flow_" + grp_str, linkFirst);
					if(nodeFirst != null){
						firstMap.put(grp_str, nodeFirst);
					}
					returnList.add(firstMap);
				} else {
					if(nodeFirst != null){
						returnList.get(returnList.size() - 1).put(grp_str, nodeFirst / 10);
						returnList.get(returnList.size() - 1).put("flow_" + grp_str, linkFirst);
					}
				}


				arrIdx++;
			}
		}
		return returnList;
	}
	/**
	 * 성능곡선 예측 그래프 데이터 반환 메서드
	 * @param param 날짜 및 데이터 종류, 펌프 그룹
	 * @return 성능곡선 예측 그래프 데이터
	 */
	public List<HashMap<String, Object>> systemPreResistanceCurves(HashMap<String, Object> param){
		int pump_grp = (Integer) param.get("pump_grp");

		//펌프 그룹에 대응되는 수두손실 그룹 데이터 Map 호출

		List<HashMap<String, Object>> returnList = new ArrayList<>();
		if(pump_grp !=0){
			HashMap<String, String> idMap = pumpDstrbIdMap.get(pump_grp);
			String flowId = idMap.get("flow");
			String pressureId = idMap.get("pressure");
			param.put("DSTRB_ID", flowId);
			List<HashMap<String, Object>> flowList = drvnMapper.selectPrdctFlowPressure(param);
			param.put("DSTRB_ID", pressureId);
			List<HashMap<String, Object>> pressureList = drvnMapper.selectPrdctFlowPressure(param);


			int minSize = Math.min(flowList.size(), pressureList.size());

			for(int i = 0; i < minSize; i++){
				HashMap<String, Object> returnMap = new HashMap<>();
				HashMap<String, Object> flowMap = flowList.get(i);
				HashMap<String, Object> pressureMap = pressureList.get(i);
				String date = (String) flowMap.get("ts");

				float flow = (float) flowMap.get("value");
				float pressure = (float) pressureMap.get("value");

				returnMap.put("date", date);
				returnMap.put("flow", flow);
				returnMap.put("pressure", pressure);

				returnList.add(returnMap);
			}


			if(headLossGrpMap.containsKey(pump_grp)){

				if(!headLossGrpMap.get(pump_grp).isEmpty()){

					Set<String> grp_nm = headLossGrpMap.get(pump_grp).keySet();
					for(String grp_str:grp_nm){
						List<String> headLossFlowId = headLossFlowIdMap.get(pump_grp).get(grp_str);

						List<Double> headLossFlow = new ArrayList<>();
						if(headLossFlowId != null && !headLossFlowId.isEmpty()){
							param.put("dstrbList", headLossFlowId);
							headLossFlow = drvnMapper.selectHeadLossTargetPreFlow(param);

						}

						//수두손실 그룹에 대응되는 수두그룹 리스트 할당
						List<String> grpList = headLossGrpMap.get(pump_grp).get(grp_str);
						param.put("grpList", grpList);


						//수두손실 그룹
						param.put("GRP_NM", grp_str);

						//과거데이터 데이터
//						List<Double> selectHeadLoss = drvnMapper.selectForHeadLoss(param);
						if(!returnList.isEmpty()){
//							int listSize = Math.min(returnList.size(), selectHeadLoss.size());
							for(int i=0;i<returnList.size();i++){
//								Double headLossMap = selectHeadLoss.get(i);
								HashMap<String, Object> flowMap = flowList.get(i);
								double flow = (float) flowMap.get("value");

								double forHeadLossFlow = 0;
								if(!headLossFlow.isEmpty()){
									forHeadLossFlow = headLossFlow.get(i);
								}
//								double forGetHeadLoss = headLossMap;
//								double forH = getH(forGetHeadLoss, pump_grp, grp_str);

//								returnList.get(i).put("flow_"+grp_str, flow - forHeadLossFlow);
//								returnList.get(i).put(grp_str, forH);
							}
						}

					}
				}
			}

			param.put("first", true);
			param.put("DSTRB_ID", flowId);
			List<HashMap<String, Object>> flowListFirst = drvnMapper.selectPrdctFlowPressure(param);
			param.put("DSTRB_ID", pressureId);
			List<HashMap<String, Object>> pressureListFirst = drvnMapper.selectPrdctFlowPressure(param);

			// 기준시각 직전에 예측값이 한 건도 없으면 현재값 구간을 건너뛴다. (실측 쪽과 같은 이유)
			if(flowListFirst.isEmpty() || pressureListFirst.isEmpty()){
				return returnList;
			}

			HashMap<String, Object> lastMap = new HashMap<>();
			HashMap<String, Object> flowFirst = flowListFirst.get(0);
			HashMap<String, Object> pressureFirst = pressureListFirst.get(0);
			String date = (String) flowFirst.get("ts");
			float flow = (float) flowFirst.get("value");
			float pressure = (float) pressureFirst.get("value");

			DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
			LocalDateTime dateTime = LocalDateTime.parse(date, formatter);
			DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
			int week =  dayOfWeek.getValue();
			int hour = dateTime.getHour();
			int month = dateTime.getMonthValue();
			String load = reduceMap.get(month).get(hour);
			HolidayChecker holidayChecker = new HolidayChecker();
			Boolean passDayBool = holidayChecker.isPassDay(date);
			if(week == 7 || passDayBool){
				load = "L";
			}else if (week == 6){
				if(load.equals("H")){
					load = "M";
				}
			}

			List<HashMap<String, Object>> pumpList = setPumpList;
			List<HashMap<String, Object>> preCombFirstList = drvnMapper.selectGrpPrdctPumpCombYn(param);
			Float returnPrdctPwr = null;
			List<String> prdctPumpUse = new ArrayList<>();
			LinkedHashMap<String, BigDecimal> freqMap = new LinkedHashMap<>();
			String oprtn=null;
			for(HashMap<String, Object> comb:preCombFirstList){
				int pump_idx = (int) comb.get("PUMP_IDX");
				List<HashMap<String, Object>> grpList = pumpList.stream()
						.filter(map -> map.containsKey("PUMP_IDX") && map.get("PUMP_IDX").equals(pump_idx))
						.collect(Collectors.toList());
				int pump_grp_idx = (int) grpList.get(0).get("PUMP_GRP_IDX");
				oprtn = (String) comb.get("FLOW_CTR");
				int data_grp = (int) comb.get("PUMP_GRP");
				String pump_yn_str = (String) comb.get("PUMP_YN");
				int pump_yn = Integer.parseInt(pump_yn_str);
				if(data_grp == pump_grp){
					if(returnPrdctPwr == null){
						returnPrdctPwr = (float) comb.get("PWR_PRDCT");

					}
				}
				if(pump_yn >=1){
					prdctPumpUse.add("P#"+pump_grp_idx);
					int pump_typ = (int) comb.get("PUMP_TYP");
					if (pump_typ == 2){
						BigDecimal freq = (BigDecimal) comb.get("FREQ");

						freqMap.put("P#"+pump_grp_idx, freq);
					}

				}
			}



			lastMap.put("load", load);
			lastMap.put("date", date);
			lastMap.put("flow", flow);
			lastMap.put("pressure", pressure);
			lastMap.put("pumpUse", prdctPumpUse);
			lastMap.put("pwr", returnPrdctPwr);
			if(!freqMap.isEmpty()){
				lastMap.put("freq", freqMap);
			}
			if(oprtn != null){
				switch (oprtn) {
					case "INC":
						lastMap.put("oprtn", "high");
						break;
					case "DEC":
						lastMap.put("oprtn", "low");
						break;
					case "KEP":
						lastMap.put("oprtn", "none");
						break;
					default:
						lastMap.put("oprtn", "none");
						break;
				}
			}else{
				lastMap.put("oprtn", "none");

			}

			returnList.add(lastMap);

			if(headLossGrpMap.containsKey(pump_grp)){

				if(!headLossGrpMap.get(pump_grp).isEmpty()){
					Set<String> grp_nm = headLossGrpMap.get(pump_grp).keySet();
					for(String grp_str:grp_nm){
						List<String> headLossFlowId = headLossFlowIdMap.get(pump_grp).get(grp_str);

						List<Double> headLossFlow = new ArrayList<>();
						if(!headLossFlowId.isEmpty()){
							param.put("dstrbList", headLossFlowId);
							headLossFlow = drvnMapper.selectHeadLossTargetPreFlow(param);

						}

						//수두손실 그룹에 대응되는 수두그룹 리스트 할당
						List<String> grpList = headLossGrpMap.get(pump_grp).get(grp_str);
						param.put("grpList", grpList);


						//수두손실 그룹
						param.put("GRP_NM", grp_str);

						//과거데이터 데이터
						Double selectHeadLoss = drvnMapper.selectHeadLoss(param);
						if(selectHeadLoss != null){


							double forHeadLossFlow = 0;
							if(!headLossFlow.isEmpty()){
								forHeadLossFlow = headLossFlow.get(0);
							}
							double forH = getH(selectHeadLoss, pump_grp, grp_str);

							returnList.get(returnList.size() - 1).put("flow_"+grp_str, flow - forHeadLossFlow);
							returnList.get(returnList.size() -1).put(grp_str, forH);
						}
					}
				}
			}
			return returnList;
		}else if(pump_grp == 0){
			Set<String> grp_nm = headLossGrpMap.get(pump_grp).keySet();
			///// 예측 통합 /////
			param.put("first", false);
			param.put("opt_idx","pre");
			//현재 값
			Set<Integer> pumpGrpSet = pumpDstrbIdMap.keySet();
			int arrIdx = 1;
			for (String grp_str : grp_nm) {
				//수두손실 그룹에 대응되는 수두그룹 리스트 할당
				List<String> grpList = headLossGrpMap.get(pump_grp).get(grp_str);
				param.put("grpList", grpList);


				//수두손실 그룹
				param.put("GRP_NM", grp_str);
				//예측 예전꺼
				LinkedHashMap<String, List<HashMap<String, Object>>> dataMap = new LinkedHashMap<>();
				List<String> dateList = new ArrayList<>();
				param.put("intradotion", false);
				for(Integer id:pumpGrpSet){
					HashMap<String, String> ditrbMap = pumpDstrbIdMap.get(id);
					String flowId = ditrbMap.get("flow");
					String pressureId = ditrbMap.get("pressure");

					param.put("DSTRB_ID", flowId);
					List<HashMap<String, Object>> flowDataList = drvnMapper.selectPrdctFlowPressure(param);

					param.put("DSTRB_ID", pressureId);
					List<HashMap<String, Object>> pressureDataList = drvnMapper.selectPrdctFlowPressure(param);

					// flow 데이터 보정 및 dateList에 ts 값 추가
					for (HashMap<String, Object> flowMap : flowDataList) {
						String ts = (String) flowMap.get("ts");
						dateList.add(ts);

						Object flowValueObj = flowMap.get("value");
						double flowDb = 0.0;

						// value가 null이거나 0.0일 경우 보정
						if (flowValueObj == null || (float) flowValueObj == 0.0) {
							Double recentAvg = drvnMapper.selectAverageValueLast10Minutes(flowId, ts);
							flowDb = (recentAvg != null) ? recentAvg : 0.0;
							flowMap.put("value", (float) flowDb); // 보정된 값으로 맵 업데이트
						}
					}

					// pressure 데이터 보정
					for (HashMap<String, Object> pressureMap : pressureDataList) {
						String ts = (String) pressureMap.get("ts");

						Object pressureValueObj = pressureMap.get("value");
						double pressureDb = 0.0;

						// value가 null이거나 0.0일 경우 보정
						if (pressureValueObj == null || (float) pressureValueObj == 0.0) {
							Double recentAvg = drvnMapper.selectAverageValueLast10Minutes(pressureId, ts);
							pressureDb = (recentAvg != null) ? recentAvg : 0.0;
							pressureMap.put("value", (float) pressureDb); // 보정된 값으로 맵 업데이트
						}
					}

					// 보정된 리스트를 dataMap에 추가
					dataMap.put("flow" + id, flowDataList);
					dataMap.put("pressure" + id, pressureDataList);

				}

				HashMap<String, List<Double>> totalData = drvnConfig.integrateFlowPressCalc(dataMap, "pre");
				List<Double> prdctFlow = totalData.get("flow");
				List<Double> prdctPressure = totalData.get("pressure");

				param.put("grpList", grpList);
				param.put("first", false);
				//수두손실 그룹
				param.put("GRP_NM", grp_str);
				//과거데이터 데이터

				// 원본 쿼리 결과 (시간대별 수두손실 값)
//				List<HashMap<String, Object>> rawHeadLossList = drvnMapper.selectForHeadLoss(param);


				List<HashMap<String, Object>> linkValList = drvnMapper.selectGsAllLinkRange(param);
				List<HashMap<String, Object>> nodeValList = drvnMapper.selectGsAllNodeRange(param);

				// 현황 데이터의 시간 축 길이
				int minSize = Math.min(prdctFlow.size(), prdctPressure.size());
				int listToProcess = Math.min(dateList.size(), minSize);


				// 2. rawHeadLossList를 Map<String, Double> 형태로 변환 (빠른 검색용)
				//    dateList의 형식("yyyy-MM-dd HH:mm")에 맞춰 Key를 생성합니다.
				java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm");
				Map<String, Double> linkMap = linkValList.stream()
						.filter(map -> map.containsKey("ts") && map.containsKey("linkVal") && map.get("ts") != null)
						.collect(Collectors.toMap(
								map -> {
									// "ts" 객체를 "yyyy-MM-dd HH:mm" 형식의 문자열로 변환
									Object tsObj = map.get("ts");
									return sdf.format((java.util.Date) tsObj);
								},
								map -> {
									// lossVal을 Double로 안전하게 변환
									Object lossValue = map.get("linkVal");
									if (lossValue instanceof Number) {
										return ((Number) lossValue).doubleValue();
									}
									return 0.0; // 변환 실패 시 0.0
								},
								(existing, replacement) -> existing // 혹시 중복 키가 있다면 기존 값 유지
						));
				Map<String, Double> nodeMap = nodeValList.stream()
						.filter(map -> map.containsKey("ts") && map.containsKey("nodeVal") && map.get("ts") != null)
						.collect(Collectors.toMap(
								map -> {
									// "ts" 객체를 "yyyy-MM-dd HH:mm" 형식의 문자열로 변환
									Object tsObj = map.get("ts");
									return sdf.format((java.util.Date) tsObj);
								},
								map -> {
									// lossVal을 Double로 안전하게 변환
									Object lossValue = map.get("nodeVal");
									if (lossValue instanceof Number) {
										return ((Number) lossValue).doubleValue();
									}
									return 0.0; // 변환 실패 시 0.0
								},
								(existing, replacement) -> existing // 혹시 중복 키가 있다면 기존 값 유지
						));

				// 3. dateList의 순서에 맞춰 headLoss 값을 동기화 (★★ 중요 ★★)
				//    (이 부분이 사용자님의 마지막 코드에서 누락되었습니다)


				List<Double> synchronizedLinkList = new ArrayList<>();
				List<Double> synchronizedNodeList = new ArrayList<>();


				for (int i = 0 ; i < listToProcess ; i++){
					String rawDate = dateList.get(i);
					String dataDate = rawDate;

					if (dataDate != null && dataDate.length() >= 16) {
						dataDate = dataDate.substring(0, 16);  // "yyyy-MM-dd HH:mm"
					}

					Double linkVal = linkMap.getOrDefault(dataDate, 0.0);
					synchronizedLinkList.add(linkVal);

					if (i < 3) { // 너무 많이 찍히지 않게 앞부분만
						System.out.println("[RESIST-pre][grp=" + grp_str + "] syncLink idx=" + i
								+ ", rawDate=" + rawDate
								+ ", cutDate=" + dataDate
								+ ", linkVal=" + linkVal);
					}
				}

				for (int i = 0 ; i < listToProcess ; i++){
					String rawDate = dateList.get(i);
					String dataDate = rawDate;

					if (dataDate != null && dataDate.length() >= 16) {
						dataDate = dataDate.substring(0, 16);
					}

					Double nodeVal = nodeMap.getOrDefault(dataDate, 0.0);
					synchronizedNodeList.add(nodeVal);

					if (i < 3) {
						System.out.println("[RESIST-pre][grp=" + grp_str + "] syncNode idx=" + i
								+ ", rawDate=" + rawDate
								+ ", cutDate=" + dataDate
								+ ", nodeVal=" + nodeVal);
					}
				}



				//현황 전력


				for (int i = 0; i < listToProcess; i++) {
					HashMap<String, Object> returnMap = new HashMap<>();
					double forPressure = prdctPressure.get(i);
					double forFlow = prdctFlow.get(i);
					double link = synchronizedLinkList.get(i);
					double node = synchronizedNodeList.get(i);
//					double forH = getH(headLoss, pump_grp, grp_str);
//					double forHeadLossFlow = 0;
					returnMap.put("date", dateList.get(i));
					returnMap.put("Q", forPressure);
					returnMap.put("pressure", forPressure);
					returnMap.put("flow", forFlow);
					returnMap.put(grp_str, node / 10);
					returnMap.put("flow_"+grp_str, link);

					returnList.add(returnMap);


				}

				//예측 데이터 (현재시간 5분뒤)
				//마지막 값만 pre로 수두손실 값 조회
				param.put("opt_idx","pre");
//				Double selectHeadLossFirst = drvnMapper.selectHeadLoss(param);
				Double linkFirst = drvnMapper.selectGsAllLinkFirst(param);
				Double nodeFirst = drvnMapper.selectGsAllNodeFirst(param);
				param.put("first", true);
				List<String> headLossFlowId = headLossFlowIdMap.get(pump_grp).get(grp_str);
				List<Double> headLossFlowFirst = new ArrayList<>();
				if(!headLossFlowId.isEmpty()){
					param.put("dstrbList", headLossFlowId);
					headLossFlowFirst = drvnMapper.selectHeadLossTargetPreFlow(param);
				}
				double headLossSumFlow = 0;
				if(!headLossFlowFirst.isEmpty()){
					headLossSumFlow = headLossFlowFirst.get(0);
				}
				LinkedHashMap<String, List<HashMap<String, Object>>> dataFirstMap = new LinkedHashMap<>();
				String dateFirstList = null;
				HashMap<Integer, HashMap<String, Double>> grpFlowPressure = new HashMap<>();
				for(Integer id:pumpGrpSet){
					HashMap<String, String> ditrbMap = pumpDstrbIdMap.get(id);
					String flowId = ditrbMap.get("flow");
					String pressureId = ditrbMap.get("pressure");

					param.put("DSTRB_ID", flowId);
					List<HashMap<String, Object>> flowDataList = drvnMapper.selectPrdctFlowPressure(param);

					param.put("DSTRB_ID", pressureId);
					List<HashMap<String, Object>> pressureDataList = drvnMapper.selectPrdctFlowPressure(param);

					// ts 값 가져오기
					String ts = null;
					if (flowDataList != null && !flowDataList.isEmpty()) {
						ts = (String) flowDataList.get(0).get("ts");
						dateFirstList = ts;
					}

					// flow 데이터 보정
					double flowDb;
					Object flowValueObj = (flowDataList != null && !flowDataList.isEmpty()) ? flowDataList.get(0).get("value") : null;
					if (flowValueObj == null || (float) flowValueObj == 0.0) {
						if (ts != null) {
							Double recentAvg = drvnMapper.selectAverageValueLast10Minutes(flowId, ts);
							flowDb = (recentAvg != null) ? recentAvg : 0.0;
						} else {
							flowDb = 0.0;
						}
					} else {
						flowDb = (double) (float) flowValueObj;
					}

					// pressure 데이터 보정
					double pressureDb;
					Object pressureValueObj = (pressureDataList != null && !pressureDataList.isEmpty()) ? pressureDataList.get(0).get("value") : null;
					if (pressureValueObj == null || (float) pressureValueObj == 0.0) {
						if (ts != null) {
							Double recentAvg = drvnMapper.selectAverageValueLast10Minutes(pressureId, ts);
							pressureDb = (recentAvg != null) ? recentAvg : 0.0;
						} else {
							pressureDb = 0.0;
						}
					} else {
						pressureDb = (double) (float) pressureValueObj;
					}

					// 보정된 값으로 dataFirstMap 업데이트 (리스트의 첫 번째 요소)
					if (flowDataList != null && !flowDataList.isEmpty()) {
						flowDataList.get(0).put("value", (float) flowDb);
					}
					if (pressureDataList != null && !pressureDataList.isEmpty()) {
						pressureDataList.get(0).put("value", (float) pressureDb);
					}
					dataFirstMap.put("flow" + id, flowDataList);
					dataFirstMap.put("pressure" + id, pressureDataList);

					// grpFlowPressureMap에 보정된 값 추가
					HashMap<String, Double> grpFlowPressureMap = new HashMap<>();
					grpFlowPressureMap.put("flow", flowDb);
					grpFlowPressureMap.put("pressure", pressureDb);
					grpFlowPressure.put(id, grpFlowPressureMap);
				}

				HashMap<String, List<Double>> totalFirstData = drvnConfig.integrateFlowPressCalc(dataFirstMap, "pre");

				List<Double> prdctFlowFirst = totalFirstData.get("flow");
				List<Double> prdctPressureFirst = totalFirstData.get("pressure");


				HashMap<String, Object> firstMap = new HashMap<>();
				firstMap.put("date",dateFirstList);


//				Double h = null;
//				if(selectHeadLossFirst != null){
//					h = getH(selectHeadLossFirst, pump_grp, grp_str);
//				}

				Double pressure = null;
				if(!prdctPressureFirst.isEmpty()){
					pressure = prdctPressureFirst.get(0);
				}

				Double flow = null;
				if(!prdctFlowFirst.isEmpty()){
					flow = prdctFlowFirst.get(0);
				}






				if (arrIdx == 1) {
					//예측 펌프 조합
					List<String> prdctPumpUse = new ArrayList<>();
					List<String> prdctPumpInQuiryUse = new ArrayList<>();


					List<String> pumpComb = new ArrayList<>();
					HashMap<Integer, Double> grpPrdctPwr = drvnConfig.allPumpGrpPwrPrdct(pumpComb, grpFlowPressure, null);
					double sum = 0.0;
					for (Map.Entry<Integer, Double> entry : grpPrdctPwr.entrySet()) {
						sum += entry.getValue();
					}
					for(String pump:pumpComb){
						prdctPumpUse.add("P#"+pump);
					}


					firstMap.put("flow_"+grp_str, linkFirst);
					firstMap.put("pumpUse", prdctPumpUse);
					if(nodeFirst!=null){
						firstMap.put(grp_str, nodeFirst / 10);
					}
					firstMap.put("Q", pressure);
					firstMap.put("pressure", pressure);
					firstMap.put("flow", flow);
					firstMap.put("pwr", sum);


					returnList.add(firstMap);
				} else {
					if(nodeFirst!=null){
						returnList.get(returnList.size() - 1).put(grp_str, nodeFirst / 10);
						returnList.get(returnList.size() - 1).put("flow_"+grp_str, linkFirst);
					}
				}
				arrIdx++;

			}
		}
		return returnList;
	}

	/**
	 * 시간 증가 계산 메서드
	 * @param dateString 기준시간
	 * @param minutesToAdd 증가한 분
	 * @return 증가된 시간
	 */
	public String increaseByMinutes(String dateString, int minutesToAdd) {
		SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
		Date date;
		try {
			date = sdf.parse(dateString);
		} catch (ParseException e) {
			e.printStackTrace();
			return null;
		}

		Calendar calendar = Calendar.getInstance();
		calendar.setTime(date);
		calendar.add(Calendar.MINUTE, minutesToAdd);

		Date adjustedDate = calendar.getTime();
		return sdf.format(adjustedDate);
	}

	/**
	 * 예측 및 실측 5분단위 차트 데이터 반환 메서드
	 * @param param 날짜 및 데이터 종류
	 * @return 예측 및 실측 5분단위 차트 데이터 반환
	 */
	public HashMap<String, Object> selectIntradotion(HashMap<String, Object> param) {
		String opt_idx = (String) param.get("opt_idx");

		//properties 에서 필요정보 가져옴
		List<String> flowTag = dstrbIdMap.get("flowTag");
		List<String> dstrb_q_id = dstrbIdMap.get("dstrb_q_id");
		List<String> dstrb_p_id = dstrbIdMap.get("dstrb_p_id");
		List<String> levelTag = dstrbIdMap.get("level_tag");
		List<String> pressureTag = dstrbIdMap.get("pressureTag");
		String startDate = (String) param.get("startDate");
		Set<Integer> pumpGrpSet = pumpDstrbIdMap.keySet();
		HashMap<String, Object> returnMap = new HashMap<>();
		List<String> dateList = generateData(startDate);
		if(opt_idx.equals("cur")){
			param.put("intradotion", false);
			returnMap.put("ts", dateList);
			param.put("tagList", flowTag);
			List<HashMap<String, Object>> flowList = drvnMapper.selectCurFlowData(param);
			HashMap<String, List<Object>> flowMap = createFlowPressureData(flowList, opt_idx, "tag", false);
			if (wpp_code.equals("gs")) {
				// 평균을 계산할 태그 그룹 정의 (대표 태그: 그룹의 첫 번째 태그)
				Map<String, List<String>> levelAverageGroups = new LinkedHashMap<>();
				levelAverageGroups.put("701-367-LEI-8001", Arrays.asList("701-367-LEI-8001", "701-367-LEI-8002", "701-367-LEI-8003", "701-367-LEI-8004"));
				levelAverageGroups.put("701-367-LEI-8006", Arrays.asList("701-367-LEI-8005", "701-367-LEI-8006", "701-367-LEI-8007", "701-367-LEI-8008"));
				levelAverageGroups.put("701-367-LEI-8009", Arrays.asList("701-367-LEI-8009", "701-367-LEI-8010"));
				levelAverageGroups.put("701-367-LEI-4008", Arrays.asList("701-367-LEI-4008", "701-367-LEI-4009"));
				levelAverageGroups.put("701-367-LEI-4011", Arrays.asList("701-367-LEI-4011", "701-367-LEI-4012", "701-367-LEI-4013", "701-367-LEI-4014"));

				// 평균 계산에 사용될 모든 태그를 담는 Set
				Set<String> tagsToAverageSet = levelAverageGroups.values().stream()
						.flatMap(Collection::stream)
						.collect(Collectors.toSet());

				// 기존 태그 리스트에서 평균 태그들을 제외한 리스트
				List<String> individualTags = levelTag.stream()
						.filter(tag -> !tagsToAverageSet.contains(tag))
						.collect(Collectors.toList());

				// DB 조회에 사용할 전체 태그 리스트
				List<String> allQueryTags = new ArrayList<>(levelAverageGroups.keySet());
				allQueryTags.addAll(tagsToAverageSet);
				allQueryTags.addAll(individualTags);
				param.put("tagList", allQueryTags.stream().distinct().collect(Collectors.toList()));
				List<HashMap<String, Object>> levelList = drvnMapper.selectCurFlowData(param);

				// 최종 반환할 levelMap
				HashMap<String, List<Object>> finalLevelMap = new HashMap<>();

				// 개별 태그 데이터 처리
				List<HashMap<String, Object>> individualDataList = levelList.stream()
						.filter(data -> individualTags.contains(data.get("tag")))
						.collect(Collectors.toList());
				finalLevelMap.putAll(createFlowPressureData(individualDataList, opt_idx, "tag", false));

				// 그룹별 데이터 처리 및 평균 계산
				for (Map.Entry<String, List<String>> group : levelAverageGroups.entrySet()) {
					String mainTag = group.getKey();
					Set<String> groupTags = new HashSet<>(group.getValue());


					// LocalDateTime을 키로 사용하여 정확한 시간대별 그룹핑
					Map<LocalDateTime, List<Double>> groupedDataByTimestamp = new HashMap<>();
					for (HashMap<String, Object> data : levelList) {
						String tagName = (String) data.get("tag");
						if (groupTags.contains(tagName)) {
							LocalDateTime timestamp = ((Timestamp) data.get("TS")).toLocalDateTime();
							Object valueObj = data.get("value");
							Double value = Double.parseDouble(String.valueOf(valueObj));
							LocalDateTime truncatedTimestamp = timestamp.truncatedTo(ChronoUnit.MINUTES);

							if (!groupedDataByTimestamp.containsKey(truncatedTimestamp)) {
								groupedDataByTimestamp.put(truncatedTimestamp, new ArrayList<>());
							}
							if (value > 0.3) {
								groupedDataByTimestamp.get(truncatedTimestamp).add(value);
							}
						}
					}


					// 시간대별 평균 수위 계산
					List<Object> averagedLevels = new ArrayList<>();
					for (String tsString : dateList) {
						LocalDateTime ts = LocalDateTime.parse(tsString, DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

						List<Double> values = groupedDataByTimestamp.getOrDefault(ts, Collections.emptyList());

						double average = 0.0;
						if (!values.isEmpty()) {
							if (values.size() == 1) {
								average = values.get(0);
							} else {
								double sum = values.stream().mapToDouble(Double::doubleValue).sum();
								average = sum / values.size();
							}
						}
						averagedLevels.add(average);

					}

					finalLevelMap.put(mainTag, averagedLevels);

				}

				returnMap.put("level", finalLevelMap);
			} else {
				// wpp_code가 'gs'가 아닐 경우 기존 로직 유지
				param.put("tagList", levelTag);
				List<HashMap<String, Object>> levelList = drvnMapper.selectCurFlowData(param);
				HashMap<String, List<Object>> levelMap = createFlowPressureData(levelList, opt_idx, "tag", false);
				returnMap.put("level", levelMap);
			}

			List<HashMap<String, Object>> pressureList;

			if(wpp_code.equals("gs")){
				param.put("tagList", pressureTag);
				pressureList = drvnMapper.selectCurFlowData(param);
			}else{
				param.put("dstrb_id", dstrb_p_id);
				pressureList = drvnMapper.selectIntradotion(param);
			}

			if(wpp_code.equals("gr")){
				List<HashMap<String, Object>> grPreesureList = drvnMapper.grPreesureList(param);
				pressureList.addAll(grPreesureList);
			}
			HashMap<String, List<Object>> pressureMap = createFlowPressureData(pressureList, opt_idx, "tag", false);

			param.put("intradotion", true);


			LinkedHashMap<String, List<HashMap<String, Object>>> dataMap = new LinkedHashMap<>();
			for(Integer id:pumpGrpSet){
				param.put("pump_grp", id);
				List<HashMap<String, Object>> flow = drvnMapper.select12HourCurPumpFlow(param);
				List<HashMap<String, Object>> pressure = drvnMapper.select12HourCurPumpPressure(param);
				dataMap.put("flow"+id, flow);
				dataMap.put("pressure"+id, pressure);

			}

			HashMap<String, List<Double>> totalData = drvnConfig.integrateFlowPressCalc(dataMap, "cur");


			List<Double> pressureAllList = totalData.get("pressure");
			List<Object> pressureObjList = new ArrayList<>();
			pressureObjList.addAll(pressureAllList);
			List<Double> flowAllList = totalData.get("flow");
			List<Object> flowObjList = new ArrayList<>();
			flowObjList.addAll(flowAllList);
			flowMap.put("all", flowObjList);

			pressureMap.put("all", pressureObjList);
			returnMap.put("flow", flowMap);
			returnMap.put("pressure", pressureMap);

		}else if(opt_idx.equals("pre")){
			param.put("first", false);
			String plusDate = increaseByMinutes(startDate, 1);
			dateList.add(plusDate);
			returnMap.put("ts", dateList);

			param.put("dstrb_id", dstrb_q_id);

			List<HashMap<String, Object>> resultflowList = drvnMapper.selectPreFlow(param);
			List<HashMap<String, Object>> flowList = resultflowList.stream()
					.filter(map -> {
						LocalDateTime ts = ((Timestamp) map.get("ts")).toLocalDateTime();
						return ts.getMinute() % 5 == 0;
					}).collect(Collectors.toList());

			param.put("first", true);

			List<HashMap<String, Object>> flowListFirst = drvnMapper.selectPreFlow(param);


			param.put("first", false);
			param.put("dstrb_id", dstrb_p_id);

			List<HashMap<String, Object>> resultPressureList = drvnMapper.selectPrePri(param);
			List<HashMap<String, Object>> pressureList = resultPressureList.stream()
					.filter(map -> {
						LocalDateTime ts = ((Timestamp) map.get("ts")).toLocalDateTime();
						return ts.getMinute() % 5 == 0;
					}).collect(Collectors.toList());
			if(wpp_code.equals("gr")){
				List<HashMap<String, Object>> grPrePressureList = drvnMapper.grPrePressure(param);
				pressureList.addAll(grPrePressureList);
			}


			param.put("first", true);

			List<HashMap<String, Object>> pressureListFirst = drvnMapper.selectPrePri(param);
			if(wpp_code.equals("gr")){
				List<HashMap<String, Object>> grPrePressureListFirst = drvnMapper.grPrePressure(param);
				pressureListFirst.addAll(grPrePressureListFirst);
			}
			pressureList.addAll(pressureListFirst);
			HashMap<String, List<Object>> flowMap = createFlowPressureData(flowList, opt_idx, "tag", false);
			HashMap<String, List<Object>> pressureMap = createFlowPressureData(pressureList, opt_idx, "tag", false);



			flowMap = plusPrdctData(flowMap, flowListFirst);
//			pressureMap = plusPrdctData(pressureMap, pressureListFirst);


			LinkedHashMap<String, List<HashMap<String, Object>>> dataMap = new LinkedHashMap<>();
			param.put("cycle", 1);
			param.put("range", 12);
			param.put("first", false);
			param.put("intradotion", true);

			for (Integer id : pumpGrpSet) {
				HashMap<String, String> ditrbMap = pumpDstrbIdMap.get(id);
				String flowId = ditrbMap.get("flow");
				String pressureId = ditrbMap.get("pressure");

				param.put("DSTRB_ID", flowId);
				List<HashMap<String, Object>> flowRaw = drvnMapper.selectPreWithDstrb(param);
				List<HashMap<String, Object>> flow = (param.get("first") == Boolean.TRUE)
						? flowRaw
						: flowRaw.stream()
						.filter(map -> {
							Timestamp ts = (Timestamp) map.get("ts");
							LocalDateTime time = ts.toLocalDateTime();
							return time.getMinute() % 5 == 0;
						})
						.collect(Collectors.toList());

				param.put("DSTRB_ID", pressureId);
				List<HashMap<String, Object>> pressureRaw = drvnMapper.selectPreWithDstrb(param);
				List<HashMap<String, Object>> pressure = (param.get("first") == Boolean.TRUE)
						? pressureRaw
						: pressureRaw.stream()
						.filter(map -> {
							Timestamp ts = (Timestamp) map.get("ts");
							LocalDateTime time = ts.toLocalDateTime();
							return time.getMinute() % 5 == 0;
						})
						.collect(Collectors.toList());


				dataMap.put("flow" + id, flow);
				dataMap.put("pressure" + id, pressure);
			}


			HashMap<String, List<Double>> totalData = drvnConfig.integrateFlowPressCalc(dataMap, "pre");


			List<Double> prdctFlow = totalData.get("flow");
			List<Double> prdctPressure = totalData.get("pressure");

			param.put("first", true);
			LinkedHashMap<String, List<HashMap<String, Object>>> dataFirstMap = new LinkedHashMap<>();

			for (Integer id : pumpGrpSet) {
				HashMap<String, String> ditrbMap = pumpDstrbIdMap.get(id);
				String flowId = ditrbMap.get("flow");
				String pressureId = ditrbMap.get("pressure");

				param.put("DSTRB_ID", flowId);

				List<HashMap<String, Object>> flow = drvnMapper.selectPreWithDstrb(param);


				param.put("DSTRB_ID", pressureId);

				List<HashMap<String, Object>> pressure = drvnMapper.selectPreWithDstrb(param);


				dataFirstMap.put("flow" + id, flow);
				dataFirstMap.put("pressure" + id, pressure);
			}


			HashMap<String, List<Double>> totalFirstData = drvnConfig.integrateFlowPressCalc(dataFirstMap, "pre");


			List<Double> prdctFlowFirst = totalFirstData.get("flow");
			List<Double> prdctPressureFirst = totalFirstData.get("pressure");

			prdctFlow.addAll(prdctFlowFirst);
			List<Object> prdctFlowObjList = new ArrayList<>();
			prdctFlowObjList.addAll(prdctFlow);
			List<Object> predctPressureObjList = new ArrayList<>();
			prdctPressure.addAll(prdctPressureFirst);
			predctPressureObjList.addAll(prdctPressure);

			flowMap.put("all", prdctFlowObjList);
			pressureMap.put("all", predctPressureObjList);

			returnMap.put("flow", flowMap);
			returnMap.put("pressure", pressureMap);
			if(wpp_code.equals("wm")){
				List<String> level_tag = new ArrayList<>();
				level_tag.add("H1_Predict");
				param.put("dstrb_id", level_tag);
				param.put("first", false);
				List<HashMap<String, Object>> levelList = drvnMapper.selectPreFlow(param);


				param.put("first", true);

				List<HashMap<String, Object>> levelListFirst = drvnMapper.selectPreFlow(param);

				HashMap<String, List<Object>> levelMap = createFlowPressureData(levelList, opt_idx, "tag", false);
				levelMap = plusPrdctData(levelMap, levelListFirst);
				returnMap.put("level", levelMap);
			}
		}

		return returnMap;
	}

	/**
	 * 차트데이터 반환시 실제 태그에 매핑해 반환하는 메서드
	 * @param hashMaps 데이터 map
	 * @param type 실측 예측 종류
	 * @param tag 실제 태그
	 * @param epa epa데이터 유무
	 * @return 유량 및 압력 태그매칭 차트데이터
	 */
	public HashMap<String, List<Object>> createFlowPressureData(List<HashMap<String, Object>> hashMaps, String type, String tag, Boolean epa){

		HashMap<String, List<Object>> returnList = new HashMap<>();

		for(HashMap<String, Object> map:hashMaps){
			String mapTag = (String) map.get(tag);
			if(type.equals("pre")){
				Object valueObj = map.get("value");
				if(!returnList.containsKey(mapTag)){
					List<Object> tagListArr = new ArrayList<>();
					returnList.put(mapTag, tagListArr);
				}

				if (valueObj instanceof Float) {
					Float mapValue = (Float) valueObj;
					if (epa) {
						returnList.get(mapTag).add(mapValue / 10);
					} else {
						returnList.get(mapTag).add(mapValue);
					}
				} else if (valueObj instanceof Double) {
					Double mapValue = (Double) valueObj;
					if (epa) {
						returnList.get(mapTag).add(mapValue / 10);
					} else {
						returnList.get(mapTag).add(mapValue);
					}
				}
			}else {
				String mapValueStr = (String) map.get("value");
				Double mapValue = Double.parseDouble(mapValueStr);
				if(!returnList.containsKey(mapTag)){
					List<Object> tagListArr = new ArrayList<>();
					returnList.put(mapTag, tagListArr);
				}
				returnList.get(mapTag).add(mapValue);
			}
		}

		return returnList;
	}

	/**
	 * 예측데이터 추가 메서드
	 * @param dataMap 추가될 기존 map 데이터
	 * @param plusData 추가할 예측 데이터
	 * @return 예측데이터가 추가된 데이터 map
	 */
	public HashMap<String, List<Object>> plusPrdctData(HashMap<String, List<Object>> dataMap, List<HashMap<String, Object>> plusData) {
		for (HashMap<String, Object> map : plusData) {
			String tag = (String) map.get("tag");

			// value를 Object로 받아서 Double 또는 Float 확인 후 처리
			Object valueObj = map.get("value");

			float value;
			if (valueObj instanceof Double) {
				value = ((Double) valueObj).floatValue();  // Double -> Float 변환
			} else if (valueObj instanceof Float) {
				value = (Float) valueObj;  // 이미 Float일 경우
			} else {
				throw new IllegalArgumentException("Unsupported type for 'value': " + valueObj.getClass().getName());
			}

			dataMap.get(tag).add(value);  // 변환된 Float 값 추가
		}
		return dataMap;
	}

	/**
	 * 시간 데이터 리스트를 생성해 반환하는 메서드
	 * @param dateTimeString 기준 날짜 데이터
	 * @return 5분단위로 생성된 날짜 리스트 데이터
	 */
	public static List<String> generateData(String dateTimeString) {
		List<String> dataList = new ArrayList<>();

		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
		LocalDateTime dateTime = LocalDateTime.parse(dateTimeString, formatter);

		LocalDateTime threeHoursAgo = dateTime.minusHours(12);

		// 시작 시간을 5분 단위로 맞추기
		int minute = threeHoursAgo.getMinute();
		int remainder = minute % 5;
		if (remainder != 0) {
			threeHoursAgo = threeHoursAgo.plusMinutes(5 - remainder);
		}

		while (threeHoursAgo.isBefore(dateTime)) {
			dataList.add(formatter.format(threeHoursAgo));
			threeHoursAgo = threeHoursAgo.plusMinutes(5);
		}

		// 마지막 시간을 포함시키기 전에 5분 단위로 맞추기
		int endMinute = dateTime.getMinute();
		int endRemainder = endMinute % 5;
		if (endRemainder != 0) {
			dateTime = dateTime.minusMinutes(endRemainder);
		}

		dataList.add(formatter.format(dateTime));
		return dataList;
	}

	/**
	 * 웹 성능곡선을 그리기위한 회기식 데이터 반환
	 * @return 성능곡선 회기식 데이터
	 */
	public List<HashMap<String, Object>> selectPumpCombCal() {
		//운문

		LocalDateTime dateTime = LocalDateTime.now();
		List<HashMap<String, Object>> pumpList = aiMapper.selectPumpList();;
		if(wpp_code.equals("wm")){


			pumpList.forEach(map -> {

				map.put("PUMP_TYP", 1);

			});
		}
		List<HashMap<String, Object>> getPumpCal;
		if(wpp_code.equals("gs")){
			getPumpCal =drvnMapper.selectPumpCombCal();
		}else{
			getPumpCal =drvnMapper.selectPumpCombCal();
		}

		List<HashMap<String, Object>> filteredList;

		if (wpp_code.equals("gs")) {
			filteredList = getPumpCal.stream()
					.filter(map -> {
						if ((int) map.get("PUMP_GRP") == 0) {
							return (int) map.get("USE_YN") == 1;
						}
						return true; // PUMP_GRP가 0이 아닌 데이터는 필터링 없이 포함
					})
					.collect(Collectors.toList());
		} else {
			filteredList = getPumpCal; // 다른 경우 필터링 없이 원본 리스트 사용
		}
		List<Integer> pumpCombTypeList = new ArrayList<>();
		int count = 0;
		int size = getPumpCal.size() - 1;

		for(HashMap<String, Object> cal:filteredList){
			int c_ord = (int) cal.get("C_ORD");
			count++;
			if(c_ord == 1){
				pumpCombTypeList = new ArrayList<>();
				String pump_comb = (String) cal.get("PUMP_COMB");
				Integer pump_grp = (Integer) cal.get("PUMP_GRP");
				String[] strArray = pump_comb.split(",");
				List<String> strList =Arrays.stream(strArray)
						.map(String::trim)
						.collect(Collectors.toList());

				if(wpp_code.equals("gr") && pump_grp == 3){
					//고령 선남가압장 짝수일 2번, 홀수일 3번 조합 생성
					int wm_day = dateTime.getDayOfMonth();
					strList = strList.stream()
							.map(str -> {
								if (wm_day % 2 == 0) {
									// wm_day가 짝수일 경우
									if (str.equals("11")) {
										return "10";
									}
								} else {
									// wm_day가 홀수일 경우
									if (str.equals("11")) {
										return "11";
									}
								}
								return str;
							})
							.collect(Collectors.toList());
				}
				List<Integer> grpIdxList = new ArrayList<>();
				for(String pump_idx_str:strList){
					if(!pump_idx_str.isEmpty()){
						int pump_idx = Integer.parseInt(pump_idx_str);
						List<HashMap<String, Object>> idxList = pumpList.stream()
								.filter(map -> map.containsKey("PUMP_IDX") && map.get("PUMP_IDX").equals(pump_idx))
								.collect(Collectors.toList());

						int pump_grp_idx = (int) idxList.get(0).get("PUMP_GRP_IDX");
						int pump_typ = (int) idxList.get(0).get("PUMP_TYP");
						grpIdxList.add(pump_grp_idx);
						pumpCombTypeList.add(pump_typ);

					}
				}
				String result;
				if(!grpIdxList.isEmpty()){
					result = joinWithComma(grpIdxList);
				}else{
					result = "";
				}

				cal.put("PUMP_COMB", result);
			}else {
				String freq_comb = (String) cal.get("PUMP_COMB");
				// TB_PUMP_CAL 의 C_ORD=2 행(주파수 조합)은 미입력 시 빈 문자열이다.
				// "".split(",") 은 [""] 를 돌려주므로 아래 파싱에서 그대로 터진다 — null 도 함께 막는다.
				String[] strArray = freq_comb == null ? new String[0] : freq_comb.split(",");
				List<String> strList = Arrays.stream(strArray)
						.map(String::trim)
						.collect(Collectors.toList());
				List<Integer> freqList = new ArrayList<>();
				int stack = 0;
				if(!pumpCombTypeList.isEmpty()){
					for(Integer type:pumpCombTypeList){
						if(type == 1){
							freqList.add(0);
						}else if(type == 2) {
							// 가변속 펌프 수보다 주파수 값이 모자라거나 비어 있으면 0(미지정)으로 둔다.
							freqList.add(parseFreqOrZero(stack < strList.size() ? strList.get(stack) : null));
							stack++;
						}
					}
				}
				String result;
				if(!freqList.isEmpty()){
					result = joinWithComma(freqList);
				}else{
					result = "";
				}
				cal.put("PUMP_COMB", result);
			}
		}




		return filteredList;
	}

	/**
	 * integer List데이터를 ,로 연결해 String 으로 반환
	 * @param numbers integer List데이터
	 * @return ,로 구분된 단일 String
	 */
	public static String joinWithComma(List<Integer> numbers) {
		return numbers.stream()
				.map(String::valueOf)
				.collect(Collectors.joining(","));
	}

	/**
	 * 펌프 조합의 주파수 문자열을 정수로 변환한다.
	 * 값이 비어 있거나 숫자가 아니면 0(미지정)으로 본다 — 운전현황 전체가 500 으로 죽는 것을 막기 위함.
	 * @param freqStr 주파수 문자열 (null 가능)
	 * @return 주파수 정수값, 파싱 불가 시 0
	 */
	private static int parseFreqOrZero(String freqStr) {
		if (freqStr == null || freqStr.trim().isEmpty()) {
			return 0;
		}
		try {
			return Integer.parseInt(freqStr.trim());
		} catch (NumberFormatException e) {
			logger.warn("펌프 조합 주파수 파싱 실패 - 0 으로 처리한다. value={}", freqStr);
			return 0;
		}
	}

	/**
	 * 예측 및 EPANET 분석 데이터를 CSV로 변환해 반환하는 메서드
	 * @param map 날짜 및 펌프 그룹, 예측 및 분석이력 분기 parameter
	 * @return csv로 변환된 데이터
	 */
	public HashMap<String, Object> getExcelData(HashMap<String, Object> map){
		HashMap<String, Object> returnMap = new HashMap<>();

		//find 1: 배수지 수요량, 분기점 압력\ 2:분기점 압력, 분기점 유량
		String findStr = (String) map.get("findIdx");
		int findIdx = Integer.parseInt(findStr);

		if(findIdx == 1){
			HashMap<String, Object> tnkMap = new HashMap<>();
			map.put("type", 1);
			map.put("find", "press");
			List<HashMap<String, Object>> tnkPreFlow = drvnMapper.selectPreTnkFlowPressure(map);
			HashMap<String, List<Object>> tnkPreFlowMap = createFlowPressureData(tnkPreFlow, "pre","srttn", false);
			List<HashMap<String, Object>> tnkCurFlow = drvnMapper.selectCurTnkFlowPressure(map);
			HashMap<String, List<Object>> tnkCurFlowMap = createFlowPressureData(tnkCurFlow, "cur","srttn", false);


			//날짜 주입
			tnkMap.put("date", dataOutputDate(tnkPreFlow));

			List<String> srttnTnkList = new ArrayList<>(tnkCurFlowMap.keySet());


			tnkMap.put("srttn", srttnTnkList);
			HashMap<String, List<Double>> dataTnkMap = returnOptDate(tnkCurFlowMap, tnkPreFlowMap, srttnTnkList);
			tnkMap.putAll(dataTnkMap);
			returnMap.put("분기점 압력 예측결과", tnkMap);

			map.put("type", 2);
			map.put("find", "flow");
			HashMap<String, Object> pipeMap = new HashMap<>();
			List<HashMap<String, Object>> pipePreFlow = drvnMapper.selectPreTnkFlowPressure(map);
			HashMap<String, List<Object>> pipePreFlowMap = createFlowPressureData(pipePreFlow, "pre","srttn", false);
			List<HashMap<String, Object>> pipeCurFlow = drvnMapper.selectCurTnkFlowPressure(map);
			HashMap<String, List<Object>> pipeCurFlowMap = createFlowPressureData(pipeCurFlow, "cur","srttn", false);


			//날짜 주입
			pipeMap.put("date", dataOutputDate(pipePreFlow));

			List<String> srttnPipeList = new ArrayList<>(pipeCurFlowMap.keySet());
			pipeMap.put("srttn", srttnPipeList);
			HashMap<String, List<Double>> dataPipeMap = returnOptDate(pipeCurFlowMap, pipePreFlowMap, srttnPipeList);
			pipeMap.putAll(dataPipeMap);
			returnMap.put("배수지 수요량 예측결과", pipeMap);

		}else if (findIdx == 2){
			List<String> epaFlowNotSrttn = notSrttnMap.get("epaFlow");
			List<String> epaPressureNotSrttn = notSrttnMap.get("epaPressure");
			map.put("type", 1);
			HashMap<String, Object> tnkFlowMap = new HashMap<>();
			map.put("find", "flow");
			if(!epaFlowNotSrttn.isEmpty()){
				map.put("notSrttn", epaFlowNotSrttn);
			}
			List<HashMap<String, Object>> tnkPreFlow = drvnMapper.selectPreEPANETTnkFlowPressure(map);
			HashMap<String, List<Object>> tnkPreFlowMap = createFlowPressureData(tnkPreFlow, "pre","srttn", false);

			List<HashMap<String, Object>> tnkCurFlow = drvnMapper.selectCurTnkFlowPressure(map);
			HashMap<String, List<Object>> tnkCurFlowMap = createFlowPressureData(tnkCurFlow, "cur","srttn", false);

			tnkFlowMap.put("date", dataOutputDate(tnkPreFlow));

			List<String> srttnTnkFlowList = new ArrayList<>(tnkPreFlowMap.keySet());

			tnkFlowMap.put("srttn", srttnTnkFlowList);
			HashMap<String, List<Double>> dataTnkMap = returnOptDate(tnkCurFlowMap, tnkPreFlowMap, srttnTnkFlowList);
			tnkFlowMap.putAll(dataTnkMap);
			returnMap.put("분기점 유량 분석 결과", tnkFlowMap);

			HashMap<String, Object> tnkPressureMap = new HashMap<>();
			map.put("find", "press");
			map.remove("notSrttn");
			if(!epaPressureNotSrttn.isEmpty()){
				map.put("notSrttn", epaPressureNotSrttn);
			}
			List<HashMap<String, Object>> tnkPrePressure = drvnMapper.selectPreEPANETTnkFlowPressure(map);

			HashMap<String, List<Object>> tnkPrePressureMap = createFlowPressureData(tnkPrePressure, "pre","srttn", true);

			List<HashMap<String, Object>> tnkCurPressure = drvnMapper.selectCurTnkFlowPressure(map);
			HashMap<String, List<Object>> tnkCurPressureMap = createFlowPressureData(tnkCurPressure, "cur","srttn", false);

			tnkPressureMap.put("date", dataOutputDate(tnkPrePressure));

			List<String> srttnTnkPressureList = new ArrayList<>(tnkPrePressureMap.keySet());


			tnkPressureMap.put("srttn", srttnTnkPressureList);
			HashMap<String, List<Double>> dataTnkPressureMap = returnOptDate(tnkCurPressureMap, tnkPrePressureMap, srttnTnkPressureList);

			tnkPressureMap.putAll(dataTnkPressureMap);
			returnMap.put("분기점 압력 분석 결과", tnkPressureMap);
		}

		return returnMap;
	}

	/**
	 * 중복날짜 제거 데이터
	 * @param curData 실측 데이터(날짜 포함)
	 * @return 중복이 제거된 날짜 String List
	 */
	public List<String> dataOutputDate(List<HashMap<String, Object>> curData){

		LinkedHashSet<String> dateSet = new LinkedHashSet<>();
		for(HashMap<String, Object> map:curData){
			String date = (String) map.get("ts");
			dateSet.add(date);
		}
		List<String> returnData = new ArrayList<>(dateSet);
		return returnData;
	}

	/**
	 * 동일한 예측과 실측 데이터를 매핑하는 메서드
	 * @param curData 실측데이터
	 * @param preData 예측데이터
	 * @param keyList 동일 key
	 * @return 동일한 key의 실측 및 예측 데이터 map
	 */
	public HashMap<String, List<Double>> returnOptDate(HashMap<String, List<Object>> curData, HashMap<String, List<Object>> preData, List<String> keyList){
		HashMap<String, List<Double>> returnMap = new HashMap<>();
		for(String srttn : keyList){
			List<Object> curList = curData.get(srttn);
			List<Object> preList = preData.get(srttn);

			// 두 리스트가 모두 null이 아닌 경우에만 반복 실행
			if(curList != null && preList != null){
				returnMap.putAll(getHashMaps(curList, preList, srttn));
			}
		}
		return returnMap;
	}

	/**
	 * 동일한 예측 및 실측데이터 key값 생성 및 데이터 연결 메서드
	 * @param curList 실측데이터 list
	 * @param preList 예측데이터 list
	 * @param srttn 고유명칭
	 * @return 매핑된 실측 예측 데이터
	 */
	public HashMap<String, List<Double>> getHashMaps(List<Object> curList, List<Object> preList, String srttn) {
		int minSize = Math.min(curList.size(), preList.size());
		HashMap<String, List<Double>> returnMap = new HashMap<>();

		for (int i = 0; i < minSize; i++) {
			HashMap<String, Double> maps = new HashMap<>();
			double cur = (double) curList.get(i);

			double pre = (float) preList.get(i);

			double errorRate;

			if (!Double.isNaN(cur) && !Double.isNaN(pre) && cur != 0.0 && pre != 0.0) {
				errorRate = ((pre - cur) / cur) * 100;
			} else {
				errorRate = 0.0;
			}
			if(i == 0){
				List<Double> list1 = new ArrayList<>();
				List<Double> list2 = new ArrayList<>();
				List<Double> list3 = new ArrayList<>();
				returnMap.put(srttn+"cur", list1);
				returnMap.put(srttn+"pre", list2);
				returnMap.put(srttn+"errorRate", list3);
			}
			returnMap.get(srttn+"cur").add(Double.isNaN(cur) ? 0.0 : round(cur));
			returnMap.get(srttn+"pre").add(Double.isNaN(pre) ? 0.0 : round(pre));
			returnMap.get(srttn+"errorRate").add(round(errorRate));
		}
		return returnMap;
	}


	/**
	 * 반올림 메서드
	 * @param value 반올림할 값
	 * @return 반올림된 값
	 */
	public double round(double value) {
		if(value != 0.0 || !Double.isFinite(value)){

			return Math.round(value * 100) / 100.0;
		}else{
			return 0.0;
		}
	}

	/**
	 * 실측 펌프 사용 차트 데이터
	 * @param param 날짜 및 펌프 그룹
	 * @return 실측 펌프 사용유무 차트 데이터
	 */
	public LinkedHashMap<String, Object> getPumpUse(HashMap<String, Object> param) {
		LinkedHashMap<String, List<Integer>> pumpComb = new LinkedHashMap<>();
		param.put("first", false);
		List<HashMap<String, Object>> getPumpUse = drvnMapper.getPumpUse(param);
		List<HashMap<String, Object>> getPumpFreq = drvnMapper.getPumpFreqUse(param);
		param.put("first", true);
		List<HashMap<String, Object>> getPumpFirstUse = drvnMapper.getPumpUse(param);
		List<HashMap<String, Object>> getPumpFirstFreq = drvnMapper.getPumpFreqUse(param);
		getPumpUse.addAll(getPumpFirstUse);
		getPumpFreq.addAll(getPumpFirstFreq);

		List<HashMap<String, Object>> mergedList = new ArrayList<>();
		for (int i = 0; i<getPumpUse.size(); i++) {
			String ts = (String) getPumpUse.get(i).get("TS");
			int pumpIdx = (int) getPumpUse.get(i).get("PUMP_IDX");
			int pumpGrp = (int) getPumpUse.get(i).get("PUMP_GRP");
			mergedList.add(getPumpUse.get(i));
			if(!getPumpFreq.isEmpty()){
				for (HashMap<String, Object> freqMap : getPumpFreq) {
					String freqTs = (String) freqMap.get("TS");
					int freqPumpIdx = (int) freqMap.get("PUMP_IDX");
					int freqPumpGrp = (int) freqMap.get("PUMP_GRP");
					if (ts.equals(freqTs) && pumpIdx == freqPumpIdx && pumpGrp == freqPumpGrp) {
						HashMap<String, Object> mergedMap = new HashMap<>(mergedList.get(i));
						mergedMap.putAll(freqMap);
						mergedList.set(i, mergedMap);
						break;
					}
				}
			}
		}

		LinkedHashMap<String, List<Double>> freqMap = new LinkedHashMap<>();
		boolean freqTrue = false;
		for(HashMap<String, Object> map : mergedList){
			String ts = (String) map.get("TS");
			String pumpGrpNm = (String) map.get("PUMP_GRP_NM");
			int pump_typ = (int) map.get("PUMP_TYP");
			if(wpp_code.equals("wm")){
				pump_typ = 2;
			}
			int pump_idx = (int) map.get("PUMP_IDX");
			int pump_grp = (int) map.get("PUMP_GRP");

			String valueStr = (String) map.get("pump_use");
			double value = Double.parseDouble((valueStr));
			int pump_yn = 0;
			if(param.containsKey("pump_grp") && param.get("pump_grp") != null && !param.get("pump_grp").equals("0")){
				String param_grp_str = (String) param.get("pump_grp");
				int param_grp = Integer.parseInt(param_grp_str);
				if(param_grp == pump_grp){
					if(value > 0){
						pump_yn = 1;
					}
					pumpComb.computeIfAbsent(pumpGrpNm + pump_idx, k -> new ArrayList<>()).add(pump_yn);

					if(pump_typ == 2){
						freqTrue = true;
						double freq = 0.0;

						if(wpp_code.equals("wm")){
							Integer useInverter = drvnMapper.getWMFreqIdx(ts);
							if(pump_idx == useInverter){
								String freqStr = "0.0";
								if (map.containsKey("pump_freq")) {
									Object freqObj = map.get("pump_freq");
									if (freqObj != null && !freqObj.toString().isBlank()) {
										freqStr = freqObj.toString();
									}
								}
								freq = Double.parseDouble(freqStr);
							}
						} else {
							String freqStr = "0.0";
							if (map.containsKey("pump_freq")) {
								Object freqObj = map.get("pump_freq");
								if (freqObj != null && !freqObj.toString().isBlank()) {
									freqStr = freqObj.toString();
								}
							}
							freq = Double.parseDouble(freqStr);
							if(wpp_code.equals("gr") && pump_grp == 1 && freq != 0.0){
								freq = 0.6 * freq;
							}
						}
						freqMap.computeIfAbsent(pumpGrpNm + pump_idx, k -> new ArrayList<>()).add((double) Math.round(freq));
					}
				}
			} else {
				if(value > 0){
					pump_yn = 1;
				}
				pumpComb.computeIfAbsent(pumpGrpNm + pump_idx, k -> new ArrayList<>()).add(pump_yn);

				if(pump_typ == 2){
					freqTrue = true;
					String freqStr = "0.0";
					if (map.containsKey("pump_freq")) {
						Object freqObj = map.get("pump_freq");
						if (freqObj != null && !freqObj.toString().isBlank()) {
							freqStr = freqObj.toString();
						}
					}
					double freq = Double.parseDouble(freqStr);
					freqMap.computeIfAbsent(pumpGrpNm + pump_idx, k -> new ArrayList<>()).add((double) Math.round(freq));
				}
			}
		}

		LinkedHashMap<String, Object> returnMap = new LinkedHashMap<>(pumpComb);
		if(freqTrue){
			returnMap.put("freq", freqMap);
		}
		return returnMap;
	}

	/**
	 * 예측 사용 차트 데이터
	 * @param param 날짜 및 펌프 그룹
	 * @return 예측 펌프 사용유무 차트 데이터
	 */
	public LinkedHashMap<String, Object> predictionPumpCombination(HashMap<String, Object> param) {
		List<HashMap<String, Object>> pumpList = setPumpList;
		List<HashMap<String, Object>> grpList;
		String grp_str;
		if(param.containsKey("pump_grp")){
			grp_str = (String) param.get("pump_grp");
		}else{
			grp_str = "0";
		}

		int grp = Integer.parseInt(grp_str);
		if(wpp_code.equals("gs") || grp == 0){
			grpList = setPumpList;
		}else{
			grpList = pumpList.stream()
					.filter(map -> map.containsKey("PUMP_GRP") && map.get("PUMP_GRP").equals(grp))
					.collect(Collectors.toList());
		}


		LinkedHashMap<String, List<Integer>> combMap = new LinkedHashMap<>();
		LinkedHashMap<Integer, String> pumpMap = new LinkedHashMap<>();
		for(HashMap<String, Object> pump:grpList){
			String pump_grp = (String) pump.get("PUMP_GRP_DSC");

			int pump_idx = (int) pump.get("PUMP_IDX");
			int pump_grp_idx = (int) pump.get("PUMP_GRP_IDX");
			String pumpName = pump_grp+pump_grp_idx;
			pumpMap.put(pump_idx, pumpName);
		}

		param.put("first", false);
		List<HashMap<String, Object>> preCombList = drvnMapper.selectPrdctPumpCombYn(param);
		param.put("first", true);
		List<HashMap<String, Object>> preCombFirstList = drvnMapper.selectPrdctPumpCombYn(param);
		preCombList.addAll(preCombFirstList);
		LinkedHashMap<String, List<BigDecimal>> freqMap = new LinkedHashMap<>();
		boolean freqTrue = false;
		for(HashMap<String, Object> comb:preCombList){
			int pump_idx = (int) comb.get("PUMP_IDX");
			int pump_grp = (int) comb.get("PUMP_GRP");
			String pump_yn_str = (String) comb.get("PUMP_YN");
			int pump_yn = Integer.parseInt(pump_yn_str);
			String pump_nm = pumpMap.get(pump_idx);
			int pump_typ = (int) comb.get("PUMP_TYP");

			if(wpp_code.equals("wm")){
				pump_typ = 2;
			}
			if(param.containsKey("pump_grp") && param.get("pump_grp") != null && !param.get("pump_grp").equals("0")){
				String param_grp_str = (String) param.get("pump_grp");
				int param_grp = Integer.parseInt(param_grp_str);
				if(param_grp == pump_grp){
					if(!combMap.containsKey(pump_nm)){
						List<Integer> pumpYnList = new ArrayList<>();
						combMap.put(pump_nm, pumpYnList);
					}
					combMap.get(pump_nm).add(pump_yn);
				}
			}else{
				if(!combMap.containsKey(pump_nm)){
					List<Integer> pumpYnList = new ArrayList<>();
					combMap.put(pump_nm, pumpYnList);
				}
				combMap.get(pump_nm).add(pump_yn);
			}
			if(pump_typ == 2){
				BigDecimal freq = (BigDecimal) comb.get("FREQ");
				freqTrue = true;
				if(!freqMap.containsKey(pump_nm)){
					List<BigDecimal> pumpFreqList = new ArrayList<>();
					freqMap.put(pump_nm, pumpFreqList);
				}
				freqMap.get(pump_nm).add(freq);
			}
		}
		LinkedHashMap<String, Object> returnMap = new LinkedHashMap<>(combMap);
		if(freqTrue){
			freqMap.remove(null);
			returnMap.put("freq", freqMap);
		}

		return returnMap;
	}
	private double getCorrectedValue(Double value, String dstrbId, String nowDateTime) {
		// 기존 로직
		if (value == null || value == 0.0) {


			// nowDateTime을 추가 파라미터로 전달
			Double recentAvg = drvnMapper.selectAverageValueLast10Minutes(dstrbId, nowDateTime);
			if (recentAvg != null) {

				return recentAvg;
			} else {

				return 0.0; // 보정 실패 시 0 반환
			}
		}
		return value;
	}
	/**
	 * 펌프 조합 수동 insert
	 * @param map 조합 생성할 날짜 범위
	 * @return 생성 로그
	 */
	public StringBuffer pumpCombInsert(HashMap<String, Object> map) {
		drvnMapper.deleteInquiryData(map);


		StringBuffer logBuffer = new StringBuffer();
		if(wpp_code.equals("gs")){
			List<HashMap<String, Object>> gsData = drvnMapper.getInsertGsFlowPressure(map);
			for(HashMap<String, Object> data:gsData){
				String ts = (String) data.get("ts");
				double flow1 = getCorrectedValue((Double) data.get("flow1"), "Q_GS_OLD_Predict", ts);
				double pressure1 = getCorrectedValue((Double) data.get("pressure1"),"P_GS_OLD_Predict",ts);
				double flow2 = getCorrectedValue((Double) data.get("flow2"),"Q_GS_NEW_Predict",ts);
				double pressure2 = getCorrectedValue((Double) data.get("pressure2"),"P_GS_NEW_Predict",ts);
//				Double flow1 = (double) flow1Fl;
//				Double pressure1 = (double) pressure1Fl;
//				Double flow2 = (double) flow2Fl;
//				Double pressure2 = (double) pressure2Fl;

				double gosanFlow = flow1 + flow2;
				double gosanPressure = (0.025268 * pressure1) + (0.968549 * pressure2) + 0.064324;
				logBuffer.append("\n");
				logBuffer.append(drvnConfig.insertPumpComb(gosanFlow, gosanPressure, 0, ts));
			}

		}else{
			Set<Integer> pumpGrpSet = new LinkedHashSet<>(pumpDstrbIdMap.keySet());
			int minSize = 0;

			for(Integer id:pumpGrpSet){

				HashMap<String, String> ditrbMap = pumpDstrbIdMap.get(id);
				String flowId = ditrbMap.get("flow");
				String pressureId = ditrbMap.get("pressure");

				map.put("DSTRB_ID", flowId);
				List<HashMap<String, Object>> flow = drvnMapper.getInsertUsePrdctFlowPressure(map);


				map.put("DSTRB_ID", pressureId);
				List<HashMap<String, Object>> pressure = drvnMapper.getInsertUsePrdctFlowPressure(map);
				minSize = Math.min(flow.size(), pressure.size());
				for(int i=0;i<minSize;i++) {

					String ts = (String) flow.get(i).get("ts");
					float flowFl = (float) flow.get(i).get("value");
					float pressureFl = (float) pressure.get(i).get("value");
					Double flowDb = (double) flowFl;
					Double pressureDb = (double) pressureFl;
					logBuffer.append("\n");
					logBuffer.append(drvnConfig.insertPumpComb(flowDb, pressureDb, id, ts));
				}
			}

		}

		return logBuffer;
	}

	/**
	 * 펌프 조합 csv 반환 메서드
	 * @param param 조합 조회할 날짜 범위
	 * @return 펌프 조합 csv
	 */
	public HashMap<String, List<HashMap<String, Object>>> pumpCombinationExcelData(HashMap<String, Object> param) {
		HashMap<String, List<HashMap<String, Object>>> returnMap = new HashMap<>();

		List<HashMap<String, Object>> pumpList = setPumpList;
		Set<Integer> pump_grp = new HashSet<>();
		for(HashMap<String, Object> maps:pumpList){
			pump_grp.add((Integer) maps.get("PUMP_GRP"));
		}

		for(Integer pumpGrp:pump_grp){
			param.put("pump_grp", pumpGrp);
			List<HashMap<String, Object>> curPumpPowerList = drvnMapper.excelCurPumpPower(param);
			List<HashMap<String, Object>> curPumpFlowList = drvnMapper.excelCurPumpFlow(param);
			List<HashMap<String, Object>> curPumpPriList = drvnMapper.excelCurPumpPri(param);
			List<HashMap<String, Object>> prePumpList = drvnMapper.excelPrePumpData(param);
			returnMap.put(pumpGrp+"_cur_power", curPumpPowerList);
			returnMap.put(pumpGrp+"_cur_flow", curPumpFlowList);
			returnMap.put(pumpGrp+"_cur_pri", curPumpPriList);
			returnMap.put(pumpGrp+"_pre_pump", prePumpList);
			List<HashMap<String, Object>> filteredList = pumpList.stream()
					.filter(map -> map.containsKey("PUMP_GRP") && map.get("PUMP_GRP").equals(pumpGrp))
					.collect(Collectors.toList());
			for(HashMap<String, Object> pump:filteredList){
				int pump_idx = (int) pump.get("PUMP_IDX");

				param.put("pump_idx", pump_idx);
				List<HashMap<String, Object>> curPumpYnList = drvnMapper.excelCurPumpYn(param);
				List<HashMap<String, Object>> prePumpYnList = drvnMapper.excelPrePumpYn(param);
				returnMap.put(pumpGrp+"_"+pump_idx+"_cur_yn", curPumpYnList);
				returnMap.put(pumpGrp+"_"+pump_idx+"_pre_yn", prePumpYnList);
			}
		}

		return returnMap;
	}

	/**
	 * 펌프 대수, 전력원단위 차트 반환 메서드
	 * @param param 조회날짜, 펌프그룹
	 * @return 펌프 대수, 전력원단위 차트 반환 메서드
	 */
	public HashMap<String, Object> pumpPwrSrcUnitData(HashMap<String, Object> param) {
		String pump_grp_str = (String) param.get("pump_grp");
		int pump_grp = Integer.parseInt(pump_grp_str);
		String time = (String) param.get("time");
		String targetDate = (String) param.get("nowDate");
		String opt_idx = (String) param.get("opt_idx");

		HashMap<String, Object> returnMap = new HashMap<>();
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
		DateTimeFormatter outputFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
		DateTimeFormatter stdFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd 00:00:00");
		DateTimeFormatter lastFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd 23:45:00");


		LocalDateTime dateTime = LocalDateTime.parse(targetDate, formatter);
		// 현재 시간의 분을 가져옴
		int minute = dateTime.getMinute();

		// 15분으로 나눈 나머지를 계산
		int remainder = minute % 15;

		// 가장 가까운 작은 15분 단위의 분으로 변경
		int adjustedMinute = minute - remainder;

		// LocalDateTime 객체의 분 값을 변경하여 새로운 LocalDateTime 객체를 생성
		dateTime = dateTime.withMinute(adjustedMinute);
		targetDate = dateTime.format(formatter);
		param.put("nowDate", targetDate);


		List<String> dateTimeList = new ArrayList<>();

		LocalDateTime startDay = dateTime.toLocalDate().atStartOfDay();

		// 두 시간 사이의 차이를 계산
		Duration duration = Duration.between(startDay, dateTime);

		// 총 분 차이
		long totalMinutes = duration.toMinutes();

		// 15분 간격의 개수를 계산
		long numberOfIntervals = (totalMinutes / 15) + 1;


		// 자정부터 시작하여 15분 간격으로 날짜 데이터 생성
		LocalDateTime startOfDay = dateTime.toLocalDate().atStartOfDay();
		LocalDateTime endOfDay = startOfDay.plusDays(1).minusMinutes(1);

		for (LocalDateTime current = startOfDay; !current.isAfter(endOfDay); current = current.plusMinutes(15)) {
			dateTimeList.add(current.format(outputFormatter));
		}
		//날짜 갯수(96개)
		int dateListSize = dateTimeList.size();
		returnMap.put("dateTime", Collections.singletonList(dateTimeList));

		//param 날짜만 추출

		String startDate = dateTime.format(stdFormatter);

		HashMap<String, Object> nowMap = new HashMap<>();
		nowMap.put("startDate", startDate);
		nowMap.put("endDate", targetDate);


		//운전조합에서 정의돼 있는 펌프 그룹 가져옴
		Set<Integer> pumpGrpSet = new LinkedHashSet<>(pumpDstrbIdMap.keySet());

		//펌프 조합 리스트
		List<HashMap<String, Object>> pumpCombList = new ArrayList<>();
		List<Double> pumpPwrList;
		List<Double> pumpFlowList;

		if(pump_grp != 0){
			//계통별 구분
			if(pump_grp == 4){
				HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
				HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();
				Set<Integer> baMuJangGrp = new HashSet<>();

				for(int i = 4;i<=5;i++){
					baMuJangGrp.add(i);
					nowMap.put("pump_grp", i);
					pwrGrpMap.put(i, drvnMapper.pumpInstPwr(nowMap));
					flowGrpMap.put(i, drvnMapper.pumpInstFlowRate(nowMap));
				}
				pumpPwrList = listDoubleSum(pwrGrpMap, baMuJangGrp);
				pumpFlowList = listDoubleSum(flowGrpMap, baMuJangGrp);
			}else{

				nowMap.put("pump_grp", pump_grp);
				pumpPwrList = drvnMapper.pumpInstPwr(nowMap);
				if(wpp_code.equals("gr") && pump_grp == 3){
					List<Double> avgPwr = new ArrayList<>();
					for(Double pwr:pumpPwrList) {
						if (pwr == null) {
							// if it's null, treat as zero
							avgPwr.add(0.0);
						} else if (pwr != 0) {
							// only non-zero values get divided
							avgPwr.add(pwr / 3);
						}
					}
					pumpPwrList = avgPwr;
				}
				pumpFlowList = drvnMapper.pumpInstFlowRate(nowMap);
			}

		}else {
			//전체
			HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
			HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();

			for(int forGrp:pumpGrpSet){
				nowMap.put("pump_grp", forGrp);
				pwrGrpMap.put(forGrp, drvnMapper.pumpInstPwr(nowMap));
				flowGrpMap.put(forGrp, drvnMapper.pumpInstFlowRate(nowMap));
			}


			pumpPwrList = listDoubleSum(pwrGrpMap, pumpGrpSet);
			pumpFlowList = listDoubleSum(flowGrpMap, pumpGrpSet);

		}
		HashMap<Integer, List<HashMap<String, Object>>> pumpCombMap = new HashMap<>();
		if(opt_idx.equals("cur")){
			if(wpp_code.equals("gs")){
				for(int i = 1;i<=2;i++){
					nowMap.put("pump_grp", i);
					pumpCombList = drvnMapper.pumpActlMsrmCmbn(nowMap);
					pumpCombMap.put(i, pumpCombList);
				}
			}else if(pump_grp == 4){
				for(int i = 4;i<=5;i++){
					nowMap.put("pump_grp", i);
					pumpCombList = drvnMapper.pumpActlMsrmCmbn(nowMap);
					pumpCombMap.put(i, pumpCombList);
				}
			}else{
				nowMap.put("pump_grp", pump_grp);
				pumpCombList = drvnMapper.pumpActlMsrmCmbn(nowMap);
				pumpCombMap.put(pump_grp, pumpCombList);
			}
			nowMap.remove("pump_grp");
		}else if(opt_idx.equals("pre")) {
			if(wpp_code.equals("gs")){
				for(int i = 1;i<=2;i++){
					nowMap.put("pump_grp", i);
					pumpCombList = drvnMapper.pumpPrdcCmbn(nowMap);
					pumpCombMap.put(i, pumpCombList);
				}
			}else if(pump_grp == 4){
				for(int i = 4;i<=5;i++){
					nowMap.put("pump_grp", i);
					pumpCombList = drvnMapper.pumpPrdcCmbn(nowMap);
					pumpCombMap.put(i, pumpCombList);

				}
			}else{
				nowMap.put("pump_grp", pump_grp);
				pumpCombList = drvnMapper.pumpPrdcCmbn(nowMap);
				pumpCombMap.put(pump_grp, pumpCombList);
			}


			nowMap.remove("pump_grp");


			//n일전 계측 펌프 조합 이어 붙이기
			HashMap<String, Object> lastCombMap = new HashMap<>();
			int agoDays;
			if(time.equals("day")){
				agoDays = 1;
			}else if(time.equals("week")){
				agoDays = 7;
			}else {
				agoDays = 28;
			}
			int nowMinute = dateTime.getMinute();
			int plusMinite = 15;
			if(nowMinute % 15 !=0){
				int trashMinute = nowMinute % 15;
				plusMinite = 15 - trashMinute;
			}

			LocalDateTime agoPlusTargetDate = dateTime.minusDays(agoDays).plusMinutes(plusMinite);
			String agoMinutePlus = agoPlusTargetDate.format(formatter);
			String agoLastDate = agoPlusTargetDate.format(lastFormatter);
			lastCombMap.put("startDate", agoMinutePlus);
			lastCombMap.put("endDate", agoLastDate);

			if(wpp_code.equals("gs")){
				for(int i = 1;i<=2;i++){
					lastCombMap.put("pump_grp", i);
					pumpCombList =drvnMapper.pumpActlMsrmCmbn(lastCombMap);
					pumpCombMap.get(i).addAll(pumpCombList);
				}
			}else if(pump_grp == 4){
				for(int i = 4;i<=5;i++){
					lastCombMap.put("pump_grp", i);
					pumpCombList =drvnMapper.pumpActlMsrmCmbn(lastCombMap);
					pumpCombMap.get(i).addAll(pumpCombList);
				}
			}else{
				lastCombMap.put("pump_grp", pump_grp);
				pumpCombList =drvnMapper.pumpActlMsrmCmbn(lastCombMap);
				pumpCombMap.get(pump_grp).addAll(pumpCombList);
			}
			lastCombMap.remove("pump_grp");
		}
		List<Double> pumpComb = new ArrayList<>();
		Set<Integer> combGrpSet = pumpCombMap.keySet();
		for(Integer combGrp:combGrpSet){
			HashMap<Integer, Double> pumpLevelInfoMap = pumpLevelInfoGrpMap.get(combGrp);
			pumpCombList = pumpCombMap.get(combGrp);
			for(int j=0;j<pumpCombList.size();j++){
				String comb = (String) pumpCombList.get(j).get("PUMP_YN_RST");

				Double sum = 0.0;

				if(comb != null){
					String[] strArray = comb.split(",");
					List<String> strList = Arrays.stream(strArray)
							.map(String::trim)
							.collect(Collectors.toList());
					sum = strList.stream()
							.mapToInt(Integer::parseInt) // str을 int형으로 변환
							.mapToObj(key -> pumpLevelInfoMap.getOrDefault(key, 0.0)) // key에 대한 값 또는 0.0 반환
							.filter(Objects::nonNull) // null 값 필터링
							.mapToDouble(Double::doubleValue) // Double을 double로 변환
							.sum();

				}else {
					sum = null;
				}
				if (j < pumpComb.size()) {
					Double value = pumpComb.get(j);
					if (value != null) {
						if (sum != null) {
							pumpComb.set(j, sum + value);
						} else {
							pumpComb.set(j, value);
						}
					} else {
						pumpComb.set(j, sum);
					}
				} else {
					pumpComb.add(j, sum); // 주의: 리스트 크기를 벗어난 인덱스에 추가할 수 없습니다.
				}
			}
		}

		//펌프 가동 대수 계산



		// 계산된 펌프 가동 대수 리스트 Map 담기
		returnMap.put("pumpComb", pumpComb);
		// 현재까지의 계측값 데이터 담기
		List<Double> nowPwrCostList = pwrCostReturn(pumpFlowList, pumpPwrList);


		List<Double> plusPwrCost = pwrSrcUnitDayData(param);
		returnMap.put("plusPwrCostLust", plusPwrCost);


		returnMap.put("nowPwrCostList", nowPwrCostList);
		//평균 원단위 계산
		double pwrSum = 0.0;
		int avgSize;
		int minusSize = 0;
		if(opt_idx.equals("cur")){
			avgSize = nowPwrCostList.size();
			for(Double pwrCost:nowPwrCostList){
				if(pwrCost != null){
					pwrSum+=pwrCost;
				}else{
					minusSize++;
				}
			}
		}else{
			avgSize = nowPwrCostList.size();
			for (int i=0;i<avgSize;i++){
				if(plusPwrCost.get(i) != null){
					pwrSum+=plusPwrCost.get(i);
				}else{
					minusSize++;
				}
			}

		}
		double pwrAvg = pwrSum / (avgSize - minusSize);

		returnMap.put("nowPwrCost", pwrAvg);

		return returnMap;
	}

	/**
	 * 
	 * @param targetMap
	 * @param pump_grp
	 * @return
	 */
	public List<Double> listDoubleSum(HashMap<Integer, List<Double>> targetMap, Set<Integer> pump_grp){
		List<Double> returnList = new ArrayList<>();
		int minSize = Integer.MAX_VALUE;
		for(int grp:pump_grp){
			int tarGetSize = targetMap.get(grp).size();
			if (tarGetSize < minSize) {
				minSize = tarGetSize;
			}
		}

		for(int i = 0 ; i < minSize ; i++){
			boolean first = true;
			for(int grp:pump_grp){
				Double value = targetMap.get(grp).get(i);
				if(first){
					returnList.add(value);
					first = false;
				}else {
					Double useValue = returnList.get(i);
					if(useValue != null){
						if(value == null){
							returnList.set(i, useValue);
						}else {
							returnList.set(i, useValue + value);
						}
					}
				}

			}
		}

		return returnList;
	}

	/**
	 * 전력 원단위 계산
	 * @param flowList 유량 리스트
	 * @param pwrList 전력 리스트
	 *
	 * @return 전력 원단위 리스트
	 */
	public List<Double> pwrCostReturn(List<Double> flowList, List<Double> pwrList){
		List<Double> returnList = new ArrayList<>();
		int minSize = Math.min(flowList.size(), pwrList.size());
		for(int i = 0 ; i < minSize ; i++){
			Double flow = flowList.get(i);
			Double pwr = pwrList.get(i);
			Double pwrCost;
			if (flow == null || pwr == null) {
				pwrCost = null;
			} else if (pwr != 0 && flow != 0) {
				pwrCost = pwr / flow;
			} else {
				pwrCost = null;
			}
			returnList.add(pwrCost);
		}


		return returnList;
	}

	/**
	 * 전력 원단위 전일, 전주, 전월 값 계산
	 * @param param 시간 및 펌프 그룹, 전일-전주-전월 구분 값
	 * @return 전력원단위 데이터
	 */
	public List<Double> pwrSrcUnitDayData(HashMap<String, Object> param){
		List<Double> returnList = new ArrayList<>();

		String pump_grp_str = (String) param.get("pump_grp");
		int pump_grp = Integer.parseInt(pump_grp_str);
		String time = (String) param.get("time");
		String targetDate = (String) param.get("nowDate");
		String opt_idx = (String) param.get("opt_idx");

		HashMap<String, List<Object>> returnMap = new HashMap<>();
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
		DateTimeFormatter outputFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
		DateTimeFormatter stdFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd 00:00:00");
		DateTimeFormatter lastFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd 23:45:00");


		LocalDateTime dateTime = LocalDateTime.parse(targetDate, formatter);
		String startDate = dateTime.format(stdFormatter);




		HashMap<String, Object> nowMap = new HashMap<>();
		nowMap.put("startDate", startDate);
		nowMap.put("endDate", targetDate);
		int agoDays;
		if(time.equals("day")){
			agoDays = 1;
		}else if(time.equals("week")){
			agoDays = 7;
		}else {
			agoDays = 1;
		}


		//운전조합에서 정의돼 있는 펌프 그룹 가져옴
		Set<Integer> pumpGrpSet = new LinkedHashSet<>(pumpDstrbIdMap.keySet());


		List<Double> pumpPwrList = new ArrayList<>();
		List<Double> pumpFlowList = new ArrayList<>();
		if(opt_idx.equals("cur")){
			if(!time.equals("month")){

				LocalDateTime agoTime = dateTime.minusDays(agoDays);
				String agoStartDate = agoTime.format(stdFormatter);
				String agoEndDate = agoTime.format(lastFormatter);
				HashMap<String, Object> agoMap = new HashMap<>();
				agoMap.put("startDate", agoStartDate);
				agoMap.put("endDate", agoEndDate);
				if(pump_grp != 0){
					if(pump_grp == 4){
						HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
						HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();
						Set<Integer> baMuJangGrp = new HashSet<>();

						for(int i = 4;i<=5;i++){
							baMuJangGrp.add(i);
							agoMap.put("pump_grp", i);
							pwrGrpMap.put(i, drvnMapper.pumpInstPwr(agoMap));
							flowGrpMap.put(i, drvnMapper.pumpInstFlowRate(agoMap));
						}
						pumpPwrList = listDoubleSum(pwrGrpMap, baMuJangGrp);
						pumpFlowList = listDoubleSum(flowGrpMap, baMuJangGrp);
					}else{
						//계통별 구분
						agoMap.put("pump_grp", pump_grp);
						pumpPwrList = drvnMapper.pumpInstPwr(agoMap);
						if(wpp_code.equals("gr") && pump_grp == 3){
							List<Double> avgPwr = new ArrayList<>();
							for(Double pwr:pumpPwrList) {
								if(pwr != 0){
									avgPwr.add(pwr/3);
								}
							}
							pumpPwrList = avgPwr;
						}
						pumpFlowList = drvnMapper.pumpInstFlowRate(agoMap);
					}

				}else {
					//전체
					HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
					HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();

					for(int forGrp:pumpGrpSet){
						agoMap.put("pump_grp", forGrp);
						pwrGrpMap.put(forGrp, drvnMapper.pumpInstPwr(agoMap));
						flowGrpMap.put(forGrp, drvnMapper.pumpInstFlowRate(agoMap));
					}


					pumpPwrList = listDoubleSum(pwrGrpMap, pumpGrpSet);
					pumpFlowList = listDoubleSum(flowGrpMap, pumpGrpSet);

				}
			}else{
				HashMap<Integer, List<Double>> flowWeekMap = new HashMap<>();
				HashMap<Integer, List<Double>> pwrWeekMap = new HashMap<>();
				LinkedHashSet<Integer> weekGrp = new LinkedHashSet<>();
				for(int i = 1;i<=4;i++){
					weekGrp.add(i);
					LocalDateTime agoTime = dateTime.minusDays(agoDays * i);
					String agoStartDate = agoTime.format(stdFormatter);
					String agoEndDate = agoTime.format(lastFormatter);
					HashMap<String, Object> agoMap = new HashMap<>();
					agoMap.put("startDate", agoStartDate);
					agoMap.put("endDate", agoEndDate);
					if(pump_grp != 0){
						if(pump_grp == 4){
							//전체
							HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
							HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();

							Set<Integer> baMuJangGrp = new HashSet<>();

							for(int j = 4;j<=5;j++){
								baMuJangGrp.add(j);
								agoMap.put("pump_grp", j);
								pwrGrpMap.put(j, drvnMapper.pumpInstPwr(agoMap));
								flowGrpMap.put(j, drvnMapper.pumpInstFlowRate(agoMap));
							}



							pwrWeekMap.put(i, listDoubleSum(pwrGrpMap, baMuJangGrp));
							flowWeekMap.put(i, listDoubleSum(flowGrpMap, baMuJangGrp));
						}else{
							//계통별 구분
							agoMap.put("pump_grp", pump_grp);
							if(wpp_code.equals("gr") && pump_grp == 3){
								List<Double> pumpAgoPwrList = drvnMapper.pumpInstPwr(agoMap);
								List<Double> avgPwr = new ArrayList<>();
								for(Double pwr:pumpAgoPwrList) {
									if(pwr != 0){
										avgPwr.add(pwr/3);
									}
								}
								pwrWeekMap.put(i, avgPwr);

							}else{
								pwrWeekMap.put(i, drvnMapper.pumpInstPwr(agoMap));

							}
							flowWeekMap.put(i, drvnMapper.pumpInstFlowRate(agoMap));
						}
					}else {
						//전체
						HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
						HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();

						for(int forGrp:pumpGrpSet){
							agoMap.put("pump_grp", forGrp);
							pwrGrpMap.put(forGrp, drvnMapper.pumpInstPwr(agoMap));
							flowGrpMap.put(forGrp, drvnMapper.pumpInstFlowRate(agoMap));
						}



						pwrWeekMap.put(i, listDoubleSum(pwrGrpMap, pumpGrpSet));
						flowWeekMap.put(i, listDoubleSum(flowGrpMap, pumpGrpSet));

					}
				}
				pumpFlowList = listDoubleAvg(flowWeekMap, weekGrp);
				pumpPwrList = listDoubleAvg(pwrWeekMap, weekGrp);
			}

		}else if(opt_idx.equals("pre")){

			if(pump_grp != 0) {
				if(pump_grp == 4){
					//전체
					HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
					HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();



					Set<Integer> baMuJangGrp = new HashSet<>();

					for(int i = 4;i<=5;i++){
						baMuJangGrp.add(i);
						nowMap.put("pump_grp", i);
						List<Double> prdctFlowList = new ArrayList<>();
						List<Double> prdctPwrList = new ArrayList<>();

						List<HashMap<String, Object>> prdctData = drvnMapper.pumpPrdcCmbn(nowMap);
						for (HashMap<String, Object> map:prdctData){
							Float pwrfl = (Float) map.get("pwr");
							Float flowfl = (Float) map.get("flow");
							if(pwrfl != null){
								prdctPwrList.add((double) pwrfl);
							}else{
								prdctPwrList.add(null);
							}

							if(flowfl != null){
								prdctFlowList.add((double) flowfl);
							}else {
								prdctFlowList.add(null);
							}



						}
						pwrGrpMap.put(i, prdctPwrList);
						flowGrpMap.put(i, prdctFlowList);
					}


					pumpPwrList = listDoubleSum(pwrGrpMap, baMuJangGrp);
					pumpFlowList = listDoubleSum(flowGrpMap, baMuJangGrp);
				}else{
					//계통별 구분
					nowMap.put("pump_grp", pump_grp);
					List<HashMap<String, Object>> prdctData = drvnMapper.pumpPrdcCmbn(nowMap);
					for (HashMap<String, Object> map:prdctData){
						Float pwrfl = (Float) map.get("pwr");
						Float flowfl = (Float) map.get("flow");
						Double pwrDb = (pwrfl == null) ? null : Double.valueOf(pwrfl);
						Double flowDb = (flowfl == null) ? null : Double.valueOf(flowfl);
						pumpPwrList.add(pwrDb);
						pumpFlowList.add(flowDb);
					}
				}

			}else{
				//전체
				HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
				HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();



				for(int forGrp:pumpGrpSet){
					nowMap.put("pump_grp", forGrp);
					List<Double> prdctFlowList = new ArrayList<>();
					List<Double> prdctPwrList = new ArrayList<>();

					List<HashMap<String, Object>> prdctData = drvnMapper.pumpPrdcCmbn(nowMap);
					for (HashMap<String, Object> map:prdctData){
						Float pwrfl = (Float) map.get("pwr");
						Float flowfl = (Float) map.get("flow");
						if(pwrfl != null){
							prdctPwrList.add((double) pwrfl);
						}else{
							prdctPwrList.add(null);
						}

						if(flowfl != null){
							prdctFlowList.add((double) flowfl);
						}else {
							prdctFlowList.add(null);
						}



					}
					pwrGrpMap.put(forGrp, prdctPwrList);
					flowGrpMap.put(forGrp, prdctFlowList);

				}


				pumpPwrList = listDoubleSum(pwrGrpMap, pumpGrpSet);
				pumpFlowList = listDoubleSum(flowGrpMap, pumpGrpSet);
			}


			HashMap<String, Object> lastCombMap = new HashMap<>();
			int nowMinute = dateTime.getMinute();

			int plusMinite = 15;
			if(nowMinute % 15 !=0){
				int trashMinute = nowMinute % 15;
				plusMinite = 15 - trashMinute;
			}
			if(!time.equals("month")){
				LocalDateTime agoPlusTargetDate = dateTime.minusDays(agoDays).plusMinutes(plusMinite);
				String agoMinutePlus = agoPlusTargetDate.format(formatter);
				String agoLastDate = agoPlusTargetDate.format(lastFormatter);
				lastCombMap.put("startDate", agoMinutePlus);
				lastCombMap.put("endDate", agoLastDate);


				if(pump_grp != 0){
					if(pump_grp == 4){
						//전체
						HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
						HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();
						Set<Integer> baMuJangGrp = new HashSet<>();

						for(int i = 4;i<=5;i++){
							baMuJangGrp.add(i);
							lastCombMap.put("pump_grp", i);
							pwrGrpMap.put(i, drvnMapper.pumpInstPwr(lastCombMap));
							flowGrpMap.put(i, drvnMapper.pumpInstFlowRate(lastCombMap));
						}
						pumpPwrList.addAll(listDoubleSum(pwrGrpMap, baMuJangGrp));
						pumpFlowList.addAll(listDoubleSum(flowGrpMap, baMuJangGrp));

					}else{
						//계통별 구분
						lastCombMap.put("pump_grp", pump_grp);
						if(wpp_code.equals("gr") && pump_grp == 3){
							List<Double> lastAgoPwr = drvnMapper.pumpInstPwr(lastCombMap);
							List<Double> avgPwr = new ArrayList<>();
							for(Double pwr:lastAgoPwr) {
								if(pwr != 0){
									avgPwr.add(pwr/3);
								}
							}
							pumpPwrList.addAll(avgPwr);

						}else{

							pumpPwrList.addAll(drvnMapper.pumpInstPwr(lastCombMap));
						}
						pumpFlowList.addAll(drvnMapper.pumpInstFlowRate(lastCombMap));
					}
				}else {
					//전체
					HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
					HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();

					for(int forGrp:pumpGrpSet){
						lastCombMap.put("pump_grp", forGrp);
						pwrGrpMap.put(forGrp, drvnMapper.pumpInstPwr(lastCombMap));
						flowGrpMap.put(forGrp, drvnMapper.pumpInstFlowRate(lastCombMap));
					}


					pumpPwrList.addAll(listDoubleSum(pwrGrpMap, pumpGrpSet));
					pumpFlowList.addAll(listDoubleSum(flowGrpMap, pumpGrpSet));

				}
			}else {
				HashMap<Integer, List<Double>> flowWeekMap = new HashMap<>();
				HashMap<Integer, List<Double>> pwrWeekMap = new HashMap<>();
				LinkedHashSet<Integer> weekGrp = new LinkedHashSet<>();
				for(int i = 1;i<=4;i++){
					weekGrp.add(i);

					LocalDateTime agoPlusTargetDate = dateTime.minusDays(agoDays * i).plusMinutes(plusMinite);
					String agoMinutePlus = agoPlusTargetDate.format(formatter);
					String agoLastDate = agoPlusTargetDate.format(lastFormatter);
					lastCombMap.put("startDate", agoMinutePlus);
					lastCombMap.put("endDate", agoLastDate);

					if(pump_grp != 0){
						if(pump_grp == 4){
							//전체
							HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
							HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();

							Set<Integer> baMuJangGrp = new HashSet<>();

							for(int j = 4;j<=5;j++){
								baMuJangGrp.add(j);
								lastCombMap.put("pump_grp", j);
								pwrGrpMap.put(j, drvnMapper.pumpInstPwr(lastCombMap));
								flowGrpMap.put(j, drvnMapper.pumpInstFlowRate(lastCombMap));
							}


							flowWeekMap.put(i, listDoubleSum(flowGrpMap, baMuJangGrp));
							pwrWeekMap.put(i, listDoubleSum(pwrGrpMap, baMuJangGrp));
						}else{
							//계통별 구분
							lastCombMap.put("pump_grp", pump_grp);

							flowWeekMap.put(i, drvnMapper.pumpInstFlowRate(lastCombMap));
							if(wpp_code.equals("gr") && pump_grp == 3){
								List<Double> lastAgoPwr = drvnMapper.pumpInstPwr(lastCombMap);
								List<Double> avgPwr = new ArrayList<>();
								for(Double pwr:lastAgoPwr) {
									if(pwr != 0){
										avgPwr.add(pwr/3);
									}
								}

								pwrWeekMap.put(i, avgPwr);
							}else{
								pwrWeekMap.put(i, drvnMapper.pumpInstPwr(lastCombMap));

							}
						}
					}else {
						//전체
						HashMap<Integer, List<Double>> flowGrpMap = new HashMap<>();
						HashMap<Integer, List<Double>> pwrGrpMap = new HashMap<>();

						for(int forGrp:pumpGrpSet){
							lastCombMap.put("pump_grp", forGrp);
							pwrGrpMap.put(forGrp, drvnMapper.pumpInstPwr(lastCombMap));
							flowGrpMap.put(forGrp, drvnMapper.pumpInstFlowRate(lastCombMap));
						}


						flowWeekMap.put(i, listDoubleSum(flowGrpMap, pumpGrpSet));
						pwrWeekMap.put(i, listDoubleSum(pwrGrpMap, pumpGrpSet));

					}
				}
				pumpFlowList.addAll(listDoubleAvg(flowWeekMap, weekGrp));
				pumpPwrList.addAll(listDoubleAvg(pwrWeekMap, weekGrp));

			}

		}


		returnList = pwrCostReturn(pumpFlowList, pumpPwrList);

		return returnList;
	}

	/**
	 * 전월 평균에서 주단위 동일 요일 값 평균값 계산
	 * @param targetMap 계산할 데이터 map
	 * @param weekCount 주 구분 데이터
	 * @return 전월 주 평균 값
	 */
	public List<Double> listDoubleAvg(HashMap<Integer, List<Double>> targetMap, Set<Integer> weekCount){
		List<Double> returnList = new ArrayList<>();
		int minSize = Integer.MAX_VALUE;
		for(int grp:weekCount){
			int tarGetSize = targetMap.get(grp).size();
			if (tarGetSize < minSize) {
				minSize = tarGetSize;
			}
		}

		for (int i = 0; i < minSize; i++) {
			double sum = 0.0;
			int count = 0;

			for (int grp : weekCount) {
				Double value = targetMap.get(grp).get(i);
				if (value != null) {
					sum += value;
					count++;
				}
			}

			if (count > 0) {
				returnList.add(sum / count);
			} else {
				returnList.add(null);
			}
		}

		return returnList;
	}

	/**
	 * 최근 조합 생성 데이터 시간대 반환
	 * @return 최근 조합 시간대
	 */
	public String getPumpCombTime() {
		return drvnMapper.getPumpCombTime();
	}

	/**
	 * 예측조회, 분석이력 csv 반환 메서드
	 * @param map 시간 및 펌프그룹, csv 종류 키값
	 * @return csv 데이터 반환
	 */
	public SXSSFWorkbook xlsxCreate(HashMap<String, Object> map) {
		SXSSFWorkbook workbook = new SXSSFWorkbook();
		HashMap<String, Object> excelData = getExcelData(map);
		Set<String> sheetName = excelData.keySet();

		for(String key:sheetName){
			HashMap<String, Object> sheetDataMap = (HashMap<String, Object>) excelData.get(key);
			drvnExcelInsert(workbook, sheetDataMap, key);
		}



		return workbook;

	}
	/**
	 * 예측조회, 분석이력 csv 생성 메서드
	 * @param workbook poi엑셀 라이브러리 SXSSFWorkbook
	 * @param dataMap 예측조회 및 분석이력데이터
	 * @param sheetName 시트명
	 * @return csv 데이터 반환
	 */
	public void drvnExcelInsert(SXSSFWorkbook workbook, HashMap<String, Object> dataMap, String sheetName){
		Sheet sheet = workbook.createSheet(sheetName);

		List<String> srttnList = (List<String>) dataMap.get("srttn");
		List<String> dateList = (List<String>) dataMap.get("date");
		CellStyle style = workbook.createCellStyle();
		style.setAlignment(HorizontalAlignment.CENTER); // 가로 정렬
		style.setVerticalAlignment(VerticalAlignment.CENTER); // 세로 정렬

		Row row_0 = sheet.createRow(0);
		Row row_1 = sheet.createRow(1);
		row_1.createCell(0).setCellValue("번호");
		row_1.getCell(0).setCellStyle(style);
		row_1.createCell(1).setCellValue("시간");
		row_1.getCell(1).setCellStyle(style);
		sheet.setColumnWidth(1, 4000);
		int dataStart = 2;
		int datamiddle = 3;
		int dataEnd = 4;
		for(String srttn:srttnList){
			if(dataMap.get(srttn+"cur") == null){
				continue;
			}
			//분기점 및 배수지 네이밍 입력
			row_0.createCell(dataStart).setCellValue(srttn);
			row_0.getCell(dataStart).setCellStyle(style);
			sheet.addMergedRegion(new CellRangeAddress(0, 0, dataStart, dataEnd));
			row_1.createCell(dataStart).setCellValue("실제 계측량");
			row_1.getCell(dataStart).setCellStyle(style);
			row_1.createCell(datamiddle).setCellValue("예측 수요량");
			row_1.getCell(datamiddle).setCellStyle(style);
			row_1.createCell(dataEnd).setCellValue("오차율");
			row_1.getCell(dataEnd).setCellStyle(style);
			sheet.setColumnWidth(dataStart, 3600);
			sheet.setColumnWidth(datamiddle, 3600);
			sheet.setColumnWidth(dataEnd, 2500);
			dataStart = dataStart+3;
			datamiddle = datamiddle+3;
			dataEnd = dataEnd+3;
		}

		//날짜 및 시간정보 데이터 insert
		int idx = 1;
		int rowNum = 2;
		HashMap<String, Double> errorRateMap = new HashMap<>();
		for(int i = 0;i<dateList.size();i++){
			Row row = sheet.createRow(rowNum);
			row.createCell(0).setCellValue(idx);
			row.createCell(1).setCellValue(dateList.get(i));
			int curCell = 2;
			int preCell = 3;
			int errorCell = 4;
			for(String srttn:srttnList){

				String curCol = srttn+"cur";
				String preCol = srttn+"pre";
				String errCol = srttn+"errorRate";
				if(dataMap.get(curCol) == null){
					continue;
				}

				List<Double> curList = (List<Double>) dataMap.get(curCol);
				List<Double> preList = (List<Double>) dataMap.get(preCol);
				List<Double> errList = (List<Double>) dataMap.get(errCol);
				if(curList.size() <= i){
					continue;
				}

				double cur = (curList.get(i) != null && !curList.get(i).isNaN()) ? curList.get(i) : 0.0;
				double pre = (preList.get(i) != null && !preList.get(i).isNaN()) ? preList.get(i) : 0.0;
				double err = (errList.get(i) != null && !errList.get(i).isNaN()) ? errList.get(i) : 0.0;

				row.createCell(curCell).setCellValue(cur);
				row.createCell(preCell).setCellValue(pre);
				row.createCell(errorCell).setCellValue(err);
				if(i==0){
					errorRateMap.put(srttn+"size", (double) curList.size());
					errorRateMap.put(srttn+"sum", err);
				}else{
					errorRateMap.put(srttn+"sum", errorRateMap.get(srttn+"sum") + err);
				}
				curCell+=3;
				preCell+=3;
				errorCell+=3;
			}



			idx++;
			rowNum++;
		}
		//마지막 row
		Row lastRow = sheet.createRow(rowNum+1);
		int preCell = 3;
		int errorCell = 4;
		for(String srttn:srttnList) {

			if(errorRateMap.get(srttn+"size") == null){
				continue;
			}
			lastRow.createCell(preCell).setCellValue("평균오차율");
			lastRow.getCell(preCell).setCellStyle(style);
			lastRow.createCell(errorCell).setCellValue(round(errorRateMap.get(srttn+"sum")/errorRateMap.get(srttn+"size")));
			preCell+=3;
			errorCell+=3;
		}

	}

	/**
	 * 펌프조합, 유량, 압력 csv 생성 및 반환메서드
	 * @param param 날짜 정보
	 * @return 펌프조합, 유량, 압력 csv workbook
	 */
	public SXSSFWorkbook pumpYnExcelCreate(HashMap<String, Object> param) {
		HashMap<String, List<HashMap<String, Object>>> excelData = pumpCombinationExcelData(param);


		SXSSFWorkbook workbook = new SXSSFWorkbook();
		Sheet sheet = workbook.createSheet("펌프조합");
		CellStyle style = workbook.createCellStyle();
		style.setAlignment(HorizontalAlignment.CENTER); // 가로 정렬
		style.setVerticalAlignment(VerticalAlignment.CENTER); // 세로 정렬

		List<HashMap<String, Object>> pumpList = setPumpList;
		LinkedHashSet<Integer> pump_grp = new LinkedHashSet();
		for(HashMap<String, Object> maps:pumpList){
			pump_grp.add((Integer) maps.get("PUMP_GRP"));
		}
		//셀 갯수 판별(유량, 전력, 압력 : 실측 or 예측)
		int cellSize = pump_grp.size() * 3 * 2;
		LinkedHashSet<String> dataKeys = new LinkedHashSet<>();
		LinkedHashSet<String> headerKeys = new LinkedHashSet<>();
		for(Integer pumpGrp:pump_grp) {
			dataKeys.add(pumpGrp+"_cur_power");
			dataKeys.add(pumpGrp+"_cur_flow");
			dataKeys.add(pumpGrp+"_cur_pri");
			dataKeys.add(pumpGrp+"_pre_pump");
			List<HashMap<String, Object>> filteredList = pumpList.stream()
					.filter(map -> map.containsKey("PUMP_GRP") && map.get("PUMP_GRP").equals(pumpGrp))
					.collect(Collectors.toList());
			String grp_nm = (String) filteredList.get(0).get("PUMP_GRP_NM");
			headerKeys.add(grp_nm+" 실측 전력");
			headerKeys.add(grp_nm+" 예측 전력");
			headerKeys.add(grp_nm+" 실측 유량");
			headerKeys.add(grp_nm+" 예측 유량");
			headerKeys.add(grp_nm+" 실측 압력");
			headerKeys.add(grp_nm+" 예측 압력");
			//셀 갯수 판별(펌프 가동여부 : 실측 or 예측)
			cellSize += filteredList.size() * 2;
		}
		for(Integer pumpGrp:pump_grp) {
			List<HashMap<String, Object>> filteredList = pumpList.stream()
					.filter(map -> map.containsKey("PUMP_GRP") && map.get("PUMP_GRP").equals(pumpGrp))
					.collect(Collectors.toList());
			String grp_nm = (String) filteredList.get(0).get("PUMP_GRP_NM");
			for(HashMap<String, Object> pump:filteredList){
				int pump_idx = (int) pump.get("PUMP_IDX");
				dataKeys.add(pumpGrp+"_"+pump_idx+"_cur_yn");
				dataKeys.add(pumpGrp+"_"+pump_idx+"_pre_yn");
				headerKeys.add(grp_nm+" "+pump_idx+"번 실측 가동");
				headerKeys.add(grp_nm+" "+pump_idx+"번 예측 가동");
			}
		}
		int minSize = Integer.MAX_VALUE;
		for(String key:dataKeys){
			int size = excelData.get(key).size();
			if(size < minSize){
				minSize = size;
			}
		}
		int defaultGrp = (int) pumpList.get(0).get("PUMP_GRP");
		List<HashMap<String, Object>> curData = excelData.get(defaultGrp+"_cur_power");

		Row row_0 = sheet.createRow(0);
		row_0.createCell(0).setCellValue("번호");
		row_0.getCell(0).setCellStyle(style);
		row_0.createCell(1).setCellValue("시간");
		row_0.getCell(1).setCellStyle(style);
		sheet.setColumnWidth(1, 4000);
		int row_0_cell_idx = 2;
		for(String header:headerKeys){
			row_0.createCell(row_0_cell_idx).setCellValue(header);
			row_0.getCell(row_0_cell_idx).setCellStyle(style);
			sheet.setColumnWidth(row_0_cell_idx, 6000);
			row_0_cell_idx++;
		}

		int rowNum = 1;
		for(int i = 0 ; i < minSize ; i++){
			int cell_idx = 2;
			int idx = i+1;
			boolean datePass = true;
			Row row = sheet.createRow(rowNum);
			row.createCell(0).setCellValue(idx);

			for(String key:dataKeys){
				HashMap<String, Object> data = excelData.get(key).get(i);
				if(datePass){
					if(data.containsKey("TS")){
						String date = (String) data.get("TS");
						row.createCell(1).setCellValue(date);
					}

					datePass = false;
				}

				if(key.contains("pre_pump")){
					float flow = (float) data.get("PRDCT_MEAN");
					float pri = (float) data.get("TUBE_PRSR_PRDCT");
					float pwr = (float) data.get("PWR_PRDCT");
					row.createCell(cell_idx-2).setCellValue(Math.round(pwr * 100)/ 100.0);
					row.createCell(cell_idx).setCellValue(Math.round(flow * 100)/ 100.0);
					row.createCell(cell_idx+2).setCellValue(Math.round(pri * 100)/ 100.0);
					cell_idx+=3;
				}else if(key.contains("cur_yn")){
					String pumpYnStr = (String) data.get("value");
					double pumpYn = Double.parseDouble(pumpYnStr);
					String onOff;
					if(pumpYn>=1){
						onOff = "ON";
					}else{
						onOff = "OFF";
					}
					row.createCell(cell_idx).setCellValue(onOff);
					cell_idx++;
				}else if(key.contains("pre_yn")){
					String pumpYnStr = (String) data.get("value");
					int pumpYn = Integer.parseInt(pumpYnStr);
					String onOff;
					if(pumpYn>=1){
						onOff = "ON";
					}else{
						onOff = "OFF";
					}
					row.createCell(cell_idx).setCellValue(onOff);
					cell_idx++;
				}else if(key.contains("_cur_power")){
					double value = (double) data.get("value");
					row.createCell(cell_idx).setCellValue(Math.round(value * 100)/ 100.0);
					cell_idx++;
				}else if(key.contains("_cur_flow")){
					double value = (double) data.get("value");
					row.createCell(cell_idx+1).setCellValue(Math.round(value * 100)/ 100.0);
					cell_idx++;
				}else if(key.contains("_cur_pri")){
					double value = (double) data.get("value");
					row.createCell(cell_idx+2).setCellValue(Math.round(value * 100)/ 100.0);
					cell_idx++;
				}



			}
			rowNum++;
		}

		return workbook;

	}

	/**
	 * 펌프조합 및 주파수 csv 생성 및 반환메서드
	 * @param param 날짜 정보
	 * @return 펌프조합 및 주파수 및 주파수 csv workbook
	 */
	public SXSSFWorkbook pumpDrvnCombExcelCreate(HashMap<String, Object> param) {
		List<HashMap<String, String>> excelData = drvnMapper.pumpDrvnCombExcelData(param);


		SXSSFWorkbook workbook = new SXSSFWorkbook();
		Sheet sheet = workbook.createSheet("펌프조합");
		CellStyle style = workbook.createCellStyle();
		style.setAlignment(HorizontalAlignment.CENTER); // 가로 정렬
		style.setVerticalAlignment(VerticalAlignment.CENTER); // 세로 정렬


		LinkedHashSet<String> headerKeys = new LinkedHashSet<>();
		headerKeys.add("실측 조합");
		headerKeys.add("예측 조합");



		Row row_0 = sheet.createRow(0);
		row_0.createCell(0).setCellValue("일시");
		row_0.getCell(0).setCellStyle(style);
		sheet.setColumnWidth(0, 6000);
		int row_0_cell_idx = 1;
		for(String header:headerKeys){
			row_0.createCell(row_0_cell_idx).setCellValue(header);
			row_0.getCell(row_0_cell_idx).setCellStyle(style);
			sheet.setColumnWidth(row_0_cell_idx, 15000);
			row_0_cell_idx++;
		}
		List<HashMap<String, Object>> pumpList = setPumpList;
		//운문 날짜 조건

		if(wpp_code.equals("wm")){


			pumpList.forEach(map -> {

				map.put("PUMP_TYP", 1);

			});
		}
		LinkedHashMap<String, Integer> typeMap = new LinkedHashMap<>();
		for(HashMap<String, Object> map:pumpList){
			int pump_idx = (int) map.get("PUMP_IDX");
			String pump_idx_str = String.valueOf(pump_idx);
			int pump_typ = (int) map.get("PUMP_TYP");

			typeMap.put(pump_idx_str, pump_typ);
		}

		int rowNum = 1;
		for(HashMap<String, String> map:excelData){
			Row row = sheet.createRow(rowNum);
			String rgstr_time = map.get("rgstr_time");
			row.createCell(0).setCellValue(rgstr_time);
			row.getCell(0).setCellStyle(style);
			String cur_comb = map.get("cur_comb");
			String pre_comb = map.get("pre_comb");
			String cur_freq = map.get("cur_freq");
			String pre_freq = map.get("pre_freq");
			List<String> curCombList = new ArrayList<>();
			List<String> preCombList = new ArrayList<>();
			if(cur_comb != null && !cur_comb.trim().isEmpty()){
				String[] curCombArr = cur_comb.split(",");
				curCombList = Arrays.stream(curCombArr)
						.map(String::trim)
						.collect(Collectors.toList());
			}
			if(pre_comb != null && !pre_comb.trim().isEmpty()){
				String[] preCombArr = pre_comb.split(",");
				preCombList = Arrays.stream(preCombArr)
						.map(String::trim)
						.collect(Collectors.toList());
			}
			HashMap<String, Double> curFreqMap = new HashMap<>();
			if(cur_freq != null && !cur_freq.trim().isEmpty()){

				String[] freqArr = cur_freq.split(",");
				List<String> freqList = Arrays.stream(freqArr)
						.map(String::trim)
						.collect(Collectors.toList());
				List<String> combIvtPump = new ArrayList<>();
				for(String pump:curCombList){
					if(pump == null){
						break;
					}else{
						if(wpp_code.equals("wm")){
							if(pump.matches("1|2")){
								combIvtPump.add(pump);
								break;
							}
							if(pump.equals("4")){
								combIvtPump.add(pump);
								break;
							}
						}else {
							if(typeMap.get(pump) == 2){
								combIvtPump.add(pump);
							}
						}
					}
				}
				if(!combIvtPump.isEmpty()){
					for(int i = 0; i < combIvtPump.size();i++){
						String idx = combIvtPump.get(i);
						String freqStr = freqList.get(i);
						Double freqDb = Double.valueOf(freqStr);
						if(wpp_code.equals("gr1") && idx.equals("4")){
							freqDb = (double) Math.round(0.6 * freqDb);
						}
						curFreqMap.put(idx, freqDb);
					}

				}
			}

			HashMap<String, Double> preFreqMap = new HashMap<>();
			if(pre_freq != null && !pre_freq.trim().isEmpty()){

				String[] freqArr = pre_freq.split(",");
				List<String> freqList = Arrays.stream(freqArr)
						.map(String::trim)
						.collect(Collectors.toList());
				List<String> combIvtPump = new ArrayList<>();
				for(String pump:preCombList){
					if(pump == null){
						break;
					}else{
						if(wpp_code.equals("wm")){
							if(pump.matches("1|2")){
								combIvtPump.add(pump);
								break;
							}
							if(pump.equals("4")){
								combIvtPump.add(pump);
								break;
							}
						}else {
							if(typeMap.get(pump) == 2){
								combIvtPump.add(pump);
							}
						}
					}
				}
				if(!combIvtPump.isEmpty()){
					for(int i = 0; i < combIvtPump.size();i++){
						String idx = combIvtPump.get(i);
						String freqStr = freqList.get(i);
						Double freqDb = Double.valueOf(freqStr);
						preFreqMap.put(idx, freqDb);
					}

				}
			}
			List<String> finalCurCombList = new ArrayList<>();
			List<String> finalpreCombList = new ArrayList<>();
			if(!curCombList.isEmpty()){
				for(String curComb:curCombList){
					String pumpIdx;
					if(curFreqMap.containsKey(curComb)){
						pumpIdx = curComb+"("+curFreqMap.get(curComb)+"Hz)";
					}else {
						pumpIdx = curComb;
					}
					finalCurCombList.add(pumpIdx);
				}
			}
			if(!preCombList.isEmpty()){

				for(String preComb:preCombList){
					String pumpIdx;
					if(preFreqMap.containsKey(preComb)){
						pumpIdx = preComb+"("+preFreqMap.get(preComb)+"Hz)";
					}else {
						pumpIdx = preComb;
					}
					finalpreCombList.add(pumpIdx);
				}
			}
			String curPump = String.join(", ", finalCurCombList);
			String prePump = String.join(", ", finalpreCombList);
			row.createCell(1).setCellValue(curPump);
			row.createCell(2).setCellValue(prePump);
			row.getCell(1).setCellStyle(style);
			row.getCell(2).setCellStyle(style);
			rowNum ++;
		}
		return workbook;

	}

	public HashMap<String, Double> getGrLifePre() {
		return drvnMapper.getGrLifePre();
	}

	public String pumpManualOperation(String serverTime, int pump_grp, String oper) {
		List<String> returnComb = new ArrayList<>();
		HashMap<String, Double> freqMap = new HashMap<>();
		List<HashMap<String, Object>> grpList;
		List<HashMap<String, Object>> pumpList = setPumpList;
		int finalPump_grp = pump_grp;
		if(!wpp_code.equals("gs")){
			grpList = pumpList.stream()
					.filter(map -> map.containsKey("PUMP_GRP") && map.get("PUMP_GRP").equals(finalPump_grp))
					.collect(Collectors.toList());
		}else{
			grpList = pumpList;
		}

		List<HashMap<String, Object>> calList = drvnMapper.selectPumpCombCal();
		List<HashMap<String, Object>> grpFilteredList = calList.stream()
				.filter(map -> map.get("PUMP_GRP").equals(finalPump_grp))
				.collect(Collectors.toList());

		LinkedHashMap<String, Integer> typeMap = new LinkedHashMap<>();
		for(HashMap<String, Object> map:grpList){
			int pump_idx = (int) map.get("PUMP_IDX");
			String pump_idx_str = String.valueOf(pump_idx);
			int pump_typ = (int) map.get("PUMP_TYP");

			typeMap.put(pump_idx_str, pump_typ);
		}
		HashMap<String, Object> pumpUseParam = new HashMap<>();
		pumpUseParam.put("targetDate", serverTime);
		if(wpp_code.equals("gs")){
			pump_grp = 0;
		}
		pumpUseParam.put("pump_grp", pump_grp);

		String beforePumpUse = null;
		String beforeFreqUse = null;
		String opt_idx = null;
		String rgstr_time = null;
		Double flow = null;
		Double pressure = null;
		HashMap<String, Double> gosanFlowPressure = new HashMap<>();
		HashMap<String, String> beforePumpUseMap = drvnMapper.getPreUsePumpStatus(pumpUseParam);


		if(beforePumpUseMap != null){
			if(beforePumpUseMap.containsKey("PUMP_USE_RST")){
				String value = beforePumpUseMap.get("PUMP_USE_RST");
				if (value != null && !value.trim().isEmpty()) {
					beforePumpUse = value;
				}
			}

			if(beforePumpUseMap.containsKey("SPI_USE_RST")){
				String value = beforePumpUseMap.get("SPI_USE_RST");
				if (value != null && !value.trim().isEmpty()) {
					beforeFreqUse = value;
				}
			}

			if(beforePumpUseMap.containsKey("OPT_IDX")){
				String value = beforePumpUseMap.get("OPT_IDX");
				if (value != null && !value.trim().isEmpty()) {
					opt_idx = value;
				}
			}
			if(beforePumpUseMap.containsKey("RGSTR_TIME")){
				String value = beforePumpUseMap.get("RGSTR_TIME");
				if (value != null && !value.trim().isEmpty()) {
					rgstr_time = value;
				}
			}
			if(beforePumpUseMap.containsKey("PRDCT_MEAN")){
				Object prdctMeanValue = beforePumpUseMap.get("PRDCT_MEAN");

				if (prdctMeanValue instanceof Double) {
					// 이미 Double 타입인 경우
					flow = (Double) prdctMeanValue;
				} else if (prdctMeanValue instanceof String) {
					// String으로 저장되어 있을 경우 Double로 변환
					flow = Double.valueOf((String) prdctMeanValue);
				} else {
					// 다른 타입일 경우 처리
					throw new IllegalArgumentException("PRDCT_MEAN의 값이 처리할 수 없는 타입입니다.");
				}
			}
			if(beforePumpUseMap.containsKey("TUBE_PRSR_PRDCT")){
				Object tubePrsrPrdctValue = beforePumpUseMap.get("TUBE_PRSR_PRDCT");

				if (tubePrsrPrdctValue instanceof Double) {
					// 이미 Double 타입인 경우
					pressure = (Double) tubePrsrPrdctValue;
				} else if (tubePrsrPrdctValue instanceof String) {
					// String으로 저장되어 있을 경우 Double로 변환
					pressure = Double.valueOf((String) tubePrsrPrdctValue);
				} else {
					// 다른 타입일 경우 처리
					throw new IllegalArgumentException("TUBE_PRSR_PRDCT의 값이 처리할 수 없는 타입입니다.");
				}

			}
		}
		String agoPumpComb = beforePumpUse;
		String agoPumpFreq = beforeFreqUse;
		if(wpp_code.equals("gs")){
			pumpUseParam.put("pump_grp", 1);
			HashMap<String, String> gosanOld = drvnMapper.getPreUsePumpStatus(pumpUseParam);
			if(gosanOld != null) {
				if (gosanOld.containsKey("PRDCT_MEAN")) {
					Object prdctMeanValue = gosanOld.get("PRDCT_MEAN");

					if (prdctMeanValue instanceof Double) {
						// 이미 Double 타입인 경우
						gosanFlowPressure.put("flow1", (Double) prdctMeanValue);
					} else if (prdctMeanValue instanceof String) {
						// String으로 저장되어 있을 경우 Double로 변환
						gosanFlowPressure.put("flow1", Double.valueOf((String) prdctMeanValue));
					} else {
						// 다른 타입일 경우 처리
						gosanFlowPressure.put("flow1", 0.0);
						throw new IllegalArgumentException("PRDCT_MEAN의 값이 처리할 수 없는 타입입니다.");
					}
				}
				if (gosanOld.containsKey("TUBE_PRSR_PRDCT")) {
					Object tubePrsrPrdctValue = gosanOld.get("TUBE_PRSR_PRDCT");

					if (tubePrsrPrdctValue instanceof Double) {
						// 이미 Double 타입인 경우

						gosanFlowPressure.put("pressure1", (Double) tubePrsrPrdctValue);
					} else if (tubePrsrPrdctValue instanceof String) {
						// String으로 저장되어 있을 경우 Double로 변환

						gosanFlowPressure.put("pressure1", Double.valueOf((String) tubePrsrPrdctValue));
					} else {
						gosanFlowPressure.put("pressure1", 0.0);
						// 다른 타입일 경우 처리
						throw new IllegalArgumentException("TUBE_PRSR_PRDCT의 값이 처리할 수 없는 타입입니다.");
					}

				}
			}
			pumpUseParam.put("pump_grp", 2);
			HashMap<String, String> gosanNew = drvnMapper.getPreUsePumpStatus(pumpUseParam);
			if(gosanNew != null) {
				if (gosanNew.containsKey("PRDCT_MEAN")) {
					Object prdctMeanValue = gosanNew.get("PRDCT_MEAN");

					if (prdctMeanValue instanceof Double) {
						// 이미 Double 타입인 경우
						gosanFlowPressure.put("flow2", (Double) prdctMeanValue);
					} else if (prdctMeanValue instanceof String) {
						// String으로 저장되어 있을 경우 Double로 변환
						gosanFlowPressure.put("flow2", Double.valueOf((String) prdctMeanValue));
					} else {
						// 다른 타입일 경우 처리
						gosanFlowPressure.put("flow2", 0.0);
						throw new IllegalArgumentException("PRDCT_MEAN의 값이 처리할 수 없는 타입입니다.");
					}
				}
				if (gosanNew.containsKey("TUBE_PRSR_PRDCT")) {
					Object tubePrsrPrdctValue = gosanNew.get("TUBE_PRSR_PRDCT");

					if (tubePrsrPrdctValue instanceof Double) {
						// 이미 Double 타입인 경우

						gosanFlowPressure.put("pressure2", (Double) tubePrsrPrdctValue);
					} else if (tubePrsrPrdctValue instanceof String) {
						// String으로 저장되어 있을 경우 Double로 변환

						gosanFlowPressure.put("pressure2", Double.valueOf((String) tubePrsrPrdctValue));
					} else {
						gosanFlowPressure.put("pressure2", 0.0);
						// 다른 타입일 경우 처리
						throw new IllegalArgumentException("TUBE_PRSR_PRDCT의 값이 처리할 수 없는 타입입니다.");
					}

				}
			}

		}

		if(beforePumpUse != null && !beforePumpUse.isEmpty()) {
			String[] strArray = beforePumpUse.split(",");
			List<String> strList = Arrays.stream(strArray)
					.map(String::trim)
					.collect(Collectors.toList());
			List<String> combIvtPump = new ArrayList<>();
			returnComb = strList;
			for (String pump : strList) {
				if (typeMap.containsKey(pump)) {
					if (typeMap.get(pump) == 2) {
						combIvtPump.add(pump);
					}
				}
			}
			HashMap<String, Double> beforeFreqMap = new HashMap<>();
			if (beforeFreqUse != null && !beforeFreqUse.trim().isEmpty() && !combIvtPump.isEmpty()) {

				String[] freqArr = beforeFreqUse.split(",");
				List<String> freqList = Arrays.stream(freqArr)
						.map(String::trim)
						.collect(Collectors.toList());
				for (int i = 0; i < combIvtPump.size(); i++) {
					String idx = combIvtPump.get(i);
					Double freqDb = 0.0;

					String freqStr = freqList.get(i);
					freqDb = Double.valueOf(freqStr);
					beforeFreqMap.put(idx, freqDb);

				}


				freqMap = beforeFreqMap;
			}
		}else{
			returnComb = new ArrayList<>();
		}
		HashMap<Integer, List<String>> gonsanAllReturnComb = new HashMap<>();
		boolean ba_mujang = false;
		if(wpp_code.equals("gs")){
			double nowPumpLevel = 0.0;
			HashMap<Integer, Double> levelMap = pumpLevelInfoGrpMap.get(0);

			for(String pump:returnComb){

				int idx = Integer.parseInt(pump);

				nowPumpLevel += levelMap.get(idx);
			}

			List<String> forCmb= Arrays.asList("4", "5", "6", "8");
			List<String> fiveCmb = Arrays.asList("2", "4", "5", "6", "11");
			if(nowPumpLevel == 4.0){
				if (new HashSet<>(forCmb).equals(new HashSet<>(returnComb))){
					//4.0대 조합 : 4대(2순위)
					if(oper.equals("up")){
						//상위 4.0대
						returnComb = fiveCmb;
					}else if(oper.equals("down")){
						//3.5대
						returnComb = new ArrayList<>();
						returnComb.add("4");
						returnComb.add("5");
						returnComb.add("6");
						returnComb.add("11");
					}
				} else if (new HashSet<>(fiveCmb).equals(new HashSet<>(returnComb))) {
					//4.0대 조합 : 5대(1순위)
					if(oper.equals("up")){
						//4.5대
						returnComb = new ArrayList<>();
						returnComb.add("2");
						returnComb.add("4");
						returnComb.add("5");
						returnComb.add("6");
						returnComb.add("8");
					}else if(oper.equals("down")){
						//하위 4.0대
						returnComb = forCmb;
					}
				}else {
					//알 수 없는 조합
					return "not down";
				}
			}else{
				double optPumpLevel = 0.0;
				if(oper.equals("up")){
					optPumpLevel = nowPumpLevel + 0.5;

				}else if(oper.equals("down")){
					optPumpLevel = nowPumpLevel - 0.5;
				}

				if(optPumpLevel < 3.0){
					return "not down";
				} else if(optPumpLevel == 3.0){
					returnComb = new ArrayList<>();
					returnComb.add("2");
					returnComb.add("4");
					returnComb.add("6");
					returnComb.add("11");
				} else if (optPumpLevel > 5.0) {
					return "not plus";
				}else if(optPumpLevel == 3.5){
					returnComb = new ArrayList<>();
					returnComb.add("4");
					returnComb.add("5");
					returnComb.add("6");
					returnComb.add("11");
				} else if (optPumpLevel == 4.0) {
					returnComb = forCmb;
				} else if (optPumpLevel == 4.5) {
					returnComb = new ArrayList<>();
					returnComb.add("2");
					returnComb.add("4");
					returnComb.add("5");
					returnComb.add("6");
					returnComb.add("8");
				} else if (optPumpLevel == 5.0) {
					returnComb = new ArrayList<>();
					returnComb.add("4");
					returnComb.add("5");
					returnComb.add("6");
					returnComb.add("8");
					returnComb.add("9");
				} else{
					return "not plus";
				}
			}
			for(String pump:returnComb){
				int idx = Integer.parseInt(pump);
				if(idx <= 7){
					if(!gonsanAllReturnComb.containsKey(1)){
						gonsanAllReturnComb.put(1, new ArrayList<>());
					}
					gonsanAllReturnComb.get(1).add(pump);
				}else{
					if(!gonsanAllReturnComb.containsKey(2)){
						gonsanAllReturnComb.put(2, new ArrayList<>());
					}
					gonsanAllReturnComb.get(2).add(pump);
				}
			}

		}else if(wpp_code.equals("ba") && pump_grp == 1){
			int nowSize = returnComb.size();
			if(oper.equals("up")){
				List<String> checkComb1 = List.of("2","4","6");
				List<String> checkComb2 = List.of("4","5","6");

				if(new HashSet<>(checkComb1).equals(new HashSet<>(returnComb))){
					returnComb = new ArrayList<>();
					returnComb.add("4");
					returnComb.add("5");
					returnComb.add("6");
					freqMap = new HashMap<>();
					freqMap.put("4", 60.0);
				}else if(new HashSet<>(checkComb2).equals(new HashSet<>(returnComb))){
					return "not up";
				}else{
					returnComb = new ArrayList<>();
					returnComb.add("2");
					returnComb.add("4");
					returnComb.add("6");
					freqMap = new HashMap<>();
					freqMap.put("4", 60.0);
				}

			}else if(oper.equals("down")){
				List<String> checkComb1 = List.of("4","6");
				List<String> checkComb2 = List.of("2","4","6");

				if(new HashSet<>(checkComb1).equals(new HashSet<>(returnComb))){
					return "not down";
				}else if(new HashSet<>(checkComb2).equals(new HashSet<>(returnComb))){
					returnComb = new ArrayList<>();
					returnComb.add("4");
					returnComb.add("6");
					freqMap = new HashMap<>();
					freqMap.put("4", 60.0);
				}else{
					returnComb = new ArrayList<>();
					returnComb.add("2");
					returnComb.add("4");
					returnComb.add("6");
					freqMap = new HashMap<>();
					freqMap.put("4", 60.0);
				}

			}
		}else if(wpp_code.equals("ba") && pump_grp == 2){
			Double nowFreq = freqMap.get("7");
			if(oper.equals("up")){

				if(nowFreq == 60.0){
					return "not plus";
				}
				if( nowFreq != 0.0){
					freqMap = new HashMap<>();
					double returnFreq = 0;
					double[] freqSteps = {50.0, 52.0, 54.0, 56.0, 58.0};
					double[] returnFreqs = {52.0, 54.0, 56.0, 58.0, 60.0};

					for (int i = 0; i < freqSteps.length; i++) {
						if (nowFreq == freqSteps[i]) {
							returnFreq = returnFreqs[i];

							break;
						}
					}

					if (nowFreq < 50.0) {
						returnFreq = 50.0;
					}
					freqMap.put("7", returnFreq);
				}


			}else if(oper.equals("down")){

				if(nowFreq <= 50.0){
					return "not down";
				}

				double returnFreq;
				freqMap = new HashMap<>();


				double[] freqSteps = {52.0, 54.0, 56.0, 58.0, 60.0};
				double[] returnFreqs = {50.0, 52.0, 54.0, 56.0, 58.0};

				for (int i = 0; i < freqSteps.length; i++) {
					if (nowFreq == freqSteps[i]) {
						returnFreq = returnFreqs[i];
						freqMap.put("7", returnFreq);
						break;
					}
				}


			}
		}else if(wpp_code.equals("ba") && pump_grp == 3){
			int nowSize = returnComb.size();
			if(oper.equals("up")){

				if(nowSize == 3){
					return "not plus";
				}
				returnComb = new ArrayList<>();

				returnComb.add("11");
				returnComb.add("13");
				returnComb.add("14");

			}else if(oper.equals("down")){
				if(nowSize == 2){
					return "not down";
				}
				returnComb = new ArrayList<>();

				returnComb.add("11");
				returnComb.add("14");

			}
		}else if(wpp_code.equals("ba") && pump_grp == 4){
			int nowSize = returnComb.size();
			Double nowFreq = 0.0;
			if(nowSize == 1){
				nowFreq = freqMap.get("16");
			}
			if(oper.equals("up")){


				if(nowSize == 1 && nowFreq == 60.0){
					return "not plus";
				}
				returnComb = new ArrayList<>();
				returnComb.add("16");
				freqMap = new HashMap<>();
				if(nowSize == 1 && nowFreq != 0.0){
					double[] freqSteps = {50.0, 52.0, 54.0, 56.0, 58.0, 60.0};
					double returnFreq = 56.0;

					for (int i = 0; i < freqSteps.length - 1; i++) {
						if (nowFreq == freqSteps[i]) {
							returnFreq = freqSteps[i + 1];
							break;
						}
					}

					if (nowFreq < 50.0) {
						returnFreq = 50.0;
					}
					freqMap.put("16", returnFreq);
				}else{
					freqMap.put("16", 46.0);
				}


			}else if(oper.equals("down")){
				if(nowSize == 0){
					return "not down";
				}
				if(nowSize == 1){
					double returnFreq;
					freqMap = new HashMap<>();
					if(nowFreq == 45){
						return "not down";
					}
					if (nowFreq == 50.0 || nowFreq == 46.0) {
						freqMap.put("16", 45.0);
					} else {
						double[] freqSteps = {52.0, 54.0, 56.0, 58.0, 60.0};
						double[] returnFreqs = {50.0, 52.0, 54.0, 56.0, 58.0};

						for (int i = 0; i < freqSteps.length; i++) {
							if (nowFreq == freqSteps[i]) {
								returnFreq = returnFreqs[i];
								freqMap.put("16", returnFreq);
								break;
							}
						}
					}
				}
			} else if (oper.equals("stop")) {
				if(nowSize == 0){
					return "not down";
				}else{
					freqMap.put("16", 45.0);
				}
			}
		}else if(wpp_code.equals("ba") && pump_grp == 5){
			int nowSize = returnComb.size();
			Double nowFreq = 0.0;
			if(nowSize == 1){
				nowFreq = freqMap.get("17");
			}
			if(oper.equals("up")){

				if (nowSize == 1 && nowFreq == 60.0) {
					return "not plus";
				}

				returnComb = new ArrayList<>();
				returnComb.add("17");

				freqMap = new HashMap<>();

				if (nowSize == 1 && nowFreq != 0.0) {
					Map<Double, Double> freqMapping = new HashMap<>();
					freqMapping.put(50.0, 52.0);
					freqMapping.put(52.0, 55.0);
					freqMapping.put(55.0, 58.0);
					freqMapping.put(58.0, 60.0);

					double returnFreq = freqMapping.getOrDefault(nowFreq, 55.0);
					freqMap.put("17", returnFreq);
				} else {
					freqMap.put("17", 55.0);
				}



			}else if(oper.equals("down")){
				if (nowSize == 0) {
					return "not down";
				}

				if (nowSize == 1) {
					freqMap = new HashMap<>();

					Map<Double, Double> freqMapping = new HashMap<>();
					freqMapping.put(52.0, 50.0);
					freqMapping.put(55.0, 52.0);
					freqMapping.put(58.0, 55.0);
					freqMapping.put(60.0, 58.0);

					if (nowFreq == 50.0) {
						returnComb = new ArrayList<>();
					} else {
						double returnFreq = freqMapping.getOrDefault(nowFreq, 52.0); // 기본 값은 52.0
						freqMap.put("17", returnFreq);
					}
				}
			} else if (oper.equals("stop")) {
				if(nowSize == 0){
					return "not down";
				}else{
					returnComb = new ArrayList<>();
					freqMap = new HashMap<>();
				}
			}
		}else if(wpp_code.equals("gr")){
			int nowSize = returnComb.size();
			if(pump_grp == 1){
				if(oper.equals("up")){
					if(nowSize == 3){
						return "not up";
					}
					returnComb = drvnConfig.getPumpCombination(pump_grp, 3, 1);
				} else if (oper.equals("down")) {
					if(nowSize == 2){
						return "not down";
					}
					returnComb = drvnConfig.getPumpCombination(pump_grp, 2, 1);
				}
			} else if (pump_grp == 3) {
				if (oper.equals("stop")) {
					if(nowSize == 0){
						return "not down";
					}else{
						returnComb = new ArrayList<>();
						freqMap = new HashMap<>();
					}
				} else if(oper.equals("up")){
					if(nowSize >= 1){
						return "not up";
					}
					List<String> strList = new ArrayList<>();
					strList.add("11");
					DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
					//날짜 치환
					LocalDateTime dateTime = LocalDateTime.parse(rgstr_time, formatter);
					DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
					int week =  dayOfWeek.getValue();
					HolidayChecker holidayChecker = new HolidayChecker();
					Boolean passDayBool = holidayChecker.isPassDay(rgstr_time);

					int wm_day = dateTime.getDayOfMonth();

					if(passDayBool || week >= 6){
						wm_day = 3;
					}
					int finalWm_day = wm_day;
					strList = strList.stream()
							.map(str -> {
								if (finalWm_day % 2 == 0) {
									// wm_day가 짝수일 경우
									if (str.equals("11")) {
										return "10";
									}
								} else {
									// wm_day가 홀수일 경우
									if (str.equals("11")) {
										return "11";
									}
								}
								return str;
							})
							.collect(Collectors.toList());

					returnComb = strList;

					freqMap = new HashMap<>();
					if(returnComb.contains("11")){
						freqMap.put("11", 60.0);
					}
				}
			}
		}else{
			String ts = rgstr_time;
			DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
			List<HashMap<String, Object>> collectList = new ArrayList<>();
			//날짜 치환
			LocalDateTime dateTime = LocalDateTime.parse(ts, formatter);
			LinkedHashSet<Integer> uniqueCIdx = new LinkedHashSet<>();
			//c_idx 전처리 조합식 순서대로 Set에 담기
			for(HashMap<String, Object> maps:grpFilteredList){
				uniqueCIdx.add((Integer) maps.get("C_IDX"));
			}
			for(int cidx:uniqueCIdx){
				List<HashMap<String, Object>> cIdxFilteredList = grpFilteredList.stream()
						.filter(map -> map.get("C_IDX").equals(cidx))
						.collect(Collectors.toList());
				HashMap<String, Object> collectMap = new HashMap<>();
				collectMap.put("c_idx", cidx);
				String pump_comb = null;
				String freq = null;

				for(HashMap<String, Object> map:cIdxFilteredList){
					int c_ord = (int) map.get("C_ORD");

					if(c_ord == 1){
						pump_comb = (String) map.get("PUMP_COMB");

					}else{
						if(map.get("PUMP_COMB") != null){
							freq = (String) map.get("PUMP_COMB");
						}

					}
				}
				String[] strArray = pump_comb.split(",");
				List<String> strList = Arrays.stream(strArray)
						.map(String::trim)
						.collect(Collectors.toList());
				if((wpp_code.equals("wm"))){
					//운문 짝수일 2번이 1번으로 홀수일은 1번은 2번으로 조합 변경
					int wm_day = dateTime.getDayOfMonth();
					int finalWm_day = wm_day;
					strList = strList.stream()
							.map(str -> {
								if (finalWm_day % 2 == 0) {
									// wm_day가 짝수일 경우
									if (str.equals("1")) {
										return "2";
									}
								} else {
									// wm_day가 홀수일 경우
									if (str.equals("2")) {
										return "1";
									}
								}
								return str;
							})
							.collect(Collectors.toList());
				}
				if(wpp_code.equals("gr") && pump_grp == 3){
					//고령 선남가압장 짝수일 2번, 홀수일 3번 조합 생성
					DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
					int week =  dayOfWeek.getValue();
					HolidayChecker holidayChecker = new HolidayChecker();
					Boolean passDayBool = holidayChecker.isPassDay(ts);

					int wm_day = dateTime.getDayOfMonth();

					if(passDayBool || week >= 6){
						wm_day = 3;
					}
					int finalWm_day = wm_day;
					strList = strList.stream()
							.map(str -> {
								if (finalWm_day % 2 == 0) {
									// wm_day가 짝수일 경우
									if (str.equals("11")) {
										return "10";
									}
								} else {
									// wm_day가 홀수일 경우
									if (str.equals("11")) {
										return "11";
									}
								}
								return str;
							})
							.collect(Collectors.toList());
				}
				//펌프 조합
				collectMap.put("pumpComb", strList);
				HashMap<String, Double> calFreqMap = new HashMap<>();
				if(freq != null && !freq.trim().isEmpty()){

					String[] freqArr = freq.split(",");
					List<String> freqList = Arrays.stream(freqArr)
							.map(String::trim)
							.collect(Collectors.toList());
					List<String> combIvtPump = new ArrayList<>();
					for(String pump:strList){
						if(pump == null){
							break;
						}else{
							if(typeMap.get(pump) == 2){
								combIvtPump.add(pump);
							}
						}
					}
					if(!combIvtPump.isEmpty()){
						for(int i = 0; i < combIvtPump.size();i++){
							String idx = combIvtPump.get(i);
							String freqStr = freqList.get(i);
							Double freqDb = Double.valueOf(freqStr);
							calFreqMap.put(idx, freqDb);
						}

						collectMap.put("freq", calFreqMap);
					}
				}
				collectList.add(collectMap);
			}
			int lastIdx = collectList.size() - 1;
			int nowCalPoint = -1;
			for(HashMap<String, Object> map:collectList){
				if(nowCalPoint == -1){
					int idx = (int) map.get("c_idx");
					List<String> calComb = (List<String>) map.get("pumpComb");
					HashMap<String, Double> calFreqMap = (HashMap<String, Double>) map.get("freq");
					if(new HashSet<>(calComb).equals(new HashSet<>(returnComb))){
						if(calFreqMap != null && !calFreqMap.isEmpty()){
							if(!calFreqMap.equals(freqMap)){
								continue;
							}
						}
						nowCalPoint = idx;
						break;
					}
				}
			}
			if(oper.equals("up")){
				nowCalPoint += 1;
			}else{
				nowCalPoint -= 1;
			}

			if(nowCalPoint > lastIdx){
				return "not plus";
			}else if(nowCalPoint < 0){
				return "not down";
			}
			freqMap = new HashMap<>();
			if(wpp_code.equals("gr") && pump_grp == 1){
				freqMap.put("1", 60.0);
			}else{
				returnComb = (List<String>) collectList.get(nowCalPoint - 1).get("pumpComb");
				if((collectList.get(nowCalPoint - 1)).containsKey("freq")){
					freqMap = (HashMap<String, Double>) (collectList.get(nowCalPoint - 1)).get("freq");
				}

			}

		}
		//전력구하기
		HashMap<Integer, HashMap<String, Double>> grpFlowPressure = new HashMap<>();
		HashMap<String, Double> grpFlowPressureMap = new HashMap<>();
		HashMap<Integer, Double> grpPrdctPwr = new HashMap<>();
		if(wpp_code.equals("gs")){
			grpFlowPressureMap.put("flow", gosanFlowPressure.get("flow1"));
			grpFlowPressureMap.put("pressure", gosanFlowPressure.get("pressure1"));
			grpFlowPressure.put(1, grpFlowPressureMap);
			grpFlowPressureMap = new HashMap<>();
			grpFlowPressureMap.put("flow", gosanFlowPressure.get("flow2"));
			grpFlowPressureMap.put("pressure", gosanFlowPressure.get("pressure2"));
			grpFlowPressure.put(2, grpFlowPressureMap);
			grpPrdctPwr = drvnConfig.allPumpGrpPwrPrdct(returnComb, grpFlowPressure, freqMap);
		}else{
			grpFlowPressureMap.put("flow", flow);
			grpFlowPressureMap.put("pressure", pressure);
			grpFlowPressure.put(pump_grp, grpFlowPressureMap);
			grpPrdctPwr = drvnConfig.allPumpGrpPwrPrdct(returnComb, grpFlowPressure, freqMap);
		}

		for(HashMap<String, Object> map:grpList){
			int idx_integer = (int) map.get("PUMP_IDX");
			int idx_grp = (int) map.get("PUMP_GRP");
			double pwrPrdct = grpPrdctPwr.get(idx_grp);
			String pump_idx = String.valueOf(idx_integer);
			map.put("wpp_code", wpp_code);
			map.put("opt_idx", opt_idx);
			map.put("pwrPrdct", pwrPrdct);
			map.put("RATE_CTGRY", null);
			map.put("FLOW_CTR", null);
			map.put("ts", rgstr_time);
			int pump_typ = (int) map.get("PUMP_TYP");
			//인버터 타입일 경우
			map.put("freq", 0);
			if(pump_typ == 2){
				//조합식 결과의 주파수 map 검사
				if(freqMap != null){
					// 주파수 map에 포함되는 주파수 값이 있는지 검사
					if(freqMap.containsKey(pump_idx)){
						Double freq = freqMap.get(pump_idx);
						map.put("freq", freq);
					}else{
						map.put("freq", 0);
					}
				}
			}
			if(wpp_code.equals("gs")){
				List<String> grpReturnComb = gonsanAllReturnComb.get(idx_grp);
				if(grpReturnComb.contains(pump_idx)){
					map.put("pump_yn", 1);
				}else{
					map.put("pump_yn", 0);
				}
				map.put("flow", gosanFlowPressure.get("flow"+idx_grp));
				map.put("pressure",  gosanFlowPressure.get("pressure"+idx_grp));

			}else{
				if(returnComb.contains(pump_idx)){
					map.put("pump_yn", 1);
				}else{
					map.put("pump_yn", 0);
				}
				map.put("flow", flow);
				map.put("pressure", pressure);
			}

			drvnMapper.insertInQuiryPumpYnData(map);
		}
		HashMap<String, Object> logInsParma = new HashMap<>();
		logInsParma.put("nowDate", rgstr_time);
		logInsParma.put("pump_grp", pump_grp);
		logInsParma.put("oper", oper);
		String newPumpComb = returnComb.isEmpty() ? "" : String.join(",", returnComb);
		String newPumpFreq = freqMap.isEmpty() ? "" : String.join(",", freqMap.values().stream()
				.map(d -> String.valueOf(d.intValue()))
				.toArray(String[]::new));
		logInsParma.put("newPumpComb", newPumpComb);
		logInsParma.put("newPumpFreq", newPumpFreq);
		logInsParma.put("agoPumpComb", agoPumpComb);
		logInsParma.put("agoPumpFreq", agoPumpFreq);
		drvnMapper.insertManualOperLogNew(logInsParma);
//		if(wpp_code.equals("ba")){
//		}else{
//			drvnMapper.insertManualOperLog(logInsParma);
//		}
		return "success";
	}

	public int checkManualOperLog(HashMap<String, Object> checkLogParam) {
		return drvnMapper.checkManualOperLog(checkLogParam);
	}

	public String getPumpCombLogTime() {
		return drvnMapper.getPumpCombLogTime();
	}

	public String pumpManualOperFreq(String serverTime, int pump_grp, double setFreq) {
		List<String> returnComb = new ArrayList<>();
		HashMap<String, Double> freqMap = new HashMap<>();
		List<HashMap<String, Object>> grpList;
		List<HashMap<String, Object>> pumpList = setPumpList;
		int finalPump_grp = pump_grp;
		if(!wpp_code.equals("gs")){
			grpList = pumpList.stream()
					.filter(map -> map.containsKey("PUMP_GRP") && map.get("PUMP_GRP").equals(finalPump_grp))
					.collect(Collectors.toList());
		}else{
			grpList = pumpList;
		}

		List<HashMap<String, Object>> calList = drvnMapper.selectPumpCombCal();
		List<HashMap<String, Object>> grpFilteredList = calList.stream()
				.filter(map -> map.get("PUMP_GRP").equals(finalPump_grp))
				.collect(Collectors.toList());

		LinkedHashMap<String, Integer> typeMap = new LinkedHashMap<>();
		for(HashMap<String, Object> map:grpList){
			int pump_idx = (int) map.get("PUMP_IDX");
			String pump_idx_str = String.valueOf(pump_idx);
			int pump_typ = (int) map.get("PUMP_TYP");

			typeMap.put(pump_idx_str, pump_typ);
		}
		HashMap<String, Object> pumpUseParam = new HashMap<>();
		pumpUseParam.put("targetDate", serverTime);

		pumpUseParam.put("pump_grp", pump_grp);

		String beforePumpUse = null;
		String beforeFreqUse = null;
		String opt_idx = null;
		String rgstr_time = null;
		Double flow = null;
		Double pressure = null;
		HashMap<String, Double> gosanFlowPressure = new HashMap<>();
		HashMap<String, String> beforePumpUseMap = drvnMapper.getPreUsePumpStatus(pumpUseParam);


		if(beforePumpUseMap != null){
			if(beforePumpUseMap.containsKey("PUMP_USE_RST")){
				String value = beforePumpUseMap.get("PUMP_USE_RST");
				if (value != null && !value.trim().isEmpty()) {
					beforePumpUse = value;
				}
			}

			if(beforePumpUseMap.containsKey("SPI_USE_RST")){
				String value = beforePumpUseMap.get("SPI_USE_RST");
				if (value != null && !value.trim().isEmpty()) {
					beforeFreqUse = value;
				}
			}

			if(beforePumpUseMap.containsKey("OPT_IDX")){
				String value = beforePumpUseMap.get("OPT_IDX");
				if (value != null && !value.trim().isEmpty()) {
					opt_idx = value;
				}
			}
			if(beforePumpUseMap.containsKey("RGSTR_TIME")){
				String value = beforePumpUseMap.get("RGSTR_TIME");
				if (value != null && !value.trim().isEmpty()) {
					rgstr_time = value;
				}
			}
			if(beforePumpUseMap.containsKey("PRDCT_MEAN")){
				Object prdctMeanValue = beforePumpUseMap.get("PRDCT_MEAN");

				if (prdctMeanValue instanceof Double) {
					// 이미 Double 타입인 경우
					flow = (Double) prdctMeanValue;
				} else if (prdctMeanValue instanceof String) {
					// String으로 저장되어 있을 경우 Double로 변환
					flow = Double.valueOf((String) prdctMeanValue);
				} else {
					// 다른 타입일 경우 처리
					throw new IllegalArgumentException("PRDCT_MEAN의 값이 처리할 수 없는 타입입니다.");
				}
			}
			if(beforePumpUseMap.containsKey("TUBE_PRSR_PRDCT")){
				Object tubePrsrPrdctValue = beforePumpUseMap.get("TUBE_PRSR_PRDCT");

				if (tubePrsrPrdctValue instanceof Double) {
					// 이미 Double 타입인 경우
					pressure = (Double) tubePrsrPrdctValue;
				} else if (tubePrsrPrdctValue instanceof String) {
					// String으로 저장되어 있을 경우 Double로 변환
					pressure = Double.valueOf((String) tubePrsrPrdctValue);
				} else {
					// 다른 타입일 경우 처리
					throw new IllegalArgumentException("TUBE_PRSR_PRDCT의 값이 처리할 수 없는 타입입니다.");
				}

			}
		}
		String agoPumpComb = beforePumpUse;
		String agoPumpFreq = beforeFreqUse;

		if(beforePumpUse != null && !beforePumpUse.isEmpty()) {
			String[] strArray = beforePumpUse.split(",");
			List<String> strList = Arrays.stream(strArray)
					.map(String::trim)
					.collect(Collectors.toList());
			List<String> combIvtPump = new ArrayList<>();
			returnComb = strList;
			for (String pump : strList) {
				if (typeMap.containsKey(pump)) {
					if (typeMap.get(pump) == 2) {
						combIvtPump.add(pump);
					}
				}
			}
			HashMap<String, Double> beforeFreqMap = new HashMap<>();
			if (beforeFreqUse != null && !beforeFreqUse.trim().isEmpty() && !combIvtPump.isEmpty()) {

				String[] freqArr = beforeFreqUse.split(",");
				List<String> freqList = Arrays.stream(freqArr)
						.map(String::trim)
						.collect(Collectors.toList());
				for (int i = 0; i < combIvtPump.size(); i++) {
					String idx = combIvtPump.get(i);
					Double freqDb = 0.0;

					String freqStr = freqList.get(i);
					freqDb = Double.valueOf(freqStr);
					beforeFreqMap.put(idx, freqDb);

				}


				freqMap = beforeFreqMap;
			}
		}else{
			returnComb = new ArrayList<>();
		}
		if(wpp_code.equals("ba")){
			freqMap = new HashMap<>();
			if(pump_grp == 1){
					freqMap.put("4", setFreq);
			}else if(pump_grp == 2){
				freqMap.put("7", setFreq);
			}
		}

		//전력구하기
		HashMap<Integer, HashMap<String, Double>> grpFlowPressure = new HashMap<>();
		HashMap<String, Double> grpFlowPressureMap = new HashMap<>();
		grpFlowPressureMap.put("flow", flow);
		grpFlowPressureMap.put("pressure", pressure);
		grpFlowPressure.put(pump_grp, grpFlowPressureMap);
		HashMap<Integer, Double> grpPrdctPwr = drvnConfig.allPumpGrpPwrPrdct(returnComb, grpFlowPressure, freqMap);

		for(HashMap<String, Object> map:grpList){
			int idx_integer = (int) map.get("PUMP_IDX");
			int idx_grp = (int) map.get("PUMP_GRP");
			double pwrPrdct = grpPrdctPwr.get(idx_grp);
			String pump_idx = String.valueOf(idx_integer);
			map.put("wpp_code", wpp_code);
			map.put("opt_idx", opt_idx);
			map.put("pwrPrdct", pwrPrdct);
			map.put("RATE_CTGRY", null);
			map.put("FLOW_CTR", null);
			map.put("ts", rgstr_time);
			int pump_typ = (int) map.get("PUMP_TYP");
			//인버터 타입일 경우
			map.put("freq", 0);
			if(pump_typ == 2){
				//조합식 결과의 주파수 map 검사
				if(freqMap != null){
					// 주파수 map에 포함되는 주파수 값이 있는지 검사
					if(freqMap.containsKey(pump_idx)){
						Double freq = freqMap.get(pump_idx);
						map.put("freq", freq);
					}else{
						map.put("freq", 0);
					}
				}
			}

			if(returnComb.contains(pump_idx)){
				map.put("pump_yn", 1);
			}else{
				map.put("pump_yn", 0);
			}
			map.put("flow", flow);
			map.put("pressure", pressure);

			drvnMapper.insertInQuiryPumpYnData(map);
		}
		HashMap<String, Object> logInsParma = new HashMap<>();
		logInsParma.put("nowDate", rgstr_time);
		logInsParma.put("pump_grp", pump_grp);
		logInsParma.put("oper", "freq");
		String newPumpComb = returnComb.isEmpty() ? "" : String.join(",", returnComb);
		String newPumpFreq = freqMap.isEmpty() ? "" : String.join(",", freqMap.values().stream()
				.map(d -> String.valueOf(d.intValue()))
				.toArray(String[]::new));
		logInsParma.put("newPumpComb", newPumpComb);
		logInsParma.put("newPumpFreq", newPumpFreq);
		logInsParma.put("agoPumpComb", agoPumpComb);
		logInsParma.put("agoPumpFreq", agoPumpFreq);
		drvnMapper.insertManualOperLogNew(logInsParma);


		return "success";
	}

	public List<HashMap<String, Object>> getGroupPumpCal(HashMap<String, Object> pumpGrp) {


		//운문

		LocalDateTime dateTime = LocalDateTime.now();
		List<HashMap<String, Object>> pumpList = aiMapper.selectPumpList();;
		if(wpp_code.equals("wm")){


			pumpList.forEach(map -> {

				map.put("PUMP_TYP", 1);

			});
		}

		List<HashMap<String, Object>> getPumpCal = drvnMapper.getGroupPumpCal(pumpGrp);

		List<HashMap<String, Object>> filteredList;

//		if (wpp_code.equals("gs")) {
//			filteredList = getPumpCal.stream()
//					.filter(map -> {
//						if ((int) map.get("PUMP_GRP") == 0) {
////							return (int) map.get("USE_YN") == 1;
//						}
//						return true; // PUMP_GRP가 0이 아닌 데이터는 필터링 없이 포함
//					})
//					.collect(Collectors.toList());
//		} else {
//		}
		filteredList = getPumpCal; // 다른 경우 필터링 없이 원본 리스트 사용
		List<Integer> pumpCombTypeList = new ArrayList<>();
		int count = 0;
		int size = getPumpCal.size() - 1;

		for(HashMap<String, Object> cal:filteredList){
			int c_ord = (int) cal.get("C_ORD");
			count++;
			if(c_ord == 1){
				pumpCombTypeList = new ArrayList<>();
				String pump_comb = (String) cal.get("PUMP_COMB");
				Integer pump_grp = (Integer) cal.get("PUMP_GRP");
				String[] strArray = pump_comb.split(",");
				List<String> strList =Arrays.stream(strArray)
						.map(String::trim)
						.collect(Collectors.toList());

				if(wpp_code.equals("gr") && pump_grp == 3){
					//고령 선남가압장 짝수일 2번, 홀수일 3번 조합 생성
					int wm_day = dateTime.getDayOfMonth();
					strList = strList.stream()
							.map(str -> {
								if (wm_day % 2 == 0) {
									// wm_day가 짝수일 경우
									if (str.equals("11")) {
										return "10";
									}
								} else {
									// wm_day가 홀수일 경우
									if (str.equals("11")) {
										return "11";
									}
								}
								return str;
							})
							.collect(Collectors.toList());
				}
				List<Integer> grpIdxList = new ArrayList<>();
				for(String pump_idx_str:strList){
					if(!pump_idx_str.isEmpty()){
						int pump_idx = Integer.parseInt(pump_idx_str);
						List<HashMap<String, Object>> idxList = pumpList.stream()
								.filter(map -> map.containsKey("PUMP_IDX") && map.get("PUMP_IDX").equals(pump_idx))
								.collect(Collectors.toList());

						int pump_grp_idx = (int) idxList.get(0).get("PUMP_GRP_IDX");
						int pump_typ = (int) idxList.get(0).get("PUMP_TYP");
						grpIdxList.add(pump_grp_idx);
						pumpCombTypeList.add(pump_typ);

					}
				}
				String result;
				if(!grpIdxList.isEmpty()){
					result = joinWithComma(grpIdxList);
				}else{
					result = "";
				}

				cal.put("PUMP_COMB", result);
			}else {
				String freq_comb = (String) cal.get("PUMP_COMB");
				// C_ORD=2 행의 주파수 조합이 비어 있어도 터지지 않게 한다 (selectPumpCombCal 과 동일)
				String[] strArray = freq_comb == null ? new String[0] : freq_comb.split(",");
				List<String> strList = Arrays.stream(strArray)
						.map(String::trim)
						.collect(Collectors.toList());
				List<Integer> freqList = new ArrayList<>();
				int stack = 0;
				if(!pumpCombTypeList.isEmpty()){
					for(Integer type:pumpCombTypeList){
						if(type == 1){
							freqList.add(0);
						}else if(type == 2) {
							freqList.add(parseFreqOrZero(stack < strList.size() ? strList.get(stack) : null));
							stack++;
						}
					}
				}
				String result;
				if(!freqList.isEmpty()){
					result = joinWithComma(freqList);
				}else{
					result = "";
				}
				cal.put("PUMP_COMB", result);
			}
		}
		return filteredList;
	}

	public List<HashMap<String, Object>> getPumpCombinationItem(HashMap<String, Object> map) {
		return drvnMapper.getPumpCombinationItem(map);
	}

	public void setPumpListYn(List<HashMap<String, Object>> updateList) {
		for(HashMap<String, Object> map:updateList){
			drvnMapper.setPumpListYn(map);

		}
	}

	public void changePumpCal(List<HashMap<String, Object>> pumpList) {
		int pump_grp = -1;
		double pump_count = -1;
		int pump_priority = -1;
		List<Integer> changeComb = new ArrayList<>();
		for(HashMap<String, Object> map:pumpList){
			if(pump_grp == -1){
				pump_grp = (int) map.get("PUMP_GRP");
			}
			if(pump_count == -1){
				Object pumpCountValue = map.get("PUMP_COUNT");
				if (pumpCountValue instanceof Integer) {
					pump_count = ((Integer) pumpCountValue).doubleValue(); // int를 double로 변환
				} else if (pumpCountValue instanceof Double) {
					pump_count = (Double) pumpCountValue; // double 그대로 사용
				} else {
					throw new IllegalArgumentException("PUMP_COUNT is not of type int or double");
				}
			}
			if(pump_priority == -1){
				pump_priority = (int) map.get("PUMP_PRIORITY");
			}

			int pump_yn = (int) map.get("PUMP_YN");
			int pump_idx = (int) map.get("PUMP_IDX");
			if(pump_yn == 1){
				changeComb.add(pump_idx);
			}
		}
		HashMap<String, Object> calParam = new HashMap<>();
		calParam.put("pump_grp", pump_grp);
		calParam.put("pump_count", pump_count);
		calParam.put("pump_priority", pump_priority);
		List<HashMap<String, Object>> getGrpCombCal = drvnMapper.getGroupPumpCal(calParam);
		boolean isMatchFound = false;

		// changeComb를 Set으로 변환 (순서 무시 및 빠른 비교를 위해)
		Set<Integer> changeCombSet = new HashSet<>(changeComb);
		HashMap<String, Object> changeCal = new HashMap<>();
		for (HashMap<String, Object> data : getGrpCombCal) {
			int cOrd = (int) data.get("C_ORD");

			// C_ORD 값이 1인 데이터만 처리
			if (cOrd == 1) {
				String pumpCombStr = (String) data.get("PUMP_COMB");

				// PUMP_COMB 문자열을 ','로 분리하여 Integer Set으로 변환
				Set<Integer> pumpCombSet = Arrays.stream(pumpCombStr.split(","))
						.map(Integer::parseInt)
						.collect(Collectors.toSet());

				// Set 비교 (동일한 값이 모두 있는지 확인)
				if (changeCombSet.equals(pumpCombSet)) {

					changeCal = data;
					isMatchFound = true;
					break; // 일치하는 데이터가 있으면 루프 중단
				}
			}
		}

		if (!isMatchFound) {

			return;
		}

		drvnMapper.disableGroupPumpCal(changeCal);
		drvnMapper.enableGroupPumpCal(changeCal);

	}


	public HashMap<Integer, HashMap<String, Double>> getGrpFlowPressure(int pumpGrp) {

		List<HashMap<String, Object>> grpFlowPressureTag = drvnMapper.getGrpFlPreTag(pumpGrp);

		HashMap<Integer, HashMap<String, Double>> returnMap = new HashMap<>();
		HashMap<String, String> rawParam = new HashMap<>();
		String maxTs = drvnMapper.getPumpCombTime();
		rawParam.put("ts", maxTs);

		for(HashMap<String, Object> map:grpFlowPressureTag){
			HashMap<String, Double> grpMap = new HashMap<>();
			int pump_grp = (int) map.get("PUMP_GRP");
			String fri_tag = (String) map.get("FRI_TAG");
			rawParam.put("tag", fri_tag);
			grpMap.put("flow", settingMapper.getAvgOneHourRaw(rawParam));
			String pri_tag = (String) map.get("PRI_T_TAG");
			rawParam.put("tag", pri_tag);
			grpMap.put("pressure", settingMapper.getAvgOneHourRaw(rawParam));

			returnMap.put(pump_grp, grpMap);
		}

		return returnMap;

	}

	List<HashMap<String, Object>> selectPumpCombList(HashMap<String, Object> map) { return drvnMapper.selectPumpCombList(map); }

	public void savePumpComb(List<HashMap<String, Object>> listMap) {
		for(HashMap<String, Object> map:listMap){
			drvnMapper.savePumpComb(map);
		}
	}

	public void updatePumpCombItem(HashMap<String, Object> map) {
		drvnMapper.updatePumpCombItem(map);
	}
	public void setInsertPumpComn() {
		drvnConfig.setInsertPumpComn();
	}

	public HashMap<Integer, HashMap<String, Double>> getPrdctPwrCalValMap() {
		return prdctPwrCalValMap;
	}

	public HashMap<Integer, HashMap<Integer, Double>> getPrdctPwrIdxValMap() {
		return prdctPwrIdxValMap;
	}
	public List<HashMap<String, Object>> getGrpPumpComb(int grp) {
		return drvnMapper.getGrpPumpComb(grp);
	}

	public void insertCombPwrUnit(List<HashMap<String, Object>> insertArr) {
		drvnMapper.insertCombPwrUnit(insertArr);
	}
}
