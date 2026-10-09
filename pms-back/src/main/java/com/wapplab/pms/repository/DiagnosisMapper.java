package com.wapplab.pms.repository;

import com.wapplab.pms.web.common.ChannelForm;
import com.wapplab.pms.web.common.RMSForm;
import com.wapplab.pms.web.common.RequestForm;
import com.wapplab.pms.web.common.SettingForm;
import org.apache.ibatis.annotations.Mapper;

import java.util.HashMap;
import java.util.List;

@Mapper
public interface DiagnosisMapper {

    List<Integer> selectPumpCount();
    List<HashMap<String, String>> selectPumpChannelList(int grp_idx);

    List<HashMap<String, Object>> selectRMSList(RMSForm rmsForm);
    List<HashMap<String, Object>> selectTimeWaveList(ChannelForm channelForm);
    List<HashMap<String, Object>> selectSpectrumList(ChannelForm channelForm);
    List<HashMap<String, Object>> selectSpectrumFreqList(ChannelForm channelForm);


    List<HashMap<String, Object>> selectSettingParmList(SettingForm settingForm);

    int updateSettingParm(HashMap<String, String> settingForm);

}
