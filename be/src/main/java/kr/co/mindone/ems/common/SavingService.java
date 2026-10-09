package kr.co.mindone.ems.common;
/**
 * packageName    : kr.co.mindone.ems.common
 * fileName       : SavingService
 * date           : 24. 9. 23.
 * description    : 에너지 절약 계산과 관련된 서비스 클래스
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        -            최초 생성
 */
import kr.co.mindone.ems.setting.SettingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.DecimalFormat;
import java.text.ParseException;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.LocalDateTime;

@Service
public class SavingService {
    public static final String SSN_SP = "봄철";
    public static final String SSN_SM = "여름";
    public static final String SSN_AT = "가을";
    public static final String SSN_WT = "겨울";

    public static final String RANGE_DAY_AGO = "dayAgo";
    public static final String RANGE_DAY = "day";
    public static final String RANGE_MONTH = "month";
    public static final String RANGE_YEAR = "year";
    public static final String RANGE_ALL = "all";

    @Autowired
    private CommonService commonService;
    @Autowired
    private SettingService settingService;
    @Value("${tag.value.default.rate.idx}")
    private String rate_idx;
    @Value("${tag.value.default.rate.fee}")
    private int default_fee;
    @Value("${tag.value.co2}")
    private double co2_value;
    @Value("${tag.value.default.frq}")
    private double default_frq;
    @Value("${tag.value.default.elec}")
    private double default_elec;

    @Value("${spring.profiles.active}")
    private String wpp_code;

    /**
     * 절감량 계산 및 삽입 처리
     * @param range 범위 (일, 월, 연도 등)
     * @param initDate 기준이 되는 날짜
     * @return 절감량 계산 결과를 담은 맵
     */
    public HashMap<String, Object> savingCalculationInsert(String range, String initDate) {
        /**
         * Step 1. 설정된 목표사용량에서 현재 월을 획득하여 일 평균 목표사용량을 구함
         */
        String date = "";
        int hour = 23;
        if (initDate.equals("none")) {
            ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
            ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);
            LocalDateTime koreaLocalDateTime = koreaZonedDateTime.toLocalDateTime();

            date = getDate(range);
            String nowDate = getDate(RANGE_DAY); // 오늘의 날짜를 가져옵니다.

            // `date`가 오늘이 아닌 경우 `hour`을 24로 설정합니다.
            if (!date.equals(nowDate)) {
                hour = 23;
            } else {
                hour = koreaLocalDateTime.getHour();
            }
        } else {
            date = initDate;
        }

        DecimalFormat df = new DecimalFormat("0.00");

        double nowGoal = 0.0;
        //nowGoal  = getGoalValue(range, date, hour);
        nowGoal  = getGoalValueNowDate( date, hour);

        /**
         *  Step 2. 전일 전력사용량을 구하고 목표값과의 차이를 구함
         */

        double allElecValue = 0.0;
        //System.out.println("getRangeAllElec:"+range +"/"+date);
        allElecValue = getRangeAllElec(range, date);
        double saveElecValue = nowGoal - allElecValue;

        /**
         * Step 3. 사용한 전력, 목표전력의 각 요금을 구함
         */

        int baseFEE = 0;
        double saveFEEvalue = 0.0;

        baseFEE = getBaseFEE(date);

        saveFEEvalue = saveElecValue * baseFEE * 0.0001;

        /**
         * Step 4. 탄소 절감량 계산하기
         */
        double saveCO2Value = 0.0;
        saveCO2Value = getCO2Value(saveElecValue);

        /**
         *  Step 5. 현재 원단위 구하기 - 현재원단위(kWh/m3) 전체전력/전체유량 FRQ
         */

        double saveUnitValue = 0.0;
        double nowFrq = getFrqValue(date,range);
        saveUnitValue = getUnitValue(date, range ,allElecValue, nowFrq);

        /**
         *  Step 6. 날짜에 대한 weekday(주중), sat(토), sun(일) 구하기
         */
        String nowDayType = "";
        if(range.equals(RANGE_MONTH))
        {
            nowDayType = "mm";
        }
        else {
            nowDayType = checkDayType(date);
        }

