package com.wapplab.pms.kafka;

import java.text.ParseException;
import java.util.*;

import com.google.gson.Gson;
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
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;


@Profile("!dev & !gm2")
@Service
@PropertySource("classpath:application-${spring.profiles.active}.yaml")
public class KafkaConsumerService implements ApplicationListener<ApplicationReadyEvent> {

    @Autowired
    private AdminClient adminClient;

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

    private boolean testFlag = true;

    @KafkaListener(topics = "${kafka.topic.scada1.name}", groupId = "${kafka.group.scada1.id}",
            containerFactory="kafkaListenerContainerFactory", autoStartup= "true")
    public void scadaFirstListen(ConsumerRecord<String, String> record) {
        //System.out.printf("Consumed1 record with key %s and value %s%n", record.key(), record.value());
        if(testFlag)
        {
            System.out.println("scadaFirstListen:"+record.toString());
            testFlag = false;
        }
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
                if(consumerCount % 100 == 0)
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

    @KafkaListener(topics = "${kafka.topic.scada2.name}", groupId = "${kafka.group.scada2.id}",
            containerFactory="kafkaListenerContainerFactory", autoStartup= "true")
    public void scadaSecondListen(ConsumerRecord<String, String> record) {
        //System.out.printf("Consumed2 record with key %s and value %s%n", record.key(), record.value());
        //System.out.println("scadaSecondListen:"+record.toString());
        if(testFlag)
        {
            System.out.println("scadaSecondListen:"+record.toString());
            testFlag = false;
        }
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
    @KafkaListener(topics = "${kafka.topic.scada3.name}", groupId = "${kafka.group.scada3.id}",
            containerFactory="kafkaListenerContainerFactory2",autoStartup= "true")
    public void scadaIPCListen(ConsumerRecord<String, String> record) {
        System.out.printf("Consumed record with key %s%n", record.key());
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
                //processMessage(messageMap);
            }catch (Exception exception)
            {
                System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
                exception.printStackTrace();
            }
        }
    }
    @Override
    public void onApplicationEvent(ApplicationReadyEvent event) {
        System.out.println("onApplicationEvent Start");
        String status = getClusterStatus();
        System.out.println("kafkaStatus:" + status);

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

    public String getClusterStatus() {
        try {
            DescribeClusterResult describeClusterResult = adminClient.describeCluster();
            String clusterId = describeClusterResult.clusterId().get();
            int nodeCount = describeClusterResult.nodes().get().size();
            return String.format("Connected to Kafka cluster with cluster id: %s and %d nodes.", clusterId, nodeCount);
        } catch (Exception e) {
            return "Failed to connect to Kafka cluster: " + e.getMessage();
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




    private String findPumpScadaId(String tag) {
        if (kafkaTagList == null) {
            kafkaTagList = commonService.kafkaTagList();
        }
        for (HashMap<String, String> tagMap : kafkaTagList) {
            if (tagMap.containsValue(tag)) {
                String pumpScadaId = tagMap.get("PUMP_SCADA_ID");
                if (pumpScadaId != null && isPumpScadaIdInList(pumpScadaId)) {
                    return pumpScadaId;
                }
            }
        }
        return null;
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
            case "SUCTION_PRESSURE_TAG":
                scadaDto.setSUCTION_PRESSURE(Float.parseFloat(value.toString()));
                break;
            default:
                break;
        }
        tryCountValue++;
        scadaDto.setTryCount(tryCountValue);
    }

    private boolean isScadaDtoComplete(ScadaDto scadaDto) {
        if (scadaDto == null) {
            return false;
        }

        boolean isGosan = centerId.equals("gosan");
        String pumpScadaId = scadaDto.getPUMP_SCADA_ID();
        int tryCount = scadaDto.getTryCount();

        if (tryCount > 100) {
            return true;
        }

        boolean commonFieldsComplete =
                scadaDto.getEQ_ON() != -1 &&
                        scadaDto.getFREQUENCY() != -1 &&
                        scadaDto.getFLOW_RATE() != -1 &&
                        scadaDto.getPRESSURE() != -1 &&
                        scadaDto.getR_TEMP() != -1 &&
                        scadaDto.getBRG_MOTOR_DE_TEMP() != -1 &&
                        scadaDto.getBRG_MOTOR_NDE_TEMP() != -1 &&
                        scadaDto.getBRG_PUMP_DE_TEMP() != -1 &&
                        scadaDto.getDISCHARGE_PRESSURE() != -1;

        boolean additionalFieldsComplete =
                scadaDto.getS_TEMP() != -1 &&
                        scadaDto.getT_TEMP() != -1 &&
                        scadaDto.getBRG_PUMP_NDE_TEMP() != -1;


        if (!isGosan) {
            return commonFieldsComplete && additionalFieldsComplete;
        }

        if (isGosan &&
                (pumpScadaId.equals("pump_scada_09") ||
                        pumpScadaId.equals("pump_scada_10") ||
                        pumpScadaId.equals("pump_scada_11"))) {
            return commonFieldsComplete && additionalFieldsComplete;
        }


        boolean isSpecialPump = pumpScadaId.equals("pump_scada_08");
        if (isSpecialPump) {
            return commonFieldsComplete &&
                    scadaDto.getS_TEMP() != -1 &&
                    scadaDto.getT_TEMP() != -1;
        }

        boolean isRegularPump = pumpScadaId.matches("pump_scada_0[1-7]");
        if (isRegularPump) {
            return commonFieldsComplete &&
                    scadaDto.getBRG_PUMP_NDE_TEMP() != -1;
        }

        return false;
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
                        //System.out.println("targetDto:"+targetDto.toString());
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

                // 모든 DTO의 ACQ_DATE가 다른 경우 일괄 업데이트
                if (isScadaDtoDateDifferent(ts)) {
                    for (ScadaDto completedDto : currentDtoList) {
                        insertScadaDto(completedDto);
                    }
                    currentDtoList.clear();
                }
            }
        }
    }

