package kr.co.mindone.ems.kafka;
/**
 * kafka 2중화 구성변경으로 미사용
 */
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

import com.google.gson.Gson;
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
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static kr.co.mindone.ems.kafka.KafkaConfig.*;

// !gu2 : 군산 섀도우는 읽기 전용이라 Kafka 를 쓰지 않는다. 운영과 같은 group.id 로
//        조인하면 파티션이 갈려 기존 앱이 SCADA 를 절반만 받는다(에러 없이 조용히).
@Profile("!dev & !gm2 & !hy2 & !hp2 & !ji2 & !gr & !wm & !gs & !gu & !gu2 & !ba & !ss")
@Service
@PropertySource("classpath:application-${spring.profiles.active}.properties")
public class KafkaConsumerService implements ApplicationListener<ApplicationReadyEvent> {

    @Autowired
    @Qualifier("adminClient")
    private AdminClient adminClient;

    @Autowired
    private CommonService commonService;

    @Autowired
    private AiService aiService;

    @Value("${kafka.topic.scada1.name}")
    private String kafka_topic_scada1;

    @Value("${kafka.topic.scada2.name}")
    private String kafka_topic_scada2;

    private List<HashMap<String, Object>> wppTagList;
    private List<HashMap<String, Object>> EMSTagList;
    public int consumerCount = 0;

    @Value("${spring.profiles.active}")
    private String wpp_code;

