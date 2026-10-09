package kr.co.mindone.ems.pump;
/**
 * packageName    : kr.co.mindone.ems.pump
 * fileName       : PumpService
 * date           : 24. 9. 8.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 8.        -            최초 생성
 */
import java.time.*;
import java.time.format.DateTimeFormatter;

import io.swagger.models.auth.In;
import kr.co.mindone.ems.kafka.KafkaProperties;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 펌프 제어를 위한 서비스
 */
@Service
public class PumpService {

    @Autowired
    private PumpMapper pumpMapper;

    @Autowired
    private KafkaProperties kafkaProperties;

    private static final int PUMP_RUN_COMMAND_SUCCESS = 0; //동작성공

    private static final int NO_VALID_PUMP_PMB_DATA = 1; // 10분내의 SCADA 데이터로 펌프 가동상태가 확인되지 않음

    private static final int PRECONDITION_NOT_MET = 2; //펌프 동작조건 관련 기능 실패

    private static final int PUMP_STOP_COMMAND_ERROR = 3; // 펌프 중단 오류

    private static final int INIT_TIME = 5000; //초기화 대기 시간

    private static final int RESEND_TIME = 10000; //초기화 대기 시간

    private static final int SM_RESEND_TIME = 60000;

    private static final int WAIT_TIME = 600000;

    private static final int WAIT_TIME_GS = 60000 * 6; // 1분 * 3

    private static final int WAIT_TIME_GS_M = 60000 * 3;

    private static final int WAIT_2M = 60000 * 2;

    private static final int PRECONDITION_CHECK_TIME = 60000;

    @Value("${time.diff.min}")
    private int TIME_DIFF_MIN;

    /** 군산 밸브 OPENC/CLOSEC 펄스 폭(초). 1 을 보낸 뒤 이만큼 기다렸다가 0 을 보낸다 */
    @Value("${ctrl.cmd.valve.pulse-width-sec:3}")
    private int VALVE_PULSE_WIDTH_SEC;

    /**
     * The constant AI_ANALYZE.
     */
    public static int AI_ANALYZE = 2;
    /**
     * The constant AI_RECOMMEND.
     */
    public static int AI_RECOMMEND = 1;
    /**
     * The constant AI_CONTROL.
     */
    public static int AI_CONTROL = 0;

    /**
     * The constant IS_ALL_GRP.
     */
    public static String IS_ALL_GRP = "0";

    @Value("${spring.profiles.active}")
    private String wpp_code;

    /**
     * AI모드인 펌프 그룹 리스트 정보를 전달 받아 현재 펌프 가동 상태 정보를 반환
     *
     * @param pumpGrpStr 펌프 그룹 리스트
     * @return 펌프 가동 상태 정보
     */
    public HashMap < String, Object > pumpCommandStatus(List < String > pumpGrpStr) {

        List < HashMap < String, Object >> resultList = isRunningList();
        List < HashMap < String, Object >> resulWaittList = isWaittingList();
        HashMap < String, Object > ctrEndItem = selectLastEndCtrTagList();
        HashMap < String, Object > resultItem = new HashMap < > ();
        List < HashMap < String, Object >> changeList = changePumpList(true, pumpGrpStr);
        boolean rangeStatus = pumpChangeRangeStatus(resultItem);

        boolean testMode = checkTestMode();
        boolean ctrTestMode = checkCtrTestMode();

        resultItem.put("testMode", testMode);
        resultItem.put("ctrTestMode", ctrTestMode);

        if (!resultList.isEmpty()) //FLAG 1이 존재할때
        {

            resultItem.put("data", getCtrListStr(resultList));
            if (!changeList.isEmpty()) {
                resultItem.put("isChange", true);
            } else {
                resultItem.put("isChange", false);
            }
            resultItem.put("isRunning", true);
        } else if (!resulWaittList.isEmpty()) //FLAG 0이 존재할때, 이때는 동작시켜야 할것만 있음으로 false
        {
            if (!changeList.isEmpty()) {
                resultItem.put("data", getRunPumpIdxStr(changeList));
                resultItem.put("isChange", true);
            } else {
                resultItem.put("data", "");
                resultItem.put("isChange", false);
            }
            resultItem.put("isRunning", false);
            return resultItem;
        } else {
            //이쪽부분 확인
            //동작, 대기중인 상태가 없을때 마지막 명령 시간 확인
            if (ctrEndItem != null) {
                String lastCtrTime = ctrEndItem.get("UPDT_TIME_M").toString();
                String nowDateTime = nowStringDateHHmm();
                resultItem.put("lastCtrTime", lastCtrTime);
                resultItem.put("nowDateTime", nowDateTime);
                resultItem.put("timeDiff(m)", checkTimeDifferenceValue(lastCtrTime, nowDateTime));
                if (!checkTimeDifference(lastCtrTime, nowDateTime)) {
                    resultItem.put("data", getCtrListStr(resultList));
                    resultItem.put("isRunning", true);
                    resultItem.put("isChange", false);
                    return resultItem;
                }
            }
            if (!changeList.isEmpty()) {
                resultItem.put("data", getRunPumpIdxStr(changeList));
                resultItem.put("isChange", true);
            } else {
                resultItem.put("data", "");
                resultItem.put("isChange", false);
            }
            resultItem.put("isRunning", false);
        }
        resultItem.put("rangeStatus", rangeStatus);
        resultItem.put("changeListSize", changeList.size());
        //System.out.println("pumpCommandStatus resultItem:"+resultItem.toString());
        return resultItem;
    }

    /**
     * 제외
     * @param pumpGrpStr
     * @return
     */
    public HashMap < String, Object > pumpCommandStatusMin(List < String > pumpGrpStr) {

        List < HashMap < String, Object >> resultList = isRunningList();
        List < HashMap < String, Object >> resulWaittList = isWaittingList();
        HashMap < String, Object > ctrEndItem = selectLastEndCtrTagList();
        HashMap < String, Object > resultItem = new HashMap < > ();
        List < HashMap < String, Object >> changeList = changePumpList(true, pumpGrpStr);
        boolean rangeStatus = pumpChangeRangeStatus(resultItem);

        boolean testMode = checkTestMode();
        boolean ctrTestMode = checkCtrTestMode();

        resultItem.put("testMode", testMode);
        resultItem.put("ctrTestMode", ctrTestMode);

        if (!resultList.isEmpty()) //FLAG 1이 존재할때
        {
            resultItem.put("data", getCtrListStr(resultList));
            if (!changeList.isEmpty()) {
                resultItem.put("isChange", true);
            } else {
                resultItem.put("isChange", false);
            }
            resultItem.put("isRunning", true);
        } else if (!resulWaittList.isEmpty()) //FLAG 0이 존재할때, 이때는 동작시켜야 할것만 있음으로 false
        {
            if (!changeList.isEmpty()) {
                resultItem.put("data", getRunPumpIdxStr(changeList));
                resultItem.put("isChange", true);
            } else {
                resultItem.put("data", "");
                resultItem.put("isChange", false);
            }
            resultItem.put("isRunning", false);
            return resultItem;
        } else {
            //동작, 대기중인 상태가 없을때 마지막 명령 시간 확인
            if (!changeList.isEmpty()) {
                resultItem.put("data", getRunPumpIdxStr(changeList));
                resultItem.put("isChange", true);
            } else {
                resultItem.put("data", "");
                resultItem.put("isChange", false);
            }
            resultItem.put("isRunning", false);
        }
        resultItem.put("rangeStatus", rangeStatus);
        resultItem.put("changeListSize", changeList.size());
        //System.out.println("pumpCommandStatus resultItem:"+resultItem.toString());
        return resultItem;
    }

    /**
     * 제어 중인 펌프 존재 여부를 반환
     *
     * @return the 제어 중인 펌프 존재 여부
     */
    public Boolean isRunningStatus() {

        List < HashMap < String, Object >> resultList = isRunningList();
        List < HashMap < String, Object >> resulWaittList = isWaittingList();

        HashMap < String, Object > ctrEndItem = selectLastEndCtrTagList();

        if (!resultList.isEmpty()) {
            return true;
        } else if (!resulWaittList.isEmpty()) {
            return false;
        } else {

            if (ctrEndItem != null) {
                String lastCtrTime = ctrEndItem.get("UPDT_TIME_M").toString();
                String nowDateTime = nowStringDateHHmm();
                if (!checkTimeDifference(lastCtrTime, nowDateTime)) {
                    return true;
                }
            }
            return false;
        }
    }

    /**
     * 제외
     * @return
     */
    public Boolean isRunningStatusMin() {

        List < HashMap < String, Object >> resultList = isRunningList();
        List < HashMap < String, Object >> resulWaittList = isWaittingList();


        boolean pumpRunningStatus = true;

        if(!resulWaittList.isEmpty() || !resultList.isEmpty())
        {
            pumpRunningStatus = false;
        }

        return pumpRunningStatus;
    }

    /**
     * 제어중인 명령이 있는 경우 해당 리스트를 반환
     *
     * @return the 제어중인 명령 리스트를 반환
     */
    public List < HashMap < String, Object >> isRunningList() {
        List < HashMap < String, Object >> resultList = new ArrayList < > ();
        HashMap < String, Object > map = new HashMap < > ();
        map.put("FLAG", 1);
        List < HashMap < String, Object >> ctrRunList = selectCtrTagList(map); //동작중인 리스트만 확인
        System.out.println("&&&&&&&&&&&&&&&& ctrRunList :"+ctrRunList );
        map.put("FLAG", 0);
        List < HashMap < String, Object >> ctrWiatList = selectCtrTagList(map); //동작중인 리스트만 확인

        resultList.addAll(ctrRunList);
        //resultList.addAll(ctrWiatList);
        return resultList;
    }

    /**
     * 제어중 대기 상태인 명령을 반환
     *
     * @return the 제어중 대기 상태 목록
     */
    public List < HashMap < String, Object >> isWaittingList() {
        List < HashMap < String, Object >> resultList = new ArrayList < > ();
        HashMap < String, Object > map = new HashMap < > ();
        //map.put("FLAG", 1);
        //List<HashMap<String,Object>> ctrRunList = selectCtrTagList(map); //동작중인 리스트만 확인
        map.put("FLAG", 0);
        List < HashMap < String, Object >> ctrWiatList = selectCtrTagList(map); //동작중인 리스트만 확인

        //resultList.addAll(ctrRunList);
        resultList.addAll(ctrWiatList);
        return resultList;
    }

    /**
     * 펌프 제어 명령을 처리
     *
     * @param ctrList 펌프 제어명령 목록
     */
    public void pumpCommandTask(List < HashMap < String, Object >> ctrList) {
        //한 사이클에 한번에 동작만 수행
        // 중지를 우선으로하며 중지가 없는 경우 동작을 실행
        //CTR_IDX
        if (!ctrList.isEmpty()) {
            HashMap < String, Object > nowCtrItem = ctrList.get(0);
            String ANLY_CD = nowCtrItem.get("ANLY_CD").toString();
            String FLAG = nowCtrItem.get("FLAG").toString();
            double value = Double.parseDouble(nowCtrItem.get("VALUE").toString());

            if (ANLY_CD.equals("SYNC") && FLAG.equals("0")) {
                sendSyncTagItem(nowCtrItem);
                //sendCtrFreqTagItemTestMode(nowCtrItem);
            } else if (ANLY_CD.equals("CTR") && FLAG.equals("0")) {

                sendCtrModeTagItem(nowCtrItem);
                //sendCtrFreqTagItemTestMode(nowCtrItem);
            } else if (ANLY_CD.equals("STOP") && FLAG.equals("0")) {
                sendCtrTagItem(nowCtrItem);
                //sendCtrTagItemTestMode(nowCtrItem);
            } else if (ANLY_CD.equals("TPP") && FLAG.equals("0") && value >= 5.0) {

                //압력전송
                //780-344-PRC-4004
                if (nowCtrItem.get("TAG").toString().equals("780-344-PRC-4004")) {
                    System.out.println("#LIFE TPP:"+selectLifeTPP());
                    nowCtrItem.put("VALUE", selectLifeTPP()); //11.5
                }
                else
                {
                    double nowTPP = Double.parseDouble(nowCtrItem.get("VALUE").toString());
                    nowTPP += selectTPPCorrection();
                    nowCtrItem.put("VALUE", String.valueOf(nowTPP));
                }
                sendCtrEtcTagItem(nowCtrItem, "TPP");

            } else if (ANLY_CD.equals("FREQ") && FLAG.equals("0") && value >= 25.0) {

                sendCtrFreqTagItem(nowCtrItem, "FREQ");
                //주파수 먼저 전송
                //sendCtrFreqTagItemTestMode(nowCtrItem);
            } else if (ANLY_CD.equals("RUN") && FLAG.equals("0")) {
                sendCtrTagItem(nowCtrItem);
                //sendCtrTagItemTestMode(nowCtrItem);
            }
            else if (ANLY_CD.equals("VVK") && FLAG.equals("0")) {
                sendCtrTagVVKItem(nowCtrItem);
                //sendCtrTagItemTestMode(nowCtrItem);
            }
            // 군산 5분 제어 판단(CtrlCmdService): 밸브 개도 설정은 주파수와 같은 1회 전송
            else if (ANLY_CD.equals(CtrlCmdService.ANLY_VALVE_OPEN) && FLAG.equals("0")) {
                sendCtrFreqTagItem(nowCtrItem, CtrlCmdService.ANLY_VALVE_OPEN);
            }
            // 군산 5분 제어 판단(CtrlCmdService): 밸브 OPENC(상향)·CLOSEC(하향) 펄스 1 → 0
            else if ((ANLY_CD.equals(CtrlCmdService.ANLY_VALVE_PULSE) || ANLY_CD.equals(CtrlCmdService.ANLY_VALVE_PULSE_CLOSE))
                    && FLAG.equals("0")) {
                sendCtrPulseTagItem(nowCtrItem);
            }

            /*if(ANLY_CD.equals("STOP"))
            {
                //sendCtrTagItem(ctrItem);
                sendCtrTagItemTestMode(ctrItem);
            }
            else if(ANLY_CD.equals("RUN"))
            {
                //sendCtrTagItem(ctrItem);
                sendCtrTagItemTestMode(ctrItem);
            }*/
        }
    }

    /**
     * 제어 명령 전송 후 전송된 명령이 잘 반영 되었는지를 확인
     *
     * @param ctrList 제어 명령 리스트
     * @return the int 상태확인 시도 횟수
     */
    public int pumpStatusTask(List < HashMap < String, Object >> ctrList) {
        //pumpService
        boolean alarmFlag = false;
        StringBuffer sb = new StringBuffer();
        int statusTryCount = 0;
        for (HashMap < String, Object > ctrItem: ctrList) {
            String ANLY_CD = ctrItem.get("ANLY_CD").toString();
            System.out.println("pumpStatusTask - ctrItem ANLY_CD: " + ctrItem.get("ANLY_CD").toString() +
                    "|CTR_NM: " + ctrItem.get("CTR_NM").toString() +
                    "|OPT_IDX: " + ctrItem.get("OPT_IDX").toString());
            List < HashMap < String, Object >> valveStatusList = selectValveStatusCheck(ctrItem);
            List < HashMap < String, Object >> pumpStatusList = selectPumpStatusCheck(ctrItem); //PMB_TAG
            //System.out.println("pumpStatusTask: "+valveStatusList.size()+" / "+pumpStatusList.size());

            if (valveStatusList.size() == 1 && pumpStatusList.size() == 1) {
                System.out.println("#valveStatusList TS:" + valveStatusList.get(0).get("TS").toString());
                System.out.println("#pumpStatusList TS:" + pumpStatusList.get(0).get("TS").toString());

                System.out.println("valveStatusList - PUMP_IDX: " +
                        valveStatusList.get(0).get("PUMP_IDX").toString() + "|STATUS: " +
                        valveStatusList.get(0).get("STATUS").toString());
                System.out.println("pumpStatusList - PUMP_NM:" + pumpStatusList.get(0).get("PUMP_NM").toString() +
                        "|STATUS: " + pumpStatusList.get(0).get("STATUS").toString());

                if (ANLY_CD.equals("RUN_STATUS") &&
                        valveStatusList.get(0).get("STATUS").toString().equals("Open") &&
                        pumpStatusList.get(0).get("STATUS").toString().equals("On")) {
                    //동작이 확인되면 상태 변경
                    ctrItem.put("FLAG", 2);
                    updateCtrTag(ctrItem);
                    insertHmiTagLog(ctrItem);
                    ctrItem.put("ANLY_CD", "RUN");
                    updateCtrTag(ctrItem); //동작태그 변경
                    insertHmiTagLog(ctrItem);
                    alarmFlag = true;
                    sb.append("가동 완료: ").append(pumpStatusList.get(0).get("PUMP_NM").toString()).append("|").append("|");
                } else if (ANLY_CD.equals("STOP_STATUS") &&
                        valveStatusList.get(0).get("STATUS").toString().equals("Close") &&
                        pumpStatusList.get(0).get("STATUS").toString().equals("Off")) {
                    //동작이 확인되면 상태 변경
                    ctrItem.put("FLAG", 2);
                    updateCtrTag(ctrItem); //STATUS변경
                    insertHmiTagLog(ctrItem);
                    ctrItem.put("ANLY_CD", "STOP");
                    updateCtrTag(ctrItem); //중단태그 변경
                    insertHmiTagLog(ctrItem);
                    alarmFlag = true;
                    sb.append("중지 완료: ").append(pumpStatusList.get(0).get("PUMP_NM").toString()).append("|").append("|");
                }
            } else {
                System.out.println("pumpStatusTask valveStatusList: " + valveStatusList.toString());
                System.out.println("pumpStatusTask pumpStatusList: " + pumpStatusList.toString());
            }
            statusTryCount++;
        }

        //AI운영 모드시 알람 추가
        if (alarmFlag && aiControlStatus() && !sb.toString().isEmpty()) {
            //부분 AI 알람 생성
            HashMap < String, Object > alarm = new HashMap < > ();
            alarm.put("alr_typ", "PUMP");
            alarm.put("nowDate", nowStringDate());
            alarm.put("msg", sb.toString());
            alarm.put("link", "");
            System.out.println("alarm: " + alarm.toString());
            emsPumpAlarmInsert(alarm);
        }
        return statusTryCount;
    }

    /**
     * 제외
     * @param ctrList
     * @return
     */
    public int pumpStatusTaskPumpOnly(List < HashMap < String, Object >> ctrList) {
        //pumpService
        boolean alarmFlag = false;
        StringBuffer sb = new StringBuffer();
        int statusTryCount = 0;
        for (HashMap < String, Object > ctrItem: ctrList) {
            String ANLY_CD = ctrItem.get("ANLY_CD").toString();
            System.out.println("pumpStatusTask - ctrItem ANLY_CD: " + ctrItem.get("ANLY_CD").toString() +
                    "|CTR_NM: " + ctrItem.get("CTR_NM").toString() +
                    "|OPT_IDX: " + ctrItem.get("OPT_IDX").toString());
            List < HashMap < String, Object >> pumpStatusList = selectPumpStatusCheck(ctrItem); //PMB_TAG
            //System.out.println("pumpStatusTask: "+valveStatusList.size()+" / "+pumpStatusList.size());

            if (pumpStatusList.size() == 1) {
                System.out.println("#pumpStatusList TS:" + pumpStatusList.get(0).get("TS").toString());
                System.out.println();
                System.out.println("pumpStatusList - PUMP_NM:" + pumpStatusList.get(0).get("PUMP_NM").toString() +
                        "|STATUS: " + pumpStatusList.get(0).get("STATUS").toString());

                if (ANLY_CD.equals("RUN_STATUS") &&
                        pumpStatusList.get(0).get("STATUS").toString().equals("On")) {
                    //동작이 확인되면 상태 변경
                    ctrItem.put("FLAG", 2);
                    updateCtrTag(ctrItem);
                    insertHmiTagLog(ctrItem);
                    ctrItem.put("ANLY_CD", "RUN");
                    updateCtrTag(ctrItem); //동작태그 변경
                    insertHmiTagLog(ctrItem);
                    alarmFlag = true;
                    sb.append("가동 완료: ").append(pumpStatusList.get(0).get("PUMP_NM").toString()).append("|").append("|");
                } else if (ANLY_CD.equals("STOP_STATUS") &&
                        pumpStatusList.get(0).get("STATUS").toString().equals("Off")) {
                    //동작이 확인되면 상태 변경
                    ctrItem.put("FLAG", 2);
                    updateCtrTag(ctrItem); //STATUS변경
                    insertHmiTagLog(ctrItem);
                    ctrItem.put("ANLY_CD", "STOP");
                    updateCtrTag(ctrItem); //중단태그 변경
                    insertHmiTagLog(ctrItem);
                    alarmFlag = true;
                    sb.append("중지 완료: ").append(pumpStatusList.get(0).get("PUMP_NM").toString()).append("|").append("|");
                }
            } else {
                System.out.println("pumpStatusTask pumpStatusList: " + pumpStatusList.toString());
            }
            statusTryCount++;
        }

        //AI운영 모드시 알람 추가
        if (alarmFlag && aiControlStatus() && !sb.toString().isEmpty()) {
            //부분 AI 알람 생성
            HashMap < String, Object > alarm = new HashMap < > ();
            alarm.put("alr_typ", "PUMP");
            alarm.put("nowDate", nowStringDate());
            alarm.put("msg", sb.toString());
            alarm.put("link", "");
            System.out.println("alarm: " + alarm.toString());
            emsPumpAlarmInsert(alarm);
        }
        return statusTryCount;
    }

