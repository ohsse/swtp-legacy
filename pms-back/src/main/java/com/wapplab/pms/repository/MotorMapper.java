package com.wapplab.pms.repository;

import com.wapplab.pms.web.common.DateForm;
import com.wapplab.pms.web.common.PumpForm;
import com.wapplab.pms.web.common.RequestForm;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.ibatis.annotations.Mapper;
import springfox.documentation.spring.web.json.Json;

@Mapper
public interface MotorMapper {

    List<Map<String, Object>> alarm(RequestForm requestForm);
    List<Map<String, Object>> alarmTemp(int grp_idx);
    List<Map<String, Object>> runningInfo(int grp_idx);
    List<Map<String, Object>> distribution(PumpForm pumpForm);
    List<Map<String, Object>> vibrationGraph(PumpForm requestForm);
    Map<String, Object> flowPressure(String id);
    List<Map<String, Object>> motorDetails(RequestForm requestForm);
    List<Map<String, Object>> bearingTempInfo(RequestForm requestForm);
    List<Map<String, Object>> windingTempInfo(RequestForm requestForm);

    String dstrbChart(String pump_scada_id);

    List<Map<String, Object>> selectPumpDstrb(String pump_id);
    List<Map<String, Object>> selectGraphThreshold();


    List<Map<String, Object>> windingScadaTempInfo(RequestForm requestForm);
    List<Map<String, Object>> bearingTempScadaInfo(RequestForm requestForm);

}