        /**
         * Step7. 해당 결과를 저장
         */
        //String.format("%.0f", )
        HashMap<String, Object> rstSavingMap = new HashMap<>();
        rstSavingMap.put("date",date);
        rstSavingMap.put("type",nowDayType);
        rstSavingMap.put("savingCo2", df.format(saveCO2Value));
        rstSavingMap.put("savingCost",df.format(saveFEEvalue));
        rstSavingMap.put("savingKwh", df.format(saveElecValue));
        rstSavingMap.put("savingUnit",df.format(saveUnitValue));
        rstSavingMap.put("nowGoal", nowGoal);
        rstSavingMap.put("allElecValue", allElecValue);
        rstSavingMap.put("nowFrq", nowFrq);

        /*
        System.out.println("#########################################");
        System.out.println("range: "+range);
        System.out.println("date: "+date);
        System.out.println("type: "+nowDayType);
        System.out.println("allElecValue: "+allElecValue);
        System.out.println("nowGoal: "+nowGoal);
        System.out.println("savingCo2: "+df.format(saveCO2Value));
        System.out.println("savingCost: "+df.format(saveFEEvalue));
        System.out.println("savingKwh: "+df.format(saveElecValue));
        System.out.println("savingUnit: "+df.format(saveUnitValue));
        System.out.println("#########################################");/**/

        commonService.insertRstSavingsTarget(rstSavingMap);

        HashMap<String, Object> baseSavingMap = new HashMap<>();
        baseSavingMap.put("type", nowDayType);
        String[] dateStr = date.split("-");
        baseSavingMap.put("mnth",dateStr[1]+"m");
        baseSavingMap.put("value", df.format(saveElecValue)); //전력
        baseSavingMap.put("unit","kwh");
        commonService.insertBaseSavingsTarget(baseSavingMap);

        baseSavingMap.put("value",saveFEEvalue); //전기료
        baseSavingMap.put("unit","won");
        commonService.insertBaseSavingsTarget(baseSavingMap);

        baseSavingMap.put("value", df.format(saveUnitValue)); //원단위
        baseSavingMap.put("unit","kwh/t*cost");
        commonService.insertBaseSavingsTarget(baseSavingMap);


