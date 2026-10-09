package com.wapplab.pms.service;

import com.wapplab.pms.repository.MainMapper;
import com.wapplab.pms.repository.MotorMapper;
import com.wapplab.pms.web.common.DateForm;
import com.wapplab.pms.web.common.PumpForm;
import com.wapplab.pms.web.common.RequestForm;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import netscape.javascript.JSObject;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import springfox.documentation.spring.web.json.Json;

@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class MotorService {

    private final MotorMapper motorMapper;
    private final MainMapper mainMapper;

    public List<List<Map<String, Object>>> alarm(RequestForm requestForm) {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<List<Map<String, Object>>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){
            List<Map<String, Object>> list = motorMapper.alarm(requestForm);
            List<Map<String, Object>> listTemp = motorMapper.alarmTemp((Integer) map.get("grp_idx"));
            //System.out.println("CK 1");
            for (Map<String, Object> item : list) {
                // map에서 키 세트를 가져와서 그 키들을 순회하는 for문
                for (String key : item.keySet()) {
                    // 현재 키에 해당하는 값을 가져옴
                    if(item.get(key) != null)
                    {
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
            }
            for(Map<String, Object> listItem : list)
            {
                //System.out.println("listItem:"+listItem.toString());
                for(Map<String, Object> listTempItem : listTemp)
                {
                    if(listItem.get("motor_id").toString().equals(listTempItem.get("motor_id").toString()))
                    {
                        if(Boolean.parseBoolean(listItem.get("Alarm").toString()) || Boolean.parseBoolean(listTempItem.get("Alarm").toString()))
                        {
                            listItem.put("Alarm", true);
                        }
                        else {
                            listItem.put("Alarm", false);
                        }
                        System.out.println("listTempItem:"+listTempItem.toString());
                        listItem.put("winding_temp_t_alarm", listTempItem.get("winding_temp_t_alarm"));
                        listItem.put("winding_temp_r_alarm", listTempItem.get("winding_temp_r_alarm"));
                        listItem.put("winding_temp_s_alarm", listTempItem.get("winding_temp_s_alarm"));
                        listItem.put("p_de_bearing_temp_alarm", listTempItem.get("p_de_bearing_temp_alarm"));
                        listItem.put("m_de_bearing_temp_alarm", listTempItem.get("m_de_bearing_temp_alarm"));
                        listItem.put("m_nde_bearing_temp_alarm", listTempItem.get("m_nde_bearing_temp_alarm"));
                    }
                }
            }
            if(!list.isEmpty()) {
                returnList.add(list);
            }
            else {
                returnList.add(new ArrayList<>());
            }
        }
        return returnList;
    }

    public List<List<Map<String, Object>>> alarmTemp() {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<List<Map<String, Object>>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){
            List<Map<String, Object>> list = motorMapper.alarmTemp((Integer) map.get("grp_idx"));
            if(list != null){
                returnList.add(list);
            }else {
                returnList.add(new ArrayList<>());
            }
        }
        return returnList;
    }

    public List<List<Map<String, Object>>> runningInfo() {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<List<Map<String, Object>>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){
            List<Map<String, Object>> list = motorMapper.runningInfo((Integer) map.get("grp_idx"));
            if(list != null){
                returnList.add(list);
            }else {
                returnList.add(new ArrayList<>());
            }
        }
        return returnList;
    }

    public List<List<Map<String, Object>>> distribution(DateForm dateForm) {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<List<Map<String, Object>>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){
            PumpForm pumpForm = new PumpForm();
            pumpForm.setId(map.get("pump_scada_id"));
            pumpForm.setStartDate(dateForm.getStartDate());
            pumpForm.setEndDate(dateForm.getEndDate());
            List<Map<String, Object>> list = motorMapper.distribution(pumpForm);
            if(list != null){
                returnList.add(list);
            }else {
                returnList.add(new ArrayList<>());
            }
        }
        return returnList;
    }

    public List<List<Map<String, Object>>> vibrationGraph(DateForm dateForm) {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<List<Map<String, Object>>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){
            PumpForm pumpForm = new PumpForm();
            pumpForm.setId(map.get("grp_idx"));
            pumpForm.setStartDate(dateForm.getStartDate());
            pumpForm.setEndDate(dateForm.getEndDate());
            List<Map<String, Object>> list = motorMapper.vibrationGraph(pumpForm);
            if(list != null){
                returnList.add(list);
            }else {
                returnList.add(new ArrayList<>());
            }
        }
        //System.out.println("vibrationGraph dateForm:"+dateForm.toString());
        //System.out.println("vibrationGraph:"+returnList.toString());
        return returnList;
    }

    public  List<Map<String, Object>> flowPressure() {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<Map<String, Object>> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){
            Map<String, Object> flowMap = motorMapper.flowPressure((String) map.get("pump_scada_id"));
            if(flowMap != null){
                flowMap.put("grp_nm", map.get("grp_nm"));
                returnList.add(flowMap);
            }else {
                Map<String, Object> dumyMap = new HashMap<>();
                dumyMap.put("grp_nm", map.get("grp_nm"));
                returnList.add(dumyMap);
            }
        }
        return returnList;
    }

    public List<Map<String, Object>> motorDetails(RequestForm requestForm) {
        return motorMapper.motorDetails(requestForm);
    }

    public List<Map<String, Object>> bearingTempInfo(RequestForm requestForm) {
        return motorMapper.bearingTempScadaInfo(requestForm);
        //return motorMapper.bearingTempInfo(requestForm);
    }

    public List<Map<String, Object>> windingTempInfo(RequestForm requestForm) {
        return motorMapper.windingScadaTempInfo(requestForm);
        //return motorMapper.windingTempInfo(requestForm);
    }

    public List<Map<String, Object>> selectGraphThreshold() {
        return motorMapper.selectGraphThreshold();
    }

    public List<String> dstrbChart() {
        List<Map<String, Object>> pumpInf = mainMapper.getPumpInf();
        List<String> returnList = new ArrayList<>();
        for(Map<String, Object> map : pumpInf){
            String jsonData = motorMapper.dstrbChart((String) map.get("pump_scada_id"));
            if(jsonData != null){
                returnList.add(jsonData);
            }else {
                returnList.add("null");
            }
        }
        return returnList;
    }

    public Map<String, Object> selectPumpDstrb(String pump_id) {
           List<Map<String, Object>> dataList = motorMapper.selectPumpDstrb(pump_id);
           String lastDstrbName = "none";
           Map<String, Object> result = new HashMap<>();
           StringBuffer sb = new StringBuffer();
           sb.append("[");
           for(Map<String, Object> item : dataList)
           {
               String nowDstrbName = item.get("dstrb_name").toString();
               double nowDstrbValue = Double.parseDouble(item.get("dstrb_value").toString());

               if(lastDstrbName.equals("none"))
               {
                   lastDstrbName = nowDstrbName;
                   sb.append(nowDstrbValue).append(",");
               }
               else if(!lastDstrbName.equals(nowDstrbName)){
                   sb.append(nowDstrbValue).append("]");
                   result.put(lastDstrbName,sb.toString());
                   sb.setLength(0);
                   lastDstrbName = nowDstrbName;
                   sb.append("[");
               }
               else {
                   sb.append(nowDstrbValue).append(",");
               }
           }
           return result;
       }
}