    /**
     * 부안 벨브 제어 (제외)
     * @param ctrList
     * @return
     */
    public int VVKStatusTask(List < HashMap < String, Object >> ctrList) {
        //pumpService
        boolean alarmFlag = false;
        StringBuffer sb = new StringBuffer();
        int statusTryCount = 0;
        for (HashMap < String, Object > ctrItem: ctrList) {
            String ANLY_CD = ctrItem.get("ANLY_CD").toString();
            System.out.println("VVKStatusTask - ctrItem ANLY_CD: " + ctrItem.get("ANLY_CD").toString() +
                    "|CTR_NM: " + ctrItem.get("CTR_NM").toString() +
                    "|OPT_IDX: " + ctrItem.get("OPT_IDX").toString());

             HashMap < String, Object > VVKStatus = selectVVKStatusCheck(); //PMB_TAG

            //System.out.println("pumpStatusTask: "+valveStatusList.size()+" / "+pumpStatusList.size());

            if(VVKStatus != null) {

                System.out.println("#VVKStatusTask TS:" + VVKStatus.get("TS").toString());
                System.out.println();
                System.out.println("VVKStatusTask STATUS:"+ VVKStatus.get("STATUS").toString());

                if (ANLY_CD.equals("VVK") &&
                        VVKStatus.get("STATUS").toString().equals("On")) {
                    //동작이 확인되면 상태 변경
                    ctrItem.put("FLAG", 2);
                    updateCtrTag(ctrItem);
                    insertHmiTagLog(ctrItem);
                    ctrItem.put("ANLY_CD", "VVK");
                    updateCtrTag(ctrItem); //동작태그 변경
                    insertHmiTagLog(ctrItem);
                    alarmFlag = true;
                    sb.append("밸브 열기 완료");
                } else if (ANLY_CD.equals("VVK") &&
                        VVKStatus.get("STATUS").toString().equals("Off")) {
                    //동작이 확인되면 상태 변경
                    ctrItem.put("FLAG", 2);
                    updateCtrTag(ctrItem); //STATUS변경
                    insertHmiTagLog(ctrItem);
                    ctrItem.put("ANLY_CD", "VVK");
                    updateCtrTag(ctrItem); //중단태그 변경
                    insertHmiTagLog(ctrItem);
                    alarmFlag = true;
                    sb.append("밸브 닫기 완료");
                }
            } else {
                System.out.println("VVKStatusTask VVKStatus is null");
            }
            statusTryCount++;
        }

        //AI운영 모드시 알람 추가
        if (alarmFlag && aiControlStatus() && !sb.toString().isEmpty()) {
            //부분 AI 알람 생성
            HashMap < String, Object > alarm = new HashMap < > ();
            alarm.put("alr_typ", "PUMP");
            alarm.put("nowDate", nowStringDate());
            alarm.put("msg", sb.toString());
            alarm.put("link", "");
            System.out.println("alarm: " + alarm.toString());
            emsPumpAlarmInsert(alarm);
        }
        return statusTryCount;
    }

    /**
     * 제외
     * @param ctrList
     */
    public void pumpStatusTaskSync(List < HashMap < String, Object >> ctrList) {
        for (HashMap < String, Object > ctrItem: ctrList) {
            String ANLY_CD = ctrItem.get("ANLY_CD").toString();
            String VALUE = ctrItem.get("VALUE").toString();
            String RGSTR_TIME = ctrItem.get("RGSTR_TIME").toString();
            String CTR_NM = ctrItem.get("CTR_NM").toString();
            String TAG = ctrItem.get("TAG").toString();

            if(ANLY_CD.equals("SYNC_STATUS"))
            {
                HashMap<String, Object> map1 = new HashMap<>();
                map1.put("TAG", TAG);

                HashMap<String, Object> item = selectCBBStatus(map1);

                int rawValue = (int) Double.parseDouble(item.get("VALUE").toString());
                System.out.println("pumpStatusTaskSync -"+rawValue+"/"+VALUE);
                if(rawValue == Integer.parseInt(VALUE))
                {
                    ctrItem.put("FLAG",2);
                    updateCtrTag(ctrItem);
                }
                else {
                    //10분동안 동기화 정보가 확인되지 않는 경우 분석모드로 전환
                    if(isDifferenceMoreThan10Minutes(RGSTR_TIME))
                    {
                        //분석 모드로 변경
                        System.out.println("pumpStatusTaskSync #TIMEOVER# "+RGSTR_TIME);
                        initCtrTag();
                        HashMap<String, Object> map = new HashMap<>();
                        map.put("STATUS", 2);//분석모드
                        map.put("PUMP_GRP", "1");
                        updateAiStatusForPump(map);
                    }
                }
            }
            //
            if(ANLY_CD.equals("IVK_STATUS"))
            {
                if(checkREACTModeCount() == 4)
                {
                    ctrItem.put("FLAG",2);
                    updateCtrTag(ctrItem);
                }
            }
        }
    }

    /**
     * 제외
     * @param inputDateTime
     * @return
     */
    public boolean isDifferenceMoreThan10Minutes(String inputDateTime) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        LocalDateTime parsedDateTime = LocalDateTime.parse(inputDateTime, formatter);
        LocalDateTime currentDateTime = LocalDateTime.now();

        // 시간 차이 계산
        Duration duration = Duration.between(parsedDateTime, currentDateTime);

