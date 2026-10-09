package com.wapplab.pms.kafka.producer;

import com.wapplab.pms.kafka.KafkaProperties;
import com.wapplab.pms.service.MainService;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Profile("gm2")
@Component
@PropertySource("classpath:application-${spring.profiles.active}.yaml")
public class KafkaProducerTasks2 {

	@Autowired
	private MainService mainService;

	@Value("${spring.kafka.bootstrap-servers1}")
	private String bootstrapServers1;
	@Value("${spring.kafka.bootstrap-servers2}")
	private String bootstrapServers2;


	@Scheduled(cron = "0 * * * * ?") // 매분마다 실행
	public void producerStart(){
		LocalDateTime currentTime = LocalDateTime.now();

		// 원하는 형식의 날짜 및 시간 문자열로 변환
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
		String formattedDateTime = currentTime.format(formatter);
		System.out.println("producerStart 현재 로컬 시간: "+formattedDateTime);

		Properties properties1 = new Properties();
		properties1.put("bootstrap.servers", bootstrapServers1);  // Kafka broker의 주소(properties 주소 설정에 따름)
		properties1.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
		properties1.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

		Properties properties2 = new Properties();
		properties2.put("bootstrap.servers", bootstrapServers2);  // Kafka broker의 주소(properties 주소 설정에 따름)
		properties2.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
		properties2.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

		List<HashMap<String, Object>> sendList = new ArrayList<>();
		List<Map<String, Object>> dataList = mainService.motorDataAllList();
		List<Map<String, Object>> motorAlarmDataList = mainService.motorAlarmList();

		//System.out.println("dataList: "+dataList.toString());
		//System.out.println("motorAlarmDataList: "+motorAlarmDataList.toString());

		List<Map<String, Object>> pumpInf = mainService.getPumpInfAllList();
		//System.out.println("pumpInf: "+pumpInf.toString());
		for(Map<String, Object> pumpItem : pumpInf)
		{

			//System.out.println("pumpItem: "+pumpItem.toString());
			int nowPumpIdx = Integer.parseInt(pumpItem.get("pump_idx").toString());
			for(Map<String, Object> item : dataList)
			{
				int nowPumpIdxItem = Integer.parseInt(item.get("pump_idx").toString());
				if(nowPumpIdx == nowPumpIdxItem)
				{
					//System.out.println("item: "+item.toString());
					String acq_date = item.get("acq_date").toString();
					if(item.get("motor_nde_rms_amp") != null) {
						HashMap<String, Object> motorNDESendItem = new HashMap<>();
						motorNDESendItem.put("tag", pumpItem.get("MOTOR_NDE_AMP_TAG").toString());
						motorNDESendItem.put("time", acq_date);
						motorNDESendItem.put("value", Double.parseDouble(item.get("motor_nde_rms_amp").toString()));
						sendList.add(motorNDESendItem);
					}
					if(item.get("motor_de_rms_amp") != null) {
						HashMap<String, Object> motorDESendItem = new HashMap<>();
						motorDESendItem.put("tag",pumpItem.get("MOTOR_DE_AMP_TAG").toString());
						motorDESendItem.put("time",acq_date);
						motorDESendItem.put("value",Double.parseDouble(item.get("motor_de_rms_amp").toString()));
						sendList.add(motorDESendItem);
					}
					if(item.get("pump_nde_rms_amp") != null) {
						HashMap<String, Object> pumpNDESendItem = new HashMap<>();
						pumpNDESendItem.put("tag", pumpItem.get("PUMP_NDE_AMP_TAG").toString());
						pumpNDESendItem.put("time", acq_date);
						pumpNDESendItem.put("value", Double.parseDouble(item.get("pump_nde_rms_amp").toString()));
						sendList.add(pumpNDESendItem);
					}
					if(item.get("pump_de_rms_amp") != null) {
						HashMap<String, Object> pumpDESendItem = new HashMap<>();
						pumpDESendItem.put("tag", pumpItem.get("PUMP_DE_AMP_TAG").toString());
						pumpDESendItem.put("time", acq_date);
						pumpDESendItem.put("value", Double.parseDouble(item.get("pump_de_rms_amp").toString()));
						sendList.add(pumpDESendItem);
					}
				}
			}

			for(Map<String, Object> alarmItem : motorAlarmDataList)
			{
				int nowAlarmIdx = Integer.parseInt(alarmItem.get("pump_idx").toString());
				System.out.println("alarmItem["+nowAlarmIdx+"/"+nowPumpIdx+"]: "+alarmItem.toString());

				if(nowAlarmIdx == nowPumpIdx)
				{
					if(alarmItem.get("motorAlram") != null) {
						HashMap<String, Object> motorAlarmSendItem = new HashMap<>();
						motorAlarmSendItem.put("tag", pumpItem.get("MOTOR_ALARM_TAG").toString());
						motorAlarmSendItem.put("time", alarmItem.get("ACQ_DATE").toString());
						motorAlarmSendItem.put("value", Double.parseDouble(alarmItem.get("motorAlram").toString()));
						sendList.add(motorAlarmSendItem);
					}

					if(alarmItem.get("pumpAlram") != null) {
						HashMap<String, Object> pumpAlarmSendItem = new HashMap<>();
						pumpAlarmSendItem.put("tag", pumpItem.get("PUMP_ALARM_TAG").toString());
						pumpAlarmSendItem.put("time", alarmItem.get("ACQ_DATE").toString());
						pumpAlarmSendItem.put("value", Double.parseDouble(alarmItem.get("pumpAlram").toString()));
						sendList.add(pumpAlarmSendItem);
					}
				}
			}
		}

		try (Producer<String, String> producer = new KafkaProducer<>(properties1)) {
			for (HashMap<String, Object> sendItem : sendList) {
				//System.out.println("sendItem1: "+sendItem.toString());
				producer.send(new ProducerRecord<>("pms_result", makeProducerJsonValue(sendItem)));
			}
			//System.out.println("producer send1 size: "+sendList.size());
			/*for (HashMap<String, Object> sendItem : sendStringList) {
				producer.send(new ProducerRecord<>("ems_result", makeProducerJsonStringValue(sendItem)));
			}*/
		} catch (Exception e) {
			e.printStackTrace();
		}

		try (Producer<String, String> producer = new KafkaProducer<>(properties2)) {
			for (HashMap<String, Object> sendItem : sendList) {
				//System.out.println("sendItem2: "+sendItem.toString());
				producer.send(new ProducerRecord<>("pms_result", makeProducerJsonValue(sendItem)));
			}
			System.out.println("producer send2 size: "+sendList.size());
			/*for (HashMap<String, Object> sendItem : sendStringList) {
				producer.send(new ProducerRecord<>("ems_result", makeProducerJsonStringValue(sendItem)));
			}*/
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	public String makeProducerJsonValue(HashMap<String, Object> item)
	{
		StringBuffer sb = new StringBuffer();
		sb.append("{");
		sb.append("\"tag\":").append("\"").append(item.get("tag").toString()).append("\"").append(",");
		sb.append("\"value\":").append(item.get("value").toString()).append(",");
		sb.append("\"time\":").append("\"").append(item.get("time").toString()).append("\"");
		sb.append("}");
		return sb.toString();
	}
	public String makeProducerJsonStringValue(HashMap<String, Object> item)
	{
		StringBuffer sb = new StringBuffer();
		sb.append("{");
		sb.append("\"tag\":").append("\"").append(item.get("tag").toString()).append("\"").append(",");
		sb.append("\"value\":").append("\"").append(item.get("value").toString()).append("\"").append(",");
		sb.append("\"time\":").append("\"").append(item.get("time").toString()).append("\"");
		sb.append("}");
		return sb.toString();
	}

}


