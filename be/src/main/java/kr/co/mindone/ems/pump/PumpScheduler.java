package kr.co.mindone.ems.pump;
/**
 * packageName    : kr.co.mindone.ems.pump
 * fileName       : PumpScheduler
 * date           : 24. 9. 8.
 * description    : 펌프제어를 담당하는 스케쥴러
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 8.        -            최초 생성
 */
import kr.co.mindone.ems.ai.AiService;
import kr.co.mindone.ems.alarm.AlarmService;
import kr.co.mindone.ems.pump.PumpService;
import kr.co.mindone.ems.setting.SettingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

import static kr.co.mindone.ems.common.SavingService.RANGE_DAY_AGO;
import static kr.co.mindone.ems.common.SavingService.RANGE_MONTH;
import static kr.co.mindone.ems.common.SavingService.RANGE_DAY;
import static kr.co.mindone.ems.common.SavingService.RANGE_YEAR;

@Service
@Profile("!dev && !gm & !hp & !ji & !hy & !ss & !gm2 & !hp2 & !ji2 & !hy2")
@PropertySource("classpath:application-${spring.profiles.active}.properties")
public class PumpScheduler {

    @Autowired
    private PumpService pumpService;

    @Autowired
    private AiService aiService;

    @Autowired
    private AlarmService alarmService;

    @Autowired
    private CtrlCmdService ctrlCmdService;

    public int TRY_COUNT = 0;

    @Value("${spring.profiles.active}")
    private String wpp_code;

    /**
     * 펌프를 실제 동작시킴
     */
    //@Scheduled(cron = "0,30 * * * * *") //군산, 부안 30초 주기
    @Scheduled(cron = "0 * * * * *") //그외 정수장 1분
    public void pumpTask() {
        //AI추천 모드일때 펌프 조합이 변경되었는지 체크함
        System.out.println("pumpTask - " + wpp_code + "-" + pumpService.checkTestMode());
        if ((wpp_code.equals("gs") || wpp_code.equals("gu") || wpp_code.equals("ba") || wpp_code.equals("wm") ||
                wpp_code.equals("gr") || wpp_code.equals("ss") || wpp_code.equals("dev")) && pumpService.checkTestMode()) {
            printDateTime("pumpTask");

            boolean aiRecommendStatus = aiService.aiRecommendStatus();
            boolean aiControlStatus = aiService.aiControlStatus();
            System.out.println("pumpTask - aiRecommendStatus:" + aiRecommendStatus + " | aiControlStatus:" + aiControlStatus);
            if (aiRecommendStatus) {
                HashMap < String, Object > map = new HashMap < > ();
                map.put("FLAG", 0);
                List < HashMap < String, Object >> ctrReadyList = pumpService.selectCtrTagList(map);
                map.put("FLAG", 1);
                List < HashMap < String, Object >> ctrRunningList = pumpService.selectCtrTagList(map);
                //진행중인 프로세스가 있는 경우 다음 동작을 확인하지 않음
                System.out.println("#pumpTask-Recommend: " + ctrReadyList.size() + " / " + ctrRunningList.size() + " = " + pumpService.checkCtrTestMode());
                if (!ctrReadyList.isEmpty() && ctrRunningList.isEmpty() && pumpService.checkCtrTestMode()) {
                    System.out.println("#Start aiRecommend pumpCommandTask");
                    pumpService.pumpCommandTask(ctrReadyList);
                }
                //pumpStatusTask
            }
            //AI운전일때 동작
            else if (aiControlStatus) {

                printDateTime("pumpTask");

                HashMap < String, Object > map = new HashMap < > ();
                map.put("FLAG", 0);
                List < HashMap < String, Object >> ctrReadyList = pumpService.selectCtrTagList(map);
                map.put("FLAG", 1);
                List < HashMap < String, Object >> ctrRunningList = pumpService.selectCtrTagList(map);
                //진행중인 프로세스가 있는 경우 다음 동작을 확인하지 않음
                System.out.println("#pumpTask-aiControl: " + ctrReadyList.size() + " / " + ctrRunningList.size() + " = " + pumpService.checkCtrTestMode());
                if (!ctrReadyList.isEmpty() && ctrRunningList.isEmpty() && pumpService.checkCtrTestMode()) {
                    //HashMap<String, Object> pumpStatus = pumpService.pumpCommandStatus();
                    //if(Boolean.parseBoolean(pumpStatus.get("isChange").toString()))
                    /*if (!pumpService.isRunningStatus()) {

                    }*/
                    System.out.println("#Start aiControl pumpCommandTask");
                    pumpService.pumpCommandTask(ctrReadyList);
                }
            }
        }
    }

