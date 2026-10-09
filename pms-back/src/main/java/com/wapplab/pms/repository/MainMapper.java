package com.wapplab.pms.repository;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MainMapper {

    List<Map<String, Object>> motorDataAll(int grp_idx);

    List<Map<String, Object>> pumpBearingTempAll(int grp_idx);

    List<Map<String, Object>> pumpBearingScadaTempAll(int grp_idx);


    List<Map<String, Object>> motorAlarm(int grp_idx);

	List<Map<String, Object>> getPumpInf();
    List<Map<String, Object>> getPumpInfAllList();

    Map<String, Object> getAllFacStats();

    Map<String, Object> getAllFacStatsMotor();
    Map<String, Object> getAllFacStatsPump();



}
