package com.wapplab.pms.repository;

import com.wapplab.pms.web.common.DateForm;
import org.apache.ibatis.annotations.Mapper;

import java.util.HashMap;
import java.util.List;

@Mapper
public interface AlarmMapper {

	HashMap<String, Object> alarmStatusDefect(HashMap<String, Object> map);

	List<HashMap<String, Object>> weeklyAlarmTrend(HashMap<String, Object> map);

	List<HashMap<String, Object>> alarmList(HashMap<String, String> map);
}