    /**
     * AI 운전을 위한 펌프 조합생성
     */
    //@Scheduled(cron = "20 * * * * *") // 실제 1분 20초 마다
    @Scheduled(cron = "20 */5 * * * *") // 실제 5분마다
    //@Scheduled(cron = "0 * * * * *") //테스트 1분
    public void pumpAiControlTask() {
        //AI운전 모드일때만 동작
        //System.out.println("pumpAiControlTask aiControlStatus:"+aiService.aiControlStatus());
        //고산 통합

        printDateTime("pumpAiControlTask");

        // 군산: 5분 제어 판단(CtrlCmdService)이 펌프 제어를 넘겨받았으면 기존 조합 생성은 쉰다.
        // 두 생성원이 같은 대기열에 쓰면 충돌한다. ctrl.cmd.consumer.enabled=false 면 기존 동작 그대로다.
        if (wpp_code.equals("gu") && ctrlCmdService.isPumpControlActive()) {
            System.out.println("pumpAiControlTask skip - gu 5분 제어 판단 연계 활성");
            return;
        }

        //System.out.println("pumpAiControlTask Start -"+formattedDateTime);

        if ((wpp_code.equals("gs") || wpp_code.equals("gu") || wpp_code.equals("ba") || wpp_code.equals("wm") || wpp_code.equals("gr")) && pumpService.checkTestMode()) {
            if (pumpService.aiControlStatus()) {
                List < String > pumpGrpStr = pumpService.selectAiPumpGrpListStr(PumpService.AI_CONTROL);

                HashMap < String, Object > readyMap = new HashMap < > ();
                readyMap.put("FLAG", 0);
                List < HashMap < String, Object >> ctrReadyList = pumpService.selectCtrTagList(readyMap);
                readyMap.put("FLAG", 1);
                List < HashMap < String, Object >> ctrRunningList = pumpService.selectCtrTagList(readyMap);

                boolean pumpRunningStatus = true;

                if(!ctrReadyList.isEmpty() || !ctrRunningList.isEmpty())
                {
                    pumpRunningStatus = false;
                }


                HashMap < String, Object > pumpStatus = pumpService.pumpCommandStatusMin(pumpGrpStr);
                //HashMap < String, Object > pumpStatus = pumpService.pumpCommandStatus(pumpGrpStr);
                System.out.println("#pumpAiControlTask pumpStatus:" + pumpStatus.get("isChange").toString()+"/"+ pumpRunningStatus+ ", pumpGrpStr:" + pumpGrpStr);
                if (Boolean.parseBoolean(pumpStatus.get("isChange").toString()) && pumpRunningStatus) {
                    //changePumpList(false)
                    //HashMap < String, Object > map = new HashMap < > ();
                    //map.put("PUMP_GRP_LIST", pumpGrpStr);
                    //if (!pumpService.changePumpList(true, pumpGrpStr).isEmpty() && pumpService.pumpChangeRangeStatus(map)) {
                    if (!pumpService.changePumpList(true, pumpGrpStr).isEmpty()) {
                        System.out.println("pumpAiControlTask pumpCommand Start");

                        /*if(wpp_code.equals("gr"))
                        {
                            System.out.println("pumpCommand gr - selectGrSnPumpMode:"+pumpService.selectGrSnPumpMode());

                            if(pumpService.selectGrSnPumpMode().equals("0"))
                            {
                                pumpGrpStr.removeIf(s -> s.equals("3"));
                            }
                            pumpGrpStr.removeIf(s -> s.equals("3"));
                        }*/

                        if (wpp_code.equals("gs")) {
                            pumpService.pumpCommandGS(pumpGrpStr);
                        } else if (wpp_code.equals("wm")) {
                            pumpService.pumpCommandWM(pumpGrpStr);
                            //pumpService.pumpCommandWMTemp(pumpGrpStr);
                        } else {
                            pumpService.pumpCommand(pumpGrpStr);
                        }
                    }
                }
            }
        }
    }

