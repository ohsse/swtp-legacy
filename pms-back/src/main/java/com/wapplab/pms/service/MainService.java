package com.wapplab.pms.service;

import com.wapplab.pms.repository.MainMapper;

import java.util.*;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MainService {
    private final MainMapper mainMapper;

    public List<List<Map<String, Object>>> motorDataAll() {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<List<Map<String, Object>>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){

            List<Map<String, Object>> list = mainMapper.motorDataAll((Integer) map.get("grp_idx"));
            if(list != null){
                returnList.add(list);
            }else {
                returnList.add(new ArrayList<>());
            }
        }
        //System.out.println("motorDataAll:"+returnList.toString());
        return returnList;
    }

    public List<Map<String, Object>> motorDataAllList() {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<Map<String, Object>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){

            List<Map<String, Object>> list = mainMapper.motorDataAll((Integer) map.get("grp_idx"));
            if(list != null){
                returnList.addAll(list);
            }
        }
        //System.out.println("motorDataAllList:"+returnList.toString());
        return returnList;
    }



    public List<List<Map<String, Object>>> pumpBearingTempAll() {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<List<Map<String, Object>>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){

            //List<Map<String, Object>> list = mainMapper.pumpBearingScadaTempAll((Integer) map.get("grp_idx"));
            List<Map<String, Object>> list = mainMapper.pumpBearingTempAll((Integer) map.get("grp_idx"));
            if(list != null){
                returnList.add(list);
            }else {
                returnList.add(new ArrayList<>());
            }
        }
        return returnList;
    }

    public List<List<Map<String, Object>>> motorAlarm() {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<List<Map<String, Object>>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){
            List<Map<String, Object>> list = mainMapper.motorAlarm((Integer) map.get("grp_idx"));
            // list가 List<Map<String, Object>> 타입이고, 이 리스트를 순회하기 위한 for문
            // list가 List<Map<String, Object>> 타입이고, 이 리스트를 순회하기 위한 for문
            for (Map<String, Object> item : list) {
                // map에서 키 세트를 가져와서 그 키들을 순회하는 for문
                for (String key : item.keySet()) {
                    // 현재 키에 해당하는 값을 가져옴
                    Object value = item.get(key);

                    // 값이 문자열인지 확인
                    if (value instanceof String) {
                        String stringValue = (String) value;
                        // 문자열이 "True" 또는 "False"인지 확인
                        if ("True".equalsIgnoreCase(stringValue) || "False".equalsIgnoreCase(stringValue)) {
                            // 문자열을 Boolean으로 파싱하고 결과 출력
                            Boolean booleanValue = Boolean.parseBoolean(stringValue);
                            //System.out.println("Key: " + key + ", Value (converted to Boolean): " + booleanValue);
                            item.put(key, booleanValue);
                        }
                    }
                }
            }
            if(list != null){
                returnList.add(list);
            }else {
                returnList.add(new ArrayList<>());
            }
        }

        return returnList;
    }

    public List<Map<String, Object>> motorAlarmList() {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<Map<String, Object>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){
            List<Map<String, Object>> list = mainMapper.motorAlarm((Integer) map.get("grp_idx"));
            if(list != null) {
                returnList.addAll(list);
            }
        }
        return returnList;
    }

    public List<Map<String, Object>> getPumpInf() { return mainMapper.getPumpInf();}

    public List<Map<String, Object>> getPumpInfAllList() { return mainMapper.getPumpInfAllList();}

    public Map<String, Object> getAllFacStats() {
        //return mainMapper.getAllFacStats();
        Map<String, Object> result = new HashMap<>();
        Map<String, Object> motor = mainMapper.getAllFacStatsMotor();
        Map<String, Object> pump = mainMapper.getAllFacStatsPump();
        Map<String, Object> sensor = mainMapper.getAllFacStats();

        result.put("sensor_count", Integer.parseInt(sensor.get("SENSOR_COUNT").toString()));
        result.put("total_sum", Integer.parseInt(motor.get("total_alarm_sum").toString())
        +Integer.parseInt(pump.get("total_alarm_sum").toString()));
        return result;
    }
}
