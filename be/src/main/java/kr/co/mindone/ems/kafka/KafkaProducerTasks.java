package kr.co.mindone.ems.kafka;
/**
 * kafka 2중화 구성변경으로 미사용
 */
import com.fasterxml.jackson.databind.ObjectMapper;
import kr.co.mindone.ems.ai.AiService;
import kr.co.mindone.ems.alarm.AlarmService;
import kr.co.mindone.ems.common.CommonService;
import kr.co.mindone.ems.pump.PumpService;
import lombok.extern.flogger.Flogger;
import org.apache.ibatis.annotations.Case;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.text.SimpleDateFormat;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

// !gu2 : 군산 섀도우는 읽기 전용이라 Kafka 를 쓰지 않는다. 운영과 같은 group.id 로
//        조인하면 파티션이 갈려 기존 앱이 SCADA 를 절반만 받는다(에러 없이 조용히).
@Profile("!dev & !gm2 & !hy2 & !hp2 & !ji2 & !gr & !wm & !gs & !gu & !gu2 & !ba & !ss")
@Component
@PropertySource("classpath:application-${spring.profiles.active}.properties")
public class KafkaProducerTasks {

	@Autowired
	private KafkaProperties kafkaProperties;
	@Autowired
	private AlarmService alarmService;

	@Autowired
	private CommonService commonService;

	@Autowired
	private AiService aiService;

	@Autowired
	private PumpService pumpService;

	@Value("${spring.profiles.active}")
    private String wpp_code;

	@Scheduled(cron = "0 * * * * ?") // 매분마다 실행
	public void producerStart(){
		LocalDateTime currentTime = LocalDateTime.now();

		// 원하는 형식의 날짜 및 시간 문자열로 변환
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
		String formattedDateTime = currentTime.format(formatter);
		System.out.println("현재 로컬 시간: "+formattedDateTime);
		Properties properties = new Properties();
		properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers());  // Kafka broker의 주소(properties 주소 설정에 따름)
		properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
		properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

		List<HashMap<String, Object>> sendList = new ArrayList<>();
		List<HashMap<String, Object>> sendStringList = new ArrayList<>();


		//전력 예측 결과 전송
		HashMap<String, Object> map = new HashMap<>();
		try {
			map.put("func_type","peakTimePrdctPwr");
			if(wpp_code.equals("GM"))
			{
				List<HashMap<String, Object>> prdctPwrList = aiService.peakTimePrdctPwrGM(map);
				sendList.addAll(prdctPwrList);
			}
//			else if(wpp_code.matches("hy|ji"))
//			{
//				List<HashMap<String, Object>> prdctPwrList = aiService.peakTimePrdctPwrAll(map);
//				//System.out.println("producerStart - prdctPwrList:"+prdctPwrList.toString());
//				sendList.addAll(prdctPwrList);
//			}
			else {
				List<HashMap<String, Object>> prdctPwrList = aiService.peakTimePrdctPwr(map);
				sendList.addAll(prdctPwrList);
			}


		}catch (Exception e){
			e.printStackTrace();
		}

		try {
			map.put("func_type","peakYn");
			List<HashMap<String, Object>> peakYnList = aiService.peakTimePrdctPwr(map);
			sendList.addAll(peakYnList);
		}catch (Exception e){
			e.printStackTrace();
		}

		try {
			map.put("func_type","peakTimePwr");
			List<HashMap<String, Object>> pwrList = aiService.peakTimePwr(map);
			sendList.addAll(pwrList);
		}catch (Exception e){
			e.printStackTrace();
		}

		//요금적용전력 전송
		try {
			List<HashMap<String, Object>> costPwrList = aiService.selectCostPwr();
			sendList.addAll(costPwrList);
		}catch (Exception e){
			e.printStackTrace();
		}
		//System.out.println("costPwrList:"+costPwrList.toString());

		//분석시간 전송
		try {
			List<HashMap<String, Object>> anlyTimeList = aiService.selectPrdctAnlyTime();
			sendStringList.addAll(anlyTimeList);
		}catch (Exception e){
			e.printStackTrace();
		}
		//System.out.println("sendStringList:"+sendStringList.toString());

