package kr.co.mindone.ems.kafka.consumer;
/**
 * packageName    : kr.co.mindone.ems.kafka.consumer
 * fileName       : KafkaConsumerService
 * date           : 24. 9. 23.
 * description    : Kafka 메시지 소비를 처리하는 서비스 클래스
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        -            최초 생성
 */
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import kr.co.mindone.ems.ai.AiService;
import kr.co.mindone.ems.common.CommonService;
import org.apache.kafka.clients.admin.AdminClient;
import org.apache.kafka.clients.admin.DescribeClusterResult;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.lang.reflect.Type;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

import static kr.co.mindone.ems.kafka.KafkaConfig.*;

@Profile({
        "gm2",
        "hy2",
        "hp2",
        "ji2",
        "gr",
        "wm",
        "gs",
        "gu",
        "ba",
        "ss"
})
@Service
@PropertySource("classpath:application-${spring.profiles.active}.properties")
public class KafkaConsumerService implements ApplicationListener < ApplicationReadyEvent > {

    @Autowired
    @Qualifier("adminClient1")
    private AdminClient adminClient1;

    @Autowired
    @Qualifier("adminClient2")
    private AdminClient adminClient2;

    @Autowired
    private CommonService commonService;

    @Autowired
    private AiService aiService;

    @Value("${kafka.topic.scada1.name}")
    private String kafka_topic_scada1;

    @Value("${kafka.topic.scada2.name}")
    private String kafka_topic_scada2;

    private List < HashMap < String,
            Object >> wppTagList;
    private List < HashMap < String,
            Object >> EMSTagList;
    public int consumerCount = 0;

    @Value("${spring.profiles.active}")
    private String wpp_code;

    // 전력 합산을 위한 임시 저장소
    private ConcurrentHashMap<String, HashMap<String, Object>> powerDataBuffer = new ConcurrentHashMap<>();
    // 전력량 합산을 위한 임시 저장소
    private ConcurrentHashMap<String, HashMap<String, Object>> energyDataBuffer = new ConcurrentHashMap<>();

    // 합산에 사용될 전력 태그 목록
    private static final Set<String> POWER_TAGS_TO_SUM = new HashSet<>(Arrays.asList(
            "701-367-PWI-2001", "701-367-PWI-2401", "701-367-PWI-4001",
            "701-367-PWI-4033", "701-367-PWI-4041", "701-367-PWI-4057"
    ));

