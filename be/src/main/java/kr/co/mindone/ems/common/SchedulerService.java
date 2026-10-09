package kr.co.mindone.ems.common;
/**
 * packageName    : kr.co.mindone.common
 * fileName       : SchedulerService
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import kr.co.mindone.ems.ai.AiService;
import kr.co.mindone.ems.alarm.AlarmService;
import kr.co.mindone.ems.drvn.DrvnConfig;
import kr.co.mindone.ems.drvn.DrvnService;
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
import java.time.Duration;
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
@Profile("!dev")
@PropertySource("classpath:application-${spring.profiles.active}.properties")
public class SchedulerService {
    @Autowired
    private CommonService commonService;

    @Autowired
    private SavingService savingService;

    @Autowired
    private SettingService settingService;
    @Autowired
    private DrvnService drvnService;
    @Autowired
    private DrvnConfig drvnConfig;

    @Value("${tag.value.co2}")
    private double co2_value;

    @Autowired
    private AiService aiService;

    public int TRY_COUNT = 0;

    @Value("${spring.profiles.active}")
    private String wpp_code;

    /**
     * 전력 절감량 계산 스케쥴링
     */
    //@Scheduled(cron = "0 * * * * *")
    //@Scheduled(cron = "0 0 * * * *") // 매 시간 0분
    public void savingCalculatorTask() {
        LocalTime nowTime = LocalTime.now();
        int currentHour = nowTime.getHour(); // 현재 시간

        Date currentDate = new Date();

        // 출력할 형식을 지정합니다. 예: "yyyy-MM-dd HH:mm:ss"
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        // 현재 날짜와 시간을 형식화하여 문자열로 변환합니다.
        String formattedDateTime = dateFormat.format(currentDate);
        //System.out.println("DPCCalculator cron job expression:: " + formattedDateTime);

        if (currentHour == 0) //자정에만 동작
        {
            savingService.savingCalculationInsert(RANGE_DAY, "none");
            savingService.savingCalculationInsert(RANGE_DAY_AGO, "none");
            savingService.savingCalculationInsert(RANGE_MONTH, "none");
        }
    }

    /**
     * 전력절감량 계산(개선)
     */
    @Scheduled(cron = "30 * * * * *")
    public void savingDayCalculatorTask() {
        LocalTime nowTime = LocalTime.now();
        int currentHour = nowTime.getHour(); // 현재 시간

        Date currentDate = new Date();

        // 출력할 형식을 지정합니다. 예: "yyyy-MM-dd HH:mm:ss"
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        // 현재 날짜와 시간을 형식화하여 문자열로 변환합니다.
        String formattedDateTime = dateFormat.format(currentDate);
        //System.out.println("DPCCalculator cron job expression:: " + formattedDateTime);

        savingService.savingCalculationInsert(RANGE_DAY, "none");
    }

    /**
     * 오래된 데이터 삭제 스케쥴링
     */
    @Scheduled(cron = "0 0 0 * * *")
    public void oldDataDeleteTask(){
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
        LocalDateTime currentTime = LocalDateTime.now();
        String nowDateTime = currentTime.format(formatter);

        commonService.deleteRawData(nowDateTime);
    }

    @Scheduled(cron = "10 0 0 * * *")
    public void oldDataDeleteTask1(){
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
        LocalDateTime currentTime = LocalDateTime.now();
        String nowDateTime = currentTime.format(formatter);

        commonService.deleteEpanetFP(nowDateTime);
    }

    @Scheduled(cron = "20 0 0 * * *")
    public void oldDataDeleteTask2(){
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
        LocalDateTime currentTime = LocalDateTime.now();
        String nowDateTime = currentTime.format(formatter);

        commonService.deleteEpanetFR(nowDateTime);
    }

    /**
     * Co2및 전력 절감
     */
    //@Scheduled(cron = "30 2 * * * *") // 매 시간 0분
    @Scheduled(cron = "30 * * * * *")
    public void calPwrPrdct() {
        LocalTime nowTime = LocalTime.now();
        Date currentDate = new Date();
        // 출력할 형식을 지정합니다. 예: "yyyy-MM-dd HH:mm:ss"
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:00:00");
        SimpleDateFormat dateFormat2 = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");

        String nowDate = dateFormat.format(currentDate);
        String runDate = dateFormat2.format(currentDate);

       // System.out.println("["+runDate+"] calPwrPrdct =>" +nowDate);

//        if(!wpp_code.matches("hy|ji")){
//        }
        if (wpp_code.equals("ss") || wpp_code.equals("gs"))
        {
            aiService.CalPrdctPwr(nowDate); //pwi
        }
        else {
            aiService.CalPrdctPwrOld(nowDate); //pwq
        }
    }

    /**
     * AI모드 제어 감지 스케쥴링
     */
    @Scheduled(cron = "0 * * * * *")
    public void aiModeRstSaving()
    {
//        Date currentDate = new Date();
//        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:00");
//        String runDate = dateFormat.format(currentDate);
            String runDate = aiService.getAIPumpTime();
            if(wpp_code.equals("gs") || wpp_code.equals("ba") || wpp_code.equals("gu")
                    || wpp_code.equals("wm") || wpp_code.equals("gr"))
            {
                List<HashMap<String, Object>> aiList = commonService.selectAiStatusAllgrp();

                for(HashMap<String, Object> aiItem: aiList)
                {
                    String pump_grp = (String) aiItem.get("PUMP_GRP");
    //                if (!wpp_code.equals("gs") || !aiItem.get("PUMP_GRP").equals("2")) {
    //                }
                    HashMap<String, String> rstItem = new HashMap<>();
                    rstItem.put("RGSTR_TIME", runDate);
                    rstItem.put("PUMP_GRP", pump_grp);
                    rstItem.put("AI_MODE", aiItem.get("VALUE").toString());
                    rstItem.put("IS_WORK", "0");
                    HashMap<String, String> drvnParam = new HashMap<>();
                    drvnParam.put("nowDate", runDate);
                    drvnParam.put("pump_grp", pump_grp);
                    HashMap<String, String> pumpDrvnMap = aiService.pumpDrvnMinute(drvnParam);
                    if(pumpDrvnMap == null || pumpDrvnMap.isEmpty()){
                        return;
                    }else{

                        HashMap<String, String> aiStatusPumpComb = aiService.createPumpCombStatus(pumpDrvnMap, pump_grp);

                        String curPumpStr = aiStatusPumpComb.get("curPump").toString();
                        String prePumpStr = aiStatusPumpComb.get("prePump").toString();
                        if(curPumpStr.equals(prePumpStr))
                        {
                            rstItem.put("IS_WORK", "1");
                        }
                        else {
                            rstItem.put("IS_WORK", "0");
                        }

                        rstItem.putAll(aiStatusPumpComb);
                    }



                    commonService.insertAiStatusRST(rstItem);
                }
            }
    }

    @Scheduled(cron = "0 0 * * * *")