    @KafkaListener(topics = "${kafka.topic.scada1.name}", groupId = "${kafka.group.scada1.id}", autoStartup= "true")
    public void scadaFirstListen(ConsumerRecord<String, String> record) {
        //System.out.printf("Consumed_1 record with key %s and value %s%n", record.key(), record.value());
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

                insertMsgHashMap(messageMap);

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

    /*@KafkaListener(topics = "${kafka.topic.name}", groupId = "${kafka.new.group.id}", containerFactory = "earliestContainerFactory", autoStartup= "false")
    public void listenFromBeginning(ConsumerRecord<String, String> record) {
        // ... 최초 데이터 획득 처리 로직
    }*/

    @KafkaListener(topics = "${kafka.topic.scada2.name}", groupId = "${kafka.group.scada2.id}", autoStartup= "true")
    public void scadaSecondListen(ConsumerRecord<String, String> record) {
        //System.out.printf("Consumed_2 record with key %s and value %s%n", record.key(), record.value());
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

                insertMsgHashMap(messageMap);
            }catch (Exception exception)
            {
                System.out.printf("Consumed record with key %s and value %s%n", record.key(), record.value());
                exception.printStackTrace();
            }
        }
    }

    /**/
    @Override
    public void onApplicationEvent(ApplicationReadyEvent event) {
        System.out.println("onApplicationEvent Start");
        String status = getClusterStatus();

        System.out.println("kafkaStatus:" + status);
        HashMap<String, Object> params = new HashMap<>();
        wppTagList = commonService.selectWppTagList(params);
        EMSTagList = commonService.selectEMSConsumerTag();
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

    public void insertMsgHashMap(HashMap<String, Object> messageMap)  {

        if(messageMap.containsKey("tagname") && messageMap.containsKey("timestamp"))
        {
            String msgTag = messageMap.get("tagname").toString();
            String msgTs =  messageMap.get("timestamp").toString();

            if(wppTagList == null)
            {
                HashMap<String, Object> params = new HashMap<>();
                wppTagList = commonService.selectWppTagList(params);
            }

            // 정규식 패턴
            String regex = "^\\d{3}-\\d{3}-[A-Za-z]{3}-.*$";
            // Pattern 객체 생성
            Pattern pattern = Pattern.compile(regex);
            Matcher matcher = pattern.matcher(msgTag);

            if (matcher.matches()) {
                boolean tagValueExists = wppTagList.stream()
                        .map(map -> map.get("TAG"))  // "tag" 키에 대한 값만 추출
                        .anyMatch(msgTag::equals);  // 찾고자 하는 값과 일치하는지 확인
                //tagValueExists를 통해 전송받은 tag가 DB에 정의되어 있는지 확인
                if(tagValueExists)
                {
                    ///System.out.println("msgTag:"+msgTag+" ");
                    //System.out.println("messageMap:"+messageMap.toString());


                    if(msgTag.contains("-EMS-")){
                        String func_type = findEMSFunctionType(msgTag);
                        //System.out.println("EMS태그 FUNC_TYP : "+func_type);
                        if(func_type != null){
                            if(func_type.contains("pumpAnlyOptStop")){
                                emsEmergency(messageMap, func_type);
                            }
                        }
                    }

                    if(wpp_code.equals("wm"))
                    {
                        //운문 정수장 인버터 펌프 판별
                        if(msgTag.contains("-IVC-4001")){
                            syncPumpType(messageMap);
                        }

                        //운문 정수장 동기화 실패 확인
                        if(msgTag.contains("-IVB-4008") ){
                            syncPumpFailedCheck(messageMap);
                        }

                        //운문 정수장 펌프 / 토출 밸브 연동운전 확인
                        if( (msgTag.contains("565-340-CBK-4003") || msgTag.contains("565-340-CBK-4007")
                                || msgTag.contains("565-340-CBK-4011") || msgTag.contains("565-340-CBK-4511"))
                                ){
                            syncPumpCtrModeCheck(messageMap);
                        }
                    }


                    String resultTimeType = checkMsgTime(msgTs);
                    //System.out.println("resultTimeType:"+resultTimeType);
                    if(!TIME_SEC.equals(resultTimeType))
                    {
                        messageMap.put("type", "all");
                        //System.out.println("resultTimeType:"+resultTimeType+" scadaDto:"+scadaDto.toString());
                        commonService.insertRawData(messageMap);
                    }

                    if(TIME_MIN.equals(resultTimeType))
                    {
                        messageMap.put("type", "min");
                        commonService.insertRawData(messageMap);
                    }

                    if(TIME_HOUR.equals(resultTimeType))
                    {
                        messageMap.put("type", "hour");
                        commonService.insertRawData(messageMap);
                        messageMap.put("type", "min");
                        commonService.insertRawData(messageMap);

                        String nowTagName = messageMap.get("tagname").toString();
                        double nowValue = Double.parseDouble(messageMap.get("value").toString());
                        HashMap<String, Object> ohMaps = new HashMap<>();
                        ohMaps.put("date",msgTs);
                        List<HashMap<String, Object>> oneHourBeforeList = commonService.oneHourBeforeList(ohMaps);

                        if (nowTagName.matches(".*-(PWQ|PWI|VOI|FRQ|SWI|FIQ)-.*"))
                        {
                            for(HashMap<String, Object> maps : oneHourBeforeList)
                            {
                                String beforeTagName = maps.get("tagname").toString();
                                if(nowTagName.equals(beforeTagName))
                                {
                                    double beforeValue = Double.parseDouble(maps.get("value").toString());
                                    double tempSumValue = 0.0;
                                    tempSumValue = nowValue - beforeValue;
                                    if(tempSumValue < 0)
                                    {
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
            else {
                //System.out.println("####################################################");
                //System.out.println("msgTag ["+msgTag+"] is Not Store");
                //System.out.println("####################################################");
            }
        }
        else{
            System.out.println("####################################################");
            System.out.println("messageMap:"+messageMap.toString());
            System.out.println("####################################################");
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
        for (HashMap<String, Object> entry : EMSTagList) {
            if (tagValue.equals(entry.get("TAG"))) {
                return (String) entry.get("FUNC_TYP");
            }
        }
        return null; // TAG에 해당하는 데이터를 찾지 못한 경우
    }

    public void emsEmergency(HashMap<String, Object> messageMap, String funcTyp){
        HashMap<String, Object> updateMap = new HashMap<>();
        String pumpGrpIdx = String.valueOf(funcTyp.charAt(funcTyp.length() - 1));
        updateMap.put("pump_grp",pumpGrpIdx);
        double statusDoubleValue = Double.parseDouble(messageMap.get("value").toString()) ;
        int statusValue = (int) statusDoubleValue;
        //System.out.println("messageMap:"+messageMap);
        //System.out.println("funcTyp"+funcTyp);
        //System.out.println("funcTyp.contains(Btn)"+funcTyp.contains("Btn"));
        if(funcTyp.contains("Btn")){
            if(statusValue == 1){
                updateMap.put("statusValue", "1");
                commonService.updateEmergencyStatus(updateMap);
                HashMap<String, Object> map = new HashMap<>();
                map.put("PUMP_GRP" , pumpGrpIdx);
                map.put("STATUS", "2");
                aiService.updateAiStatus(map);
            }
        }else if(funcTyp.contains("Off")){
            if(statusValue == 1){
                updateMap.put("statusValue", "0");
                commonService.updateEmergencyStatus(updateMap);
                HashMap<String, Object> map = new HashMap<>();
                map.put("PUMP_GRP" , pumpGrpIdx);
                map.put("STATUS", "2");
            }
        }
    }
    public String checkMsgTime(String msgTs)
    {
        try {
            String resultTimeType;
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            Date date = sdf.parse(msgTs);

            SimpleDateFormat minuteFormat = new SimpleDateFormat("mm");
            SimpleDateFormat secondFormat = new SimpleDateFormat("ss");

            String minute = minuteFormat.format(date);
            String second = secondFormat.format(date);

            if(second.equals("00")) {
                if (minute.equals("00")) {
                    resultTimeType = TIME_HOUR;
                } else if (minute.equals("15") || minute.equals("30") || minute.equals("45")) {
                    resultTimeType = TIME_MIN;
                } else {
                    resultTimeType = TIME_ALL;
                }
            }
            else {
                resultTimeType = TIME_SEC;
            }

            return resultTimeType;
        }catch (Exception e)
        {
            System.out.println("checkMsgTime msgTs:"+msgTs);
            e.printStackTrace();
            return "";
        }
    }

    /* 운문 인버터 체크 기능 */
    public void syncPumpType(HashMap<String, Object> messageMap){

        int[] pumpList = new int[]{1,2,3,4};
        int nowValue = 0;
        if(messageMap.get("value") != null) {
            nowValue = (int) Double.parseDouble(messageMap.get("value").toString());
        }
        //System.out.println("syncPumpType - nowValue:"+nowValue + "/" +messageMap.get("value").toString());
        for (int j : pumpList) {
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

    /* 운문 동기화 실패여부 체크 기능 */
    public void syncPumpFailedCheck(HashMap<String, Object> messageMap){

        int nowValue = 0;
        if(messageMap.get("value") != null) {
            nowValue = (int) Double.parseDouble(messageMap.get("value").toString());

            messageMap.put("check_value", nowValue);
            commonService.updatePumpSyncCheck(messageMap);

            if(nowValue == 1)
            {
                //AI분석모드로 변경
                HashMap<String, Object> updateParam = new HashMap<>();
                updateParam.put("STATUS", 2);
                updateParam.put("PUMP_GRP", 1);

                aiService.updateAiStatus(updateParam);
            }
        }
    }

    /* 운문 제어모드 확인 */
    public void syncPumpCtrModeCheck(HashMap<String, Object> messageMap){

        int nowValue = 0;
        if(messageMap.get("value") != null) {
            nowValue = (int) Double.parseDouble(messageMap.get("value").toString());
            if(nowValue == 0)
            {
                //AI분석모드로 변경
                HashMap<String, Object> updateParam = new HashMap<>();
                updateParam.put("STATUS", 2);
                updateParam.put("PUMP_GRP", 1);
                aiService.updateAiStatus(updateParam);
            }
        }
    }
}
