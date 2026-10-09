package kr.co.mindone.ems.pump;

import org.apache.ibatis.annotations.Mapper;

import java.util.HashMap;
import java.util.List;

/**
 * 군산 5분 제어 판단(TB_CTRL_CMD_RST) → 제어명령 대기열 연계 매퍼.
 * SQL: sqlmapper/mysql/ctrl_cmd_mssql.xml
 */
@Mapper
interface CtrlCmdMapper {

    List<HashMap<String, Object>> selectReadyCmdList(HashMap<String, Object> map);

    HashMap<String, Object> selectCmdForUpdate(HashMap<String, Object> map);

    HashMap<String, Object> selectCmd(HashMap<String, Object> map);

    HashMap<String, Object> selectLatestCmd();

    int countNewerDeviceCmd(HashMap<String, Object> map);

    int updateDeviceStatus(HashMap<String, Object> map);

    List<HashMap<String, Object>> selectCmdHistory(HashMap<String, Object> map);

    List<HashMap<String, Object>> selectQueueByOptIdx(HashMap<String, Object> map);

    List<HashMap<String, Object>> selectQueueByCtrlId(HashMap<String, Object> map);

    int countForeignActiveQueue(HashMap<String, Object> map);

    int discardQueueRows(HashMap<String, Object> map);

    List<HashMap<String, Object>> selectPumpMaster(HashMap<String, Object> map);

    HashMap<String, Object> selectLatestRaw(HashMap<String, Object> map);

    List<HashMap<String, Object>> selectCtrlCmdTagConfig();

    void insertTrace(HashMap<String, Object> map);

    List<HashMap<String, Object>> selectTraceByCtrlIds(HashMap<String, Object> map);
}