        // 10분 이상 차이 여부 확인
        return duration.toMinutes() >= 20;
    }


    /**
     * 주파수 제어명령 결과를 확인 (제외)
     *
     * @param ctrList 제어 명령 리스트
     * @return the int
     */
    public int pumpStatusTaskFreq(List < HashMap < String, Object >> ctrList) {
        //pumpService
        boolean alarmFlag = false;
        StringBuffer sb = new StringBuffer();
        int statusTryCount = 0;
        for (HashMap < String, Object > ctrItem: ctrList) {
            String ANLY_CD = ctrItem.get("ANLY_CD").toString();
            System.out.println("pumpStatusTask - ctrItem ANLY_CD: " + ctrItem.get("ANLY_CD").toString() +
                    "|CTR_NM: " + ctrItem.get("CTR_NM").toString() +
                    "|OPT_IDX: " + ctrItem.get("OPT_IDX").toString());
            if (ANLY_CD.equals("FREQ")) {
                HashMap < String, Object > nowSpiMap = new HashMap < > ();
                nowSpiMap.put("TAG", ctrItem.get("TAG").toString());
                HashMap < String, Object > nowSpiItem = selectPumpFreqStatusCheck(nowSpiMap);
                if (nowSpiItem != null) {
                    double nowSpiValue = Double.parseDouble(nowSpiItem.get("VALUE").toString());
                    int notSpiRoundValue = (int) Math.round(nowSpiValue);
                    int ctrFreqValue = (int) Double.parseDouble(ctrItem.get("VALUE").toString());
                    System.out.println("pumpStatusTask FREQ: " + notSpiRoundValue + " / " + ctrFreqValue + "(" + nowSpiItem.get("VALUE").toString() + ")");
                    if (notSpiRoundValue == ctrFreqValue) {
                        //동작이 확인되면 상태 변경
                        ctrItem.put("FLAG", 2);
                        updateCtrTag(ctrItem);
                        insertHmiTagLog(ctrItem);
                        alarmFlag = true;
                        sb.append("가동 완료: [").append(nowSpiItem.get("PUMP_NM").toString());
                        sb.append("] ").append(ctrFreqValue).append(" -> ").append(notSpiRoundValue);
                        sb.append("|").append("|");
                    }
                }
            } else {
                List < HashMap < String, Object >> valveStatusList = selectValveStatusCheck(ctrItem);
                List < HashMap < String, Object >> pumpStatusList = selectPumpStatusCheck(ctrItem); //PMB_TAG
                //System.out.println("pumpStatusTask: "+valveStatusList.size()+" / "+pumpStatusList.size());

                if (valveStatusList.size() == 1 && pumpStatusList.size() == 1) {
                    System.out.println("valveStatusList - PUMP_IDX: " +
                            valveStatusList.get(0).get("PUMP_IDX").toString() + "|STATUS: " +
                            valveStatusList.get(0).get("STATUS").toString());
                    System.out.println("pumpStatusList - PUMP_NM:" + pumpStatusList.get(0).get("PUMP_NM").toString() +
                            "|STATUS: " + pumpStatusList.get(0).get("STATUS").toString());

                    if (ANLY_CD.equals("RUN_STATUS") &&
                            valveStatusList.get(0).get("STATUS").toString().equals("Open") &&
                            pumpStatusList.get(0).get("STATUS").toString().equals("On")) {
                        //동작이 확인되면 상태 변경
                        ctrItem.put("FLAG", 2);
                        updateCtrTag(ctrItem);
                        insertHmiTagLog(ctrItem);
                        ctrItem.put("ANLY_CD", "RUN");
                        updateCtrTag(ctrItem); //동작태그 변경
                        insertHmiTagLog(ctrItem);
                        alarmFlag = true;
                        sb.append("가동 완료: ").append(pumpStatusList.get(0).get("PUMP_NM").toString()).append("|").append("|");
                    } else if (ANLY_CD.equals("STOP_STATUS") &&
                            valveStatusList.get(0).get("STATUS").toString().equals("Close") &&
                            pumpStatusList.get(0).get("STATUS").toString().equals("Off")) {
                        //동작이 확인되면 상태 변경
                        ctrItem.put("FLAG", 2);
                        updateCtrTag(ctrItem); //STATUS변경
                        insertHmiTagLog(ctrItem);
                        ctrItem.put("ANLY_CD", "STOP");
                        updateCtrTag(ctrItem); //중단태그 변경
                        insertHmiTagLog(ctrItem);
                        alarmFlag = true;
                        sb.append("중지 완료: ").append(pumpStatusList.get(0).get("PUMP_NM").toString()).append("|").append("|");
                    }
                }
            }
            statusTryCount++;
        }

        //AI운영 모드시 알람 추가
        if (alarmFlag && aiControlStatus() && !sb.toString().isEmpty()) {
            //부분 AI 알람 생성
            HashMap < String, Object > alarm = new HashMap < > ();
            alarm.put("alr_typ", "PUMP");
            alarm.put("nowDate", nowStringDate());
            alarm.put("msg", sb.toString());
            alarm.put("link", "");
            System.out.println("alarm: " + alarm.toString());
            emsPumpAlarmInsert(alarm);
        }
        return statusTryCount;
    }

    /**
     * 제어 명령을 kafka로 전송 (제외)
     *
     * @param sendItem 제어 명령 데이터
     * @param type     제어 명령 구분
     */
    @Async("taskExecutor")
    public void sendCtrEtcTagItem(HashMap < String, Object > sendItem, String type) {
        Properties properties = new Properties();
        properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers()); // Kafka broker의 주소(properties 주소 설정에 따름)
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer < String, String > producer = new KafkaProducer < > (properties)) {
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            String org_anly_cd = sendItem.get("ANLY_CD").toString();
            String org_tag = sendItem.get("TAG").toString();
            HashMap < String, Object > sendItemReSend = new HashMap < > ();
            sendItemReSend = sendItem;
            insertHmiTagLog(sendItem);
            sendItem.put("FLAG", 1);
            updateCtrTag(sendItem);

            if (wpp_code.equals("gs")) //고산은 태그 두번 전송
            {
                Thread.sleep(RESEND_TIME);

                if (org_anly_cd.equals("RUN")) {
                    sendItemReSend.put("ANLY_CD", "RUN");
                } else {
                    sendItemReSend.put("ANLY_CD", "STOP");
                }
                //sendItemReSend.put("VALUE", 1);
                sendItemReSend.put("TIME", nowStringDate());
                /* 두번 전송 시작 */
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItemReSend)));
                String tempValue = sendItemReSend.toString();
                sendItemReSend.put("VALUE", tempValue);
                //insertHmiTagLog(sendItemReSend);
                sendItemReSend.put("FLAG", 1);
                updateCtrTag(sendItemReSend);
            }

            Thread.sleep(RESEND_TIME); //10초
            //동작 대기 상태 종료
            updateCtrTag(sendItem);

            if(wpp_code.equals("gr") && org_tag.equals("780-344-PRC-4004"))
            {
                //동작 확인 명령 관압은 완료로 변경
                sendItem.put("FLAG", 2);
                sendItem.put("ANLY_CD", type);
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            }
            else
            {
                //동작 확인 명령 진행중으로 변경
                sendItem.put("FLAG", 1);
                sendItem.put("ANLY_CD", type);
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 주파수 제어명령을 전송
     *
     * @param sendItem 제어 명령 데이터
     * @param type     제어 명령 구분
     */
    @Async("taskExecutor")
    public void sendCtrFreqTagItem(HashMap < String, Object > sendItem, String type) {
        Properties properties = new Properties();
        properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers()); // Kafka broker의 주소(properties 주소 설정에 따름)
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer < String, String > producer = new KafkaProducer < > (properties)) {
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            String org_anly_cd = sendItem.get("ANLY_CD").toString();
            HashMap < String, Object > sendItemReSend = new HashMap < > ();
            sendItemReSend = sendItem;
            insertHmiTagLog(sendItem);
            sendItem.put("FLAG", 1);
            updateCtrTag(sendItem);

            if (wpp_code.equals("gs")) //고산은 태그 두번 전송
            {
                Thread.sleep(RESEND_TIME);

                if (org_anly_cd.equals("RUN")) {
                    sendItemReSend.put("ANLY_CD", "RUN");
                } else {
                    sendItemReSend.put("ANLY_CD", "STOP");
                }
                //sendItemReSend.put("VALUE", 1);
                sendItemReSend.put("TIME", nowStringDate());
                /* 두번 전송 시작 */
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItemReSend)));
                String tempValue = sendItemReSend.toString();
                sendItemReSend.put("VALUE", tempValue);
                //insertHmiTagLog(sendItemReSend);
                sendItemReSend.put("FLAG", 1);
                updateCtrTag(sendItemReSend);
            }

            Thread.sleep(RESEND_TIME); //10초
            //동작 대기 상태 종료
            updateCtrTag(sendItem);

            //동작 확인 명령 진행중으로 변경
            //주파수는 전송과 동시에 완료로 변경
            sendItem.put("FLAG", 2);
            sendItem.put("ANLY_CD", type);
            insertHmiTagLog(sendItem);
            updateCtrTag(sendItem); //상태태그 확인 활성화

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 동기화 제어 명령을 전송 (제외)
     *
     * @param sendItem 제어 명령 데이터
     */
    @Async("taskExecutor")
    public void sendSyncTagItem(HashMap < String, Object > sendItem) {
        Properties properties = new Properties();
        properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers()); // Kafka broker의 주소(properties 주소 설정에 따름)
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer < String, String > producer = new KafkaProducer < > (properties)) {
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            insertHmiTagLog(sendItem);
            sendItem.put("FLAG", 1);
            updateCtrTag(sendItem);

            Thread.sleep(INIT_TIME); //5초

            sendItem.put("VALUE", 0);
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            Thread.sleep(INIT_TIME); //10초
            //동작 대기 상태 종료

            //sendItem.put("FLAG", 1);
            //updateCtrTag(sendItem);
            /*

            //동작 확인 명령 진행중으로 변경
            sendItem.put("FLAG", 1);
            if (org_anly_cd.equals("RUN")) {
                sendItem.put("ANLY_CD", "SYNC_STATUS");
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            } else if (org_anly_cd.equals("STOP")) {
                sendItem.put("ANLY_CD", "STOP_STATUS");
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
             */

            //동작 확인 명령 진행중으로 변경
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);
            updateCtrTag(sendItem); //상태태그 확인 활성화

            String pumpIdx = sendItem.get("CTR_NM").toString();
            String sync_check_tag = "";

            if(pumpIdx.equals("송수펌프1"))
            {
                sync_check_tag = "565-340-CBB-4148";
            }
            else if(pumpIdx.equals("송수펌프2"))
            {
                sync_check_tag = "565-340-CBB-4151";
            }
            else if(pumpIdx.equals("송수펌프3"))
            {
                sync_check_tag = "565-340-CBB-4154";
            }
            else if(pumpIdx.equals("송수펌프4"))
            {
                sync_check_tag = "565-340-CBB-4554";
            }

            sendItem.put("FLAG", 1);
            sendItem.put("ANLY_CD", "SYNC_STATUS");
            sendItem.put("TAG", sync_check_tag);
            insertHmiTagLog(sendItem);
            updateCtrTag(sendItem); //상태태그 확인 활성화

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 제어모드 변경 명령을 전송 (제외)
     *
     * @param sendItem 제어 명령 데이터
     */
    @Async("taskExecutor")
    public void sendCtrModeTagItem(HashMap < String, Object > sendItem) {
        Properties properties = new Properties();
        properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers()); // Kafka broker의 주소(properties 주소 설정에 따름)
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer < String, String > producer = new KafkaProducer < > (properties)) {

            Thread.sleep(RESEND_TIME); //10초, 모드변경이라 전후 10초 대기

            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            String org_anly_cd = sendItem.get("ANLY_CD").toString();
            HashMap < String, Object > sendItemReSend = new HashMap < > ();
            sendItemReSend = sendItem;
            insertHmiTagLog(sendItem);
            sendItem.put("FLAG", 1);
            updateCtrTag(sendItem);

            if (wpp_code.equals("gs")) //고산은 태그 두번 전송
            {
                Thread.sleep(RESEND_TIME);

                if (org_anly_cd.equals("RUN")) {
                    sendItemReSend.put("ANLY_CD", "RUN");
                } else {
                    sendItemReSend.put("ANLY_CD", "STOP");
                }
                //sendItemReSend.put("VALUE", 1);
                sendItemReSend.put("TIME", nowStringDate());
                /* 두번 전송 시작 */
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItemReSend)));
                String tempValue = sendItemReSend.toString();
                sendItemReSend.put("VALUE", tempValue);
                //insertHmiTagLog(sendItemReSend);
                sendItemReSend.put("FLAG", 1);
                updateCtrTag(sendItemReSend);
            }

            Thread.sleep(RESEND_TIME); //10초
            //동작 대기 상태 종료
            updateCtrTag(sendItem);

            //동작 확인 명령 진행중으로 변경
            sendItem.put("FLAG", 2);
            sendItem.put("ANLY_CD", "CTR");
            insertHmiTagLog(sendItem);
            updateCtrTag(sendItem); //상태태그 확인 활성화

            String ctrNm = sendItem.get("CTR_NM").toString();
            String sync_check_tag = "";
            String pumpIdx = "";
            if(ctrNm.equals("송수펌프1"))
            {
                sync_check_tag = "565-340-CBB-4148";
                pumpIdx = "1";
            }
            else if(ctrNm.equals("송수펌프2"))
            {
                sync_check_tag = "565-340-CBB-4151";
                pumpIdx = "2";
            }
            else if(ctrNm.equals("송수펌프3"))
            {
                sync_check_tag = "565-340-CBB-4154";
                pumpIdx = "3";
            }
            else if(ctrNm.equals("송수펌프4"))
            {
                sync_check_tag = "565-340-CBB-4554";
                pumpIdx = "4";
            }

            HashMap < String, Object > nowRunMap = new HashMap < > ();
            nowRunMap.put("PUMP_IDX", pumpIdx);
            HashMap < String, Object > nowRunItem = nowRunAllPumpItem(nowRunMap); // 현재 변경 대상 펌프 상태

            if(nowRunItem.get("PUMP_YN").equals("Off"))
            {
                sendItem.put("FLAG", 1);
                sendItem.put("ANLY_CD", "SYNC_STATUS");
                sendItem.put("TAG", sync_check_tag);
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            }



        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 가동 및 중단 태그를 전송
     *
     * @param sendItem 제어 명령 데이터
     */
    //@Async("singleThreadExecutor")
    @Async("taskExecutor")
    public void sendCtrTagItem(HashMap < String, Object > sendItem) {
        Properties properties = new Properties();
        properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers()); // Kafka broker의 주소(properties 주소 설정에 따름)
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer < String, String > producer = new KafkaProducer < > (properties)) {
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            String org_anly_cd = sendItem.get("ANLY_CD").toString();
            HashMap < String, Object > sendItemReSend = new HashMap < > ();
            sendItemReSend = sendItem;
            insertHmiTagLog(sendItem);
            sendItem.put("FLAG", 1);
            updateCtrTag(sendItem);

            Thread.sleep(INIT_TIME); // 5초 대기
            sendItem.put("VALUE", 0);
            sendItem.put("TIME", nowStringDate());
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            sendItem.put("ANLY_CD", "INIT");
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);

            /*sendItem.put("VALUE", 5);
            sendItem.put("TIME", nowStringDate());
            sendItem.put("ANLY_CD", "WAIT");
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);*/

            if (wpp_code.equals("ba")) {
                Thread.sleep(RESEND_TIME);

                if (org_anly_cd.equals("RUN")) {
                    sendItemReSend.put("ANLY_CD", "RUN");
                } else {
                    sendItemReSend.put("ANLY_CD", "STOP");
                }
                sendItemReSend.put("VALUE", 1);
                sendItemReSend.put("TIME", nowStringDate());

                /* 두번 전송 시작 */
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItemReSend)));
                String tempValue = sendItemReSend.toString();
                sendItemReSend.put("VALUE", tempValue);
                //insertHmiTagLog(sendItemReSend);
                sendItemReSend.put("FLAG", 1);
                updateCtrTag(sendItemReSend);

                Thread.sleep(INIT_TIME); // 5초 대기

                sendItem.put("VALUE", 0);
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                sendItem.put("TIME", nowStringDate());
                sendItem.put("ANLY_CD", "INIT");
                sendItem.put("FLAG", 2);
                insertHmiTagLog(sendItem);
            }

            if (wpp_code.equals("gs")) {
                Thread.sleep(RESEND_TIME);

                if (org_anly_cd.equals("RUN")) {
                    sendItemReSend.put("ANLY_CD", "RUN");
                } else {
                    sendItemReSend.put("ANLY_CD", "STOP");
                }
                sendItemReSend.put("VALUE", 1);
                sendItemReSend.put("TIME", nowStringDate());

                /* 두번 전송 시작 */
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItemReSend)));
                String tempValue = sendItemReSend.toString();
                sendItemReSend.put("VALUE", tempValue);
                //insertHmiTagLog(sendItemReSend);
                sendItemReSend.put("FLAG", 1);
                updateCtrTag(sendItemReSend);

                Thread.sleep(INIT_TIME); // 5초 대기

                sendItem.put("VALUE", 0);
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                sendItem.put("TIME", nowStringDate());
                sendItem.put("ANLY_CD", "INIT");
                sendItem.put("FLAG", 2);
                insertHmiTagLog(sendItem);

                Thread.sleep(RESEND_TIME);

                if (org_anly_cd.equals("RUN")) {
                    sendItemReSend.put("ANLY_CD", "RUN");
                } else {
                    sendItemReSend.put("ANLY_CD", "STOP");
                }
                sendItemReSend.put("VALUE", 1);
                sendItemReSend.put("TIME", nowStringDate());

                /* 세번 전송 시작 */
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItemReSend)));
                String tempValue2 = sendItemReSend.toString();
                sendItemReSend.put("VALUE", tempValue2);
                //insertHmiTagLog(sendItemReSend);
                sendItemReSend.put("FLAG", 1);
                updateCtrTag(sendItemReSend);

                Thread.sleep(INIT_TIME); // 5초 대기

                sendItem.put("VALUE", 0);
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                sendItem.put("TIME", nowStringDate());
                sendItem.put("ANLY_CD", "INIT");
                sendItem.put("FLAG", 2);
                insertHmiTagLog(sendItem);
            }

            /*sendItem.put("VALUE", 5);
            sendItem.put("TIME", nowStringDate());
            sendItem.put("ANLY_CD", "WAIT");
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);*/
            /* 두번 전송 종료 */

            if (wpp_code.equals("gs")) {
                //10분 대기 시작
                sendItem.put("VALUE", 180);
                sendItem.put("TIME", nowStringDate());
                sendItem.put("ANLY_CD", "WAIT");
                sendItem.put("FLAG", 1);
                updateCtrTag(sendItem);

                //Thread.sleep(WAIT_TIME); // 10분 대기
                if (isSunTimeWithinRange()) {
                    Thread.sleep(WAIT_TIME_GS); //6분 대기
                } else {
                    Thread.sleep(WAIT_TIME_GS_M); //3분 대기
                }

                sendItem.put("VALUE", 180);
                sendItem.put("TIME", nowStringDate());
                sendItem.put("ANLY_CD", "WAIT");
                sendItem.put("FLAG", 2);
                insertHmiTagLog(sendItem);

                //동작 대기 상태 종료
                updateCtrTag(sendItem);
            }
            else {
                //기본 10초 대기
                Thread.sleep(RESEND_TIME);

                sendItem.put("VALUE", 180);
                sendItem.put("TIME", nowStringDate());
                sendItem.put("ANLY_CD", "WAIT");
                sendItem.put("FLAG", 2);
                insertHmiTagLog(sendItem);
                //동작 대기 상태 종료
                updateCtrTag(sendItem);
            }

            //동작 확인 명령 진행중으로 변경
            sendItem.put("FLAG", 1);
            if (org_anly_cd.equals("RUN")) {
                sendItem.put("ANLY_CD", "RUN_STATUS");
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            } else if (org_anly_cd.equals("STOP")) {
                sendItem.put("ANLY_CD", "STOP_STATUS");
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * (제외)
     * @param sendItem
     */
    @Async("taskExecutor")
    public void sendCtrTagVVKItem(HashMap < String, Object > sendItem) {
        Properties properties = new Properties();
        properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers()); // Kafka broker의 주소(properties 주소 설정에 따름)
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer < String, String > producer = new KafkaProducer < > (properties)) {
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            String org_anly_cd = sendItem.get("ANLY_CD").toString();
            HashMap < String, Object > sendItemReSend = new HashMap < > ();
            sendItemReSend = sendItem;
            insertHmiTagLog(sendItem);
            sendItem.put("FLAG", 1);
            updateCtrTag(sendItem);

            Thread.sleep(INIT_TIME); // 5초 대기
            sendItem.put("VALUE", 0);
            sendItem.put("TIME", nowStringDate());
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            sendItem.put("ANLY_CD", "INIT");
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);

            /*sendItem.put("VALUE", 5);
            sendItem.put("TIME", nowStringDate());
            sendItem.put("ANLY_CD", "WAIT");
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);*/

            if (wpp_code.equals("gs") || wpp_code.equals("ba")) {
                Thread.sleep(RESEND_TIME);

                if (org_anly_cd.equals("RUN")) {
                    sendItemReSend.put("ANLY_CD", "RUN");
                } else {
                    sendItemReSend.put("ANLY_CD", "STOP");
                }
                sendItemReSend.put("VALUE", 1);
                sendItemReSend.put("TIME", nowStringDate());

                /* 두번 전송 시작 */
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItemReSend)));
                String tempValue = sendItemReSend.toString();
                sendItemReSend.put("VALUE", tempValue);
                //insertHmiTagLog(sendItemReSend);
                sendItemReSend.put("FLAG", 1);
                updateCtrTag(sendItemReSend);

                Thread.sleep(INIT_TIME); // 5초 대기

                sendItem.put("VALUE", 0);
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                sendItem.put("TIME", nowStringDate());
                sendItem.put("ANLY_CD", "INIT");
                sendItem.put("FLAG", 2);
                insertHmiTagLog(sendItem);
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 밸브 OPENC(상향)·CLOSEC(하향) 펄스 전송 (군산 5분 제어 판단).
     * 1 을 보내고 펄스 폭만큼 기다린 뒤 0 을 보내고 대기열 행을 FLAG=2 로 되돌린다.
     * 기존 sendCtrTagVVKItem 은 군산 경로에서 FLAG 를 1 에 남겨 대기열을 막으므로 따로 둔다.
     *
     * @param sendItem 제어 명령 데이터 (ANLY_CD = VPL 또는 VPC)
     */
    @Async("taskExecutor")
    public void sendCtrPulseTagItem(HashMap < String, Object > sendItem) {
        Properties properties = new Properties();
        properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers());
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer < String, String > producer = new KafkaProducer < > (properties)) {
            sendItem.put("VALUE", 1);
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            // 1 을 보낸 뒤에는 무슨 일이 있어도 0 을 보내 OPENC/CLOSEC 접점이 1 에 남지 않게 한다
            try {
                insertHmiTagLog(sendItem);
                sendItem.put("FLAG", 1);
                updateCtrTag(sendItem);
                Thread.sleep(VALVE_PULSE_WIDTH_SEC * 1000L);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
            } catch (Exception e) {
                e.printStackTrace();
            } finally {
                sendItem.put("VALUE", 0);
                sendItem.put("TIME", nowStringDate());
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                sendItem.put("FLAG", 2);
                insertHmiTagLog(sendItem);
                // updateCtrTag 는 TAG + ANLY_CD + OPT_IDX 로 찾으므로 ANLY_CD 를 바꾸지 않는다
                updateCtrTag(sendItem);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 제어명령 전송 테스트 (제외)
     *
     * @param sendItem 제어 명령 데이터
     */
    @Async("taskExecutor")
    public void sendCtrTagItemTestMode(HashMap < String, Object > sendItem) {
        try {
            String org_anly_cd = sendItem.get("ANLY_CD").toString();
            insertHmiTagLog(sendItem);
            sendItem.put("FLAG", 1);
            updateCtrTag(sendItem);

            Thread.sleep(INIT_TIME); // 5초 대기
            sendItem.put("VALUE", 0);
            sendItem.put("TIME", nowStringDate());
            sendItem.put("ANLY_CD", "INIT");
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);

            Thread.sleep(RESEND_TIME);
            /*sendItem.put("VALUE", 0);
            sendItem.put("TIME", nowStringDate());
            sendItem.put("ANLY_CD", "WAIT");
            sendItem.put("FLAG", 1);
            insertHmiTagLog(sendItem);*/

            //Thread.sleep(WAIT_TIME); // 10분 대기
            Thread.sleep(INIT_TIME);
            updateCtrTag(sendItem);

            sendItem.put("VALUE", 0);
            sendItem.put("TIME", nowStringDate());
            sendItem.put("ANLY_CD", "WAIT");
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);

            //동작 대기 상태 종료
            updateCtrTag(sendItem);

            sendItem.put("FLAG", 1);
            if (org_anly_cd.equals("RUN")) {
                sendItem.put("ANLY_CD", "RUN_STATUS");
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            } else if (org_anly_cd.equals("STOP")) {
                sendItem.put("ANLY_CD", "STOP_STATUS");
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    /**
     * 주파수 제어명령 테스트 (제외)
     *
     * @param sendItem 제어 명령 데이터
     */
    @Async("taskExecutor")
    public void sendCtrFreqTagItemTestMode(HashMap < String, Object > sendItem) {
        try {
            String org_anly_cd = sendItem.get("ANLY_CD").toString();
            insertHmiTagLog(sendItem);
            sendItem.put("FLAG", 1);
            updateCtrTag(sendItem);

            Thread.sleep(INIT_TIME); // 5초 대기
            sendItem.put("VALUE", 0);
            sendItem.put("TIME", nowStringDate());
            sendItem.put("ANLY_CD", "INIT");
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);

            Thread.sleep(RESEND_TIME);
            /*sendItem.put("VALUE", 0);
            sendItem.put("TIME", nowStringDate());
            sendItem.put("ANLY_CD", "WAIT");
            sendItem.put("FLAG", 1);
            insertHmiTagLog(sendItem);*/

            //Thread.sleep(WAIT_TIME); // 10분 대기
            Thread.sleep(INIT_TIME);
            updateCtrTag(sendItem);

            sendItem.put("VALUE", 0);
            sendItem.put("TIME", nowStringDate());
            sendItem.put("ANLY_CD", "WAIT");
            sendItem.put("FLAG", 2);
            insertHmiTagLog(sendItem);

            //동작 대기 상태 종료
            updateCtrTag(sendItem);

            sendItem.put("FLAG", 1);
            if (org_anly_cd.equals("RUN")) {
                sendItem.put("ANLY_CD", "RUN_STATUS");
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            } else if (org_anly_cd.equals("STOP")) {
                sendItem.put("ANLY_CD", "STOP_STATUS");
                insertHmiTagLog(sendItem);
                updateCtrTag(sendItem); //상태태그 확인 활성화
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    /**
     * 펌프 제어 명령을 생성
     *
     * @param pumpGrpStr 펌프 그룹 리스트
     */
    public void pumpCommand(List < String > pumpGrpStr) {
        // 이전 명령 초기화 기능
        initCtrTag();
        System.out.println("pumpCommand Start:" + pumpGrpStr+ "/ isRunningStatusMin():" +isRunningStatusMin());

        if (isRunningStatusMin()) {
            HashMap < String, Object > tempCtrItem = new HashMap < > ();
            List < HashMap < String, Object >> changeList = changePumpList(true, pumpGrpStr);

            System.out.println("####### pumpCommand changeList START #######");
            for(HashMap<String, Object> item : changeList)
            {
                StringBuffer sb = new StringBuffer();

                sb.append(item.get("PUMP_IDX").toString()+"#"+item.get("PUMP_YN").toString());
                if(item.get("FREQ") != null)
                {
                    sb.append("#"+item.get("FREQ").toString());
                }
                System.out.println(sb.toString());
            }
            System.out.println("####### pumpCommand changeList END #######");

            // 끄는 리스트와 켜는 리스트를 분리
            List < HashMap < String, Object >> offList = new ArrayList < > ();
            List < HashMap < String, Object >> onList = new ArrayList < > ();

            for (HashMap < String, Object > item: changeList) {
                String pumpStatus = item.get("PUMP_YN").toString();
                if (pumpStatus.equals("Off")) {
                    offList.add(item); // 끄는 리스트에 추가
                } else {
                    onList.add(item); // 켜는 리스트에 추가
                }
            }

            // 끄는 리스트와 켜는 리스트를 PUMP_IDX 기준으로 정렬
            offList.sort((item1, item2) -> Integer.compare(
                    Integer.parseInt(item1.get("PUMP_IDX").toString()),
                    Integer.parseInt(item2.get("PUMP_IDX").toString())));

            onList.sort((item1, item2) -> Integer.compare(
                    Integer.parseInt(item1.get("PUMP_IDX").toString()),
                    Integer.parseInt(item2.get("PUMP_IDX").toString())));

            boolean isFREQ = false;
            // 초기 DEBUG 로그
            tempCtrItem.put("TAG", "DEBUG");
            tempCtrItem.put("TIME", nowStringDate());
            tempCtrItem.put("VALUE", changeList.toString());
            tempCtrItem.put("ANLY_CD", "pumpCommand");
            tempCtrItem.put("FLAG", 2);
            insertHmiTagLog(tempCtrItem);

            // 고령 공업 펌프 모두 켜짐/꺼짐 방지 2025_05_20
            if(wpp_code.equals("gr")) {
                int gr_2_on_count = 0;
                for (HashMap<String, Object> onCountItem : onList) {
                    if(onCountItem.get("PUMP_GRP").equals("1"))
                    {
                        gr_2_on_count++;
                    }
                }
                if(gr_2_on_count >= 4)
                {
                    return;
                }
                int gr_2_off_count = 0;
                for (HashMap<String, Object> onCountItem : offList) {
                    if(onCountItem.get("PUMP_GRP").equals("1"))
                    {
                        gr_2_off_count++;
                    }
                }
                if(gr_2_off_count >= 4)
                {
                    return;
                }
            }
            // 켜짐/꺼짐 방지 종료

            boolean gr_grp_flag = false;

            //고령 펌프 4대 켜짐 방지 추가
            int gr_now_run_count_1 = 0;
            int gr_now_run_count_2 = 0;
            if(wpp_code.equals("gr")) {
                List<HashMap<String, Object>> nowRumnList = nowRunAllPumpList();
                for (HashMap<String, Object> item : nowRumnList) {
                    if (item.get("PUMP_GRP").equals("1")) {
                        gr_now_run_count_1 += 1;
                    }
                    else if(item.get("PUMP_GRP").equals("2"))
                    {
                        gr_now_run_count_2 += 1;
                    }
                }
                for(HashMap < String, Object > onItem : onList)
                {
                    if (onItem.get("PUMP_GRP").equals("1")) {
                        gr_now_run_count_1 += 1;
                    }
                    else if(onItem.get("PUMP_GRP").equals("2"))
                    {
                        gr_now_run_count_2 += 1;
                    }
                }

                if(gr_now_run_count_1 <= 3 || gr_now_run_count_2 <= 3 )
                {
                    gr_grp_flag = true;
                }

            }


            int offIndex = 0;
            int onIndex = 0;

            // 교차로 실행 (낮은 PUMP_IDX 순서대로)
            while (offIndex < offList.size() || onIndex < onList.size()) {
                // 끄는 항목이 남아있으면 끄는 명령 실행
                if(wpp_code.equals("gr") && gr_grp_flag) //고령은 On 우선, 4대를 on하는 상황에서는 off 먼저 실행하도록 함
                {
                    // 켜는 항목이 남아있으면 켜는 명령 실행
                    if (onIndex < onList.size()) {
                        HashMap < String, Object > onItem = onList.get(onIndex);
                        String nowOptIdx = onItem.get("OPT_IDX").toString();
                        String pumpNm = onItem.get("PUMP_NM").toString();
                        String ctrAutoTag = onItem.get("CTR_AUTO_TAG").toString();
                        String pumpType = onItem.get("PUMP_TYP").toString();
                        String pumpGrp = onItem.get("PUMP_GRP").toString();
                        String pumpIdx = onItem.get("PUMP_IDX").toString();

                        // 켜는 스케쥴링 데이터 만들기
                        HashMap < String, Object > nowRunMap = new HashMap < > ();
                        nowRunMap.put("PUMP_IDX", onItem.get("PUMP_IDX").toString());
                        HashMap < String, Object > nowRunItem = nowRunAllPumpItem(nowRunMap);
                        String nowRunPumpYn = "Off";
                        if (nowRunItem != null) {
                            nowRunPumpYn = nowRunItem.get("PUMP_YN").toString();
                        } else {
                            System.out.println("nowRunItem is Null - " + onItem.get("PUMP_IDX").toString());
                        }

                        // 인버터 펌프의 경우 주파수 값을 미리 생성
                        if (pumpType.equals("2")) {
                            if (wpp_code.equals("gr") && (pumpGrp.equals("1") || pumpGrp.equals("2"))) {
                                String ctrAutoFreqTag = onItem.get("CTR_AUTO_FREQ_TAG").toString();
                                System.out.println("##TPP:" + ctrAutoFreqTag + " / " + onItem.get("TUBE_PRSR_PRDCT").toString());
                                insertPumpControlDataDouble(nowOptIdx, pumpNm, ctrAutoFreqTag, "TPP",
                                        Double.parseDouble(onItem.get("TUBE_PRSR_PRDCT").toString()));
                            } else {
                                String ctrAutoFreqTag = onItem.get("CTR_AUTO_FREQ_TAG").toString();
                                insertPumpControlData(nowOptIdx, pumpNm, ctrAutoFreqTag, "FREQ",
                                        Integer.parseInt(onItem.get("FREQ").toString()));
                                isFREQ = true;
                            }
                        }

                        // 꺼진 펌프의 경우 켜는 명령 생성
                        if (!nowRunPumpYn.equals("On")) {
                            // 부안 주산가압장 4번 펌프 추가 제어 코드
                            if (wpp_code.equals("ba") && pumpIdx.equals("10")) {
                                HashMap < String, Object > nowRawDataParam = new HashMap < > ();
                                String ctrManualTag = onItem.get("CTR_MANUAL_TAG").toString();
                                nowRawDataParam.put("tag", ctrManualTag);
                                HashMap < String, Object > nowRawData = selectNowRawData(nowRawDataParam);
                                int nowValue = (int) Double.parseDouble(nowRawData.get("value").toString());
                                if (nowValue == 0) { // 제어모드 Off 상태일때 On 상태로 변경
                                    insertPumpControlData(nowOptIdx, pumpNm, ctrManualTag, "CTR", 1);
                                }
                            }

                            // 켜는 동작 셋팅
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN", 1);
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "WAIT", 180);
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN_STATUS", 0);

                            //부안 무장B(17) 밸브 닫기, 펌프 켤때 키고 닫기
//                            if (wpp_code.equals("ba") && pumpIdx.equals("17")) {
//
//                                //밸브 열기
//                                insertPumpControlData(nowOptIdx, "무장(가) 바이패스 밸브#2 닫힘", "892-482-VVK-8026", "VVK", 1);
//                            }
                        }

                        onIndex++; // 켜는 항목 인덱스 증가
                    }
                    if (offIndex < offList.size()) {
                        HashMap < String, Object > offItem = offList.get(offIndex);
                        String nowOptIdx = offItem.get("OPT_IDX").toString();
                        String pumpNm = offItem.get("PUMP_NM").toString();
                        String ctrAutoStopTag = offItem.get("CTR_AUTO_STOP_TAG").toString();
    
                        //부안 무장B(17) 밸브 오픈, 펌프 끌때 먼저 열기
//                        if (wpp_code.equals("ba") && offItem.get("PUMP_IDX").toString().equals("17")) {
//
//                            //밸브 열기
//                            insertPumpControlData(nowOptIdx, "무장(가) 바이패스 밸브#2 열림", "892-482-VVK-8025", "VVK", 1);
//                        }
    
    
                        // 끄는 명령 실행
                        insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "STOP", 1);
                        insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "WAIT", 180);
                        insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "STOP_STATUS", 0);
    
                        // 부안 주산가압장 4번 펌프 추가 제어 코드
                        if (wpp_code.equals("ba") && offItem.get("PUMP_IDX").toString().equals("10")) {
                            HashMap < String, Object > nowRawDataParam = new HashMap < > ();
                            String ctrManualTag = offItem.get("CTR_MANUAL_TAG").toString();
                            nowRawDataParam.put("tag", ctrManualTag);
                            HashMap < String, Object > nowRawData = selectNowRawData(nowRawDataParam);
                            int nowValue = (int) Double.parseDouble(nowRawData.get("value").toString());
                            if (nowValue == 1) { // 제어모드 On 상태일때 Off 상태로 변경
                                insertPumpControlData(nowOptIdx, pumpNm, ctrManualTag, "CTR", 0);
                            }
                        }
    
                        offIndex++; // 끄는 항목 인덱스 증가
                    }
                }
                else //고령을 제외한 다른 정수장은 Off 우선
                {
                    if (offIndex < offList.size()) {
                        HashMap < String, Object > offItem = offList.get(offIndex);
                        String nowOptIdx = offItem.get("OPT_IDX").toString();
                        String pumpNm = offItem.get("PUMP_NM").toString();
                        String ctrAutoStopTag = offItem.get("CTR_AUTO_STOP_TAG").toString();
    
                        //부안 무장B(17) 밸브 오픈, 펌프 끌때 먼저 열기
//                        if (wpp_code.equals("ba") && offItem.get("PUMP_IDX").toString().equals("17")) {
//
//                            //밸브 열기
//                            insertPumpControlData(nowOptIdx, "무장(가) 바이패스 밸브#2 열림", "892-482-VVK-8025", "VVK", 1);
//                        }
    
    
                        // 끄는 명령 실행
                        insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "STOP", 1);
                        insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "WAIT", 180);
                        insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "STOP_STATUS", 0);
    
                        // 부안 주산가압장 4번 펌프 추가 제어 코드
                        if (wpp_code.equals("ba") && offItem.get("PUMP_IDX").toString().equals("10")) {
                            HashMap < String, Object > nowRawDataParam = new HashMap < > ();
                            String ctrManualTag = offItem.get("CTR_MANUAL_TAG").toString();
                            nowRawDataParam.put("tag", ctrManualTag);
                            HashMap < String, Object > nowRawData = selectNowRawData(nowRawDataParam);
                            int nowValue = (int) Double.parseDouble(nowRawData.get("value").toString());
                            if (nowValue == 1) { // 제어모드 On 상태일때 Off 상태로 변경
                                insertPumpControlData(nowOptIdx, pumpNm, ctrManualTag, "CTR", 0);
                            }
                        }
    
                        offIndex++; // 끄는 항목 인덱스 증가
                    }
    
                    // 켜는 항목이 남아있으면 켜는 명령 실행
                    if (onIndex < onList.size()) {
                        HashMap < String, Object > onItem = onList.get(onIndex);
                        String nowOptIdx = onItem.get("OPT_IDX").toString();
                        String pumpNm = onItem.get("PUMP_NM").toString();
                        String ctrAutoTag = onItem.get("CTR_AUTO_TAG").toString();
                        String pumpType = onItem.get("PUMP_TYP").toString();
                        String pumpGrp = onItem.get("PUMP_GRP").toString();
                        String pumpIdx = onItem.get("PUMP_IDX").toString();
    
                        // 켜는 스케쥴링 데이터 만들기
                        HashMap < String, Object > nowRunMap = new HashMap < > ();
                        nowRunMap.put("PUMP_IDX", onItem.get("PUMP_IDX").toString());
                        HashMap < String, Object > nowRunItem = nowRunAllPumpItem(nowRunMap);
                        String nowRunPumpYn = "Off";
                        if (nowRunItem != null) {
                            nowRunPumpYn = nowRunItem.get("PUMP_YN").toString();
                        } else {
                            System.out.println("nowRunItem is Null - " + onItem.get("PUMP_IDX").toString());
                        }
    
                        // 인버터 펌프의 경우 주파수 값을 미리 생성
                        if (pumpType.equals("2")) {
                            if (wpp_code.equals("gr") && (pumpGrp.equals("1") || pumpGrp.equals("2"))) {
                                String ctrAutoFreqTag = onItem.get("CTR_AUTO_FREQ_TAG").toString();
                                System.out.println("##TPP:" + ctrAutoFreqTag + " / " + onItem.get("TUBE_PRSR_PRDCT").toString());
                                insertPumpControlDataDouble(nowOptIdx, pumpNm, ctrAutoFreqTag, "TPP",
                                        Double.parseDouble(onItem.get("TUBE_PRSR_PRDCT").toString()));
                            } else {
                                String ctrAutoFreqTag = onItem.get("CTR_AUTO_FREQ_TAG").toString();
                                insertPumpControlData(nowOptIdx, pumpNm, ctrAutoFreqTag, "FREQ",
                                        Integer.parseInt(onItem.get("FREQ").toString()));
                                isFREQ = true;
                            }
                        }
    
                        // 꺼진 펌프의 경우 켜는 명령 생성
                        if (!nowRunPumpYn.equals("On")) {
                            // 부안 주산가압장 4번 펌프 추가 제어 코드
                            if (wpp_code.equals("ba") && pumpIdx.equals("10")) {
                                HashMap < String, Object > nowRawDataParam = new HashMap < > ();
                                String ctrManualTag = onItem.get("CTR_MANUAL_TAG").toString();
                                nowRawDataParam.put("tag", ctrManualTag);
                                HashMap < String, Object > nowRawData = selectNowRawData(nowRawDataParam);
                                int nowValue = (int) Double.parseDouble(nowRawData.get("value").toString());
                                if (nowValue == 0) { // 제어모드 Off 상태일때 On 상태로 변경
                                    insertPumpControlData(nowOptIdx, pumpNm, ctrManualTag, "CTR", 1);
                                }
                            }
    
                            // 켜는 동작 셋팅
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN", 1);
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "WAIT", 180);
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN_STATUS", 0);
    
                            //부안 무장B(17) 밸브 닫기, 펌프 켤때 키고 닫기
//                            if (wpp_code.equals("ba") && pumpIdx.equals("17")) {
//
//                                //밸브 열기
//                                insertPumpControlData(nowOptIdx, "무장(가) 바이패스 밸브#2 닫힘", "892-482-VVK-8026", "VVK", 1);
//                            }
                        }
    
                        onIndex++; // 켜는 항목 인덱스 증가
                    }
                }
            }

            if (aiControlStatus() && !changeList.isEmpty()) {
                HashMap < String, Object > alarm = new HashMap < > ();
                alarm.put("alr_typ", "PUMP");
                alarm.put("nowDate", nowStringDate());
                StringBuilder sb = new StringBuilder();
                sb.append("[AI운전] 펌프 상태를 변경합니다.||");
                for (HashMap < String, Object > changeItem: changeList) {
                    if (isFREQ) {
                        sb.append(changeItem.get("PUMP_NM").toString()).append(": ").append(changeItem.get("FREQ").toString()).append("|");
                    } else {
                        sb.append(changeItem.get("PUMP_NM").toString()).append(": ").append(changeItem.get("value").toString()).append("|");
                    }
                }
                alarm.put("msg", sb.toString());
                alarm.put("link", "");
                emsPumpAlarmInsert(alarm);
            }
        }
    }
    public boolean isNightTime() {
        // 예시: 22:00 ~ 06:00 을 야간으로 처리
        LocalTime now = LocalTime.now(ZoneId.of("Asia/Seoul"));

        LocalTime nightStart = LocalTime.of(21, 0);
        LocalTime nightEnd   = LocalTime.of(5, 0);

        // 22:00 ~ 24:00 또는 00:00 ~ 06:00
        return !now.isBefore(nightStart) || now.isBefore(nightEnd);
    }


    /**
     * 금강남부 고산정수장의 펌프 제어명령을 생성 (제외)
     * @param pumpGrpStr 펌프 그룹 리스트
     */
    public void pumpCommandGS(List < String > pumpGrpStr) {
        // 이전 명령 초기화 기능
        initCtrTag();
        System.out.println("pumpCommand Start:" + pumpGrpStr);

        if (!isRunningStatus()) {
            HashMap<String, Object> tempCtrItem = new HashMap<>();
            List<HashMap<String, Object>> changeList = changePumpList(true, pumpGrpStr);
            List<HashMap<String, Object>> nowRumnList = nowRunAllPumpList();

            // [안전장치] 위험 명령 감지 및 전체 제어 중단 로직
            long runningShinPumpCount = nowRumnList.stream()
                    .filter(p -> {
                        int idx = Integer.parseInt(p.get("PUMP_IDX").toString());
                        return idx >= 8 && idx <= 11 && "On".equals(p.get("PUMP_YN").toString());
                    })
                    .count();

            long shinPumpsToTurnOffCount = changeList.stream()
                    .filter(p -> {
                        int idx = Integer.parseInt(p.get("PUMP_IDX").toString());
                        return idx >= 8 && idx <= 11 && "Off".equals(p.get("PUMP_YN").toString());
                    })
                    .count();
            long shinPumpsToTurnOnCount = changeList.stream()
                    .filter(p -> {
                        int idx = Integer.parseInt(p.get("PUMP_IDX").toString());
                        return idx >= 8 && idx <= 11 && "On".equals(p.get("PUMP_YN").toString());
                    })
                    .count();
            // 만약 이 명령으로 모든 신정수장 펌프가 꺼지게 된다면, 즉시 중단
            if ((runningShinPumpCount - shinPumpsToTurnOffCount + shinPumpsToTurnOnCount) <= 0) {
                System.out.println("!!! 심각한 오류: 모든 신정수장 펌프를 정지시키는 명령 감지. 모든 제어 명령을 중단하고 알람을 전송합니다.");

                // 사용자에게 시스템 이상을 알리는 알람 전송
                if (aiControlStatus()) {
                    HashMap<String, Object> alarm = new HashMap<>();
                    alarm.put("alr_typ", "PUMP_ERROR");
                    alarm.put("nowDate", nowStringDate());
                    String msg = "[AI운전 경고] 신정수장 펌프 전체 정지 시도 감지. 안전을 위해 펌프 제어 명령을 취소했습니다.";
                    alarm.put("msg", msg);
                    alarm.put("link", "");
                    emsPumpAlarmInsert(alarm);
                }

                // 즉시 함수를 종료하여 이후 제어 로직을 모두 중단시킴
                return;
            }
            // 끄는 리스트와 켜는 리스트를 분리
            List<HashMap<String, Object>> offList = new ArrayList<>();
            List<HashMap<String, Object>> onList = new ArrayList<>();
            for (HashMap<String, Object> item : changeList) {
                if ("Off".equals(item.get("PUMP_YN").toString())) {
                    offList.add(item);
                } else {
                    onList.add(item);
                }
            }

            // [단순화된 교번 운전 로직]
            boolean isShinPumpSwap = onList.stream().anyMatch(p -> Integer.parseInt(p.get("PUMP_IDX").toString()) >= 8) &&
                    offList.stream().anyMatch(p -> Integer.parseInt(p.get("PUMP_IDX").toString()) >= 8);

            // 야간 여부 (예: 22시~06시를 야간으로 가정)
            boolean nightMode = isNightTime();   // <= 아래에 헬퍼 메소드 예시 있음

            if (isShinPumpSwap) {

                if (nightMode) {
                    System.out.println("### [야간] 신정수장 교번 운전 실행 (OFF -> ON) ###");

                    // 1. 야간: 기존 펌프 OFF 먼저
                    offList.stream()
                            .filter(p -> Integer.parseInt(p.get("PUMP_IDX").toString()) >= 8)
                            .findFirst()
                            .ifPresent(item -> {
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_STOP_TAG").toString(),
                                        "STOP",
                                        1
                                );
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_STOP_TAG").toString(),
                                        "WAIT",
                                        300
                                );
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_STOP_TAG").toString(),
                                        "STOP_STATUS",
                                        0
                                );
                                offList.remove(item); // 처리된 항목은 리스트에서 제거
                            });

                    // 2. 그 다음 새로운 펌프 ON
                    onList.stream()
                            .filter(p -> Integer.parseInt(p.get("PUMP_IDX").toString()) >= 8)
                            .findFirst()
                            .ifPresent(item -> {
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_TAG").toString(),
                                        "RUN",
                                        1
                                );
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_TAG").toString(),
                                        "WAIT",
                                        300
                                );
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_TAG").toString(),
                                        "RUN_STATUS",
                                        0
                                );
                                onList.remove(item); // 처리된 항목은 리스트에서 제거
                            });

                } else {
                    System.out.println("### [주간] 신정수장 교번 운전 실행 (ON -> OFF, 기존 로직) ###");

                    // 1. 주간: 새로운 펌프 ON 먼저 (기존 로직 유지)
                    onList.stream()
                            .filter(p -> Integer.parseInt(p.get("PUMP_IDX").toString()) >= 8)
                            .findFirst()
                            .ifPresent(item -> {
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_TAG").toString(),
                                        "RUN",
                                        1
                                );
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_TAG").toString(),
                                        "WAIT",
                                        300
                                );
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_TAG").toString(),
                                        "RUN_STATUS",
                                        0
                                );
                                onList.remove(item); // 처리된 항목은 리스트에서 제거
                            });

                    // 2. 그 다음 기존 펌프 OFF (기존 로직 유지)
                    offList.stream()
                            .filter(p -> Integer.parseInt(p.get("PUMP_IDX").toString()) >= 8)
                            .findFirst()
                            .ifPresent(item -> {
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_STOP_TAG").toString(),
                                        "STOP",
                                        1
                                );
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_STOP_TAG").toString(),
                                        "WAIT",
                                        300
                                );
                                insertPumpControlData(
                                        item.get("OPT_IDX").toString(),
                                        item.get("PUMP_NM").toString(),
                                        item.get("CTR_AUTO_STOP_TAG").toString(),
                                        "STOP_STATUS",
                                        0
                                );
                                offList.remove(item); // 처리된 항목은 리스트에서 제거
                            });
                }
            }


            // 교번 운전에서 처리되지 않은 잔여 명령 처리 (구 펌프 등)
            if (!offList.isEmpty() || !onList.isEmpty()) {
                System.out.println("잔여 명령 처리 시작: OFF List Size=" + offList.size() + ", ON List Size=" + onList.size());
                offList.sort(Comparator.comparingInt(item -> Integer.parseInt(item.get("PUMP_IDX").toString())));
                onList.sort(Comparator.comparingInt(item -> Integer.parseInt(item.get("PUMP_IDX").toString())));

                int offIndex = 0;
                int onIndex = 0;

                // 끄고-켜는 순서로 교차 실행
                while (offIndex < offList.size() || onIndex < onList.size()) {
                    if (offIndex < offList.size()) {
                        HashMap<String, Object> offItem = offList.get(offIndex++);
                        insertPumpControlData(offItem.get("OPT_IDX").toString(), offItem.get("PUMP_NM").toString(), offItem.get("CTR_AUTO_STOP_TAG").toString(), "STOP", 1);
                        insertPumpControlData(offItem.get("OPT_IDX").toString(), offItem.get("PUMP_NM").toString(), offItem.get("CTR_AUTO_STOP_TAG").toString(), "WAIT", 600);
                        insertPumpControlData(offItem.get("OPT_IDX").toString(), offItem.get("PUMP_NM").toString(), offItem.get("CTR_AUTO_STOP_TAG").toString(), "STOP_STATUS", 0);
                    }
                    if (onIndex < onList.size()) {
                        HashMap<String, Object> onItem = onList.get(onIndex++);
                        insertPumpControlData(onItem.get("OPT_IDX").toString(), onItem.get("PUMP_NM").toString(), onItem.get("CTR_AUTO_TAG").toString(), "RUN", 1);
                        insertPumpControlData(onItem.get("OPT_IDX").toString(), onItem.get("PUMP_NM").toString(), onItem.get("CTR_AUTO_TAG").toString(), "WAIT", 600);
                        insertPumpControlData(onItem.get("OPT_IDX").toString(), onItem.get("PUMP_NM").toString(), onItem.get("CTR_AUTO_TAG").toString(), "RUN_STATUS", 0);
                    }
                }
            }

            // 최종적으로 실행된 명령에 대한 사용자 알람
            if (aiControlStatus() && !changeList.isEmpty()) {
                HashMap<String, Object> alarm = new HashMap<>();
                alarm.put("alr_typ", "PUMP");
                alarm.put("nowDate", nowStringDate());

                // StringJoiner를 사용하여 메시지를 깔끔하게 만듭니다.
                StringJoiner sj = new StringJoiner("|");
                for (HashMap<String, Object> changeItem : changeList) {
                    String pumpName = changeItem.get("PUMP_NM").toString();

                    // PUMP_YN 값을 기반으로 상태 메시지를 생성합니다.
                    String status = "On".equals(changeItem.get("PUMP_YN").toString()) ? "가동" : "정지";

                    sj.add(pumpName + ": " + status);
                }

                String finalMessage = "[AI운전] 펌프 상태를 변경합니다.||" + sj.toString();
                alarm.put("msg", finalMessage);
                alarm.put("link", "");
                emsPumpAlarmInsert(alarm);
            }
        }
    }

    /**
     * 태양광 발전시간대 확인 (제외)
     * @return 태양광 발전시간 여부
     */
    public boolean isSunTimeWithinRange() {
        // 현재 시간을 가져옴
        LocalTime now = LocalTime.now();

        // 06:00:00과 20:00:00의 시간을 설정
        LocalTime start = LocalTime.of(6, 0); // 06:00
        LocalTime end = LocalTime.of(20, 0); // 20:00

        // 현재 시간이 06:00 ~ 20:00 사이에 있는지 확인
        return now.isAfter(start) && now.isBefore(end);
    }

    /**
     * (제외)
     * @return
     */
    public boolean isLowTimeWithinRange() {
        // 현재 시간을 가져옴
        LocalTime now = LocalTime.now();

        // 06:00:00과 20:00:00의 시간을 설정
        LocalTime start = LocalTime.of(8, 0); // 06:00
        LocalTime end = LocalTime.of(22, 0); // 20:00

        // 현재 시간이 06:00 ~ 20:00 사이에 있는지 확인
        return now.isAfter(start) && now.isBefore(end);
    }

    /**
     * 낙동강 북부 운문정수장의 펌프 제어명령을 생성 (제외)
     * @param pumpGrpStr 펌프 그룹 리스트
     */
    public void pumpCommandWM(List < String > pumpGrpStr) {
        // 이전 명령 초기화 기능
        initCtrTag();
        System.out.println("pumpCommand WM Start:" + pumpGrpStr);

        if (!isRunningStatus()) {
            HashMap < String, Object > tempCtrItem = new HashMap < > ();
            List < HashMap < String, Object >> changeList = changePumpList(true, pumpGrpStr);
            List < HashMap < String, Object >> nowRumnList = nowRunAllPumpList();

            // changeList를 PUMP_IDX 순으로 정렬 (오름차순)
            changeList.sort((item1, item2) -> {
                int pumpIdx1 = Integer.parseInt(item1.get("PUMP_IDX").toString());
                int pumpIdx2 = Integer.parseInt(item2.get("PUMP_IDX").toString());
                return Integer.compare(pumpIdx1, pumpIdx2);
            });

            boolean isFREQ = false;
            boolean controlDataGenerated = false; // 제어 데이터가 생성되었는지 확인하는 플래그

            // 초기 DEBUG 로그
            tempCtrItem.put("TAG", "DEBUG");
            tempCtrItem.put("TIME", nowStringDate());
            tempCtrItem.put("VALUE", changeList.toString());
            tempCtrItem.put("ANLY_CD", "pumpCommandWm");
            tempCtrItem.put("FLAG", 2);
            insertHmiTagLog(tempCtrItem);

            boolean stopChange = false;

            for(HashMap<String, Object> item : changeList)
            {
                String pumpIdx = item.get("PUMP_IDX").toString();

                if(wpp_code.equals("wm") && (pumpIdx.equals("1") || pumpIdx.equals("2")))
                {
                    //stopChange = true;
                }
            }

            if(stopChange)
            {
                initCtrTag();
                HashMap<String, Object> map = new HashMap<>();
                map.put("STATUS", 1);//추천모드
                map.put("PUMP_GRP", "1");
                updateAiStatusForPump(map);
            }
            else {
                boolean expectStop = true; // 첫 번째로 STOP을 기대

                while (!changeList.isEmpty()) {
                    Iterator < HashMap < String, Object >> iterator = changeList.iterator();

                    while (iterator.hasNext()) {
                        HashMap < String, Object > changeItem = iterator.next();
                        String pumpStatus = changeItem.get("PUMP_YN").toString();
                        String nowOptIdx = changeItem.get("OPT_IDX").toString();
                        String pumpNm = changeItem.get("PUMP_NM").toString();
                        String pumpType = changeItem.get("PUMP_TYP").toString();
                        String pumpIdx = changeItem.get("PUMP_IDX").toString();

                        System.out.println("pumpCommandWm While - changeItem - pumpNm: " + pumpNm + "|pumpStatus: " + pumpStatus);

                        // 1. 먼저 현재 상태가 'Off'인 펌프를 처리
                        if (expectStop && pumpStatus.equals("Off")) {
                            // 끄는 스케줄링 데이터 만들기
                            String ctrAutoStopTag = changeItem.get("CTR_AUTO_STOP_TAG").toString();
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "STOP", 1);
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "WAIT", 180);
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "STOP_STATUS", 0);

                            iterator.remove();
                            expectStop = false; // 다음은 RUN을 기대
                            controlDataGenerated = true; // 제어 데이터가 생성되었음을 표시
                            break;
                        } else {
                            expectStop = false; // 다음은 RUN을 기대
                        }

                        // 2. 켜야 하는 펌프의 처리 (PUMP_YN이 'On'인 경우)
                        if (!expectStop && pumpStatus.equals("On")) {
                            // 현재 상태 조회
                            HashMap < String, Object > nowRunMap = new HashMap < > ();
                            nowRunMap.put("PUMP_IDX", pumpIdx);
                            HashMap < String, Object > nowRunItem = nowRunAllPumpItem(nowRunMap); // 현재 변경 대상 펌프 상태
                            String nowRunPumpYn = "Off";
                            String nowRunPumpType = "1"; // 기본값을 리액터 모드로 설정
                            String nowRunFreq = "0"; // 현재 주파수 기본값

                            if (nowRunItem != null) {
                                nowRunPumpYn = nowRunItem.get("PUMP_YN").toString();
                                nowRunPumpType = nowRunItem.get("PUMP_TYP").toString();
                                nowRunFreq = nowRunItem.get("FREQ").toString();
                            } else {
                                // nowRunItem이 null인 경우, 펌프 상태를 가져오지 못하였으므로 제어 데이터를 생성하지 않음
                                System.out.println("현재 펌프 상태를 확인하지 못하였습니다. - PUMP_IDX: " + pumpIdx);

                                // 알람 생성
                                HashMap < String, Object > alarm = new HashMap < > ();
                                alarm.put("alr_typ", "PUMP");
                                alarm.put("nowDate", nowStringDate());
                                alarm.put("msg", "[AI운전] 현재 펌프 상태를 확인하지 못하였습니다. - PUMP_IDX: " + pumpIdx);
                                alarm.put("link", "");
                                emsPumpAlarmInsert(alarm);
                                return; // 함수 종료, 제어 데이터 생성하지 않음
                            }
                            String sync_check_tag = ""; //인버터 동기화 상태 태그

                            // 3. 인버터 모드로 전환하기 전에 기존 인버터 펌프 확인
                            HashMap < String, Object > nowInverterPumpItem = nowInverterPumpItem();
                            if (nowInverterPumpItem != null) {
                                String inverterPumpIdx = nowInverterPumpItem.get("PUMP_IDX").toString();
                                String inverterPumpYN = nowInverterPumpItem.get("PUMP_YN").toString();
                                String inverterPumpNm = nowInverterPumpItem.get("PUMP_NM").toString();

                                if(inverterPumpIdx.equals("1"))
                                {
                                    sync_check_tag = "565-340-CBB-4148";
                                }
                                else if(inverterPumpIdx.equals("2"))
                                {
                                    sync_check_tag = "565-340-CBB-4151";
                                }
                                else if(inverterPumpIdx.equals("3"))
                                {
                                    sync_check_tag = "565-340-CBB-4154";
                                }
                                else if(inverterPumpIdx.equals("4"))
                                {
                                    sync_check_tag = "565-340-CBB-4554";
                                }

                                // 기존 인버터 펌프가 켜져 있는 상태이거나 꺼져 있는 경우 모두 리액터 모드로 전환
                                if (nowRunPumpType.equals("1") && !inverterPumpIdx.equals(pumpIdx)) {
                                    // 기존 인버터 펌프가 켜져 있는 경우 리액터 모드로 전환
                                    // 앞으로 끌 펌프인지 확인 로직 추가

                                    HashMap < String, Object > map = new HashMap < > ();
                                    map.put("FLAG", 0);
                                    map.put("ANLY_CD", "STOP");
                                    List < HashMap < String, Object >> ctrRunningList = selectCtrTagList(map);
                                    String stopPumpIdx = "";
                                    if(!ctrRunningList.isEmpty())
                                    {
                                        String tag = ctrRunningList.get(0).get("TAG").toString();

                                        if(tag.equals("565-340-CBK-4002"))
                                        {
                                            stopPumpIdx = "1";
                                        }
                                        else if(tag.equals("565-340-CBK-4006"))
                                        {
                                            stopPumpIdx = "2";
                                        }
                                        else if(tag.equals("565-340-CBK-4010"))
                                        {
                                            stopPumpIdx = "3";
                                        }
                                        else if(tag.equals("565-340-CBK-4510"))
                                        {
                                            stopPumpIdx = "4";
                                        }
                                        else {
                                            stopPumpIdx = "0";
                                        }
                                    }
                                    //기존 인버터가 켜져 있지만 앞으로 끌 예정이라면 동기화 버튼을 진행하지 않음
                                    if (inverterPumpYN.equals("On") && !stopPumpIdx.equals(inverterPumpIdx)) {
                                        //동기화 버튼 -> 누르면 인버터 빠짐
                                        String beforeCtrSyncTag_1 = nowInverterPumpItem.get("CTR_SYNC_TAG").toString();
                                        insertPumpControlData(nowOptIdx, inverterPumpNm, beforeCtrSyncTag_1, "SYNC", 1);

                                        //위 동기화를 진행하면 해당 태그 값이 0으로 빠진것을 확인해야함
                                        insertPumpControlData(nowOptIdx, "인버터 해제확인", sync_check_tag, "SYNC_STATUS", 0);

                                        //리액터 모드 전환
                                        String beforeCtrManualTag_2 = nowInverterPumpItem.get("CTR_MANUAL_TAG").toString();
                                        insertPumpControlData(nowOptIdx, inverterPumpNm, beforeCtrManualTag_2, "CTR", 0);
                                    }
                                    // 기존 인버터 펌프가 꺼져 있는 경우 처리, 앞으로 끌 예정이라도 이쪽으로
                                    else {

                                        //리액터 모드 전환
                                        String beforeCtrManualTag_1 = nowInverterPumpItem.get("CTR_MANUAL_TAG").toString();
                                        insertPumpControlData(nowOptIdx, inverterPumpNm, beforeCtrManualTag_1, "CTR", 0);

                                        //위 동기화를 진행하면 해당 태그 값이 0으로 빠진것을 확인해야함
                                        insertPumpControlData(nowOptIdx, "인버터 해제확인", sync_check_tag, "SYNC_STATUS", 0);
                                    }
                                }
                            }
                            //인버터가 모두 빠졌을때
                            else {

                            }
                            /// 여기까지 진행하면 기존에 동작중인 인버터 펌프가 없음

                            // 4. 대상 펌프가 이미 인버터 모드라면 불필요한 전환을 하지 않음
                            if (nowRunPumpType.equals("2")) {
                                // 이미 인버터 모드인 경우, 전환하지 않고 주파수 값만 비교하여 변경
                                if (changeItem.get("FREQ") != null && !changeItem.get("FREQ").toString().isEmpty()) {
                                    int freqValue = Integer.parseInt(changeItem.get("FREQ").toString());

                                    // 주파수가 60Hz를 초과하지 않도록 제한
                                    if (freqValue > 60) {
                                        freqValue = 60;
                                    }
                                    else if(freqValue < 56)
                                    {
                                        freqValue = 60;
                                    }

                                    // 주파수 값이 현재 값과 다를 때만 변경
                                    if (!nowRunFreq.equals(String.valueOf(freqValue))) {
                                        String ctrAutoFreqTag = changeItem.get("CTR_AUTO_FREQ_TAG").toString();
                                        insertPumpControlData(nowOptIdx, pumpNm, ctrAutoFreqTag, "FREQ", freqValue);
                                        isFREQ = true;
                                    }
                                }
                            } else {
                                // 대상 펌프가 리액터 모드라면 인버터 모드로 전환
                                // 인버터 전환전 인버터상태 태그 값이 0인것을 확인
                                //insertPumpControlData(nowOptIdx, "리액터 상태", "565-340-IVK", "IVK_STATUS", 4);

                                //현재 인버터가 없는 것을 확인 필요 => 위에서 했음


                                String ctrManualTag = changeItem.get("CTR_MANUAL_TAG").toString();
                                insertPumpControlData(nowOptIdx, pumpNm, ctrManualTag, "CTR", 1); //인버터 누름

                                if (nowRunPumpYn.equals("On")) {
                                    String ctrSyncTag = "565-340-IVK-4002";
                                    System.out.println("changeItem:"+changeItem.toString());
                                    insertPumpControlData(nowOptIdx, pumpNm, ctrSyncTag, "SYNC", 1); //동기화 누름
                                }
                                String sync_check_tag_prdct = ""; //인버터 동기화 상태 태그
                                if(pumpIdx.equals("1"))
                                {
                                    sync_check_tag_prdct = "565-340-CBB-4148";
                                }
                                else if(pumpIdx.equals("2"))
                                {
                                    sync_check_tag_prdct = "565-340-CBB-4151";
                                }
                                else if(pumpIdx.equals("3"))
                                {
                                    sync_check_tag_prdct = "565-340-CBB-4154";
                                }
                                else if(pumpIdx.equals("4"))
                                {
                                    sync_check_tag_prdct = "565-340-CBB-4554";
                                }

                                //동기화 후 인버터 올라온 것을 확인
                                insertPumpControlData(nowOptIdx, "인버터 등록확인", sync_check_tag_prdct, "SYNC_STATUS", 1);

                                // 주파수 값 설정
                                if (changeItem.get("FREQ") != null && !changeItem.get("FREQ").toString().isEmpty()) {
                                    int freqValue = Integer.parseInt(changeItem.get("FREQ").toString());

                                    // 주파수가 60Hz를 초과하지 않도록 제한
                                    if (freqValue > 60) {
                                        freqValue = 60;
                                    }
                                    else if(freqValue < 56)
                                    {
                                        freqValue = 60;
                                    }

                                    String ctrAutoFreqTag = changeItem.get("CTR_AUTO_FREQ_TAG").toString();
                                    insertPumpControlData(nowOptIdx, pumpNm, ctrAutoFreqTag, "FREQ", freqValue);
                                    isFREQ = true;
                                }
                            }

                            // 펌프 동작 명령 생성
                            if (!nowRunPumpYn.equals(pumpStatus)) {

                                //insertPumpControlData(nowOptIdx, "인버터 상태", sync_check_tag, "SYNC_STATUS", 1);

                                String ctrAutoTag = changeItem.get("CTR_AUTO_TAG").toString();
                                insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN", 1);
                                insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "WAIT", 180);
                                insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN_STATUS", 0);
                                controlDataGenerated = true; // 제어 데이터가 생성되었음을 표시
                            }

                            iterator.remove();
                            expectStop = true; // 다음은 STOP을 기대
                            break;
                        }
                    }
                }

                // 7. AI 제어 상태가 활성화된 경우 알람 생성
                if (aiControlStatus()) {
                    HashMap < String, Object > alarm = new HashMap < > ();
                    alarm.put("alr_typ", "PUMP");
                    alarm.put("nowDate", nowStringDate());
                    StringBuffer sb = new StringBuffer();
                    sb.append("[AI운전] 펌프 상태를 변경합니다.||");
                    for (HashMap < String, Object > changeItem: changeList) {
                        if (isFREQ) {
                            sb.append(changeItem.get("PUMP_NM").toString()).append(": ").append(changeItem.get("value").toString());
                            sb.append(changeItem.get("FREQ").toString()).append("|");
                        } else {
                            sb.append(changeItem.get("PUMP_NM").toString()).append(": ").append(changeItem.get("value").toString()).append("|");
                        }
                    }
                    alarm.put("msg", sb.toString());
                    alarm.put("link", "");

                    // 알람이 발생되었을 때 제어 데이터가 생성되지 않았으면 추가 메시지
                    if (!controlDataGenerated) {
                        alarm.put("msg", "[AI운전] 제어 명령이 생성되지 않았습니다.");
                    }

                    emsPumpAlarmInsert(alarm);
                }
            }
        }
    }

    /**
     * (제외)
     * @param pumpGrpStr
     */
    public void pumpCommandWMTemp(List < String > pumpGrpStr) {
        // 이전 명령 초기화 기능
        initCtrTag();
        System.out.println("pumpCommand WM Start:" + pumpGrpStr);

        if (!isRunningStatus()) {
            HashMap < String, Object > tempCtrItem = new HashMap < > ();
            List < HashMap < String, Object >> changeList = changePumpList(true, pumpGrpStr);
            List < HashMap < String, Object >> nowRumnList = nowRunAllPumpList();

            // changeList를 PUMP_IDX 순으로 정렬 (오름차순)
            changeList.sort((item1, item2) -> {
                int pumpIdx1 = Integer.parseInt(item1.get("PUMP_IDX").toString());
                int pumpIdx2 = Integer.parseInt(item2.get("PUMP_IDX").toString());
                return Integer.compare(pumpIdx1, pumpIdx2);
            });

            boolean isFREQ = false;
            boolean controlDataGenerated = false; // 제어 데이터가 생성되었는지 확인하는 플래그

            // 초기 DEBUG 로그
            tempCtrItem.put("TAG", "DEBUG");
            tempCtrItem.put("TIME", nowStringDate());
            tempCtrItem.put("VALUE", changeList.toString());
            tempCtrItem.put("ANLY_CD", "pumpCommandWm");
            tempCtrItem.put("FLAG", 2);
            insertHmiTagLog(tempCtrItem);

            boolean stopChange = false;

            for(HashMap<String, Object> item : changeList)
            {
                String pumpIdx = item.get("PUMP_IDX").toString();

                if(wpp_code.equals("wm") && (pumpIdx.equals("1") || pumpIdx.equals("2")))
                {
                    stopChange = true;
                }
            }

            if(stopChange)
            {
                initCtrTag();
                HashMap<String, Object> map = new HashMap<>();
                map.put("STATUS", 1);//추천모드
                map.put("PUMP_GRP", "1");
                updateAiStatusForPump(map);
            }
            else {
                boolean expectStop = true; // 첫 번째로 STOP을 기대

                while (!changeList.isEmpty()) {
                    Iterator < HashMap < String, Object >> iterator = changeList.iterator();

                    while (iterator.hasNext()) {
                        HashMap < String, Object > changeItem = iterator.next();
                        String pumpStatus = changeItem.get("PUMP_YN").toString();
                        String nowOptIdx = changeItem.get("OPT_IDX").toString();
                        String pumpNm = changeItem.get("PUMP_NM").toString();
                        String pumpType = changeItem.get("PUMP_TYP").toString();
                        String pumpIdx = changeItem.get("PUMP_IDX").toString();

                        System.out.println("pumpCommandWm While - changeItem - pumpNm: " + pumpNm + "|pumpStatus: " + pumpStatus);

                        // 1. 먼저 현재 상태가 'Off'인 펌프를 처리
                        if (expectStop && pumpStatus.equals("Off")) {
                            // 끄는 스케줄링 데이터 만들기
                            String ctrAutoStopTag = changeItem.get("CTR_AUTO_STOP_TAG").toString();
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "STOP", 1);
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "WAIT", 180);
                            insertPumpControlData(nowOptIdx, pumpNm, ctrAutoStopTag, "STOP_STATUS", 0);

                            iterator.remove();
                            expectStop = false; // 다음은 RUN을 기대
                            controlDataGenerated = true; // 제어 데이터가 생성되었음을 표시
                            break;
                        } else {
                            expectStop = false; // 다음은 RUN을 기대
                        }

                        // 2. 켜야 하는 펌프의 처리 (PUMP_YN이 'On'인 경우)
                        if (!expectStop && pumpStatus.equals("On")) {
                            // 현재 상태 조회
                            HashMap < String, Object > nowRunMap = new HashMap < > ();
                            nowRunMap.put("PUMP_IDX", pumpIdx);
                            HashMap < String, Object > nowRunItem = nowRunAllPumpItem(nowRunMap); // 현재 변경 대상 펌프 상태
                            String nowRunPumpYn = "Off";
                            String nowRunPumpType = "1"; // 기본값을 리액터 모드로 설정
                            String nowRunFreq = "0"; // 현재 주파수 기본값

                            if (nowRunItem != null) {
                                nowRunPumpYn = nowRunItem.get("PUMP_YN").toString();
                                nowRunPumpType = nowRunItem.get("PUMP_TYP").toString();
                                nowRunFreq = nowRunItem.get("FREQ").toString();
                            } else {
                                // nowRunItem이 null인 경우, 펌프 상태를 가져오지 못하였으므로 제어 데이터를 생성하지 않음
                                System.out.println("현재 펌프 상태를 확인하지 못하였습니다. - PUMP_IDX: " + pumpIdx);

                                // 알람 생성
                                HashMap < String, Object > alarm = new HashMap < > ();
                                alarm.put("alr_typ", "PUMP");
                                alarm.put("nowDate", nowStringDate());
                                alarm.put("msg", "[AI운전] 현재 펌프 상태를 확인하지 못하였습니다. - PUMP_IDX: " + pumpIdx);
                                alarm.put("link", "");
                                emsPumpAlarmInsert(alarm);
                                return; // 함수 종료, 제어 데이터 생성하지 않음
                            }


                            // 4. 대상 펌프가 이미 인버터 모드라면 불필요한 전환을 하지 않음
                            if (nowRunPumpType.equals("2")) {
                                // 이미 인버터 모드인 경우, 전환하지 않고 주파수 값만 비교하여 변경
                                if (changeItem.get("FREQ") != null && !changeItem.get("FREQ").toString().isEmpty()) {
                                    int freqValue = Integer.parseInt(changeItem.get("FREQ").toString());

                                    // 주파수가 60Hz를 초과하지 않도록 제한
                                    if (freqValue > 60) {
                                        freqValue = 60;
                                    }
                                    else if(freqValue < 56)
                                    {
                                        freqValue = 60;
                                    }

                                    // 주파수 값이 현재 값과 다를 때만 변경
                                    if (!nowRunFreq.equals(String.valueOf(freqValue))) {
                                        String ctrAutoFreqTag = changeItem.get("CTR_AUTO_FREQ_TAG").toString();
                                        insertPumpControlData(nowOptIdx, pumpNm, ctrAutoFreqTag, "FREQ", freqValue);
                                        isFREQ = true;
                                    }
                                }
                            }

                            // 펌프 동작 명령 생성
                            if (!nowRunPumpYn.equals(pumpStatus)) {

                                //insertPumpControlData(nowOptIdx, "인버터 상태", sync_check_tag, "SYNC_STATUS", 1);

                                String ctrAutoTag = changeItem.get("CTR_AUTO_TAG").toString();
                                insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN", 1);
                                insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "WAIT", 180);
                                insertPumpControlData(nowOptIdx, pumpNm, ctrAutoTag, "RUN_STATUS", 0);
                                controlDataGenerated = true; // 제어 데이터가 생성되었음을 표시
                            }

                            iterator.remove();
                            expectStop = true; // 다음은 STOP을 기대
                            break;
                        }
                    }
                }

                // 7. AI 제어 상태가 활성화된 경우 알람 생성
                if (aiControlStatus()) {
                    HashMap < String, Object > alarm = new HashMap < > ();
                    alarm.put("alr_typ", "PUMP");
                    alarm.put("nowDate", nowStringDate());
                    StringBuffer sb = new StringBuffer();
                    sb.append("[AI운전] 펌프 상태를 변경합니다.||");
                    for (HashMap < String, Object > changeItem: changeList) {
                        if (isFREQ) {
                            sb.append(changeItem.get("PUMP_NM").toString()).append(": ").append(changeItem.get("value").toString());
                            sb.append(changeItem.get("FREQ").toString()).append("|");
                        } else {
                            sb.append(changeItem.get("PUMP_NM").toString()).append(": ").append(changeItem.get("value").toString()).append("|");
                        }
                    }
                    alarm.put("msg", sb.toString());
                    alarm.put("link", "");

                    // 알람이 발생되었을 때 제어 데이터가 생성되지 않았으면 추가 메시지
                    /*if (!controlDataGenerated) {
                        alarm.put("msg", "[AI운전] 제어 명령이 생성되지 않았습니다.");
                    }*/

                    emsPumpAlarmInsert(alarm);
                }
            }
        }
    }

    /**
     * 펌프 제어명령을 DB에 저장함
     * @param opx_idx 예측 데이터 IDX
     * @param ctr_nm 제어 대상 펌프 이름
     * @param tag SCADA 제어 태그
     * @param anlyCd 제어 구분
     * @param value 정수형 제어 값
     */
    private void insertPumpControlData(String opx_idx, String ctr_nm, String tag, String anlyCd, int value) {
        //tempCtrItem.put("OPT_IDX", tempCtrItem.get("OPT_IDX").toString());
        //System.out.println("tempCtrItem:"+tempCtrItem.toString());
        HashMap < String, Object > tempCtrItem = new HashMap < > ();
        tempCtrItem.put("OPT_IDX", opx_idx);
        tempCtrItem.put("CTR_NM", ctr_nm);
        tempCtrItem.put("TAG", tag);
        tempCtrItem.put("TIME", nowStringDate());
        tempCtrItem.put("VALUE", value);
        tempCtrItem.put("ANLY_CD", anlyCd);
        tempCtrItem.put("FLAG", 0);
        tempCtrItem.put("AI_STATUS", getAiControlStatus());
        pumpMapper.insertHmiTag(tempCtrItem);
    }

    /**
     * 펌프 제어명령을 DB에 저장함 (제외)
     * @param opx_idx 예측 데이터 IDX
     * @param ctr_nm 제어 대상 펌프 이름
     * @param tag SCADA 제어 태그
     * @param anlyCd 제어 구분
     * @param value 실수형 제어 값
     */
    private void insertPumpControlDataDouble(String opx_idx, String ctr_nm, String tag, String anlyCd, double value) {
        //tempCtrItem.put("OPT_IDX", tempCtrItem.get("OPT_IDX").toString());
        //System.out.println("tempCtrItem:"+tempCtrItem.toString());
        HashMap < String, Object > tempCtrItem = new HashMap < > ();
        tempCtrItem.put("OPT_IDX", opx_idx);
        tempCtrItem.put("CTR_NM", ctr_nm);
        tempCtrItem.put("TAG", tag);
        tempCtrItem.put("TIME", nowStringDate());
        tempCtrItem.put("VALUE", value);
        tempCtrItem.put("ANLY_CD", anlyCd);
        tempCtrItem.put("FLAG", 0);
        tempCtrItem.put("AI_STATUS", getAiControlStatus());
        pumpMapper.insertHmiTag(tempCtrItem);
    }

    /**
     * 제어 대상 펌프 목록 반환
     *
     * @param isBtn      웹에서 실행된 명령 구분
     * @param pumpGrpStr 펌프 그룹 리스트
     * @return the list 제어 대상 펌프 데이터 목록
     */
    public List < HashMap < String, Object >> changePumpList(boolean isBtn, List < String > pumpGrpStr) {
        List < HashMap < String, Object >> scadaResult = new ArrayList < > ();
        List < HashMap < String, Object >> result = new ArrayList < > ();

        HashMap < String, Object > map = new HashMap < > ();
        map.put("PUMP_GRP_LIST", pumpGrpStr);
        System.out.println("changePumpList- pumpGrpStr:" + pumpGrpStr);
        //List<HashMap<String, Object>> nowPrdctlist = selectPumpPrdctNowOnOffList_test(map); //최종분석결과
        //System.out.println("nowPrdctlist:"+nowPrdctlist);
        List < HashMap < String, Object >> nowPrdctlist = selectPumpPrdctNowOnOffList(map); //최종분석결과
        List < HashMap < String, Object >> nowRumnList = nowRunAllPumpList();
        System.out.println("changePumpList- nowPrdctlist:"+nowPrdctlist.toString());
        //System.out.println("nowRumnList:"+nowRumnList.toString());
        HashMap < String, Object > logItem = new HashMap < > ();

        String nowPrdctOptIdx = "";
        String nowPrdctTime = "";

        /*logItem.put("TAG","DEBUG");
        logItem.put("TIME",nowStringDate());
        logItem.put("VALUE",usePrdctlist.toString());
        logItem.put("ANLY_CD","usePrdctlist");
        logItem.put("FLAG",2);
        insertHmiTagLog(logItem);*/

        if (isBtn) {
            logItem.put("TAG", "DEBUG");
            logItem.put("TIME", nowStringDate());
            logItem.put("VALUE", nowPrdctlist.toString());
            logItem.put("ANLY_CD", "nowPrdctlist");
            logItem.put("FLAG", 2);
            insertHmiTagLog(logItem);

            logItem.put("TAG", "DEBUG");
            logItem.put("TIME", nowStringDate());
            logItem.put("VALUE", nowRumnList.toString());
            logItem.put("ANLY_CD", "nowRumnList");
            logItem.put("FLAG", 2);
            insertHmiTagLog(logItem);
        }

        //가동중인 펌프와 비교
        for (HashMap < String, Object > nowPrdctItem: nowPrdctlist) {
            nowPrdctOptIdx = nowPrdctItem.get("OPT_IDX").toString();
            nowPrdctTime = nowPrdctItem.get("PRDCT_TIME").toString();
            for (HashMap < String, Object > nowRunItem: nowRumnList) {
                String nowRunPumpIdx = nowRunItem.get("PUMP_IDX").toString();
                String usePumpIdx = nowPrdctItem.get("PUMP_IDX").toString();
                if (nowRunPumpIdx.equals(usePumpIdx)) {
                    //System.out.println("changePumpList - nowRunItem:"+nowRunItem.toString());
                    //System.out.println("changePumpList - nowPrdctItem:"+ nowPrdctItem.toString());
                    String usePumpYn = nowRunItem.get("PUMP_YN").toString();
                    String nowPumpYn = nowPrdctItem.get("PUMP_YN").toString();
                    if (!nowPumpYn.equals(usePumpYn)) {
                        scadaResult.add(nowPrdctItem);
                    } else {
                        //주파수 변화에 대한 감지

                        /*System.out.println("nowPrdctItem");
                        System.out.println("PUMP_TYP:"+nowPrdctItem.get("PUMP_TYP").toString());
                        System.out.println("PUMP_YN:"+nowPrdctItem.get("PUMP_YN").toString());
                        System.out.println("FREQ:"+nowPrdctItem.get("FREQ").toString());

                        System.out.println("nowRunItem");
                        System.out.println("PUMP_TYP:"+nowRunItem.get("PUMP_TYP").toString());
                        System.out.println("PUMP_YN:"+nowRunItem.get("PUMP_YN").toString());
                        System.out.println("FREQ:"+nowRunItem.get("FREQ").toString());

                        System.out.println("#FREQ STATUS:"+!nowPrdctItem.get("FREQ").toString().equals(nowRunItem.get("FREQ").toString()));
                        */

                        //고령은 압력제어
                        if (wpp_code.equals("gr") && (nowPrdctItem.get("PUMP_GRP").toString().equals("1") || nowPrdctItem.get("PUMP_GRP").toString().equals("2"))) {
                            /*if(nowPrdctItem.get("PUMP_TYP").toString().equals("2") && nowRunItem.get("PUMP_TYP").toString().equals("2"))
                            {
                                System.out.println("Check PRI CHANGE");
                                String useTPPFreq = nowRunItem.get("PRI").toString();
                                String nowTPPFreq = nowPrdctItem.get("TUBE_PRSR_PRDCT").toString();
                                System.out.println("Check TUBE_PRSR_PRDCT CHANGE - "+useTPPFreq+"/"+nowTPPFreq);
                            }*/
                            if (nowPrdctItem.get("PUMP_TYP").toString().equals("2") && nowRunItem.get("PUMP_TYP").toString().equals("2") &&
                                    nowPrdctItem.get("PUMP_YN").toString().equals("On") && nowRunItem.get("PUMP_YN").toString().equals("On") &&
                                    !nowPrdctItem.get("TUBE_PRSR_PRDCT").toString().equals(nowRunItem.get("PRI").toString())
                                    && nowPrdctItem.get("PUMP_GRP").toString().equals("2")
                            ) {
                                System.out.println("Check PRI CHANGE 2");
                                double useTPPFreqTemp = Double.parseDouble(nowRunItem.get("PRI").toString());
                                useTPPFreqTemp = Math.round(useTPPFreqTemp * 10) / 10.0;
                                String useTPPFreq = String.valueOf(useTPPFreqTemp); //실제값
                                String nowTPPFreq = nowPrdctItem.get("TUBE_PRSR_PRDCT").toString();
                                double nowTPPFreqTemp = Double.parseDouble(nowTPPFreq);
                                System.out.println("Check TUBE_PRSR_PRDCT CHANGE 2 - " + useTPPFreq + "/" + nowTPPFreq);
                                if (!useTPPFreq.equals(nowTPPFreq) && nowTPPFreqTemp >= 7.0) {
                                    scadaResult.add(nowPrdctItem);
                                }
                            }
                            if (nowPrdctItem.get("PUMP_TYP").toString().equals("2") && nowRunItem.get("PUMP_TYP").toString().equals("2") &&
                                    nowPrdctItem.get("PUMP_YN").toString().equals("On") && nowRunItem.get("PUMP_YN").toString().equals("On") &&
                                    !nowPrdctItem.get("TUBE_PRSR_PRDCT").toString().equals(nowRunItem.get("PRI").toString())
                                    && nowPrdctItem.get("PUMP_GRP").toString().equals("1")
                            ) {
                                System.out.println("Check PRI CHANGE 1");
                                double useTPPFreqTemp = Double.parseDouble(nowRunItem.get("PRI").toString());
                                useTPPFreqTemp = Math.round(useTPPFreqTemp * 10) / 10.0;
                                String useTPPFreq = String.valueOf(useTPPFreqTemp); //실제값
                                String nowTPPFreq = nowPrdctItem.get("TUBE_PRSR_PRDCT").toString();
                                System.out.println("Check TUBE_PRSR_PRDCT CHANGE 1 - " + useTPPFreq + "/" + nowTPPFreq);
                                /*if (!useTPPFreq.equals(nowTPPFreq)) {
                                    nowPrdctItem.put("TUBE_PRSR_PRDCT", nowTPPFreq);
                                    scadaResult.add(nowPrdctItem);
                                }*/
                                double useTPP = Double.parseDouble(useTPPFreq);
                                if(useTPP < 10.2)
                                {
                                    nowPrdctItem.put("TUBE_PRSR_PRDCT", "10.8");
                                    scadaResult.add(nowPrdctItem);
                                }
                            }
                        } else {
                            //그 외에 주파수 검사
                            if (nowPrdctItem.get("PUMP_TYP").toString().equals("2") && nowRunItem.get("PUMP_TYP").toString().equals("2") &&
                                    nowPrdctItem.get("PUMP_YN").toString().equals("On") && nowRunItem.get("PUMP_YN").toString().equals("On") &&
                                    !nowPrdctItem.get("FREQ").toString().equals(nowRunItem.get("FREQ").toString())) {
                                //System.out.println("Check FREQ CHANGE");
                                String usePumpFreq = nowRunItem.get("FREQ").toString();
                                String nowPumpFreq = nowPrdctItem.get("FREQ").toString();
                                System.out.println("Check FREQ CHANGE - "+usePumpIdx+"/"+ usePumpFreq + "/" + nowPumpFreq);
                                if (!usePumpFreq.equals(nowPumpFreq)) {
                                    if(wpp_code.equals("gu"))
                                    {
                                        int useFreq = Integer.parseInt(usePumpFreq); // 실주파수
                                        int nowFreq = Integer.parseInt(nowPumpFreq); // 예측 주파수

                                        int freqDiff = Math.abs(useFreq - nowFreq);

                                        HashMap < String, Object > tempCtrItem = new HashMap < > ();
                                        tempCtrItem.put("TAG", "DEBUG");
                                        tempCtrItem.put("TIME", nowStringDate());
                                        tempCtrItem.put("ANLY_CD", "FREQ");
                                        tempCtrItem.put("FLAG", 2);

                                        System.out.println("#GS FREQ CHANGE - " + usePumpIdx + "/" + useFreq + "/" + nowFreq + "/" + freqDiff);

                                        tempCtrItem.put("VALUE", "FREQ:"+usePumpIdx + "/" + usePumpFreq + "/" + nowPumpFreq);
                                        insertHmiTagLog(tempCtrItem);

                                        if (freqDiff >= 3) {
                                            if (nowFreq > useFreq) { // 늘릴 때
                                                while (useFreq + 3 <= nowFreq) {
                                                    useFreq += 3;
                                                    HashMap<String, Object> tempPrdctItem = new HashMap<>(nowPrdctItem); // nowPrdctItem을 복사
                                                    String FREQ = String.valueOf(useFreq);
                                                    System.out.println("#GS FREQ CHANGE 1 - " + usePumpIdx + "/" + FREQ + "/" + nowPumpFreq);
                                                    tempPrdctItem.put("FREQ", FREQ);
                                                    scadaResult.add(tempPrdctItem);

                                                    tempCtrItem.put("VALUE", "FREQ_1:"+usePumpIdx + "/" + FREQ + "/" + nowPumpFreq);
                                                    insertHmiTagLog(tempCtrItem);
                                                }
                                                // 마지막 단계 주파수를 설정
                                                HashMap<String, Object> tempPrdctItem = new HashMap<>(nowPrdctItem); // nowPrdctItem을 복사
                                                tempPrdctItem.put("FREQ", nowPumpFreq);
                                                System.out.println("#GS FREQ CHANGE 2 - " + usePumpIdx + "/" + nowPumpFreq + "/" + nowPumpFreq);
                                                tempCtrItem.put("VALUE", "FREQ_2:"+usePumpIdx + "/" + nowPumpFreq + "/" + nowPumpFreq);
                                                insertHmiTagLog(tempCtrItem);
                                                scadaResult.add(tempPrdctItem);
                                            } else { // 줄일 때
                                                while (useFreq - 3 >= nowFreq) {
                                                    useFreq -= 3;
                                                    HashMap<String, Object> tempPrdctItem = new HashMap<>(nowPrdctItem); // nowPrdctItem을 복사
                                                    String FREQ = String.valueOf(useFreq);
                                                    System.out.println("#GS FREQ CHANGE 3 - " + usePumpIdx + "/" + FREQ + "/" + nowPumpFreq);
                                                    tempPrdctItem.put("FREQ", FREQ);
                                                    tempCtrItem.put("VALUE", "FREQ_3:"+usePumpIdx + "/" + FREQ + "/" + nowPumpFreq);
                                                    insertHmiTagLog(tempCtrItem);
                                                    scadaResult.add(tempPrdctItem);
                                                }
                                                // 마지막 단계 주파수를 설정
                                                HashMap<String, Object> tempPrdctItem = new HashMap<>(nowPrdctItem); // nowPrdctItem을 복사
                                                tempPrdctItem.put("FREQ", nowPumpFreq);
                                                System.out.println("#GS FREQ CHANGE 4 - " + usePumpIdx + "/" + nowPumpFreq + "/" + nowPumpFreq);
                                                tempCtrItem.put("VALUE", "FREQ_4:"+usePumpIdx + "/" + nowPumpFreq + "/" + nowPumpFreq);
                                                insertHmiTagLog(tempCtrItem);
                                                scadaResult.add(tempPrdctItem);
                                            }
                                        } else {
                                            // 주파수 차이가 3 미만일 때
                                            HashMap<String, Object> tempPrdctItem = new HashMap<>(nowPrdctItem); // nowPrdctItem을 복사
                                            System.out.println("#GS FREQ CHANGE 5 - " + usePumpIdx + "/" + usePumpFreq + "/" + nowPumpFreq);
                                            scadaResult.add(tempPrdctItem);
                                        }

                                    }
                                    else {
                                        //17
//                                      // usePumpFreq : 실제 주파수
                                        // nowPumpFreq : 예측 주파수
                                        if(usePumpIdx.equals("17"))
                                        {
                                            if (
                                                    (!usePumpFreq.equals("59") || !nowPumpFreq.equals("58")) &&
                                                    (!usePumpFreq.equals("56") || !nowPumpFreq.equals("55")) &&
                                                    (!usePumpFreq.equals("53") || !nowPumpFreq.equals("52")) &&
                                                    (!usePumpFreq.equals("51") || !nowPumpFreq.equals("50"))
                                            ){
                                                scadaResult.add(nowPrdctItem);
                                                System.out.println("#FREQ ADD CHECK START");
                                                System.out.println(nowPrdctItem.toString());
                                                System.out.println("#FREQ ADD CHECK END");
                                            }
                                        }
                                        else {
                                            scadaResult.add(nowPrdctItem);
                                            System.out.println("#FREQ ADD CHECK START");
                                            System.out.println(nowPrdctItem.toString());
                                            System.out.println("#FREQ ADD CHECK END");
                                        }
                                    }
                                }
                            }
                            // 대상 펌프의 타입이 변경되는 경우(운문)
                            else if (wpp_code.equals("wm") &&
                                    !nowPrdctItem.get("PUMP_TYP").toString().equals(nowRunItem.get("PUMP_TYP").toString()) &&
                                    nowPrdctItem.get("PUMP_YN").toString().equals("On") && nowRunItem.get("PUMP_YN").toString().equals("On")) {
                                scadaResult.add(nowPrdctItem);
                            }
                        }
                    }

                }
            }
        }

        result.addAll(scadaResult);
        if (isBtn) {
            HashMap < String, Object > tempCtrItem = new HashMap < > ();
            tempCtrItem.put("TAG", "DEBUG");
            tempCtrItem.put("TIME", nowStringDate());
            tempCtrItem.put("VALUE", getRunPumpIdxStr(result));
            tempCtrItem.put("ANLY_CD", "result");
            tempCtrItem.put("FLAG", 2);
            insertHmiTagLog(tempCtrItem);
        }

        int ctrLimit = 5;
        if (wpp_code.equals("ba") || wpp_code.equals("gr") || wpp_code.equals("gs") || wpp_code.equals("gu")) {
            ctrLimit = 20;
        }else if(wpp_code.equals("wm")){
            ctrLimit = 70;
        }

        if (wpp_code.equals("gs")) {

            List < HashMap < String, Object >> nowRunOldList = new ArrayList < > ();
            List < HashMap < String, Object >> nowRunNewList = new ArrayList < > ();

            boolean nowRunPump2 = false;
            //boolean nowRunPump8 = false;
            //boolean nowRunPump11 = false;

            for (HashMap < String, Object > nowRunItem: nowRumnList) {
                Object pumpIdxObj = nowRunItem.get("PUMP_IDX");
                String pumpYm =  nowRunItem.get("PUMP_YN").toString();
                if (pumpIdxObj != null) {
                    int pumpIdx = Integer.parseInt(pumpIdxObj.toString());
                    if (pumpIdx >= 1 && pumpIdx <= 7) {
                        if(pumpYm.equals("On"))
                        {
                            if (pumpIdx == 3) {
                                nowRunPump2 = true;
                            }
                            nowRunOldList.add(nowRunItem);
                        }
                    } else if (pumpIdx >= 8 && pumpIdx <= 11) {
                        if(pumpYm.equals("On")) {
                            nowRunNewList.add(nowRunItem);
                        }
                    }
                }
            }

            boolean newPumpAreaChange = false;

            for (HashMap < String, Object > resultItem: result) {
                Object pumpIdxObj = resultItem.get("PUMP_IDX");
                Object pumpYnObj = resultItem.get("PUMP_YN");
                int pumpIdx = Integer.parseInt(pumpIdxObj.toString());
                String pumpYn = String.valueOf(pumpYnObj.toString());

                if (pumpIdx >= 8 && pumpIdx <= 11) {
                    newPumpAreaChange = true;
                }
            }

            //isSunTimeWithinRange()
            //2,4,5,6,8 or 11
            // 이때는 2번을 끄고 켜는 명령 추가
            if (nowRunOldList.size() >= 4 && nowRunPump2 && nowRunNewList.size() > 1 && newPumpAreaChange) {
                ctrLimit = 15;
                HashMap < String, Object > pump2RunItem = new HashMap < > ();
                HashMap < String, Object > pump2StopItem = new HashMap < > ();
                /*
                OPT_IDX
                PUMP_GRP
                PUMP_GRP_IDX
                PUMP_IDX
                PUMP_GRP_NM
                PUMP_NM
                PUMP_TYP
                FREQ
                TUBE_PRSR_PRDCT
                CTR_AUTO_TAG
                CTR_AUTO_STOP_TAG
                CTR_AUTO_FREQ_TAG
                CTR_MANUAL_TAG
                PRDCT_TIME
                PUMP_YN
                value
                PUMP_YN_VALUE
                FLAG
                RATE_CTGRY
                FLOW_CTR
                 */

                pump2RunItem.put("OPT_IDX", nowPrdctOptIdx);
                pump2RunItem.put("PUMP_GRP", "1");
                pump2RunItem.put("PUMP_GRP_IDX", "3");
                pump2RunItem.put("PUMP_IDX", "3");
                pump2RunItem.put("PUMP_GRP_NM", "(구)송수펌프");
                pump2RunItem.put("PUMP_NM", "(구)송수펌프_3");
                pump2RunItem.put("PUMP_TYP", "1");
                pump2RunItem.put("FREQ", "0");
                pump2RunItem.put("TUBE_PRSR_PRDCT", "");

                pump2RunItem.put("CTR_AUTO_TAG", "701-367-PMK-4009");
                pump2RunItem.put("CTR_AUTO_STOP_TAG", "701-367-PMK-4010");

                pump2RunItem.put("CTR_AUTO_FREQ_TAG", "");
                pump2RunItem.put("CTR_MANUAL_TAG", "");
                pump2RunItem.put("PRDCT_TIME", nowPrdctTime);
                pump2RunItem.put("PUMP_YN", "On");
                pump2RunItem.put("value", "On");
                pump2RunItem.put("PUMP_YN_VALUE", "1");
                pump2RunItem.put("FLAG", "0");
                pump2RunItem.put("RATE_CTGRY", "");
                pump2RunItem.put("FLOW_CTR", "");

                pump2StopItem.put("OPT_IDX", nowPrdctOptIdx);
                pump2StopItem.put("PUMP_GRP", "1");
                pump2StopItem.put("PUMP_GRP_IDX", "3");
                pump2StopItem.put("PUMP_IDX", "3");
                pump2StopItem.put("PUMP_GRP_NM", "(구)송수펌프");
                pump2StopItem.put("PUMP_NM", "(구)송수펌프_3");
                pump2StopItem.put("PUMP_TYP", "1");
                pump2StopItem.put("FREQ", "0");
                pump2StopItem.put("TUBE_PRSR_PRDCT", "");

                pump2StopItem.put("CTR_AUTO_TAG", "701-367-PMK-4009");
                pump2StopItem.put("CTR_AUTO_STOP_TAG", "701-367-PMK-4010");

                pump2StopItem.put("CTR_AUTO_FREQ_TAG", "");
                pump2StopItem.put("CTR_MANUAL_TAG", "");
                pump2StopItem.put("PRDCT_TIME", nowPrdctTime);
                pump2StopItem.put("PUMP_YN", "Off");
                pump2StopItem.put("value", "Off");
                pump2StopItem.put("PUMP_YN_VALUE", "0");
                pump2StopItem.put("FLAG", "0");
                pump2StopItem.put("RATE_CTGRY", "");
                pump2StopItem.put("FLOW_CTR", "");

                result.add(pump2RunItem);
                result.add(pump2StopItem);

                HashMap < String, Object > tempCtrItem = new HashMap < > ();
                tempCtrItem.put("TAG", "DEBUG2");
                tempCtrItem.put("TIME", nowStringDate());
                tempCtrItem.put("VALUE", getRunPumpIdxStr(result));
                tempCtrItem.put("ANLY_CD", "result2");
                tempCtrItem.put("FLAG", 2);
                insertHmiTagLog(tempCtrItem);
            }

            //System.out.println("Items with PUMP_IDX between 1 and 7: " + list1to7);
            //System.out.println("Items with PUMP_IDX between 8 and 11: " + list8to11);
        }

        if (result.size() >= ctrLimit) {
            HashMap < String, Object > tempCtrItem = new HashMap < > ();
            tempCtrItem.put("TAG", "DEBUG");
            tempCtrItem.put("TIME", nowStringDate());
            tempCtrItem.put("VALUE", getRunPumpIdxStr(result));
            tempCtrItem.put("ANLY_CD", "clear");
            tempCtrItem.put("FLAG", 2);
            insertHmiTagLog(tempCtrItem);
            result.clear();
        }

        // pump_yn 값이 0일 때 pumpGroupCount와 비교하여 일치하는지 확인
        if(wpp_code.equals("ba"))
        {
            //List <HashMap<String, Object>> pumpInfList = selectPumpInfList();
            Map<Integer, Integer> pumpGroupCount = new HashMap<>();

            // pumpInfList에서 각 pump_grp 값을 확인하고 카운트
            for (HashMap<String, Object> pumpInfo : nowRumnList) {
                // pump_grp 값을 가져오기
                if(pumpInfo.get("PUMP_YN").toString().equals("On"))
                {
                    Integer pumpGrp = Integer.parseInt(pumpInfo.get("PUMP_GRP").toString());

                    // 해당 pump_grp의 카운트를 증가
                    pumpGroupCount.put(pumpGrp, pumpGroupCount.getOrDefault(pumpGrp, 0) + 1);
                }
            }

            //펌프 끄고 켜는 최대수 검토
            List<HashMap<String, Object>> resultGrpList = new ArrayList<>();
            HashMap<Integer, HashMap<String, Object>> tempMap = new HashMap<>();

            // result 리스트에서 각 pump_grp 별로 pump_yn 값 카운트 및 결과 저장
            for (HashMap<String, Object> item : result) {
                Integer pumpGrp = Integer.parseInt(item.get("PUMP_GRP").toString());
                Integer pumpYn = Integer.parseInt(item.get("PUMP_YN_VALUE").toString()); // 0 또는 1

                // 현재 pump_grp에 해당하는 카운트 정보를 가져오거나, 새로운 정보를 생성
                HashMap<String, Object> resultMap = tempMap.getOrDefault(pumpGrp, new HashMap<>());

                // pump_grp, pump_yn_0_count, pump_yn_1_count 초기화
                if (!resultMap.containsKey("PUMP_GRP")) {
                    resultMap.put("PUMP_GRP", pumpGrp);
                    resultMap.put("pump_yn_0_count", 0);
                    resultMap.put("pump_yn_1_count", 0);
                }

                // pump_yn 값이 0이면 0의 카운트를 증가시키고, 1이면 1의 카운트를 증가
                if (pumpYn == 0) {
                    resultMap.put("pump_yn_0_count", Integer.parseInt(resultMap.get("pump_yn_0_count").toString()) + 1);
                } else if (pumpYn == 1) {
                    resultMap.put("pump_yn_1_count", Integer.parseInt(resultMap.get("pump_yn_1_count").toString()) + 1);
                }

                // 임시 맵에 업데이트
                tempMap.put(pumpGrp, resultMap);
            }

            // 임시 맵의 모든 결과를 resultList에 추가
            resultGrpList.addAll(tempMap.values());

            for (HashMap<String, Object> resultMap : resultGrpList) {
                Integer pumpGrp = Integer.parseInt(resultMap.get("PUMP_GRP").toString());
                Integer pumpYn0Count = Integer.parseInt(resultMap.get("pump_yn_0_count").toString());
                //Integer pumpYn1Count = Integer.parseInt(resultMap.get("pump_yn_1_count").toString());

                // pump_yn 값이 0인 경우의 카운트가 pumpGroupCount의 값과 일치하는지 확인
                if (pumpGroupCount.containsKey(pumpGrp) && pumpGroupCount.get(pumpGrp).equals(pumpYn0Count) && pumpGrp<4) {
                    System.out.println("#ALL_OFF_CHECK PUMP_GRP " + pumpGrp + "의 pump_yn_0_count: " + pumpYn0Count + " (일치) CLEAR");
                    HashMap < String, Object > tempCtrItem = new HashMap < > ();
                    tempCtrItem.put("TAG", "DEBUG");
                    tempCtrItem.put("TIME", nowStringDate());
                    tempCtrItem.put("VALUE", getRunPumpIdxStr(result));
                    tempCtrItem.put("ANLY_CD", "clearStop");
                    tempCtrItem.put("FLAG", 2);
                    insertHmiTagLog(tempCtrItem);
                    result.clear();
                } else {
                    System.out.println("PUMP_GRP " + pumpGrp + "의 pump_yn_0_count: " + pumpYn0Count + " (불일치)");
                }
                // pump_yn 값이 1인 경우의 카운트가 pumpGroupCount의 값과 일치하는지 확인
            /*if (pumpGroupCount.containsKey(pumpGrp) && pumpGroupCount.get(pumpGrp).equals(pumpYn1Count)  && pumpGrp<4) {
                System.out.println("PUMP_GRP " + pumpGrp + "의 pump_yn_1_count: " + pumpYn1Count + " (일치)");
                HashMap < String, Object > tempCtrItem = new HashMap < > ();
                tempCtrItem.put("TAG", "DEBUG");
                tempCtrItem.put("TIME", nowStringDate());
                tempCtrItem.put("VALUE", getRunPumpIdxStr(result));
                tempCtrItem.put("ANLY_CD", "clearStart");
                tempCtrItem.put("FLAG", 2);
                insertHmiTagLog(tempCtrItem);
                result.clear();
            } else {
                System.out.println("PUMP_GRP " + pumpGrp + "의 pump_yn_1_count: " + pumpYn1Count + " (불일치)");
            }*/
            }
        }
        else
        {
            // ********************************************
            // * System      : 펌프 제어 시스템
            // * Program ID  : PumpControlValidator
            // * Description : 단일 그룹의 모든 펌프가 꺼지는 것을 방지
            // * Execute Program : 해당 그룹의 최종 상태를 검사하여 모두 Off인 경우 result에서 제외
            // * Revision    :
            // * 2025-06-20  -      최초 작성 및 최적화 적용
            // ********************************************

            Map<Integer, Integer> pumpGroupCountMap = new HashMap<>();

            // 1. 현재 가동 중인 펌프 개수만 계산 (켜진 것만 +1)
            for (HashMap<String, Object> pumpInfo : nowRumnList) {
                int pumpGrp = (int) pumpInfo.get("PUMP_GRP");
                if (pumpGrp >= 3) continue;

                String pumpYn = pumpInfo.get("PUMP_YN").toString();
                if (pumpYn.equals("On")) {
                    pumpGroupCountMap.put(pumpGrp, pumpGroupCountMap.getOrDefault(pumpGrp, 0) + 1);
                }
            }

            // 2. result에서 상태 변화가 있는 경우만 반영
            for (HashMap<String, Object> item : result) {
                int pumpGrp = (int) item.get("PUMP_GRP");
                if (pumpGrp >= 3) continue;

                String targetYn = item.get("PUMP_YN").toString();

                // 현재 상태 조회
                String currentYn = "Off"; // 기본값
                for (HashMap<String, Object> pumpInfo : nowRumnList) {
                    if (Objects.equals(pumpInfo.get("PUMP_IDX"), item.get("PUMP_IDX"))) {
                        currentYn = pumpInfo.get("PUMP_YN").toString();
                        break;
                    }
                }

                // 상태 변화가 있는 경우만 count 반영
                if (!targetYn.equals(currentYn)) {
                    if (targetYn.equals("On")) {
                        pumpGroupCountMap.put(pumpGrp, pumpGroupCountMap.getOrDefault(pumpGrp, 0) + 1);
                    } else {
                        pumpGroupCountMap.put(pumpGrp, pumpGroupCountMap.getOrDefault(pumpGrp, 0) - 1);
                    }
                }
            }

            // 3. 최종적으로 켜진 펌프 수가 0 이하인 그룹 제거
            int removeGrp = 0;
            for (Map.Entry<Integer, Integer> entry : pumpGroupCountMap.entrySet()) {
                int pumpGrp = entry.getKey();
                int count = entry.getValue();

                if (count <= 0) {
                    System.out.println("⚠ 그룹 " + pumpGrp + "의 모든 펌프가 꺼질 예정이므로 제거");

                    // result에서 해당 그룹 제거
                    result.removeIf(item -> (int) item.get("PUMP_GRP") == pumpGrp);
                    removeGrp = pumpGrp;

                    // 로그 기록
                    HashMap<String, Object> tempCtrItem = new HashMap<>();
                    tempCtrItem.put("TAG", "DEBUG");
                    tempCtrItem.put("TIME", nowStringDate());
                    tempCtrItem.put("VALUE", removeGrp);
                    tempCtrItem.put("ANLY_CD", "clearStop");
                    tempCtrItem.put("FLAG", 2);
                    insertHmiTagLog(tempCtrItem);
                }
            }
        }

        /*
            if(wpp_code.equals("gs"))
            {
                boolean pumpGrpOld = true;
                boolean pumpGrpNew = true;

                for (HashMap<String, Object> item : result) {
                    int pumpGrp = Integer.parseInt(item.get("PUMP_GRP").toString());
                    int pumpYn = Integer.parseInt(item.get("PUMP_YN_VALUE").toString()); // 0 또는 1

                    if(pumpGrp == 1)
                    {
                        if(pumpYn == 1)
                        {
                            pumpGrpOld  = false;
                        }
                    }

                    if(pumpGrp == 2)
                    {
                        if(pumpYn == 1)
                        {
                            pumpGrpNew  = false;
                        }
                    }
                }

                if(pumpGrpOld || pumpGrpNew)
                {
                    System.out.println("#ALL_OFF_CHECK PUMP_GRP GS " + pumpGrpOld+"/"+pumpGrpNew);
                    HashMap < String, Object > tempCtrItem = new HashMap < > ();
                    tempCtrItem.put("TAG", "DEBUG");
                    tempCtrItem.put("TIME", nowStringDate());
                    tempCtrItem.put("VALUE", getRunPumpIdxStr(result));
                    tempCtrItem.put("ANLY_CD", "clearStop");
                    tempCtrItem.put("FLAG", 2);
                    insertHmiTagLog(tempCtrItem);
                    result.clear();
                }
            }*/
        return result;
    }

    /**
     * (제외)
     * @return
     */
    public List<HashMap<String, Object>> selectPumpInfList()
    {
        return pumpMapper.selectPumpInfList();
    }

    /**
     * yyyy-MM-dd HH:mm:ss 형식의 현재 시점 일시 (제외)
     *
     * @return the 일시
     */
    public String nowStringDate() {
        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId).minusMinutes(TIME_DIFF_MIN);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        // Format the ZonedDateTime using the formatter
        return koreaZonedDateTime.format(formatter);
    }

    /**
     * yyyy-MM-dd HH:mm 형식의 현재 시점 일시 (제외)
     *
     * @return the string 일시
     */
    public String nowStringDateHHmm() {
        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId).minusMinutes(TIME_DIFF_MIN);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
        // Format the ZonedDateTime using the formatter
        return koreaZonedDateTime.format(formatter);
    }

    /**
     * kafka로 전송하기 위한 json 생성 (제외)
     *
     * @param item 생성 대상 데이터
     * @return the string json 형식의 String 데이터
     */
    public String makeProducerJsonValue(HashMap < String, Object > item) {
        StringBuffer sb = new StringBuffer();
        sb.append("{");
        sb.append("\"tag\":").append("\"").append(item.get("TAG").toString()).append("\"").append(",");
        sb.append("\"value\":").append(item.get("VALUE").toString()).append(",");
        sb.append("\"time\":").append("\"").append(item.get("TIME").toString()).append("\"");
        sb.append("}");
        return sb.toString();
    }

    /**
     * 선택된 AI모드인 펌프 그룹 리스트를 반환
     *
     * @param default_value AI 모드 구분
     * @return the list 펌프 그룹 리스트
     */
    public List < String > selectAiPumpGrpListStr(int default_value) {
        List < HashMap < String, Object >> list = pumpMapper.selectAiPumpGrpList(default_value);
        List < String > pumpGrpList = new ArrayList < > ();
        //TAG_GRP
        for (HashMap < String, Object > map: list) {
            if (map.containsKey("PUMP_GRP")) {
                Object pumpGrp = map.get("PUMP_GRP");
                if (pumpGrp != null) {
                    if (wpp_code.equals("ba") && pumpGrp.toString().equals("4")) {
                        pumpGrpList.add(pumpGrp.toString());
                        pumpGrpList.add("5"); //무장B
                    } else {
                        pumpGrpList.add(pumpGrp.toString());
                    }
                }
            }
        }
        return pumpGrpList;
    }

    /**
     * 전체 펌프 그룹 리스트를 반환
     *
     * @return the 전체 펌프 그룹 리스트
     */
    public List < String > selectPumpGrpListStr() {
        List < HashMap < String, Object >> resultList = selectPumpGrpList();
        List < String > pumpGrpList = new ArrayList < > ();

        for (HashMap < String, Object > map: resultList) {
            if (map.containsKey("PUMP_GRP")) {
                Object pumpGrp = map.get("PUMP_GRP");
                if (pumpGrp != null) {
                    pumpGrpList.add(pumpGrp.toString());
                }
            }
        }
        return pumpGrpList;
    }

    /**
     * 펌프 그룹 리스트를 반환
     *
     * @return the list 펌프 그룹 리스트
     */
    public List < HashMap < String, Object >> selectPumpGrpList() {
        return pumpMapper.selectPumpGrpList();
    }

    /**
     * 제어 명령 리스트를 반환
     *
     * @param map 제어 대상 구분
     * @return the list 제어 명령 리스트
     */
    public List < HashMap < String, Object >> selectCtrTagList(HashMap < String, Object > map) {
        return pumpMapper.selectCtrTagList(map);
    }

    /**
     * 제어 명령 상태를 업데이트
     *
     * @param map 업데이트 대상 제어 명령
     */
    public void updateCtrTag(HashMap < String, Object > map) {
        pumpMapper.updateCtrTag(map);
    }

    /**
     * 제어 관련 로그를 저장
     *
     * @param map 제어 로그
     */
    public void insertHmiTagLog(HashMap < String, Object > map) {
        String ANLY_CD = map.get("ANLY_CD").toString();
        if (ANLY_CD.equals("RUN")) {
            map.put("DCS", "펌프 가동");
        } else if (ANLY_CD.equals("STOP")) {
            map.put("DCS", "펌프 정지");
        } else if (ANLY_CD.equals("WAIT")) {
            map.put("DCS", "동작 대기");
        } else if (ANLY_CD.equals(CtrlCmdService.ANLY_VALVE_OPEN)) {
            map.put("DCS", "밸브 개도 설정");
        } else if (ANLY_CD.equals(CtrlCmdService.ANLY_VALVE_PULSE)) {
            map.put("DCS", "밸브 열림 펄스(OPENC)");
        } else if (ANLY_CD.equals(CtrlCmdService.ANLY_VALVE_PULSE_CLOSE)) {
            map.put("DCS", "밸브 닫힘 펄스(CLOSEC)");
        } else {
            //STATUS
            map.put("DCS", "상태 확인");
        }
        pumpMapper.insertHmiTagLog(map);
    }

    /**
     * 펌프 토출밸브 상태를 반환
     *
     * @param map 대상 펌프 정보
     * @return the list 대상 토출밸브 상태
     */
    public List < HashMap < String, Object >> selectValveStatusCheck(HashMap < String, Object > map) {
        return pumpMapper.selectValveStatusCheck(map);
    }

    /**
     * 펌프 가동 상태를 반환
     *
     * @param map 대상 펌프 정보
     * @return the list 대상 펌프 가동정보
     */
    public List < HashMap < String, Object >> selectPumpStatusCheck(HashMap < String, Object > map) {
        return pumpMapper.selectPumpStatusCheck(map);
    }



    /**
     * 제어 명령을 FLAG 3으로 초기화
     */
    public void initCtrTag() {
        pumpMapper.initCtrTag();
    }

    /**
     * 가장 마지막 예측 펌프 조합을 반환 (제외)
     *
     * @param map 대상 펌프 정보
     * @return the list 예측 펌프 조합
     */
    public List < HashMap < String, Object >> selectPumpPrdctOnOffLastList(HashMap < String, Object > map) {
        return pumpMapper.selectPumpPrdctOnOffLastList(map);
    }

    /**
     * 대상 펌프 그룹 예측 펌프 조합을 반환
     *
     * @param map 대상 펌프 정보
     * @return the list 예측 펌프 조합
     */
    public List < HashMap < String, Object >> selectPumpPrdctNowOnOffList(HashMap < String, Object > map) {

        return removeDecimalPoint(pumpMapper.selectPumpPrdctNowOnOffList(map), "FREQ");
    }

    /**
     * 중복 리스트 제거 (제외)
     *
     * @param list 대상 리스트
     * @param key  대상 키값
     * @return the list 데이터 리스트
     */
    public List < HashMap < String, Object >> removeDuplicatesList(List < HashMap < String, Object >> list, String key) {
        // LinkedHashMap을 사용하여 순서 유지 및 중복 제거
        Map < Object, HashMap < String, Object >> map = new LinkedHashMap < > ();
        for (HashMap < String, Object > item: list) {
            map.put(item.get(key), item);
        }
        return new ArrayList < > (map.values());
    }

    /**
     * 두 시간 차이 결과를 반환
     *
     * @param timeString1 기준 시간
     * @param timeString2 비교 시간
     * @return the boolean 30분 차이 여부
     */
    public boolean checkTimeDifference(String timeString1, String timeString2) {
        int timeDiff = 30;

        if (wpp_code.equals("gu")) {
            timeDiff = 5;
        }

        // 날짜와 시간 포맷터 생성
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");

        // 문자열을 LocalDateTime 객체로 변환
        LocalDateTime dateTime1 = LocalDateTime.parse(timeString1, formatter);
        LocalDateTime dateTime2 = LocalDateTime.parse(timeString2, formatter);

        // 두 시간의 차이 계산
        Duration duration = Duration.between(dateTime2, dateTime1);
        System.out.println("checkTimeDifference - duration:" + Math.abs(duration.toMinutes()));
        // 30분 (1800초) 차이가 나는지 확인
        return Math.abs(duration.toMinutes()) >= timeDiff;
    }

    /**
     * 두 시간 차이 값을 반환
     *
     * @param timeString1 기준 시간
     * @param timeString2 비교 시간
     * @return the int 시간 차이 값
     */
    public int checkTimeDifferenceValue(String timeString1, String timeString2) {

        int timeDiff = 30;

        if (wpp_code.equals("gu")) {
            timeDiff = 5;
        } else if(wpp_code.equals("wm")){
            timeDiff = 70;
        }
        // 날짜와 시간 포맷터 생성
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");

        // 문자열을 LocalDateTime 객체로 변환
        LocalDateTime dateTime1 = LocalDateTime.parse(timeString1, formatter);
        LocalDateTime dateTime2 = LocalDateTime.parse(timeString2, formatter);

        // 두 시간의 차이 계산
        Duration duration = Duration.between(dateTime2, dateTime1);

        // 30분 (1800초) 차이가 나는지 확인
        return (int) Math.abs(duration.toMinutes());
    }

    /**
     * 가장 마지막 제어를 성공한 명령 반환
     *
     * @return the hash map 제어 명령 반환
     */
    public HashMap < String, Object > selectLastEndCtrTagList() {
        return pumpMapper.selectLastEndCtrTagList();
    }

    /**
     * 펌프 제어 상태에 대한 알람 정보를 저장
     *
     * @param map 알람 정보
     */
    public void emsPumpAlarmInsert(HashMap < String, Object > map) {
        pumpMapper.emsPumpAlarmInsert(map);
    }

    /**
     * AI 운영 상태를 확인
     *
     * @return the boolean AI 모드 상태 여부
     */
    public Boolean aiControlStatus() {
        //AI운영 모드일때 펌프 조합이 변경되었는지 체크함
        List < HashMap < String, Object >> statusList = pumpMapper.selectAiStatus();
        boolean aiRecommend = false;

        for (HashMap < String, Object > statusItem: statusList) {
            String nowAiStatus = statusItem.get("AI_STATUS").toString();
            //부분 AI
            if (nowAiStatus.equals("0")) {
                aiRecommend = true;
            }
        }
        return aiRecommend;
    }

    /**
     * 각 펌프 그룹별 AI 모드 상태를 반환
     *
     * @return the int AI모드 상태
     */
    public int getAiControlStatus() {
        //AI추천 모드일때 펌프 조합이 변경되었는지 체크함
        List < HashMap < String, Object >> statusList = pumpMapper.selectAiStatus();
        int aiRecommend = 2;

        for (HashMap < String, Object > statusItem: statusList) {
            String nowAiStatus = statusItem.get("AI_STATUS").toString();
            //부분 AI
            if (nowAiStatus.equals("0")) {
                aiRecommend = 0;
                break;
            } else if (nowAiStatus.equals("1")) {
                aiRecommend = 1;
                break;
            }
        }
        return aiRecommend;
    }

    /**
     * 펌프 예측 조합을 반환
     *
     * @param map 대상 펌프 그룹
     * @return the list 펌프 예측 조합
     */
    public List < HashMap < String, Object >> selectPumpPrdctOnOffList(HashMap < String, Object > map) {
        return pumpMapper.selectPumpPrdctOnOffList(map);
    }

    /**
     * 10분 동안의 펌프 조합 결과가 일치하는지 확인
     *
     * @param list 10분간의 펌프 예측 조합 데이터
     * @return the boolean 펌프 조합 일치 여부
     */
    public boolean calculatePumpYnValueMatchRate(List < HashMap < String, Object >> list) {
        // 각 PUMP_IDX 별로 데이터를 그룹화
        Map < Object, List < HashMap < String, Object >>> groupedByPumpIdx = list.stream()
                .collect(Collectors.groupingBy(map -> map.get("PUMP_IDX")));

        boolean allGroupsMatch = true;

        for (Map.Entry < Object, List < HashMap < String, Object >>> entry: groupedByPumpIdx.entrySet()) {
            Object pumpIdx = entry.getKey();
            List < HashMap < String, Object >> pumpGroup = entry.getValue();

            // 첫 번째 PUMP_YN_VALUE 값을 기준값으로 설정
            int referenceValue = (int) pumpGroup.get(0).get("PUMP_YN_VALUE");

            // 각 그룹에서 얼마나 다른지 카운트
            long countMismatch = pumpGroup.stream()
                    .filter(map -> (int) map.get("PUMP_YN_VALUE") != referenceValue)
                    .count();

            // 차이가 있는 경우 출력
            if (countMismatch > 0) {
                System.out.println("PUMP_IDX: " + pumpIdx + " has " + countMismatch + " mismatched PUMP_YN_VALUE out of " + pumpGroup.size());
                allGroupsMatch = false;
            }
        }

        // 모든 그룹의 값이 동일하면 true 반환, 하나라도 다르면 false 반환
        return allGroupsMatch;
    }

    /**
     * 주파수 예측 결과가 10분동안 유지되는지 확인
     *
     * @param list 10분간의 펌프 예측 조합 데이터
     * @return the boolean 주파수 데이터 일치 여부
     */
    public boolean calculatePumpFreqValueMatchRate(List < HashMap < String, Object >> list) {
        // 각 PUMP_IDX 별로 데이터를 그룹화
        Map < Object, List < HashMap < String, Object >>> groupedByPumpIdx = list.stream()
                .collect(Collectors.groupingBy(map -> map.get("PUMP_IDX")));

        boolean allGroupsMatch = true;

        for (Map.Entry < Object, List < HashMap < String, Object >>> entry: groupedByPumpIdx.entrySet()) {
            Object pumpIdx = entry.getKey();
            List < HashMap < String, Object >> pumpGroup = entry.getValue();

            // 첫 번째 PUMP_YN_VALUE 값을 기준값으로 설정
            int referenceValue = (int) pumpGroup.get(0).get("FREQ");

            // 각 그룹에서 얼마나 다른지 카운트
            long countMismatch = pumpGroup.stream()
                    .filter(map -> (int) map.get("FREQ") != referenceValue)
                    .count();

            // 차이가 있는 경우 출력
            if (countMismatch > 0) {
                System.out.println("PUMP_IDX: " + pumpIdx + " has " + countMismatch + " mismatched PUMP_YN_VALUE out of " + pumpGroup.size());
                allGroupsMatch = false;
            }
        }

        // 모든 그룹의 값이 동일하면 true 반환, 하나라도 다르면 false 반환
        return allGroupsMatch;
    }

    /**
     * 마지막 10분동안의 펌프조합 결과가 일치해야 승인 (제외)
     *
     * @param map 대상 펌프 그룹
     * @return boolean 일치 여부
     */
    public Boolean pumpChangeRangeStatus(HashMap < String, Object > map) {
        List < HashMap < String, Object >> list = selectPumpPrdctOnOffList(map);

        if (list.isEmpty()) {
            return false;
        } else {
            return calculatePumpYnValueMatchRate(list);
        }
    }

    /**
     * 가동중인 펌프 그룹 정보를 반환
     *
     * @param nowPrdctlist 가동중인 펌프 그룹 리스트
     * @return the string 가동중인 펌프 그룹 정보
     */
    public String getRunPumpIdxStr(List < HashMap < String, Object >> nowPrdctlist) {
        StringBuffer sb = new StringBuffer();
        for (HashMap < String, Object > item: nowPrdctlist) {
            sb.append("PUMP_IDX:").append(item.get("PUMP_IDX").toString()).append("=").append(item.get("PUMP_YN").toString()).append(",");
        }
        if (sb.toString().length() > 1) {
            return sb.toString().substring(0, sb.toString().length() - 1);
        } else {
            return "None";
        }
    }

    /**
     * 로깅을 위한 제어 중인 데이터를 반환
     *
     * @param ctrList 제어 명령 리스트
     * @return 제어 명령 리스트 str
     */
    public String getCtrListStr(List < HashMap < String, Object >> ctrList) {
        StringBuffer sb = new StringBuffer();

        for (HashMap < String, Object > item: ctrList) {
            System.out.println("item:" + item.toString());
            sb.append(item.get("CTR_NM").toString()).append("|").append(item.get("ANLY_CD").toString());
            sb.append("|").append(item.get("FLAG").toString()).append("|").append(item.get("UPDT_TIME").toString());
            sb.append("\n###");
        }
        if (sb.toString().length() > 3) {
            return sb.toString().substring(0, sb.toString().length() - 3);
        } else {
            return "None";
        }
    }

    /**
     * 현재 가동중인 펌프 상태를 모두 반환
     *
     * @return the 펌프 가동 상태
     */
    public List < HashMap < String, Object >> nowRunAllPumpList() {
        List < HashMap < String, Object >> result = new ArrayList < > ();
        List < HashMap < String, Object >> useList = pumpMapper.nowRunAllPumpList();
        List < HashMap < String, Object >> priList = pumpMapper.nowRunAllPriPumpList();

        // 이중 루프 대신 PUMP_IDX 로 색인해 짝을 찾는다. 예전 방식은 priList 에 같은
        // PUMP_IDX 가 두 번 오면 같은 펌프를 두 번 담았다.
        Map < String, HashMap < String, Object >> priByPumpIdx = new HashMap < > ();
        for (HashMap < String, Object > subItem: priList) {
            Object key = subItem.get("PUMP_IDX");
            if (key != null) {
                priByPumpIdx.putIfAbsent(String.valueOf(key), subItem);
            }
        }

        for (HashMap < String, Object > item: useList) {
            //System.out.println("nowRunAllPumpList item :"+item.toString());
            Object key = item.get("PUMP_IDX");
            HashMap < String, Object > subItem = key == null ? null : priByPumpIdx.get(String.valueOf(key));
            if (subItem == null) {
                continue;
            }

            // 계측이 10분 넘게 끊기면 nowRunAllPriPumpList 의 PRI 가 NULL 로 온다.
            // 예전에는 여기서 NPE 가 났다. 짝을 못 찾은 경우와 똑같이 목록에서 뺀다.
            // 0 으로 채워 넣으면 안 된다 - 계측 공백을 '정지'로 오인해
            // changePumpList 가 가동 명령을 만들어낸다.
            Double pri = parseMeasuredValue(subItem.get("PRI"));
            if (pri == null) {
                continue;
            }
            item.put("PRI", pri);
            result.add(item);
        }
        //System.out.println("nowRunAllPumpList result :"+result.toString());
        return removeDecimalPoint(result, "FREQ");
    }

    /**
     * 계측값을 double 로 읽는다.
     *
     * NULL·빈 문자열·숫자가 아닌 값은 예외 대신 '미상'(null)으로 돌려준다.
     * TB_RAWDATA 조인이 10분 창을 벗어나면 NULL 이 오는 것이 정상 경로이기 때문이다.
     *
     * @param value 계측 컬럼 값
     * @return the double 읽어낸 값, 미상이면 null
     */
    private Double parseMeasuredValue(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        String text = value.toString().trim();
        if (text.isEmpty()) {
            return null;
        }
        try {
            return Double.parseDouble(text);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /**
     * 소수점 제거 함수 (제외)
     *
     * @param list 대상 리스트
     * @param tag  대상 키값
     * @return the 제거된 리스트 결과
     */
    public List < HashMap < String, Object >> removeDecimalPoint(List < HashMap < String, Object >> list, String tag) {
        for (HashMap < String, Object > map: list) {
            if (map.containsKey(tag)) {
                Object value = map.get(tag);
                if (value instanceof Number) {
                    Number numberValue = (Number) value;
                    map.put(tag, numberValue.intValue());
                }
            }
        }
        return list;
    }

    /**
     * 가동중인 인버터 펌프 정보를 반환
     *
     * @param map 대상 펌프 그룹
     * @return the hash map 인버터 펌프 정보
     */
    public HashMap < String, Object > nowRunAllPumpItem(HashMap < String, Object > map) {
        return removeDecimalPointHashMap(pumpMapper.nowRunAllPumpItem(map), "FREQ");
    }

    /**
     * hashmap의 소수점 데이터를 변환 (제외)
     *
     * @param map 대상 map
     * @param tag 대상 키값
     * @return the hash map 제거된 hashmap 데이터
     */
    public HashMap < String, Object > removeDecimalPointHashMap(HashMap < String, Object > map, String tag) {
        if (map.containsKey(tag)) {
            Object value = map.get(tag);
            if (value instanceof Number) {
                Number numberValue = (Number) value;
                map.put(tag, numberValue.intValue());
            }
        }
        return map;
    }

    /**
     * 펌프 주파수 변환을 확인
     *
     * @param map 대상 펌프
     * @return the hash map 인버터 펌프 제어 정보를 반환
     */
    public HashMap < String, Object > selectPumpFreqStatusCheck(HashMap < String, Object > map) {
        return pumpMapper.selectPumpFreqStatusCheck(map);
    }

    /**
     * AI 모드를 테스트 하기위한 상태 정보를 반환 (제외)
     *
     * @return the boolean 0은 AI모드 미동작, 1은 동작
     */
    public boolean checkTestMode() {
        HashMap < String, Object > item = pumpMapper.selectTestMode();

        if (item == null || item.isEmpty() || item.get("MODE") == null) {
            return false;
        }

        return "1".equals(item.get("MODE").toString());
    }

    /**
     * 제어 명령을 테스트하기 위한 값을 반환 (제외)
     *
     * @return the boolean 0은 제어명령을 전송하지 않음, 1은 제어 명령을 전송
     */
    public boolean checkCtrTestMode() {
        HashMap < String, Object > item = pumpMapper.selectCtrTestMode();

        if (item == null || item.isEmpty() || item.get("MODE") == null) {
            return false;
        }

        return "1".equals(item.get("MODE").toString());
    }

    /**
     * 대상 SCADA 데이터를 반환
     *
     * @param map 대상 태그
     * @return the hash map SCADA 데이터
     */
    public HashMap < String, Object > selectNowRawData(HashMap < String, Object > map) {
        return pumpMapper.selectNowRawData(map);
    }

    /**
     * 현재 인버터 펌프 정보를 반환(운문) (제외)
     *
     * @return the hash map 인버터 펌프 정보
     */
    public HashMap < String, Object > nowInverterPumpItem() {

        List < HashMap < String, Object >> list = pumpMapper.nowInverterPumpItem();
        if (list.size() == 1) {
            return list.get(0);
        } else {
            return null;
        }
    }

    /**
     * 선남 가압장 펌프를 모두 중단 (제외)
     */
    @Async("taskExecutor")
    public void pumpStop() {

        HashMap < String, Object > tempCtrItem = new HashMap < > ();
        tempCtrItem.put("TAG", "DEBUG");
        tempCtrItem.put("TIME", nowStringDate());

        String tagStr = "";

        ///780-379-PMC-101D
        ///780-379-PMC-102D
        ///780-379-PMC-103D
        Properties properties = new Properties();
        properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers()); // Kafka broker의 주소(properties 주소 설정에 따름)
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer < String, String > producer = new KafkaProducer < > (properties)) {
            HashMap < String, Object > sendItem = new HashMap < > ();

            sendItem.put("TAG", "780-379-PMC-101D");
            sendItem.put("TIME", nowStringDate());
            sendItem.put("VALUE", "1");
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            Thread.sleep(INIT_TIME);

            //초기화
            sendItem.put("TAG", "780-379-PMC-101D");
            sendItem.put("TIME", nowStringDate());
            sendItem.put("VALUE", "0");
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));

            Thread.sleep(SM_RESEND_TIME);

            sendItem.put("TAG", "780-379-PMC-102D");
            sendItem.put("TIME", nowStringDate());
            sendItem.put("VALUE", "1");
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            Thread.sleep(INIT_TIME);

            //초기화
            sendItem.put("TAG", "780-379-PMC-102D");
            sendItem.put("TIME", nowStringDate());
            sendItem.put("VALUE", "0");
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));

            Thread.sleep(SM_RESEND_TIME);

            sendItem.put("TAG", "780-379-PMC-103D");
            sendItem.put("TIME", nowStringDate());
            sendItem.put("VALUE", "1");
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            Thread.sleep(INIT_TIME);

            //초기화
            sendItem.put("TAG", "780-379-PMC-103D");
            sendItem.put("TIME", nowStringDate());
            sendItem.put("VALUE", "0");
            producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
            Thread.sleep(INIT_TIME);

        } catch (Exception e) {
            e.printStackTrace();
        }

        ///780-379-PMC-101D
        ///780-379-PMC-102D
        ///780-379-PMC-103D
        tempCtrItem.put("VALUE", "780-379-PMC-101D#780-379-PMC-102D#780-379-PMC-103D");
        tempCtrItem.put("ANLY_CD", "pumpCommand_stop");
        tempCtrItem.put("FLAG", 2);
        insertHmiTagLog(tempCtrItem);

    }

    /**
     * 선남 가압장 대상 펌프를 구동 (제외)
     *
     * @param map 대상 펌프 정보
     */
    @Async("taskExecutor")
    public void pumpStart(HashMap < String, Object > map) {
        ///780-379-PMC-101B
        ///780-379-PMC-102B
        ///780-379-PMC-103B

        String pump = map.get("pump").toString();

        Properties properties = new Properties();
        properties.put("bootstrap.servers", kafkaProperties.getBootstrapServers()); // Kafka broker의 주소(properties 주소 설정에 따름)
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        try (Producer < String, String > producer = new KafkaProducer < > (properties)) {
            HashMap < String, Object > sendItem = new HashMap < > ();

            HashMap < String, Object > tempCtrItem = new HashMap < > ();
            tempCtrItem.put("TAG", "DEBUG");
            tempCtrItem.put("TIME", nowStringDate());

            if (pump.equals("1")) {
                // 주파수
                sendItem.put("TAG", "780-379-SWC-1001");
                sendItem.put("TIME", nowStringDate());
                sendItem.put("VALUE", "50");
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                Thread.sleep(RESEND_TIME);

                //전송
                sendItem.put("TAG", "780-379-PMC-101B");
                sendItem.put("TIME", nowStringDate());
                sendItem.put("VALUE", "1");
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                Thread.sleep(INIT_TIME);

                //초기화
                sendItem.put("TAG", "780-379-PMC-101B");
                sendItem.put("TIME", nowStringDate());
                sendItem.put("VALUE", "0");
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                Thread.sleep(INIT_TIME);

                tempCtrItem.put("VALUE", "780-379-PMC-101B");
            } else if (pump.equals("2")) {
                //전송
                sendItem.put("TAG", "780-379-PMC-102B");
                sendItem.put("TIME", nowStringDate());
                sendItem.put("VALUE", "1");
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                Thread.sleep(INIT_TIME);

                //초기화
                sendItem.put("TAG", "780-379-PMC-102B");
                sendItem.put("TIME", nowStringDate());
                sendItem.put("VALUE", "0");
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                Thread.sleep(INIT_TIME);

                tempCtrItem.put("VALUE", "780-379-PMC-102B");

            } else if (pump.equals("3")) {
                // 주파수
                sendItem.put("TAG", "780-379-SWC-1002");
                sendItem.put("TIME", nowStringDate());
                sendItem.put("VALUE", "50");
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                Thread.sleep(RESEND_TIME);

                //전송
                sendItem.put("TAG", "780-379-PMC-103B");
                sendItem.put("TIME", nowStringDate());
                sendItem.put("VALUE", "1");
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                Thread.sleep(INIT_TIME);

                //초기화
                sendItem.put("TAG", "780-379-PMC-103B");
                sendItem.put("TIME", nowStringDate());
                sendItem.put("VALUE", "0");
                producer.send(new ProducerRecord < > ("ems_result", makeProducerJsonValue(sendItem)));
                Thread.sleep(INIT_TIME);

                tempCtrItem.put("VALUE", "780-379-PMC-103B");
            }

            tempCtrItem.put("ANLY_CD", "pumpCommand_start");
            tempCtrItem.put("FLAG", 2);
            insertHmiTagLog(tempCtrItem);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * (제외)
     * @return
     */
    private Double selectTPPCorrection(){
        double nowTPP = 0.0;
        HashMap<String, Object> dbValue = pumpMapper.selectTPPCorrection();
        if(dbValue != null)
        {
            nowTPP = Double.parseDouble(dbValue.get("MODE").toString());
        }
        return  nowTPP;
    }

    /**
     * (제외)
     * @return
     */
    private Double selectLifeTPP()
    {
        HashMap<String, Object> dbValue = pumpMapper.selectLifeTPP();
        double nowTPP = 10.8;
        if(dbValue != null)
        {
            nowTPP = Double.parseDouble(dbValue.get("MODE").toString());
        }
        return  nowTPP;
    }

    /**
     * (제외)
     * @return
     */
    public String selectGrSnPumpMode()
    {
        if(wpp_code.equals("gr"))
        {
            System.out.println("selectGrSnPumpMode:"+pumpMapper.selectGrSnPumpMode().get("MODE").toString());
        }

        return pumpMapper.selectGrSnPumpMode().get("MODE").toString();
    }

    // 이하 제외
    public void updateGrSnPumpMode(HashMap<String, Object> map)
    {
        pumpMapper.updateGrSnPumpMode(map);
    }

    public HashMap<String, Object> selectInvStatus()
    {
        return pumpMapper.selectInvStatus();
    }

    public int checkREACTModeCount()
    {
        return pumpMapper.checkREACTModeCount();
    }

    public void updateAiStatusForPump(HashMap<String, Object> map)
    {
        pumpMapper.updateAiStatusForPump(map);
    }

    public HashMap<String, Object> selectVVKStatusCheck()
    {
        return pumpMapper.selectVVKStatusCheck();
    }

    public HashMap<String, Object> selectCBBStatus(HashMap<String, Object> map)
    {
        return pumpMapper.selectCBBStatus(map);
    }


}