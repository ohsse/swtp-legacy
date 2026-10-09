package kr.co.mindone.ems.drvn;
/**
 * packageName    : kr.co.mindone.ems.drvn
 * fileName       : DrvnConfig
 * author         : geunwon
 * date           : 24. 9. 9.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 9.        geunwon       최초 생성
 */

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import kr.co.mindone.ems.ai.AiMapper;
import kr.co.mindone.ems.common.holiday.HolidayChecker;
import kr.co.mindone.ems.epa.EpaService;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Lazy;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.lang.reflect.Type;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

@Slf4j
@Component
@PropertySource("classpath:application-${spring.profiles.active}.properties")
@Profile("!gm & !hp & !ji & !hy & !ss & !gm2 & !hp2 & !hy2 & !ji2")
public class DrvnConfig {
	private static final Logger logger = LoggerFactory.getLogger(DrvnConfig.class);
	public static HashMap<Integer, HashMap<Integer, String>> reduceMap;
	static String opt_idx;
	@Autowired
	DrvnMapper drvnMapper;
	@Autowired
	AiMapper aiMapper;
	@Autowired
	@Lazy
	EpaService epaService;
	@Value("${dstrb.optidx}")
	String optIdxTag;
	@Value("${dstrb.prdct.pwrCal.idx}")
	private String prdctPwrIdxVal;
	@Value("${dstrb.pump.level}")
	private String pumpLevel;
	@Value("${dstrb.prdct.pumpDstrbId}")
	private String pumpDstrbId;
	@Value("${dstrb.prdct.pwrCal.calVal}")
	private String prdctPwrCalVal;
	@Value("${dstrb.prdct.pumpComb.target.max.down}")
	private String pumpCombTargetMax;
	@Value("${dstrb.prdct.pumpComb.target.max.up}")
	private String pumpCombTargetMaxUp;
	@Value("${dstrb.prdct.pumpComb.target.min}")
	private String pumpCombTargetMin;
	@Value("${dstrb.prdct.pumpComb.target.level}")
	private String pumpCombTargetLevel;
	private HashMap<Integer, HashMap<String, Double>> prdctPwrCalValMap;
	private HashMap<Integer, HashMap<Integer, Double>> prdctPwrIdxValMap;
	private HashMap<Integer, HashMap<Integer, Double>> pumpLevelInfoGrpMap;
	private LinkedHashMap<Integer, HashMap<String, String>> pumpDstrbIdMap;
	private List<HashMap<String, Object>> calList;
	private List<HashMap<String, Object>> setPumpList;
	private HashMap<Integer, HashMap<String, Double>> pumpCombTargetMap;
	private HashMap<Integer, HashMap<String, Double>> pumpCombTargetMapUp;
	private HashMap<Integer, HashMap<String, Double>> pumpCombTargetMapMin;
	private HashMap<Integer, HashMap<String, Double>> pumpCombTargetLevelMap;
	@Value("${spring.profiles.active}")
	private String wpp_code;
	private int setMonth;
	private StringBuffer loadCheckLog = new StringBuffer();

	/**
	 * 거리계산시 압력 및 유량의 평균화를 위한 표준편차를 구하는 메서드
	 *
	 * @param values value값
	 * @param mean   평균값
	 * @return 표준편차 반환
	 */
	public static double calculateStdDev(List<Double> values, double mean) {
		double sum = 0.0;
		for (double value : values) {
			sum += Math.pow(value - mean, 2);
		}
		return Math.sqrt(sum / values.size());
	}

	/**
	 * 운전현황 properties 값
	 * Json -> HashMap 파싱 메서드
	 */
	@PostConstruct
	public void setIntegerDobleMap() {
		LocalDateTime currentTimeSetMonth = LocalDateTime.now();
		setMonth = currentTimeSetMonth.getMonthValue();
		reduceMap = getMonthPwrReduc();
		Gson gson = new Gson();
		Type doubleType = new TypeToken<HashMap<Integer, HashMap<String, Double>>>() {
		}.getType();
		Type intStrDoubleType = new TypeToken<HashMap<Integer, HashMap<Integer, Double>>>() {
		}.getType();

		Type linkedStrType = new TypeToken<LinkedHashMap<Integer, HashMap<String, String>>>() {
		}.getType();
		Type arrType = new TypeToken<HashMap<Integer, HashMap<String, List<String>>>>() {
		}.getType();
		Type strArrType = new TypeToken<HashMap<String, List<String>>>() {
		}.getType();


		prdctPwrCalValMap = gson.fromJson(prdctPwrCalVal, doubleType);
		pumpLevelInfoGrpMap = gson.fromJson(pumpLevel, intStrDoubleType);
		pumpDstrbIdMap = gson.fromJson(pumpDstrbId, linkedStrType);

		prdctPwrIdxValMap = gson.fromJson(prdctPwrIdxVal, intStrDoubleType);
		calList = drvnMapper.selectPumpCombCal();
		setPumpList = aiMapper.selectPumpList();
		pumpCombTargetMap = gson.fromJson(pumpCombTargetMax, doubleType);
		pumpCombTargetMapUp = gson.fromJson(pumpCombTargetMaxUp, doubleType);
		pumpCombTargetMapMin = gson.fromJson(pumpCombTargetMin, doubleType);
		pumpCombTargetLevelMap = gson.fromJson(pumpCombTargetLevel, doubleType);
		opt_idx = optIdxTag;

	}

	@Scheduled(cron = "0,30 * * * * *")
	public void schedulePumpTask() {
		setInsertPumpComn(); // 비동기 실행
	}

	/**
	 * 펌프 조합 스케쥴링
	 * <p>
	 * 30초마다 properties에 정의된 펌프 그룹마다의 예측 압력과 유량값을 가져와 펌프조합 메서드에 입력
	 */
	@Async("taskExecutor") // 명시적으로 executor 이름 지정 (선택)
	public void setInsertPumpComn() {
		try {
			log.info("=== [펌프 조합 생성 스케줄러 실행됨] ===");

			LocalDateTime currentTimeSetMonth = LocalDateTime.now();
			setMonth = currentTimeSetMonth.getMonthValue();
			reduceMap = getMonthPwrReduc();

			DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
			DateTimeFormatter idxFormatter = DateTimeFormatter.ofPattern("yyMMddHHmm");
			LocalDateTime now = LocalDateTime.now();
			String nowDateScd = now.format(formatter);

			// setPumpList가 null이면 빈 리스트로 초기화
			if (setPumpList == null) {
				log.warn("setPumpList가 null입니다. 빈 리스트로 초기화합니다.");
				setPumpList = new ArrayList<>();
			}

			// DB 조회로 덮어쓰기 (이전 pumpList 변수 불필요)
			setPumpList = aiMapper.selectPumpList();
			calList = drvnMapper.selectPumpCombCal();
			//날짜 조회를 위한 date 포맷 및 예측 데이터의 key값 생성을 위한 날짜 포맷 생성

			int epaMode;
			try {
				epaMode = epaService.getEpaModeInfo();

			} catch (Exception e) {
				logger.error("epaMode 정보를 가져오는 중 에러가 발생했습니다.", e);
				epaMode = 0; // 에러가 발생했으므로 기본값 0을 대입
			}

			logger.info("최종적으로 결정된 epaMode: {}", epaMode);
			HashMap<String, Object> param = new HashMap<>();
			for (int i = -4; i <= 0; i++) {
				try {
					LocalDateTime currentTime = LocalDateTime.now().plusMinutes(i);
					String nowDateTime = currentTime.format(formatter);
					param.put("nowDateTime", nowDateTime);

					Set<Integer> pumpGrpSet = new LinkedHashSet<>(pumpDstrbIdMap.keySet());

					LinkedHashMap<String, List<HashMap<String, Object>>> dataCtrMap = new LinkedHashMap<>();
					String ts = null;
					HashMap<String, Double> gosanDataMap = new HashMap<>();
					for (Integer id : pumpGrpSet) {
						try {
							HashMap<String, String> ditrbMap = pumpDstrbIdMap.get(id);

							String flowId = ditrbMap.get("flow");
							String pressureId = ditrbMap.get("pressure");

							// 현재 데이터 조회
							param.put("DSTRB_ID", flowId);
							List<HashMap<String, Object>> flowDataList = drvnMapper.prdctFlowPressure(param);
							param.put("DSTRB_ID", pressureId);
							List<HashMap<String, Object>> pressureDataList = drvnMapper.prdctFlowPressure(param);

							// 데이터가 없거나 0.0인 경우 보정
							double flowDb = getCorrectedValue(flowDataList, flowId, nowDateTime);
							double pressureDb = getCorrectedValue(pressureDataList, pressureId, nowDateTime);

							dataCtrMap.put("flow" + id, flowDataList);
							dataCtrMap.put("pressure" + id, pressureDataList);
							if (ts == null || ts.isEmpty()) {
								if (!flowDataList.isEmpty()) {
									ts = (String) flowDataList.get(0).get("ts");
								}
							}
							if (ts == null || ts.isEmpty()) {
								ts = nowDateTime;
							}

							if (wpp_code.equals("gs")) {
								gosanDataMap.put("flow" + id, flowDb);
								gosanDataMap.put("pressure" + id, pressureDb);
							} else {
								if (ts != null) {
									insertPumpComb(flowDb, pressureDb, id, ts);
								}
							}

						} catch (Exception e) {
							log.error("펌프 그룹 {} 데이터 처리 중 오류 발생: {}", id, e.getMessage(), e);
						}
					}
					if (wpp_code.equals("gs")) {
						// 1. Key 개수 확인
						if (gosanDataMap.size() != 4) {
							return; // key 개수가 4가 아니면 return
						}

						// 2. Value 중 0.0 확인
						for (Double value : gosanDataMap.values()) {
							if (value == null || value.equals(0.0)) {
								return; // value가 null이거나 0.0이면 return
							}
						}

						double gosanFlow = gosanDataMap.get("flow1") + gosanDataMap.get("flow2");
						double gosanPressure = (0.025268 * gosanDataMap.get("pressure1")) + (0.968549 * gosanDataMap.get("pressure2")) + 0.064324;

						if(epaMode == 1){
							double epaFlow = epaService.getEpaFlow(gosanFlow, ts, 0);
							double epaPressure = epaService.getEpaPressure(gosanPressure, ts, 0);

							// ✨ 로깅: EPA 모드 (epaMode == 1)
							System.out.println("--- [DEBUG] EPA Mode (epaMode=1) ---");
							System.out.println("[DEBUG] Original gosanFlow: " + gosanFlow);
							System.out.println("[DEBUG] Original gosanPressure: " + gosanPressure);
							System.out.println("[DEBUG] Final Flow (epaFlow): " + epaFlow);
							System.out.println("[DEBUG] Final Pressure (epaPressure): " + epaPressure);

							insertPumpComb(epaFlow, epaPressure, 0, ts);
						}else{
							// ✨ 로깅: 일반 모드 (epaMode != 1)
							System.out.println("--- [DEBUG] Normal Mode (epaMode!=" + epaMode + ") ---");
							System.out.println("[DEBUG] Final Flow (gosanFlow): " + gosanFlow);
							System.out.println("[DEBUG] Final Pressure (gosanPressure): " + gosanPressure);

							insertPumpComb(gosanFlow, gosanPressure, 0, ts);
						}
					}
				} catch (Exception e) {
					log.error("시간 오프셋 {}분 처리 중 오류 발생: {}", i, e.getMessage(), e);
				}
			}
		} catch (Exception e) {
			log.error("펌프 조합 스케줄러 전체 실패: {}", e.getMessage(), e);
		}
	}

	/**
	 * 펌프 데이터를 보정하는 헬퍼 메서드.
	 * 데이터가 없거나 0일 경우 최근 10분간의 평균값을 사용합니다.
	 */
	/**
	 * 펌프 데이터를 보정하는 헬퍼 메서드.
	 * 데이터가 없거나 0일 경우 지정된 시간(nowDateTime) 기준 최근 10분간의 평균값을 사용합니다.
	 */
	private double getCorrectedValue(List<HashMap<String, Object>> dataList, String dstrbId, String nowDateTime) {
		Double originalValue = extractNumericValue(dataList);
		if (originalValue == null || originalValue == 0.0) {
			log.warn("데이터가 없거나 0입니다. dstrbId: {}. 최근 10분간의 평균값으로 보정합니다.", dstrbId);

			// nowDateTime을 추가 파라미터로 전달
			Double recentAvg = drvnMapper.selectAverageValueLast10Minutes(dstrbId, nowDateTime);
			if (recentAvg != null) {
				log.info("보정된 값: {} -> {}", originalValue, recentAvg);
				return recentAvg;
			} else {
				log.warn("최근 10분간 유효한 데이터가 없어 보정에 실패했습니다. dstrbId: {}", dstrbId);
				return 0.0; // 보정 실패 시 0 반환
			}
		}
		return originalValue;
	}

	private Double extractNumericValue(List<HashMap<String, Object>> dataList) {
		if (dataList == null || dataList.isEmpty()) {
			return null;
		}
		Object value = dataList.get(0).get("value");
		if (value instanceof Number) {
			return ((Number) value).doubleValue();
		}
		if (value instanceof String) {
			try {
				return Double.parseDouble((String) value);
			} catch (NumberFormatException e) {
				log.warn("펌프 예측값 숫자 변환 실패: {}", value);
			}
		}
		return null;
	}

