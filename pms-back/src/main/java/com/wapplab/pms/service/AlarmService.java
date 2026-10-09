package com.wapplab.pms.service;

import com.wapplab.pms.repository.AlarmMapper;
import com.wapplab.pms.web.common.DateForm;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AlarmService {
	@Autowired
	AlarmMapper alarmMapper;


	public HashMap<String, Object> alarmStatusDefect(HashMap<String, Object> map) {
		return alarmMapper.alarmStatusDefect(map);
	}

	public List<HashMap<String, Object>> weeklyAlarmTrend(HashMap<String, Object> map) {
		return alarmMapper.weeklyAlarmTrend(map);
	}

	public List<HashMap<String, Object>> alarmList(HashMap<String, String> map) {
		return alarmMapper.alarmList(map);
	}
}
