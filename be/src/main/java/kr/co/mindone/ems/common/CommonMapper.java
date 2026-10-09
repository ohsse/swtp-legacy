package kr.co.mindone.ems.common;
/**
 * packageName    : kr.co.mindone.common
 * fileName       : CommonMapper
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import org.apache.ibatis.annotations.Mapper;

import java.util.HashMap;
import java.util.List;

@Mapper
interface CommonMapper {
    /**
     * WPP 태그 목록 조회
     * @param map 조회할 파라미터
     * @return 태그 목록 데이터
     */
    List<HashMap<String, Object>> selectWppTagList(HashMap<String, Object> map);

    /**
     * 태그 정보 조회
     * @param map 조회할 파라미터
     * @return 태그 정보 데이터
     */
    List<HashMap<String, Object>> selectTagInfo(HashMap<String, Object> map);

    /**
     * WPP 태그 코드 목록 조회
     * @param func_typ 기능 타입
     * @return 태그 코드 목록
     */
    List<HashMap<String, Object>> selectWppTagCodeList(String func_typ);

    /**
     * 전력 값의 범위 조회
     * @param elecParam 전력 값에 대한 파라미터
     * @return 범위 내의 전력 값 데이터
     */
    HashMap<String, Object> selectRangeElecValue(HashMap<String, Object> elecParam);

    HashMap<String, Object> selectRangeElecPwiValue(HashMap<String, Object> elecParam);


    /**
     * 전일 주파수 값 조회
     * @param elecParam 조회할 전기 값 파라미터
     * @return 전일 주파수 값 데이터
     */
    HashMap<String, Object> selectAfterDayFRQ(HashMap<String, Object> elecParam);

    /**
     * 펌프 그룹 목록 조회
     * @return 펌프 그룹 목록 데이터
     */
    List<HashMap<String, Object>> selectPumpGroupItem();

    /**
     * Raw 데이터 삽입
     * @param params 삽입할 데이터 파라미터
     */
    void insertRawData(HashMap<String, Object> params);

    /**
     * w전력 절감 목표 데이터 삽입
     * @param params 삽입할 데이터 파라미터
     */
    void insertBaseSavingsTarget(HashMap<String, Object> params);

    /**
     * 절감 목표 결과 데이터 삽입
     * @param params 삽입할 데이터 파라미터
     */
    void insertRstSavingsTarget(HashMap<String, Object> params);

    /**
     * 한 시간 전 목록 조회
     * @param map 조회할 파라미터
     * @return 한 시간 전 데이터 목록
     */
    List<HashMap<String, Object>> oneHourBeforeList(HashMap<String, Object> map);

    /**
     * EMS Kafka Consumer 태그 목록 조회
     * @return EMS Kafka Consumer 태그 목록
     */
	List<HashMap<String, Object>> selectEMSConsumerTag();

    /**
     * 펌프 비상정지 상태 업데이트
     * @param map 업데이트할 데이터 파라미터
     */
    void updateEmergencyStatus(HashMap<String, Object> map);

    /**
     * WPP EMS 태그 목록 조회
     * @return WPP EMS 태그 목록
     */
	List<HashMap<String, Object>> selectWppEMSTag();

    /**
     * WPP 태그 코드 목록 조회 (유사한 이름으로 조회)
     * @param funcType 기능 타입
     * @return 태그 코드 목록
     */
	List<HashMap<String, Object>> selectWppTagCodeLikeList(String funcType);

    /**
     * 테스트 API 조회
     * @param func_typ 기능 타입
     * @return 테스트 API 결과 데이터
     */
    HashMap<String, Object> selectTestApi(String func_typ);

    /**
     * Raw 데이터 삭제
     * @param nowDateTime 삭제할 데이터의 시간
     */
	void deleteRawData(String nowDateTime);

    void deleteEpanetFP(String nowDateTime);
    void deleteEpanetFR(String nowDateTime);


    /**
     * 펌프 타입 업데이트
     * @param map 업데이트할 데이터 파라미터
     */
    void updatePumpType(HashMap<String, Object> map);

    /**
     * 펌프 동기화 체크 업데이트
     * @param map 업데이트할 데이터 파라미터
     */
    void updatePumpSyncCheck(HashMap<String, Object> map);

    /**
     * 일일 목표 전력 조회
     * @param map 조회할 파라미터
     * @return 일일 목표 전력 데이터
     */
    HashMap<String, Object> selectDayGoal(HashMap<String, Object> map);

    /**
     * AI 상태 모든 그룹 조회
     * @return AI 상태 모든 그룹 데이터
     */
    List<HashMap<String, Object>> selectAiStatusAllgrp();

    /**
     * AI 상태 결과 데이터 삽입
     * @param map 삽입할 데이터 파라미터
     */
    void insertAiStatusRST(HashMap<String, String> map);

	String getLastRawDate(String nowDate);
}