    /**
     * 제어가 시작된 명령의 실제 수행된 상태를 확인
     * gs 인증에서는 X
     */
    @Scheduled(cron = "0,30 * * * * *")
    public void pumpStatusTask() {
        //펌프 토출밸브 on/off 체크, 펌프 가동상태 확인
        if ((wpp_code.equals("gs") || wpp_code.equals("gu") || wpp_code.equals("gr") || wpp_code.equals("wm") ||
                wpp_code.equals("ss") || wpp_code.equals("ba") || wpp_code.equals("dev")) && pumpService.checkTestMode()) {
            if (aiService.aiRecommendStatus() || aiService.aiControlStatus()) {
                printDateTime("pumpStatusTask");
                HashMap < String, Object > map = new HashMap < > ();
                map.put("FLAG", 1);
                map.put("ANLY_CD", "STATUS");
                List < HashMap < String, Object >> ctrRunningList = pumpService.selectCtrTagList(map);

                if(wpp_code.equals("wm"))
                {
                    map.put("ANLY_CD", "SYNC_STATUS");
                    //map.put("FLAG", 0);
                    List < HashMap < String, Object >> ctrSyncRunningList = pumpService.selectCtrTagList(map);
                    System.out.println("SYNC_STATUS ctrSyncRunningList size:"+ctrSyncRunningList.size());
                    if(!ctrSyncRunningList.isEmpty())
                    {
                        pumpService.pumpStatusTaskSync(ctrSyncRunningList);
                    }
                }

                if (!ctrRunningList.isEmpty()) {
                    if(wpp_code.equals("gr") || wpp_code.equals("ba") || wpp_code.equals("wm"))
                    {
                        TRY_COUNT += pumpService.pumpStatusTaskPumpOnly(ctrRunningList);

                    }
                    else {
                        TRY_COUNT += pumpService.pumpStatusTask(ctrRunningList);
                    }

                } else {
                    TRY_COUNT = 0;
                }


                if(wpp_code.equals("ba"))
                {
                    map.put("ANLY_CD", "VVK");
                    map.put("FLAG", 1);
                    List < HashMap < String, Object >> ctrVVKRunningList = pumpService.selectCtrTagList(map);
                    if(!ctrVVKRunningList.isEmpty())
                    {
                        pumpService.VVKStatusTask(ctrVVKRunningList);
                    }
                }

                //System.out.println("#pumpStatusTask: " + pumpService.getCtrListStr(ctrRunningList));


                /*
                map.put("ANLY_CD", "FREQ");
                List<HashMap<String, Object>> ctrRunningFreqList = pumpService.selectCtrTagList(map);

                if (!ctrRunningList.isEmpty() || !ctrRunningFreqList.isEmpty()) {
                    if(!ctrRunningList.isEmpty())
                    {
                        TRY_COUNT += pumpService.pumpStatusTask(ctrRunningList);
                    }
                    if(!ctrRunningFreqList.isEmpty()) {
                        TRY_COUNT += pumpService.pumpStatusTask(ctrRunningFreqList);
                    }
                } else {
                    TRY_COUNT = 0;
                }*/
                /*
                if (TRY_COUNT > 15 && !ctrRunningList.isEmpty()) {
                    //TINE OVER
                    //분석모드로 변경
                    map.put("STATUS", 2);
                    aiService.updateAiStatus(map);

                    HashMap<String, Object> ctrRunItem = ctrRunningList.get(0);


                    //부분 AI 알람 생성
                    HashMap<String, Object> alarm = new HashMap<>();
                    alarm.put("alr_typ", "PUMP");
                    alarm.put("nowDate", pumpService.nowStringDate());
                    alarm.put("msg", "[" + ctrRunItem.get("CTR_NM").toString() + "] 제어 결과를 확인 할 수 없습니다.|");
                    //alarm.put("msg", "[" + ctrRunItem.get("CTR_NM").toString() + "] 제어 결과를 확인 할 수 없어 분석모드로 변경됩니다.|");
                    alarm.put("link", "");
                    System.out.println("alarm: " + alarm.toString());
                    pumpService.emsPumpAlarmInsert(alarm);

                    TRY_COUNT = 0;
                }*/
            }
        }
        //WM 테스트 코드
        /*printDateTime("#######   pumpStatusTask WM TEST   #######");
        HashMap < String, Object > map = new HashMap < > ();
        map.put("FLAG", 0);

        if(wpp_code.equals("wm"))
        {
            map.put("ANLY_CD", "SYNC_STATUS");
            List < HashMap < String, Object >> ctrSyncRunningList = pumpService.selectCtrTagList(map);
            if(!ctrSyncRunningList.isEmpty())
            {
                pumpService.pumpStatusTaskSync(ctrSyncRunningList);
            }
        }*/
    }

    private void printDateTime(String name)
    {
        Date currentDate = new Date();
        // 출력할 형식을 지정합니다. 예: "yyyy-MM-dd HH:mm:ss"
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        // 현재 날짜와 시간을 형식화하여 문자열로 변환합니다.
        String formattedDateTime = dateFormat.format(currentDate);
        System.out.println(name+" cron job expression:: " + formattedDateTime);
    }

}