    private void insertScadaDto(ScadaDto scadaDto) {
        // DB에 삽입하는 로직 (예제에서는 출력)
        //System.out.println("Inserting ScadaDto to DB: " + scadaDto);

        // -1 값을 null로 변환
        if (scadaDto.getEQ_ON() == -1) scadaDto.setEQ_ON(0);
        if (scadaDto.getFREQUENCY() == -1) scadaDto.setFREQUENCY(0);
        if (scadaDto.getFLOW_RATE() == -1) scadaDto.setFLOW_RATE(0);
        if (scadaDto.getPRESSURE() == -1) scadaDto.setPRESSURE(0);
        if (scadaDto.getR_TEMP() == -1) scadaDto.setR_TEMP(0);
        if (scadaDto.getS_TEMP() == -1) scadaDto.setS_TEMP(0);
        if (scadaDto.getT_TEMP() == -1) scadaDto.setT_TEMP(0);
        if (scadaDto.getBRG_MOTOR_DE_TEMP() == -1) scadaDto.setBRG_MOTOR_DE_TEMP(0);
        if (scadaDto.getBRG_MOTOR_NDE_TEMP() == -1) scadaDto.setBRG_MOTOR_NDE_TEMP(0);
        if (scadaDto.getBRG_PUMP_DE_TEMP() == -1) scadaDto.setBRG_PUMP_DE_TEMP(0);
        if (scadaDto.getBRG_PUMP_NDE_TEMP() == -1) scadaDto.setBRG_PUMP_NDE_TEMP(0);
        if (scadaDto.getDISCHARGE_PRESSURE() == -1) scadaDto.setDISCHARGE_PRESSURE(0);
        if (scadaDto.getSUCTION_PRESSURE() == -1) scadaDto.setSUCTION_PRESSURE(0);

        //System.out.println("Inserting ScadaDto to DB: " + scadaDto);
        commonService.insertScadaDto(scadaDto);
    }

    private boolean isScadaDtoDateDifferent(String acqDate) {
        for (ScadaDto dto : currentDtoList) {
            if (!dto.getACQ_DATE().equals(acqDate)) {
                return true;
            }
        }
        return false;
    }

}