    // 합산에 사용될 전력량 태그 목록
    private static final Set<String> ENERGY_TAGS_TO_SUM = new HashSet<>(Arrays.asList(
            "701-367-PWQ-2001", "701-367-PWQ-2401", "701-367-PWQ-4001",
            "701-367-PWQ-4033", "701-367-PWQ-4041", "701-367-PWQ-4057"
    ));
    // ⭐ 태그별 단위 정보를 하드코딩
    private static final HashMap<String, Double> PWI_UNIT_VALUES = new HashMap<>();
    private static final HashMap<String, Double> PWQ_UNIT_VALUES = new HashMap<>();
    static {
        // PWI 태그 단위 (kW -> kW이므로 1.0)
        PWI_UNIT_VALUES.put("701-367-PWI-2001", 1.0);
        PWI_UNIT_VALUES.put("701-367-PWI-2401", 1.0);
        PWI_UNIT_VALUES.put("701-367-PWI-4001", 1.0);
        PWI_UNIT_VALUES.put("701-367-PWI-4033", 0.1);
        PWI_UNIT_VALUES.put("701-367-PWI-4041", 1.0);
        PWI_UNIT_VALUES.put("701-367-PWI-4057", 0.001);

        // PWQ 태그 단위 (kWh -> kWh이므로 1.0)
        PWQ_UNIT_VALUES.put("701-367-PWQ-2001", 1000.0);
        PWQ_UNIT_VALUES.put("701-367-PWQ-2401", 1000.0);
        PWQ_UNIT_VALUES.put("701-367-PWQ-4001", 1000.0);
        PWQ_UNIT_VALUES.put("701-367-PWQ-4033", 10.0);
        PWQ_UNIT_VALUES.put("701-367-PWQ-4041", 0.001);
        PWQ_UNIT_VALUES.put("701-367-PWQ-4057", 0.0001);
    }
    /**
     * Kafka 메시지를 소비하는 첫 번째 리스너 (첫 번째 Kafka 클러스터)
     *
     * @param record Kafka ConsumerRecord
     */
    @KafkaListener(topics = "${kafka.topic.scada1.name}", groupId = "${kafka.group.scada1_1.id}",
            containerFactory = "kafkaListenerContainerFactory1", autoStartup = "true")
    public void scadaFirstListen(ConsumerRecord < String, String > record) {
        //System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
        consumerCount++;
        if (record.value() != null) {
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap < String, Object > messageMap = new HashMap < > ();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken < HashMap < String, Object >> () {}.getType();
                messageMap = gson.fromJson(jsonString, type);
                messageMap.put("server", kafka_topic_scada1);

                insertMsgHashMap(messageMap);

                if (consumerCount % 100000 == 0) {
                    System.out.println("Consumed record Count value is" + record.value());
                    consumerCount = 0;
                }

            } catch (Exception exception) {

                exception.printStackTrace();
            }
        }
    }

    /*@KafkaListener(topics = "${kafka.topic.name}", groupId = "${kafka.new.group.id}", containerFactory = "earliestContainerFactory", autoStartup= "false")
    public void listenFromBeginning(ConsumerRecord<String, String> record) {
        // ... 최초 데이터 획득 처리 로직
    }*/

    /**
     * Kafka 메시지를 소비하는 두 번째 리스너 (첫 번째 Kafka 클러스터)
     *
     * @param record Kafka ConsumerRecord
     */
    @KafkaListener(topics = "${kafka.topic.scada2.name}", groupId = "${kafka.group.scada1_2.id}",
            containerFactory = "kafkaListenerContainerFactory1", autoStartup = "true")
    public void scadaSecondListen(ConsumerRecord < String, String > record) {
        //System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
        if (record.value() != null) {
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap < String, Object > messageMap = new HashMap < > ();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken < HashMap < String, Object >> () {}.getType();
                messageMap = gson.fromJson(jsonString, type);
                messageMap.put("server", kafka_topic_scada2);

                insertMsgHashMap(messageMap);
            } catch (Exception exception) {

                exception.printStackTrace();
            }
        }
    }

    /**
     * Kafka 메시지를 소비하는 첫 번째 리스너 (두 번째 Kafka 클러스터)
     *
     * @param record Kafka ConsumerRecord
     */
    @KafkaListener(topics = "${kafka.topic.scada1.name}", groupId = "${kafka.group.scada2_1.id}",
            containerFactory = "kafkaListenerContainerFactory2", autoStartup = "true")
    public void scadaFirstListen2(ConsumerRecord < String, String > record) {
        //System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
        consumerCount++;
        if (record.value() != null) {
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap < String, Object > messageMap = new HashMap < > ();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken < HashMap < String, Object >> () {}.getType();
                messageMap = gson.fromJson(jsonString, type);
                messageMap.put("server", kafka_topic_scada1);

                insertMsgHashMap(messageMap);

                if (consumerCount % 100000 == 0) {
                    System.out.println("Consumed2 record Count value is" + record.value());
                    consumerCount = 0;
                }

            } catch (Exception exception) {

                exception.printStackTrace();
            }
        }
    }

    /*@KafkaListener(topics = "${kafka.topic.name}", groupId = "${kafka.new.group.id}", containerFactory = "earliestContainerFactory", autoStartup= "false")
    public void listenFromBeginning(ConsumerRecord<String, String> record) {
        // ... 최초 데이터 획득 처리 로직
    }*/

    /**
     * Kafka 메시지를 소비하는 두 번째 리스너 (두 번째 Kafka 클러스터)
     *
     * @param record Kafka ConsumerRecord
     */
    @KafkaListener(topics = "${kafka.topic.scada2.name}", groupId = "${kafka.group.scada2_2.id}",
            containerFactory = "kafkaListenerContainerFactory2", autoStartup = "true")
    public void scadaSecondListen2(ConsumerRecord < String, String > record) {
        //System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
        if (record.value() != null) {
            // Gson 객체 생성
            Gson gson = new Gson();
            // Json 문자열 -> Map
            HashMap < String, Object > messageMap = new HashMap < > ();
            try {
                String jsonString = record.value().toString(); // record.value().toString()를 가정
                Type type = new TypeToken < HashMap < String, Object >> () {}.getType();
                messageMap = gson.fromJson(jsonString, type);
                messageMap.put("server", kafka_topic_scada2);

                insertMsgHashMap(messageMap);
            } catch (Exception exception) {

                exception.printStackTrace();
            }
        }
    }

    /**
     * ApplicationReadyEvent가 발생했을 때 호출되는 메서드
     *
     * @param event 어플리케이션 준비 완료 이벤트
     */
    @Override
    public void onApplicationEvent(ApplicationReadyEvent event) {
        System.out.println("onApplicationEvent Start2");
        String status1 = getClusterStatus1();
        String status2 = getClusterStatus2();

        System.out.println("kafkaStatus:" + status1 + "/" + status2);
        HashMap < String, Object > params = new HashMap < > ();
        wppTagList = commonService.selectWppTagList(params);
        EMSTagList = commonService.selectEMSConsumerTag();
    }

    /**
     * Kafka 클러스터 1의 AdminClient를 사용해 클러스터 상태를 조회하는 메서드
     *
     * @return 클러스터 ID와 노드 수 정보
     */
    public String getClusterStatus1() {
        try {
            DescribeClusterResult describeClusterResult = adminClient1.describeCluster();
            String clusterId = describeClusterResult.clusterId().get();
            int nodeCount = describeClusterResult.nodes().get().size();
            return String.format("Connected1 to Kafka cluster with cluster id: %s and %d nodes.", clusterId, nodeCount);
        } catch (Exception e) {
            return "Failed to connect to Kafka1 cluster: " + e.getMessage();
        }
    }

    /**
     * Kafka 클러스터 2의 AdminClient를 사용해 클러스터 상태를 조회하는 메서드
     *
     * @return 클러스터 ID와 노드 수 정보
     */
    public String getClusterStatus2() {
        try {
            DescribeClusterResult describeClusterResult = adminClient2.describeCluster();
            String clusterId = describeClusterResult.clusterId().get();
            int nodeCount = describeClusterResult.nodes().get().size();
            return String.format("Connected2 to Kafka cluster with cluster id: %s and %d nodes.", clusterId, nodeCount);
        } catch (Exception e) {
            return "Failed to connect to Kafka2 cluster: " + e.getMessage();
        }
    }

    /**
     * Kafka 메시지를 HashMap으로 변환 후 처리하는 메서드
     *
     * @param messageMap Kafka에서 수신한 메시지 정보
     * @throws ParseException 메시지의 시간 정보를 처리 중 발생하는 예외
     */
    public void insertMsgHashMap(HashMap < String, Object > messageMap) throws ParseException {
        String msgTag = messageMap.get("tagname").toString();
        String originTs = messageMap.get("timestamp").toString();
        // Define the formatter for the input timestamp string
        DateTimeFormatter inputFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        // Parse the string into a LocalDateTime
        LocalDateTime localDateTime = LocalDateTime.parse(originTs, inputFormatter);

        // Convert LocalDateTime to ZonedDateTime in Asia/Seoul
        ZonedDateTime kstTime = localDateTime.atZone(ZoneId.of("Asia/Seoul"));
        String msgTs = kstTime.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        messageMap.put("timestamp", msgTs);
        if (wppTagList == null) {
            HashMap < String, Object > params = new HashMap < > ();
            wppTagList = commonService.selectWppTagList(params);
        }

        boolean tagValueExists = wppTagList.stream()
                .map(map -> map.get("TAG")) // "tag" 키에 대한 값만 추출
                .anyMatch(msgTag::equals); // 찾고자 하는 값과 일치하는지 확인
        //tagValueExists를 통해 전송받은 tag가 DB에 정의되어 있는지 확인
        if (tagValueExists) {
            if (msgTag.contains("-EMS-")) {
                String func_type = findEMSFunctionType(msgTag);
                //System.out.println("EMS태그 FUNC_TYP : "+func_type);
                if (func_type != null) {
                    if (func_type.contains("pumpAnlyOptStop")) {
                        emsEmergency(messageMap, func_type);
                    }
                }
            }

            if (wpp_code.equals("wm")) {
                //운문 정수장 인버터 펌프 판별
                if (msgTag.contains("-IVC-4001")) {
                    syncPumpType(messageMap);
                }

                //운문 정수장 동기화 실패 확인
                if (msgTag.contains("-IVB-4008")) {
                    syncPumpFailedCheck(messageMap);
                }

                //운문 정수장 펌프 / 토출 밸브 연동운전 확인
                if ((msgTag.contains("565-340-CBK-4003") || msgTag.contains("565-340-CBK-4007") ||
                        msgTag.contains("565-340-CBK-4011") || msgTag.contains("565-340-CBK-4511"))) {
                    syncPumpCtrModeCheck(messageMap);
                }
            }

            if (wpp_code.equals("gs")) {
                // 전력 합산 로직
                if (POWER_TAGS_TO_SUM.contains(msgTag)) {
                    processTagData(messageMap, powerDataBuffer, POWER_TAGS_TO_SUM, "301-367-PWI-0000");
                }
                // 전력량 합산 로직
                if (ENERGY_TAGS_TO_SUM.contains(msgTag)) {
                    processTagData(messageMap, energyDataBuffer, ENERGY_TAGS_TO_SUM, "301-367-PWQ-0000");
                }
            }



            String resultTimeType = checkMsgTime(msgTs);

            if (!TIME_SEC.equals(resultTimeType)) {
                messageMap.put("type", "all");
                //System.out.println("resultTimeType:"+resultTimeType+" scadaDto:"+scadaDto.toString());
                commonService.insertRawData(messageMap);
            }

            if (TIME_MIN.equals(resultTimeType)) {
                messageMap.put("type", "min");
                commonService.insertRawData(messageMap);
            }

            if (TIME_HOUR.equals(resultTimeType)) {
                messageMap.put("type", "hour");
                commonService.insertRawData(messageMap);
                messageMap.put("type", "min");
                commonService.insertRawData(messageMap);

                String nowTagName = messageMap.get("tagname").toString();
                double nowValue = Double.parseDouble(messageMap.get("value").toString());
                HashMap < String, Object > ohMaps = new HashMap < > ();
                ohMaps.put("date", msgTs);
                List < HashMap < String, Object >> oneHourBeforeList = commonService.oneHourBeforeList(ohMaps);

                if (nowTagName.matches(".*-(PWQ|PWI|VOI|FRQ|SWI|FIQ)-.*")) {
                    for (HashMap < String, Object > maps: oneHourBeforeList) {
                        String beforeTagName = maps.get("tagname").toString();
                        if (nowTagName.equals(beforeTagName)) {
                            double beforeValue = Double.parseDouble(maps.get("value").toString());
                            double tempSumValue = 0.0;
                            tempSumValue = nowValue - beforeValue;
                            if (tempSumValue < 0) {
                                tempSumValue = 0.0;
                            }
                            messageMap.put("value", tempSumValue);
                            messageMap.put("type", "sum");
                            //System.out.println(scadaDtoTemp.toString());
                            commonService.insertRawData(messageMap);
                        }
                    }
                }

            }

        }
    }

    /**@apiNote
     * EMS Consumer태그의 TB_WPP_TAG_CODE상에 명세돼 있는 FUNC_TYP를 탐색
     * @param tagValue Kafka EMS tag
     * @return EMS TAG FUNC_TYP
     */
    public String findEMSFunctionType(String tagValue) {
        if (EMSTagList == null) {
            EMSTagList = commonService.selectEMSConsumerTag();
        }
        for (HashMap < String, Object > entry: EMSTagList) {
            if (tagValue.equals(entry.get("TAG"))) {
                return (String) entry.get("FUNC_TYP");
            }
        }
        return null; // TAG에 해당하는 데이터를 찾지 못한 경우
    }

    /**
     * EMS 비상 정지 상태를 처리하는 메서드
     *
     * @param messageMap 메시지 정보
     * @param funcTyp 기능 타입
     */
    public void emsEmergency(HashMap < String, Object > messageMap, String funcTyp) {
        HashMap < String, Object > updateMap = new HashMap < > ();
        String pumpGrpIdx = String.valueOf(funcTyp.charAt(funcTyp.length() - 1));
        updateMap.put("pump_grp", pumpGrpIdx);
        double statusDoubleValue = Double.parseDouble(messageMap.get("value").toString());
        int statusValue = (int) statusDoubleValue;
        //System.out.println("messageMap:"+messageMap);
        //System.out.println("funcTyp"+funcTyp);
        //System.out.println("funcTyp.contains(Btn)"+funcTyp.contains("Btn"));
        if (funcTyp.contains("Btn")) {
            if (statusValue == 1) {
                updateMap.put("statusValue", "1");
                commonService.updateEmergencyStatus(updateMap);
                HashMap < String, Object > map = new HashMap < > ();
                map.put("PUMP_GRP", pumpGrpIdx);
                map.put("STATUS", "2");
                aiService.updateAiStatus(map);
            }
        } else if (funcTyp.contains("Off")) {
            if (statusValue == 1) {
                updateMap.put("statusValue", "0");
                commonService.updateEmergencyStatus(updateMap);
                HashMap < String, Object > map = new HashMap < > ();
                map.put("PUMP_GRP", pumpGrpIdx);
                map.put("STATUS", "2");
            }
        }
    }

    /**
     * 메시지의 시간을 분석하여 시간 유형을 반환하는 메서드
     *
     * @param msgTs 메시지의 타임스탬프
     * @return 시간 유형 (all, hour, min, sec)
     * @throws ParseException 시간 파싱 중 발생하는 예외
     */
    public String checkMsgTime(String msgTs) throws ParseException {
        String resultTimeType;
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        Date date = sdf.parse(msgTs);

        SimpleDateFormat minuteFormat = new SimpleDateFormat("mm");
        SimpleDateFormat secondFormat = new SimpleDateFormat("ss");

        String minute = minuteFormat.format(date);
        String second = secondFormat.format(date);

        if (second.equals("00")) {
            if (minute.equals("00")) {
                resultTimeType = TIME_HOUR;
            } else if (minute.equals("15") || minute.equals("30") || minute.equals("45")) {
                resultTimeType = TIME_MIN;
            } else {
                resultTimeType = TIME_ALL;
            }
        } else {
            resultTimeType = TIME_SEC;
        }

        return resultTimeType;
    }

    /**
     * 운문 인버터 펌프 타입을 동기화하는 메서드
     *
     * @param messageMap 메시지 정보
     */
    public void syncPumpType(HashMap < String, Object > messageMap) {

        int[] pumpList = new int[] {
                1,
                2,
                3,
                4
        };
        int nowValue = 0;
        if (messageMap.get("value") != null) {
            nowValue = (int) Double.parseDouble(messageMap.get("value").toString());
        }
        //System.out.println("syncPumpType - nowValue:"+nowValue + "/" +messageMap.get("value").toString());
        for (int j: pumpList) {
            if (j == nowValue) {
                messageMap.put("type", 2);
                messageMap.put("pump_idx", j);
                commonService.updatePumpType(messageMap);
            } else {
                messageMap.put("type", 1);
                messageMap.put("pump_idx", j);
                commonService.updatePumpType(messageMap);
            }
        }
    }

    /**
     * 운문 펌프 동기화 실패 여부를 확인하는 메서드
     *
     * @param messageMap 메시지 정보
     */
    public void syncPumpFailedCheck(HashMap < String, Object > messageMap) {

        int nowValue = 0;
        if (messageMap.get("value") != null) {
            nowValue = (int) Double.parseDouble(messageMap.get("value").toString());

            messageMap.put("check_value", nowValue);
            commonService.updatePumpSyncCheck(messageMap);

            if (nowValue == 1) {
                //AI분석모드로 변경
                HashMap < String, Object > updateParam = new HashMap < > ();
                updateParam.put("STATUS", 2);
                updateParam.put("PUMP_GRP", 1);

                aiService.updateAiStatus(updateParam);
            }
        }
    }

    /**
     * 운문 제어 모드를 확인하는 메서드
     *
     * @param messageMap 메시지 정보
     */
    public void syncPumpCtrModeCheck(HashMap < String, Object > messageMap) {

        int nowValue = 0;
        if (messageMap.get("value") != null) {
            nowValue = (int) Double.parseDouble(messageMap.get("value").toString());
            if (nowValue == 0) {
                //AI분석모드로 변경
                HashMap < String, Object > updateParam = new HashMap < > ();
                updateParam.put("STATUS", 2);
                updateParam.put("PUMP_GRP", 1);
                aiService.updateAiStatus(updateParam);
            }
        }
    }
    /**
     * 특정 태그 데이터들을 버퍼에 저장하고, 모든 태그가 수신되면 합산하여 DB에 저장하는 메서드
     *
     * @param messageMap 현재 수신된 메시지 맵
     * @param bufferMap  데이터를 임시로 저장할 버퍼 맵
     * @param tagsToSum  합산 대상 태그 목록
     * @param newTagName 새로 생성될 임시 태그 이름
     */
    @SuppressWarnings("unchecked")
    private void processTagData(HashMap<String, Object> messageMap, ConcurrentHashMap<String, HashMap<String, Object>> bufferMap, Set<String> tagsToSum, String newTagName) throws ParseException {
        String msgTag = (String) messageMap.get("tagname");
        String timestamp = (String) messageMap.get("timestamp");
        String server = (String) messageMap.get("server");
        String quality = (String) messageMap.get("quality");

        bufferMap.computeIfAbsent(timestamp, k -> new HashMap<>());
        HashMap<String, Object> timeBuffer = bufferMap.get(timestamp);
        timeBuffer.put(msgTag, messageMap);

        if (timeBuffer.keySet().containsAll(tagsToSum)) {
            double totalSum = 0.0;



            // PWI 태그 합산 로직
            if (newTagName.equals("301-367-PWI-0000")) {
                for (String tag : tagsToSum) {
                    HashMap<String, Object> data = (HashMap<String, Object>) timeBuffer.get(tag);
                    if (data != null && data.get("value") != null) {
                        try {
                            double value = Double.parseDouble(data.get("value").toString());
                            double unitValue = PWI_UNIT_VALUES.getOrDefault(tag, 1.0);
                            value *= unitValue;



                            totalSum += value;
                        } catch (NumberFormatException e) {
                            System.err.println("값 변환 오류: " + data.get("value"));
                        }
                    }
                }


                HashMap<String, Object> newTagData = new HashMap<>();
                newTagData.put("tagname", newTagName);
                newTagData.put("value", totalSum);
                newTagData.put("timestamp", timestamp);
                newTagData.put("server", server);
                newTagData.put("quality", quality);

                String resultTimeType = checkMsgTime(timestamp);

                if (!TIME_SEC.equals(resultTimeType)) {
                    newTagData.put("type", "all");
                    commonService.insertRawData(newTagData);
                }
                if (TIME_MIN.equals(resultTimeType)) {
                    newTagData.put("type", "min");
                    commonService.insertRawData(newTagData);
                }
                if (TIME_HOUR.equals(resultTimeType)) {
                    newTagData.put("type", "hour");
                    commonService.insertRawData(newTagData);
                }

                // PWQ 태그 합산 로직 (직전 1시간 PWI 평균값)
            } else if (newTagName.equals("301-367-PWQ-0000")) {
                String resultTimeType = checkMsgTime(timestamp);

                // PWQ 태그는 TIME_HOUR일 때만 처리
                if (TIME_HOUR.equals(resultTimeType)) {

                    // 직전 1시간 동안의 PWI_0000 태그 데이터 조회
                    HashMap<String, Object> ohMaps = new HashMap<>();
                    ohMaps.put("date", timestamp);
                    ohMaps.put("tagname", "301-367-PWI-0000"); // PWI 가상 태그의 데이터 조회
                    List<HashMap<String, Object>> oneHourBeforeList = commonService.oneHourBeforeList(ohMaps);

                    double totalPWIValue = 0.0;
                    for (HashMap<String, Object> maps : oneHourBeforeList) {
                        Object valueObj = maps.get("value");
                        if (valueObj != null) {
                            try {
                                totalPWIValue += Double.parseDouble(valueObj.toString());
                            } catch (NumberFormatException e) {
                                System.err.println("PWI 값 변환 오류: " + valueObj);
                            }
                        }
                    }

                    double averagePWIValue = 0.0;
                    if (!oneHourBeforeList.isEmpty()) {
                        averagePWIValue = totalPWIValue / oneHourBeforeList.size();
                    }

                    // 합산된 전력량 값 (평균 전력) 저장
                    HashMap<String, Object> newTagData = new HashMap<>();
                    newTagData.put("tagname", newTagName);
                    newTagData.put("value", averagePWIValue);
                    newTagData.put("timestamp", timestamp);
                    newTagData.put("server", server);
                    newTagData.put("quality", quality);
                    newTagData.put("type", "sum"); // 시간 합산 데이터로 저장

                    commonService.insertRawData(newTagData);

                }
            }

            bufferMap.remove(timestamp);
        }
    }
}