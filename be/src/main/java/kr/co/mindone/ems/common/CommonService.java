package kr.co.mindone.ems.common;
/**
 * packageName    : kr.co.mindone.common
 * fileName       : CommonService
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import io.swagger.models.auth.In;
import net.bytebuddy.description.method.MethodDescription;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class CommonService {
	@Autowired
	private CommonMapper commonMapper;

	/**
	 * WPP 태그 목록 조회
	 * @param map 태그 조회를 위한 파라미터
	 * @return WPP 태그 목록
	 */
	public List<HashMap<String, Object>> selectWppTagList(HashMap<String, Object> map) { return commonMapper.selectWppTagList(map); }

	/**
	 * 태그 정보 조회
	 * @param map 태그 정보를 조회할 파라미터
	 * @return 태그 정보 목록
	 */
	public List<HashMap<String, Object>> selectTagInfo(HashMap<String, Object> map) { return commonMapper.selectTagInfo(map); }

	/**
	 * WPP 태그 코드 목록 조회
	 * @param func_typ 기능 타입
	 * @return WPP 태그 코드 목록
	 */
	public List<HashMap<String, Object>> selectWppTagCodeList(String func_typ) { return commonMapper.selectWppTagCodeList(func_typ); }

	/**
	 * 전력값 범위 조회
	 * @param elecParam 전력 파라미터
	 * @return 전력값 범위
	 */
	public HashMap<String, Object> selectRangeElecValue(HashMap<String, Object> elecParam) { return commonMapper.selectRangeElecValue(elecParam); }

	public HashMap<String, Object> selectRangeElecPwiValue(HashMap<String, Object> elecParam) { return commonMapper.selectRangeElecPwiValue(elecParam); }

	/**
	 * 전일 주파수 값 조회
	 * @param elecParam 전력 파라미터
	 * @return 주파수 값
	 */
	HashMap<String, Object> selectAfterDayFRQ(HashMap<String, Object> elecParam) { return commonMapper.selectAfterDayFRQ(elecParam); }

	/**
	 * Kafka Raw 데이터 삽입
	 * @param params 데이터 파라미터
	 */
	public void insertRawData(HashMap<String, Object> params) { commonMapper.insertRawData(params); }

	/**
	 * 절감 목표 데이터 삽입
	 * @param params 절감 목표 데이터
	 */
	public void insertBaseSavingsTarget(HashMap<String, Object> params) { commonMapper.insertBaseSavingsTarget(params); }

	/**
	 * 절감 결과 목표 데이터 삽입
	 * @param params 절감 목표 결과 데이터
	 */
	public void insertRstSavingsTarget(HashMap<String, Object> params) { commonMapper.insertRstSavingsTarget(params); }

	/**
	 * 펌프 그룹 목록 조회
	 * @return 펌프 그룹 목록
	 */
	public List<HashMap<String, Object>> selectPumpGroupItem()
	{
		return commonMapper.selectPumpGroupItem();
	}

	/**
	 * 1시간 전 데이터 목록 조회
	 * @param map 조회할 파라미터
	 * @return 1시간 전 데이터 목록
	 */
	public List<HashMap<String, Object>> oneHourBeforeList(HashMap<String, Object> map) { return commonMapper.oneHourBeforeList(map); }

	/**
	 * JSON 포맷의 Kafka Value 생성
	 * @param item 전송 데이터
	 * @return JSON 문자열
	 */
	public String makeProducerJsonValue(HashMap<String, Object> item)
	{
		StringBuffer sb = new StringBuffer();
		if(item.get("value") != null && item.get("tag") != null && item.get("time")!= null)
		{
			sb.append("{");
			sb.append("\"tag\":").append("\"").append(item.get("tag").toString()).append("\"").append(",");
			sb.append("\"value\":").append(item.get("value").toString()).append(",");
			sb.append("\"time\":").append("\"").append(item.get("time").toString()).append("\"");
			sb.append("}");
		}
		else {
			sb.append("None");
		}
		return sb.toString();
	}

	/**
	 * JSON String 포맷의 Kafka Value 생성
	 * @param item 전송 데이터
	 * @return JSON String 문자열
	 */
	public String makeProducerJsonStringValue(HashMap<String, Object> item)
	{
		StringBuffer sb = new StringBuffer();
		if(item.get("value") != null && item.get("tag") != null && item.get("time")!= null) {
			sb.append("{");
			sb.append("\"tag\":").append("\"").append(item.get("tag").toString()).append("\"").append(",");
			sb.append("\"value\":").append("\"").append(item.get("value").toString()).append("\"").append(",");
			sb.append("\"time\":").append("\"").append(item.get("time").toString()).append("\"");
			sb.append("}");
		}
		else {
			sb.append("None");
		}
		return sb.toString();
	}

	/**
	 * Kafka 사용 EMS Consumer 태그 조회
	 * @return Consumer 태그 목록
	 */
	public List<HashMap<String, Object>> selectEMSConsumerTag(){
		return commonMapper.selectEMSConsumerTag();
	}

	/**
	 * 비상 정지 태그 Value 업데이트
	 * @param map 비상 정지 태그 Value
	 */
	public void updateEmergencyStatus(HashMap<String, Object> map){
		commonMapper.updateEmergencyStatus(map);
	}

	/**
	 * WPP테이블 EMS 태그 조회
	 * @return WPP테이블 EMS 태그 목록
	 */
	public List<HashMap<String, Object>> selectWppEMSTag() {
		return commonMapper.selectWppEMSTag();
	}

	/**
	 * WPP 태그 코드 목록 조회
	 * @param func_type 기능 타입
	 * @return 태그 코드 목록
	 */
	public List<HashMap<String, Object>> selectWppTagCodeLikeList(String func_type){
		return commonMapper.selectWppTagCodeLikeList(func_type);
	}

	/**
	 * 테스트 API 데이터 조회
	 * @param func_typ 기능 타입
	 * @return 테스트 API 데이터
	 */
	public HashMap<String, Object> selectTestApi (String func_typ)
	{
		return commonMapper.selectTestApi(func_typ);
	}

	/**
	 * 펌프 타입 업데이트
	 * @param map 펌프 데이터 파라미터
	 */
	public void updatePumpType(HashMap<String, Object> map){

		if(map.get("type").equals(2))
		{
			map.put("pwi","565-340-PWI-4000R");
		}
		else {
			switch (Integer.parseInt(map.get("pump_idx").toString()))
			{
				case 1:
					map.put("pwi","565-340-PWI-4101");
					break;
				case 2:
					map.put("pwi","565-340-PWI-4201");
					break;
				case 3:
					map.put("pwi","565-340-PWI-4301");
					break;
				case 4:
					map.put("pwi","565-340-PWI-4501");
					break;
				default:
					break;
			}
		}
		commonMapper.updatePumpType(map);
	}

	/**
	 * Raw 데이터 삭제
	 * @param nowDateTime 시간 데이터
	 */
	public void deleteRawData(String nowDateTime) {
		commonMapper.deleteRawData(nowDateTime);
	}

	public void deleteEpanetFP(String nowDateTime) {
		commonMapper.deleteEpanetFP(nowDateTime);
	}

	public void deleteEpanetFR(String nowDateTime) {
		commonMapper.deleteEpanetFR(nowDateTime);
	}

	/**
	 * 펌프 동기화 상태 업데이트
	 * @param map 동기화 체크 파라미터
	 */
	public void updatePumpSyncCheck(HashMap<String, Object> map){
		commonMapper.updatePumpSyncCheck(map);
	}

	/**
	 * 일간 목표 전력 데이터 조회
	 * @param map 조회 파라미터
	 * @return 일간 목표 전력 데이터
	 */
	public HashMap<String, Object> selectDayGoal (HashMap<String, Object> map)
	{
		return commonMapper.selectDayGoal(map);
	}

	/**
	 * 모든 그룹의 AI 상태 조회
	 * @return AI 상태 목록
	 */
	public List<HashMap<String, Object>> selectAiStatusAllgrp(){
		return commonMapper.selectAiStatusAllgrp();
	}

	/**
	 * AI 상태 결과 삽입
	 * @param map AI 상태 파라미터
	 */
	public void insertAiStatusRST(HashMap<String, String> map)
	{
		commonMapper.insertAiStatusRST(map);
	}

	public String getLastRawDate(String nowDate) {
		return commonMapper.getLastRawDate(nowDate);
	}
}
