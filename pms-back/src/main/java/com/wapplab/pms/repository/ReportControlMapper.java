package com.wapplab.pms.repository;

import com.wapplab.pms.web.common.DateForm;
import com.wapplab.pms.web.common.PumpForm;
import com.wapplab.pms.web.common.RequestForm;
import org.apache.ibatis.annotations.Mapper;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Mapper
public interface ReportControlMapper {

    List<HashMap<String, Object>> alarmCount(String dateType);
    List<Map<String, Object>> alarmList(DateForm dateForm);
}