		//펌프 분석결과 전송
		List<HashMap<String, Object>> pumpUsageList = null;
		try {
			pumpUsageList = aiService.pumpUsageList();
			for (HashMap<String, Object> pumpAlGrpItem : pumpUsageList) {
				int pump_grp = Integer.parseInt(pumpAlGrpItem.get("PUMP_GRP").toString());

				if (pump_grp == 1) {
					HashMap<String, Object> pumpMap = new HashMap<>();
					pumpMap.put("pump_grp", pump_grp);
					pumpMap.put("data_type", "fri");

					try {
						pumpMap.put("func_type", "PumpPrdctFriTime" + pump_grp);
						List<HashMap<String, Object>> pumpFriList = aiService.selectPumpPrdctScadaList(pumpMap);
						sendList.addAll(pumpFriList);
					} catch (Exception e) {
						e.printStackTrace();
					}

					try {
						pumpMap.put("func_type", "PumpPrdctPriTime" + pump_grp);
						pumpMap.put("data_type", "pri");
						List<HashMap<String, Object>> pumpPriList = aiService.selectPumpPrdctScadaList(pumpMap);
						sendList.addAll(pumpPriList);
					} catch (Exception e) {
						e.printStackTrace();
					}

					try {
						pumpMap.put("func_type", "PumpPrdctPwrTime" + pump_grp);
						pumpMap.put("data_type", "pwr");
						List<HashMap<String, Object>> pumpPwrList = aiService.selectPumpPrdctScadaList(pumpMap);
						sendList.addAll(pumpPwrList);
					} catch (Exception e) {
						e.printStackTrace();
					}

					try {
						pumpMap.put("func_type", "pumpAnlyFir" + pump_grp);
						pumpMap.put("data_type", "fri");
						List<HashMap<String, Object>> pumpFriItem = aiService.selectPumpPrdctScadaOne(pumpMap);
						sendList.addAll(pumpFriItem);
					} catch (Exception e) {
						e.printStackTrace();
					}

					try {
						pumpMap.put("func_type", "pumpAnlyPri" + pump_grp);
						pumpMap.put("data_type", "pri");
						List<HashMap<String, Object>> pumpPriItem = aiService.selectPumpPrdctScadaOne(pumpMap);
						sendList.addAll(pumpPriItem);
					} catch (Exception e) {
						e.printStackTrace();
					}

					try {
						pumpMap.put("func_type", "pumpAnlyPwr" + pump_grp);
						pumpMap.put("data_type", "pwr");
						List<HashMap<String, Object>> pumpPwrItem = aiService.selectPumpPrdctScadaOne(pumpMap);
						sendList.addAll(pumpPwrItem);
					} catch (Exception e) {
						e.printStackTrace();
					}
				}
			}
		} catch (Exception e) {
			e.printStackTrace();
		}
		// 산성은 이후 펌프조합 생겼을 시 제거
		if (!wpp_code.matches("gm2|hy|hp|ji|ss")) {
			//펌프조합 운전결과 전송
			try {
				//selectGrpPrdctPumpCombYn
				HashMap<String, Object> tempItem = new HashMap<>();
				tempItem.put("PUMP_GRP_LIST", pumpService.selectPumpGrpListStr());
				List<HashMap<String, Object>> aiPumpEMSYnDataList = pumpService.selectPumpPrdctNowOnOffList(tempItem);

				//tempItem.put("ROW","BEFORE");
				//List<HashMap<String, Object>> beforePrdctList = pumpService.selectPumpPrdctNowOnOffList(tempItem);

				List<HashMap<String, Object>> nowRunPrdctList = pumpService.selectPumpPrdctOnOffLastList(tempItem);

				String nowRunPrdctTime = "";

				if(!nowRunPrdctList.isEmpty())
				{
					nowRunPrdctTime = nowRunPrdctList.get(0).get("PRDCT_TIME").toString();
					for (HashMap<String, Object> nowPrdctItem : aiPumpEMSYnDataList) {
						/*for (HashMap<String, Object> beforePrdctItem : beforePrdctList) {
							String nowPumpIdx = nowPrdctItem.get("PUMP_IDX").toString();
							String beforePumpIdx = beforePrdctItem.get("PUMP_IDX").toString();

							if (nowPumpIdx.equals(beforePumpIdx)) {
								String nowPumpYn = nowPrdctItem.get("PUMP_YN").toString();
								String beforePumpYn = beforePrdctItem.get("PUMP_YN").toString();

								//System.out.println("nowPrdctItem:"+nowPrdctItem.toString());
								//System.out.println("beforePrdctItem:"+beforePrdctItem.toString());

								if (!nowPumpYn.equals(beforePumpYn)) {

									if(nowRunPrdctTime.isEmpty()){
										// 변화된 펌프조합 업데이트
										pumpService.updatePumpYnFlagInit();
										pumpService.updatePumpYnFlag(aiPumpEMSYnDataList);
										break;

									}
									else {
										String nowPrdctTime = nowPrdctItem.get("PRDCT_TIME").toString();
										if(pumpService.checkTimeDifference(nowRunPrdctTime, nowPrdctTime, 30) )
										{
											pumpService.updatePumpYnFlagInit();
											// 기존 펌프 조합 초기화
											//pumpService.updatePumpYnFlag(nowRunPrdctList);
											// 변화된 펌프조합 업데이트
											pumpService.updatePumpYnFlag(aiPumpEMSYnDataList);
											break;
										}
										break;
									}
								}
							}
						}*/
						sendList.addAll(aiService.aiPumpEMSYnData(nowPrdctItem));
					}
				}
				//else{
					//기존 추천조합이 없는 경우 현재 상태를 FLAG 1로 저장
				//	pumpService.updatePumpYnFlagInit();
				//	pumpService.updatePumpYnFlag(aiPumpEMSYnDataList);
				//}
				//List<HashMap<String, Object>> aiPumpEMSYnDataList = drvnService.selectGrpPrdctPumpCombYnAllList();
				//System.out.println("beforePrdctList init Size:"+beforePrdctList.size());

				//System.out.println("#aiPumpEMSYnDataList:" + aiPumpEMSYnDataList.toString());
				//System.out.println("#beforePrdctList:" + beforePrdctList.toString());
			} catch (Exception e) {
				e.printStackTrace();
			}

			try {
				//펌프 그룹 AI 운영모드 상태 전송
				List<HashMap<String, Object>> pumpAIUsage = aiService.getPumpAiUsage();
				sendList.addAll(pumpAIUsage);

				for (int i = 1; i <= pumpUsageList.size(); i++) {
					try {
						List<HashMap<String, Object>> pumpAnlyOptResultList = aiService.selectPumpAnlyOptResult(i);
						sendStringList.addAll(pumpAnlyOptResultList);
					} catch (Exception e) {
						e.printStackTrace();
					}
				}
			} catch (Exception e) {
				e.printStackTrace();
			}

			try {
				//펌프 비상정지 유무 전송
				List<HashMap<String, Object>> emergencyResult = aiService.getEmergencyUse();
				sendList.addAll(emergencyResult);
			} catch (Exception e) {
				e.printStackTrace();
			}
		}
		try {
			//절감량 전송
			List<HashMap<String, Object>> savingResultList = aiService.selectSavingResult();
			sendList.addAll(savingResultList);
		} catch (Exception e) {
			e.printStackTrace();
		}

		try {
			//배수지 최소관압 전송
			List<HashMap<String, Object>> tnkMinPri = aiService.getTnkMinPri();
			sendList.addAll(tnkMinPri);
		} catch (Exception e) {
			e.printStackTrace();
		}

		try {
			//정수장 최소관압 전송
			List<HashMap<String, Object>> waterMinPri = aiService.getWaterMinPri();
			sendList.addAll(waterMinPri);
		} catch (Exception e) {
			e.printStackTrace();
		}




		try (Producer<String, String> producer = new KafkaProducer<>(properties)) {
			for (HashMap<String, Object> sendItem : sendList) {
				String msg = commonService.makeProducerJsonValue(sendItem);
				if(!msg.equals("None"))
				{
					producer.send(new ProducerRecord<>("ems_result", msg));
				}

			}
			for (HashMap<String, Object> sendItem : sendStringList) {
				String msg = commonService.makeProducerJsonStringValue(sendItem);
				if(!msg.equals("None"))
				{
					producer.send(new ProducerRecord<>("ems_result", msg));
				}

			}
		} catch (Exception e) {
			e.printStackTrace();
		}
	}



}