	/**
	 * 펌프 조합 생성 메서드(현재 정수장마다 커스텀이 많이 들어가 코드가 지저분한 상태)
	 *
	 * @param flow     예측 유량
	 * @param pressure 예측 압력
	 * @param pump_grp 계산할 펌프 그룹
	 * @param ts       계산할 시간
	 * @return 수동 생성시 확인을 위한 로그값 반환을 위한 objeect
	 */
	public Object insertPumpComb(double flow, double pressure, int pump_grp, String ts) {
		loadCheckLog.append("  - **데이터 확인!** flow: " + flow + ", pressure: " + pressure + ", pump_grp: " + pump_grp + ", ts: " + ts + "#");

		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
		//날짜 치환
		LocalDateTime dateTime = LocalDateTime.parse(ts, formatter);

		HashMap<Integer, Double> pumpLevelInfoMap = pumpLevelInfoGrpMap.get(pump_grp);


		List<String> returnComb = new ArrayList<>();
		loadCheckLog = new StringBuffer();
		List<HashMap<String, Object>> calList;
		if (wpp_code.equals("gs")) {
			calList = drvnMapper.selectPumpCombCal();
		} else {
			calList = drvnMapper.selectPumpCombCal();
		}

		List<HashMap<String, Object>> grpFilteredList;

		if (wpp_code.equals("gs")) {
			grpFilteredList = calList.stream()
					.filter(map -> String.valueOf(map.get("PUMP_GRP")).equals(String.valueOf(pump_grp)))
					.filter(map -> Integer.parseInt(String.valueOf(map.get("USE_YN"))) == 1)
					.collect(Collectors.toList());

		} else {
			grpFilteredList = calList.stream()
					.filter(map -> map.get("PUMP_GRP").equals(pump_grp))
					.collect(Collectors.toList());
		}


		// 새로운 C_IDX를 부여하기 위한 Map과 카운터
		Map<String, Integer> newCidxMap = new HashMap<>();
		AtomicInteger cidxCounter = new AtomicInteger(1);

		// 기존 grpFilteredList의 데이터를 순회하며 C_IDX를 재부여
		// 새로운 리스트를 만들고, 마지막에 grpFilteredList에 재할당
		List<HashMap<String, Object>> tempReindexedList = grpFilteredList.stream()
				.map(map -> {
					HashMap<String, Object> newMap = new HashMap<>(map);
					String key = String.valueOf(map.get("PUMP_COUNT")) + "_" + String.valueOf(map.get("PUMP_PRIORITY"));

					// Map에 키가 없으면 새로운 C_IDX를 부여
					if (!newCidxMap.containsKey(key)) {
						newCidxMap.put(key, cidxCounter.getAndIncrement());
					}

					newMap.put("C_IDX", newCidxMap.get(key));
					return newMap;
				})
				.collect(Collectors.toList());




		// 재부여된 C_IDX를 가진 리스트를 grpFilteredList에 다시 할당
		grpFilteredList = tempReindexedList;




		HashMap<Double, Integer> pumpLevelMap = new HashMap<>();

		LinkedHashSet<Integer> uniqueCIdx = new LinkedHashSet<>();
		//c_idx 전처리 조합식 순서대로 Set에 담기
		for (HashMap<String, Object> maps : grpFilteredList) {
			uniqueCIdx.add((Integer) maps.get("C_IDX"));
		}
		List<HashMap<String, Object>> collectData = new ArrayList<>();
		List<HashMap<String, Object>> pumpList = setPumpList;
		//운문 날짜 조건

		if (wpp_code.equals("wm")) {
			pumpList.forEach(map -> {

				map.put("PUMP_TYP", 1);

			});
		}
		int wm_day = 0;
		// 조합 구한 펌프 리스트만 필터링
		List<HashMap<String, Object>> grpList;
		if (wpp_code.equals("gs")) {
			grpList = pumpList;
		} else {
			grpList = pumpList.stream()
					.filter(map -> map.containsKey("PUMP_GRP") && map.get("PUMP_GRP").equals(pump_grp))
					.collect(Collectors.toList());
		}
		LinkedHashMap<String, Integer> typeMap = new LinkedHashMap<>();
		for (HashMap<String, Object> map : grpList) {
			int pump_idx = (int) map.get("PUMP_IDX");
			String pump_idx_str = String.valueOf(pump_idx);
			int pump_typ = (int) map.get("PUMP_TYP");

			typeMap.put(pump_idx_str, pump_typ);
		}
		boolean pumpTypeBool = typeMap.values().stream().anyMatch(value -> value >= 2);

		if (wpp_code.equals("ba")) {
			if (pump_grp == 5) {
				if (!uniqueCIdx.isEmpty()) {
					uniqueCIdx.remove(0);
				}
			}
		}
		//표준화를 위한 데이터 적재
		double flowSum = 0;
		double pressSum = 0;
		int cnt = 0;
		List<Double> targetflowList = new ArrayList<>();
		List<Double> targetpressList = new ArrayList<>();
		//회기식의 유량조건을 반목문 돌리면서 distance를 구해야함(min max값을 담기)
		for (int cidx : uniqueCIdx) {
			List<HashMap<String, Object>> cIdxFilteredList = grpFilteredList.stream()
					.filter(map -> map.get("C_IDX").equals(cidx))
					.collect(Collectors.toList());
			HashMap<String, Object> collectMap = new HashMap<>();
			String pump_comb = null;
			String freq = null;
			double min_flow = 0;
			double max_flow = 0;
			HashMap<String, Object> pressureCal = new HashMap<>();
			for (HashMap<String, Object> map : cIdxFilteredList) {
				int c_ord = (int) map.get("C_ORD");
				double fc_val = (double) map.get("FC_VAL");
				if (c_ord == 1) {
					pump_comb = (String) map.get("PUMP_COMB");
					//첫번 째 식만 가져옴
					pressureCal = map;
					min_flow = fc_val;
				} else {
					if (map.get("PUMP_COMB") != null) {
						freq = (String) map.get("PUMP_COMB");
					}
					max_flow = fc_val;
				}
			}
			String[] strArray = pump_comb.split(",");
			List<String> strList = Arrays.stream(strArray)
					.map(String::trim)
					.collect(Collectors.toList());
			if (wpp_code.equals("wm")) {
				wm_day = dateTime.getDayOfMonth();
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
			if (wpp_code.equals("gr") && pump_grp == 3) {
				//고령 선남가압장 짝수일 2번, 홀수일 3번 조합 생성
				DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
				int week = dayOfWeek.getValue();
				HolidayChecker holidayChecker = new HolidayChecker();
				Boolean passDayBool = holidayChecker.isPassDay(ts);
				wm_day = dateTime.getDayOfMonth();
				if (passDayBool || week >= 6) {
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
			HashMap<String, Double> freqMap = new HashMap<>();
			if (freq != null && !freq.trim().isEmpty()) {

				String[] freqArr = freq.split(",");
				List<String> freqList = Arrays.stream(freqArr)
						.map(String::trim)
						.collect(Collectors.toList());
				List<String> combIvtPump = new ArrayList<>();
				for (String pump : strList) {
					if (pump == null) {
						break;
					} else {
						if (typeMap.get(pump) == 2) {
							combIvtPump.add(pump);
						}
					}
				}
				if (!combIvtPump.isEmpty()) {
					for (int i = 0; i < combIvtPump.size(); i++) {
						String idx = combIvtPump.get(i);
						String freqStr = freqList.get(i);
						Double freqDb = Double.valueOf(freqStr);
						freqMap.put(idx, freqDb);
					}

					collectMap.put("freq", freqMap);
				}
			}
			double pumpLevel = 0.0;
			if (!strList.isEmpty()) {
				for (String pump_idx : strList) {
					if (!pump_idx.isEmpty()) {
						int idx = Integer.parseInt(pump_idx);
						double pumpVal = pumpLevelInfoMap.get(idx);
						if (typeMap.get(pump_idx) == 1) {
							pumpLevel += pumpVal;
						} else {
							if (freqMap.containsKey(pump_idx)) {
								double freqVal = (freqMap.get(pump_idx) / 60) * 1;
								pumpLevel += freqVal;
							}
						}

					}
				}
			}

			if (pumpTypeBool) {
				int nowListSize = collectData.size() - 1;
				if (nowListSize >= 0) {
					double agoLevel = (double) collectData.get(nowListSize).get("pumpLevel");
					double middleLevel = (((pumpLevel - agoLevel) / 10) * 5) + agoLevel;
					collectMap.put("uppLev", middleLevel);
					collectData.get(nowListSize).put("lowLev", middleLevel);
				}
			}

			pumpLevelMap.put(pumpLevel, cidx);
			collectMap.put("pumpLevel", pumpLevel);
			collectMap.put("combIdx", cidx);

			List<HashMap<String, Double>> flowPriList = new ArrayList<>();
			double flusFlow = 1;
			if (max_flow - min_flow > 1000) {
				flusFlow = 10;
			}

			for (double i = min_flow; i <= max_flow; i += flusFlow) {
				HashMap<String, Double> calMap = new HashMap<>();
				double calPressure = pressureCalValue(i, pressureCal, pump_grp);
				calMap.put("calPressure", calPressure);
				calMap.put("calFlow", i);
				flowPriList.add(calMap);

				//표준화를 위한 데이터 적재
				cnt++;
				flowSum += i;
				pressSum += calPressure;
				targetflowList.add(i);
				targetpressList.add(calPressure);
			}
			collectMap.put("calList", flowPriList);
			collectData.add(collectMap);
		}

		//mean값
		double flowAvg = flowSum / cnt;
		double pressAvg = pressSum / cnt;
		//표준편차
		double pressStd = calculateStdDev(targetpressList, pressAvg);
		double flowStd = calculateStdDev(targetflowList, flowAvg);

		int closestPointIndex = -1;
		double minDistance = Double.MAX_VALUE;
		if (!collectData.isEmpty()) {
			double distance;
			for (int i = 0; i < collectData.size(); i++) {
				HashMap<String, Object> targetMap = collectData.get(i);
				List<HashMap<String, Double>> flowPriList = (List<HashMap<String, Double>>) targetMap.get("calList");
				for (HashMap<String, Double> calMap : flowPriList) {
					double targetPre = calMap.get("calPressure");
					double targetFlow = calMap.get("calFlow");


					// curP, curQ 표준화
					double standardizedCurP = (pressure - pressAvg) / pressStd;
					double standardizedCurQ = (flow - flowAvg) / flowStd;
					// preP, preQ 표준화
					double standardizedPreP = (targetPre - pressAvg) / pressStd;
					double standardizedPreQ = (targetFlow - flowAvg) / flowStd;
					// 거리 계산
					double deltaX = Math.abs(standardizedCurP - standardizedPreP);
					double deltaY = Math.abs(standardizedCurQ - standardizedPreQ);
					// 계산된 좌표의 값에 유클리드 거리방정식을 적용해 거리 계산
					distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
					// 각 데이터 포인트별 거리 로그
//					loadCheckLog.append("  - Data Point (Pre, Flow): (" + targetPre + ", " + targetFlow + ") -> Distance: " + distance + "#");

					// 거리 값이 기존 거리값보다 작으면 최소거리 변수에 값 저장 및 조합 idx 값 저장
					if (distance < minDistance) {
						minDistance = distance;
						closestPointIndex = i;
//						loadCheckLog.append("  - **New Min Distance Found!** distance: " + minDistance + ", closestPointIndex: " + closestPointIndex + "#");
					}

				}


			}
		}

		// 최종 결과 로그
		loadCheckLog.append("--- Final Result ---#");
		loadCheckLog.append("Final closestPointIndex: " + closestPointIndex + "#");
		if (closestPointIndex != -1) {
			loadCheckLog.append("Selected Pump Combination: " + collectData.get(closestPointIndex).get("pumpComb") + "#");
		}
		loadCheckLog.append("--------------------#");
		List<String> agoComb = new ArrayList<>();
		HashMap<String, Double> agoFreqMap = new HashMap<>();
		String agoPumpUse = null;
		String agoFreqUse = null;
		HashMap<String, Object> agoPumpUseParam = new HashMap<>();
		agoPumpUseParam.put("targetDate", ts);

		agoPumpUseParam.put("pump_grp", pump_grp);


		HashMap<String, String> agoPumpUseMap = drvnMapper.getPreUsePumpString(agoPumpUseParam);


		if (agoPumpUseMap != null) {
			if (agoPumpUseMap.containsKey("PUMP_USE_RST")) {
				String value = agoPumpUseMap.get("PUMP_USE_RST");
				if (value != null && !value.trim().isEmpty()) {
					agoPumpUse = value;
				}
			}

			if (agoPumpUseMap.containsKey("SPI_USE_RST")) {
				String value = agoPumpUseMap.get("SPI_USE_RST");
				if (value != null && !value.trim().isEmpty()) {
					agoFreqUse = value;
				}
			}
		}

		if (agoPumpUse != null && !agoPumpUse.isEmpty()) {
			String[] strArray = agoPumpUse.split(",");
			List<String> strList = Arrays.stream(strArray)
					.map(String::trim)
					.collect(Collectors.toList());
			List<String> combIvtPump = new ArrayList<>();
			for (String pump : strList) {
				if (typeMap.containsKey(pump)) {
					if (typeMap.get(pump) == 2) {
						combIvtPump.add(pump);
					}
				}
			}
			HashMap<String, Double> beforeFreqMap = new HashMap<>();
			if (agoFreqUse != null && !agoFreqUse.trim().isEmpty() && !combIvtPump.isEmpty()) {

				String[] freqArr = agoFreqUse.split(",");
				List<String> freqList = Arrays.stream(freqArr)
						.map(String::trim)
						.collect(Collectors.toList());
				for (int i = 0; i < combIvtPump.size(); i++) {
					String pump_idx = combIvtPump.get(i);
					Double freqDb = 0.0;

					String freqStr = freqList.get(i);
					freqDb = Double.valueOf(freqStr);
					beforeFreqMap.put(pump_idx, freqDb);

				}

				agoComb = strList;
				agoFreqMap = beforeFreqMap;


			}
		}
		@SuppressWarnings("unchecked")
		HashMap<String, Double> freqMap = null;
		boolean ago_pump_use = false;
		boolean gu_bool = false;
		boolean ba_bool = false;
		final double MIN_FREQ = 48.0;
		final double MAX_FREQ = 60.0;
		boolean gs_bool = false;
		boolean gr_bool = false;
		boolean gsLowLoad = false;
		String changeStatus = "keep";
		String freqIdx = "0";
		if (wpp_code.equals("gu")) {
			String idx = "";

			DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
			int week = dayOfWeek.getValue();
			int month = dateTime.getMonthValue();
			int hour = dateTime.getHour();
			String load = reduceMap.get(month).get(hour);
			HolidayChecker holidayChecker = new HolidayChecker();
			boolean passDayBool = holidayChecker.isPassDay(ts);
			if (week == 7 || passDayBool) {
				load = "L";
			} else if (week == 6) {
				if (load.equals("H")) {
					load = "M";
				}
			}


			boolean weekdayLunch = !passDayBool && week <= 5 && hour == 12;
			boolean weekdaysBool = !passDayBool && week <= 5 && (hour >= 7 && hour <= 10);

			HashMap<String, Object> waterLevelParam = new HashMap<>();
			waterLevelParam.put("nowDateTime", ts);

			boolean plusCondition = false; // + 조건 체크용
			boolean minusCondition = false; // - 조건 체크용
			waterLevelParam.put("tagname", "891-365-LEI-8652");
			Double oshikdoBaesuji = drvnMapper.selectRawData(waterLevelParam);
			waterLevelParam.put("tagname", "891-365-LEI-8600");
			Double naunbaeSuji = drvnMapper.selectRawData(waterLevelParam);

			if (weekdaysBool) {
				//평일
				final double OSHIKDO_MIN_LEVEL = 3.8;
				final double OSHIKDO_MAX_LEVEL = 4.1;
				final double NAUNBAE_MIN_LEVEL = 4.05;
				final double NAUNBAE_MAX_LEVEL = 4.0;
				//오식도 배수지 수위 4.05m 미만이면 예측조합보다 한단계 up, 4.1m 이상이면 한단계 다운
				if (oshikdoBaesuji != null) {
					if (oshikdoBaesuji < OSHIKDO_MIN_LEVEL) {
						plusCondition = true;  // + 조건 만족
					} else if (oshikdoBaesuji >= OSHIKDO_MAX_LEVEL) {
						minusCondition = true;  // - 조건 만족
					}
				}

				if (naunbaeSuji != null) {
					if (naunbaeSuji < NAUNBAE_MIN_LEVEL) {
						plusCondition = true;  // + 조건 만족
					} else if (naunbaeSuji >= NAUNBAE_MAX_LEVEL) {
						minusCondition = true;  // - 조건 만족
					}
				}
			} else if (weekdayLunch) {
				//평일 12:00 ~ 12:59까지 두 수위가 둘다 4.1 미만일 시 증가
				final double MIN_LEVEL = 4.1;
				if (oshikdoBaesuji < MIN_LEVEL || naunbaeSuji < MIN_LEVEL) {
					plusCondition = true;
				}
			} else if (load.equals("H")) {
				//최대 부하시간 배수지 수위 검사
				final double OSHIKDO_MIN_LEVEL = 3.8;
				final double OSHIKDO_MAX_LEVEL = 3.9;
				final double NAUNBAE_MIN_LEVEL = 3.7;
				final double NAUNBAE_MAX_LEVEL = 4.0;
				if (oshikdoBaesuji != null) {
					if (oshikdoBaesuji < OSHIKDO_MIN_LEVEL) {
						plusCondition = true;  // + 조건 만족
					} else if (oshikdoBaesuji >= OSHIKDO_MAX_LEVEL) {
						minusCondition = true;  // - 조건 만족
					}
				}

				if (naunbaeSuji != null) {
					if (naunbaeSuji < NAUNBAE_MIN_LEVEL) {
						plusCondition = true;  // + 조건 만족
					} else if (naunbaeSuji >= NAUNBAE_MAX_LEVEL) {
						minusCondition = true;  // - 조건 만족
					}
				}
			} else {
				//그 외에 시간대
				final double OSHIKDO_MIN_LEVEL = 3.8;
				final double OSHIKDO_MAX_LEVEL = 4.1;
				final double NAUNBAE_MIN_LEVEL = 3.8;
				final double NAUNBAE_MAX_LEVEL = 4.0;
				if (oshikdoBaesuji != null) {
					if (oshikdoBaesuji < OSHIKDO_MIN_LEVEL) {
						plusCondition = true;  // + 조건 만족
					} else if (oshikdoBaesuji >= OSHIKDO_MAX_LEVEL) {
						minusCondition = true;  // - 조건 만족
					}
				}

				if (naunbaeSuji != null) {
					if (naunbaeSuji < NAUNBAE_MIN_LEVEL) {
						plusCondition = true;  // + 조건 만족
					} else if (naunbaeSuji >= NAUNBAE_MAX_LEVEL) {
						minusCondition = true;  // - 조건 만족
					}
				}
			}
			// 결과 설정
			if (plusCondition) {
				gu_bool = true;  // + 조건이 하나라도 있으면 true
				idx = "+";  // 우선 +로 설정
			} else if (minusCondition) {
				gu_bool = true;  // - 조건만 있을 때 true
				idx = "-";  // +가 없을 경우에만 -로 설정
			}
			boolean naunHighLevel = false;
			if (naunbaeSuji > 4.15) {
				naunHighLevel = true;
				gu_bool = true;  // - 조건만 있을 때 true
				idx = "-";  // +가 없을 경우에만 -로 설정
			}


			if (!gu_bool) {

				List<String> leiList = new ArrayList<>();
				leiList.add("891-365-LEI-4000");
				leiList.add("891-365-LEI-4001");
				HashMap<String, Object> rawParam = new HashMap<>();
				rawParam.put("nowDateTime", ts);
				for (String lei : leiList) {
					rawParam.put("tagname", lei);
					Double leiDb = drvnMapper.selectRawData(rawParam);

					if (leiDb != null) {
						if (leiDb < 2.7 && leiDb >= 0.4) {
							gu_bool = true;
							idx = "-";
							break;
						} else if (leiDb > 3.6) {
							gu_bool = true;
							idx = "+";
							break;
						}

					}
				}


			}

			if (gu_bool) {
				if (idx.equals("+")) {
					changeStatus = "up";
				} else if (idx.equals("-")) {
					changeStatus = "down";
				}
				int size = collectData.size() - 1;
				int upDownCnt = 1;
				HashMap<String, Object> statusParam = new HashMap<>();
				statusParam.put("nowDate", ts);
				//3단계 조건 제외로 인한 조회 범위 축소
				statusParam.put("interval", 15);
				statusParam.put("limit", 10);

				HashMap<String, Object> pumpMap = new HashMap<>();

				pumpMap.put("nowDate", ts);
				pumpMap.put("pump_grp", pump_grp);

				if (!changeStatus.equals("keep")) {
					if (!weekdayLunch && !naunHighLevel) {
						List<String> guPumpStatus = drvnMapper.guPumpStatusChange(statusParam);
						List<String> change1List = guPumpStatus.subList(0, Math.min(10, guPumpStatus.size()));
						Set<String> chn1st = new HashSet<>(change1List);
						/*
						펌프 주파수 변화를 검사
						직전 2번 3번 펌프의 주파수 값을 가져와(10분, 20분)
						2단계 상승은 각 펌프 모두 직전 주파수 값이 1가지로 유지되어야함(성능점으로 인한 펌프 주파수 변경에 대응)
						 */
						pumpMap.put("interval", 15);
						pumpMap.put("limit", 10);
						pumpMap.put("pump_idx", 2);

						pumpMap.put("pump_idx", 3);

						if (chn1st.size() == 1 && chn1st.contains(changeStatus)) {
							//2단계 증감
							upDownCnt += 1;
						}
					}
				}
				if (idx.equals("+")) {

					if ((closestPointIndex + upDownCnt) >= size) {
						returnComb = (List<String>) (collectData.get(size)).get("pumpComb");

						if ((collectData.get(closestPointIndex)).containsKey("freq")) {
							freqMap = (HashMap<String, Double>) (collectData.get(size)).get("freq");
						}
					} else {
						returnComb = (List<String>) (collectData.get(closestPointIndex + upDownCnt)).get("pumpComb");

						if ((collectData.get(closestPointIndex)).containsKey("freq")) {
							freqMap = (HashMap<String, Double>) (collectData.get(closestPointIndex + upDownCnt)).get("freq");
						}
					}
				} else if (idx.equals("-")) {

					if ((closestPointIndex - upDownCnt) <= 0) {
						returnComb = (List<String>) (collectData.get(0)).get("pumpComb");

						if ((collectData.get(closestPointIndex)).containsKey("freq")) {
							freqMap = (HashMap<String, Double>) (collectData.get(0)).get("freq");
						}
					} else {
						returnComb = (List<String>) (collectData.get(closestPointIndex - upDownCnt)).get("pumpComb");

						if ((collectData.get(closestPointIndex)).containsKey("freq")) {
							freqMap = (HashMap<String, Double>) (collectData.get(closestPointIndex - upDownCnt)).get("freq");
						}
					}
				}
			} else {
				returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");

				if ((collectData.get(closestPointIndex)).containsKey("freq")) {
					freqMap = (HashMap<String, Double>) (collectData.get(closestPointIndex)).get("freq");
				}
			}

		} else if (wpp_code.equals("wm")) {
			freqMap = null;
			//조합식에 따른 인버터 부여
			if (closestPointIndex != 0) {
				freqMap = new HashMap<>();

				if (closestPointIndex == 1) {
					freqIdx = "4";
				} else {
					if (wm_day % 2 == 0) {
						freqIdx = "2";
					} else {
						freqIdx = "1";
					}
				}
				typeMap.put(freqIdx, 2);
				freqMap.put(freqIdx, 60.0);

			}


			returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");

		} else if (wpp_code.equals("gs")) {
			int hour = dateTime.getHour();
			int minute = dateTime.getMinute();

			boolean is2200UpCondition = false;
			if (hour >= 22 || hour <= 7) {
				gs_bool = true;
				List<String> levelTagList;
				HashMap<String, Object> levelMap = new HashMap<>();
				levelMap.put("nowDateTime", ts);
				Double optLevel = drvnMapper.getGosanOptLevel(hour);

				// 효자배수지 목표값 조회 (새로 추가)
				Double hujaOptLevel = drvnMapper.getHujaOptLevel(hour);
				// 효자배수지 평균 수위 계산 (새로 추가)
				double hujaAvgLevel = 0.0;
				double hujaSumLevel = 0.0;
				int hujaCount = 0;
				List<String> hujaLevelTags = Arrays.asList("701-367-LEI-8009", "701-367-LEI-8010");
				for (String hujaTag : hujaLevelTags) {
					levelMap.put("DSTRB_ID", hujaTag);
					List<HashMap<String, Object>> hujaLevelList = drvnMapper.curFlowPressure(levelMap);
					if (hujaLevelList != null && !hujaLevelList.isEmpty()) {
						String hujaLevelStr = (String) hujaLevelList.get(0).get("value");
						double hujaLevel = Double.parseDouble(hujaLevelStr);
						if (hujaLevel >= 1.0) { // 1 미만 값 무시
							hujaCount++;
							hujaSumLevel += hujaLevel;
						}
					}
				}
				if (hujaCount > 0) {
					hujaAvgLevel = hujaSumLevel / hujaCount;
				}

				String pumpStatus = "using";

				List<String> tagArray = Arrays.asList("701-367-LEI-8001", "701-367-LEI-8005");

				double sumLevel = 0.0;
				for (String tag : tagArray) {
					int count = 0;
					double avgLevel = 0.0;

					if (tag.equals("701-367-LEI-8001")) {
						levelTagList = Arrays.asList("701-367-LEI-8001", "701-367-LEI-8002", "701-367-LEI-8003", "701-367-LEI-8004");
					} else {
						levelTagList = Arrays.asList("701-367-LEI-8005", "701-367-LEI-8006", "701-367-LEI-8007", "701-367-LEI-8008");
					}
					for (String level : levelTagList) {
						levelMap.put("DSTRB_ID", level);
						List<HashMap<String, Object>> forLevelList = drvnMapper.curFlowPressure(levelMap);
						if (forLevelList != null && !forLevelList.isEmpty()) {
							String forLevelStr = (String) forLevelList.get(0).get("value");
							double forLevel = Double.parseDouble(forLevelStr);
							// 1 미만의 값은 무시하도록 조건 추가
							if (forLevel >= 1.0) {
								count++;
								avgLevel += forLevel;
							}
						}
					}
					// count가 0일 경우, sumLevel에 0이 더해지도록 예외 처리 추가
					if (count > 0) {
						sumLevel += avgLevel / count;
					}
				}

				// 효자배수지 목표값 조건 추가 (가장 높은 우선순위)
				if (hujaAvgLevel < hujaOptLevel) {
					pumpStatus = "up";
				} else { // 효자배수지 목표값에 도달했을 경우 기존 로직 실행
					if (hour != 23 && minute == 0) { // 23시를 제외한 정각
						if (optLevel > sumLevel) {
							pumpStatus = "up";
						} else if (optLevel + 0.3 <= sumLevel) {
							pumpStatus = "down";
						}
					}
				}

				// 22시 특별 로직 플래그 설정: pumpStatus가 'up'이고 22시 정각이면 is2200UpCondition을 true로 설정
				if (hour == 22 && minute == 0 && "up".equals(pumpStatus)) {
					is2200UpCondition = true;
				}

				if ("up".equals(pumpStatus)) {
					levelMap.put("DSTRB_ID", "701-370-PRI-8005"); // 압력 태그
					List<HashMap<String, Object>> pressureList = drvnMapper.curFlowPressure(levelMap);

					// 1. DB 조회 결과 리스트가 유효한지 확인
					if (pressureList != null && !pressureList.isEmpty()) {
						String pressureStr = (String) pressureList.get(0).get("value");

						// ### 추가된 부분 ###
						// 2. 가져온 압력값이 null이 아니고 비어있지 않은지 확인
						if (pressureStr != null && !pressureStr.trim().isEmpty()) {
							try {
								double jPressure = Double.parseDouble(pressureStr);
								if (jPressure > 8.4) {
									pumpStatus = "using"; // 압력 높으면 'up' 시키지 않고 현재 상태 유지
								}
							} catch (NumberFormatException e) {
								// 만약 값이 숫자가 아닐 경우를 대비한 예외 처리
								// 필요시 에러 로그를 남길 수 있습니다.
							}
						}
						// pressureStr가 null이거나 비어있다면, 압력 체크 로직을 실행하지 않고 넘어갑니다.
					}
				}

				if (is2200UpCondition) {
					// 22시 특별 UP 조건이 발동했다면, pumpStatus 상태와 관계없이 최적 조합을 먼저 찾는다.
					// (압력 초과로 pumpStatus가 'using'으로 변경되었더라도 22시에는 증대가 필요하다고 판단)
					returnComb = findOptimalPumpCombFor2200(collectData);
				} else if (pumpStatus.equals("using")) {
					HashMap<String, Object> pumpUseParam = new HashMap<>();
					pumpUseParam.put("targetDate", ts);

					pumpUseParam.put("pump_grp", pump_grp);
					//직전 예측 펌프 조합

					String beforePumpUse = null;
					HashMap<String, String> beforePumpUseMap = drvnMapper.getPreUsePumpString(pumpUseParam);
					if (beforePumpUseMap != null) {
						if (beforePumpUseMap.containsKey("PUMP_USE_RST")) {
							String value = beforePumpUseMap.get("PUMP_USE_RST");
							if (value != null && !value.trim().isEmpty()) {
								beforePumpUse = value;
							}
						}

						if (beforePumpUse != null && !beforePumpUse.isEmpty()) {
							String[] strArray = beforePumpUse.split(",");

							returnComb = Arrays.stream(strArray)
									.map(String::trim)
									.collect(Collectors.toList());

						}

					}

					if (returnComb.isEmpty() || returnComb == null) {
						returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");
					}
				} else {
					if (pumpStatus.equals("up")) {
						int size = collectData.size() - 1;
						if (closestPointIndex == size) {
							returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");
						} else {
							returnComb = (List<String>) (collectData.get(closestPointIndex + 1)).get("pumpComb");
						}

					} else {
						if (closestPointIndex == 0) {
							returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");
						} else {
							returnComb = (List<String>) (collectData.get(closestPointIndex - 1)).get("pumpComb");
						}
					}
				}
				if (hour == 7 && minute >= 30) {
					if (returnComb != null && !returnComb.isEmpty()) {
						// 현재 조합의 펌프 대수를 계산합니다.
						double currentPumpSize = calculatePumpSize(returnComb);

						// 펌프 대수가 4.0대를 초과하는 경우, 4.0대 이하 조합으로 조정합니다.
						if (currentPumpSize > 4.0) {
							// 현재 조합의 인덱스를 찾습니다.
							int currentIndex = -1;
							for (int i = 0; i < collectData.size(); i++) {
								List<String> comb = (List<String>) collectData.get(i).get("pumpComb");

								if (returnComb.equals(comb)) {
									currentIndex = i;
									break;
								}
							}


							if (currentIndex != -1) {

								for (int i = currentIndex; i >= 0; i--) {
									List<String> candidateComb = (List<String>) collectData.get(i).get("pumpComb");
									double candidateSize = calculatePumpSize(candidateComb);


									if (candidateSize <= 4.0) {
										returnComb = candidateComb;
										break;
									}
								}
							}
						}
					}
				}
			}
//			else if (hour == 8) {
//				gs_bool = true;
//				returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");
//
//			}
			else {
				returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");
			}
		} else if (wpp_code.equals("gr")) {
			int hour = dateTime.getHour();
			int minute = dateTime.getMinute();
			if (pump_grp == 1) {
				// 01:00부터 06:00까지
				if (hour >= 0 && hour < 8) {
					gr_bool = true;
					gsLowLoad = true;

					HashMap<String, Object> rawParam = new HashMap<>();
					rawParam.put("nowDateTime", ts);

					rawParam.put("tagname", "780-344-LEI-8040");
					Double sungjuAllLevel = drvnMapper.selectRawData(rawParam);
					rawParam.put("tagname", "780-344-LEI-8022");
					Double dasanLevel = drvnMapper.selectRawData(rawParam);
					Double waterThreshold = 2.8;
					if (hour >= 6 && hour < 8) {
						waterThreshold = 3.0;
					}


					freqMap = new HashMap<>();
					freqMap.put("4", 60.0);

					if ((hour == 0 && minute < 30) || (sungjuAllLevel < waterThreshold || dasanLevel < waterThreshold)) {
						returnComb = getPumpCombination(pump_grp, 3, 1);

					}// 하나의 값이라도 최소값보다 작으면 켜짐 조건
					else if ((sungjuAllLevel < waterThreshold || dasanLevel < waterThreshold) && hour >= 6) {
						returnComb = getPumpCombination(pump_grp, 3, 1);

					}
					// 모든 값이 최대값보다 크면 꺼짐 조건
					else if (sungjuAllLevel > waterThreshold && dasanLevel > waterThreshold) {
						returnComb = getPumpCombination(pump_grp, 2, 1);

					} else {
						returnComb = agoComb;
					}
				} else {
					// 다른 시간대는 기존 거리계산에 따른 펌프 조합을 사용
					int size = ((List<String>) (collectData.get(closestPointIndex)).get("pumpComb")).size();
					returnComb = getPumpCombination(pump_grp, size, 1);
					if ((collectData.get(closestPointIndex)).containsKey("freq")) {
						freqMap = (HashMap<String, Double>) (collectData.get(closestPointIndex)).get("freq");
					}
				}
			} else if (pump_grp == 3) {
				String sunnamPump = (wm_day % 2 == 0) ? "10" : "11";
				boolean changePump = false;
				gr_bool = true;
				// 독립된 펌프 실행환경
				gsLowLoad = true;
				// 직전 펌프조합에 따라 계산이 변경되며 30분간의 펌프 조합을 유지
				if (agoComb == null || agoComb.isEmpty()) {
					HashMap<String, Object> pumpMap = new HashMap<>();
					pumpMap.put("startDate", ts);
					pumpMap.put("local", "custom");
					pumpMap.put("limit", 30);
					pumpMap.put("interval", 35);
					pumpMap.put("pump_idx", 10);


					List<Integer> pump2stUseList = drvnMapper.optPrePumpUse(pumpMap);
					boolean sunnam2st = pump2stUseList.contains(1);

					pumpMap.put("pump_idx", 11);
					List<Integer> pump3stUseList = drvnMapper.optPrePumpUse(pumpMap);
					boolean sunnam3st = pump3stUseList.contains(1);

					if (!sunnam2st && !sunnam3st) {
						changePump = true;
					}
				} else if (!agoComb.isEmpty()) {
					String usePumpStr = agoComb.get(0);
					int usePump = Integer.parseInt(usePumpStr);
					HashMap<String, Object> pumpMap = new HashMap<>();
					pumpMap.put("startDate", ts);
					pumpMap.put("local", "custom");
					pumpMap.put("limit", 30);
					pumpMap.put("interval", 35);
					pumpMap.put("pump_idx", usePump);


					List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
					boolean sunnamUse = pumpUseList.contains(0);
					if (!sunnamUse) {
						changePump = true;
					}

				}


				/**
				 *선남
				 * 최대는 AND : 펌프종료
				 * 최소는 OR : 펌프가동
				 *
				 * 08:00 ~ 12:59
				 * 성주통합 : 3.0 - 3.5
				 * 선남 : 3.0 - 3.3
				 *
				 * 13:00-17:59
				 * 수위가 3(선남/성주) M 이상이고, 유입(직전 10분 평균)이 유출(직전 10분 평균)량보다 많으면 펌프 OFF
				 * 수위가 2.8(선남/성주) M 이하로 떨어지고, 유입량이 유출량보다 적으면 펌프 ON
				 *  선남 유입유량
				 * 780-344-FRI-8004
				 * 선남 유출유량
				 * 780-344-FRI-8034
				 *
				 * 성주 유입유량
				 * 780-344-FRI-8054
				 * 성주 유출유량
				 * 780-344-FRI-8035
				 * 18:00 - 22:59
				 * 성주통합 : 2.15 - 2.8
				 * 선남 : 2.5 - 2.8
				 *
				 * 11번펌프 가동시 60Hz로 시작(주파수조절은 아직X
				 */
				if (agoComb == null || agoComb.isEmpty()) {
					returnComb = new ArrayList<>();
					freqMap = new HashMap<>();
				} else {
					returnComb = agoComb;
					freqMap = new HashMap<>();
					if (agoFreqMap != null && !agoFreqMap.isEmpty()) {
						freqMap = agoFreqMap;
					}
				}
				if (changePump) {

					HashMap<String, Object> rawParam = new HashMap<>();
					rawParam.put("nowDateTime", ts);

					rawParam.put("tagname", "780-344-LEI-8040");
					Double sungjuAllLevel = drvnMapper.selectRawData(rawParam);
					rawParam.put("tagname", "780-344-LEI-8038");
					Double sunnamLevel = drvnMapper.selectRawData(rawParam);
					rawParam.put("tagname", "780-344-FRI-8054");
					Double sungjuInFlow = drvnMapper.select10MinuteAvgRawData(rawParam);
					rawParam.put("tagname", "780-344-FRI-8035");
					Double sungjuOutFlow = drvnMapper.select10MinuteAvgRawData(rawParam);
					rawParam.put("tagname", "780-344-FRI-8004");
					Double sunnamInFlow = drvnMapper.select10MinuteAvgRawData(rawParam);
					rawParam.put("tagname", "780-344-FRI-8034");
					Double sunnamOutFlow = drvnMapper.select10MinuteAvgRawData(rawParam);
					if (hour < 8) {
						DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
						int week = dayOfWeek.getValue();
						HolidayChecker holidayChecker = new HolidayChecker();
						Boolean passDayBool = holidayChecker.isPassDay(ts);
						HashMap<String, Double> thresholds = new HashMap<>();
						if (!passDayBool && week <= 5) {
							if (hour >= 0 && hour < 2) {
								thresholds.put("780-344-LEI-8040", 3.0); // sungjuAllLevel에 대한 최소, 최대
								thresholds.put("780-344-LEI-8038", 3.0); // sunnamLevel에 대한 최소, 최대
							} else if (hour >= 2 && hour < 4) {
								thresholds.put("780-344-LEI-8040", 3.4); // sungjuAllLevel에 대한 최소, 최대
								thresholds.put("780-344-LEI-8038", 3.2); // sunnamLevel에 대한 최소, 최대

							} else if (hour >= 4 && hour < 6) {
								thresholds.put("780-344-LEI-8040", 3.9); // sungjuAllLevel에 대한 최소, 최대
								thresholds.put("780-344-LEI-8038", 3.4); // sunnamLevel에 대한 최소, 최대

							} else {
								thresholds.put("780-344-LEI-8040", 4.1); // sungjuAllLevel에 대한 최소, 최대
								thresholds.put("780-344-LEI-8038", 3.5); // sunnamLevel에 대한 최소, 최대
							}
						} else {
							if (hour >= 0 && hour < 2) {
								thresholds.put("780-344-LEI-8040", 3.0); // sungjuAllLevel에 대한 최소, 최대
								thresholds.put("780-344-LEI-8038", 3.0); // sunnamLevel에 대한 최소, 최대
							} else if (hour >= 2 && hour < 4) {
								thresholds.put("780-344-LEI-8040", 3.3); // sungjuAllLevel에 대한 최소, 최대
								thresholds.put("780-344-LEI-8038", 3.2); // sunnamLevel에 대한 최소, 최대

							} else if (hour >= 4 && hour < 6) {
								thresholds.put("780-344-LEI-8040", 3.7); // sungjuAllLevel에 대한 최소, 최대
								thresholds.put("780-344-LEI-8038", 3.3); // sunnamLevel에 대한 최소, 최대

							} else {
								thresholds.put("780-344-LEI-8040", 4.0); // sungjuAllLevel에 대한 최소, 최대
								thresholds.put("780-344-LEI-8038", 3.5); // sunnamLevel에 대한 최소, 최대
							}
						}


						Double sungjuThreshold = thresholds.get("780-344-LEI-8040");
						Double sunnamThreshold = thresholds.get("780-344-LEI-8038");


						// 모든 값이 최대값보다 크면 꺼짐 조건
						if (sungjuAllLevel > sungjuThreshold || sunnamLevel > sunnamThreshold) {
							returnComb = new ArrayList<>();
							freqMap = new HashMap<>();
						}
						// 하나의 값이라도 최소값보다 작으면 켜짐 조건
						else if (sungjuAllLevel < sungjuThreshold || sunnamLevel < sunnamThreshold) {
							returnComb = new ArrayList<>();
							returnComb.add(sunnamPump);
							freqMap = new HashMap<>();
							if (sunnamPump.equals("11")) {
								freqMap.put("11", 60.0);
							}
						}
					} else if (hour >= 8 && hour < 13) {
						// 중부하부터 최대부하 최소값과 최대값 설정
						HashMap<String, Double[]> thresholds = new HashMap<>();
						thresholds.put("780-344-LEI-8040", new Double[]{3.0, 3.5}); // sungjuAllLevel에 대한 최소, 최대
						thresholds.put("780-344-LEI-8038", new Double[]{3.0, 3.3}); // sunnamLevel에 대한 최소, 최대

						Double[] sungjuThreshold = thresholds.get("780-344-LEI-8040");
						Double[] sunnamThreshold = thresholds.get("780-344-LEI-8038");


						// 모든 값이 최대값보다 크면 꺼짐 조건
						if (sungjuAllLevel > sungjuThreshold[1] || sunnamLevel > sunnamThreshold[1]) {
							returnComb = new ArrayList<>();
							freqMap = new HashMap<>();
						}
						// 하나의 값이라도 최소값보다 작으면 켜짐 조건
						else if (sungjuAllLevel < sungjuThreshold[0] || sunnamLevel < sunnamThreshold[0]) {
							returnComb = new ArrayList<>();
							returnComb.add(sunnamPump);
							freqMap = new HashMap<>();
							if (sunnamPump.equals("11")) {
								freqMap.put("11", 60.0);
							}
						}
					} else if (hour >= 13 && hour < 18) {
						// 중부하부터 최대부하 최소값과 최대값 설정
						HashMap<String, Double[]> thresholds = new HashMap<>();
						thresholds.put("780-344-LEI-8040", new Double[]{2.8, 3.0}); // sungjuAllLevel에 대한 최소, 최대
						thresholds.put("780-344-LEI-8038", new Double[]{2.8, 3.0}); // sunnamLevel에 대한 최소, 최대

						Double[] sungjuThreshold = thresholds.get("780-344-LEI-8040");
						Double[] sunnamThreshold = thresholds.get("780-344-LEI-8038");


						// 모든 값이 최대값보다 크면 꺼짐 조건
						if (sungjuAllLevel > sungjuThreshold[1] || sunnamLevel > sunnamThreshold[1]) {
							if (sungjuInFlow > sungjuOutFlow && sunnamInFlow > sunnamOutFlow) {
								returnComb = new ArrayList<>();
								freqMap = new HashMap<>();
							}
						}
						// 하나의 값이라도 최소값보다 작으면 켜짐 조건
						else if (sungjuAllLevel < sungjuThreshold[0] || sunnamLevel < sunnamThreshold[0]) {
							if (sungjuInFlow < sungjuOutFlow && sunnamInFlow < sunnamOutFlow) {
								returnComb = new ArrayList<>();
								returnComb.add(sunnamPump);
								freqMap = new HashMap<>();
								if (sunnamPump.equals("11")) {
									freqMap.put("11", 60.0);
								}
							}
						}
					} else if (hour >= 18 && hour < 22) {
						// 그외 시간대 최소값과 최대값 설정
						HashMap<String, Double[]> thresholds = new HashMap<>();
						thresholds.put("780-344-LEI-8040", new Double[]{2.15, 2.8}); // sungjuAllLevel에 대한 최소, 최대
						thresholds.put("780-344-LEI-8038", new Double[]{2.5, 2.8}); // sunnamLevel에 대한 최소, 최대

						Double[] sungjuThreshold = thresholds.get("780-344-LEI-8040");
						Double[] sunnamThreshold = thresholds.get("780-344-LEI-8038");


						// 모든 값이 최대값보다 크면 꺼짐 조건
						if (sungjuAllLevel > sungjuThreshold[1] || sunnamLevel > sunnamThreshold[1]) {
							returnComb = new ArrayList<>();
							freqMap = new HashMap<>();
						}
						// 하나의 값이라도 최소값보다 작으면 켜짐 조건
						else if (sungjuAllLevel < sungjuThreshold[0] || sunnamLevel < sunnamThreshold[0]) {
							returnComb = new ArrayList<>();
							returnComb.add(sunnamPump);
							freqMap = new HashMap<>();
							if (sunnamPump.equals("11")) {
								freqMap.put("11", 60.0);
							}
						}
					} else if (hour >= 22) {
						// 그외 시간대 최소값과 최대값 설정
						HashMap<String, Double[]> thresholds = new HashMap<>();
						thresholds.put("780-344-LEI-8040", new Double[]{2.3, 2.8}); // sungjuAllLevel에 대한 최소, 최대
						thresholds.put("780-344-LEI-8038", new Double[]{2.4, 2.8}); // sunnamLevel에 대한 최소, 최대

						Double[] sungjuThreshold = thresholds.get("780-344-LEI-8040");
						Double[] sunnamThreshold = thresholds.get("780-344-LEI-8038");


						// 모든 값이 최대값보다 크면 꺼짐 조건
						if (sungjuAllLevel > sungjuThreshold[1] || sunnamLevel > sunnamThreshold[1]) {
							returnComb = new ArrayList<>();
							freqMap = new HashMap<>();
						}
						// 하나의 값이라도 최소값보다 작으면 켜짐 조건
						else if (sungjuAllLevel < sungjuThreshold[0] || sunnamLevel < sunnamThreshold[0]) {
							returnComb = new ArrayList<>();
							returnComb.add(sunnamPump);
							freqMap = new HashMap<>();
							if (sunnamPump.equals("11")) {
								freqMap.put("11", 60.0);
							}
						}
					}
				}
			} else {
				returnComb = getPumpCombination(2, 1, 1);

				if (collectData.get(closestPointIndex).containsKey("freq")) {
					freqMap = new HashMap<>();

					// freqSubMap을 먼저 꺼냄
					@SuppressWarnings("unchecked")
					HashMap<String, Double> freqSubMap = (HashMap<String, Double>) collectData.get(closestPointIndex).get("freq");

					// 예: 첫 번째 값만 가져오기
					double freq = freqSubMap.values().iterator().next();

					// 필요한 key를 가져와서 map에 넣기
					freqMap.put(getPumpCombination(2, 1, 1).get(0), freq);
				}
			}
		} else if (wpp_code.equals("ba")) {
			// 상수로 최소 및 최대 주파수 정의

			String idx = "";
			DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
			int week = dayOfWeek.getValue();
			int month = dateTime.getMonthValue();
			int hour = dateTime.getHour();
			int minute = dateTime.getMinute();
			String load = reduceMap.get(month).get(hour);
			HolidayChecker holidayChecker = new HolidayChecker();
			boolean passDayBool = holidayChecker.isPassDay(ts);
			if (week == 7 || passDayBool) {
				load = "L";
			} else if (week == 6) {
				if (load.equals("H")) {
					load = "M";
				}
			}
			HashMap<String, Object> pumpUseParam = new HashMap<>();
			pumpUseParam.put("targetDate", ts);

			pumpUseParam.put("pump_grp", pump_grp);

			//직전 예측 펌프 조합

			// 각 배수지의 최소/최대 수위 설정
			HashMap<String, Double[]> thresholds = new HashMap<>();
			thresholds.put("892-481-LEI-8880", new Double[]{1.9, 3.5}); // 아산배수지
			thresholds.put("892-481-LEI-8500", new Double[]{2.1, 3.5}); // 무장배수지
			thresholds.put("892-481-LEI-8450", new Double[]{2.3, 3.6}); // 해리배수지


			if (pump_grp == 1) {

				boolean weekdayLunch = (hour == 12) || (hour == 13 && minute <= 29);
				List<String> leiList = new ArrayList<>();

				leiList.add("892-480-LEI-8000");
				leiList.add("892-480-LEI-8001");
				boolean levelIncreasing = false;
				double minLei = Double.MAX_VALUE;
				HashMap<String, Object> rawParam = new HashMap<>();
				rawParam.put("nowDateTime", ts);
				for (String lei : leiList) {
					rawParam.put("tagname", lei);
					Double currentLeiDb = drvnMapper.selectRawData(rawParam);
					LocalDateTime pastTs = dateTime.minusMinutes(30);
					rawParam.put("nowDateTime", pastTs.format(formatter));
					Double pastLeiDb = drvnMapper.selectRawData(rawParam);
					if (currentLeiDb != null && pastLeiDb != null) {
						if (currentLeiDb > pastLeiDb) {
							levelIncreasing = true;
						}
					} else {
						ago_pump_use = true;
					}
					if (currentLeiDb != null && currentLeiDb > 0.0) {  // 유효한 수치인지 확인
						if (currentLeiDb < minLei) {
							minLei = currentLeiDb;
						}
					}
				}

				HashMap<String, Object> inOutFriParam = new HashMap<>();
				inOutFriParam.put("nowDateTime", ts);
				inOutFriParam.put("tagname", "892-480-FRI-8004");
				Double inFri = drvnMapper.select5MinuteAvgRawData(inOutFriParam);
				inOutFriParam.put("tagname", "892-480-FRI-8000");
				Double outFri = drvnMapper.select5MinuteAvgRawData(inOutFriParam);
				Double sumFri = 0.0;
				if (inFri != null && outFri != null) {
					sumFri = inFri - outFri;
				} else {
					ago_pump_use = true;
				}
				Double agoFreq = agoFreqMap.get("4");
				gsLowLoad = true;
				boolean using_pump = false;
				if (weekdayLunch) {
					returnComb = new ArrayList<>();
					returnComb.add("4");
					returnComb.add("6");
					if (hour == 12 && minute == 0) {
						agoFreq = 60.0;
					}
					agoFreq = baFreqCheck(ts, agoFreq, sumFri);
					freqMap = new HashMap<>();
					freqMap.put("4", agoFreq);
				} else {

					/**
					 * 부안정수장은 3시간 조합 유지조건 X
					 * 주산 가압장 흡수정 수위 892-480-LEI-8000 or 892-480-LEI-8001의 수위가 1.7 이하일때
					 * 아래 펌프 3대 운영
					 * 부안(892-360-FRI-8901), 하서(892-360-FRI-8400), 변산(892-360-FRI-8951)분기 직전 5분간 유량 합의 평균이 1200톤 이상이면 4,5,6 가동,
					 * 직전 5분간 3 분기점 유량 합의 평균이 1200톤 미만이면 2,4,6 가동
					 * 직전 주파수 값 가져와서 사용
					 * 주산 가압장의 유입유량(892-480-FRI-8004)과 유출유량(892-480-FRI-8000)의 차이(직전 5분간 평균)가 +400이상이면 8Hz down
					 * +300이상이면 6Hz 다운
					 * +200이상이면 4Hz 다운
					 * +100이상이면 2Hz 다운
					 * (주파수의 MIN: 40Hz)
					 * -- 5분 정각에만 계산
					 * -300이상이면 6Hz 업
					 * -200이상이면 4Hz 업
					 * -100이상이면 2Hz 업
					 *
					 * 3대일경우 주파수 업만 있음
					 * 2대일 경우 주파수 업다운 + 밸브조건
					 *
					 * 흡수정 수위 892-480-LEI-8000 or 892-480-LEI-8001의 수위가 3m 가 될때까지 직전 조합 유지
					 * 둘 중 하나라도 3m 이상이 됐을시 4,6(60) 가동
					 *
					 *
					 */


					rawParam.put("nowDateTime", ts);

					for (String lei : leiList) {
						rawParam.put("tagname", lei);
						Double leiDb = drvnMapper.selectRawData(rawParam);
						if (leiDb != null) {
							if (leiDb <= 1.8 && leiDb >= 0.3) {
								ba_bool = true;
								break;
							}
						} else {
							ago_pump_use = true;
						}
					}
					if (ba_bool) {
						returnComb = new ArrayList<>();
						if (agoComb.size() == 2) {
							Double friSum = 0.0;
							List<String> friList = new ArrayList<>();
							friList.add("892-360-FRI-8901");
							friList.add("892-360-FRI-8400");
							friList.add("892-360-FRI-8951");
							for (String fri : friList) {
								rawParam.put("tagname", fri);
								Double friDb = drvnMapper.select5MinuteAvgRawData(rawParam);
								if (friDb != null) {
									friSum += friDb;
								} else {
									ago_pump_use = true;
								}
							}

							if (friSum >= 1300.0) {
								returnComb.add("4");
								returnComb.add("5");
								returnComb.add("6");
							} else {
								returnComb.add("2");
								returnComb.add("4");
								returnComb.add("6");
							}
							freqMap = new HashMap<>();
							freqMap.put("4", 60.0);
						} else {
							using_pump = true;
						}

					} else {
						/**
						 * 펌프가 2대 운영중일 때(4,6) (성능점 무시 기준 주파수 60)
						 * 주산 가압장의 유입유량(892-480-FRI-8004)과 유출유량(892-480-FRI-8000)의 차이(직전 5분간 평균)가 +400이상이면 8Hz down
						 * +300이상이면 6Hz 다운
						 * +200이상이면 4Hz 다운
						 * +100이상이면 2Hz 다운
						 * (주파수의 MIN: 40Hz, Max : 60Hz)
						 * -- 5분 정각에만 계산
						 * -300이상이면 6Hz 업
						 * -200이상이면 4Hz 업
						 * -100이상이면 2Hz 업
						 *
						 *
						 */
						if (agoComb.size() == 3) {
							boolean levelCheck = false;
							for (String lei : leiList) {
								rawParam.put("tagname", lei);
								Double leiDb = drvnMapper.selectRawData(rawParam);
								if (leiDb != null) {
									if (leiDb >= 2.8) {
										levelCheck = true;
										break;
									}
								} else {
									ago_pump_use = true;
								}
							}

							if (levelCheck) {
								returnComb.add("4");
								returnComb.add("6");
								freqMap = new HashMap<>();
								freqMap.put("4", 60.0);
							} else {
								boolean buanPumpCheck = false;
								for (String pump : agoComb) {
									int pump_idx = Integer.parseInt(pump);
									HashMap<String, Object> pumpMap = new HashMap<>();
									pumpMap.put("pump_idx", pump_idx);
									pumpMap.put("startDate", ts);
									pumpMap.put("local", "custom");
									pumpMap.put("interval", 65);
									pumpMap.put("limit", 60);

									List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
									buanPumpCheck = pumpUseList.contains(0);

									if (buanPumpCheck) {
										break;
									} else {
										buanPumpCheck = false;
									}
								}

								if (!buanPumpCheck) {
									Double friSum = 0.0;
									List<String> friList = new ArrayList<>();
									friList.add("892-360-FRI-8901");
									friList.add("892-360-FRI-8400");
									friList.add("892-360-FRI-8951");
									for (String fri : friList) {
										rawParam.put("tagname", fri);
										Double friDb = drvnMapper.select5MinuteAvgRawData(rawParam);
										if (friDb != null) {
											friSum += friDb;
										} else {
											ago_pump_use = true;
										}
									}

									if (friSum >= 1300.0) {
										returnComb.add("4");
										returnComb.add("5");
										returnComb.add("6");
									} else {
										returnComb.add("2");
										returnComb.add("4");
										returnComb.add("6");
									}
									freqMap = agoFreqMap;
								} else {
									using_pump = true;
								}
							}
						} else {
							using_pump = true;
						}
					}
					if (using_pump) {
						returnComb = agoComb;

						// 밸브 검사 로직 도입 전
						if (minute % 5 == 0) {
							// sumFri 값을 기준으로 주파수를 증감시킴
							if (returnComb.size() == 2) {

								agoFreq = baFreqCheck(ts, agoFreq, sumFri);
							} else {
								//3대 조건
								if (agoFreq != null) {
									if (sumFri <= -300) {
										agoFreq += 6; // -300 이하이면 6Hz 업
									} else if (sumFri <= -200) {
										agoFreq += 4; // -200 이하이면 4Hz 업
									} else if (sumFri <= -100) {
										agoFreq += 2; // -100 이하이면 2Hz 업
									}

									// 주파수를 MIN_FREQ와 MAX_FREQ 범위 내로 조정
									if (agoFreq < MIN_FREQ) {
										agoFreq = MIN_FREQ; // 최소 주파수는 40Hz
									} else if (agoFreq > MAX_FREQ) {
										agoFreq = MAX_FREQ; // 최대 주파수는 60Hz
									}
								} else {
									agoFreq = agoFreqMap.get("4");
								}
							}
							freqMap = new HashMap<>();
							freqMap.put("4", agoFreq);
						} else {
							freqMap = agoFreqMap;
						}

					}
				}

				// 13시 30분 이후 수위 체크 및 주기적 판단 로직 추가
				if (hour == 13 && minute == 30) {
					if (levelIncreasing) {
						returnComb = agoComb;
						freqMap = agoFreqMap;
					} else {
						Double friSum = 0.0;
						List<String> friList = new ArrayList<>();
						friList.add("892-360-FRI-8901");
						friList.add("892-360-FRI-8400");
						friList.add("892-360-FRI-8951");
						rawParam.put("nowDateTime", ts);
						for (String fri : friList) {
							rawParam.put("tagname", fri);
							Double friDb = drvnMapper.select5MinuteAvgRawData(rawParam);
							if (friDb != null) {
								friSum += friDb;
							} else {
								ago_pump_use = true;
							}
						}
						returnComb = new ArrayList<>();
						if (friSum >= 1300.0) {
							returnComb.add("4");
							returnComb.add("5");
							returnComb.add("6");
						} else {

							returnComb.add("2");
							returnComb.add("4");
							returnComb.add("6");
						}
						freqMap = new HashMap<>();
						freqMap.put("4", 60.0);
					}
				}

				if ((hour >= 18 && hour < 21) && minute % 5 == 0) {
					/**
					 * 4,6 조합일때
					 * 18시 2.4미만 이후 -200 톤이하 차이나면 2,4(50),6
					 * 3대 일때 수위 2.6 초과 시 4,6(60)
					 */
					if (agoComb.size() == 2) {
						if (minLei < 2.4 && sumFri <= -200) {
							returnComb = new ArrayList<>();
							returnComb.add("2");
							returnComb.add("4");
							returnComb.add("6");
							freqMap = new HashMap<>();
							freqMap.put("4", 60.0);
						}
					} else {
						if (minLei > 2.6) {
							returnComb = new ArrayList<>();
							returnComb.add("4");
							returnComb.add("6");
							freqMap = new HashMap<>();
							freqMap.put("4", 60.0);
						}
					}
				}

			} else if (pump_grp == 3) {
				/**
				 * 신림
				 * 아산배수지 최소:1.9  최대: 3.5
				 * 무장배수지: 최소:1.9 최대: 3.5
				 * 해리배수지: 최소:2.1 최대: 3.6
				 * 아산 : 892-481-LEI-8880
				 * 무장(배) : 892-481-LEI-8500
				 * 해리(배) : 892-481-LEI-8450
				 * 3개 배수지 중 한개의 배수지라도 최소 수위에 도달하면 3대가동
				 *
				 * 3개의 배수지 중 한개의 배수지라도 최대 수위에 도달하면 2대 가동
				 */
				boolean sinlimLeiBool = false;
				boolean sinlimMin = false;

				HashMap<String, Double[]> thresholdsGrp3 = new HashMap<>();
				thresholdsGrp3.put("892-481-LEI-8880", new Double[]{1.9, 3.5}); // 아산배수지
				thresholdsGrp3.put("892-481-LEI-8500", new Double[]{1.9, 3.5}); // 무장배수지
				thresholdsGrp3.put("892-481-LEI-8450", new Double[]{2.1, 3.6}); // 해리배수지


				List<String> leiList = Arrays.asList("892-481-LEI-8880", "892-481-LEI-8500", "892-481-LEI-8450");

				HashMap<String, Object> rawParam = new HashMap<>();
				rawParam.put("nowDateTime", ts);

				List<String> sinlimLeiList = new ArrayList<>();

				sinlimLeiList.add("892-481-LEI-8001");
				sinlimLeiList.add("892-480-LEI-8000");
				double nowMinLei = Double.MAX_VALUE;
				for (String lei : sinlimLeiList) {
					rawParam.put("tagname", lei);
					Double leiDb = drvnMapper.selectRawData(rawParam);

					if (leiDb != null && leiDb > 0) {
						if (leiDb < nowMinLei) {
							nowMinLei = leiDb;
						}
					}

				}
				boolean isMinReached = false;
				boolean isMaxReached = false;

				for (String lei : leiList) {
					rawParam.put("tagname", lei);
					Double leiDb = drvnMapper.selectRawData(rawParam); // 직전 수위 값


					if (leiDb != null) {
						Double minLevel = thresholdsGrp3.get(lei)[0];
						Double maxLevel = thresholdsGrp3.get(lei)[1];


						if (leiDb <= minLevel) {

							isMinReached = true;
							break;
						}
						if (leiDb >= maxLevel) {

							isMaxReached = true;
							break;
						}
					} else {
						ago_pump_use = true;
					}
				}
				if (nowMinLei < 1.6) {
					returnComb = new ArrayList<>();
					returnComb.add("11");
					returnComb.add("14");
				} else {
					// 2대 또는 3대 가동 조건
					if (isMinReached) {
						HashMap<String, Object> pumpMap = new HashMap<>();
						pumpMap.put("pump_idx", 13);
						pumpMap.put("startDate", ts);
						pumpMap.put("local", "custom");
						pumpMap.put("limit", 60);
						pumpMap.put("interval", 65);


						List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
						boolean hasZero = pumpUseList.contains(1);
						returnComb = new ArrayList<>();
						returnComb.add("11");
						if (!hasZero && nowMinLei > 1.8) {
							returnComb.add("13");
						}
						returnComb.add("14");

					} else if (isMaxReached) {
						returnComb = new ArrayList<>();
						returnComb.add("11");
						returnComb.add("14");
					}
					if (agoComb.size() == 3) {
						HashMap<String, Object> pumpMap = new HashMap<>();
						pumpMap.put("pump_idx", 13);
						pumpMap.put("startDate", ts);
						pumpMap.put("local", "custom");
						pumpMap.put("limit", 120);
						pumpMap.put("interval", 135);


						List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
						boolean hasZero = pumpUseList.contains(0);
						if (!hasZero) {
							returnComb = new ArrayList<>();
							returnComb.add("11");
							returnComb.add("14");
						} else {
							returnComb = agoComb;
						}

					} else {
						returnComb = agoComb;
					}
				}
				if (returnComb.isEmpty() || returnComb == null) {
					returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");
				}
			} else if (pump_grp == 4) {
				/**
				 * 무장 A 라인
				 * 무장배수지: 최소:2.1 최대: 3.6
				 *
				 * 무장 B라인
				 * 해리배수지: 최소:2.3 최대: 3.7
				 *
				 * 최소 수위 도달하면 A라인은 2번펌프 가동, B라인은 3번펌프 가동
				 *
				 * 최대 수위에 도달하면 A라인은 2번펌프 OFF, B라인은 3번  펌프 OFF
				 */
				HashMap<String, Object> rawParam = new HashMap<>();
				rawParam.put("nowDateTime", ts);
				boolean usingPump = true;
				rawParam.put("tagname", "892-481-LEI-8500");
				Double leiDb = drvnMapper.selectRawData(rawParam); // 직전 수위 값

				if (leiDb != null) {

					Double minLevel = thresholds.get("892-481-LEI-8500")[0];
					Double maxLevel = thresholds.get("892-481-LEI-8500")[1];

					// 최소 수위 도달 여부 확인
					if (leiDb <= minLevel && agoComb.isEmpty()) {
						usingPump = false;
						freqMap = new HashMap<>();
						returnComb = new ArrayList<>();
						returnComb.add("16");
						freqMap.put("16", 46.0);
					} else if (leiDb >= maxLevel && !agoComb.isEmpty()) {
						// 최대 수위 도달 여부 확인
						double minLei = Double.MAX_VALUE;  // 매우 큰 값으로 초기화
						List<String> leiList = Arrays.asList("892-482-LEI-8960", "892-481-LEI-8551", "892-481-LEI-8552");

						for (String lei : leiList) {
							rawParam.put("tagname", lei);
							Double lei_daesan = drvnMapper.selectRawData(rawParam);
							if (lei_daesan != null && lei_daesan > 0.0) {  // 유효한 수치인지 확인
								if (lei_daesan < minLei) {
									minLei = lei_daesan;
								}
							} else {
								ago_pump_use = true;
							}
						}

						// 최소값이 변경된 경우에만 처리
						if (minLei != Double.MAX_VALUE) {
							if (minLei >= 2.6) {
								//종료조건 45로
								usingPump = false;
								returnComb = new ArrayList<>();
								freqMap = new HashMap<>();
								returnComb.add("16");
								freqMap.put("16", 45.0);
							} else {
								usingPump = true;
							}
						} else {
							usingPump = true;
						}

					} else {
						usingPump = true;
					}
				} else {
					ago_pump_use = true;
				}
				if (!agoComb.isEmpty()) {
					HashMap<String, Double> endFreqMap = new HashMap<>();
					endFreqMap.put("16", 45.0);
					HashMap<String, Double> startFreqMap = new HashMap<>();
					startFreqMap.put("16", 46.0);
					if (startFreqMap.equals(agoFreqMap)) {
						double agoValue = 46.0;
						HashMap<String, String> curPumpUseMap = drvnMapper.getCurUsePumpString(pumpUseParam);
						String curPumpUse = null;
						String curFreqUse = null;

						if (curPumpUseMap != null) {
							if (curPumpUseMap.containsKey("PUMP_USE_RST")) {
								String value = curPumpUseMap.get("PUMP_USE_RST");
								if (value != null && !value.trim().isEmpty()) {
									curPumpUse = value;
								}
							}

							if (curPumpUseMap.containsKey("SPI_USE_RST")) {
								String value = curPumpUseMap.get("SPI_USE_RST");
								if (value != null && !value.trim().isEmpty()) {
									curFreqUse = value;
								}
							}
						}

						if (curPumpUse != null && !curPumpUse.isEmpty()) {
							String[] strArray = curPumpUse.split(",");
							List<String> curComb = Arrays.stream(strArray)
									.map(String::trim)
									.collect(Collectors.toList());
							List<String> combIvtPump = new ArrayList<>();
							for (String pump : curComb) {
								if (typeMap.containsKey(pump)) {
									if (typeMap.get(pump) == 2) {
										combIvtPump.add(pump);
									}
								}
							}

							if (curFreqUse != null && !curFreqUse.trim().isEmpty() && !combIvtPump.isEmpty()) {
								HashMap<String, Double> curFreqMap = new HashMap<>();
								String[] freqArr = curFreqUse.split(",");
								List<String> freqList = Arrays.stream(freqArr)
										.map(String::trim)
										.collect(Collectors.toList());
								for (int i = 0; i < combIvtPump.size(); i++) {
									String pump_idx = combIvtPump.get(i);
									double freqDb;

									String freqStr = freqList.get(i);
									freqDb = Double.parseDouble(freqStr);
									curFreqMap.put(pump_idx, freqDb);

								}
								if (new HashSet<>(agoComb).equals(new HashSet<>(curComb))) {
									boolean isWithinTolerance = true;

									for (String key : curFreqMap.keySet()) {
										if (agoFreqMap.containsKey(key)) {
											double curValue = curFreqMap.get(key);


											// 값 차이가 ±1 이내인지 확인
											if (Math.abs(curValue - agoValue) > 1) {
												isWithinTolerance = false;
												break;
											}
										} else {
											// key가 존재하지 않으면 tolerance 범위를 벗어남
											isWithinTolerance = false;
											break;
										}
									}

									if (isWithinTolerance) {
										usingPump = false;
										returnComb = new ArrayList<>();
										returnComb.add("16");
										freqMap = new HashMap<>();
										freqMap.put("16", 52.0);
									} else {
										returnComb = agoComb;
										freqMap = agoFreqMap;
									}
								} else {
									returnComb = agoComb;
									freqMap = agoFreqMap;
								}


							}
						} else {
							returnComb = agoComb;
							freqMap = agoFreqMap;
						}
					} else if (endFreqMap.equals(agoFreqMap)) {
						double agoValue = 45.0;
						HashMap<String, String> curPumpUseMap = drvnMapper.getCurUsePumpString(pumpUseParam);
						String curPumpUse = null;
						String curFreqUse = null;

						if (curPumpUseMap != null) {
							if (curPumpUseMap.containsKey("PUMP_USE_RST")) {
								String value = curPumpUseMap.get("PUMP_USE_RST");
								if (value != null && !value.trim().isEmpty()) {
									curPumpUse = value;
								}
							}

							if (curPumpUseMap.containsKey("SPI_USE_RST")) {
								String value = curPumpUseMap.get("SPI_USE_RST");
								if (value != null && !value.trim().isEmpty()) {
									curFreqUse = value;
								}
							}
						}

						if (curPumpUse != null && !curPumpUse.isEmpty()) {
							String[] strArray = curPumpUse.split(",");
							List<String> curComb = Arrays.stream(strArray)
									.map(String::trim)
									.collect(Collectors.toList());
							List<String> combIvtPump = new ArrayList<>();
							for (String pump : curComb) {
								if (typeMap.containsKey(pump)) {
									if (typeMap.get(pump) == 2) {
										combIvtPump.add(pump);
									}
								}
							}

							if (curFreqUse != null && !curFreqUse.trim().isEmpty() && !combIvtPump.isEmpty()) {
								HashMap<String, Double> curFreqMap = new HashMap<>();
								String[] freqArr = curFreqUse.split(",");
								List<String> freqList = Arrays.stream(freqArr)
										.map(String::trim)
										.collect(Collectors.toList());
								for (int i = 0; i < combIvtPump.size(); i++) {
									String pump_idx = combIvtPump.get(i);
									double freqDb;

									String freqStr = freqList.get(i);
									freqDb = Double.parseDouble(freqStr);
									curFreqMap.put(pump_idx, freqDb);

								}
								if (new HashSet<>(agoComb).equals(new HashSet<>(curComb))) {
									boolean isWithinTolerance = true;

									for (String key : curFreqMap.keySet()) {
										if (agoFreqMap.containsKey(key)) {
											double curValue = curFreqMap.get(key);

											// 값 차이가 ±1 이내인지 확인
											if (Math.abs(curValue - agoValue) > 1) {
												isWithinTolerance = false;
												break;
											}
										} else {
											// key가 존재하지 않으면 tolerance 범위를 벗어남
											isWithinTolerance = false;
											break;
										}
									}

									if (isWithinTolerance) {
										usingPump = false;
										returnComb = new ArrayList<>();
										freqMap = new HashMap<>();
									} else {
										returnComb = agoComb;
										freqMap = agoFreqMap;
									}
								} else {
									returnComb = agoComb;
									freqMap = agoFreqMap;
								}


							}
						} else {
							returnComb = agoComb;
							freqMap = agoFreqMap;
						}
					} else {
						returnComb = agoComb;
						freqMap = agoFreqMap;

					}

				}
				if (usingPump) {
					returnComb = agoComb;
					freqMap = agoFreqMap;

				}
			} else if (pump_grp == 5) {

				returnComb = agoComb;
				freqMap = agoFreqMap;
			} else if (pump_grp == 2) {
				HashMap<String, Object> rawParam = new HashMap<>();
				rawParam.put("nowDateTime", ts);
				List<String> sinlimLeiList = new ArrayList<>();

				sinlimLeiList.add("892-481-LEI-8001");
				sinlimLeiList.add("892-480-LEI-8000");
				double nowMinLei = Double.MAX_VALUE;
				for (String lei : sinlimLeiList) {
					rawParam.put("tagname", lei);
					Double leiDb = drvnMapper.selectRawData(rawParam);

					if (leiDb != null && leiDb > 0) {
						if (leiDb < nowMinLei) {
							nowMinLei = leiDb;
						}
					}

				}
				if (nowMinLei < 1.6) {
					freqMap = new HashMap<>();
					freqMap.put("7", 60.0);
				} else {
					if (agoFreqMap.get("7") != null) {
						double agoFreq = agoFreqMap.get("7");
						if (agoFreq == 60.0) {
							if (nowMinLei < 2.8) {
								freqMap = new HashMap<>();
								freqMap.put("7", 60.0);
							} else {
								returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");

								if ((collectData.get(closestPointIndex)).containsKey("freq")) {
									freqMap = (HashMap<String, Double>) (collectData.get(closestPointIndex)).get("freq");
								}
							}
						} else {
							returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");

							if ((collectData.get(closestPointIndex)).containsKey("freq")) {
								freqMap = (HashMap<String, Double>) (collectData.get(closestPointIndex)).get("freq");
							}
						}
					} else {
						returnComb = (List<String>) (collectData.get(closestPointIndex)).get("pumpComb");

						if ((collectData.get(closestPointIndex)).containsKey("freq")) {
							freqMap = (HashMap<String, Double>) (collectData.get(closestPointIndex)).get("freq");
						}
					}

				}

				if (returnComb.isEmpty()) {
					returnComb = agoComb;
					freqMap = agoFreqMap;
				}
			}

		}

		// 조합 구한 펌프 리스트만 필터링
		List<HashMap<String, Object>> filteredList;
		if (wpp_code.equals("gs")) {
			filteredList = grpList;
		} else {
			filteredList = grpList.stream()
					.filter(map -> map.containsKey("PUMP_GRP") && map.get("PUMP_GRP").equals(pump_grp))
					.collect(Collectors.toList());
		}

		// 거리계산 직전 펌프조합 30분 계산 시작
		HashMap<String, Object> pumpUseParam = new HashMap<>();
		pumpUseParam.put("targetDate", ts);

		pumpUseParam.put("pump_grp", pump_grp);
		//직전 예측 펌프 조합


		HashMap<String, String> beforePumpUseMap = drvnMapper.getPreUsePumpString(pumpUseParam);

		String beforePumpUse = null;
		String beforeFreqUse = null;
		boolean pump_check = true;
		Double pump_freq = 60.0;
		String wm_pump = "0";
		if (beforePumpUseMap != null) {
			loadCheckLog.append("펌프 그룹 : " + pump_grp + "#");
			if (beforePumpUseMap.containsKey("PUMP_USE_RST")) {
				String value = beforePumpUseMap.get("PUMP_USE_RST");
				if (value != null && !value.trim().isEmpty()) {

					beforePumpUse = value;
				}
			}

			if (beforePumpUseMap.containsKey("SPI_USE_RST")) {
				String value = beforePumpUseMap.get("SPI_USE_RST");
				if (value != null && !value.trim().isEmpty()) {

					beforeFreqUse = value;
				}
			}
		}
		if (beforePumpUse != null && !beforePumpUse.isEmpty()) {
			String[] strArray = beforePumpUse.split(",");
			List<String> strList = Arrays.stream(strArray)
					.map(String::trim)
					.collect(Collectors.toList());
			List<String> combIvtPump = new ArrayList<>();
			for (String pump : strList) {
				if (wpp_code.equals("wm")) {
					if (pump.equals("1")) {
						combIvtPump.add("1");
						wm_pump = "1";
						break;
					} else if (pump.equals("2")) {
						combIvtPump.add("2");
						wm_pump = "2";
						break;
					} else if (pump.equals("4")) {
						combIvtPump.add("4");
						wm_pump = "4";
						break;
					}
				} else {
					if (typeMap.containsKey(pump)) {
						if (typeMap.get(pump) == 2) {
							combIvtPump.add(pump);
						}
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
					if (wpp_code.equals("wm")) {
						pump_freq = freqDb;
					}
				}
				loadCheckLog.append("직전 예측 주파수 MAP :" + beforeFreqMap + "#");
			}

			if (!gs_bool || !gsLowLoad) {

				List<String> finalReturnComb = new ArrayList<>(returnComb);
				loadCheckLog.append("💡 GS Logic Initiated. Current returnComb: " + returnComb + "#");


				//실측 조합 대비 종료 예정 펌프
				List<String> endPump = strList.stream()
						.filter(item -> !finalReturnComb.contains(item))
						.collect(Collectors.toList());
				loadCheckLog.append("  - Pumps to end: " + endPump + "#");


				List<String> finalStrList = strList;
				//실측 조합 대비 시작 예정 펌프
				List<String> startPump = finalReturnComb.stream()
						.filter(item -> !finalStrList.contains(item))
						.collect(Collectors.toList());
				loadCheckLog.append("  - Pumps to start: " + startPump + "#");

				boolean hasZero = false;
				int wmPump = 0;
				if (!startPump.isEmpty()) {
					loadCheckLog.append("  - Checking start pumps for conflicts.#");
					for (String pump : startPump) {
						if (pump.isEmpty()) {
							break;
						}
						int pump_idx = Integer.parseInt(pump);
						HashMap<String, Object> pumpMap = new HashMap<>();
						pumpMap.put("pump_idx", pump_idx);
						pumpMap.put("startDate", ts);
						pumpMap.put("local", wpp_code);


						List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
						loadCheckLog.append("    - Pump " + pump + " history: " + pumpUseList + "#");
						hasZero = pumpUseList.contains(1);


						if (hasZero) {
							loadCheckLog.append("    - Conflict found! Pump " + pump + " was already ON. Setting hasZero=true.#");
							if (wpp_code.equals("wm")) {
								pump_check = false;
							}
							break;
						} else {
							if (wpp_code.equals("wm")) {
								pump_check = true;
							}
						}
					}
				}
				if (!endPump.isEmpty() && !hasZero) {
					loadCheckLog.append("  - Checking end pumps for conflicts.#");
					for (String pump : endPump) {
						int pump_idx = Integer.parseInt(pump);
						HashMap<String, Object> pumpMap = new HashMap<>();
						pumpMap.put("pump_idx", pump_idx);
						pumpMap.put("startDate", ts);
						pumpMap.put("local", wpp_code);

						List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
						loadCheckLog.append("    - Pump " + pump + " history: " + pumpUseList + "#");
						hasZero = pumpUseList.contains(0);


						if (hasZero) {
							loadCheckLog.append("    - Conflict found! Pump " + pump + " was already OFF. Setting hasZero=true.#");
							if (wpp_code.equals("wm")) {
								pump_check = false;
							}
							break;
						} else {
							if (wpp_code.equals("wm")) {
								pump_check = true;
							}
						}
					}
				}
				if (wpp_code.equals("wm") && !wm_pump.equals("0") && !hasZero) {
					HashMap<String, Object> pumpMap = new HashMap<>();
					pumpMap.put("pump_idx", wm_pump);
					pumpMap.put("startDate", ts);
					Set<Integer> freqSize = drvnMapper.wmInverterPumpFreqCheck(pumpMap);
					if (freqSize.size() != 1) {
						hasZero = true;
						pump_check = false;
					} else if (wm_pump != null && pump_freq != null) {
						freqMap = new HashMap<>();
						freqMap.put(wm_pump, pump_freq);
					}
				} else if (wpp_code.equals("ba") && pump_grp == 2) {
					HashMap<String, Object> pumpMap = new HashMap<>();
					pumpMap.put("nowDate", ts);
					pumpMap.put("interval", 20);
					pumpMap.put("limit", 15);
					pumpMap.put("pump_grp", pump_grp);
					pumpMap.put("pump_idx", 7);
					Set<Integer> size2Pump1st = drvnMapper.inverterPumpFreqCheck(pumpMap);

					if (size2Pump1st.size() != 1) {
						hasZero = true;
					}
					Double agoJusanFreq = agoFreqMap.get("7");

					if (agoJusanFreq <= 50.0) {
						hasZero = true;
					}
				}
				loadCheckLog.append("  - Final hasZero status: " + hasZero + "#");

				if (hasZero) {
					loadCheckLog.append("💡 Conflict detected. Reverting to previous combination: " + strList + "#");

					if (wpp_code.equals("wm")) {
						freqIdx = wm_pump;

					}
					returnComb = strList;
					freqMap = new HashMap<>();
					if (beforeFreqMap != null && !beforeFreqMap.isEmpty()) {
						freqMap = beforeFreqMap;
					}


				}
				loadCheckLog.append("💡 Final returnComb: " + returnComb + "#");

				if (wpp_code.equals("wm")) {
					int hour = dateTime.getHour();

					if (!wm_pump.equals(freqIdx) || pump_freq == 0) {
						pump_freq = 60.0;
					} else if (hour < 22 && hour >= 7 && (hour < 11 || hour >= 19)) {
						pump_freq = 60.0;
					}


					Integer idxInt = Integer.valueOf(freqIdx);
					for (HashMap<String, Object> map : filteredList) {
						Integer pumpIdx = (Integer) map.get("PUMP_IDX");
						if (pumpIdx == idxInt) {
							map.put("PUMP_TYP", 2);
						} else {
							map.put("PUMP_TYP", 1);
						}

					}
				}
			}
		} else if (beforePumpUse == null) {
			//직전 예측 펌프조합에 실행 펌프가 없을 경우 예정 펌프 가동시간 검사
			boolean hasZero = false;
			if (!returnComb.isEmpty()) {
				for (String pump : returnComb) {
					if (pump.isEmpty()) {
						break;
					}
					int pump_idx = Integer.parseInt(pump);
					HashMap<String, Object> pumpMap = new HashMap<>();
					pumpMap.put("pump_idx", pump_idx);
					pumpMap.put("startDate", ts);
					pumpMap.put("local", wpp_code);


					List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
					hasZero = pumpUseList.contains(1);
					if (hasZero) {
						break;
					}
				}
			}
			if (wpp_code.equals("ba") && (pump_grp == 4 || pump_grp == 5)) {
				// 부안은 직전 조합이 꺼져있으면 꺼져 있게 유지
				// 단 조건에 따라 returnComb 가 비어있지 않고 hasZero가 true 가 아니면은

				if (!returnComb.isEmpty() && !hasZero) {
					hasZero = false;
				} else {
					hasZero = true;
				}
			}
			if (wpp_code.equals("gr") && pump_grp == 3) {
				if (!returnComb.isEmpty() && !hasZero) {
					hasZero = false;
				} else {
					hasZero = true;
				}
			}
			if (hasZero) {

				returnComb = new ArrayList<>();
				freqMap = new HashMap<>();
			}
		}

		if (wpp_code.equals("gr") && pump_grp == 2) {
			returnComb = getPumpCombination(2, 1, 1);

			if (collectData.get(closestPointIndex).containsKey("freq")) {
				freqMap = new HashMap<>();

				// freqSubMap을 먼저 꺼냄
				@SuppressWarnings("unchecked")
				HashMap<String, Double> freqSubMap = (HashMap<String, Double>) collectData.get(closestPointIndex).get("freq");

				// 예: 첫 번째 값만 가져오기
				double freq = freqSubMap.values().iterator().next();

				// 필요한 key를 가져와서 map에 넣기
				freqMap.put(getPumpCombination(2, 1, 1).get(0), freq);
			}
			int hour = dateTime.getHour();
			int minute = dateTime.getMinute();
			DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
			int week = dayOfWeek.getValue();
			int month = dateTime.getMonthValue();
			String load = reduceMap.get(month).get(hour);
			HolidayChecker holidayChecker = new HolidayChecker();
			Boolean passDayBool = holidayChecker.isPassDay(ts);
			if (week == 7 || passDayBool) {
				load = "L";
			} else if (week == 6) {
				if (load.equals("H")) {
					load = "M";
				}
			}


			boolean loadL = (load.equals("L") && (hour >= 22 || hour <= 6));
			HashMap<String, Object> combParam = new HashMap<>();

			combParam.put("nowDate", ts);
			combParam.put("pumpGrp", pump_grp);


			if (loadL) {
				//예측으로 변경
				String loadCheck = getLoadCheck(ts, load, pump_grp);

				if (load.equals("L")) {
					loadCheck = getLowLoadLevelCheck(ts, pump_grp);
				}

				if (hour == 22 && minute == 0) {
					if (loadCheck.equals("+")) {
						pressure = 7.3;
					} else {
						pressure = 7.2;
					}
				} else if (hour >= 22) {
					//22시 이후 0시 전까지 직전 압력 유지
					combParam.put("interval", 30);
					combParam.put("limit", 1);
					List<Double> agoPressureList = drvnMapper.selectPumpCombPressure(combParam);
					if (!agoPressureList.isEmpty()) {
						pressure = agoPressureList.get(0);
					} else {
						pressure = 7.2;  // 기본값 설정
					}

				} else {
					combParam.put("interval", 130);
					combParam.put("limit", 120);
					List<Double> agoPressureList = drvnMapper.selectPumpCombPressure(combParam);
					Set<Double> setAgoPressure = new HashSet<>(agoPressureList);
					if (setAgoPressure.size() == 1) {
						// 120분 동일 압력 유지 O
						Double agoPressure = setAgoPressure.iterator().next(); // 첫 번째 요소 가져오기
						if (loadCheck.equals("+")) {
							pressure = agoPressure;
							pressure += 0.1;
						} else if (loadCheck.equals("-")) {
							pressure = agoPressure;
							pressure -= 0.1;
						} else {
							pressure = agoPressure;
						}
						//pressure이 7.5을 초과하거나 7.2미만의 값일경우 직전 값 유지
						if (pressure > 7.5) {
							pressure = 7.5;
						} else if (pressure < 7.2) {
							pressure = 7.2;
						}
					} else {

						// 120분 동일 압력 유지 X
						//22시 이후 0시 전까지 직전 압력 유지
						combParam.put("interval", 30);
						combParam.put("limit", 1);
						List<Double> lastPressureList = drvnMapper.selectPumpCombPressure(combParam);
						if (!lastPressureList.isEmpty()) {
							pressure = lastPressureList.get(0);
						} else {
							pressure = 7.2;  // 기본값 설정
						}
					}
				}
			} else {
				HashMap<String, Object> waterLevelParam = new HashMap<>();
				waterLevelParam.put("nowDateTime", ts);
				waterLevelParam.put("tagname", "780-344-LEI-8012");
				Double dasanSandanBaesuji = drvnMapper.selectRawData(waterLevelParam);
				if (dasanSandanBaesuji <= 2.4) {
					pressure += 0.1;
				}
				if (pressure > 7.5) {
					pressure = 7.5;
				}
			}
		}

		if (wpp_code.equals("ba") && ago_pump_use) {
			returnComb = agoComb;
			freqMap = agoFreqMap;
		}

		/**
		 * 버튼 감지
		 * 조회가 될시 해당 조합으로 강제 변경 및 경부하 최대부하 막기
		 */
		boolean manualOper = true;
		if (wpp_code.equals("ba")) {
			HashMap<String, Object> manualOperLogParam = new HashMap<>();
			manualOperLogParam.put("nowDate", ts);
			manualOperLogParam.put("local", wpp_code);
			manualOperLogParam.put("pump_grp", pump_grp);
			HashMap<String, String> checkManualOperLogPump = drvnMapper.checkManualOperLogPump(manualOperLogParam);

			if (checkManualOperLogPump != null && !checkManualOperLogPump.isEmpty()) {
				manualOper = false;
				String logDate = checkManualOperLogPump.get("RGSTR_TIME");
				String newPumpComb = checkManualOperLogPump.get("NewPumpComb");
				String newPumpFreq = checkManualOperLogPump.get("NewPumpFreq");
				if (newPumpComb != null && !newPumpComb.trim().isEmpty()) {
					String[] strArray = newPumpComb.split(",");
					List<String> strList = Arrays.stream(strArray)
							.map(String::trim)
							.collect(Collectors.toList());
					List<String> combIvtPump = new ArrayList<>();
					for (String pump : strList) {
						if (typeMap.containsKey(pump)) {
							if (typeMap.get(pump) == 2) {
								combIvtPump.add(pump);
							}
						}
					}

					HashMap<String, Double> beforeFreqMap = new HashMap<>();
					if (newPumpFreq != null && !newPumpFreq.trim().isEmpty() && !combIvtPump.isEmpty()) {

						String[] freqArr = newPumpFreq.split(",");
						List<String> freqList = Arrays.stream(freqArr)
								.map(String::trim)
								.collect(Collectors.toList());
						for (int i = 0; i < combIvtPump.size(); i++) {
							String pump_idx = combIvtPump.get(i);
							Double freqDb = 0.0;

							String freqStr = freqList.get(i);
							freqDb = Double.valueOf(freqStr);
							beforeFreqMap.put(pump_idx, freqDb);

						}

					}
					if (pump_grp == 4) {
						if (beforeFreqMap != null && !beforeFreqMap.isEmpty()) {
							Double operFreq = beforeFreqMap.get("16");


							if (operFreq != null && operFreq.intValue() == 45) {
								if (freqMap != null && !freqMap.isEmpty() && freqMap.containsKey("16")) {
									returnComb = strList;
									freqMap = beforeFreqMap;
								}
							} else if (operFreq.intValue() == 46) {
								if (freqMap != null && !freqMap.isEmpty() && freqMap.containsKey("16")) {
									Double freq = freqMap.get("16");
									if (freq != null && freq.intValue() != 52) {
										freqMap = beforeFreqMap;
									}

								}
							} else {
								returnComb = strList;
								freqMap = beforeFreqMap;
							}
						}
					} else {
						returnComb = strList;
						freqMap = beforeFreqMap;
					}

				} else {
					returnComb = new ArrayList<>();
					freqMap = new HashMap<>();
				}
			}
		} else if (wpp_code.equals("gr")) {
			HashMap<String, Object> manualOperLogParam = new HashMap<>();
			manualOperLogParam.put("nowDate", ts);
			manualOperLogParam.put("local", wpp_code);
			manualOperLogParam.put("pump_grp", pump_grp);
			HashMap<String, String> checkManualOperLogPump = drvnMapper.checkManualOperLogPump(manualOperLogParam);

			if (checkManualOperLogPump != null && !checkManualOperLogPump.isEmpty()) {
				manualOper = false;
				String logDate = checkManualOperLogPump.get("RGSTR_TIME");
				String newPumpComb = checkManualOperLogPump.get("NewPumpComb");
				String newPumpFreq = checkManualOperLogPump.get("NewPumpFreq");
				if (newPumpComb != null && !newPumpComb.trim().isEmpty()) {
					String[] strArray = newPumpComb.split(",");
					List<String> strList = Arrays.stream(strArray)
							.map(String::trim)
							.collect(Collectors.toList());
					List<String> combIvtPump = new ArrayList<>();
					for (String pump : strList) {
						if (typeMap.containsKey(pump)) {
							if (typeMap.get(pump) == 2) {
								combIvtPump.add(pump);
							}
						}
					}

					HashMap<String, Double> beforeFreqMap = new HashMap<>();
					if (newPumpFreq != null && !newPumpFreq.trim().isEmpty() && !combIvtPump.isEmpty()) {

						String[] freqArr = newPumpFreq.split(",");
						List<String> freqList = Arrays.stream(freqArr)
								.map(String::trim)
								.collect(Collectors.toList());
						for (int i = 0; i < combIvtPump.size(); i++) {
							String pump_idx = combIvtPump.get(i);
							Double freqDb = 0.0;

							String freqStr = freqList.get(i);
							freqDb = Double.valueOf(freqStr);
							beforeFreqMap.put(pump_idx, freqDb);

						}

					}
					if (pump_grp == 1) {
						returnComb = strList;
						freqMap = beforeFreqMap;
					}


				}
			}
		}


		//고령정수장 강제 조절
		if (wpp_code.equals("gr") && pump_grp == 1) {
			if (returnComb.size() > 3) {
				returnComb = getPumpCombination(pump_grp, 3, 1);
				freqMap.put("4", 60.0);
			} else if (returnComb.isEmpty()) {
				returnComb = getPumpCombination(pump_grp, 2, 1);
				freqMap.put("4", 60.0);
			}
		}



		// idx를 만들기 위한 formater 및 idx 생성

		DateTimeFormatter idxFormatter = DateTimeFormatter.ofPattern("yyMMddHHmm");

		LocalDateTime rgstDate = LocalDateTime.parse(Objects.requireNonNull(ts), formatter);
		LocalTime rgstTime = rgstDate.toLocalTime();
		String idxRgstTime = String.valueOf(rgstTime.getHour()) + rgstTime.getMinute();
		String preDateTime = rgstDate.format(idxFormatter);
		String insertIdx = ":" + preDateTime + "-" + idxRgstTime;


		//전력구하기
		HashMap<Integer, HashMap<String, Double>> grpFlowPressure = new HashMap<>();
		HashMap<String, Double> grpFlowPressureMap = new HashMap<>();
		HashMap<Integer, Double> grpPrdctPwr = new HashMap<>();

		if (wpp_code.equals("gs")) {
			DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
			int week = dayOfWeek.getValue();
			int month = dateTime.getMonthValue();
			int hour = dateTime.getHour();
			String load = reduceMap.get(month).get(hour);
			HolidayChecker holidayChecker = new HolidayChecker();
			boolean passDayBool = holidayChecker.isPassDay(ts);
			if (week == 7 || passDayBool) {
				load = "L";
			} else if (week == 6) {
				if (load.equals("H")) {
					load = "M";
				}
			}
			if (load.equals("H") || (week <= 5 && (hour >= 10 && hour <= 17)) || load.equals("M")) {
				if (returnComb.size() >= 4) {
					returnComb = findValidPumpComb(collectData, returnComb);

					if (returnComb.isEmpty()) {
						returnComb = (List<String>) collectData.get(0).get("pumpComb");
					}
				}
			}
			if(wpp_code.equals("gs")){
				if (returnComb == null || returnComb.isEmpty()) {
					System.out.println("DEBUG: GS 로직 - returnComb이 비어 있어 agoComb로 대체됩니다. agoComb: " + agoComb);
					loadCheckLog.append("💡 DEBUG: GS 로직 - returnComb이 비어 있어 agoComb로 대체됩니다. agoComb: " + agoComb + "#");
					returnComb = agoComb;
				}
			}
			loadCheckLog.append("💡 Final returnComb: " + returnComb + "#");
			HashMap<String, Object> param = new HashMap<>();
			param.put("nowDateTime", ts);


			Set<Integer> pumpGrpSet = new LinkedHashSet<>(pumpDstrbIdMap.keySet());

			LinkedHashMap<String, List<HashMap<String, Object>>> dataCtrMap = new LinkedHashMap<>();

//			System.out.println("comb :" + returnComb);
			for (Integer id : pumpGrpSet) {
				HashMap<String, String> ditrbMap = pumpDstrbIdMap.get(id);

				String flowId = ditrbMap.get("flow");
				String pressureId = ditrbMap.get("pressure");
				param.put("DSTRB_ID", flowId);

				List<HashMap<String, Object>> flowGs = drvnMapper.prdctFlowPressure(param);

				param.put("DSTRB_ID", pressureId);
				List<HashMap<String, Object>> pressureGS = drvnMapper.prdctFlowPressure(param);


				if (!flowGs.isEmpty() || !pressureGS.isEmpty()) {

					float flowStr = (float) (flowGs.get(0)).get("value");
					float pressureStr = (float) (pressureGS.get(0)).get("value");
					Double flowDb = (double) flowStr;
					Double pressureDb = (double) pressureStr;
					grpFlowPressureMap.put("flow", flowDb);
					grpFlowPressureMap.put("pressure", pressureDb);
					grpFlowPressure.put(id, grpFlowPressureMap);
				}
				List<String> grpComb = new ArrayList<>();
				for (String pumpStr : returnComb) {
					int pump = Integer.parseInt(pumpStr);
					if (id == 1) {
						if (pump <= 7) {
							grpComb.add(pumpStr);
						}
					} else {
						if (pump > 7) {
							grpComb.add(pumpStr);
						}
					}
				}
				HashMap<Integer, Double> gsPrdctPwr = allPumpGrpPwrPrdct(grpComb, grpFlowPressure, freqMap);
				grpPrdctPwr.put(id, gsPrdctPwr.get(id));
			}

		} else {
			grpFlowPressureMap.put("flow", flow);
			grpFlowPressureMap.put("pressure", pressure);
			grpFlowPressure.put(pump_grp, grpFlowPressureMap);
			grpPrdctPwr = allPumpGrpPwrPrdct(returnComb, grpFlowPressure, freqMap);

		}


		for (HashMap<String, Object> map : filteredList) {

			int map_grp = (int) map.get("PUMP_GRP");
			int idx_integer = (int) map.get("PUMP_IDX");
			double pwrPrdct = grpPrdctPwr.get(map_grp);
			String pump_idx = String.valueOf(idx_integer);
			int pump_typ = (int) map.get("PUMP_TYP");
			map.put("freq", 0);
			//인버터 타입일 경우
			if (pump_typ == 2) {
				//조합식 결과의 주파수 map 검사
				if (freqMap != null) {
					// 주파수 map에 포함되는 주파수 값이 있는지 검사
					if (wpp_code.equals("wm")) {
						map.put("freq", pump_freq);
					} else if (freqMap.containsKey(pump_idx)) {
						Double freq = freqMap.get(pump_idx);
						map.put("freq", freq);
					} else {
						map.put("freq", 0);
					}
				}
			}
			map.put("flow", flow);
			map.put("pressure", pressure);
			map.put("opt_idx", optIdxTag + insertIdx);
			map.put("pwrPrdct", pwrPrdct);
			map.put("ts", ts);
			if (returnComb.contains(pump_idx)) {
				map.put("pump_yn", 1);
			} else {
				map.put("pump_yn", 0);
			}
			if (wpp_code.equals("gu")) {
				map.put("chng_stts", changeStatus);
			}

			drvnMapper.insertDrvnPumpYnData(map);
		}


		DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
		int week = dayOfWeek.getValue();
		int month = dateTime.getMonthValue();
		int hour = dateTime.getHour();

		int minute = dateTime.getMinute();
		//버튼 시간에 따라 동작 구분
		if (manualOper) {
			String load = reduceMap.get(month).get(hour);
			HolidayChecker holidayChecker = new HolidayChecker();
			Boolean passDayBool = holidayChecker.isPassDay(ts);
			if (week == 7 || passDayBool) {
				load = "L";
			} else if (week == 6) {
				if (load.equals("H")) {
					load = "M";
				}
			}
			int endLoadHour = 6;
			if (wpp_code.equals("wm")) {
				if (passDayBool || week >= 6) {
					endLoadHour = 7;
				}
			}
			boolean loadL = (load.equals("L") && (hour >= 22 || hour <= endLoadHour));

			if (wpp_code.equals("wm")) {
				if (pump_check) {
					boolean loadH = (!load.equals("L")) && !passDayBool && week <= 5 && (hour >= 11 && hour <= 18);
					DateTimeFormatter formatterOnlyDate = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
					// 날짜 치환
					LocalDateTime wmTsDate = LocalDateTime.parse(ts, formatterOnlyDate);
					// 시간 부분 22:00 수동 설정

					boolean wmInquiry = false;

					if (hour < 22) {
						wmTsDate = wmTsDate.minusDays(1);
					}
					wmTsDate = wmTsDate.withHour(22).withMinute(0);

					// 다시 포맷팅하여 문자열로 변환
					String wmTargetTs = wmTsDate.format(formatterOnlyDate);


					HashMap<String, Object> curPump = curPumpCheck(ts, pump_grp, typeMap, false);
					List<String> wmCurPump = new ArrayList<>();
					HashMap<String, Double> wmCurFreq = new HashMap<>();
					if (curPump != null && !curPump.isEmpty()) {
						if (curPump.containsKey("comb")) {
							wmCurPump = (List<String>) curPump.get("comb");
						}
						if (curPump.containsKey("freq")) {
							wmCurFreq = (HashMap<String, Double>) curPump.get("freq");
						}
					}

					HashMap<String, Object> targetCurPump = curPumpCheck(wmTargetTs, pump_grp, typeMap, false);
					List<String> wmTargetCurPump = new ArrayList<>();
					HashMap<String, Double> wmTargetCurFreq = new HashMap<>();
					if (targetCurPump != null && !targetCurPump.isEmpty()) {
						if (targetCurPump.containsKey("comb")) {
							wmTargetCurPump = (List<String>) targetCurPump.get("comb");
						}
						if (targetCurPump.containsKey("freq")) {
							wmTargetCurFreq = (HashMap<String, Double>) targetCurPump.get("freq");
						}
					}
					HashMap<String, Object> prePump = curPumpCheck(ts, pump_grp, typeMap, true);
					List<String> wmPrePump = new ArrayList<>();
					HashMap<String, Double> wmPreFreq = new HashMap<>();
					if (prePump != null && !prePump.isEmpty()) {
						if (prePump.containsKey("comb")) {
							wmPrePump = (List<String>) prePump.get("comb");
						}
						if (prePump.containsKey("freq")) {
							wmPreFreq = (HashMap<String, Double>) prePump.get("freq");
						}
					}

					if (wmPrePump == null || wmPrePump.isEmpty()) {
						int mi = 1;
						for (int i = 0; i < 10; i++) {
							mi = mi + i;
							LocalDateTime minusDateTime = dateTime.minusMinutes(mi);
							String minusTime = minusDateTime.format(formatter);
							prePump = curPumpCheck(minusTime, pump_grp, typeMap, true);
							if (prePump != null && !prePump.isEmpty()) {
								if (prePump.containsKey("comb")) {
									wmPrePump = (List<String>) prePump.get("comb");
								}
								if (prePump.containsKey("freq")) {
									wmPreFreq = (HashMap<String, Double>) prePump.get("freq");
								}
							}
							if (wmPrePump != null && !wmPrePump.isEmpty()) {
								break;
							}
						}
					}
					if (wmPrePump.isEmpty() || wmPrePump == null || wmTargetCurPump.isEmpty() || wmTargetCurPump == null || wmCurPump.isEmpty() || wmCurPump == null) {
						wmInquiry = true;
					}
					int level = 0;
					String loadCheck = null;
					if (!wmInquiry) {
						if (loadH) {

							if (hour == 11) {
								level = 300;
							} else if (hour >= 12 && hour <= 14) {
								level = 300;
							} else if (hour >= 15 && hour <= 18) {
								level = 300;
							}

							loadCheck = getHighLoadLevelCheck(ts, level);


						} else if (loadL) {

							//해당 경부하 시간 22시 00분 조합이 2대 이상일시
							if (!wmTargetCurPump.isEmpty() && wmTargetCurPump.size() >= 2) {
								//22시부터 02시까지는 직전 실측 조합 유지
								if (hour >= 22 || hour < 2) {

									loadCheck = "wmCurUsing";

								} else if (hour <= 3 && minute == 0) {
									HashMap<String, Object> levelMap = new HashMap<>();
									levelMap.put("nowDateTime", ts);
									levelMap.put("DSTRB_ID", "565-340-SWI-8101");
									List<HashMap<String, Object>> nowLevelList = drvnMapper.curFlowPressure(levelMap);
									String nowLevelStr = (String) nowLevelList.get(0).get("value");
									double nowLevel = Double.parseDouble(nowLevelStr);
									//송수터널 수위 330 미만일시 직전 2대 이상조합 유지
									if (nowLevel < 330) {
										loadCheck = "wmCurUsing";
									} else {
										//아닐시 한대 감소(단 직전 조합과 기준 조합의 대수가 차이나면 조합 유지)
										if (wmTargetCurPump.size() != wmCurPump.size()) {
											loadCheck = "wmCurUsing";
										} else {
											loadCheck = "wm";
										}

									}

								} else {
									if (wmCurPump.size() >= 2) {
										loadCheck = "wmCurUsing";
									} else {
										loadCheck = getLowLoadLevelCheck(ts, pump_grp);
									}
								}
							} else {
								loadCheck = getLowLoadLevelCheck(ts, pump_grp);
							}
						}

						if (loadCheck != null && !loadCheck.equals("=")) {

							Double max_freq = 60.0;
							Double min_freq = 56.0;
							if (loadCheck.equals("+")) {
								if (pump_freq + 1 < max_freq) {
									pump_freq += 1.0;
								} else {
									pump_freq = max_freq;
								}
							} else {
								if (pump_freq - 1 >= min_freq) {
									pump_freq -= 1.0;
								} else {
									pump_freq = min_freq;
								}
							}


							freqMap = new HashMap<>();
							if (!freqIdx.equals("0")) {
								freqMap.put(freqIdx, pump_freq);
							}
							if (loadCheck != null) {

								if (loadCheck.equals("wm")) {
									int nowCombSize = returnComb.size();
									if (nowCombSize == 3) {
										returnComb = new ArrayList<>();
										returnComb.add("3");
										returnComb.add("4");
										for (HashMap<String, Object> map : filteredList) {
											Integer pumpIdx = (Integer) map.get("PUMP_IDX");
											if (pumpIdx == 4) {
												map.put("PUMP_TYP", 2);
											} else {
												map.put("PUMP_TYP", 1);
											}
										}
										freqMap = new HashMap<>();
										freqMap.put("4", 60.0);
									} else if (nowCombSize == 2) {
										returnComb = new ArrayList<>();
										returnComb.add("3");
										for (HashMap<String, Object> map : filteredList) {
											map.put("PUMP_TYP", 1);
										}
										freqMap = new HashMap<>();
									}
								} else if (loadCheck.equals("wmCurUsing")) {
									freqMap = wmCurFreq;
									returnComb = wmCurPump;
								} else if (loadCheck.equals("wmPreUsing")) {

									freqMap = wmPreFreq;
									returnComb = wmPrePump;
								} else if (loadCheck.equals("wmMaxOper")) {
									int wmPump = 1;
									returnComb = new ArrayList<>();
									freqMap = new HashMap<>();
									if (wm_day % 2 == 0) {
										wmPump = 2;
										returnComb.add("2");
										freqMap.put("2", 60.0);
									} else {
										returnComb.add("1");
										freqMap.put("1", 60.0);
									}
									returnComb.add("3");
									returnComb.add("4");
									for (HashMap<String, Object> map : filteredList) {
										Integer pumpIdx = (Integer) map.get("PUMP_IDX");
										if (pumpIdx == wmPump) {
											map.put("PUMP_TYP", 2);
										} else {
											map.put("PUMP_TYP", 1);
										}
									}


								}


								List<String> finalReturnComb = new ArrayList<>(returnComb);
								List<String> endPump = wmPrePump.stream()
										.filter(item -> !finalReturnComb.contains(item))
										.collect(Collectors.toList());


								List<String> finalStrList = wmPrePump;
								//실측 조합 대비 시작 예정 펌프
								List<String> startPump = finalReturnComb.stream()
										.filter(item -> !finalStrList.contains(item))
										.collect(Collectors.toList());
								boolean hasZero = false;

								if (!startPump.isEmpty()) {
									for (String pump : startPump) {
										if (pump.isEmpty()) {
											break;
										}
										int pump_idx = Integer.parseInt(pump);
										HashMap<String, Object> pumpMap = new HashMap<>();
										pumpMap.put("pump_idx", pump_idx);
										pumpMap.put("startDate", ts);
										pumpMap.put("local", wpp_code);


										List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
										hasZero = pumpUseList.contains(1);

										if (hasZero) {
											break;
										}
									}
								}
								if (!endPump.isEmpty() && !hasZero) {
									for (String pump : endPump) {
										int pump_idx = Integer.parseInt(pump);
										HashMap<String, Object> pumpMap = new HashMap<>();
										pumpMap.put("pump_idx", pump_idx);
										pumpMap.put("startDate", ts);
										pumpMap.put("local", wpp_code);

										List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
										hasZero = pumpUseList.contains(0);

										if (hasZero) {
											break;
										}
									}
								}
								if ((hour != 22 && minute != 0) && hasZero) {
									//운문 2시간 유지 X
									returnComb = wmPrePump;
									freqMap = wmPreFreq;
								}

							}


							HashMap<Integer, Double> grpInQuiryPrdctPwr = allPumpGrpPwrPrdct(returnComb, grpFlowPressure, freqMap);
							String flow_ctr;
							if (loadCheck.equals("+")) {
								flow_ctr = "INC";
							} else if (loadCheck.equals("-")) {
								flow_ctr = "DEC";
							} else {
								flow_ctr = "KEP";
							}
							for (HashMap<String, Object> map : filteredList) {
								int idx_integer = (int) map.get("PUMP_IDX");
								double pwrPrdct = grpInQuiryPrdctPwr.get(pump_grp);
								String pump_idx = String.valueOf(idx_integer);
								map.put("flow", flow);
								map.put("pressure", pressure);
								map.put("opt_idx", optIdxTag + insertIdx);
								map.put("pwrPrdct", pwrPrdct);
								map.put("RATE_CTGRY", load);
								map.put("FLOW_CTR", flow_ctr);
								map.put("ts", ts);
								int pump_typ = (int) map.get("PUMP_TYP");
								//인버터 타입일 경우
								map.put("freq", 0);
								if (pump_typ == 2) {
									//조합식 결과의 주파수 map 검사
									if (freqMap != null) {
										// 주파수 map에 포함되는 주파수 값이 있는지 검사
										if (wpp_code.equals("wm")) {
											map.put("freq", pump_freq);
										} else if (freqMap.containsKey(pump_idx)) {
											Double freq = freqMap.get(pump_idx);
											map.put("freq", freq);
										} else {
											map.put("freq", 0);
										}
									}
								}
								if (returnComb.contains(pump_idx)) {
									map.put("pump_yn", 1);
								} else {
									map.put("pump_yn", 0);
								}


								drvnMapper.insertInQuiryPumpYnData(map);
							}
						}
					}
				}
			} else if (wpp_code.equals("ba") && pump_grp != 2 && (load.equals("L") || load.equals("H"))) {
				boolean inquiry = false;
				if (pump_grp == 1) {
					if (loadL) {
						/**
						 * 00:00까지는 현 상태 유지(공통로직의 내용을 우선하여 적용)
						 * 흡수정의 수위가 2.3m 이하
						 * 3대 운영(분기유량 1200톤 이상이면 4,5,6/ 1200톤 미만이면 2,4,6,)
						 * 수위 3m 도달시 2대로 상태 변경(2대 조합 생성 후 경부하시간 insert x)
						 */
						returnComb = new ArrayList<>();
						freqMap = new HashMap<>();


						List<String> leiList = new ArrayList<>();
						leiList.add("892-480-LEI-8000");
						leiList.add("892-480-LEI-8001");
						HashMap<String, Object> rawParam = new HashMap<>();
						rawParam.put("nowDateTime", ts);
						boolean using_pump = false;
						HashMap<String, Object> inOutFriParam = new HashMap<>();
						inOutFriParam.put("nowDateTime", ts);
						inOutFriParam.put("tagname", "892-480-FRI-8004");
						Double inFri = drvnMapper.select5MinuteAvgRawData(inOutFriParam);
						inOutFriParam.put("tagname", "892-480-FRI-8000");
						Double outFri = drvnMapper.select5MinuteAvgRawData(inOutFriParam);
						if (hour == 0 && minute == 0) {
							ba_bool = false;


							for (String lei : leiList) {
								rawParam.put("tagname", lei);
								Double leiDb = drvnMapper.selectRawData(rawParam);
								if (leiDb != null) {
									if (leiDb <= 2.3 && leiDb >= 0.3) {
										ba_bool = true;
										break;
									}
								}
							}
							if (ba_bool) {
								if (agoComb.size() == 2) {
									inquiry = true;
									Double friSum = 0.0;
									List<String> friList = new ArrayList<>();
									friList.add("892-360-FRI-8901");
									friList.add("892-360-FRI-8400");
									friList.add("892-360-FRI-8951");
									for (String fri : friList) {
										rawParam.put("tagname", fri);
										Double friDb = drvnMapper.select5MinuteAvgRawData(rawParam);
										if (friDb != null) {
											friSum += friDb;
										}
									}

									if (friSum >= 1300.0) {
										returnComb.add("4");
										returnComb.add("5");
										returnComb.add("6");
									} else {
										returnComb.add("2");
										returnComb.add("4");
										returnComb.add("6");
									}
									freqMap = new HashMap<>();
									freqMap.put("4", 60.0);
								}

							}
						} else if (hour >= 0 && hour <= 6) {
							if (agoComb.size() == 3) {
								boolean levelCheck = false;
								for (String lei : leiList) {
									rawParam.put("tagname", lei);
									Double leiDb = drvnMapper.selectRawData(rawParam);
									if (leiDb != null) {
										if (leiDb >= 2.8) {
											levelCheck = true;
											break;
										}
									}
								}

								if (levelCheck) {
									inquiry = true;
									returnComb.add("4");
									returnComb.add("6");
									freqMap = new HashMap<>();
									freqMap.put("4", 60.0);
								}
							}
						}
					}
				} else if (pump_grp == 3) {
					/**
					 * 아산배수지 최소:1.9  최대: 3.5
					 * 무장배수지: 최소:2.1 최대: 3.5
					 * 해리배수지: 최소:2.3 최대: 3.6
					 * 아산 : 892-481-LEI-8880
					 * 무장(배) : 892-481-LEI-8500
					 * 해리(배) : 892-481-LEI-8450
					 * 경부하 로직은 최대 값을 만수위로 하여
					 * 02시에 수위 도달 시간을 체크, 07시에 최대 수위 도달 못할것 같으면,
					 *
					 * 3대 운영
					 * 도달 하면 2대운영
					 * -> 이 판단을 2시간마다 체크
					 */
					if (loadL) {
						boolean sinlimLeiBool = false;
						HashMap<String, Object> rawParam = new HashMap<>();
						rawParam.put("nowDateTime", ts);

						List<String> sinlimLeiList = new ArrayList<>();

						sinlimLeiList.add("892-481-LEI-8001");
						sinlimLeiList.add("892-480-LEI-8000");
						for (String lei : sinlimLeiList) {
							rawParam.put("tagname", lei);
							Double leiDb = drvnMapper.selectRawData(rawParam);
							if (leiDb != null) {
								if (leiDb <= 1.8) {
									sinlimLeiBool = true;
								}
							}
						}
						if (hour >= 2 && hour < 22) {
							String returnCheck = "=";
							boolean using_pump = false;
							inquiry = true;
							if (hour % 2 == 0 && minute == 0) {
								HashMap<String, Double> levelTagMap = new HashMap<>();
								levelTagMap.put("892-481-LEI-8880", 3.5);
								levelTagMap.put("892-481-LEI-8500", 3.5);
								levelTagMap.put("892-481-LEI-8450", 3.6);
								Set<String> levelSet = levelTagMap.keySet();
								for (String levelTag : levelSet) {
									LocalDateTime minusTime = dateTime.minusMinutes(5);
									String minusTs = minusTime.format(formatter);
									double optMinute = 300;

									int nowScore = (hour * 60) + minute;


									String level_tag = levelTag;
									double max_level = levelTagMap.get(levelTag);
									HashMap<String, Object> levelMap = new HashMap<>();
									levelMap.put("nowDateTime", ts);
									levelMap.put("DSTRB_ID", level_tag);
									List<HashMap<String, Object>> nowLevelList = drvnMapper.curFlowPressure(levelMap);

									String nowLevelStr = (String) nowLevelList.get(0).get("value");
									String nowLevelTs = (String) nowLevelList.get(0).get("ts");

									double nowLevel = Double.parseDouble(nowLevelStr);
									levelMap.put("nowDateTime", minusTs);
									List<HashMap<String, Object>> minusLevelList = drvnMapper.curFlowPressure(levelMap);

									String minusLevelStr = (String) minusLevelList.get(0).get("value");
									String minusLevelTs = (String) minusLevelList.get(0).get("ts");
									double minusLevel = Double.parseDouble(minusLevelStr);

									if (nowLevel == 0.0 || minusLevel == 0.0) {
										returnCheck = "+";
										break;
									}
									//현재 수위가 목표수위보다 높을경우 -1(전시간 5분전 수위도 혹시모르니 같이 뺴줌)
									if (nowLevel > max_level && minusLevel > max_level) {
										nowLevel -= 1;
										minusLevel -= 1;
									}

									//수위 차이가 음수 일 시 바로 추가운영으로 조건 변경
									//수위차이 0일시 해결
									double wtrLvlDiff = nowLevel - minusLevel;

									if (wtrLvlDiff == 0) {


										boolean pass = true;
										int forMinute = 5;
										while (pass && nowScore > 0) {

											nowScore -= 5;
											LocalDateTime afterTime = dateTime.minusMinutes(forMinute);
											LocalDateTime afterMinusTime = minusTime.minusMinutes(forMinute);
											String afterTs = afterTime.format(formatter);
											String afterMinusTs = afterMinusTime.format(formatter);

											HashMap<String, Object> afterMap = new HashMap<>();
											afterMap.put("nowDateTime", afterTs);
											afterMap.put("DSTRB_ID", level_tag);
											List<HashMap<String, Object>> afterNowList = drvnMapper.curFlowPressure(afterMap);
											String afterNowStr = (String) afterNowList.get(0).get("value");
											double afterNow = Double.parseDouble(afterNowStr);
											levelMap.put("nowDateTime", afterMinusTs);
											List<HashMap<String, Object>> afterMinusList = drvnMapper.curFlowPressure(levelMap);
											String afterMinusStr = (String) afterMinusList.get(0).get("value");
											double afterMinus = Double.parseDouble(afterMinusStr);

											if ((afterNow - afterMinus) != 0) {
												pass = false;
												nowLevel = afterNow;
												minusLevel = afterMinus;
											}
											forMinute += 5;
										}

										if (pass) {
											returnCheck = "+";
											continue;
										}
									}

									//1시간 예상 수위 증가량
									double levelPlus = (nowLevel - minusLevel) * 12;
									//목표수위와 현재수위의 차
									double optLevel = max_level - nowLevel;
									//목표수위 도달 시간
									double optLevelMinute = (optLevel / levelPlus) * 60;


									//목표시간내에 목표수위 도달 예상시간
									double totalScore = nowScore + optLevelMinute;


									if (wtrLvlDiff < 0) {

										returnCheck = "+";
										continue;
									}

									if (totalScore < optMinute) {
										returnCheck = "-";
										break;
									} else {
										returnCheck = "+";
									}
								}
							}


							if (returnCheck.equals("+") && !sinlimLeiBool) {
								returnComb = new ArrayList<>();
								returnComb.add("11");
								returnComb.add("13");
								returnComb.add("14");
							} else {
								returnComb = new ArrayList<>();
								returnComb.add("11");
								returnComb.add("14");
							}

						}
					}
				} else if (pump_grp == 4) {
					/**
					 * 무장 A 최대부하 조건(13~18)
					 * 14시에 무장배수지 수위가 2.8보다 높다면 펌프 off
					 * 892-481-LEI-8500
					 * 펌프 off 상태는 무장배수지의 수위가  18시 이전에 2.3m 아래로 떨어지면 재가동
					 */
					if (load.equals("H") && hour >= 14) {


						HashMap<String, Object> rawParam = new HashMap<>();
						rawParam.put("nowDateTime", ts);
						rawParam.put("tagname", "892-481-LEI-8500");
						Double leiDb = drvnMapper.selectRawData(rawParam);
						if (hour == 14 && minute == 0 && (agoComb != null || !agoComb.isEmpty())) {
							if (leiDb > 2.8) {
								double minLei = Double.MAX_VALUE;  // 매우 큰 값으로 초기화
								List<String> leiList = Arrays.asList("892-482-LEI-8960", "892-481-LEI-8551", "892-481-LEI-8552");

								for (String lei : leiList) {
									rawParam.put("tagname", lei);
									Double lei_daesan = drvnMapper.selectRawData(rawParam);
									if (lei_daesan != null && lei_daesan > 0.0) {  // 유효한 수치인지 확인
										if (lei_daesan < minLei) {
											minLei = lei_daesan;
										}
									}
								}

								// 최소값이 변경된 경우에만 처리
								if (minLei != Double.MAX_VALUE) {
									if (minLei >= 2.6) {
										inquiry = true;
										//종료조건 45로
										returnComb = new ArrayList<>();
										returnComb.add("16");
										freqMap.put("16", 45.0);
									}
								}


							}
						} else if (hour < 18) {
							if (leiDb <= 2.3 && agoComb.isEmpty()) {
								inquiry = true;
								freqMap = new HashMap<>();
								returnComb = new ArrayList<>();
								returnComb.add("16");

								freqMap.put("16", 46.0);
							}

						}

					}
				}

				if (inquiry) {
					HashMap<Integer, Double> grpInQuiryPrdctPwr = allPumpGrpPwrPrdct(returnComb, grpFlowPressure, freqMap);

					for (HashMap<String, Object> map : filteredList) {
						int idx_integer = (int) map.get("PUMP_IDX");
						double pwrPrdct = grpInQuiryPrdctPwr.get(pump_grp);
						String pump_idx = String.valueOf(idx_integer);
						map.put("flow", flow);
						map.put("pressure", pressure);
						map.put("opt_idx", optIdxTag + insertIdx);
						map.put("pwrPrdct", pwrPrdct);
						map.put("RATE_CTGRY", load);
						map.put("ts", ts);
						int pump_typ = (int) map.get("PUMP_TYP");
						//인버터 타입일 경우
						map.put("freq", 0);
						if (pump_typ == 2) {
							//조합식 결과의 주파수 map 검사
							if (freqMap != null) {
								// 주파수 map에 포함되는 주파수 값이 있는지 검사
								if (freqMap.containsKey(pump_idx)) {
									Double freq = freqMap.get(pump_idx);
									map.put("freq", freq);
								} else {
									map.put("freq", 0);
								}
							}
						}
						if (returnComb.contains(pump_idx)) {
							map.put("pump_yn", 1);
						} else {
							map.put("pump_yn", 0);
						}


						drvnMapper.insertInQuiryPumpYnData(map);
					}
				}
			} else if ((loadL || load.equals("H")) && !gu_bool && !gs_bool && !gr_bool) {
				if (!wpp_code.equals("gr") && !load.equals("L")) {

					List<String> inQuiryComb;

					String loadCheck;
					//예측으로 변경
					if (wpp_code.equals("gs")) {
						loadCheck = getLoadCheck(ts, load, 1);
					} else {
						loadCheck = getLoadCheck(ts, load, pump_grp);
					}


					if (load.equals("L")) {
						if (wpp_code.equals("gs")) {
							loadCheck = getLowLoadLevelCheck(ts, 1);
						} else {
							loadCheck = getLowLoadLevelCheck(ts, pump_grp);
						}

					}

					double pumpLevel = 0.0;
					double usePumpLevel;
					List<String> strList = List.of();

					String curPumpUse = null;
					String curFreqUse = null;

					if (!returnComb.isEmpty() && returnComb != null) {
						curPumpUse = String.join(",", returnComb);
					}
					if (freqMap != null && !freqMap.isEmpty()) {
						StringJoiner joiner = new StringJoiner(",");
						for (Double value : Objects.requireNonNull(freqMap).values()) {
							if (value != null) {
								String valueStr = String.valueOf(value);
								joiner.add(valueStr);
							}
						}
						curFreqUse = joiner.toString();
					}

					if (curPumpUse == null || curPumpUse.trim().isEmpty()) {
						pumpLevel = 0.0;
					} else {
						String[] strArray = curPumpUse.split(",");
						strList = Arrays.stream(strArray)
								.map(String::trim)
								.collect(Collectors.toList());
						loadCheckLog.append("직전 실측 조합 :" + strList + "#");
						List<String> combIvtPump = new ArrayList<>();
						for (String pump : strList) {
							if (typeMap.containsKey(pump)) {
								if (typeMap.get(pump) == 2) {
									combIvtPump.add(pump);
								}
							}
						}
						HashMap<String, Double> curFreqMap = new HashMap<>();
						if (curFreqUse != null && !curFreqUse.trim().isEmpty() && !combIvtPump.isEmpty()) {

							String[] freqArr = curFreqUse.split(",");
							List<String> freqList = Arrays.stream(freqArr)
									.map(String::trim)
									.collect(Collectors.toList());
							for (int i = 0; i < combIvtPump.size(); i++) {
								String idx = combIvtPump.get(i);
								Double freqDb = 0.0;

								String freqStr = freqList.get(i);
								freqDb = Double.valueOf(freqStr);
								//고령 주파수는 백분율
								if (wpp_code.equals("wm")) {
									pumpUseParam.put("pump_idx", Integer.parseInt(idx));
									Double freq = drvnMapper.getLastCurFreq(pumpUseParam);

									curFreqMap.put(idx, freq);
								} else {
									curFreqMap.put(idx, freqDb);
								}
							}
						}

						if (!strList.isEmpty()) {
							for (String pump_idx : strList) {
								if (!pump_idx.isEmpty()) {
									int idx = Integer.parseInt(pump_idx);
									double pumpVal = pumpLevelInfoMap.get(idx);
									if (typeMap.get(pump_idx) == 1) {
										pumpLevel += pumpVal;
									} else {
										if (curFreqMap != null && curFreqMap.containsKey(pump_idx)) {
											double freqVal = curFreqMap.get(pump_idx) / 60;
											pumpLevel += freqVal;
										}
									}

								}
							}
						}
					}
					int uIdx = 0;
					int cIdx = 0;

					for (HashMap<String, Object> collectDatum : collectData) {
						int idx = (int) collectDatum.get("combIdx");
						if (!pumpTypeBool) {
							double getCumpLevel = (double) collectDatum.get("pumpLevel");
							if (getCumpLevel == pumpLevel) {
								cIdx = idx;
								uIdx = idx;
							}
						} else {
							boolean condition = false;
							Double uppLev = (Double) collectDatum.get("uppLev");
							Double lowLev = (Double) collectDatum.get("lowLev");
							if (uppLev == null && lowLev == null) {
								if (pumpLevel == 0.0) {
									// 조건 1: uppLev와 lowLev가 null이고 pumpLevel이 0.0인 경우
									condition = true;
								}
							} else if (uppLev == null) {
								if (pumpLevel < lowLev) {
									// 조건 2: uppLev가 null이고 pumpLevel이 lowLev보다 작은 경우
									condition = true;
								}
							} else if (lowLev == null) {
								if (pumpLevel >= uppLev) {
									// 조건 3: lowLev가 null이고 pumpLevel이 uppLev보다 크거나 같은 경우
									condition = true;
								}
							} else {
								if (pumpLevel >= uppLev && pumpLevel < lowLev) {
									// 조건 4: uppLev와 lowLev가 둘 다 null이 아니고, pumpLevel이 uppLev보다 크거나 같고 lowLev보다 작은 경우
									condition = true;
								}
							}
							if (condition) {
								cIdx = idx;
								uIdx = idx;
								break;
							}
						}
					}
					if (cIdx != 0) {
						if (loadCheck.equals("+")) {
							if (uniqueCIdx.contains(cIdx + 1)) {
								cIdx += 1;
								// cIdx가 collectData의 최대 인덱스를 초과하지 않도록 조정
								cIdx = Math.min(cIdx, collectData.size() - 1);
							}
						} else if (loadCheck.equals("-")) {
							if (uniqueCIdx.contains(cIdx - 1)) {
								cIdx -= 1;
							}
						}
					} else {
						loadCheck = "=";
					}
					// 인덱스가 범위를 벗어나는지 검사하고 조정
					int safeIndex = Math.min(Math.max(cIdx - 1, 0), collectData.size() - 1);

					if (uniqueCIdx.contains(cIdx) && !loadCheck.equals("=")) {
						inQuiryComb = (List<String>) (collectData.get(safeIndex)).get("pumpComb");
						if ((collectData.get(cIdx - 1)).containsKey("freq")) {
							freqMap = (HashMap<String, Double>) (collectData.get(safeIndex)).get("freq");
						}
						List<String> sinComb = new ArrayList<>();

						boolean pass = true;
						final List<String> finalInQuiryComb = new ArrayList<>(inQuiryComb);
						//실측 조합 대비 종료 예정 펌프
						List<String> result = strList.stream()
								.filter(item -> !finalInQuiryComb.contains(item))
								.collect(Collectors.toList());


						List<String> finalStrList = strList;
						//실측 조합 대비 시작 예정 펌프
						List<String> startPump = finalInQuiryComb.stream()
								.filter(item -> !finalStrList.contains(item))
								.collect(Collectors.toList());
						boolean hasZero = false;
						int wmPump = 0;
						if (!startPump.isEmpty()) {
							loadCheckLog.append("증감 운영에 따른 시작 예정 펌프 :" + startPump + "#");
							for (String pump : startPump) {
								if (pump.isEmpty()) {
									break;
								}
								int pump_idx = Integer.parseInt(pump);
								HashMap<String, Object> pumpMap = new HashMap<>();
								pumpMap.put("pump_idx", pump_idx);
								pumpMap.put("startDate", ts);
								pumpMap.put("local", wpp_code);
								List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
								hasZero = pumpUseList.contains(1);

								if (hasZero) {
									break;
								} else {
									if (wpp_code.equals("wm")) {
										if (wmPump == 0) {
											wmPump = pump_idx;
										}
									}
								}
							}
						}

						if (!result.isEmpty() && !hasZero) {
							loadCheckLog.append("증감 운영에 따른 종료 예정 펌프 :" + result + "#");
							for (String pump : result) {
								int pump_idx = Integer.parseInt(pump);
								HashMap<String, Object> pumpMap = new HashMap<>();
								pumpMap.put("pump_idx", pump_idx);
								pumpMap.put("startDate", ts);
								pumpMap.put("local", wpp_code);
								List<Integer> pumpUseList = drvnMapper.optPrePumpUse(pumpMap);
								hasZero = pumpUseList.contains(0);

								if (hasZero) {
									break;
								}
							}
						}
						if (wpp_code.equals("gr") && pump_grp == 3) {
							HashMap<String, Object> pumpMap = new HashMap<>();
							pumpMap.put("pump_idx", "11");
							pumpMap.put("startDate", ts);
							Set<Integer> freqSize = drvnMapper.wmInverterPumpFreqCheck(pumpMap);
							if (freqSize.size() != 1) {
								hasZero = true;
							}
						} else if (wpp_code.equals("ba") && pump_grp == 2) {
							HashMap<String, Object> pumpMap = new HashMap<>();
							pumpMap.put("nowDate", ts);
							pumpMap.put("interval", 20);
							pumpMap.put("limit", 15);
							pumpMap.put("pump_grp", pump_grp);
							pumpMap.put("pump_idx", 7);
							Set<Integer> size2Pump1st = drvnMapper.inverterPumpFreqCheck(pumpMap);
							if (size2Pump1st.size() != 1) {
								hasZero = true;
							}
						}

						if (hasZero) {
							inQuiryComb = returnComb;
							if ((collectData.get(uIdx - 1)).containsKey("freq")) {
								freqMap = (HashMap<String, Double>) (collectData.get(uIdx - 1)).get("freq");
							}
							loadCheck = "=";

						}
						//고령정수장 강제 조절
						if (wpp_code.equals("gr") && pump_grp == 1) {
							if (returnComb.size() > 3) {
								returnComb = getPumpCombination(1, 3, 1);
							}
						}
						if (!hasZero) {
							HashMap<Integer, Double> grpInQuiryPrdctPwr = new HashMap<>();
							if (wpp_code.equals("gs")) {
								if (load.equals("H") || (week <= 5 && (hour >= 10 && hour <= 17))) {
									if (inQuiryComb.size() >= 4) {
										inQuiryComb = findValidPumpComb(collectData, inQuiryComb);

										if (inQuiryComb.isEmpty()) {
											inQuiryComb = (List<String>) collectData.get(0).get("pumpComb");
										}
									}
								}

								Set<Integer> pumpGrpSet = new LinkedHashSet<>(pumpDstrbIdMap.keySet());

								for (Integer id : pumpGrpSet) {

									List<String> grpComb = new ArrayList<>();
									for (String pumpStr : inQuiryComb) {
										int pump = Integer.parseInt(pumpStr);
										if (id == 1) {
											if (pump <= 7) {
												grpComb.add(pumpStr);
											}
										} else {
											if (pump > 7) {
												grpComb.add(pumpStr);
											}
										}
									}
									HashMap<Integer, Double> gsPrdctPwr = allPumpGrpPwrPrdct(grpComb, grpFlowPressure, freqMap);
									grpInQuiryPrdctPwr.put(id, gsPrdctPwr.get(id));
								}

							} else {
								grpInQuiryPrdctPwr = allPumpGrpPwrPrdct(inQuiryComb, grpFlowPressure, freqMap);
							}
							String flow_ctr;
							if (loadCheck.equals("+")) {
								flow_ctr = "INC";
								changeStatus = "up";
							} else if (loadCheck.equals("-")) {
								changeStatus = "down";
								flow_ctr = "DEC";
							} else {
								flow_ctr = "KEP";
							}
							for (HashMap<String, Object> map : filteredList) {
								int map_grp = (int) map.get("PUMP_GRP");
								int idx_integer = (int) map.get("PUMP_IDX");
								double pwrPrdct = grpInQuiryPrdctPwr.get(map_grp);
								String pump_idx = String.valueOf(idx_integer);
								map.put("wpp_code", wpp_code);
								map.put("flow", flow);
								map.put("pressure", pressure);
								map.put("opt_idx", optIdxTag + insertIdx);
								map.put("pwrPrdct", pwrPrdct);
								map.put("RATE_CTGRY", load);
								map.put("FLOW_CTR", flow_ctr);
								map.put("ts", ts);
								int pump_typ = (int) map.get("PUMP_TYP");
								//인버터 타입일 경우
								map.put("freq", 0);
								if (pump_typ == 2) {
									//조합식 결과의 주파수 map 검사
									if (freqMap != null) {
										// 주파수 map에 포함되는 주파수 값이 있는지 검사
										if (wpp_code.equals("wm")) {
											map.put("freq", pump_freq);
										} else if (freqMap.containsKey(pump_idx)) {
											Double freq = freqMap.get(pump_idx);
											map.put("freq", freq);
										} else {
											map.put("freq", 0);
										}
									}
								}
								if (inQuiryComb.contains(pump_idx)) {
									map.put("pump_yn", 1);
								} else {
									map.put("pump_yn", 0);
								}

								if (wpp_code.equals("gu")) {
									map.put("chng_stts", changeStatus);
								}

								drvnMapper.insertInQuiryPumpYnData(map);
							}

						}


					}


				}
			}

		}


		return loadCheckLog;
	}
	/**
	 * 주어진 펌프 조합 데이터에서 총 펌프 대수가 4.5대 이하인 유효한 조합을 찾습니다.
	 * <p>
	 * 이 메서드는 에너지 비용 절감을 위해 최대 부하 시간대에 가동 펌프 수를 제한하는 데 사용됩니다.
	 * 먼저 {@code targetComb}와 일치하는 조합을 찾아 해당 조합부터 역순으로 탐색합니다.
	 * 일치하는 조합이 없으면 가장 마지막 조합부터 역순으로 탐색합니다.
	 * 탐색 과정에서 0.5대 펌프와 1대 펌프를 구분하여 총 펌프 대수가 4.5대 이하인
	 * 첫 번째 조합을 찾아 반환합니다.
	 * 조건을 만족하는 조합을 찾지 못하면 원래의 {@code targetComb}를 반환합니다.
	 *
	 * @param collectData 펌프 조합 및 성능 곡선 데이터가 담긴 리스트.
	 * 각 HashMap은 'pumpComb' 키를 통해 펌프 조합 리스트를 포함해야 합니다.
	 * @param targetComb  유효성 검사를 시작할 기준이 되는 펌프 조합 (현재 예측된 조합).
	 * 일치하는 조합이 없으면 전체 리스트를 역순으로 탐색합니다.
	 * @return 펌프 대수가 4.5대 이하인 유효한 펌프 조합 리스트를 반환합니다.
	 * 만약 조건을 만족하는 조합을 찾지 못하면 원래의 {@code targetComb}를 반환합니다.
	 */
	public List<String> findValidPumpComb(List<HashMap<String, Object>> collectData, List<String> targetComb) {
		// 💡 로그 시작
		loadCheckLog.append("--- Starting findValidPumpComb Logic ---#");
		if (collectData == null || collectData.isEmpty()) {
			loadCheckLog.append("  - collectData is null or empty. Returning targetComb.#");
			return targetComb;
		}
		if (targetComb == null) {
			targetComb = new ArrayList<>();
		}
		loadCheckLog.append("  - Target Combination: " + targetComb + "#");

		// 0. 펌프 대수 정보를 미리 정의 (0.5대 펌프)
		Set<Integer> halfPumpIdxs = new HashSet<>(Arrays.asList(2, 3, 11));

		// 💡 Step 1: targetComb 자체의 펌프 대수를 계산하고 유효성을 먼저 검사
		double targetPumpSize = 0.0;
		for (String pumpIdxStr : targetComb) {
			try {
				int pumpIdx = Integer.parseInt(pumpIdxStr.trim());
				if (halfPumpIdxs.contains(pumpIdx)) {
					targetPumpSize += 0.5;
				} else {
					targetPumpSize += 1.0;
				}
			} catch (NumberFormatException e) {
				continue;
			}
		}
		loadCheckLog.append("  - Checking targetComb. Total size: " + targetPumpSize + "대.#");

		if (targetPumpSize <= 4.5) {
			// 💡 targetComb가 이미 유효한 조합이므로, 바로 반환
			loadCheckLog.append("  - targetComb is already valid (size <= 4.5대). Returning it.#");
			return targetComb;
		}

		// 💡 Step 2: targetComb가 유효하지 않을 경우, collectData에서 탐색 시작
		loadCheckLog.append("  - targetComb is not valid. Searching for a valid combination below.#");

		// 1. targetComb와 값이 같은 인덱스 찾기
		int idx = -1;
		for (int i = 0; i < collectData.size(); i++) {
			Map<String, Object> item = collectData.get(i);
			if (item != null && item.get("pumpComb") != null) {
				List<String> comb = (List<String>) item.get("pumpComb");
				if (comb != null && comb.size() == targetComb.size() &&
						comb.containsAll(targetComb) && targetComb.containsAll(comb)) {
					idx = i;
					break;
				}
			}
		}

		// 2. 못 찾으면 마지막 인덱스부터, 찾으면 해당 인덱스 바로 전부터 탐색
		if (idx == -1) {
			idx = collectData.size() - 1;
		} else {
			idx--; // 찾은 인덱스 바로 이전부터 탐색을 시작
		}

		loadCheckLog.append("  - Starting search from index: " + idx + "#");

		while (idx >= 0) {
			Map<String, Object> item = collectData.get(idx);
			if (item != null && item.get("pumpComb") != null) {
				List<String> comb = (List<String>) item.get("pumpComb");

				double totalPumpSize = 0.0;
				if (comb != null) {
					for (String pumpIdxStr : comb) {
						try {
							int pumpIdx = Integer.parseInt(pumpIdxStr.trim());
							if (halfPumpIdxs.contains(pumpIdx)) {
								totalPumpSize += 0.5;
							} else {
								totalPumpSize += 1.0;
							}
						} catch (NumberFormatException e) {
							continue;
						}
					}
				}
				loadCheckLog.append("  - Checking combination " + comb + " at index " + idx + ". Total size: " + totalPumpSize + "대.#");

				if (totalPumpSize <= 4.5) {
					loadCheckLog.append("  - Found a valid combination with size <= 4.5대. Returning: " + comb + "#");
					return comb;
				}
			}
			idx--;
		}

		// 3. 조건에 맞는 조합이 없으면 기존 조합을 반환
		loadCheckLog.append("  - No valid combination found. Returning original targetComb.#");
		loadCheckLog.append("--- findValidPumpComb Logic Finished ---#");
		return targetComb;
	}
	/**
	 * 펌프 조합의 총 대수를 계산합니다. (e.g., 2, 3, 11번은 0.5대로 계산)
	 * @param pumpComb 펌프 조합 리스트 (e.g., ["1", "3"])
	 * @return 계산된 총 펌프 대수
	 */
	private double calculatePumpSize(List<String> pumpComb) {
		if (pumpComb == null || pumpComb.isEmpty()) {
			return 0.0;
		}
		// 0.5대로 취급되는 펌프 인덱스 정의
		final Set<Integer> halfPumpIdxs = new HashSet<>(Arrays.asList(2, 3, 11));
		double totalSize = 0.0;
		for (String pumpIdxStr : pumpComb) {
			try {
				int pumpIdx = Integer.parseInt(pumpIdxStr.trim());
				if (halfPumpIdxs.contains(pumpIdx)) {
					totalSize += 0.5;
				} else {
					totalSize += 1.0;
				}
			} catch (NumberFormatException e) {
				// 숫자 변환 실패 시 무시
				continue;
			}
		}
		return totalSize;
	}

	/**
	 * 22시 UP 조건 시, 4.5대에 가장 적합한 펌프 조합을 찾습니다.
	 * 1순위: 4.5대 이상 중 가장 가까운 조합
	 * 2순위: 4.5대 미만 중 가장 가까운 조합
	 * @param collectData 전체 펌프 조합 데이터
	 * @return 최적의 펌프 조합
	 */
	private List<String> findOptimalPumpCombFor2200(List<HashMap<String, Object>> collectData) {
		if (collectData == null || collectData.isEmpty()) {
			return new ArrayList<>(); // 비어있는 조합 반환
		}

		List<String> bestComb = null;
		double minAbsDifference = Double.MAX_VALUE;
		double bestCombSize = -1.0; // 현재까지 찾은 최적 조합의 대수

		for (HashMap<String, Object> item : collectData) {
			List<String> currentComb = (List<String>) item.get("pumpComb");
			if (currentComb == null) continue;

			double currentSize = calculatePumpSize(currentComb);
			double currentDifference = Math.abs(currentSize - 4.5);

			if (bestComb == null) {
				// 첫 번째 유효한 조합을 기준으로 설정
				bestComb = currentComb;
				minAbsDifference = currentDifference;
				bestCombSize = currentSize;
			} else {
				// 우선순위 결정 로직:
				// 1. 현재 최적 조합(best)은 4.5 미만인데, 새로운 조합(current)이 4.5 이상이면 무조건 교체
				if (bestCombSize < 4.5 && currentSize >= 4.5) {
					bestComb = currentComb;
					minAbsDifference = currentDifference;
					bestCombSize = currentSize;
				}
				// 2. 둘 다 4.5 이상이거나 둘 다 4.5 미만일 경우, 차이가 더 적은 쪽으로 교체
				else if ((bestCombSize >= 4.5 && currentSize >= 4.5) || (bestCombSize < 4.5 && currentSize < 4.5)) {
					if (currentDifference < minAbsDifference) {
						bestComb = currentComb;
						minAbsDifference = currentDifference;
						bestCombSize = currentSize;
					}
				}
				// 3. 현재 최적 조합(best)이 4.5 이상이고 새로운 조합(current)이 4.5 미만이면, 교체하지 않음 (기존 우선순위 유지)
			}
		}

		return (bestComb != null) ? bestComb : new ArrayList<>();
	}
	/**
	 * 부하시간대에 압력(정수장에 따라 수위)조건이 만족하는지를 보는 메서드
	 *
	 * @param ts       계산할 시간
	 * @param load     부하 정보(L:경부하 or H:최대부하)
	 * @param pump_grp 계산할 펌프 그룹
	 * @return +, = , - 중 하나를 반환
	 */
	private String getLoadCheck(String ts, String load, int pump_grp) {
		String returnCheck = null;
		if (load.equals("H")) {
			//properties에 정의된 분기 압력 정보 받아오기
			loadCheckLog.append("최대부하 축소운영 압력 조건 비교" + "#");

			Set<String> targetPre = pumpCombTargetMap.get(pump_grp).keySet();
			int fullLimit = targetPre.size();
			int stack = 0;
			for (String targetId : targetPre) {
				double limit = pumpCombTargetMap.get(pump_grp).get(targetId);
				HashMap<String, Object> param = new HashMap<>();
				param.put("nowDateTime", ts);
				param.put("DSTRB_ID", targetId);
				List<HashMap<String, Object>> targetPressureList = new ArrayList<>();
				if (wpp_code.equals("gu")) {
					targetPressureList = drvnMapper.curFlowPressure(param);
				} else {
					targetPressureList = drvnMapper.preFlowPressure(param);
				}
				String targetPressureStr;

				if (targetPressureList.isEmpty() || !targetPressureList.get(0).containsKey("value") || targetPressureList.get(0) == null) {
					targetPressureStr = "0";
				} else {
					targetPressureStr = (String) targetPressureList.get(0).get("value");
					String targetTs = (String) targetPressureList.get(0).get("ts");
					loadCheckLog.append("조회 TAG 시간: " + targetTs + "#");
				}
				double targetPressureFl = Double.parseDouble(targetPressureStr);
				loadCheckLog.append("조회 TAG : " + targetId + "#");
				loadCheckLog.append("최소 압력 : " + limit + " < 조회 압력 : " + targetPressureFl + "#");
				if (limit < targetPressureFl) {
					stack++;

				} else if (targetPressureFl == 0) {
					returnCheck = "=";
					return returnCheck;
				}
			}
			if (fullLimit == stack) {
				loadCheckLog.append("압력 기준 O" + "#");
				returnCheck = "-";
			} else {
				loadCheckLog.append("압력 기준 X" + "#");
				returnCheck = "=";
			}
			// 최대부하 축소가 아닐때
			if (!returnCheck.equals("-")) {
				Set<String> targetPreUp = pumpCombTargetMapUp.get(pump_grp).keySet();
				int fullLimitUp = targetPreUp.size();
				int stackUp = 0;
				for (String targetId : targetPreUp) {
					double limit = pumpCombTargetMapUp.get(pump_grp).get(targetId);
					HashMap<String, Object> param = new HashMap<>();
					param.put("nowDateTime", ts);
					param.put("DSTRB_ID", targetId);

					List<HashMap<String, Object>> targetPressureList = new ArrayList<>();
					if (wpp_code.equals("gu")) {
						targetPressureList = drvnMapper.curFlowPressure(param);
					} else {
						targetPressureList = drvnMapper.preFlowPressure(param);
					}
					String targetPressureStr;

					if (targetPressureList.isEmpty() || !targetPressureList.get(0).containsKey("value") || targetPressureList.get(0) == null) {
						targetPressureStr = "0";
					} else {
						targetPressureStr = (String) targetPressureList.get(0).get("value");
						String targetTs = (String) targetPressureList.get(0).get("ts");
						loadCheckLog.append("조회 TAG 시간: " + targetTs + "#");
					}

					double targetPressureFl = Double.parseDouble(targetPressureStr);
					loadCheckLog.append("조회 TAG : " + targetId + "#");

					loadCheckLog.append("최소 압력 : " + limit + " > 조회 압력 : " + targetPressureFl + "#");
					if (limit > targetPressureFl) {
						stackUp++;

					} else if (targetPressureFl == 0) {
						returnCheck = "=";
						return returnCheck;
					}
				}
				if (fullLimitUp == stackUp) {
					loadCheckLog.append("압력 기준 O" + "#");
					returnCheck = "+";
				} else {
					loadCheckLog.append("압력 기준 X" + "#");
					returnCheck = "=";
				}
			}

		} else if (load.equals("L")) {
			loadCheckLog.append("경부하 압력 조건 비교" + "#");
			Set<String> targetPre = pumpCombTargetMapMin.get(pump_grp).keySet();
			int fullLimit = targetPre.size();
			int stack = 0;
			for (String targetId : targetPre) {

				double limit = pumpCombTargetMapMin.get(pump_grp).get(targetId);
				HashMap<String, Object> param = new HashMap<>();
				param.put("nowDateTime", ts);
				param.put("DSTRB_ID", targetId);

				List<HashMap<String, Object>> targetPressureList = new ArrayList<>();
				if (wpp_code.equals("gu")) {
					targetPressureList = drvnMapper.curFlowPressure(param);
				} else {
					targetPressureList = drvnMapper.preFlowPressure(param);
				}
				String targetPressureStr;

				if (targetPressureList.isEmpty() || !targetPressureList.get(0).containsKey("value") || targetPressureList.get(0) == null) {
					targetPressureStr = "0";
				} else {
					targetPressureStr = (String) targetPressureList.get(0).get("value");
					String targetTs = (String) targetPressureList.get(0).get("ts");
					loadCheckLog.append("조회 TAG 시간: " + targetTs + "#");
				}
				double targetPressureFl = Double.parseDouble(targetPressureStr);
				loadCheckLog.append("조회 TAG : " + targetId + "#");
				loadCheckLog.append("최대 압력 : " + limit + "> 조회 압력 : " + targetPressureFl + "#");
				if (limit > targetPressureFl) {
					stack++;

				} else if (targetPressureFl == 0) {
					returnCheck = "=";
					return returnCheck;
				}
			}
			if (fullLimit == stack || targetPre.isEmpty()) {
				loadCheckLog.append("압력 기준 O" + "#");
				returnCheck = "+";
			} else {
				loadCheckLog.append("압력 기준 X" + "#");
				returnCheck = "=";
			}
		} else {
			returnCheck = "=";
		}

		return returnCheck;
	}

	/**
	 * 경부하시간대에 목표수위에 따른 증감여부 반환 메섣,
	 *
	 * @param ts       계산할 시간(현재 시간 및 수위 값 가져오기 위함)
	 * @param pump_grp 계산할 펌프 그룹(properties에 저장된 값을 가져오기 위함)
	 * @return +, = , - 중 하나를 반환
	 */
	private String getLowLoadLevelCheck(String ts, int pump_grp) {
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
		LocalDateTime dateTime = LocalDateTime.parse(ts, formatter);
		String returnCheck = "=";
		int endHour = 7;
		int wmOptMinute = 450;
		double optMinute = 540;
		if (wpp_code.equals("wm")) {
			DayOfWeek dayOfWeek = dateTime.getDayOfWeek();
			int week = dayOfWeek.getValue();
			HolidayChecker holidayChecker = new HolidayChecker();
			Boolean passDayBool = holidayChecker.isPassDay(ts);

			if (passDayBool || week >= 6) {
				//공휴일 및 주말
				endHour = 8;
				wmOptMinute += 60;
				optMinute += 60;
			}
		}
		if (dateTime.getHour() < endHour || dateTime.getHour() >= 22) {
			Set<String> levelSet = pumpCombTargetLevelMap.get(pump_grp).keySet();
			for (String levelTag : levelSet) {
				int hour = dateTime.getHour();
				int minute = dateTime.getMinute();
				LocalDateTime minusTime = dateTime.minusMinutes(5);
				String minusTs = minusTime.format(formatter);


				//22시 시작
				if (hour == 22) {
					hour = 0;
				} else if (hour == 23) {
					hour = 1;
				} else if (hour == 0) {
					hour = 2;
				} else {
					hour += 2;
				}
				int nowScore = (hour * 60) + minute;


				String level_tag = levelTag;
				double max_level = pumpCombTargetLevelMap.get(pump_grp).get(levelTag);
				HashMap<String, Object> levelMap = new HashMap<>();
				levelMap.put("nowDateTime", ts);
				levelMap.put("DSTRB_ID", level_tag);

				String nowLevelTs = "";
				double nowLevel;

				try {
					if (wpp_code.equals("wm")) {
						List<HashMap<String, Object>> nowLevelList = drvnMapper.preFlowPressure(levelMap);
						if (nowLevelList == null || nowLevelList.isEmpty()) {
							return "=";
						}
						String nowLevelStr = (String) nowLevelList.get(0).get("value");
						nowLevel = Double.parseDouble(nowLevelStr);
						nowLevelTs = (String) nowLevelList.get(0).get("ts");
					} else if (wpp_code.equals("gs")) {
						List<String> levelTagList;

						if ("701-367-LEI-8001".equals(level_tag)) {
							levelTagList = Arrays.asList("701-367-LEI-8001", "701-367-LEI-8002", "701-367-LEI-8003", "701-367-LEI-8004");
						} else if ("701-367-LEI-8005".equals(level_tag)) {
							levelTagList = Arrays.asList("701-367-LEI-8005", "701-367-LEI-8006", "701-367-LEI-8007", "701-367-LEI-8008");
						} else {
							return "=";
						}

						int cnt = 0;
						double avgLevel = 0.0;

						for (String level : levelTagList) {
							levelMap.put("DSTRB_ID", level);
							List<HashMap<String, Object>> forLevelList = drvnMapper.curFlowPressure(levelMap);

							if (forLevelList != null && !forLevelList.isEmpty()) {
								if (nowLevelTs.isEmpty()) {
									nowLevelTs = (String) forLevelList.get(0).get("ts");
								}

								String forLevelStr = (String) forLevelList.get(0).get("value");
								try {
									double forLevel = Double.parseDouble(forLevelStr);
									if (forLevel >= 2) {
										cnt++;
										avgLevel += forLevel;
									}
								} catch (NumberFormatException e) {
									return "="; // 잘못된 값이 있을 경우 "=" 반환
								}
							}
						}

						if (cnt == 0 || avgLevel < 2) {
							return "=";
						}

						nowLevel = avgLevel / cnt;
					} else {
						List<HashMap<String, Object>> nowLevelList = drvnMapper.curFlowPressure(levelMap);
						if (nowLevelList == null || nowLevelList.isEmpty()) {
							return "=";
						}
						String nowLevelStr = (String) nowLevelList.get(0).get("value");
						try {
							nowLevel = Double.parseDouble(nowLevelStr);
							nowLevelTs = (String) nowLevelList.get(0).get("ts");
						} catch (NumberFormatException e) {
							return "="; // 잘못된 값이 있을 경우 "=" 반환
						}
					}
				} catch (Exception e) {
					return "="; // 예상치 못한 예외 발생 시 "=" 반환
				}


				levelMap.put("nowDateTime", minusTs);

				String minusLevelTs = "";
				double minusLevel;

				try {
					if (wpp_code.equals("wm")) {
						List<HashMap<String, Object>> minusLevelList = drvnMapper.preFlowPressure(levelMap);
						if (minusLevelList == null || minusLevelList.isEmpty()) {
							return "=";
						}
						String minusLevelStr = (String) minusLevelList.get(0).get("value");
						minusLevel = Double.parseDouble(minusLevelStr);
						minusLevelTs = (String) minusLevelList.get(0).get("ts");
					} else if (wpp_code.equals("gs")) {
						List<String> levelTagList;

						if ("701-367-LEI-8001".equals(level_tag)) {
							levelTagList = Arrays.asList("701-367-LEI-8001", "701-367-LEI-8002", "701-367-LEI-8003", "701-367-LEI-8004");
						} else if ("701-367-LEI-8005".equals(level_tag)) {
							levelTagList = Arrays.asList("701-367-LEI-8005", "701-367-LEI-8006", "701-367-LEI-8007", "701-367-LEI-8008");
						} else {
							return "=";
						}

						int cnt = 0;
						double avgLevel = 0.0;

						for (String level : levelTagList) {
							levelMap.put("DSTRB_ID", level);
							List<HashMap<String, Object>> forLevelList = drvnMapper.curFlowPressure(levelMap);

							if (forLevelList != null && !forLevelList.isEmpty()) {
								if (minusLevelTs.isEmpty()) {
									minusLevelTs = (String) forLevelList.get(0).get("ts");
								}

								String forLevelStr = (String) forLevelList.get(0).get("value");
								try {
									double forLevel = Double.parseDouble(forLevelStr);
									if (forLevel >= 2) {
										cnt++;
										avgLevel += forLevel;
									}
								} catch (NumberFormatException e) {
									return "="; // 잘못된 값이 있을 경우 "=" 반환
								}
							}
						}

						if (cnt == 0 || avgLevel < 2) {
							return "=";
						}

						minusLevel = avgLevel / cnt;
					} else {
						List<HashMap<String, Object>> minusLevelList = drvnMapper.curFlowPressure(levelMap);
						if (minusLevelList == null || minusLevelList.isEmpty()) {
							return "=";
						}
						String minusLevelStr = (String) minusLevelList.get(0).get("value");
						try {
							minusLevel = Double.parseDouble(minusLevelStr);
							minusLevelTs = (String) minusLevelList.get(0).get("ts");
						} catch (NumberFormatException e) {
							return "="; // 잘못된 값이 있을 경우 "=" 반환
						}
					}
				} catch (Exception e) {
					return "="; // 예상치 못한 예외 발생 시 "=" 반환
				}

				if (wpp_code.equals("wm") && nowLevel > max_level) {
					returnCheck = "wm";
					break;
				}
				if (nowLevel == 0.0 || minusLevel == 0.0) {
					returnCheck = "=";
					break;
				}
				//현재 수위가 목표수위보다 높을경우 -1(전시간 5분전 수위도 혹시모르니 같이 뺴줌)
				if (nowLevel > max_level && minusLevel > max_level) {
					nowLevel -= 1;
					minusLevel -= 1;
				}

				//수위 차이가 음수 일 시 바로 추가운영으로 조건 변경
				//수위차이 0일시 해결
				double wtrLvlDiff = nowLevel - minusLevel;

				if (wtrLvlDiff == 0) {
					boolean pass = true;
					int forMinute = 5;
					while (pass && nowScore > 0) {

						nowScore -= 5;
						LocalDateTime afterTime = dateTime.minusMinutes(forMinute);
						LocalDateTime afterMinusTime = minusTime.minusMinutes(forMinute);
						String afterTs = afterTime.format(formatter);
						String afterMinusTs = afterMinusTime.format(formatter);

						HashMap<String, Object> afterMap = new HashMap<>();
						afterMap.put("nowDateTime", afterTs);
						afterMap.put("DSTRB_ID", level_tag);
						List<HashMap<String, Object>> afterNowList = drvnMapper.curFlowPressure(afterMap);
						String afterNowStr = (String) afterNowList.get(0).get("value");
						double afterNow = Double.parseDouble(afterNowStr);
						levelMap.put("nowDateTime", afterMinusTs);
						List<HashMap<String, Object>> afterMinusList = drvnMapper.curFlowPressure(levelMap);
						String afterMinusStr = (String) afterMinusList.get(0).get("value");
						double afterMinus = Double.parseDouble(afterMinusStr);
						if ((afterNow - afterMinus) != 0) {
							pass = false;
							nowLevel = afterNow;
							minusLevel = afterMinus;
						}
						forMinute += 5;
					}

					if (pass) {
						returnCheck = "=";
						break;
					}
				}

				//1시간 예상 수위 증가량
				double levelPlus = (nowLevel - minusLevel) * 12;
				//목표수위와 현재수위의 차
				double optLevel = max_level - nowLevel;
				//목표수위 도달 시간
				double optLevelMinute = (optLevel / levelPlus) * 60;


				//목표시간내에 목표수위 도달 예상시간
				double totalScore = nowScore + optLevelMinute;

				// 목표 시간보다 도달 예상시간이 작은경우?
				if (wtrLvlDiff < 0) {

					if (wpp_code.equals("wm")) {
						int forMinute = 10;
						nowScore -= 10;
						LocalDateTime afterTime = dateTime.minusMinutes(forMinute);
						LocalDateTime afterMinusTime = minusTime.minusMinutes(forMinute);
						String afterTs = afterTime.format(formatter);
						String afterMinusTs = afterMinusTime.format(formatter);

						HashMap<String, Object> afterMap = new HashMap<>();
						afterMap.put("nowDateTime", afterTs);
						afterMap.put("DSTRB_ID", level_tag);
						List<HashMap<String, Object>> afterNowList = drvnMapper.preFlowPressure(levelMap);
						String afterNowStr = (String) afterNowList.get(0).get("value");
						double afterNow = Double.parseDouble(afterNowStr);
						levelMap.put("nowDateTime", afterMinusTs);
						List<HashMap<String, Object>> afterMinusList = drvnMapper.preFlowPressure(levelMap);
						String afterMinusStr = (String) afterMinusList.get(0).get("value");
						double afterMinus = Double.parseDouble(afterMinusStr);
						//1시간 예상 수위 증가량
						double afterLevelPlus = (afterNow - afterMinus) * 12;
						//목표수위와 현재수위의 차
						double afterOptLevel = max_level - afterNow;
						//목표수위 도달 시간
						double afterOptLevelMinute = (afterOptLevel / afterLevelPlus) * 60;


						//목표시간내에 목표수위 도달 예상시간
						double afterTotalScore = nowScore + afterOptLevelMinute;
						if (afterOptLevel > 0) {
							//직전 예측조합 유지
							returnCheck = "wmPreUsing";
							break;
						} else {
							returnCheck = "+";
							break;
						}
					} else {
						returnCheck = "+";
						continue;
					}
				}
				if (wpp_code.equals("wm") && totalScore > 0 && totalScore < wmOptMinute) {
					if (wtrLvlDiff > 2.5) {
						int forMinute = 5;
						nowScore -= 5;
						LocalDateTime afterTime = dateTime.minusMinutes(forMinute);
						LocalDateTime afterMinusTime = minusTime.minusMinutes(forMinute);
						String afterTs = afterTime.format(formatter);
						String afterMinusTs = afterMinusTime.format(formatter);

						HashMap<String, Object> afterMap = new HashMap<>();
						afterMap.put("nowDateTime", afterTs);
						afterMap.put("DSTRB_ID", level_tag);
						List<HashMap<String, Object>> afterNowList = drvnMapper.preFlowPressure(levelMap);
						String afterNowStr = (String) afterNowList.get(0).get("value");
						double afterNow = Double.parseDouble(afterNowStr);
						levelMap.put("nowDateTime", afterMinusTs);
						List<HashMap<String, Object>> afterMinusList = drvnMapper.preFlowPressure(levelMap);
						String afterMinusStr = (String) afterMinusList.get(0).get("value");
						double afterMinus = Double.parseDouble(afterMinusStr);
						//1시간 예상 수위 증가량
						double afterLevelPlus = (afterNow - afterMinus) * 12;
						//목표수위와 현재수위의 차
						double afterOptLevel = max_level - afterNow;
						//목표수위 도달 시간
						double afterOptLevelMinute = (afterOptLevel / afterLevelPlus) * 60;


						//목표시간내에 목표수위 도달 예상시간
						double afterTotalScore = nowScore + afterOptLevelMinute;
						if (afterTotalScore > 0) {
							if (afterTotalScore < wmOptMinute) {
								returnCheck = "wm";
								break;
							}
						}
					} else {
						returnCheck = "wm";
						break;
					}

				}
				if (totalScore < optMinute) {
					returnCheck = "-";
					break;
				} else {
					returnCheck = "+";
				}
			}
		} else {
			returnCheck = "=";
		}


		loadCheckLog.append("returnCheck:" + returnCheck + "#");
		return returnCheck;
	}

	/**
	 * 최대부하시간 목표수위에 따른 증감 여부 반환 메서드(운문에서만 사용)
	 *
	 * @param ts        측정할 시간(수위값을 가져오기, 현재 시간값)
	 * @param opt_level 목표 시간값 전달
	 * @return +, = , - 중 하나를 반환
	 */
	private String getHighLoadLevelCheck(String ts, double opt_level) {
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
		LocalDateTime dateTime = LocalDateTime.parse(ts, formatter);
		String returnCheck = "=";
		if (dateTime.getHour() < 19 && dateTime.getHour() >= 11) {


			int hour = dateTime.getHour();
			int minute = dateTime.getMinute();
			LocalDateTime minusTime = dateTime.minusMinutes(5);
			String minusTs = minusTime.format(formatter);
			double optMinute = 19 * 60;

			int nowScore = (hour * 60) + minute;


			String level_tag = "H1_Predict";
			double max_level = opt_level;
			HashMap<String, Object> levelMap = new HashMap<>();
			levelMap.put("nowDateTime", ts);
			levelMap.put("DSTRB_ID", level_tag);
			List<HashMap<String, Object>> nowLevelList = new ArrayList<>();
			if (wpp_code.equals("wm")) {
				nowLevelList = drvnMapper.preFlowPressure(levelMap);
			} else {
				nowLevelList = drvnMapper.curFlowPressure(levelMap);
			}
			String nowLevelStr = (String) nowLevelList.get(0).get("value");
			String nowLevelTs = (String) nowLevelList.get(0).get("ts");

			double nowLevel = Double.parseDouble(nowLevelStr);
			levelMap.put("nowDateTime", minusTs);
			List<HashMap<String, Object>> minusLevelList = new ArrayList<>();
			if (wpp_code.equals("wm")) {
				minusLevelList = drvnMapper.preFlowPressure(levelMap);
			} else {
				minusLevelList = drvnMapper.curFlowPressure(levelMap);
			}
			String minusLevelStr = (String) minusLevelList.get(0).get("value");
			String minusLevelTs = (String) minusLevelList.get(0).get("ts");
			double minusLevel = Double.parseDouble(minusLevelStr);

			if (nowLevel == 0.0 || minusLevel == 0.0) {
				returnCheck = "=";
				return returnCheck;
			}
			//현재 수위가 목표수위보다 높을경우 -1(전시간 5분전 수위도 혹시모르니 같이 뺴줌)
			if (nowLevel > max_level && minusLevel > max_level) {
				nowLevel -= 1;
				minusLevel -= 1;
			}

			//수위 차이가 음수 일 시 바로 추가운영으로 조건 변경
			//수위차이 0일시 해결
			double wtrLvlDiff = nowLevel - minusLevel;

			if (wtrLvlDiff == 0) {


				boolean pass = true;
				int forMinute = 5;
				while (pass && nowScore > 0) {

					nowScore -= 5;
					LocalDateTime afterTime = dateTime.minusMinutes(forMinute);
					LocalDateTime afterMinusTime = minusTime.minusMinutes(forMinute);
					String afterTs = afterTime.format(formatter);
					String afterMinusTs = afterMinusTime.format(formatter);

					HashMap<String, Object> afterMap = new HashMap<>();
					afterMap.put("nowDateTime", afterTs);
					afterMap.put("DSTRB_ID", level_tag);
					List<HashMap<String, Object>> afterNowList = drvnMapper.curFlowPressure(afterMap);
					String afterNowStr = (String) afterNowList.get(0).get("value");
					double afterNow = Double.parseDouble(afterNowStr);
					levelMap.put("nowDateTime", afterMinusTs);
					List<HashMap<String, Object>> afterMinusList = drvnMapper.curFlowPressure(levelMap);
					String afterMinusStr = (String) afterMinusList.get(0).get("value");
					double afterMinus = Double.parseDouble(afterMinusStr);

					if ((afterNow - afterMinus) != 0) {
						pass = false;
						nowLevel = afterNow;
						minusLevel = afterMinus;
					}
					forMinute += 5;
				}


			}

			//1시간 예상 수위 증가량
			double levelPlus = (nowLevel - minusLevel) * 12;
			//목표수위와 현재수위의 차
			double optLevel = max_level - nowLevel;
			//목표수위 도달 시간
			double optLevelMinute = (optLevel / levelPlus) * 60;


			//목표시간내에 목표수위 도달 예상시간
			double totalScore = nowScore + optLevelMinute;

			// 목표 시간보다 도달 예상시간이 작은경우?

			if (totalScore < optMinute) {
				returnCheck = "+";
			} else {
				returnCheck = "-";
			}

		} else {
			returnCheck = "=";
		}


		loadCheckLog.append("returnCheck:" + returnCheck + "#");
		return returnCheck;
	}


	/**
	 * @param flow     계산할 유량값
	 * @param map      회기식 데이터가 담긴 map
	 * @param pump_grp 펌프 그룹 0 만아니면 상관없음 계산할 펌프 그룹값을 전달
	 * @return 계산된 회기식 기반 압력
	 */
	public double pressureCalValue(double flow, HashMap<String, Object> map, int pump_grp) {
		String cs_op = (String) map.get("CS_OP");
		String ss_op = (String) map.get("SS_OP");
		double p_add_val = (double) map.get("P_ADD_VAL");
		double p_mul_val = (double) map.get("P_MUL_VAL");
		double p_sqrt_mul_val = (double) map.get("P_SQRT_MUL_VAL");

		return (p_add_val * Math.pow(flow, 2)) + (p_mul_val * flow) + (p_sqrt_mul_val);


	}

	/**
	 * 통합 유량 및 압력을 계산하는 메서드
	 *
	 * @param dataMap 데이터 map(유량과 압력이 들어있는 map flow:유량, pressure: 압력)
	 * @param type    예측인지 실측인지 구분하는 param
	 * @return 통합 압력 및 유량의 리스트를 묶은 map 반환
	 */
	public HashMap<String, List<Double>> integrateFlowPressCalc(LinkedHashMap<String, List<HashMap<String, Object>>> dataMap, String type) {
		Set<String> dataKey = dataMap.keySet();
		int minSize = -1;
		for (String key : dataKey) {

			List<HashMap<String, Object>> list = dataMap.get(key);

			if (minSize == -1) {
				minSize = list.size();
			} else {
				if (minSize > list.size()) {
					minSize = list.size();
				}
			}
		}
		List<Double> flowList = new ArrayList<>();
		List<Double> pressureList = new ArrayList<>();


		HashMap<String, List<Double>> returnMap = new HashMap<>();
		for (int i = 0; i < minSize; i++) {


			double flow = 0.0;
			double pressure1 = 0.0;
			double pressure2 = 0.0;

			for (String key : dataKey) {
				List<HashMap<String, Object>> list = dataMap.get(key);
				HashMap<String, Object> map = list.get(i);
				if (type.equals("pre")) {
					Float valueObj = (float) map.get("value");
					Double value;
					if (valueObj != null) {
						value = (double) valueObj;
					} else {
						value = null;
					}

					if (key.contains("flow")) {
						if (value != null) {
							flow += value;
						}
					} else if (key.contains("pressure1")) {
						if (value != null) {
							pressure1 = value;
						}
					} else if (key.contains("pressure2")) {
						if (value != null) {
							pressure2 = value;
						}
					}

				} else {
					String valueObj = (String) map.get("value");
					Double value;
					if (valueObj != null) {
						value = Double.valueOf(valueObj);
					} else {
						value = 0.0;
					}

					if (key.contains("flow")) {
						flow += value;
					} else if (key.contains("pressure1")) {
						pressure1 = value;
					} else if (key.contains("pressure2")) {
						pressure2 = value;
					}
				}


			}

			//y = (0.025268*구송수압력) + (0.968549*신송수압력) + 0.064324
			if (flow != 0.0 && pressure1 != 0.0 && pressure2 != 0.0) {
				flowList.add(flow);
				pressureList.add((0.025268 * pressure1) + (0.968549 * pressure2) + 0.064324);

			} else {
				flowList.add(0.0);
				pressureList.add(0.0);
			}

		}

		returnMap.put("flow", flowList);
		returnMap.put("pressure", pressureList);

		return returnMap;

	}

	/**
	 * 예측 펌프조합에 따른 예측 전력 계산 메섣,
	 *
	 * @param pumpComb        펌프 조합 String List
	 * @param grpFlowPressure 그룹별 유량 및 압력(이제는 계산할 그룹만 매핑해서 map으로 전달하면 됨)
	 * @param freqMap         인버터 펌프가 있을 경우 주파수 값을 전달해 계산에 사용(주파수 값 Map<펌프 idx, 주파수 값>)
	 * @return 계산된 그룹별 전력
	 */
	public HashMap<Integer, Double> allPumpGrpPwrPrdct(List<String> pumpComb, HashMap<Integer, HashMap<String, Double>> grpFlowPressure, HashMap<String, Double> freqMap) {
		HashMap<Integer, Double> returnMap = new HashMap<>();
		List<HashMap<String, Object>> pumpList = setPumpList;
		HashMap<Integer, List<Integer>> grpPumpMap = new HashMap<>();
		for (HashMap<String, Object> pump : pumpList) {
			int pumpIdx = (int) pump.get("PUMP_IDX");
			int pumpGrp = (int) pump.get("PUMP_GRP");
			String idxStr = String.valueOf(pumpIdx);
			if (pumpComb.contains(idxStr)) {
				if (grpPumpMap.containsKey(pumpGrp)) {
					grpPumpMap.get(pumpGrp).add(pumpIdx);
				} else {
					List<Integer> firstList = new ArrayList<>();
					firstList.add(pumpIdx);
					grpPumpMap.put(pumpGrp, firstList);
				}
			}
		}

		Set<Integer> grpKey = grpFlowPressure.keySet();
		for (Integer grp : grpKey) {

			HashMap<Integer, Double> grpPwrIdxMap = prdctPwrIdxValMap.get(grp);

			HashMap<String, Double> flowPressureMap = grpFlowPressure.get(grp);
			double flow = flowPressureMap.get("flow");
			double pressure = flowPressureMap.get("pressure");
			List<Integer> grpPumpComb = grpPumpMap.get(grp);

			HashMap<String, Double> prdctPwrCalMap = prdctPwrCalValMap.get(grp);
			double prdctPwrFlow = prdctPwrCalMap.get("prdctPwrFlow");
			double prdctPwrPress = prdctPwrCalMap.get("prdctPwrPress");
			//예측 전력 고정값
			double prdctPwrDefault = prdctPwrCalMap.get("prdctPwrDefault");

			double returnPrdctPwr = (prdctPwrFlow * flow)
					+
					(prdctPwrPress * pressure)
					+
					prdctPwrDefault;

			if (grpPumpComb == null) {
				returnMap.put(grp, 0.0);
			} else {
				for (Integer pump : grpPumpComb) {

					Double defaultFreq = 60.0;
					if (freqMap != null) {
						String pump_idx_str = String.valueOf(pump);
						if (freqMap.containsKey(pump_idx_str)) {
							Double pump_freq = freqMap.get(pump_idx_str);
							defaultFreq = pump_freq;
						}
					}
					returnPrdctPwr += (grpPwrIdxMap.get(pump) * defaultFreq);

				}
				if (wpp_code.equals("wm")) {
					returnMap.put(grp, returnPrdctPwr * 1000);
				} else {
					returnMap.put(grp, returnPrdctPwr);

				}
			}
		}


		return returnMap;
	}

	/**
	 * DB에 저장된 월별 시간대 부하정보를 Map으로 return하는 메서드
	 *
	 * @return 월별 시간대 부하 정보
	 */
	public HashMap<Integer, HashMap<Integer, String>> getMonthPwrReduc() {
		HashMap<Integer, HashMap<Integer, String>> returnMap = new HashMap<>();

		List<HashMap<String, String>> reduceList = drvnMapper.getLoadInquiry();
		for (int i = 1; i <= 12; i++) {
			HashMap<Integer, String> map = new HashMap<>();
			returnMap.put(i, map);
		}
		for (HashMap<String, String> reduce : reduceList) {
			String mnthStr = reduce.get("MNTH");
			int mnth = Integer.parseInt(mnthStr);
			String hourStr = reduce.get("STN_TM");
			int hour = Integer.parseInt(hourStr);
			String timezone = reduce.get("TIMEZONE");
			returnMap.get(mnth).put(hour, timezone);
		}
		return returnMap;
	}

	public HashMap<String, Object> curPumpCheck(String ts, int pump_grp, LinkedHashMap<String, Integer> typeMap, boolean pre) {
		HashMap<String, Object> returnMap = new HashMap<>();
		HashMap<String, Object> pumpUseParam = new HashMap<>();
		pumpUseParam.put("targetDate", ts);

		pumpUseParam.put("pump_grp", pump_grp);


		HashMap<String, String> beforePumpUseMap = new HashMap<>();
		if (pre) {
			beforePumpUseMap = drvnMapper.getPreUsePumpString(pumpUseParam);
		} else {
			beforePumpUseMap = drvnMapper.getCurUsePumpString(pumpUseParam);
		}
		String beforePumpUse = null;
		String beforeFreqUse = null;


		if (beforePumpUseMap != null) {
			if (beforePumpUseMap.containsKey("PUMP_USE_RST")) {
				String value = beforePumpUseMap.get("PUMP_USE_RST");
				if (value != null && !value.trim().isEmpty()) {
					beforePumpUse = value;
				}
			}

			if (beforePumpUseMap.containsKey("SPI_USE_RST")) {
				String value = beforePumpUseMap.get("SPI_USE_RST");
				if (value != null && !value.trim().isEmpty()) {
					beforeFreqUse = value;
				}
			}
		}

		if (beforePumpUse != null && !beforePumpUse.isEmpty()) {
			String[] strArray = beforePumpUse.split(",");
			List<String> strList = Arrays.stream(strArray)
					.map(String::trim)
					.collect(Collectors.toList());
			List<String> combIvtPump = new ArrayList<>();
			for (String pump : strList) {
				if (wpp_code.equals("wm")) {
					if (pump.equals("1")) {
						combIvtPump.add("1");
						break;
					} else if (pump.equals("2")) {
						combIvtPump.add("2");
						break;
					} else if (pump.equals("4")) {
						combIvtPump.add("4");
						break;
					}
				} else {
					if (typeMap.containsKey(pump)) {
						if (typeMap.get(pump) == 2) {
							combIvtPump.add(pump);
						}
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
				returnMap.put("comb", strList);
				returnMap.put("freq", beforeFreqMap);

			}
		}
		return returnMap;
	}

	public Double baFreqCheck(String ts, Double agoFreq, Double sumFri) {
		Double firstFreq = agoFreq;
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
		//날짜 치환
		LocalDateTime dateTime = LocalDateTime.parse(ts, formatter);
		final double MIN_USING_FREQ = 48.0;
		final double MAX_USING_FREQ = 60.0;

		double nowMinLei = Double.MAX_VALUE;
		double agoMinLei = Double.MAX_VALUE;
		List<String> avgList = new ArrayList<>();

		avgList.add("892-480-LEI-8000");
		avgList.add("892-480-LEI-8001");
		HashMap<String, Object> rawAvgParam = new HashMap<>();
		LocalDateTime agoTs = dateTime.minusMinutes(10);
		String agoTsCast = agoTs.format(formatter);
		for (String lei : avgList) {
			rawAvgParam.put("tagname", lei);
			rawAvgParam.put("nowDateTime", ts);
			Double leiNowDb = drvnMapper.select5MinuteAvgRawData(rawAvgParam);
			if (leiNowDb != null && leiNowDb > 0) {
				if (leiNowDb < nowMinLei) {
					nowMinLei = leiNowDb;
				}
			}
			rawAvgParam.put("nowDateTime", agoTsCast);
			Double leiAgoDb = drvnMapper.select5MinuteAvgRawData(rawAvgParam);
			if (leiAgoDb != null && leiAgoDb > 0) {
				if (leiAgoDb < agoMinLei) {
					agoMinLei = leiAgoDb;
				}
			}
		}

		double result = (nowMinLei - agoMinLei) / agoMinLei;
		HashMap<String, Object> pumpMap = new HashMap<>();
		pumpMap.put("nowDate", ts);
		pumpMap.put("interval", 15);
		pumpMap.put("limit", 10);
		pumpMap.put("pump_grp", 1);
		pumpMap.put("pump_idx", 4);
		Set<Integer> freqSet = drvnMapper.inverterPumpFreqCheck(pumpMap);

		// 동일 주파수 10분간 유지
		if (freqSet.size() == 1) {
			if (Math.abs(result) > 0.3) {
				if (result > 0) {
					agoFreq = firstFreq - 2.0;
				} else {
					agoFreq = firstFreq + 2.0;
				}
				if (agoFreq < MIN_USING_FREQ) {
					agoFreq = MIN_USING_FREQ; // 최소 주파수는 48Hz
				} else if (agoFreq > MAX_USING_FREQ) {
					agoFreq = MAX_USING_FREQ; // 최대 주파수는 60Hz
				}
			} else {
				agoFreq = firstFreq;
			}
		} else {
			agoFreq = firstFreq;
		}
		return agoFreq;
	}

	/**
	 * 현재 조합 및 대수, 우선순위에 따라 저장된 펌프조합 가져옴
	 *
	 * @param pump_grp
	 * @param pump_count
	 * @param pump_priority
	 * @return
	 */
	public List<String> getPumpCombination(int pump_grp, double pump_count, int pump_priority) {
		HashMap<String, Object> combParam = new HashMap<>();
		if (wpp_code.equals("gs")) {
			combParam.put("pump_grp", 0);
		} else {
			combParam.put("pump_grp", pump_grp);
		}
		combParam.put("pump_count", pump_count);
		combParam.put("pump_priority", pump_priority);

		List<HashMap<String, Integer>> getComb = drvnMapper.getPumpCombination(combParam);
		List<String> returnComb = new ArrayList<>();

		for (HashMap<String, Integer> map : getComb) {
			int pump_idx = map.get("PUMP_IDX");
			String pump_idx_str = String.valueOf(pump_idx);
			returnComb.add(pump_idx_str);

		}


		return returnComb;
	}


}
