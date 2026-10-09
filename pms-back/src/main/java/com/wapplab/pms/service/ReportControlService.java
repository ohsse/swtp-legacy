package com.wapplab.pms.service;

import com.wapplab.pms.repository.ReportControlMapper;
import com.wapplab.pms.web.common.DateForm;
import com.wapplab.pms.web.common.PumpForm;
import com.wapplab.pms.web.common.RequestForm;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ReportControlService {

    private final ReportControlMapper reportControlMapper;

    public List<HashMap<String, Object>> alarmCount(String dateType) {
        return reportControlMapper.alarmCount(dateType);
    }

    public List<Map<String, Object>> alarmList(DateForm dateForm) {
        return  reportControlMapper.alarmList(dateForm);
    }
}
