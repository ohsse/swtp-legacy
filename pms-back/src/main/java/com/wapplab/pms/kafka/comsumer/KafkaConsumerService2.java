package com.wapplab.pms.kafka.comsumer;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.wapplab.pms.service.CommonService;
import com.wapplab.pms.web.common.ScadaDto;
import org.apache.kafka.clients.admin.AdminClient;
import org.apache.kafka.clients.admin.DescribeClusterResult;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.lang.reflect.Type;
import java.text.ParseException;
import java.util.*;

@Profile("gm2")
@PropertySource("classpath:application-${spring.profiles.active}.yaml")
@Service
public class KafkaConsumerService2 implements ApplicationListener<ApplicationReadyEvent> {

    @Autowired
    private AdminClient adminClient1;

    @Autowired
    private AdminClient adminClient2;

    @Autowired
    private CommonService commonService;

    @Value("${kafka.topic.scada1.name}")
    private String kafka_topic_scada1;
    @Value("${kafka.topic.scada2.name}")
    private String kafka_topic_scada2;

    @Value("${kafka.centerId}")
    private String centerId;
    public int consumerCount = 0;
    private List<HashMap<String, String>> kafkaTagList;

    private List<ScadaDto> currentDtoList = new ArrayList<>();

    @KafkaListener(topics = "${kafka.topic.scada1.name}", groupId = "${kafka.group.scada1_1.id}",
            containerFactory = "kafkaListenerContainerFactory1", autoStartup= "true")
    public void scadaFirstListen1(ConsumerRecord<String, String> record) {
        consumerCount++;
        if(record.value() != null){
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap<String, Object> messageMap = new HashMap<>();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken<HashMap<String, Object>>(){}.getType();
                messageMap = gson.fromJson(jsonString, type);
                messageMap.put("server", kafka_topic_scada1);

                //insertMsgHashMap(messageMap);
                processMessage(messageMap);
                if(consumerCount % 100000 == 0)
                {
                    System.out.println("Consumed record Count value is"+record.value());
                    consumerCount = 0;
                }

            }catch (Exception exception)
            {
                System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
                exception.printStackTrace();
            }
        }
    }

    @KafkaListener(topics = "${kafka.topic.scada2.name}", groupId = "${kafka.group.scada1_2.id}",
            containerFactory = "kafkaListenerContainerFactory1", autoStartup= "true")
    public void scadaSecondListen1(ConsumerRecord<String, String> record) {
        //System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
        if(record.value() != null){
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap<String, Object> messageMap = new HashMap<>();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken<HashMap<String, Object>>(){}.getType();
                messageMap = gson.fromJson(jsonString, type);
                messageMap.put("server", kafka_topic_scada2);

                //insertMsgHashMap(messageMap);
                processMessage(messageMap);
            }catch (Exception exception)
            {
                System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
                exception.printStackTrace();
            }
        }
    }

    @KafkaListener(topics = "${kafka.topic.scada1.name}", groupId = "${kafka.group.scada2_1.id}",
            containerFactory = "kafkaListenerContainerFactory2", autoStartup= "true")
    public void scadaFirstListen2(ConsumerRecord<String, String> record) {
        consumerCount++;
        if(record.value() != null){
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap<String, Object> messageMap = new HashMap<>();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken<HashMap<String, Object>>(){}.getType();
                messageMap = gson.fromJson(jsonString, type);
                messageMap.put("server", kafka_topic_scada1);

                //insertMsgHashMap(messageMap);
                processMessage(messageMap);
                if(consumerCount % 100000 == 0)
                {
                    System.out.println("Consumed record Count value is"+record.value());
                    consumerCount = 0;
                }

            }catch (Exception exception)
            {
                System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
                exception.printStackTrace();
            }
        }
    }

    @KafkaListener(topics = "${kafka.topic.scada2.name}", groupId = "${kafka.group.scada2_1.id}",
            containerFactory = "kafkaListenerContainerFactory2", autoStartup= "true")
    public void scadaSecondListen2(ConsumerRecord<String, String> record) {
        //System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
        if(record.value() != null){
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap<String, Object> messageMap = new HashMap<>();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken<HashMap<String, Object>>(){}.getType();
                messageMap = gson.fromJson(jsonString, type);
                messageMap.put("server", kafka_topic_scada2);

                //insertMsgHashMap(messageMap);
                processMessage(messageMap);
            }catch (Exception exception)
            {
                System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
                exception.printStackTrace();
            }
        }
    }



    @KafkaListener(topics = "${kafka.topic.scada3.name}", groupId = "${kafka.group.scada3_1.id}",
            containerFactory = "kafkaListenerContainerFactory1", autoStartup= "true")
    public void scadaIPCListen1(ConsumerRecord<String, String> record) {
        //System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
        if(record.value() != null){
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap<String, Object> messageMap = new HashMap<>();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken<HashMap<String, Object>>(){}.getType();
                messageMap = gson.fromJson(jsonString, type);
                //messageMap.put("CENTER_ID", centerId);

                commonService.msgInsert(messageMap);
            }catch (Exception exception)
            {
                System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
                exception.printStackTrace();
            }
        }
    }

    @KafkaListener(topics = "${kafka.topic.scada3.name}", groupId = "${kafka.group.scada3_2.id}",
            containerFactory = "kafkaListenerContainerFactory2", autoStartup= "true")
    public void scadaIPCListen2(ConsumerRecord<String, String> record) {
        //System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
        if(record.value() != null){
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap<String, Object> messageMap = new HashMap<>();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken<HashMap<String, Object>>(){}.getType();
                messageMap = gson.fromJson(jsonString, type);
                //messageMap.put("CENTER_ID", centerId);

                commonService.msgInsert(messageMap);
            }catch (Exception exception)
            {
                System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
                exception.printStackTrace();
            }
        }
    }


    @Override
    public void onApplicationEvent(ApplicationReadyEvent event) {
        System.out.println("onApplicationEvent Start2");
        String status1 = getClusterStatus1();
        String status2 = getClusterStatus2();
        System.out.println("kafkaStatus2:" + status1 + "/"+status2);
    }
    public List<HashMap<String, String>> findKeyValue(String targetValue) {
        if (kafkaTagList == null) {
            kafkaTagList = commonService.kafkaTagList();
        }

        Optional<Map.Entry<String, String>> targetMapEntry = kafkaTagList.stream()
                .flatMap(map -> map.entrySet().stream())
                .filter(entry -> targetValue.equals(entry.getValue()))
                .findFirst();

        List<String> pumpScadaId = new ArrayList<>();
        for (HashMap<String, String> kafkaTag : kafkaTagList) {
            for (Map.Entry<String, String> entry : kafkaTag.entrySet()) {
                if (targetValue.equals(entry.getValue())) {

                    String pumpScadaIdValue = kafkaTag.get("PUMP_SCADA_ID");

                    if (pumpScadaIdValue != null) {
                        pumpScadaId.add(pumpScadaIdValue);
                        break;
                    }

                }
            }
        }

        List<HashMap<String, String>> returnList = new ArrayList<>();
        if (targetMapEntry.isPresent()) {
            Map.Entry<String, String> targetEntry = targetMapEntry.get();
            String targetKey = targetEntry.getKey();
            //System.out.println("targetKey: " + targetKey);

            for (String id : pumpScadaId) {
                //System.out.println("pumpScadaId: " + id);
                HashMap<String, String> returnMap = new HashMap<>();
                returnMap.put("targetKey", targetKey);
                returnMap.put("pumpScadaId", id);
                returnList.add(returnMap);
            }
            return returnList;
        }else{
            return null;
        }


    }
    public String getClusterStatus1() {
        try {
            DescribeClusterResult describeClusterResult = adminClient1.describeCluster();
            String clusterId = describeClusterResult.clusterId().get();
            int nodeCount = describeClusterResult.nodes().get().size();
            return String.format("Connected to Kafka1 cluster with cluster id: %s and %d nodes.", clusterId, nodeCount);
        } catch (Exception e) {
            return "Failed to connect to Kafka1 cluster: " + e.getMessage();
        }
    }

    public String getClusterStatus2() {
        try {
            DescribeClusterResult describeClusterResult = adminClient2.describeCluster();
            String clusterId = describeClusterResult.clusterId().get();
            int nodeCount = describeClusterResult.nodes().get().size();
            return String.format("Connected to Kafka2 cluster with cluster id: %s and %d nodes.", clusterId, nodeCount);
        } catch (Exception e) {
            return "Failed to connect to Kafka2 cluster: " + e.getMessage();
        }
    }


    public void insertMsgHashMap(HashMap<String, Object> messageMap) throws ParseException {
        String msgTag = messageMap.get("tagname").toString();
        String msgTs =  messageMap.get("timestamp").toString();
        List<HashMap<String, String>> returnList = findKeyValue(msgTag);
        if(returnList!=null){
            for(HashMap<String, String> map:returnList){
                messageMap.put("targetKey",map.get("targetKey"));
                messageMap.put("pumpScadaId", map.get("pumpScadaId"));
                messageMap.put("centerId", centerId);
                commonService.insertRawData(messageMap);

            }

        }
    }

    private boolean isPumpScadaIdInList(String pumpScadaId) {
        if (kafkaTagList == null) {
            kafkaTagList = commonService.kafkaTagList();
        }
        for (HashMap<String, String> tagMap : kafkaTagList) {
            if (pumpScadaId.equals(tagMap.get("PUMP_SCADA_ID"))) {
                return true;
            }
        }
        return false;
    }

    private void updateScadaDto(ScadaDto scadaDto, HashMap<String, Object> messageMap, String key, Object value) {
        //System.out.println("updateScadaDto:"+messageMap.toString());
        //System.out.println("key:"+key + ", value:"+value);
        int tryCountValue = scadaDto.getTryCount();

        switch (key) {
            case "EQ_ON_TAG":
                scadaDto.setEQ_ON((int)Double.parseDouble(value.toString()));
                break;
            case "FREQUENCY_TAG":
                scadaDto.setFREQUENCY(Float.parseFloat(value.toString()));
                break;
            case "FLOW_RATE_TAG":
                scadaDto.setFLOW_RATE(Float.parseFloat(value.toString()));
                break;
            case "PRESSURE_TAG":
                scadaDto.setPRESSURE(Float.parseFloat(value.toString()));
                break;
            case "R_TEMP_TAG":
                scadaDto.setR_TEMP(Float.parseFloat(value.toString()));
                break;
            case "S_TEMP_TAG":
                scadaDto.setS_TEMP(Float.parseFloat(value.toString()));
                break;
            case "T_TEMP_TAG":
                scadaDto.setT_TEMP(Float.parseFloat(value.toString()));
                break;
            case "BRG_MOTOR_DE_TEMP_TAG":
                scadaDto.setBRG_MOTOR_DE_TEMP(Float.parseFloat(value.toString()));
                break;
            case "BRG_MOTOR_NDE_TEMP_TAG":
                scadaDto.setBRG_MOTOR_NDE_TEMP(Float.parseFloat(value.toString()));
                break;
            case "BRG_PUMP_DE_TEMP_TAG":
                scadaDto.setBRG_PUMP_DE_TEMP(Float.parseFloat(value.toString()));
                break;
            case "BRG_PUMP_NDE_TEMP_TAG":
                scadaDto.setBRG_PUMP_NDE_TEMP(Float.parseFloat(value.toString()));
                break;
            case "DISCHARGE_PRESSURE_TAG":
                scadaDto.setDISCHARGE_PRESSURE(Float.parseFloat(value.toString()));
                break;
            /*case "SUCTION_PRESSURE_TAG":
                scadaDto.setSUCTION_PRESSURE(Float.parseFloat(value.toString()));
                break;*/
            default:
                break;
        }
        tryCountValue++;
        scadaDto.setTryCount(tryCountValue);
    }

    private boolean isScadaDtoComplete(ScadaDto scadaDto) {
        // 모든 필드가 -1이 아닌지 확인
        //System.out.println("isScadaDtoComplete:"+scadaDto.toString());
        return (scadaDto.getEQ_ON() != -1 &&
                scadaDto.getFREQUENCY() != -1 &&
                scadaDto.getFLOW_RATE() != -1 &&
                scadaDto.getPRESSURE() != -1 &&
                scadaDto.getR_TEMP() != -1 &&
                scadaDto.getS_TEMP() != -1 &&
                scadaDto.getT_TEMP() != -1 &&
                scadaDto.getBRG_MOTOR_DE_TEMP() != -1 &&
                scadaDto.getBRG_MOTOR_NDE_TEMP() != -1 &&
                scadaDto.getBRG_PUMP_DE_TEMP() != -1 &&
                scadaDto.getBRG_PUMP_NDE_TEMP() != -1 &&
                scadaDto.getDISCHARGE_PRESSURE() != -1 )||
                /*scadaDto.getSUCTION_PRESSURE() != -1 ||*/
                scadaDto.getTryCount() > 100;
    }

    private void processMessage(HashMap<String, Object> messageMap) {
        String ts = (String) messageMap.get("timestamp");
        String tag = (String) messageMap.get("tagname");
        Object value = messageMap.get("value");

        if (kafkaTagList == null) {
            kafkaTagList = commonService.kafkaTagList();
        }

        // 모든 PUMP_SCADA_ID 확인
        for (HashMap<String, String> tagMap : kafkaTagList) {
            String pumpScadaId = tagMap.get("PUMP_SCADA_ID");
            if (tagMap.containsValue(tag) && pumpScadaId != null) {
                ScadaDto targetDto = null;

                // 현재 시간대와 PUMP_SCADA_ID를 가진 ScadaDto 찾기
                for (ScadaDto dto : currentDtoList) {
                    if (dto.getACQ_DATE().equals(ts) && pumpScadaId.equals(dto.getPUMP_SCADA_ID())) {
                        targetDto = dto;
                        break;
                    }
                }

                // 해당하는 ScadaDto가 없으면 새로운 객체 생성
                if (targetDto == null) {
                    targetDto = new ScadaDto();
                    targetDto.setACQ_DATE(ts);
                    targetDto.setPUMP_SCADA_ID(pumpScadaId);
                    targetDto.setTryCount(0);
                    currentDtoList.add(targetDto);
                }

                // ScadaDto 업데이트
                for (Map.Entry<String, String> entry : tagMap.entrySet()) {
                    if (entry.getValue().equals(tag)) {
                        updateScadaDto(targetDto, messageMap, entry.getKey(), value);
                    }
                }

                // ScadaDto가 완성되면 DB에 삽입하고 currentDtoList에서 제거
                if (isScadaDtoComplete(targetDto)) {
                    currentDtoList.remove(targetDto);
                    insertScadaDto(targetDto);
                }
            }
        }
    }

    private void insertScadaDto(ScadaDto scadaDto) {
        // DB에 삽입하는 로직 (예제에서는 출력)
        //System.out.println("Inserting ScadaDto to DB: " + scadaDto);
        // 실제 DB 삽입 로직은 여기서 구현 (예: JDBC, JPA, MyBatis 등)
        commonService.insertScadaDto(scadaDto);
    }

}