        return rstSavingMap;
    }

    /**
     * 현재 월에 따른 계절 반환
     * @param daysInMonth 월의 일 수
     * @return 계절 이름
     */
    public String getNowSSN(int daysInMonth)
    {
        String result_SSN = "";

        if(daysInMonth == 3 || daysInMonth == 4 || daysInMonth == 5)
        {
            result_SSN = SSN_SP;
        }
        else if(daysInMonth == 6 || daysInMonth == 7 || daysInMonth == 8)
        {
            result_SSN = SSN_SM;
        }
        else if(daysInMonth == 9 || daysInMonth == 10 || daysInMonth == 11)
        {
            result_SSN = SSN_AT;
        }
        else if(daysInMonth == 1 || daysInMonth == 2 || daysInMonth == 12)
        {
            result_SSN = SSN_WT;
        }
        else
        {
            result_SSN = SSN_SP;
        }
        return result_SSN;
    }

    /**
     * 주중, 주말, 휴일을 체크하여 반환
     * @param date 확인할 날짜
     * @return 날짜의 타입 (주중, 토요일, 일요일)
     */
    public String checkDayType(String date) {
        // 입력된 날짜 문자열을 LocalDate 객체로 파싱
        LocalDate inputDate = LocalDate.parse(date, DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        DayOfWeek dayOfWeek = inputDate.getDayOfWeek();
        switch (dayOfWeek) {
            case MONDAY:
            case TUESDAY:
            case WEDNESDAY:
            case THURSDAY:
            case FRIDAY:
                return "weekday";
            case SATURDAY:
                return "sat";
            case SUNDAY:
                return "sun";
            default:
                return "unknown";
        }
    }

    /**
     * 범위와 날짜에 따른 목표 전력 사용량 계산
     * @param range 범위 (일, 월, 연도 등)
     * @param date 기준이 되는 날짜
     * @param hour 현재 시간
     * @return 목표 전력 사용량
     */
    public double getGoalValue(String range, String date, int hour)
    {
        double goalResult = 0.0;
        String[] dateStr = date.split("-");
        int year = Integer.valueOf(dateStr[0]);
        int month = Integer.valueOf(dateStr[1]);
        int day = Integer.valueOf(dateStr[2]);

        LocalDate currentDate = LocalDate.now();
        LocalDate inputDate = LocalDate.parse(date, DateTimeFormatter.ofPattern("yyyy-MM-dd"));



        HashMap<String, Object> map = new HashMap<>();

        double nowDayGoalValue = 0.0;

        //Double.parseDouble(nowGoalMap.get("goalValue").toString());

        if(range.equals(RANGE_DAY_AGO) || range.equals(RANGE_DAY) || range.equals(RANGE_MONTH))
        {
            if(range.equals(RANGE_MONTH))
            {
                map.put("mm", month+"m");
                map.put("type", "mm");
                map.put("year", year);
                HashMap<String, Object> nowGoalMap = commonService.selectDayGoal(map);
                //nowDayGoalValue =  Double.parseDouble(nowGoalMap.get("goalValue").toString());
            }
            else {

                map.put("mm", month+"m");
                map.put("year", year);
                map.put("type", getDayType(year, date));
                //System.out.println("map:"+map.toString());
                HashMap<String, Object> nowGoalMap = commonService.selectDayGoal(map);
                //System.out.println("nowGoalMap"+nowGoalMap.toString());
                nowDayGoalValue =  Double.parseDouble(nowGoalMap.get("goalValue").toString());
                //System.out.println("nowDayGoalValue:"+nowDayGoalValue + "/"+hour);
                if(hour != 24)
                {
                    goalResult = (nowDayGoalValue/24) * hour;
                }
                else {
                    goalResult = nowDayGoalValue;
                }
            }
        }
        else { //year

        }
        return goalResult;
    }


    public double getGoalValueNowDate(String date, int hour) {
        double goalResult = 0.0;
        String[] dateStr = date.split("-");
        int year = Integer.valueOf(dateStr[0]);
        int month = Integer.valueOf(dateStr[1]);

        HashMap<String, Object> map = new HashMap<>();
        map.put("mm", month + "m");
        map.put("year", "2024");
        map.put("type", getDayType(year, date));


        double nowDayGoalValue = 0.0;
        System.out.println("nowGoal#Map:"+map.toString());
        HashMap<String, Object> nowGoalMap = commonService.selectDayGoal(map);
        System.out.println("nowGoalMap:"+nowGoalMap.toString());
        if (nowGoalMap.get("goalValue") != null) {
            nowDayGoalValue = Double.parseDouble(nowGoalMap.get("goalValue").toString());
        }

        if (hour < 23) {
            goalResult = (nowDayGoalValue / 24) * (hour+1);
        } else {
            goalResult = nowDayGoalValue;
        }

        return goalResult;
    }


    /**

    public double getGoalValue_old(String range, String date, int hour)
    {
        double goalResult = 0.0;
        String[] dateStr = date.split("-");
        int year = Integer.valueOf(dateStr[0]);
        int month = Integer.valueOf(dateStr[1]);
        int day = Integer.valueOf(dateStr[2]);

        HashMap<String, Object> map = new HashMap<>();
        map.put("mm", month+"m");
        map.put("type", "");
        HashMap<String, Object> nowGoalMap = commonService.selectDayGoal(map);

        List<HashMap<String, Object>> goalList = settingService.selectGetSetting();

        if(range.equals(RANGE_DAY_AGO) || range.equals(RANGE_DAY) || range.equals(RANGE_MONTH))
        {
            double nowYearMonthGoal = goalList.stream()
                    .filter(item -> item.get("year").equals(String.valueOf(year)))
                    .mapToDouble(item -> {
                        String mnth = String.valueOf(month) + "m";
                        return Double.parseDouble(item.getOrDefault(mnth, "0.0").toString());
                    })
                    .findFirst()
                    .orElse(0.0);

            if(range.equals(RANGE_MONTH))
            {
                int daysInMonth = getMonthDayCount(date);
                goalResult = (nowYearMonthGoal / daysInMonth) *day;
            }
            else
            {
                int daysInMonth = getMonthDayCount(date);
                if(hour != 0 )
                {
                    double timeGaol = 0.0;
                    timeGaol = nowYearMonthGoal / daysInMonth;
                    goalResult = (timeGaol / 24) * hour;
                }
                else {
                    goalResult = nowYearMonthGoal / daysInMonth;
                }
            }
        }
        else {
            // 연도의 경우 해당 연도의 월까지의 합산 목표 절감량을 더함
            for(HashMap<String, Object> item : goalList)
            {
                if(item.get("year").toString().equals(String.valueOf(year)))
                {
                    for (int i = 1; i <= month; i++)
                    {
                        String monthKey = i + "m";
                        Object monthValue = item.get(monthKey);
                        if (monthValue != null) {
                            goalResult += Double.parseDouble(monthValue.toString());
                        }
                    }
                }
            }
        }
        BigDecimal bd = new BigDecimal(Double.toString(goalResult));
        bd = bd.setScale(2, RoundingMode.HALF_UP);
        return bd.doubleValue();
    }*/

    /**
     * 범위에 따른 전체 전력 사용량 반환
     * @param range 범위 (일, 월, 연도 등)
     * @param date 기준이 되는 날짜
     * @return 전체 전력 사용량
     */
    public double getRangeAllElec(String range, String date)
    {
        double value = 0.0;
        HashMap<String, Object> elecParam = new HashMap<>();
        elecParam.put("date",date);
        elecParam.put("range",range);
        HashMap<String, Object> rstItem = commonService.selectRangeElecPwiValue(elecParam);
        //HashMap<String, Object> rstItem = commonService.selectRangeElecValue(elecParam);
        System.out.println("rstItem:"+rstItem);
        value = Double.parseDouble(rstItem.get("value").toString());
        if(value == 0.0)
        {
            value = default_elec;
        }
        return value;
    }

    /**
     * 전력 사용량 대비 원단위 계산
     * @param date 기준이 되는 날짜
     * @param range 범위 (일, 월, 연도 등)
     * @param allElecValue 전력 사용량
     * @param previousDayFRQ 전날의 유량
     * @return 원단위 계산 결과
     */
    public double getUnitValue(String date, String range, double allElecValue, double previousDayFRQ)
    {
        if(previousDayFRQ == 0.0)
        {
            previousDayFRQ = default_frq;
        }

        return allElecValue/previousDayFRQ;
    }

    /**
     * 유량 값 반환
     * @param date 기준이 되는 날짜
     * @param range 범위 (일, 월, 연도 등)
     * @return 유량 값
     */
    public double getFrqValue(String date, String range) {
        HashMap<String, Object> elecParam = new HashMap<>();
        elecParam.put("date", date);
        elecParam.put("range", range);

        HashMap<String, Object> frqItem = commonService.selectAfterDayFRQ(elecParam);
        String frqVale = frqItem.get("value").toString().replaceAll(",", "");
        double frqValue = Double.parseDouble(frqVale);

        try {
            // 소수점 둘째 자리까지만 포맷팅
            DecimalFormat decimalFormat = new DecimalFormat("#.##");
            return Double.parseDouble(decimalFormat.format(frqValue));
        } catch (Exception e) {
            // 포맷팅 실패 시 원본 double 값 반환
            return frqValue;
        }
    }

    /**
     * 날짜에 따른 포맷팅된 날짜 반환
     * @param range 범위 (일, 월, 연도 등)
     * @return 포맷팅된 날짜 문자열
     */
    public String getDate(String range)
    {
        String date = "";
        LocalDate currentDate = LocalDate.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");

        if(range.equals(RANGE_DAY_AGO))
        {
            LocalDate previousDay = currentDate.minusDays(1); // 하루 전 날짜를 계산
            date = previousDay.format(formatter);
        }
        else {
            date = currentDate.format(formatter);
        }
        return date;
    }

    /**
     * 해당 월의 일수 반환
     * @param date 날짜
     * @return 월의 일수
     */
    public int getMonthDayCount(String date)
    {
        int daysInMonth = 0;
        LocalDate currentDate = LocalDate.parse(date);
        int year = currentDate.getYear();
        int month = currentDate.getMonthValue();
        YearMonth dayYearMonth = YearMonth.of(year, month);
        daysInMonth = dayYearMonth.lengthOfMonth();
        return  daysInMonth;
    }

    /**
     * 날짜에 해당하는 월 반환
     * @param date 날짜
     * @return 월
     */
    public int getMonth(String date)
    {
        LocalDate inputDate = LocalDate.parse(date, DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        int month = inputDate.getMonthValue();
        return month;
    }

    /**
     * 해당 날짜에 따른 기본 전기 요금 반환
     * @param date 기준이 되는 날짜
     * @return 기본 전기 요금
     */
    public int getBaseFEE(String date)
    {
        HashMap<String, Object> rateInfoParam = new HashMap<>();
        rateInfoParam.put("rate_idx",rate_idx);
        rateInfoParam.put("ssn",getNowSSN(getMonth(date)));
        List<HashMap<String, Object>> rateInfoList =  settingService.selectRT_RATE_INF(rateInfoParam);

        int baseFEE = 0;
        double previousDayFEE = 0.0;

        if(!rateInfoList.isEmpty())
        {
            baseFEE = Integer.parseInt(rateInfoList.get(0).get("BASE_RATE").toString());
        }
        else
        {
            baseFEE = default_fee;
        }
        return  baseFEE;
    }


    /**
     * 전력 사용량에 따른 탄소 절감량 반환
     * @param elecValue 전력 사용량
     * @return 탄소 절감량
     */
    public double getCO2Value(double elecValue)
    {
        return elecValue * co2_value;
    }

    /**
     * 연도와 날짜에 따른 날 타입 반환 (주중, 주말, 휴일)
     * @param year 연도
     * @param date 날짜
     * @return 날 타입
     */
    public String getDayType(int year, String date) {
        ArrayList<LocalDate> hDay = new ArrayList<>();
        hDay.add(LocalDate.parse(year + "-01-01")); // 신정
        hDay.add(LocalDate.parse(year + "-01-21")); // 설날 연휴 시작
        hDay.add(LocalDate.parse(year + "-01-22")); // 설날
        hDay.add(LocalDate.parse(year + "-01-23")); // 설날 연휴 끝
        hDay.add(LocalDate.parse(year + "-03-01")); // 삼일절
        hDay.add(LocalDate.parse(year + "-05-05")); // 어린이날
        hDay.add(LocalDate.parse(year + "-05-27")); // 석가탄신일
        hDay.add(LocalDate.parse(year + "-06-06")); // 현충일
        hDay.add(LocalDate.parse(year + "-08-15")); // 광복절
        hDay.add(LocalDate.parse(year + "-09-28")); // 추석 연휴 시작
        hDay.add(LocalDate.parse(year + "-09-29")); // 추석
        hDay.add(LocalDate.parse(year + "-09-30")); // 추석 연휴 끝
        hDay.add(LocalDate.parse(year + "-10-03")); // 개천절
        hDay.add(LocalDate.parse(year + "-10-09")); // 한글날
        hDay.add(LocalDate.parse(year + "-12-25")); // 성탄절

        LocalDate inputDate = LocalDate.parse(date, DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        DayOfWeek dayOfWeek = inputDate.getDayOfWeek();
        if (dayOfWeek == DayOfWeek.SATURDAY) {
            return "sat";
        } else if (dayOfWeek == DayOfWeek.SUNDAY) {
            return "sun";
        } else {
            if(hDay.contains(inputDate))
            {
                return "sun";
            }
            return "weekday";
        }
    }
}
