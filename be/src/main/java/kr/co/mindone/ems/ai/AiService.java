package kr.co.mindone.ems.ai;
/**
 * packageName    : kr.co.mindone.ems.ai
 * fileName       : AiService
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import kr.co.mindone.ems.alarm.AlarmService;
import kr.co.mindone.ems.common.CommonService;
import kr.co.mindone.ems.drvn.DrvnMapper;
import kr.co.mindone.ems.drvn.DrvnService;
import kr.co.mindone.ems.pump.PumpService;
import kr.co.mindone.ems.setting.SettingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Lazy;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.LocalTime;
import java.util.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

@PropertySource("classpath:application-${spring.profiles.active}.properties")
@Service
public class AiService {
    @Autowired
    private AiMapper aiMapper;

    @Autowired
    private SettingService settingService;

    @Autowired
    private CommonService commonService;

    @Autowired
    private PumpService pumpService;

    @Autowired
    private DrvnMapper drvnMapper;

    @Autowired
    @Lazy
    private AlarmService alarmService;

    @Value("${spring.profiles.active}")
    private String wpp_code;

    private final ArrayList < Double > randomList = new ArrayList < > ();

    private int nowHour = 25;
    private Boolean pass = true;

    /**
     * 펌프 상태를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 상태를 조회
     */
    HashMap < String, Object > pumpSelect(HashMap < String, Object > map) {
        HashMap < String, Object > returnMap = new HashMap < > ();
        String combString = drvnMapper.getPumpCombTime();
        map.put("combDate", combString);
        if (wpp_code.equals("ba")) {
            returnMap.put("data", aiMapper.pumpSelectYn(map));
            returnMap.put("pumpStatus", aiMapper.pumpStatusSelectYn(map));
        } else if (wpp_code.equals("gs")) {
            returnMap.put("data", aiMapper.pumpSelectYn(map));
            returnMap.put("pumpStatus", aiMapper.pumpStatusSelectYn(map));
        } else {
            returnMap.put("data", aiMapper.pumpSelect(map));
            returnMap.put("pumpStatus", aiMapper.pumpStatusSelect(map));
        }

        //returnMap.put("data3", aiMapper.pumpSelect3());
        return returnMap;
    }

    /**
     * 펌프 그룹 정보를 출력하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 그룹 정보
     */
    HashMap < String, Object > pumpGrpSelect(HashMap < String, Object > map) {
        HashMap < String, Object > returnMap = new HashMap < > ();
        returnMap.put("data", aiMapper.pumpGrpSelect(map));
        //returnMap.put("pumpStatus", aiMapper.pumpStatusSelect(map));
        //returnMap.put("data3", aiMapper.pumpSelect3());
        return returnMap;
    }

    /**
     * 펌프 상태를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 상태를 조회
     */
    HashMap < String, Object > pumpSelect_new(HashMap < String, Object > map) {
        HashMap < String, Object > returnMap = new HashMap < > ();
        returnMap.put("data", aiMapper.pumpSelect_new(map));
        //returnMap.put("data2", aiMapper.pumpSelect2());
        //returnMap.put("data3", aiMapper.pumpSelect3());
        return returnMap;
    }

    /**
     * 펌프 상태 목록을 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 상태 목록
     */
    HashMap < String, Object > pumpSelectList(HashMap < String, Object > map) {
        HashMap < String, Object > returnMap = new HashMap < > ();
        returnMap.put("data", aiMapper.pumpSelect(map));
        return returnMap;
    }

    /**
     * 펌프 상태 목록을 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 상태 목록
     */
    HashMap < String, Object > pumpSelectList_new(HashMap < String, Object > map) {
        HashMap < String, Object > returnMap = new HashMap < > ();

        List < HashMap < String, Object >> returnMapList1 = aiMapper.pumpSelectList_1(map);
        List < HashMap < String, Object >> returnMapList2 = aiMapper.pumpSelectList_2(map);
        List < HashMap < String, Object >> returnMapList3 = aiMapper.pumpSelectList_3(map);

        List < HashMap < String, Object >> returnMapList = new ArrayList < > ();

        for (HashMap < String, Object > item3: returnMapList3) {
            for (HashMap < String, Object > item2: returnMapList2) {
                if (item3.get("PRDCT_TIME").toString().equals(item2.get("PRDCT_TIME").toString())) {
                    item3.put("TUBE_PRSR_PRDCT", Double.parseDouble(item2.get("TUBE_PRSR_PRDCT").toString().replaceAll(",", "")));
                }
            }
            for (HashMap < String, Object > item1: returnMapList1) {
                if (item3.get("PRDCT_TIME").toString().equals(item1.get("PRDCT_TIME").toString())) {
                    item3.put("PRDCT_MEAN", Double.parseDouble(item1.get("PRDCT_MEAN").toString().replaceAll(",", "")));
                }
            }
            String temp = item3.get("PWR_PRDCT").toString().replaceAll(",", "");
            item3.put("PWR_PRDCT", temp);
            returnMapList.add(item3);
        }
        returnMap.put("data", returnMapList);
        return returnMap;
    }

    /**
     * 배수지 태그 값 목록을 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 배수지 태그 태그 값 목록
     */
    List < HashMap < String, Object >> selectTnkTagValueList(HashMap < String, Object > map) {
        return aiMapper.selectTnkTagValueList(map);
    }

    /**
     * 펌프 태그 값 목록을 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 태그 값 목록
     */
    List < HashMap < String, Object >> selectPumpTagValueList(HashMap < String, Object > map) {
        return aiMapper.selectPumpTagValueList(map);
    }

    /**
     * AI 켜기/끄기 목록을 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return AI 켜기/끄기 목록
     */
    List < HashMap < String, Object >> aiOnOffList(HashMap < String, Object > map) {
        return aiMapper.aiOnOffList(map);
    }
    /**
     * 배수지 태그 범위 리스트를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 배수지 태그 범위 리스트
     */
    List < HashMap < String, Object >> selectWpTnkTagRangeList(HashMap < String, Object > map) {
        return aiMapper.selectWpTnkTagRangeList(map);
    }

    /**
     * 시간별 배수지 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 시간별 배수지 데이터 리스트
     */
    List < HashMap < String, Object >> selectTankDataHourList(HashMap < String, Object > map) {
        return aiMapper.selectTankDataHourList(map);
    }

    /**
     * 시간별 배수지 데이터 합계를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 시간별 배수지 데이터 합계 리스트
     */
    List < HashMap < String, Object >> selectTankDataHourSumList(HashMap < String, Object > map) {
        return aiMapper.selectTankDataHourSumList(map);
    }

    /**
     * 배수지의 순간 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 배수지 순간 데이터 리스트
     */
    List < HashMap < String, Object >> tankInstantaneous(HashMap < String, Object > map) {
        return aiMapper.tankInstantaneous(map);
    }

    /**
     * 전력 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 전력 데이터 리스트
     */
    List < HashMap < String, Object >> selectElcPwqList(HashMap < String, Object > map) {
        return aiMapper.selectElcPwqList(map);
    }

    /**
     * 최대 피크 값을 조회하는 메서드
     * @return 최대 피크 리스트
     */
    List < HashMap < String, Object >> peak_max() {
        return aiMapper.peak_max();
    }

    /**
     * 펌프 PRI 태그 상태를 조회하는 메서드
     * @return 펌프 PRI 태그 상태 리스트
     */
    List < HashMap < String, Object >> selectPumpPRITagStatus() {
        return aiMapper.selectPumpPRITagStatus();
    }

    /**
     * 펌프 FRI 태그 상태를 조회하는 메서드
     * @return 펌프 FRI 태그 상태 리스트
     */
    List < HashMap < String, Object >> selectPumpFRITagStatus() {
        return aiMapper.selectPumpFRITagStatus();
    }

    /**
     * 펌프 SPI 태그 상태를 조회하는 메서드
     * @return 펌프 SPI 태그 상태 리스트
     */
    List < HashMap < String, Object >> selectPumpSPITagStatus() {
        return aiMapper.selectPumpSPITagStatus();
    }

    /**
     * 펌프별 전력 상태를 조회하는 메서드
     * @return 펌프 전력 상태 리스트
     */
    List < HashMap < String, Object >> selectPumpPwiStatus() //펌프 각자 전력
    {
        return aiMapper.selectPumpPwiStatus();
    }

    /**
     * 밸브 상태를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 밸브 상태 리스트
     */
    List < HashMap < String, Object >> selectValve(HashMap < String, Object > map) //펌프 가동 대수
    {
        return aiMapper.selectValve(map);
    }

    /**
     * 전력 피크 분석 데이터를 조회하는 메서드
     * @return 전력 피크 분석 리스트
     */
    List < HashMap < String, Object >> selectPeakControl() //전력피크 분석
    {
        return aiMapper.selectPeakControl();
    }

    /**
     * 펌프의 온/오프 상태를 조회하는 메서드
     * @return 펌프 온/오프 상태 리스트
     */
    List < HashMap < String, Object >> selectPumpOnOffStatus() {
        return aiMapper.selectPumpOnOffStatus();
    }

    /**
     * 펌프 사용 상태를 조회하는 메서드
     * @return 펌프 사용 상태 리스트
     */
    public List < HashMap < String, Object >> getPumpUseStatus() {
        return aiMapper.getPumpUseStatus();
    }

    /**
     * 시설의 상위 3개의 전력 데이터를 조회하는 메서드
     * @param params 조회에 필요한 파라미터
     * @return 시설의 상위 3개의 전력  데이터 리스트
     */
    public List < HashMap < String, Object >> getTop3(HashMap < String, Object > params) {
        return aiMapper.getTop3(params);
    }

    /**
     * 알람 데이터를 조회하는 메서드
     * @return 알람 데이터 리스트
     */
    List < HashMap < String, Object >> selectAlarm() {
        return aiMapper.selectAlarm();
    }

    /**
     * 배수지 리스트를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 배수지 리스트
     */
    List < HashMap < String, Object >> selectTankList(HashMap < String, Object > map) {
        return aiMapper.selectTankList(map);
    }

    /**
     * 피크 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 피크 데이터 리스트
     */
    List < HashMap < String, Object >> peakSelect(HashMap < String, Object > map) {
        return aiMapper.peakSelect(map);
    }

    /**
     * 실시간 요금 비율을 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 요금 비율 리스트
     */
    List < HashMap < String, Object >> selectRtRate(HashMap < String, Object > map) {
        return aiMapper.selectRtRate(map);
    }

    /**
     * 펌프 리스트를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 리스트
     */
    public List < HashMap < String, Object >> selectPumpList(HashMap < String, Object > map) {
        return aiMapper.selectPumpList();
    }

    /**
     * 전력 합계 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 전력 합계 리스트
     */
    List < HashMap < String, Object >> selectPwrSumList(HashMap < String, Object > map) {
        return aiMapper.selectPwrSumList(map);
    }

    /**
     * 펌프 예측 조합을 조회하는 메서드
     * @return 펌프 예측 조합
     */
    public HashMap < String, Object > selectPumpPrdct() {
        HashMap < String, Object > returnMap = new HashMap < > ();
        returnMap.put("optMode", aiMapper.getOptMode());

        List < Map < String, Object >> pressureData = aiMapper.getPressureData();
        for (Map < String, Object > map: pressureData) {
            returnMap.put((String) map.get("DISPLAY_ID"), map.get("DEFAULT_VALUE"));
        }
        return returnMap;
    }

    /**
     * 펌프 정보를 조회하는 메서드
     * @return 펌프 정보를 조회
     */
    public List < HashMap < String, Object >> selectPumpMaster() {
        return aiMapper.selectPumpMaster();
    }

    /**
     * 시간별 전력 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @param hour 조회할 시간 범위
     * @return 시간별 전력 데이터 리스트
     */
    public List < HashMap < String, Object >> selectHourPwrList(HashMap < String, Object > map, int hour) {

        // 날짜 및 시간 포맷 지정
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:00:00");

        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        // 한국 시간대를 사용하여 현재 시간을 ZonedDateTime으로 가져옴
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);

        // ZonedDateTime에서 LocalDateTime으로 변환 (시간대 정보는 손실됨)
        LocalDateTime koreaLocalDateTime = koreaZonedDateTime.toLocalDateTime();

        String end_date = formatter.format(koreaLocalDateTime);

        // 6시간 전 시간 계산
        LocalDateTime startTime = koreaLocalDateTime.minusHours(6);

        String start_date = formatter.format(startTime);

        //System.out.println(start_date + "#" + end_date);

        map.put("start_date", start_date);
        map.put("end_date", end_date);

        /*List<HashMap<String, Object>> temp = new ArrayList<>();

        HashMap<String, Object> itme = new HashMap<>();


        itme.put("01-09 14:00" , 3332);
        		temp.add(itme);

        itme.put("01-09 15:00" , 3333);
        		temp.add(itme);
        itme.put("01-09 16:00" , 3334);
        		temp.add(itme);
        itme.put("01-09 17:00" , 3335);
        		temp.add(itme);
        itme.put("01-09 18:00" , 3336);
        temp.add(itme);
        		itme.put("01-09 19:00" , 3337);
        		temp.add(itme);

        		return  temp;*/

        return aiMapper.selectHourPwrList(map);
    }

    /**
     * 시간별 평균 전력 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 시간별 평균 전력 데이터 리스트
     */
    List < HashMap < String, Object >> selectHourAvgPwrList(HashMap < String, Object > map) {
        return aiMapper.selectHourAvgPwrList(map);
    }

    /**
     * 시간별 펌프 전력 예측 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 시간별 펌프 전력 예측 리스트
     */
    List < HashMap < String, Object >> selectHourPwrPrdctList(HashMap < String, Object > map) {
        return aiMapper.selectHourPwrPrdctList(map);
    }

    /**
     * 펌프 사용량 리스트를 조회하는 메서드
     * @return 펌프 사용량 리스트
     */
    public List < HashMap < String, Object >> pumpUsageList() {
        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:00");

        // Format the ZonedDateTime using the formatter
        String asiaSeoulNowDate = koreaZonedDateTime.format(formatter);
        return aiMapper.pumpUsageList(asiaSeoulNowDate);
    }

    /**
     * 펌프 사용 여부 리스트를 조회하는 메서드
     * @return 펌프 사용 여부 리스트
     */
    public List < HashMap < String, Object >> pumpUsageYnList() {
        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:00");

        // Format the ZonedDateTime using the formatter
        String asiaSeoulNowDate = koreaZonedDateTime.format(formatter);
        return aiMapper.pumpUsageYnList(asiaSeoulNowDate);
    }

    /**
     * 예측 펌프 전력 항목을 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @param hour 조회할 시간 범위
     * @return 예측 펌프 전력 항목 리스트
     */
    List < HashMap < String, Object >> selectPrdctPumpPwrItem(HashMap < String, Object > map, int hour) {

        List < HashMap < String, Object >> returnMapList = new ArrayList < > ();

        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        // 한국 시간대를 사용하여 현재 시간을 ZonedDateTime으로 가져옴
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);

        // ZonedDateTime에서 LocalDateTime으로 변환 (시간대 정보는 손실됨)
        LocalDateTime koreaLocalDateTime = koreaZonedDateTime.toLocalDateTime();

        //LocalDateTime now = LocalDateTime.now();
        // 6시간 전 시간 계산
        LocalDateTime startTime = koreaLocalDateTime.minusHours(hour);

        // 날짜 및 시간 포맷 지정
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("MM-dd HH:00");

        // 24시간 동안의 시간 출력
        for (int i = 0; i < 24; i++) {
            LocalDateTime timePoint = startTime.plusHours(i);
            map.put("DATE_TIME", timePoint.format(formatter));
            //System.out.println("DATE_TIME:"+timePoint.format(formatter));
            HashMap < String, Object > pwrItem = aiMapper.selectPrdctPumpPwrItem(map);
            if (pwrItem != null) {
                returnMapList.add(pwrItem);
            }
        }

        return returnMapList;
    }

    /**
     * 예측 펌프 상태 목록을 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 예측 펌프 상태 목록
     */
    public List < HashMap < String, Object >> pumpPrdctSelectList(HashMap < String, Object > map) {
        List < HashMap < String, Object >> resultList = new ArrayList < > ();
        List < HashMap < String, Object >> resultTempList = new ArrayList < > ();
        if (false) {
            resultList = aiMapper.pumpPrdctSunEssSelectList(map);
            //        }else if(wpp_code.equals("gs") || wpp_code.equals("ba") || wpp_code.equals("gr"))
        }
        //        else if(wpp_code.matches("hy|ji"))
        //        {
        //            //resultList = aiMapper.pumpPrdctEssSelectList(map);
        //            resultList = aiMapper.pumpPrdctLSTMSelectList(map);
        //            //pumpPrdctSelectList
        //        }
        //        else if(wpp_code.equals("gs"))
        //        {
        //            resultList = aiMapper.pumpPrdctSunSelectList(map);
        //        }
        //        else if(wpp_code.equals("wm"))
        //        {
        //            resultList = aiMapper.pumpPrdctEssSelectList(map);
        //        }
        //        else if(wpp_code.equals("hp"))
        //        {
        //            resultList = aiMapper.pumpPrdctSelectList(map);
        //        }
        else {
            LocalDateTime currentTime = LocalDateTime.now();

            // 원하는 형식의 날짜 및 시간 문자열로 변환
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
            String formattedDateTime = currentTime.format(formatter);
            System.out.println("pumpPrdctSelectList - 현재 로컬 시간: " + formattedDateTime);
            resultTempList = aiMapper.pumpPrdctAvgNowSelectList();
            int nowCalHour = currentTime.getHour();
            int nowCalMinute = currentTime.getMinute();
            //System.out.println("현재 시간: " + nowCalHour);
            //System.out.println("현재 분: " + nowCalMinute);
            //System.out.println("HOUR CHECK: "+nowHour+"/"+nowCalHour);
            if ((nowHour != nowCalHour)) {
                setRandomList(resultTempList);
                //System.out.println("HOUR CHECK randomList: "+randomList.toString());
                nowHour = nowCalHour;
                pass = false;
            }
            int rCount = 0;
            //System.out.println("PowerPrdctList: "+randomList.toString());
            for (HashMap < String, Object > item: resultTempList) {
                double nowPwrValue = Double.parseDouble(item.get("PWR").toString());
                //System.out.println("nowPwrValue: "+nowPwrValue);
                if (nowPwrValue != 0 && rCount < 7) {
                    if (!randomList.isEmpty()) {
                        ///System.out.println("PowerPrdctList["+rCount+"]:"+randomList.toString());
                        double nowPrdctValue = nowPwrValue + randomList.get(rCount);
                        BigDecimal bd = new BigDecimal(nowPrdctValue);
                        bd = bd.setScale(2, RoundingMode.HALF_UP); // 소수점 두 자리로 반올림
                        double formattedValue = bd.doubleValue(); // 다시 double 값으로 변환
                        item.put("PRDCT_PWR", formattedValue);
                        //System.out.println("item:"+item.toString());
                        rCount++;
                    } else {
                        setRandomList(resultTempList);
                        //System.out.println("HOUR CHECK PowerPrdctList: "+randomList.toString());
                        nowHour = nowCalHour;
                        pass = false;
                        double nowPrdctValue = nowPwrValue + randomList.get(rCount);
                        BigDecimal bd = new BigDecimal(nowPrdctValue);
                        bd = bd.setScale(2, RoundingMode.HALF_UP); // 소수점 두 자리로 반올림
                        double formattedValue = bd.doubleValue(); // 다시 double 값으로 변환
                        item.put("PRDCT_PWR", formattedValue);
                        //System.out.println("item:"+item.toString());
                        rCount++;
                    }
                }
                //System.out.println("NOW item:"+item.toString());
                resultList.add(item);
            }
            //System.out.println("resultTempList:"+resultTempList.toString());

            //PEAK_YN 설정 및 PEAK 값 삭제 처리
            for (int i = 0; i < resultList.size(); i++) {
                double peak = Double.parseDouble(resultList.get(i).get("PEAK").toString());
                double nowValue = Double.parseDouble(resultList.get(i).get("PRDCT_PWR").toString());
                if (nowValue >= peak) {
                    resultList.get(i).put("PEAK_YN", "Y");
                } else {
                    resultList.get(i).put("PEAK_YN", "N");
                }
                resultList.get(i).remove("PEAK");
            }

        }
        //System.out.println("resultList:"+resultList.toString());
        for (int i = 0; i < resultList.size(); i++) {
            //System.out.println("resultList.get(i):"+resultList.get(i).toString());
            double nowPwr = Double.parseDouble(resultList.get(i).get("PWR").toString());
            if (nowPwr == 0) {
                resultList.get(i).remove("PWR");
            }
        }
        return resultList;
    }

    /**
     * 무작위 리스트를 설정하는 메서드
     * @param list 설정할 리스트
     */
    public void setRandomList(List < HashMap < String, Object >> list) {
        randomList.clear();
        if (list.size() > 6) {
            for (int i = 0; i < 7; i++) {
                HashMap < String, Object > stringObjectHashMap = list.get(i);
                double nowValue = 0.0;
                if (Double.parseDouble(stringObjectHashMap.get("PWR").toString()) != 0) {
                    nowValue = Double.parseDouble(stringObjectHashMap.get("PWR").toString()); // 주어진 값
                } else {
                    nowValue = 3000;
                }
                double percentage = 5.0; // A의 5%를 계산하기 위한 퍼센테이지 값
                // A의 5% 계산
                double fivePercentValue = nowValue * (percentage / 100);
                // -fivePercentValue부터 fivePercentValue까지의 랜덤값 생성
                double min = -fivePercentValue;
                double max = fivePercentValue;
                // min과 max 사이의 랜덤값 생성 후 A에 더하기
                double randomValueWithinRange = min + (Math.random() * (max - min));
                //System.out.println("Random Adjustment within +/- 5% of A: " + randomValueWithinRange);
                randomList.add(randomValueWithinRange);
            }
        }
        /*for (HashMap<String, Object> stringObjectHashMap : list) {
            if(Double.parseDouble(stringObjectHashMap.get("PWR").toString()) != 0) {
                double nowValue = Double.parseDouble(stringObjectHashMap.get("PWR").toString()); // 주어진 값
                double percentage = 5.0; // A의 5%를 계산하기 위한 퍼센테이지 값
                //System.out.println("#####now Value#####");
                //System.out.println(nowValue);
                //System.out.println("#####now Value#####");

                // A의 5% 계산
                double fivePercentValue = nowValue * (percentage / 100);
                // -fivePercentValue부터 fivePercentValue까지의 랜덤값 생성
                double min = -fivePercentValue;
                double max = fivePercentValue;
                // min과 max 사이의 랜덤값 생성 후 A에 더하기
                double randomValueWithinRange = min + (Math.random() * (max - min));
                //System.out.println("Random Adjustment within +/- 5% of A: " + randomValueWithinRange);
                randomList.add(randomValueWithinRange);
            }
        }*/
    }

    /**
     * 전력 예측 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @param hour 조회할 시간 범위
     * @return 전력 예측 리스트
     */
    public List < HashMap < String, Object >> selectPwrPrdctList(HashMap < String, Object > map, int hour) {
        //List<HashMap<String, Object>> tempPrdctList = aiService.peakSelect(map);

        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        // 한국 시간대를 사용하여 현재 시간을 ZonedDateTime으로 가져옴
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);

        // ZonedDateTime에서 LocalDateTime으로 변환 (시간대 정보는 손실됨)
        LocalDateTime now = koreaZonedDateTime.toLocalDateTime();

        //LocalDateTime now = LocalDateTime.now();
        // 날짜 및 시간 포맷 지정
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("MM-dd");
        DateTimeFormatter dateHourFormatter = DateTimeFormatter.ofPattern("MM-dd HH:00");
        DateTimeFormatter onlyHourFormatter = DateTimeFormatter.ofPattern("HH:00");
        String nowDate = now.format(formatter);
        List < HashMap < String, Object >> tempPrdctPumpList = new ArrayList < > ();
        if (wpp_code.equals("hy") || wpp_code.equals("ji") || wpp_code.equals("ss") || wpp_code.equals("dev") || wpp_code.equals("ba")) {
            HashMap < String, Object > usageItem = new HashMap < > ();
            usageItem.put("PUMP_GRP", 1);
            usageItem.put("PUMP_GRP_DSC", "none");
            tempPrdctPumpList.add(usageItem);
        } else {
            tempPrdctPumpList = pumpUsageList();
        }
        //System.out.println("tempPrdctPumpList:" + tempPrdctPumpList.toString());
        HashMap < String, Object > pumpPrdctPwrSumMap = new HashMap < > ();

        for (HashMap < String, Object > pumpItem: tempPrdctPumpList) {
            HashMap < String, Object > param = new HashMap < > ();
            //System.out.println("PUMP_GRP:" + pumpItem.get("PUMP_GRP"));
            param.put("pump_grp", pumpItem.get("PUMP_GRP"));
            //System.out.println("param:" + param.toString());
            List < HashMap < String, Object >> tempPumpList = selectPrdctPumpPwrItem(param, hour);
            //System.out.println("tempPumpList:" + tempPumpList.toString());

            for (HashMap < String, Object > pumpPrdctItem: tempPumpList) {
                //System.out.println("pumpPrdctItem:"+pumpPrdctItem.toString());
                double nowPrdctPumpPwr = Double.parseDouble(pumpPrdctItem.get("PWR_PRDCT").toString());
                //System.out.println("nowPrdctPumpPwr:"+nowPrdctPumpPwr);
                //System.out.println("pumpPrdctItem.get(\"PRDCT_TIME\").toString():"+pumpPrdctItem.get("PRDCT_TIME").toString());
                if (pumpPrdctPwrSumMap.containsKey(pumpPrdctItem.get("PRDCT_TIME").toString())) {
                    double all = Double.parseDouble(pumpPrdctPwrSumMap.get(pumpPrdctItem.get("PRDCT_TIME").toString()).toString());
                    pumpPrdctPwrSumMap.put(pumpPrdctItem.get("PRDCT_TIME").toString(), all + nowPrdctPumpPwr);
                } else {
                    pumpPrdctPwrSumMap.put(pumpPrdctItem.get("PRDCT_TIME").toString(), nowPrdctPumpPwr);
                }
                //System.out.println("pumpPrdctPwrSumMap:"+pumpPrdctPwrSumMap.toString());
            }
        }
        //System.out.println("pumpPrdctPwrSumMap:" + pumpPrdctPwrSumMap.toString());

        List < HashMap < String, Object >> tempPwrPrdctCalHourList = new ArrayList < > ();
        //System.out.println("wpp_code:"+wpp_code);
        if (wpp_code.equals("hy") || wpp_code.equals("ji") || wpp_code.equals("ss") || wpp_code.equals("dev")) {
            tempPwrPrdctCalHourList.add(pumpPrdctPwrSumMap);
        } else {
            //selectHourPwrList
            List < HashMap < String, Object >> tempPwrAvgHourList = selectHourAvgPwrList(map);
            HashMap < String, Object > tempPwrAvgHourMap = new HashMap < > ();

            for (HashMap < String, Object > pwrAvgItem: tempPwrAvgHourList) {
                tempPwrAvgHourMap.put(pwrAvgItem.get("DATE").toString(), Double.parseDouble(pwrAvgItem.get("PWR").toString()));
            }

            //System.out.println("tempPwrAvgHourMap:" + tempPwrAvgHourMap.toString());
            LocalDateTime startTime = now.minusHours(6);
            for (int i = 0; i < 24; i++) {
                HashMap < String, Object > tempItem = new HashMap < > ();
                LocalDateTime timePoint = startTime.plusHours(i);
                String checkDateTime = timePoint.format(dateHourFormatter);
                String checkTime = timePoint.format(onlyHourFormatter);
                //System.out.println("checkDate:"+checkDateTime+"#"+pumpPrdctPwrSumMap.containsKey(checkDateTime));
                //System.out.println("checkDateTime:"+checkTime+"#"+tempPwrAvgHourMap.containsKey(checkTime));
                if (pumpPrdctPwrSumMap.containsKey(checkDateTime) && tempPwrAvgHourMap.containsKey(checkTime)) {
                    //System.out.println("pumpPrdctPwrSumMap["+checkDateTime+"]:"+pumpPrdctPwrSumMap.get(checkDateTime));
                    //System.out.println("tempPwrAvgHourMap["+checkTime+"]:"+tempPwrAvgHourMap.get(checkTime));
                    double tempSum = 0.0;
                    if (wpp_code.equals("gu")) {
                        //15일평균의 10% 추가
                        tempSum = (Double.parseDouble(tempPwrAvgHourMap.get(checkTime).toString())) * 0.1;
                    } else {
                        //화성방식 계산
                        tempSum = (Double.parseDouble(tempPwrAvgHourMap.get(checkTime).toString()) - Double.parseDouble(pumpPrdctPwrSumMap.get(checkDateTime).toString())) * 0.75;
                    }

                    tempItem.put(checkDateTime, tempSum + Double.parseDouble(pumpPrdctPwrSumMap.get(checkDateTime).toString()));
                    tempPwrPrdctCalHourList.add(tempItem);
                } else if (tempPwrAvgHourMap.containsKey(checkTime)) {
                    //System.out.println("#######################################");
                    tempItem.put(checkDateTime, tempPwrAvgHourMap.get(checkTime).toString());
                    tempPwrPrdctCalHourList.add(tempItem);
                    //System.out.println("#######################################");
                } else {
                    //System.out.println("#######################################");
                    tempItem.put(checkDateTime, 0);
                    tempPwrPrdctCalHourList.add(tempItem);
                    //System.out.println("#######################################");
                }
            }
        }

        //System.out.println("tempPwrPrdctCalHourList:" + tempPwrPrdctCalHourList.toString());

        List < HashMap < String, Object >> tempPwrHourList = selectHourPwrList(map, hour);

        List < HashMap < String, Object >> tempResultList = new ArrayList < > ();

        //System.out.println("tempPwrAvgHourList:"+tempPwrAvgHourList.toString());
        //System.out.println("tempPwrHourList:" + tempPwrHourList.toString());

        List < HashMap < String, Object >> nowGoalList = settingService.selectPeakGoal();

        int nowIntGoal = 0;

        for (HashMap < String, Object > nowGoalItem: nowGoalList) {
            nowIntGoal = Integer.parseInt(nowGoalItem.get("value").toString());
        }

        if (nowIntGoal == 0) {
            nowIntGoal = 4000;
        }

        for (HashMap < String, Object > calItem: tempPwrPrdctCalHourList) {
            for (String key: calItem.keySet()) {
                HashMap < String, Object > tempItme = new HashMap < > ();
                //System.out.println("key:"+key);
                tempItme.put("DATE", key);
                double prdctDoubleValue = Double.parseDouble(calItem.get(key).toString());
                int prdctIntValue = (int) Math.round(prdctDoubleValue);
                tempItme.put("PRDCT_PWR", prdctIntValue);
                tempItme.put("PEAK_YN", "1");
                for (HashMap < String, Object > pwrItem: tempPwrHourList) {
                    if (pwrItem.get("DATE").toString().equals(key)) {
                        double pwrDoubleValue = Double.parseDouble(pwrItem.get("PWR").toString());
                        int pwrIntValue = (int) Math.round(pwrDoubleValue);
                        tempItme.put("PWR", pwrIntValue);
                    }
                }
                if (nowIntGoal < prdctIntValue) {
                    tempItme.put("PEAK_YN", "1");
                } else {
                    tempItme.put("PEAK_YN", "0");
                }
                tempResultList.add(tempItme);
            }
        }

        SimpleDateFormat sdf = new SimpleDateFormat("MM-dd HH:mm");
        // Comparator를 사용하여 리스트 정렬
        Collections.sort(tempResultList, new Comparator < HashMap < String, Object >> () {
            public int compare(HashMap < String, Object > map1, HashMap < String, Object > map2) {
                try {
                    Date date1 = sdf.parse(map1.get("DATE").toString());
                    Date date2 = sdf.parse(map2.get("DATE").toString());
                    return date1.compareTo(date2);
                } catch (ParseException e) {
                    e.printStackTrace();
                    return 0;
                }
            }
        });

        return tempResultList;
    }

    /**
     * WPP 태그 리스트를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return WPP 태그 리스트
     */
    public List < HashMap < String, Object >> wppTagList(HashMap < String, Object > map) {
        return aiMapper.wppTagList(map);
    }

    /**
     * 피크 시간의 전력 예측 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 피크 시간 전력 예측 리스트
     */
    public List < HashMap < String, Object >> peakTimePrdctPwr(HashMap < String, Object > map) {
        //map.put("func_type","peakTimePrdctPwr");

        String funcType = map.get("func_type").toString();

        List < HashMap < String, Object >> resultList = new ArrayList < > ();
        List < HashMap < String, Object >> emsTagList = wppTagList(map);
        List < HashMap < String, Object >> pwrPrdctList = selectPwrPrdctList(map, 0);

        //System.out.println("emsTagList:" + emsTagList);
        //System.out.println("pwrPrdctList:" + pwrPrdctList);

        for (HashMap < String, Object > prdctItem: pwrPrdctList) {
            //System.out.println("prdctItem.get(date).toString():" + prdctItem.get("DATE").toString());
            int timeSort = Integer.parseInt(prdctItem.get("DATE").toString().split(" ")[1].split(":")[0].toString());
            for (int i = 0; i < emsTagList.size(); i++) {
                HashMap < String, Object > resultItem = new HashMap < > ();
                if (emsTagList.get(i) != null) {
                    HashMap < String, Object > item = emsTagList.get(i);
                    int nowSort = Integer.parseInt(item.get("SORT").toString()) - 1;
                    if (nowSort == timeSort) {
                        resultItem.put("tag", item.get("TAG").toString());
                        resultItem.put("time", prdctItem.get("DATE").toString());
                        if (funcType.equals("peakTimePrdctPwr")) {
                            if (prdctItem.containsKey("PRDCT_PWR")) {
                                resultItem.put("value", Double.parseDouble(prdctItem.get("PRDCT_PWR").toString()));
                            } else {
                                resultItem.put("value", 1000);
                            }
                        } else if (funcType.equals("peakYn")) {
                            if (prdctItem.containsKey("PEAK_YN")) {
                                resultItem.put("value", Integer.parseInt(prdctItem.get("PEAK_YN").toString()));
                            } else {
                                resultItem.put("value", 0);
                            }
                        }
                        resultList.add(resultItem);
                    }
                    //System.out.println("item:"+item.toString());
                }
                //item.put
            }
        }
        return resultList;
    }

    /**
     * 구미 대응 수정된 피크 시간 전력 예측 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 피크 시간 전력 예측 리스트
     */
    public List < HashMap < String, Object >> peakTimePrdctPwrGM(HashMap < String, Object > map) {
        //map.put("func_type","peakTimePrdctPwr");

        String funcType = map.get("func_type").toString();

        List < HashMap < String, Object >> resultList = new ArrayList < > ();
        List < HashMap < String, Object >> emsTagList = wppTagList(map);

        //원본
        //List<HashMap<String, Object>> pwrPrdctList = selectPwrPrdctList(map, 0);

        //구미 대응 수정
        List < HashMap < String, Object >> pwrPrdctList = pumpPrdctSelectList(map);

        //System.out.println("emsTagList:" + emsTagList);
        //System.out.println("pwrPrdctList:" + pwrPrdctList);

        for (HashMap < String, Object > prdctItem: pwrPrdctList) {
            //System.out.println("prdctItem.get(date).toString():" + prdctItem.get("DATE").toString());
            int timeSort = Integer.parseInt(prdctItem.get("DATE").toString().split(" ")[1].split(":")[0].toString());
            for (int i = 0; i < emsTagList.size(); i++) {
                HashMap < String, Object > resultItem = new HashMap < > ();
                if (emsTagList.get(i) != null) {
                    HashMap < String, Object > item = emsTagList.get(i);
                    int nowSort = Integer.parseInt(item.get("SORT").toString()) - 1;
                    if (nowSort == timeSort) {
                        resultItem.put("tag", item.get("TAG").toString());
                        resultItem.put("time", prdctItem.get("DATE").toString());
                        if (funcType.equals("peakTimePrdctPwr")) {
                            if (prdctItem.containsKey("PRDCT_PWR")) {
                                resultItem.put("value", Double.parseDouble(prdctItem.get("PRDCT_PWR").toString()));
                            } else {
                                resultItem.put("value", 1000);
                            }
                        } else if (funcType.equals("peakYn")) {
                            if (prdctItem.containsKey("PEAK_YN")) {
                                resultItem.put("value", Integer.parseInt(prdctItem.get("PEAK_YN").toString()));
                            } else {
                                resultItem.put("value", 0);
                            }
                        }
                        resultList.add(resultItem);
                    }
                    //System.out.println("item:"+item.toString());
                }
                //item.put
            }
        }
        return resultList;
    }

    /**
     * 피크 시간의 전력 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 피크 시간 전력 리스트
     */
    public List < HashMap < String, Object >> peakTimePwr(HashMap < String, Object > map) {
        map.put("func_type", "peakTimePwr");

        String funcType = map.get("func_type").toString();

        List < HashMap < String, Object >> resultList = new ArrayList < > ();

        List < HashMap < String, Object >> emsTagList = wppTagList(map);

        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        // 한국 시간대를 사용하여 현재 시간을 ZonedDateTime으로 가져옴
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);
        // ZonedDateTime에서 LocalDateTime으로 변환 (시간대 정보는 손실됨)
        LocalDateTime koreaLocalDateTime = koreaZonedDateTime.toLocalDateTime();
        // 날짜 및 시간 포맷 지정
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        //plusDays
        String StartDate = koreaLocalDateTime.format(formatter);

        int nowHour = koreaLocalDateTime.getHour(); // 시간 추출

        LocalDateTime tomorrow = koreaLocalDateTime.plusDays(1);
        String endDate = tomorrow.format(formatter);
        //System.out.println("StartDate:" + StartDate);
        //System.out.println("endDate:" + endDate);
        map.put("start_date", StartDate);
        map.put("end_date", endDate);
        List < HashMap < String, Object >> pwrList = aiMapper.selectHourPwrList(map);

        if (pwrList.size() < 24) {
            ZoneId koreaZoneIdTemp = ZoneId.of("Asia/Seoul");
            // 한국 시간대를 사용하여 현재 시간을 ZonedDateTime으로 가져옴
            ZonedDateTime koreaZonedDateTimeTemp = ZonedDateTime.now(koreaZoneIdTemp);
            // ZonedDateTime에서 LocalDateTime으로 변환 (시간대 정보는 손실됨)
            LocalDateTime koreaLocalDateTimeTemp = koreaZonedDateTimeTemp.toLocalDateTime();
            // 날짜 및 시간 포맷 지정
            DateTimeFormatter formatterTemp = DateTimeFormatter.ofPattern("MM-dd");
            for (int i = (nowHour + 1); i < 24; i++) {
                String nowHourStr = "";
                if (i < 10) {
                    nowHourStr = "0" + i;
                } else {
                    nowHourStr = String.valueOf(i);
                }
                HashMap < String, Object > noneDataMap = new HashMap < > ();
                noneDataMap.put("DATE", koreaLocalDateTimeTemp.format(formatterTemp) + " " + nowHourStr + ":00");
                noneDataMap.put("TIME", nowHourStr);
                noneDataMap.put("PWR", 0);
                pwrList.add(noneDataMap);
            }
        }

        //System.out.println("pwrList:"+pwrList.toString());

        for (HashMap < String, Object > pwrItem: pwrList) {
            int timeSort = Integer.parseInt(pwrItem.get("DATE").toString().split(" ")[1].split(":")[0].toString());
            for (int i = 0; i < emsTagList.size(); i++) {
                HashMap < String, Object > item = emsTagList.get(i);
                int nowSort = Integer.parseInt(item.get("SORT").toString()) - 1;
                if (nowSort == timeSort) {
                    HashMap < String, Object > resultItem = new HashMap < > ();
                    resultItem.put("tag", item.get("TAG").toString());
                    resultItem.put("time", pwrItem.get("DATE").toString());
                    resultItem.put("value", Double.parseDouble(pwrItem.get("PWR").toString()));
                    resultList.add(resultItem);
                }
            }
        }
        return resultList;
    }

    /**
     * 예측 분석 시간을 조회하는 메서드
     * @return 예측 분석 시간 리스트
     */
    public List < HashMap < String, Object >> selectPrdctAnlyTime() {
        List < HashMap < String, Object >> resultList = new ArrayList < > ();
        HashMap < String, Object > anlyItem = aiMapper.selectPrdctAnlyTime();
        HashMap < String, Object > anlyYnItem = aiMapper.selectPrdctYnAnlyTime();
        //차후 사용
        HashMap < String, Object > map = new HashMap < > ();
        if (anlyItem != null) {
            HashMap < String, Object > resultItem = new HashMap < > ();
            map.put("func_type", "peakUpdateTime");
            List < HashMap < String, Object >> peakUpdateTimeList = wppTagList(map);
            if (!peakUpdateTimeList.isEmpty()) {
                resultItem.put("tag", peakUpdateTimeList.get(0).get("TAG"));
                resultItem.put("value", anlyItem.get("ANLY_TIME"));
                resultItem.put("time", anlyItem.get("ANLY_TIME"));

                resultList.add(resultItem);
            }

            map.put("func_type", "pumpUpdateTime");
            List < HashMap < String, Object >> pumpUpdateTimeList = wppTagList(map);

            for (HashMap < String, Object > pumpUpdateTimeItem: pumpUpdateTimeList) {
                HashMap < String, Object > resultItem2 = new HashMap < > ();
                resultItem2.put("tag", pumpUpdateTimeItem.get("TAG"));
                resultItem2.put("value", anlyItem.get("ANLY_TIME"));
                resultItem2.put("time", anlyItem.get("ANLY_TIME"));

                resultList.add(resultItem2);
            }

            map.put("func_type", "pumpYnUpdateTime");
            List < HashMap < String, Object >> pumpYnUpdateTimeList = wppTagList(map);

            for (HashMap < String, Object > pumpUpdateTimeItem: pumpYnUpdateTimeList) {
                HashMap < String, Object > resultItem3 = new HashMap < > ();
                resultItem3.put("tag", pumpUpdateTimeItem.get("TAG"));
                resultItem3.put("value", anlyYnItem.get("ANLY_TIME"));
                resultItem3.put("time", anlyYnItem.get("ANLY_TIME"));

                resultList.add(resultItem3);
            }
            /*

            resultItem2.put("tag", pumpUpdateTimeList.get(0).get("TAG")); //for 추가
            resultItem2.put("value", anlyItem.get("ANLY_TIME"));
            resultItem2.put("time", anlyItem.get("ANLY_TIME"));
            resultList.add(resultItem2);*/
        }
        return resultList;
    }

    /**
     * 요금제 비용과 전력 데이터를 조회하는 메서드
     * @return 요금제 비용과 전력 데이터 리스트
     */
    public List < HashMap < String, Object >> selectCostPwr() {
        List < HashMap < String, Object >> resultList = new ArrayList < > ();
        HashMap < String, Object > resultItem = new HashMap < > ();
        HashMap < String, Object > costPwrList = aiMapper.selectCostPwr();

        if (costPwrList != null) {
            HashMap < String, Object > map = new HashMap < > ();
            map.put("func_type", "peakCostPwr");
            List < HashMap < String, Object >> peakCostList = wppTagList(map);
            if (!peakCostList.isEmpty()) {
                resultItem.put("tag", peakCostList.get(0).get("TAG"));
                resultItem.put("value", costPwrList.get("COST_PWR"));
                resultItem.put("time", costPwrList.get("ANLY_DATE"));
                resultList.add(resultItem);
            }
        }
        return resultList;
    }

    /**
     * 펌프 예측데이터와 SCADA 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 예측데이터와 SCADA 데이터 리스트
     */
    public List < HashMap < String, Object >> selectPumpPrdctScadaList(HashMap < String, Object > map) {

        List < HashMap < String, Object >> resultList = new ArrayList < > ();

        List < HashMap < String, Object >> emsTagList = wppTagList(map);
        //System.out.println("selectPumpPrdctScadaList map:" + map.toString());
        List < HashMap < String, Object >> pwrList = aiMapper.selectPumpPrdctScadaList(map);
        //System.out.println("pwrList:" + pwrList.toString());

        for (HashMap < String, Object > pwrItem: pwrList) {
            int timeSort = Integer.parseInt(pwrItem.get("PRDCT_TIME").toString().split(" ")[1].split(":")[0].toString());
            for (int i = 0; i < emsTagList.size(); i++) {
                HashMap < String, Object > item = emsTagList.get(i);
                int nowSort = Integer.parseInt(item.get("SORT").toString()) - 1;
                if (nowSort == timeSort) {
                    HashMap < String, Object > resultItem = new HashMap < > ();
                    resultItem.put("tag", item.get("TAG").toString());
                    resultItem.put("time", pwrItem.get("PRDCT_TIME").toString());
                    resultItem.put("value", Double.parseDouble(pwrItem.get("VALUE").toString()));
                    resultList.add(resultItem);
                }
            }
        }
        return resultList;
    }

    /**
     * 펌프 예측 데이터와 SCADA 데이터 단일 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 예측 데이터와 SCADA 단일 데이터
     */
    public List < HashMap < String, Object >> selectPumpPrdctScadaOne(HashMap < String, Object > map) {

        List < HashMap < String, Object >> resultList = new ArrayList < > ();

        List < HashMap < String, Object >> emsTagList = wppTagList(map);
        //System.out.println("selectPumpPrdctScadaOne map:" + map.toString());
        HashMap < String, Object > scadaItem = aiMapper.selectPumpPrdctScadaOne(map);
        //System.out.println("scadaItem:" + scadaItem.toString());

        if (!emsTagList.isEmpty()) {
            HashMap < String, Object > item = emsTagList.get(0);
            HashMap < String, Object > resultItem = new HashMap < > ();
            resultItem.put("tag", item.get("TAG").toString());
            resultItem.put("time", scadaItem.get("PRDCT_TIME").toString());
            resultItem.put("value", Double.parseDouble(scadaItem.get("VALUE").toString()));
            resultList.add(resultItem);
        }
        return resultList;
    }
    /**
     * 전력 절감을 하는 메서드
     * @return 전력 절감 데이터 리스트
     */
    public List < HashMap < String, Object >> selectSavingResult() {
        List < HashMap < String, Object >> resultList = new ArrayList < > ();

        HashMap < String, Object > savingMap = aiMapper.selectSavingResult();
        HashMap < String, Object > map = new HashMap < > ();

        if (savingMap != null) {
            //System.out.println("savingMap:"+savingMap.toString());

            HashMap < String, Object > costResultMap = new HashMap < > ();
            HashMap < String, Object > pwrResultMap = new HashMap < > ();
            HashMap < String, Object > co2ResultMap = new HashMap < > ();

            map.put("func_type", "saveCost");
            List < HashMap < String, Object >> costTagList = wppTagList(map);
            costResultMap.put("tag", costTagList.get(0).get("TAG").toString());
            costResultMap.put("time", savingMap.get("DATE"));
            double costValue = Double.parseDouble(savingMap.get("SAVINGCOST").toString());
            if (0 < costValue) {
                costValue = Math.abs(costValue);
            } else {
                costValue = costValue * -1;
            }
            costResultMap.put("value", costValue);
            resultList.add(costResultMap);

            map.put("func_type", "savePwr");
            List < HashMap < String, Object >> pwrTagList = wppTagList(map);
            pwrResultMap.put("tag", pwrTagList.get(0).get("TAG").toString());
            pwrResultMap.put("time", savingMap.get("DATE"));
            double pwrValue = Double.parseDouble(savingMap.get("SAVINGKWH").toString());
            if (0 < pwrValue) {
                pwrValue = Math.abs(pwrValue);
            } else {
                pwrValue = pwrValue * -1;
            }
            pwrResultMap.put("value", pwrValue);
            resultList.add(pwrResultMap);

            map.put("func_type", "saveCo2");
            List < HashMap < String, Object >> co2TagList = wppTagList(map);
            co2ResultMap.put("tag", co2TagList.get(0).get("TAG").toString());
            co2ResultMap.put("time", savingMap.get("DATE"));
            double co2Value = Double.parseDouble(savingMap.get("SAVINGCO2").toString());
            if (0 < co2Value) {
                co2Value = Math.abs(co2Value);
            } else {
                co2Value = co2Value * -1;
            }
            co2ResultMap.put("value", co2Value);
            resultList.add(co2ResultMap);
        }
        //System.out.println("selectSavingResult:"+resultList.toString());
        return resultList;
    }
    /**
     * 펌프 그룹에 대한 분석 최적화 결과를 조회하는 메서드
     * @param pumpGrp 조회할 펌프 그룹
     * @return 분석 최적화 결과 리스트
     */
    public List < HashMap < String, Object >> selectPumpAnlyOptResult(int pumpGrp) {
        List < HashMap < String, Object >> resultList = new ArrayList < > ();

        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        // 한국 시간대를 사용하여 현재 시간을 ZonedDateTime으로 가져옴
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);
        // ZonedDateTime에서 LocalDateTime으로 변환 (시간대 정보는 손실됨)
        LocalDateTime koreaLocalDateTime = koreaZonedDateTime.toLocalDateTime();
        // 날짜 및 시간 포맷 지정
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        String dateTime = koreaLocalDateTime.format(formatter);

        HashMap < String, Object > map = new HashMap < > ();
        map.put("func_type", "pumpAnlyOptMode" + pumpGrp);
        List < HashMap < String, Object >> pumpAnlyOptModeTagList = wppTagList(map);
        if (!pumpAnlyOptModeTagList.isEmpty()) {
            HashMap < String, Object > pumpAnlyOptModeResultMap = new HashMap < > ();
            pumpAnlyOptModeResultMap.put("tag", pumpAnlyOptModeTagList.get(0).get("TAG").toString());
            pumpAnlyOptModeResultMap.put("time", dateTime);
            pumpAnlyOptModeResultMap.put("value", pumpAnlyOptModeTagList.get(0).get("DEFAULT_VALUE").toString());
            resultList.add(pumpAnlyOptModeResultMap);
        }

        map.put("func_type", "pumpAnlyOptCtr" + pumpGrp);
        List < HashMap < String, Object >> pumpAnlyOptCtrTagList = wppTagList(map);

        if (!pumpAnlyOptCtrTagList.isEmpty()) {
            HashMap < String, Object > pumpAnlyOptCtrResultMap = new HashMap < > ();
            pumpAnlyOptCtrResultMap.put("tag", pumpAnlyOptCtrTagList.get(0).get("TAG").toString());
            pumpAnlyOptCtrResultMap.put("time", dateTime);
            pumpAnlyOptCtrResultMap.put("value", pumpAnlyOptCtrTagList.get(0).get("DEFAULT_VALUE").toString());
            resultList.add(pumpAnlyOptCtrResultMap);
        }

        //pumpAnlyOptMode1
        //pumpAnlyOptCtr1
        //pumpAnlyOptMode2
        //pumpAnlyOptCtr2

        //System.out.println("resultList:"+resultList.toString());

        return resultList;
    }
    /**
     * AI 상태를 조회하는 메서드
     * @return AI 상태 리스트
     */
    public List < HashMap < String, Object >> selectAiStatus() {
        List < HashMap < String, Object >> statusList = aiMapper.selectAiStatus();
        List < HashMap < String, Object >> resultList = new ArrayList < > ();
        //System.out.println("statusList:"+statusList.toString());
        for (HashMap < String, Object > map: statusList) {
            //System.out.println("map:"+map.toString());
            String pumpGrp = map.get("PUMP_GRP").toString();
            //System.out.println("pumpGrp:"+pumpGrp);
            if (wpp_code.equals("ba") && pumpGrp.equals("4")) {
                //System.out.println("ck1");
                HashMap < String, Object > grp5 = new HashMap < > ();
                grp5.put("AI_STATUS", map.get("AI_STATUS"));
                grp5.put("PUMP_GRP", "5");
                grp5.put("emergencyStatus", aiMapper.selectPumpEmergencyStatus("4"));
                //System.out.println("grp5:"+grp5.toString());
                map.put("emergencyStatus", aiMapper.selectPumpEmergencyStatus("4"));
                resultList.add(map);
                resultList.add(grp5);
                //System.out.println("ck2");
                //System.out.println("statusList2:"+statusList.toString());
            } else {
                //System.out.println("ck3");
                map.put("emergencyStatus", aiMapper.selectPumpEmergencyStatus(pumpGrp));
                resultList.add(map);
            }
        }
        //System.out.println("statusList3:"+resultList.toString());
        return resultList;
    }
    /**
     * AI 상태를 업데이트하는 비동기 메서드
     * @param map 업데이트할 정보가 담긴 맵
     * @return CompletableFuture 객체로 비동기 실행 결과 반환
     */
    @Async
    public CompletableFuture < Integer > updateAiStatusTemp(HashMap < String, Object > map) {
        return CompletableFuture.supplyAsync(() -> {

            int runType = Integer.parseInt(map.get("STATUS").toString());
            HashMap < String,
                    Object > logItem = new HashMap < > ();
            //AI분석모드가 아닐때
            if (runType == 0) {
                /*int status = pumpService.runAiPumpGrp(map);
               System.out.println("CompletableFuture updateAiStatus - "+status);
               if (status == 0) {
                    aiMapper.updateAiStatus(map);
                 }
               else {
                    //emsAlarmInsert
                    String nowPumpGrp = map.get("PUMP_GRP").toString();
                    String url = AlarmService.LOCALHOST +"/EMSPumpControl";
                    HashMap<String, String> alarm = new HashMap<>();
                    alarm.put("nowDate",pumpService.nowStringDate());
                    alarm.put("msg","펌프 그룹 ["+nowPumpGrp+"] AI 운전 실패 "+status);
                    alarm.put("link",url);
                    System.out.println("alarm: "+alarm.toString());
                    alarmService.emsAlarmInsert(alarm);
                    map.put("STATUS","2");
                    aiMapper.updateAiStatus(map);
              }
              return status;
              */
                return 0;
            }
            //AI 추천모드 개발 필요
            else if (runType == 1) {
                /*map.put("FLAG", "2"); //추천중인 펌프 스케쥴
                map.put("UPDATE_FLAG", "3"); // 추천했던 펌프 스케쥴
                pumpService.updatePumpYnFlagGrpInit(map);*/

                //pumpService.updatePumpYnFlag(map);
                //STATUS == 3

                pumpService.initCtrTag();
                logItem.put("tag", "AiMode");
                logItem.put("value", "AI Recommend Start");
                logItem.put("time", pumpService.nowStringDate());
                logItem.put("anly_cd", "INIT");
                logItem.put("flag", 2);
                pumpService.insertHmiTagLog(logItem);
                if (wpp_code.equals("gs")) {
                    map.put("PUMP_GRP", 1);
                    aiMapper.updateAiStatus(map);
                    map.put("PUMP_GRP", 2);
                    aiMapper.updateAiStatus(map);
                } else {
                    aiMapper.updateAiStatus(map);
                }
                return 0;
            } else {
                //AI분석모드로 돌아갈때 마지막 펌프가동 여부 체크를 초기화
                //map.put("FLAG", "1"); //가동중인 펌프 스케쥴
                //map.put("UPDATE_FLAG", "2"); //가동했던 펌프 스케쥴
                //pumpService.updatePumpYnFlagGrpInit(map);
                pumpService.initCtrTag();
                logItem.put("tag", "AiMode");
                logItem.put("value", "AI Mode End");
                logItem.put("time", pumpService.nowStringDate());
                logItem.put("anly_cd", "INIT");
                logItem.put("flag", 2);
                pumpService.insertHmiTagLog(logItem);
                if (wpp_code.equals("gs")) {
                    map.put("PUMP_GRP", 1);
                    aiMapper.updateAiStatus(map);
                    map.put("PUMP_GRP", 2);
                    aiMapper.updateAiStatus(map);
                } else {
                    aiMapper.updateAiStatus(map);
                }
                return 0;
            }
        });
    }

    /**
     * AI 상태를 업데이트하는 메서드
     * @param map 업데이트할 정보가 담긴 맵
     */
    public void updateAiStatus(HashMap < String, Object > map) {
        int runType = Integer.parseInt(map.get("STATUS").toString());
        String STATUS = map.get("STATUS").toString();
        String pumpGrp = map.get("PUMP_GRP").toString();
        map.put("STATUS", STATUS);
        HashMap < String, Object > logItem = new HashMap < > ();
        //AI분석모드가 아닐때
        if (runType == 0) {
            pumpService.initCtrTag();
            logItem.put("TAG", "AiMode");
            logItem.put("VALUE", "AI Control Start");
            logItem.put("TIME", pumpService.nowStringDate());
            logItem.put("ANLY_CD", "INIT");
            logItem.put("FLAG", 2);
            pumpService.insertHmiTagLog(logItem);
            if (wpp_code.equals("gs")) {
                map.put("PUMP_GRP", "1");
                aiMapper.updateAiStatus(map);
                map.put("PUMP_GRP", "2");
                aiMapper.updateAiStatus(map);
            } else if (wpp_code.equals("ba")) {
                if (pumpGrp.equals("4") || pumpGrp.equals("5")) {
                    map.put("PUMP_GRP", "4");
                    aiMapper.updateAiStatus(map);
                } else {
                    aiMapper.updateAiStatus(map);
                }
            } else {
                aiMapper.updateAiStatus(map);
            }
        }
        //AI 추천모드 개발 필요
        else if (runType == 1) {
            /*map.put("FLAG", "2"); //추천중인 펌프 스케쥴
            map.put("UPDATE_FLAG", "3"); // 추천했던 펌프 스케쥴
            pumpService.updatePumpYnFlagGrpInit(map);*/

            //pumpService.updatePumpYnFlag(map);
            //STATUS == 3

            pumpService.initCtrTag();
            logItem.put("TAG", "AiMode");
            logItem.put("VALUE", "AI Recommend Start");
            logItem.put("TIME", pumpService.nowStringDate());
            logItem.put("ANLY_CD", "INIT");
            logItem.put("FLAG", 2);
            pumpService.insertHmiTagLog(logItem);
            if (wpp_code.equals("gs")) {
                map.put("PUMP_GRP", "1");
                aiMapper.updateAiStatus(map);
                map.put("PUMP_GRP", "2");
                aiMapper.updateAiStatus(map);
            } else if (wpp_code.equals("ba")) {
                if (pumpGrp.equals("4") || pumpGrp.equals("5")) {
                    map.put("PUMP_GRP", "4");
                    aiMapper.updateAiStatus(map);
                } else {
                    aiMapper.updateAiStatus(map);
                }
            } else {
                aiMapper.updateAiStatus(map);
            }
        } else {
            //AI분석모드로 돌아갈때 마지막 펌프가동 여부 체크를 초기화
            //map.put("FLAG", "1"); //가동중인 펌프 스케쥴
            //map.put("UPDATE_FLAG", "2"); //가동했던 펌프 스케쥴
            //pumpService.updatePumpYnFlagGrpInit(map);
            pumpService.initCtrTag();
            logItem.put("TAG", "AiMode");
            logItem.put("VALUE", "AI Mode End");
            logItem.put("TIME", pumpService.nowStringDate());
            logItem.put("ANLY_CD", "INIT");
            logItem.put("FLAG", 2);
            pumpService.insertHmiTagLog(logItem);
            if (wpp_code.equals("gs")) {
                map.put("PUMP_GRP", "1");
                System.out.println("updateAiStatus 2-1:" + map.toString());
                aiMapper.updateAiStatus(map);
                map.put("PUMP_GRP", "2");
                System.out.println("updateAiStatus 2-2:" + map.toString());
                aiMapper.updateAiStatus(map);
            } else if (wpp_code.equals("ba")) {
                if (pumpGrp.equals("4") || pumpGrp.equals("5")) {
                    map.put("PUMP_GRP", "4");
                    aiMapper.updateAiStatus(map);
                } else {
                    aiMapper.updateAiStatus(map);
                }
            } else {
                System.out.println("updateAiStatus 2-3:" + map.toString());
                aiMapper.updateAiStatus(map);
            }
        }
    }

    /**
     * AI 펌프 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return AI 펌프 데이터 리스트
     */
    public List < HashMap < String, Object >> selectAIPumpData(HashMap < String, Object > map) {
        return aiMapper.selectAIPumpData(map);
    }
    /**
     * 서울 시간 기준 현재 시간을 반환하는 메서드
     * @return 서울 시간 'yyyy-mm-dd HH24:mi:ss' 형식의 문자열
     */
    public String getAsiaSeoulTime() {
        ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
        // 한국 시간대를 사용하여 현재 시간을 ZonedDateTime으로 가져옴
        ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);
        // ZonedDateTime에서 LocalDateTime으로 변환 (시간대 정보는 손실됨)
        LocalDateTime koreaLocalDateTime = koreaZonedDateTime.toLocalDateTime();
        // 날짜 및 시간 포맷 지정
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

        return koreaLocalDateTime.format(formatter);
    }
    /**
     * AI 펌프 EMS 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return AI 펌프 EMS 데이터 리스트
     */
    public List < HashMap < String, Object >> aiPumpEMSData(HashMap < String, Object > map) {
        List < HashMap < String, Object >> AIData = aiMapper.selectAIPumpData(map);
        List < HashMap < String, Object >> returnList = new ArrayList < > ();

        int pump_grp = (int) map.get("PUMP_GRP");

        if (!AIData.isEmpty()) {
            String func_type = "";

            HashMap < String, Object > AIDataMap = AIData.get(0);
            HashMap < String, Object > returnMap = new HashMap < > ();
            //예상관압
            returnMap.put("time", getAsiaSeoulTime());
            func_type = "pumpAnlyPri" + pump_grp;
            returnMap.put("tag", getEMSTag(func_type, null));
            returnMap.put("value", AIDataMap.get("TUBE_PRSR_PRDCT"));
            returnList.add(returnMap);

            //예상유량
            returnMap = new HashMap < > ();
            returnMap.put("time", getAsiaSeoulTime());
            func_type = "pumpAnlyFir" + pump_grp;
            returnMap.put("value", AIDataMap.get("PRDCT_MEAN"));
            returnMap.put("tag", getEMSTag(func_type, null));
            returnList.add(returnMap);

            //예상전력
            returnMap = new HashMap < > ();
            returnMap.put("time", getAsiaSeoulTime());
            func_type = "pumpAnlyPwr" + pump_grp;
            returnMap.put("value", AIDataMap.get("PWR_PRDCT"));
            returnMap.put("tag", getEMSTag(func_type, null));
            returnList.add(returnMap);
        }

        return returnList;
    }
    /**
     * AI 펌프 EMS 사용 여부 데이터를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return AI 펌프 EMS 사용 여부 데이터 리스트
     */
    public List < HashMap < String, Object >> aiPumpEMSYnData(HashMap < String, Object > map) {
        List < HashMap < String, Object >> AIYnData = aiMapper.selectAIPumpYnData(map);

        List < HashMap < String, Object >> returnList = new ArrayList < > ();

        int pump_grp = (int) map.get("PUMP_GRP");

        //System.out.println("AIYnData["+pump_grp+"]:"+AIYnData.toString());

        for (HashMap < String, Object > AIYnDataMap: AIYnData) {
            HashMap < String, Object > returnYnMap = new HashMap < > ();
            String func_type = "";
            //펌프별 AI 운영여부
            returnYnMap.put("time", getAsiaSeoulTime());
            func_type = "pumpAnlyOptOnOff" + pump_grp;
            returnYnMap.put("tag", getEMSTag(func_type, String.valueOf(AIYnDataMap.get("PUMP_IDX"))));
            Integer pump_yn = Integer.parseInt((String) AIYnDataMap.get("PUMP_YN"));
            returnYnMap.put("value", pump_yn);
            returnList.add(returnYnMap);

            //펌프타입 인버터일 경우 해당 EMS태그 탐색 / AI 주파수
            if (AIYnDataMap.containsKey("PUMP_TYP")) {
                int pump_type = (int) AIYnDataMap.get("PUMP_TYP");
                if (pump_type == 2) {
                    HashMap < String, Object > returnYnFreqMap = new HashMap < > ();
                    returnYnFreqMap.put("time", getAsiaSeoulTime());
                    func_type = "pumpAnlyOptSpi" + pump_grp;
                    returnYnFreqMap.put("tag", getEMSTag(func_type, String.valueOf(AIYnDataMap.get("PUMP_IDX"))));
                    returnYnFreqMap.put("value", AIYnDataMap.get("FREQ"));
                    returnList.add(returnYnFreqMap);
                }
            }

        }
        return returnList;
    }
    /**
     * EMS 태그를 반환하는 메서드
     * @param func_type 함수 타입
     * @param indexOption 함수 타입으로 구분 가능할 경우 null 전달
     * @return EMS 태그
     */
    public String getEMSTag(String func_type, String indexOption) {
        List < HashMap < String, Object >> EMSTagList = commonService.selectWppEMSTag();
        String returnTag = null;
        for (HashMap < String, Object > entry: EMSTagList) {
            if (indexOption != null) {
                if (func_type.equals(entry.get("FUNC_TYP"))) {
                    String tag_kor = (String) entry.get("TAG_KOR_NM");
                    if (tag_kor.contains(indexOption)) {
                        returnTag = (String) entry.get("TAG");
                        break;
                    }
                }
            } else {
                if (func_type.equals(entry.get("FUNC_TYP"))) {
                    returnTag = (String) entry.get("TAG");
                    break;
                }
            }
        }
        //        System.out.println("탐색할 FUNC_TYPE: "+func_type);
        //        System.out.println("탐색할 indexOption: "+indexOption);
        //
        //        System.out.println("탐색된 EMS태그: "+returnTag);
        return returnTag;
    }
    /**
     * 비상 사용 상태를 조회하는 메서드
     * @return 비상 사용 상태 리스트
     */
    public List < HashMap < String, Object >> getEmergencyUse() {
        List < HashMap < String, Object >> returnList = new ArrayList < > ();
        HashMap < String, Object > returnMap = new HashMap < > ();
        returnMap.put("time", getAsiaSeoulTime());
        //현재 전체 펌프 그룹 및 그룹명 호출
        List < HashMap < String, Object >> pumpMaster = selectPumpMaster();
        for (HashMap < String, Object > map: pumpMaster) {
            int pump_grp = (int) map.get("PUMP_GRP");

            //비상정지에 해당하는 전체 WPP 데이터 호출
            List < HashMap < String, Object >> emergencyWppCode = commonService.selectWppTagCodeList("pumpAnlyOptStopOn" + pump_grp);
            //그룹 별 1대1매칭이니 index 0 인것을 호출
            if (emergencyWppCode.size() == 1) {
                returnMap.put("tag", emergencyWppCode.get(0).get("TAG"));
                Integer value = Integer.parseInt((String) emergencyWppCode.get(0).get("DEFAULT_VALUE"));
                returnMap.put("value", value);
                returnList.add(returnMap);
            }
        }

        return returnList;
    }
    /**
     * 최소 배수지 압력을 조회하는 메서드
     * @return 최소 배수지 압력 리스트
     */
    public List < HashMap < String, Object >> getTnkMinPri() {
        List < HashMap < String, Object >> returnList = new ArrayList < > ();
        HashMap < String, Object > returnMap = new HashMap < > ();
        List < HashMap < String, Object >> hashMaps = commonService.selectWppTagCodeLikeList("tnkMinPri");
        for (HashMap < String, Object > map: hashMaps) {
            returnMap = new HashMap < > ();
            returnMap.put("time", getAsiaSeoulTime());
            returnMap.put("tag", map.get("TAG"));
            Object defaultValueObject = map.get("DEFAULT_VALUE");

            if (defaultValueObject != null) {
                try {
                    double doubleValue = Double.parseDouble(defaultValueObject.toString());
                    returnMap.put("value", doubleValue);
                } catch (NumberFormatException e) {
                    // 변환에 실패한 경우, 로깅 또는 다른 처리를 수행할 수 있습니다.
                    e.printStackTrace();
                    returnMap.put("value", 0); // 또는 다른 기본값으로 설정할 수 있습니다.
                }
            }
            returnList.add(returnMap);
        }

        return returnList;
    }
    /**
     * 펌프 AI 사용 여부를 조회하는 메서드
     * @return 펌프 AI 사용 여부 리스트
     */
    public List < HashMap < String, Object >> getPumpAiUsage() {
        List < HashMap < String, Object >> returnList = new ArrayList < > ();
        List < HashMap < String, Object >> pumpMaster = selectAiStatus();
        for (HashMap < String, Object > map: pumpMaster) {
            HashMap < String, Object > returnMap = new HashMap < > ();
            returnMap.put("time", getAsiaSeoulTime());
            int pump_grp = Integer.parseInt((String) map.get("PUMP_GRP"));
            //AI운영모드에 해당하는 전체 WPP 데이터 호출
            List < HashMap < String, Object >> emergencyWppCode = commonService.selectWppTagCodeList("pumpAiOnOff" + pump_grp);
            //그룹 별 1대1매칭이니 index 0 인것을 호출
            if (emergencyWppCode.size() == 1) {
                returnMap.put("tag", emergencyWppCode.get(0).get("TAG"));
                int status = Integer.parseInt((String) map.get("AI_STATUS"));
                int value = 1;
                if (status == 2) {
                    value = 0;
                }
                returnMap.put("value", value);
                returnList.add(returnMap);
            }
        }

        return returnList;
    }
    /**
     * 펌프 가동 상태를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 가동 상태 리스트
     */
    public List < HashMap < String, Object >> selectPumpPrdctOnOffStatus(HashMap < String, Object > map) {

        //selectPumpPrdctInquiryOnOffStatus

        /*List<HashMap<String, Object>> preList = aiMapper.selectPumpPrdctInquiryOnOffStatus(map);
        if(preList.isEmpty())
        {
            preList = aiMapper.selectPumpPrdctOnOffStatus(map);
        }*/
        List < HashMap < String, Object >> preList = aiMapper.selectPumpPrdctOnOffStatus(map);
        //System.out.println("selectPumpPrdctOnOffStatus map:"+map.toString());
        //System.out.println("preList:"+preList.toString());
        //System.out.println("preList size:"+preList.size());
        //List<HashMap<String, Object>> curList = aiMapper.setLastCurPumpUse(map);
        List < HashMap < String, Object >> curList = aiMapper.setLastCurPumpUseFreq(map);
        List < HashMap < String, Object >> priList = aiMapper.setLastCurPumpUsePri(map);

        //System.out.println("curList:"+curList.toString());
        //System.out.println("curList size:"+curList.size());

        // 예측(preList)과 실측(curList/priList)을 같은 i 번째끼리 짝지으면 안 된다.
        // 두 쿼리의 대상 집합과 정렬이 서로 다르기 때문이다.
        //   preList     : TB_CTR_PUMPYN_RST 기준. 마스터의 USE_YN 을 보지 않으며
        //                 ORDER BY PRDCT_TIME DESC, PUMP_IDX ASC 다. 일부 펌프만 최근 5분 내
        //                 TB_CTR_PUMPYN_INQUIRY 행을 가지면 PRDCT_TIME 이 갈려 PUMP_IDX 순서가 깨진다.
        //   cur/priList : 마스터의 USE_YN=1 기준이고 ORDER BY 가 아예 없다.
        // 길이가 어긋나면 IndexOutOfBounds, 순서가 어긋나면 남의 펌프 실측값이 조용히 붙는다.
        // 그래서 위치가 아니라 PUMP_IDX 로 짝을 찾는다.
        Map < String, HashMap < String, Object >> curByPumpIdx = indexByPumpIdx(curList);
        Map < String, HashMap < String, Object >> priByPumpIdx = indexByPumpIdx(priList);

        for (HashMap < String, Object > preItem: preList) {
            String pumpIdx = asPumpKey(preItem.get("PUMP_IDX"));
            HashMap < String, Object > curMap = curByPumpIdx.get(pumpIdx);
            HashMap < String, Object > priMap = priByPumpIdx.get(pumpIdx);
            //System.out.println("curMap:"+curMap);

            // 계측이 10분 넘게 끊기면 LEFT JOIN 이 NULL 을 돌려준다. 예전에는 그 값을
            // 그대로 parseDouble 에 넣어 NPE 가 났고, 전역 폴링이라 화면 전체가 500 이 됐다.
            // 이제는 '미상'으로 두고 기본값을 내려보낸다.
            Double pumpUse = curMap == null ? null : parseMeasuredValue(curMap.get("PMB_VALUE"));
            Double pumpUseFreq = curMap == null ? null : parseMeasuredValue(curMap.get("SPI_VALUE"));
            Double pumpUsePri = priMap == null ? null : parseMeasuredValue(priMap.get("PRI"));

            preItem.put("nowUse", (pumpUse != null && pumpUse > 0) ? "On" : "Off");
            preItem.put("nowFreq", pumpUseFreq == null ? 0.0 : pumpUseFreq);
            preItem.put("nowPri", pumpUsePri == null ? 0.0 : pumpUsePri);
            // 위 세 값이 진짜 계측인지 기본값인지 프런트가 구분할 수 있게 표시한다.
            preItem.put("nowDataValid", pumpUse != null && pumpUseFreq != null && pumpUsePri != null);
        }
        return preList;
    }
    /**
     * 펌프 실측 조회 결과를 PUMP_IDX 로 색인한다.
     *
     * 같은 PUMP_IDX 가 여러 행으로 올 수 있어(setLastCurPumpUseFreq 의 GROUP BY 에
     * TAGNAME 이 들어 있다) 첫 행을 쓴다.
     * @param list 색인할 조회 결과
     * @return PUMP_IDX 문자열을 키로 하는 맵
     */
    private Map < String, HashMap < String, Object >> indexByPumpIdx(List < HashMap < String, Object >> list) {
        Map < String, HashMap < String, Object >> index = new HashMap < > ();
        for (HashMap < String, Object > item: list) {
            String key = asPumpKey(item.get("PUMP_IDX"));
            if (key != null) {
                index.putIfAbsent(key, item);
            }
        }
        return index;
    }
    /**
     * PUMP_IDX 를 비교용 문자열로 바꾼다.
     *
     * 같은 컬럼이라도 COALESCE 를 거치면 Integer 가 아니라 Long 으로 오는 경우가 있어
     * 객체 비교 대신 문자열로 맞춘다.
     * @param value PUMP_IDX 값
     * @return 비교용 문자열, 값이 없으면 null
     */
    private String asPumpKey(Object value) {
        return value == null ? null : String.valueOf(value);
    }
    /**
     * 계측값을 double 로 읽는다.
     *
     * NULL·빈 문자열·숫자가 아닌 값은 예외 대신 '미상'(null)으로 돌려준다.
     * TB_RAWDATA 조인이 10분 창을 벗어나면 NULL 이 오는 것이 정상 경로이기 때문이다.
     * @param value 계측 컬럼 값
     * @return 읽어낸 값, 미상이면 null
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
     * 관압을 조회하는 메서드
     * @return 최소 관압 리스트
     */
    public List < HashMap < String, Object >> getWaterMinPri() {
        List < HashMap < String, Object >> returnList = new ArrayList < > ();
        HashMap < String, Object > returnMap = new HashMap < > ();
        List < HashMap < String, Object >> wppInPri = commonService.selectWppTagCodeLikeList("wppInPri");
        List < HashMap < String, Object >> wppOutPri = commonService.selectWppTagCodeLikeList("wppOutPri");
        for (HashMap < String, Object > map: wppInPri) {
            returnMap = new HashMap < > ();
            returnMap.put("time", getAsiaSeoulTime());
            returnMap.put("tag", map.get("TAG"));
            Object defaultValueObject = map.get("DEFAULT_VALUE");

            if (defaultValueObject != null) {
                try {
                    double doubleValue = Double.parseDouble(defaultValueObject.toString());
                    returnMap.put("value", doubleValue);
                } catch (NumberFormatException e) {
                    // 변환에 실패한 경우, 로깅 또는 다른 처리를 수행할 수 있습니다.
                    e.printStackTrace();
                    returnMap.put("value", 0); // 또는 다른 기본값으로 설정할 수 있습니다.
                }
            }
            returnList.add(returnMap);
        }
        for (HashMap < String, Object > map: wppOutPri) {
            returnMap = new HashMap < > ();
            returnMap.put("time", getAsiaSeoulTime());
            returnMap.put("tag", map.get("TAG"));
            Object defaultValueObject = map.get("DEFAULT_VALUE");

            if (defaultValueObject != null) {
                try {
                    double doubleValue = Double.parseDouble(defaultValueObject.toString());
                    returnMap.put("value", doubleValue);
                } catch (NumberFormatException e) {
                    // 변환에 실패한 경우, 로깅 또는 다른 처리를 수행할 수 있습니다.
                    e.printStackTrace();
                    returnMap.put("value", 0); // 또는 다른 기본값으로 설정할 수 있습니다.
                }
            }
            returnList.add(returnMap);
        }
        return returnList;
    }
    /**
     * 펌프 명령을 실행하는 메서드
     * @param map 실행에 필요한 파라미터
     */
    public void pumpCommand(HashMap < String, Object > map) {
        List < String > pumpGrpValue = Arrays.asList(map.get("pump_grp").toString().split(","));
        List < String > pumpGrpList;
        boolean checkAiModeStr = false;
        if (!pumpGrpValue.isEmpty()) {
            pumpGrpList = pumpGrpValue;
            List < String > nowPumpGrpList = pumpService.selectAiPumpGrpListStr(PumpService.AI_RECOMMEND);
            //System.out.println("nowPumpGrpList:"+nowPumpGrpList);
            checkAiModeStr = new HashSet < > (nowPumpGrpList).containsAll(pumpGrpList);
        } else {
            pumpGrpList = pumpService.selectAiPumpGrpListStr(PumpService.AI_RECOMMEND);
            checkAiModeStr = true;
        }

        System.out.println("checkAiModeStr:" + checkAiModeStr);

        if (!pumpGrpList.isEmpty() && checkAiModeStr) {
            if (wpp_code.equals("gr") || wpp_code.equals("gu") || wpp_code.equals("ba") || wpp_code.equals("dev")) {
                pumpService.pumpCommand(pumpGrpList);
            } else if (wpp_code.equals("wm")) {
                pumpService.pumpCommandWM(pumpGrpList);
            } else if (wpp_code.equals("gs")) {
                pumpService.pumpCommandGS(pumpGrpList);
            }
        }
    }

    public void pumpCommandAI(HashMap < String, Object > map) {
        List < String > pumpGrpValue = Arrays.asList(map.get("pump_grp").toString().split(","));
        List < String > pumpGrpList;
        boolean checkAiModeStr = false;
        if (!pumpGrpValue.isEmpty()) {
            pumpGrpList = pumpGrpValue;
            List < String > nowPumpGrpList = pumpService.selectAiPumpGrpListStr(PumpService.AI_CONTROL);
            //System.out.println("nowPumpGrpList:"+nowPumpGrpList);
            checkAiModeStr = new HashSet < > (nowPumpGrpList).containsAll(pumpGrpList);
        } else {
            pumpGrpList = pumpService.selectAiPumpGrpListStr(PumpService.AI_CONTROL);
            checkAiModeStr = true;
        }

        System.out.println("pumpCommandAI checkAiModeStr:" + checkAiModeStr);

        if (!pumpGrpList.isEmpty() && checkAiModeStr) {
            if (wpp_code.equals("gr") || wpp_code.equals("gu") || wpp_code.equals("ba") || wpp_code.equals("dev")) {
                pumpService.pumpCommand(pumpGrpList);
            } else if (wpp_code.equals("wm")) {
                pumpService.pumpCommandWM(pumpGrpList);
            } else if (wpp_code.equals("gs")) {
                pumpService.pumpCommandGS(pumpGrpList);
            }
        }
    }
    /**
     * 펌프 명령 상태를 조회하는 메서드
     * @return 펌프 명령 상태를 담은 해시맵
     */
    public HashMap < String, Object > pumpCommandStatus() {

        List < String > pumpGrpList = pumpService.selectAiPumpGrpListStr(PumpService.AI_RECOMMEND);

        if (!pumpGrpList.isEmpty()) {
            if (wpp_code.equals("gs") || wpp_code.equals("gr") || wpp_code.equals("gu") || wpp_code.equals("ba") || wpp_code.equals("dev")) {
                return pumpService.pumpCommandStatus(pumpService.selectAiPumpGrpListStr(PumpService.AI_RECOMMEND));
            } else {
                return pumpService.pumpCommandStatus(pumpService.selectAiPumpGrpListStr(PumpService.AI_RECOMMEND));
            }
        } else {
            return null;
        }
    }
    /**
     * 펌프 AI 제어 상태를 조회하는 메서드
     * @return 펌프 AI 제어 상태를 담은 해시맵
     */
    public HashMap < String, Object > pumpCommandAiControlStatus() {

        List < String > pumpGrpList = pumpService.selectAiPumpGrpListStr(PumpService.AI_CONTROL);

        if (!pumpGrpList.isEmpty()) {
            return pumpService.pumpCommandStatus(pumpGrpList);
            /*if(wpp_code.equals("gs") || wpp_code.equals("gu") || wpp_code.equals("ba") || wpp_code.equals("dev"))
            {
                return pumpService.pumpCommandStatus(pumpService.selectAiPumpGrpListStr(PumpService.AI_CONTROL));
            }
            else {
                return pumpService.pumpCommandStatus(pumpService.selectAiPumpGrpListStr(PumpService.AI_CONTROL));
            }*/
        } else {
            return null;
        }
    }
    /**
     * AI 추천 모드 상태를 확인하는 메서드
     * @return AI 추천 모드 상태 여부
     */
    public Boolean aiRecommendStatus() {
        //AI추천 모드일때 펌프 조합이 변경되었는지 체크함
        List < HashMap < String, Object >> statusList = selectAiStatus();
        boolean aiRecommend = false;

        for (HashMap < String, Object > statusItem: statusList) {
            String nowAiStatus = statusItem.get("AI_STATUS").toString();
            //부분 AI
            if (nowAiStatus.equals("1")) {
                aiRecommend = true;
            }
        }
        return aiRecommend;
    }
    /**
     * AI 제어 상태를 확인하는 메서드
     * @return AI 제어 상태 여부
     */
    public Boolean aiControlStatus() {
        //AI추천 모드일때 펌프 조합이 변경되었는지 체크함
        List < HashMap < String, Object >> statusList = selectAiStatus();
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
     * 펌프 제어 이력 리스트를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 펌프 제어 이력 리스트
     */
    public List<HashMap<String, Object>> selectPumpCtrHistoryList(HashMap<String, Object> map) {
        int nowOffset = Integer.parseInt(map.get("offset").toString());
        map.put("offset", nowOffset);
        List<HashMap<String, Object>> ctrList = aiMapper.selectPumpCtrHistoryList(map);
        List<HashMap<String, Object>> aiModeList = aiMapper.selectAiModeList(map);

        // aiModeList를 분까지만 + PUMP_GRP로 key 생성해서 Map으로 변환
        Map<String, HashMap<String, Object>> aiModeMap = new HashMap<>();
        for (HashMap<String, Object> aiMap : aiModeList) {
            Object aiTimeObj = aiMap.get("RGSTR_TIME");
            String aiTime = null;
            if (aiTimeObj != null) {
                aiTime = aiTimeObj.toString();
            }
            if (aiTime != null && aiMap.get("PUMP_GRP") != null) {
                String aiTimeMinute = aiTime.substring(0, 16) + ":00"; // 'YYYY-MM-DD HH:MM:00'
                String key = aiTimeMinute + "_" + aiMap.get("PUMP_GRP").toString();
                aiModeMap.put(key, aiMap);
            }
        }

        // ctrList에 AI_STATUS 추가
        for (HashMap<String, Object> ctrMap : ctrList) {
            String orderTime = ctrMap.get("ORDER_TIME") != null ? ctrMap.get("ORDER_TIME").toString() : null;
            Object pumpGrp = ctrMap.get("PUMP_GRP");
            String aiStatus = "AI정보없음";

            if (orderTime != null && pumpGrp != null) {
                String orderTimeMinute = orderTime.substring(0, 16) + ":00";
                String key = orderTimeMinute + "_" + pumpGrp.toString();

                HashMap<String, Object> matchAi = aiModeMap.get(key);
                if (matchAi != null && matchAi.containsKey("AI_MODE")) {
                    Object aiMode = matchAi.get("AI_MODE");
                    if ("0".equals(String.valueOf(aiMode))) {
                        aiStatus = "AI운전";
                    } else if ("1".equals(String.valueOf(aiMode))) {
                        aiStatus = "AI추천";
                    } else {
                        aiStatus = "AI분석";
                    }
                }
            }
            ctrMap.put("AI_STATUS", aiStatus);
        }

        // AI_STATUS가 추가된 ctrList 반환
        return ctrList;
    }

    /**
     * 펌프 제어 이력 전체 카운트를 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 전체 카운트를 담은 해시맵
     */
    public HashMap < String, Object > selectPumpCtrHistoryListAllCount(HashMap < String, Object > map) {
        HashMap < String, Object > result = new HashMap < > ();
        //int nowOffset = Integer.parseInt(map.get("offset").toString());
        //map.put("offset", nowOffset);
        int rawCount = aiMapper.selectPumpCtrHistoryCount(map);
        if (rawCount < 60) {
            result.put("allCount", 1);
        } else {
            int allCount = (int) Math.ceil((double) rawCount / 60);
            result.put("allCount", allCount);
        }
        return result;
    }

    /**
     * 펌프 상태를 변경하는 메서드
     * @param map 변경할 상태 정보
     * @return 상태 변경 결과를 담은 해시맵
     */
    public HashMap < String, Object > pumpChangeStatus(HashMap < String, Object > map) {
        List < String > pumpGrpList = pumpService.selectAiPumpGrpListStr(PumpService.AI_CONTROL);

        List < HashMap < String, Object >> list = pumpService.selectPumpPrdctOnOffList(map);

        if (list.isEmpty()) {
            map.put("result", "None");
        } else {
            map.put("result", pumpService.calculatePumpYnValueMatchRate(list));
        }

        return map;
    }
    /**
     * 고산에서 펌프 상태를 변경하는 메서드
     * @param map 변경할 상태 정보
     * @return 고산 상태 변경 결과를 담은 해시맵
     */
    public HashMap < String, Object > pumpChangeStatusAIModeGs(HashMap < String, Object > map) {
        System.out.println("pumpAiControlTask Start");
        HashMap < String, Object > pumpStatus = pumpService.pumpCommandStatus(pumpService.selectPumpGrpListStr());
        System.out.println("pumpChangeStatusAImode pumpStatus:" + pumpStatus.toString());

        String mode = map.get("mode").toString();
        pumpStatus.put("mode", mode);
        boolean rangeStatus = pumpService.pumpChangeRangeStatus(map);
        pumpStatus.put("rangeStatus", rangeStatus);
        if (Boolean.parseBoolean(pumpStatus.get("isChange").toString()) && !Boolean.parseBoolean(pumpStatus.get("isRunning").toString())) {
            List < HashMap < String, Object >> changePumpList = pumpService.changePumpList(true, pumpService.selectPumpGrpListStr());
            //changePumpList(false)
            if (!changePumpList.isEmpty() && rangeStatus) {
                pumpStatus.put("control", "RUN");
                System.out.println("pumpAiControlTask pumpCommand Start");
                if (mode.equals("real")) {
                    pumpService.pumpCommand(pumpService.selectPumpGrpListStr());
                }
            } else {
                pumpStatus.put("control", "No List and rangeStatus false");
            }
        } else {
            pumpStatus.put("control", "Not Change");
        }
        return pumpStatus;
    }
    /**
     * 펌프 예측 조합 정보를 조회하는 메서드
     * @return 펌프 예측 조합 리스트
     */
    public List < HashMap < String, Object >> selectDrvnPumpMaster() {
        return aiMapper.selectDrvnPumpMaster();
    }
    /**
     * 시간별 전력 사용량을 조회하는 메서드
     * @param map 조회에 필요한 파라미터
     * @return 시간별 전력 사용량을 담은 해시맵
     */
    public HashMap < String, Object > selectHourUsePwr(HashMap < String, Object > map) {
        return aiMapper.selectHourUsePwr(map);
    }

    public HashMap < String, Object > selectHourUsePwrPwi(HashMap < String, Object > map) {
        return aiMapper.selectHourUsePwrPwi(map);
    }

    /**
     * 예측 결과 데이터를 삽입하는 메서드
     * @param item 삽입할 데이터
     */
    public void insertPrdctResult(HashMap < String, Object > item) {
        aiMapper.insertPrdctResult(item);
    }
    /**
     * 펌프 예측 계산 리스트를 조회하는 메서드
     * @return 펌프 예측 계산 리스트
     */
    public List < HashMap < String, Object >> pumpPrdctCalSelectList() {
        List < HashMap < String, Object >> list = aiMapper.pumpPrdctCalSelectList();

        for (HashMap < String, Object > item: list) {
            double nowPeakValue = Double.parseDouble(item.get("PEAK").toString());
            double nowPrdctPwr = Double.parseDouble(item.get("PRDCT_PWR").toString());
            if (item.get("PWR").toString().equals("0.0")) {
                item.remove("PWR");
            }

            if (nowPrdctPwr >= nowPeakValue) {
                item.put("PEAK_YN", "Y");
            } else {
                item.put("PEAK_YN", "N");
            }

        }
        System.out.println("pumpPrdctCalSelectList:" + list.toString());
        return list;
    }

    public List < HashMap < String, Object >> pumpPrdctCalSelectListPwi() {
        List < HashMap < String, Object >> list = aiMapper.pumpPrdctCalSelectListPwi();

        for (HashMap < String, Object > item: list) {
            double nowPeakValue = Double.parseDouble(item.get("PEAK").toString());
            double nowPrdctPwr = Double.parseDouble(item.get("PRDCT_PWR").toString());
            if (item.get("PWR").toString().equals("0.0")) {
                item.remove("PWR");
            }

            if (nowPrdctPwr >= nowPeakValue) {
                item.put("PEAK_YN", "Y");
            } else {
                item.put("PEAK_YN", "N");
            }

        }
        System.out.println("pumpPrdctCalSelectList:" + list.toString());
        return list;
    }
    /**
     * 예측 전력 계산 작업을 비동기로 수행하는 메서드
     * @param date 계산할 날짜
     */
    @Async
    public void CalPrdctPwr(String date) {
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:00:00");
        SimpleDateFormat timeFormat = new SimpleDateFormat("HHmm");

        HashMap < String, Object > map = new HashMap < > ();
        map.put("date", date);
        System.out.println("CalPrdctPwr date:" + date);

        // 최대 10번 재시도 로직 추가
        HashMap < String, Object > nowPwr = null;
        int retryCount = 0;
        int maxRetry = 15;
        while (retryCount < maxRetry) {
            LocalTime nowTime = LocalTime.now();
            Date currentDate = new Date();
            // 출력할 형식을 지정합니다. 예: "yyyy-MM-dd HH:mm:ss"
            SimpleDateFormat dateFormat2 = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            String runDate = dateFormat2.format(currentDate);
            System.out.println("CalPrdctPwr tryDateTime:" + runDate);
            nowPwr = selectHourUsePwrPwi(map);
            //nowPwr = selectHourUsePwr(map);
            if (nowPwr != null && !nowPwr.isEmpty()) {
                break; // 값이 정상적으로 반환되면 루프 탈출
            }
            retryCount++;
            try {
                System.out.println("No data found, retrying... (" + retryCount + ")");
                Thread.sleep(30000); // 30초간 대기
            } catch (InterruptedException e) {
                System.out.println("Sleep interrupted: " + e.getMessage());
            }
        }

        // 재시도 횟수를 초과했을 때 로그 출력 및 기본 값 설정
        if (nowPwr == null || nowPwr.isEmpty()) {
            System.out.println("Failed to retrieve data after " + maxRetry + " attempts. Setting default value.");
        } else {
            // 값 추출
            double nowValue = 0.0;
            Object value = null;
            if (nowPwr != null && !nowPwr.isEmpty()) {
                value = nowPwr.values().iterator().next();
                nowValue = Double.parseDouble(value.toString());
            } else {
                nowValue = 3000; // 기본값 설정
            }

            try {
                Calendar prdctTimeCal = Calendar.getInstance();
                prdctTimeCal.setTime(dateFormat.parse(date));

                for (int time_diff = 0; time_diff < 24; time_diff++) { // time_diff를 0부터 시작
                    // 퍼센테이지에 따른 값을 계산
                    double percentage = 3.0 + (Math.random() * 2.0);
                    double valueRange = nowValue * (percentage / 100);
                    double min = -valueRange;
                    double max = valueRange;

                    // min과 max 사이의 랜덤값 생성 후 nowValue에 더하기
                    double randomValueWithinRange = min + (Math.random() * (max - min));
                    double finalValue = nowValue + randomValueWithinRange;

                    // 시간을 HHmm 형식으로 추출하여 OPT_IDX 생성
                    String timeStr = timeFormat.format(prdctTimeCal.getTime());
                    String optIdx = String.format(wpp_code + ":%s-%s", dateFormat.format(prdctTimeCal.getTime()).replace(":", "").replace("-", "").replace(" ", ""), timeStr);

                    // ANLY_TIME, RGSTR_TIME 설정
                    String anlyTimeStr = dateFormat.format(prdctTimeCal.getTime());

                    // HashMap에 데이터 설정
                    HashMap < String, Object > item = new HashMap < > ();
                    item.put("WPP_CODE", wpp_code);
                    item.put("OPT_IDX", optIdx);
                    item.put("ANLY_TIME", date);
                    item.put("PRDCT_TIME", anlyTimeStr);
                    item.put("PRDCT_TIME_DIFF", time_diff);
                    item.put("PUMP_GRP", 0);
                    item.put("PRDCT_MEAN", randomValueWithinRange); // 예측값 평균 설정 필요
                    item.put("PRDCT_STD", nowValue); // 예측값 표준편차 설정 필요
                    item.put("TUBE_PRSR_PRDCT", percentage); // 관압 예측값 설정 필요
                    item.put("PWR_PRDCT", finalValue);
                    item.put("DC_NMB", null);
                    item.put("FLAG", '2');

                    // 데이터베이스에 삽입
                    insertPrdctResult(item);

                    // prdctTimeCal에 1시간 추가
                    prdctTimeCal.add(Calendar.HOUR, 1);
                }
            } catch (Exception e) {
                System.out.println(e.toString());
                e.printStackTrace();
            }
        }
    }

    @Async
    public void CalPrdctPwrPwi(String date) {
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:00:00");
        SimpleDateFormat timeFormat = new SimpleDateFormat("HHmm");

        HashMap < String, Object > map = new HashMap < > ();
        map.put("date", date);
        System.out.println("CalPrdctPwr date:" + date);

        // 최대 10번 재시도 로직 추가
        HashMap < String, Object > nowPwr = null;
        int retryCount = 0;
        int maxRetry = 15;
        while (retryCount < maxRetry) {
            LocalTime nowTime = LocalTime.now();
            Date currentDate = new Date();
            // 출력할 형식을 지정합니다. 예: "yyyy-MM-dd HH:mm:ss"
            SimpleDateFormat dateFormat2 = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            String runDate = dateFormat2.format(currentDate);
            System.out.println("CalPrdctPwr tryDateTime:" + runDate);
            nowPwr = selectHourUsePwrPwi(map);
            if (nowPwr != null && !nowPwr.isEmpty()) {
                break; // 값이 정상적으로 반환되면 루프 탈출
            }
            retryCount++;
            try {
                System.out.println("No data found, retrying... (" + retryCount + ")");
                Thread.sleep(30000); // 30초간 대기
            } catch (InterruptedException e) {
                System.out.println("Sleep interrupted: " + e.getMessage());
            }
        }

        // 재시도 횟수를 초과했을 때 로그 출력 및 기본 값 설정
        if (nowPwr == null || nowPwr.isEmpty()) {
            System.out.println("Failed to retrieve data after " + maxRetry + " attempts. Setting default value.");
        } else {
            // 값 추출
            double nowValue = 0.0;
            Object value = null;
            if (nowPwr != null && !nowPwr.isEmpty()) {
                value = nowPwr.values().iterator().next();
                nowValue = Double.parseDouble(value.toString());
            } else {
                nowValue = 3000; // 기본값 설정
            }

            try {
                Calendar prdctTimeCal = Calendar.getInstance();
                prdctTimeCal.setTime(dateFormat.parse(date));

                for (int time_diff = 0; time_diff < 24; time_diff++) { // time_diff를 0부터 시작
                    // 퍼센테이지에 따른 값을 계산
                    double percentage = 3.0 + (Math.random() * 2.0);
                    double valueRange = nowValue * (percentage / 100);
                    double min = -valueRange;
                    double max = valueRange;

                    // min과 max 사이의 랜덤값 생성 후 nowValue에 더하기
                    double randomValueWithinRange = min + (Math.random() * (max - min));
                    double finalValue = nowValue + randomValueWithinRange;

                    // 시간을 HHmm 형식으로 추출하여 OPT_IDX 생성
                    String timeStr = timeFormat.format(prdctTimeCal.getTime());
                    String optIdx = String.format(wpp_code + ":%s-%s", dateFormat.format(prdctTimeCal.getTime()).replace(":", "").replace("-", "").replace(" ", ""), timeStr);

                    // ANLY_TIME, RGSTR_TIME 설정
                    String anlyTimeStr = dateFormat.format(prdctTimeCal.getTime());

                    // HashMap에 데이터 설정
                    HashMap < String, Object > item = new HashMap < > ();
                    item.put("WPP_CODE", wpp_code);
                    item.put("OPT_IDX", optIdx);
                    item.put("ANLY_TIME", date);
                    item.put("PRDCT_TIME", anlyTimeStr);
                    item.put("PRDCT_TIME_DIFF", time_diff);
                    item.put("PUMP_GRP", 0);
                    item.put("PRDCT_MEAN", randomValueWithinRange); // 예측값 평균 설정 필요
                    item.put("PRDCT_STD", nowValue); // 예측값 표준편차 설정 필요
                    item.put("TUBE_PRSR_PRDCT", percentage); // 관압 예측값 설정 필요
                    item.put("PWR_PRDCT", finalValue);
                    item.put("DC_NMB", null);
                    item.put("FLAG", '2');

                    // 데이터베이스에 삽입
                    insertPrdctResult(item);

                    // prdctTimeCal에 1시간 추가
                    prdctTimeCal.add(Calendar.HOUR, 1);
                }
            } catch (Exception e) {
                System.out.println(e.toString());
                e.printStackTrace();
            }
        }
    }

    public void CalPrdctPwrOld(String date) {
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:00:00");
        SimpleDateFormat timeFormat = new SimpleDateFormat("HHmm");

        HashMap < String, Object > map = new HashMap < > ();
        map.put("date", date);
        System.out.println("CalPrdctPwr date:" + date);
        HashMap < String, Object > nowPwr = selectHourUsePwr(map);

        if(nowPwr != null)
        {
            // 값 추출
            double nowValue = 0.0;
            Object value = null;
            if (!nowPwr.isEmpty()) {
                value = nowPwr.values().iterator().next();
                nowValue = Double.parseDouble(value.toString());
            } else {
                nowValue = 3000;
            }

            try {
                Calendar prdctTimeCal = Calendar.getInstance();
                prdctTimeCal.setTime(dateFormat.parse(date));

                for (int time_diff = 0; time_diff < 24; time_diff++) { // time_diff를 0부터 시작
                    // 퍼센테이지에 따른 값을 계산
                    double percentage = 3.0 + (Math.random() * 2.0);
                    double valueRange = nowValue * (percentage / 100);
                    double min = -valueRange;
                    double max = valueRange;

                    // min과 max 사이의 랜덤값 생성 후 nowValue에 더하기
                    double randomValueWithinRange = min + (Math.random() * (max - min));
                    double finalValue = nowValue + randomValueWithinRange;

                    // 시간을 HHmm 형식으로 추출하여 OPT_IDX 생성
                    String timeStr = timeFormat.format(prdctTimeCal.getTime());
                    String optIdx = String.format(wpp_code + ":%s-%s", dateFormat.format(prdctTimeCal.getTime()).replace(":", "").replace("-", "").replace(" ", ""), timeStr);

                    // ANLY_TIME, RGSTR_TIME 설정
                    String anlyTimeStr = dateFormat.format(prdctTimeCal.getTime());

                    // HashMap에 데이터 설정
                    HashMap < String, Object > item = new HashMap < > ();
                    item.put("WPP_CODE", wpp_code);
                    item.put("OPT_IDX", optIdx);
                    item.put("ANLY_TIME", date);
                    item.put("PRDCT_TIME", anlyTimeStr);
                    item.put("PRDCT_TIME_DIFF", time_diff);
                    item.put("PUMP_GRP", 0);
                    item.put("PRDCT_MEAN", randomValueWithinRange); // 예측값 평균 설정 필요
                    item.put("PRDCT_STD", nowValue); // 예측값 표준편차 설정 필요
                    item.put("TUBE_PRSR_PRDCT", percentage); // 관압 예측값 설정 필요
                    item.put("PWR_PRDCT", finalValue);
                    item.put("DC_NMB", null);
                    item.put("FLAG", '2');

                    //System.out.println("CalPrdctPwr item[" + time_diff + "]:" + item.toString());
                    // 데이터베이스에 삽입
                    insertPrdctResult(item);

                    // prdctTimeCal에 1시간 추가
                    prdctTimeCal.add(Calendar.HOUR, 1);
                }
            } catch (Exception e) {
                System.out.println(e.toString());
                e.printStackTrace();
            }
        }
        else
        {
            System.out.println("CalPrdctPwrOld is null");
        }
    }
    /**
     * 펌프제어 중지 메서드
     */
    public void pumpStop() {
        pumpService.pumpStop();
        HashMap<String, Object> map = new HashMap<>();
        map.put("value", 0);
        pumpService.updateGrSnPumpMode(map);
    }
    /**
     * 펌프제어 시작 메서드
     * @param map 펌프 시작을 위한 파라미터
     */
    public void pumpStart(HashMap < String, Object > map) {
        pumpService.pumpStart(map);
        HashMap<String, Object> u_map = new HashMap<>();
        u_map.put("value", 1);
        pumpService.updateGrSnPumpMode(u_map);
    }

    /**
     * 예측 조합 분 단위 데이터를 조회하는 메서드
     * @param drvnParam 조회에 필요한 파라미터
     * @return 예측 조합 데이터를 담은 해시맵
     */
    public HashMap < String, String > pumpDrvnMinute(HashMap < String, String > drvnParam) {
        return aiMapper.pumpDrvnMinute(drvnParam);
    }
    /**
     * 펌프 조합 상태를 생성하는 메서드
     * @param pumpDrvnMap 펌프 구동 정보
     * @param pump_grp_Str 펌프 그룹 정보
     * @return 펌프 조합 상태를 담은 해시맵
     */
    public HashMap < String, String > createPumpCombStatus(HashMap < String, String > pumpDrvnMap, String pump_grp_Str) {
        HashMap < String, String > returnMap = new HashMap < > ();
        int pump_grp = Integer.parseInt(pump_grp_Str);

        // 펌프 정보 조회 및 펌프 그룹으로 필터링
        List < HashMap < String, Object >> pumpAllList = aiMapper.selectPumpList();
        List < HashMap < String, Object >> pumpList = pumpAllList.stream()
                .filter(map -> map.containsKey("PUMP_GRP") && map.get("PUMP_GRP").equals(pump_grp))
                .collect(Collectors.toList());

        // 운문은 펌프타입 조건에 따른 인버터 모듈 부여를 위해 1로 초기화
        if (wpp_code.equals("wm")) {
            pumpList.forEach(map -> {
                map.put("PUMP_TYP", 1);
            });
        }

        // 펌프 idx에 따른 펌프 타입 설정
        LinkedHashMap < String, Integer > typeMap = new LinkedHashMap < > ();
        for (HashMap < String, Object > map: pumpList) {
            int pump_idx = (int) map.get("PUMP_IDX");
            String pump_idx_str = String.valueOf(pump_idx);
            int pump_typ = (int) map.get("PUMP_TYP");

            typeMap.put(pump_idx_str, pump_typ);
        }

        String cur_comb = pumpDrvnMap.get("cur_comb");
        String pre_comb = pumpDrvnMap.get("pre_comb");
        String cur_freq = pumpDrvnMap.get("cur_freq");
        String pre_freq = pumpDrvnMap.get("pre_freq");

        List < String > curCombList = new ArrayList < > ();
        List < String > preCombList = new ArrayList < > ();
        if (cur_comb != null && !cur_comb.trim().isEmpty()) {
            String[] curCombArr = cur_comb.split(",");
            curCombList = Arrays.stream(curCombArr)
                    .map(String::trim)
                    .collect(Collectors.toList());
        }
        if (pre_comb != null && !pre_comb.trim().isEmpty()) {
            String[] preCombArr = pre_comb.split(",");
            preCombList = Arrays.stream(preCombArr)
                    .map(String::trim)
                    .collect(Collectors.toList());
        }
        HashMap < String, Double > curFreqMap = new HashMap < > ();
        if (cur_freq != null && !cur_freq.trim().isEmpty()) {

            String[] freqArr = cur_freq.split(",");
            List < String > freqList = Arrays.stream(freqArr)
                    .map(String::trim)
                    .collect(Collectors.toList());
            List < String > combIvtPump = new ArrayList < > ();
            for (String pump: curCombList) {
                if (pump == null) {
                    break;
                } else {
                    if (wpp_code.equals("wm")) {
                        if (pump.matches("1|2")) {
                            combIvtPump.add(pump);
                            break;
                        }
                        if (pump.equals("4")) {
                            combIvtPump.add(pump);
                            break;
                        }
                    } else {
                        if (typeMap.get(pump) == 2) {
                            combIvtPump.add(pump);
                        }
                    }
                }
            }
            if (!combIvtPump.isEmpty()) {
                for (int i = 0; i < combIvtPump.size(); i++) {
                    String idx = combIvtPump.get(i);
                    String freqStr = freqList.get(i);
                    Double freqDb = Double.valueOf(freqStr);
                    if (wpp_code.equals("gr")) {
                        freqDb = (double) Math.round(0.6 * freqDb);
                    }
                    curFreqMap.put(idx, freqDb);
                }

            }
        }

        HashMap < String, Double > preFreqMap = new HashMap < > ();
        if (pre_freq != null && !pre_freq.trim().isEmpty()) {

            String[] freqArr = pre_freq.split(",");
            List < String > freqList = Arrays.stream(freqArr)
                    .map(String::trim)
                    .collect(Collectors.toList());
            List < String > combIvtPump = new ArrayList < > ();
            for (String pump: preCombList) {
                if (pump == null) {
                    break;
                } else {
                    if (wpp_code.equals("wm")) {
                        if (pump.matches("1|2")) {
                            combIvtPump.add(pump);
                            break;
                        }
                        if (pump.equals("4")) {
                            combIvtPump.add(pump);
                            break;
                        }
                    } else {
                        if (typeMap.get(pump) == 2) {
                            combIvtPump.add(pump);
                        }
                    }
                }
            }
            if (!combIvtPump.isEmpty()) {
                for (int i = 0; i < combIvtPump.size(); i++) {
                    String idx = combIvtPump.get(i);
                    String freqStr = freqList.get(i);
                    Double freqDb = Double.valueOf(freqStr);
                    preFreqMap.put(idx, freqDb);
                }

            }
        }
        List < String > finalCurCombList = new ArrayList < > ();
        List < String > finalpreCombList = new ArrayList < > ();
        if (!curCombList.isEmpty()) {
            for (String curComb: curCombList) {
                String pumpIdx;
                if (curFreqMap.containsKey(curComb)) {
                    pumpIdx = curComb + "(" + curFreqMap.get(curComb) + "Hz)";
                } else {
                    pumpIdx = curComb;
                }
                finalCurCombList.add(pumpIdx);
            }
        }
        if (!preCombList.isEmpty()) {

            for (String preComb: preCombList) {
                String pumpIdx;
                if (preFreqMap.containsKey(preComb)) {
                    pumpIdx = preComb + "(" + preFreqMap.get(preComb) + "Hz)";
                } else {
                    pumpIdx = preComb;
                }
                finalpreCombList.add(pumpIdx);
            }
        }

        //정리된 조합
        String curPump = String.join(", ", finalCurCombList);
        String prePump = String.join(", ", finalpreCombList);
        String flow_ctr = pumpDrvnMap.get("FLOW_CTR");

        returnMap.put("curPump", curPump);
        returnMap.put("prePump", prePump);
        returnMap.put("flow_ctr", flow_ctr);

        return returnMap;
    }
    /**
     * AI 펌프 시간을 조회하는 메서드
     * @return AI 펌프 시간을 반환
     */
    public String getAIPumpTime() {
        return aiMapper.getAIPumpTime();
    }

    public List<HashMap<String, Object>> selectAiModeRstList(HashMap<String, Object> map){
        return  aiMapper.selectAiModeRstList(map);
    }

    public void updateAiModeRst(HashMap<String, String> map)
    {
        aiMapper.updateAiModeRst(map);
    }

    public HashMap<String, String> selectAiModeRstItem(HashMap<String, String> map){
        return  aiMapper.selectAiModeRstItem(map);
    }

    public HashMap<String, Integer> getAiModeCount(HashMap<String, Object> param){
        HashMap<String, Integer> countMap = new HashMap<>();
        List<String> aiModeList = aiMapper.getAiModeCount(param);
        countMap.put("total", 0);
        countMap.put("ai", 0);
        countMap.put("recom", 0);
        countMap.put("anal", 0);

        if (!aiModeList.isEmpty()) {
            for (String mode : aiModeList) {
                int modeInt;
                try {
                    modeInt = Integer.parseInt(mode);
                } catch (NumberFormatException | NullPointerException e) {
                    modeInt = 2;
                }

                // total은 무조건 1씩 증가
                countMap.put("total", countMap.get("total") + 1);

                // 각 값에 따라 해당 key를 1 증가
                switch (modeInt) {
                    case 0:
                        countMap.put("ai", countMap.get("ai") + 1);
                        break;
                    case 1:
                        countMap.put("recom", countMap.get("recom") + 1);
                        break;
                    case 2:
                    default:
                        countMap.put("anal", countMap.get("anal") + 1);
                        break;
                }
            }
        }

        return countMap;
    }

}