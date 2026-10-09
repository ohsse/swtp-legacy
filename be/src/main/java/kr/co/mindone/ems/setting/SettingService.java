package kr.co.mindone.ems.setting;
/**
 * packageName    : kr.co.mindone.ems.setting
 * fileName       : SettingService
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import io.swagger.models.auth.In;
import kr.co.mindone.ems.alarm.AlarmMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.text.DecimalFormat;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class SettingService {

    @Autowired
    private SettingMapper settingMapper;
    @Autowired
    private AlarmMapper alarmMapper;
    /**
     * 사용량 데이터 조회
     * @param map 요청 필터 조건
     * @return 사용량 데이터 리스트
     */
    List<HashMap<String, Object>> getUsageData(HashMap<String, Object> map) { return settingMapper.getUsageData(map); }
    /**
     * 목표 전력 데이터 조회
     * @param map 요청 필터 조건
     * @return 목표 전력 데이터 리스트
     */
    List<HashMap<String, Object>> getGoalData(HashMap<String, Object> map) {
        return settingMapper.getGoalData(map);
    }
    /**
     * 설비 정보 조회
     * @param map 요청 필터 조건
     * @return 설비 데이터 리스트
     */
    public List<HashMap<String, Object>> selectZone(HashMap<String, Object> map) { return settingMapper.selectZone(map); }
    /**
     * 태그 리스트 조회
     * @param map 요청 필터 조건
     * @return 태그 리스트
     */
    List<HashMap<String, Object>> selectTagList(HashMap<String, Object> map) { return settingMapper.selectTagList(map); }



    /**
     * 실시간 절감 정보 조회
     * @param params 요청 필터 조건
     * @return 실시간 절감 정보 리스트
     */
    public List<HashMap<String, Object>> selectRtInfo(HashMap<String, Object> params) {
        return settingMapper.selectRtInfo(params);
    }
    /**
     * 실시간 요금 정보 조회
     * @param params 요청 필터 조건
     * @return 실시간 요금 정보 리스트
     */
    public List<HashMap<String, Object>> selectRT_RATE_INF(HashMap<String, Object> params) {
        return settingMapper.selectRT_RATE_INF(params);
    }
    /**
     * 순시 전력 정보 조회
     * @param params 요청 필터 조건
     * @return 순시 전력 정보 리스트
     */
    public List<HashMap<String, Object>> selectSuji(HashMap<String, Object> params) {
        return settingMapper.selectSuji(params);
    }

    /**
     * 펌프 정보 조회
     * @return 펌프 정보 리스트
     */
    public List<HashMap<String, Object>> selectCTR_PRF_PUMPMST_INF() {
        return settingMapper.selectCTR_PRF_PUMPMST_INF();
    }
    /**
     * 태그 정보 업데이트
     * @param map 업데이트할 태그 정보
     */
    public void updateTagInfo(HashMap<String, Object> map) {
        settingMapper.updateTagInfo(map);
    }
    /**
     * 시설 정보 업데이트
     * @param map 업데이트할 시설 정보
     */
    public void updateFac(HashMap<String, Object> map) {
        settingMapper.updateFac(map);
    }

    /**
     * 실시간 요금 정보 업데이트
     * @param params 요금 정보
     * @param time 시간 정보
     */
    public void updateRT_RATE_INF(HashMap<String, Object> params, HashMap time) {
        settingMapper.update_L_RT_RATE_INF(params);//경부하
        settingMapper.update_M_RT_RATE_INF(params);//중간부하
        settingMapper.update_H_RT_RATE_INF(params);//최대부하
        settingMapper.update_time_RT_RATE_INF(time);
    }
    /**
     * 목표 전력 설정 정보 조회
     * @return 목표 전력 정보 리스트
     */
    public List<HashMap<String, Object>> selectGetSetting() {
        return settingMapper.selectGetSetting();
    }
    /**
     * 목표 전력정보 업데이트
     * @param params 업데이트할 목표 전력 정보
     */
    public void updateGoal(HashMap<String, Object> params) {
        settingMapper.updateGoal(params);
    }
    /**
     * 전략 정보 병합
     * @param maps 병합할 전략 정보 리스트
     */
    public void mergePTR_STRTG_INF(List<HashMap<String , String>> maps) {
        for(HashMap<String, String> map:maps){
            settingMapper.mergePTR_STRTG_INF(map);
        }
    }
    /**
     * 운영 정보 병합
     * @param params 병합할 운영 정보
     */
    public void mergeOPER_INF(HashMap<String, Object> params) {
        settingMapper.mergeOPER_INF(params);
    }
    /**
     * 펌프 설정 정보 업데이트
     * @param list 업데이트할 펌프 설정 리스트
     */
    public void updateSetCTR_PRF_PUMPMST_INF(List<HashMap<String, Object>> list) {
        for(HashMap<String, Object> map:list){
            settingMapper.updateSetCTR_PRF_PUMPMST_INF(map);

        }
    }
    /**
     * 리포트 전력 사용량 조회
     * @param params 요청 필터 조건
     * @return 전력 사용량 리포트 리스트
     */
    public List<HashMap<String, Object>> selectReport_kwh(HashMap<String, Object> params) {
        return settingMapper.selectReport_kwh(params);
    }
    /**
     * 전력 사용량 퍼센트 조회
     * @param params 요청 필터 조건
     * @param type 전력 타입
     * @return 전력 사용량 퍼센트 값
     */
    public Double selectReport_kwh_p(HashMap<String, Object> params, String type){
        double value = 0.0;
        value = (
                Double.parseDouble(params.get(type).toString()) /
                        (
                            Double.parseDouble(params.get("l_kwh").toString()) +
                            Double.parseDouble(params.get("m_kwh").toString()) +
                            Double.parseDouble(params.get("h_kwh").toString())
                        )
                ) * 100;
        return value;
    }
    /**
     * 펌프 리포트 조회
     * @param params 요청 필터 조건
     * @return 펌프 리포트 리스트
     */
    public List<HashMap<String, Object>> selectReportPump(HashMap<String, Object> params)
    {
        DecimalFormat df = new DecimalFormat("0.00");
        List<HashMap<String, Object>> tempObjectList3 = new ArrayList<HashMap<String, Object>>();
        List<HashMap<String, Object>> tempReturnObjectList3 =  new ArrayList<HashMap<String, Object>>();

        params.put("range","day");
        params.put("type","ctr_rate");
        tempObjectList3.addAll(selectReport3(params)); //282
        params.put("type","pump_kwh");
        tempObjectList3.addAll(selectReport3(params)); //306
        params.put("type","frq_value");
        tempObjectList3.addAll(selectReport3(params)); //331

        params.put("range","month");
        params.put("type","ctr_rate");
        tempObjectList3.addAll(selectReport3(params));  //582
        params.put("type","pump_kwh");
        tempObjectList3.addAll(selectReport3(params)); //294
        params.put("type","frq_value");
        tempObjectList3.addAll(selectReport3(params));  //352

        HashMap<String, Object> ctrRateDayMap = new HashMap<>();
        HashMap<String, Object> pwrKwhDayMap = new HashMap<>();
        HashMap<String, Object> ctrRateMonthMap = new HashMap<>();
        HashMap<String, Object> pwrKwhMonthMap = new HashMap<>();

        double dayPwrSum = 0.0;
        double monthPwrSum = 0.0;
        double dayFrqValue = 0.0;
        double monthFrqValue = 0.0;

        ctrRateDayMap.put("type", "ctr_rate_day");
        pwrKwhDayMap.put("type", "pwr_kwh_day");
        ctrRateMonthMap.put("type", "ctr_rate_month");
        pwrKwhMonthMap.put("type", "pwr_kwh_month");

        for(int i=0; i<tempObjectList3.size(); i++)
        {
            HashMap<String, Object> tempData = tempObjectList3.get(i);
            String PUMP_IDX = tempData.get("PUMP_IDX").toString();
            PUMP_IDX = "pump_"+PUMP_IDX;
            double ctr_rate = 0.0, pump_kwh = 0.0, frq_value =0.0;
            //System.out.println(tempData);
            if(tempData.get("range").toString().equals("day"))
            {
                if(tempData.get("ctr_rate")!=null)
                {
                    ctr_rate = Double.parseDouble(tempData.get("ctr_rate").toString());
                    ctrRateDayMap.put(PUMP_IDX,ctr_rate);
                }
                else if(tempData.get("pump_kwh")!=null)
                {
                    pump_kwh = Double.parseDouble(tempData.get("pump_kwh").toString());
                    //System.out.println(pump_kwh);
                    dayPwrSum += pump_kwh;
                    pwrKwhDayMap.put(PUMP_IDX,pump_kwh);
                }
                else if(tempData.get("frq_value")!=null)
                {
                    frq_value = Double.parseDouble(tempData.get("frq_value").toString());
                    dayFrqValue = frq_value;
                }
            }
            else if(tempData.get("range").toString().equals("month")){
                if(tempData.get("ctr_rate")!=null)
                {
                    ctr_rate = Double.parseDouble(tempData.get("ctr_rate").toString());
                    ctrRateMonthMap.put(PUMP_IDX,ctr_rate);
                }
                else if(tempData.get("pump_kwh")!=null)
                {
                    pump_kwh = Double.parseDouble(tempData.get("pump_kwh").toString());
                    monthPwrSum += pump_kwh;
                    pwrKwhMonthMap.put(PUMP_IDX,pump_kwh);
                }
                else if(tempData.get("frq_value")!=null)
                {
                    frq_value = Double.parseDouble(tempData.get("frq_value").toString());
                    monthFrqValue = frq_value;
                }
            }
        }
        pwrKwhDayMap.put("pwr_sum",df.format(dayPwrSum));
        ctrRateDayMap.put("pwr_sum",df.format(dayPwrSum));
        pwrKwhMonthMap.put("pwr_sum",df.format(monthPwrSum));
        ctrRateMonthMap.put("pwr_sum",df.format(monthPwrSum));

        pwrKwhDayMap.put("frq_value",df.format(dayFrqValue));
        ctrRateDayMap.put("frq_value",df.format(dayFrqValue));
        pwrKwhMonthMap.put("frq_value",df.format(monthFrqValue));
        ctrRateMonthMap.put("frq_value",df.format(monthFrqValue));

        pwrKwhDayMap.put("basic_unit",df.format(dayPwrSum/dayFrqValue));
        ctrRateDayMap.put("basic_unit",df.format(dayPwrSum/dayFrqValue));
        pwrKwhMonthMap.put("basic_unit",df.format(monthPwrSum/monthFrqValue));
        ctrRateMonthMap.put("basic_unit",df.format(monthPwrSum/monthFrqValue));

        pwrKwhDayMap.put("type", "pwr_kwh_day");
        ctrRateDayMap.put("type", "ctr_rate_day");
        pwrKwhMonthMap.put("type", "pwr_kwh_month");
        ctrRateMonthMap.put("type", "ctr_rate_month");

        tempReturnObjectList3.add(pwrKwhDayMap);
        tempReturnObjectList3.add(ctrRateDayMap);
        tempReturnObjectList3.add(pwrKwhMonthMap);
        tempReturnObjectList3.add(ctrRateMonthMap);

        return  tempReturnObjectList3;
    }
    /**
     * 설비별 전력 사용량 리포트 조회
     * @param params 요청 필터 조건
     * @return 설비별 전력 사용량 리포트 리스트
     */
    public List<HashMap<String, Object>> selectReportZonePwr(HashMap<String, Object> params)
    {
        DecimalFormat df = new DecimalFormat("0.00");
        List<HashMap<String, Object>> tempObjectList2 = new ArrayList<HashMap<String, Object>>();
        List<HashMap<String, Object>> tempReturnObjectList2 = new ArrayList<HashMap<String, Object>>();

        params.put("range","dayAgo");
        tempObjectList2.addAll(selectReport2(params));

        params.put("range","day");
        tempObjectList2.addAll(selectReport2(params));

        params.put("range","month");
        tempObjectList2.addAll(selectReport2(params));

        params.put("range","year");
        tempObjectList2.addAll(selectReport2(params));

        HashMap<String, Object> kwhDayAgoMap2 = new HashMap<>();
        HashMap<String, Object> kwhDayMap2 = new HashMap<>();
        HashMap<String, Object> kwhMonthMap2 = new HashMap<>();
        HashMap<String, Object> KwhYearMap2 = new HashMap<>();

        kwhDayAgoMap2.put("type", "kwh_dayAgo");
        kwhDayMap2.put("type", "kwh_day");
        kwhMonthMap2.put("type", "kwh_month");
        KwhYearMap2.put("type", "kwh_year");

        double kwh_dayAgo_sum = 0.0, kwh_day_sum = 0.0, kwh_month_sum = 0.0, kwh_year_sum = 0.0;

        for(int i=0; i<tempObjectList2.size(); i++)
        {
            HashMap<String, Object> tempData = tempObjectList2.get(i);
            String typeCode = tempData.get("type").toString();
            String zone_code = tempData.get("zone_code").toString();
            double value = 0.0;
            value = Double.parseDouble(tempData.get("value").toString());
            if(typeCode.equals("kwh_dayAgo")){
                kwhDayAgoMap2.put(zone_code, df.format(value));
                kwh_dayAgo_sum += value;
            }
            else if(typeCode.equals("kwh_day")){
                kwhDayMap2.put(zone_code, df.format(value));
                kwh_day_sum += value;
            }
            else if(typeCode.equals("kwh_month")){
                 kwhMonthMap2.put(zone_code, df.format(value));
                 kwh_month_sum += value;
            }
            else if(typeCode.equals("kwh_year")){
                 KwhYearMap2.put(zone_code, df.format(value));
                 kwh_year_sum += value;
            }
        }
        kwhDayAgoMap2.put("kwh_sum",kwh_dayAgo_sum);
        kwhDayMap2.put("kwh_sum",kwh_day_sum);
        kwhMonthMap2.put("kwh_sum",kwh_month_sum);
        KwhYearMap2.put("kwh_sum",kwh_year_sum);
        tempReturnObjectList2.add(kwhDayAgoMap2);
        tempReturnObjectList2.add(kwhDayMap2);
        tempReturnObjectList2.add(kwhMonthMap2);
        tempReturnObjectList2.add(KwhYearMap2);


        return tempReturnObjectList2;
    }
    /**
     * 전력 리포트 조회
     * @param params 요청 필터 조건
     * @param type 리포트 타입
     * @return 전력 리포트 데이터
     */
    public HashMap<String, Object> selectReportPwr(HashMap<String, Object> params, String type )
    {
        DecimalFormat df = new DecimalFormat("0.00");
        List<HashMap<String, Object>> tempObjectPwrList = new ArrayList<HashMap<String, Object>>();
        List<HashMap<String, Object>> tempObjectSavingList = new ArrayList<HashMap<String, Object>>();

        params.put("range",type);

        tempObjectPwrList.addAll(selectReport_kwh(params));
        tempObjectSavingList.addAll(selectReport_saving(params));

        HashMap<String, Object> rangeObjMap = new HashMap<>();
        rangeObjMap.put("type", "kwh_"+type);

        for(int i=0; i<tempObjectPwrList.size(); i++)
        {
            HashMap<String, Object> tempData = tempObjectPwrList.get(i);
            double temp_value = Double.parseDouble(tempData.get("value").toString());
            if(tempData.get("timezone").toString().equals("L"))
            {
                rangeObjMap.put("l_kwh", temp_value);
            }
            else if(tempData.get("timezone").toString().equals("M"))
            {
                rangeObjMap.put("m_kwh", temp_value);
            }
            else if(tempData.get("timezone").toString().equals("H"))
            {
                rangeObjMap.put("h_kwh", temp_value);
            }
        }

        for(int i=0; i<tempObjectSavingList.size(); i++)
        {
            HashMap<String, Object> tempData = tempObjectSavingList.get(i);
            if(tempData.get("range").equals("dayAgo"))
            {
                rangeObjMap.put("savingKwh",tempData.get("savingKwh").toString());
                rangeObjMap.put("savingCo2",tempData.get("savingCo2").toString());
            }
            if(tempData.get("range").equals("day"))
            {
                rangeObjMap.put("savingKwh",tempData.get("savingKwh").toString());
                rangeObjMap.put("savingCo2",tempData.get("savingCo2").toString());
            }
            if(tempData.get("range").equals("month"))
            {
                rangeObjMap.put("savingKwh",tempData.get("savingKwh").toString());
                rangeObjMap.put("savingCo2",tempData.get("savingCo2").toString());
            }
            if(tempData.get("range").equals("year"))
            {
                rangeObjMap.put("savingKwh",tempData.get("savingKwh").toString());
                rangeObjMap.put("savingCo2",tempData.get("savingCo2").toString());
            }
        }

        rangeObjMap.put("l_kwh_p",df.format(selectReport_kwh_p(rangeObjMap,"l_kwh")));
        rangeObjMap.put("m_kwh_p",df.format(selectReport_kwh_p(rangeObjMap,"m_kwh")));
        rangeObjMap.put("h_kwh_p",df.format(selectReport_kwh_p(rangeObjMap,"h_kwh")));
        return rangeObjMap;
    }
    /**
     * 전력 절감 리포트 조회
     * @param params 요청 필터 조건
     * @return 전력 절감 리포트 리스트
     */
    public List<HashMap<String, Object>> selectReport_saving(HashMap<String, Object> params) {
        return settingMapper.selectReport_saving(params);
    }

    /**
     * 보고서 타입 2 데이터 조회
     * @param params 요청 필터 조건
     * @return 보고서 데이터 리스트
     */
    public List<HashMap<String, Object>> selectReport2(HashMap<String, Object> params) {
        return settingMapper.selectReport2(params);
    }
    /**
     * 보고서 타입 3 데이터 조회
     * @param params 요청 필터 조건
     * @return 보고서 데이터 리스트
     */
    public List<HashMap<String, Object>> selectReport3(HashMap<String, Object> params) {
        return settingMapper.selectReport3(params);
    }
    /**
     * 보고서 타입 4 데이터 조회
     * @param params 요청 필터 조건
     * @return 보고서 데이터 리스트
     */
    public List<HashMap<String, Object>> selectReport4(HashMap<String, Object> params) {
        return settingMapper.selectReport4(params);
    }
    /**
     * 보고서 타입 5 데이터 조회
     * @param params 요청 필터 조건
     * @return 보고서 데이터 리스트
     */
    public List<HashMap<String, Object>> selectReport5(HashMap<String, Object> params) {
        return settingMapper.selectReport5(params);
    }
    /**
     * 보고서 타입 6 데이터 조회
     * @param params 요청 필터 조건
     * @return 보고서 데이터 리스트
     */
    public List<HashMap<String, Object>> selectReport6(HashMap<String, Object> params) {
        return settingMapper.selectReport6(params);
    }
    /**
     * 보고서 타입 7 데이터 조회
     * @param params 요청 필터 조건
     * @return 보고서 데이터 리스트
     */
    public List<HashMap<String, Object>> selectReport7(HashMap<String, Object> params) {
        return settingMapper.selectReport7(params);
    }
    /**
     * 피크 목표 정보 삽입
     * @param params 삽입할 피크 목표 정보
     */
    void insertPeakGoal(Map<String, Object> params) {
        alarmMapper.updateAlarmPrdctData(null);
        settingMapper.insertPeakGoal(params);
	}
    /**
     * 피크 목표 정보 조회
     * @return 피크 목표 정보 리스트
     */
    public List<HashMap<String, Object>> selectPeakGoal() {
		return settingMapper.selectPeakGoal();
	}

    /**
     * 월, 계절 목표 전력 데이터 조회
     * @return 월, 계절 목표 전력 데이터 리스트
     */
	public List<HashMap<String, Object>> selectMonthSeason() {
        return settingMapper.selectMonthSeason();
	}
    /**
     * 월, 계절 목표 전력 데이터설정
     * @param updateList 업데이트할 월, 계절 목표 전력 데이터 리스트
     */
    public void setMonthSeason(List<HashMap<String, Object>> updateList) {
        for(HashMap<String, Object> updateMap : updateList){
            settingMapper.setMonthSeason(updateMap);
            List<HashMap<String, Object>> targetSeasonLoad = settingMapper.selectSeasonLoad((String) updateMap.get("ssn"));
            for(HashMap<String, Object> map : targetSeasonLoad){
                map.put("month", updateMap.get("month"));
                settingMapper.setTargetMonthLoad(map);
            }
        }
    }
    /**
     * 계절별 요금 정보 조회
     * @param ssn 시즌 정보
     * @return 계절별 요금 정보
     */
    public HashMap<String, Object> selectRateSeason(String ssn) {
        HashMap<String, Object> returnMap = new HashMap<>();
        List<HashMap<String, Object>> rateList = settingMapper.selectRate(ssn);
        for(HashMap<String, Object> map:rateList){
            if (!returnMap.containsKey("BASE_RATE")){
                returnMap.put("BASE_RATE", map.get("BASE_RATE"));
            }
            returnMap.put((String) map.get("TIMEZONE"), map.get("ELCTR_RATE"));
        }
        returnMap.put("selectSeasonLoad", settingMapper.selectSeasonLoad(ssn));
        return returnMap;
    }
    /**
     * 계절 부하 설정
     * @param updateList 업데이트할 계절 부하 리스트
     */
    public void setSeasonLoad(List<HashMap<String, Object>> updateList) {
        for(HashMap<String, Object> map : updateList){
            settingMapper.setSeasonLoad(map);
        }
    }

    /**
     * 요금 설정
     * @param updateMap 요금 설정 데이터
     */
    public void setRateCost(HashMap<String, Object> updateMap) {
        HashMap<String, Object> updateMapTemp = new HashMap<>();
        updateMapTemp.putAll(updateMap);
        if(updateMapTemp.containsKey("ssn")) {
            updateMapTemp.remove("ssn");
        }
        //System.out.println("updateMap:"+updateMap.toString());
        //System.out.println("updateMapTemp:"+updateMapTemp.toString());
        for (Map.Entry<String, Object> entry : updateMapTemp.entrySet()) {
            Map<String, Object> entryMap = new HashMap<>();
            entryMap.put("key", entry.getKey());
            entryMap.put("value", entry.getValue());
            entryMap.put("ssn", updateMap.get("ssn").toString());
            //System.out.println("entryMap:"+entryMap.toString());
            settingMapper.setRateCost(entryMap);
        }
    }


	public Double getAvgOneDayRaw(Map<String, Object> param) {
        return settingMapper.getAvgOneDayRaw(param);
	}
}