//    @Scheduled(fixedRate = 30000)
    public void calPumpCombPwrUnitCost(){
        Date currentDate = new Date();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:00:00");

        String nowDate = dateFormat.format(currentDate);
        Map<String, Object> param = new HashMap<>();
        param.put("ts", nowDate);
        List<HashMap<String, Object>> grpList = commonService.selectPumpGroupItem();

        List<HashMap<String, Object>> insertArr = new ArrayList<>();
        if(wpp_code.equals("gs") || wpp_code.equals("gs-auth")){

            HashMap<Integer, HashMap<String, Double>> grpFlowPressure = new HashMap<>();

            Map<Integer, Double> pwrPumpMap = new HashMap<>();
            pwrPumpMap.put(1, -4.4517);
            pwrPumpMap.put(2, 7.9505);
            pwrPumpMap.put(3, 8.3894);
            pwrPumpMap.put(4, 10.7594);
            pwrPumpMap.put(5, 11.9779);
            pwrPumpMap.put(6, 12.9400);
            pwrPumpMap.put(7, 9.8855);
            pwrPumpMap.put(8, 13.7385);
            pwrPumpMap.put(9, 11.9917);
            pwrPumpMap.put(10, 13.6098);
            pwrPumpMap.put(11, 8.5532);


            Set<Integer> grpSet = grpFlowPressure.keySet();
            List<HashMap<String, Object>> combs = drvnService.getGrpPumpComb(0);

            for(HashMap<String, Object> combMap:combs){
                String comb = combMap.get("PUMP_COMB").toString();
                double minFlow = (double) combMap.get("FC_MIN_VAL");
                double maxFlow = (double) combMap.get("FC_MAX_VAL");


                double avgFlow = (maxFlow + minFlow) /2;
                double pressure = drvnConfig.pressureCalValue(avgFlow, combMap, 0);
                System.out.println("flow :"+ avgFlow +", pressure :"+pressure);
                double pwr = (avgFlow * 0.0496) + (pressure * -5.8793) + 71.4878;
                    String[] numberStrings = comb.split(",");


                for(String pump:numberStrings){
                    int pumpInt = Integer.parseInt(pump);
                    pwr += (pwrPumpMap.get(pumpInt) * 60);
        }

            HashMap<String, Object> insertMap = new HashMap<>();


            double pwrUnitCost = (avgFlow != 0) ? pwr / avgFlow : 0.0;
            insertMap.put("comb", comb);
            insertMap.put("pwr", pwr);
            insertMap.put("flow", avgFlow);
            insertMap.put("pwrUnitCost", pwrUnitCost);

            insertArr.add(insertMap);



            }
        }

        drvnService.insertCombPwrUnit(insertArr);
    }
}
