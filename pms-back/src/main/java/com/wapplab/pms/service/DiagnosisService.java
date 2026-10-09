package com.wapplab.pms.service;

import com.google.gson.Gson;
import com.wapplab.pms.repository.DiagnosisMapper;
import com.wapplab.pms.repository.MainMapper;
import com.wapplab.pms.web.common.ChannelForm;
import com.wapplab.pms.web.common.RMSForm;
import com.wapplab.pms.web.common.RequestForm;
import com.wapplab.pms.web.common.SettingForm;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.google.gson.reflect.TypeToken;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.text.DecimalFormat;
import java.util.zip.GZIPInputStream;
import java.nio.charset.StandardCharsets;


import java.io.IOException;
import java.lang.reflect.Type;

import java.util.*;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DiagnosisService {

    private final DiagnosisMapper diagnosisMapper;

    private static final Gson gson = new Gson(); // 클래스 레벨의 Gson 인스턴스
    private static final Type DATA_ARRAY_TYPE = new TypeToken<List<Map<String, Object>>>(){}.getType(); // 타입 객체 재사용

    public List<List<HashMap<String, String>>> selectPumpChannelList() {
        List<Integer> pumpGrpList = diagnosisMapper.selectPumpCount();
        List<List<HashMap<String, String>>> returnList = new ArrayList<>();
        for(int grp_idx : pumpGrpList){

            List<HashMap<String, String>> list = diagnosisMapper.selectPumpChannelList(grp_idx);
            if(list != null){
                returnList.add(list);
            }else {
                returnList.add(new ArrayList<>());
            }
        }
        return returnList;
    }


    public List<HashMap<String, Object>> selectRMSList(RMSForm rmsForm) {
        return diagnosisMapper.selectRMSList(rmsForm);
    }

    public List<HashMap<String, Object>> selectTimeWaveList(ChannelForm channelForm) {
        List<HashMap<String, Object>> dataList = diagnosisMapper.selectTimeWaveList(channelForm);
        List<HashMap<String, Object>> result = new ArrayList<>();

        for (HashMap<String, Object> item : dataList) {
            result.add(convertItem(item, "TimeWave"));
        }
        return result;
    }


    public List<HashMap<String, Object>> selectSpectrumList(ChannelForm channelForm) {
        List<HashMap<String, Object>> dataList = diagnosisMapper.selectSpectrumList(channelForm);
        List<HashMap<String, Object>> result = new ArrayList<>();

        for (HashMap<String, Object> item : dataList) {
            result.add(convertItem(item, "spectrum"));
        }
        return result;
    }

    public List<HashMap<String, Object>> selectSpectrumFreqList(ChannelForm channelForm) {
        return diagnosisMapper.selectSpectrumFreqList(channelForm);
    }

    public List<HashMap<String, Object>> selectSettingParmList(SettingForm settingForm) {
            return diagnosisMapper.selectSettingParmList(settingForm);
    }

    public int updateSettingParm(List<HashMap<String, String>> settingForms){
        int result = 0;
        for(HashMap<String, String> item: settingForms)
        {
            result = diagnosisMapper.updateSettingParm(item);
            if(result != 1)
            {
                return 2;
            }
        }
        return result;
    }


    public HashMap<String, Object> convertItem(HashMap<String, Object> item, String type) {
        HashMap<String, Object> returnItem = new HashMap<>();
        returnItem.put("MOTOR_ID", item.get("MOTOR_ID").toString());
        returnItem.put("CHANNEL_ID", item.get("CHANNEL_ID").toString());
        returnItem.put("ACQ_DATE", item.get("ACQ_DATE").toString());

        ArrayList<Double> list = decompressList((String) item.get("DATA_ARRAY"));
        
        // JSON 리스트 생성
        ArrayList<Map<String, Object>> jsonList = new ArrayList<>();
        double x = 0.0; // 초기 x값
        double step = type.equals("TimeWave") ? 1.0 : 0.5; // x값 증가량 조정
        for (int i = 0; i < list.size(); i++) {
            double y = list.get(i); // 리스트의 값으로 y값 설정

            // JSON 객체 생성
            Map<String, Object> jsonItem = new HashMap<>();
            if(type.equals("TimeWave"))
            {
                jsonItem.put("x", String.format("%.0f", x)); // x값을 소수점 10자리까지 형식화하여 저장
            }
            else{
                jsonItem.put("x", String.format("%.1f", x)); // x값을 소수점 10자리까지 형식화하여 저장
            }
            jsonItem.put("y", String.format("%.10f", y)); // y값을 소수점 10자리까지 형식화하여 저장

            // JSON 리스트에 추가
            jsonList.add(jsonItem);

            x += step;
        }
        returnItem.put("DATA_ARRAY", jsonList); // 변환된 리스트 저장
        return returnItem;
    }

    public static List<Map<String, Object>> decompress(String base64Data)  {
        try {
            // Base64 디코딩
           byte[] compressedData = Base64.getDecoder().decode(base64Data);

           // GZIP 압축 해제
           ByteArrayInputStream bis = new ByteArrayInputStream(compressedData);
           GZIPInputStream gis = new GZIPInputStream(bis);
           byte[] decompressedData = gis.readAllBytes();

           // UTF-16 디코딩 및 JSON 파싱
           String jsonText = new String(decompressedData, StandardCharsets.UTF_16);

           // 정의된 타입으로 JSON 파싱
           Type dataType = new TypeToken<List<Map<String, Object>>>(){}.getType();

            return gson.fromJson(jsonText, dataType);
        }catch (Exception e)
        {
            e.printStackTrace();
            return null;
        }
   }

    public static ArrayList<Double> decompressList(String base64Data) {
        try {
            // Base64 디코딩
            byte[] compressedData = Base64.getDecoder().decode(base64Data);

            // GZIP 압축 해제
            ByteArrayInputStream bis = new ByteArrayInputStream(compressedData);
            GZIPInputStream gis = new GZIPInputStream(bis);
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            byte[] buffer = new byte[1024];
            int len;
            while ((len = gis.read(buffer)) != -1) {
                bos.write(buffer, 0, len);
            }
            gis.close();
            bos.close();
            byte[] decompressedData = bos.toByteArray();

            // UTF-16 디코딩
            String utf16Data = new String(decompressedData, StandardCharsets.UTF_16);
            String[] stringArray = utf16Data.split("\n");
            ArrayList<Double> doubleList = new ArrayList<>();
            for (String str : stringArray) {
                doubleList.add(Double.parseDouble(str));
            }
            return doubleList;
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
}
