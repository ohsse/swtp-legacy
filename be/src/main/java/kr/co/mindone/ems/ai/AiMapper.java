package kr.co.mindone.ems.ai;
/**
 * packageName    : kr.co.mindone.ems.ai
 * fileName       : AiMapper
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
import java.util.Map;

@Mapper
public interface AiMapper {

	/**
	 * 펌프 상태 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 상태 리스트
	 */
	List<HashMap<String, Object>> pumpSelect(HashMap<String, Object> map);

	/**
	 * 펌프 가동 여부 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 가동 여부 리스트
	 */
	List<HashMap<String, Object>> pumpSelectYn(HashMap<String, Object> map);

	/**
	 * 펌프 그룹 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 그룹 리스트
	 */
	List<HashMap<String, Object>> pumpGrpSelect(HashMap<String, Object> map);

	/**
	 * 새로운 방식으로 펌프 상태 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 상태 리스트
	 */
	List<HashMap<String, Object>> pumpSelect_new(HashMap<String, Object> map);

	/**
	 * 첫 번째 펌프 리스트를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 첫 번째 펌프 리스트
	 */
	List<HashMap<String, Object>> pumpSelectList_1(HashMap<String, Object> map);

	/**
	 * 두 번째 펌프 리스트를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 두 번째 펌프 리스트
	 */
	List<HashMap<String, Object>> pumpSelectList_2(HashMap<String, Object> map);

	/**
	 * 세 번째 펌프 리스트를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 세 번째 펌프 리스트
	 */
	List<HashMap<String, Object>> pumpSelectList_3(HashMap<String, Object> map);

	/**
	 * 배수지 태그 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 배수지 태그 리스트
	 */
	List<HashMap<String, Object>> selectTnkTagValueList(HashMap<String, Object> map);

	/**
	 * 펌프 태그 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 태그 리스트
	 */
	List<HashMap<String, Object>> selectPumpTagValueList(HashMap<String, Object> map);

	/**
	 * AI On/Off 상태 리스트를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return AI On/Off 리스트
	 */
	List<HashMap<String, Object>> aiOnOffList(HashMap<String, Object> map);

	/**
	 * 배수지 태그 범위 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 배수지 태그 범위 리스트
	 */
	List<HashMap<String, Object>> selectWpTnkTagRangeList(HashMap<String, Object> map);

	/**
	 * 시간별 배수지 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 시간별 배수지 데이터 리스트
	 */
	List<HashMap<String, Object>> selectTankDataHourList(HashMap<String, Object> map);

	/**
	 * 시간별 배수지 데이터 합계를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 시간별 배수지 데이터 합계 리스트
	 */
	List<HashMap<String, Object>> selectTankDataHourSumList(HashMap<String, Object> map);

	/**
	 * 탱크의 순간 유량 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 탱크의 순간 유량 리스트
	 */
	List<HashMap<String, Object>> tankInstantaneous(HashMap<String, Object> map);

	/**
	 * 전력량 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 전력량 리스트
	 */
	List<HashMap<String, Object>> selectElcPwqList(HashMap<String, Object> map);

	/**
	 * 전력 피크 최대 값을 조회한다.
	 * @return 전력 피크 최대 값 리스트
	 */
	List<HashMap<String, Object>> peak_max();

	/**
	 * 펌프 가동 상태 중 관압(PRITag) 데이터를 조회한다.
	 * @return 펌프 관압 상태 리스트
	 */
	List<HashMap<String, Object>> selectPumpPRITagStatus();

	/**
	 * 펌프 가동 상태 중 유량(FRITag) 데이터를 조회한다.
	 * @return 펌프 관압 상태 리스트
	 *///관압
	List<HashMap<String, Object>> selectPumpFRITagStatus();

	/**
	 * 펌프 가동 상태 중 주파수(SPITag) 데이터를 조회한다.
	 * @return 펌프 관압 상태 리스트
	 *///관압
	List<HashMap<String, Object>> selectPumpSPITagStatus();     //관압

	/**
	 * 펌프 가동 대수 데이터를 조회한다.
	 * @return 펌프 가동 대수 리스트
	 */
	List<HashMap<String, Object>> selectPumpPwiStatus();     //펌프 각자 전력

	/**
	 * 펌프의 전력 소비 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 전력 소비 데이터 리스트
	 */
	List<HashMap<String, Object>> selectValve(HashMap<String, Object> map);

	/**
	 * 전력 피크를 제어하는 데이터를 조회한다.
	 * @return 전력 피크 제어 리스트
	 */
	List<HashMap<String, Object>> selectPeakControl(); /**
	 * 펌프 예측 On/Off 상태를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 예측 On/Off 리스트
	 */
	List<HashMap<String, Object>> selectPumpPrdctOnOffStatus(HashMap<String, Object> map);

	/**
	 * 펌프 On/Off 상태를 조회한다.
	 * @return 펌프 On/Off 리스트
	 */
	List<HashMap<String, Object>> selectPumpOnOffStatus();
	/**
	 * 펌프 조합을 조회한다.
	 * @return 펌프 조합 리스트
	 */
	List<HashMap<String, Object>> getPumpUseStatus();

	/**
	 * 설비별 상위 3개 전력 데이터를 조회한다.
	 * @param params 조회 조건을 포함하는 파라미터
	 * @return 설비별 상위 3개 전력 데이터 리스트
	 */
	List<HashMap<String, Object>> getTop3(HashMap<String, Object> params);

	/**
	 * 알람 데이터를 조회한다.
	 * @return 알람 리스트
	 */
	List<HashMap<String, Object>> selectAlarm();
	/**
	 * 배수지 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 배수지 데이터 리스트
	 */
	List<HashMap<String, Object>> selectTankList(HashMap<String, Object> map);
	/**
	 * 피크 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 피크 데이터 리스트
	 */
	List<HashMap<String, Object>> peakSelect(HashMap<String, Object> map);

	/**
	 * 실시간 전력 요금제 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 실시간 전력 요금제 리스트
	 */
	List<HashMap<String, Object>> selectRtRate(HashMap<String, Object> map);
	/**
	 * 펌프 리스트를 조회한다.
	 * @return 펌프 리스트
	 */
	List<HashMap<String, Object>> selectPumpList();
	/**
	 * 전력 합계 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 전력 합계 리스트
	 */
	List<HashMap<String, Object>> selectPwrSumList(HashMap<String, Object> map);

	/**
	 * 현재 AI 상태를 조회한다.
	 * @return AI 상태
	 */
	String getOptMode();
	/**
	 * 압력 데이터를 조회한다.
	 * @return 압력 데이터 리스트
	 */
	List<Map<String, Object>> getPressureData();
	/**
	 * 펌프 정보를 조회한다.
	 * @return 펌프 정보
	 */
	List<HashMap<String, Object>> selectPumpMaster();
	/**
	 * 시간별 전력 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 시간별 전력 리스트
	 */
	List<HashMap<String, Object>> selectHourPwrList(HashMap<String, Object> map);
	/**
	 * 시간별 평균 전력 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 시간별 평균 전력 리스트
	 */
	List<HashMap<String, Object>> selectHourAvgPwrList(HashMap<String, Object> map);
	/**
	 * 시간별 예측 전력 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 시간별 예측 전력 리스트
	 */
	List<HashMap<String, Object>> selectHourPwrPrdctList(HashMap<String, Object> map);
	/**
	 * 펌프 사용 데이터를 조회한다.
	 * @param nowDate 현재 날짜
	 * @return 펌프 사용 리스트
	 */
	List<HashMap<String, Object>> pumpUsageList(String nowDate);
	/**
	 * 펌프 사용 여부 데이터를 조회한다.
	 * @param nowDate 현재 날짜
	 * @return 펌프 사용 여부 리스트
	 */
	List<HashMap<String, Object>> pumpUsageYnList(String nowDate);


	/**
	 * 펌프 예측 전력 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 예측 전력 항목
	 */
	HashMap<String, Object> selectPrdctPumpPwrItem(HashMap<String, Object> map);
	/**
	 * 펌프 상태 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 상태 리스트
	 */
	List<HashMap<String, Object>> pumpStatusSelect(HashMap<String, Object> map);
	/**
	 * 펌프 예측 조합을 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 예측 조합
	 */
	List<HashMap<String, Object>> pumpStatusSelectYn(HashMap<String, Object> map);
	/**
	 * WPP 태그 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return WPP 태그 리스트
	 */
	List<HashMap<String, Object>> wppTagList(HashMap<String, Object> map);
	/**
	 * 예측 분석 시간을 조회한다.
	 * @return 예측 분석 시간 항목
	 */
	HashMap<String, Object> selectPrdctAnlyTime();
	/**
	 * 예측 조합 생성 시간을 조회한다.
	 * @return 예측 조합 생성 시간
	 */
	HashMap<String, Object> selectPrdctYnAnlyTime();
	/**
	 * 전력 요금과 전력 데이터를 조회한다.
	 * @return 전력 요금과 전력 데이터
	 */
	HashMap<String, Object> selectCostPwr();
	/**
	 * SCADA 데이터 및 예측 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return SCADA 데이터 및 예측 데이터
	 */
	List<HashMap<String, Object>> selectPumpPrdctScadaList(HashMap<String, Object> map);
	/**
	 * ESS 및 태양광 전력 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return ESS 및 태양광 전력 데이터
	 */
	List<HashMap<String, Object>> pumpPrdctSunEssSelectList(HashMap<String, Object> map);

	/**
	 * SCADA 데이터 및 예측 데이터 단일 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return SCADA 데이터 및 예측 데이터 단일 데이터
	 */
	HashMap<String, Object> selectPumpPrdctScadaOne(HashMap<String, Object> map);
	/**
	 * 전력 절감 데이터를 조회한다.
	 * @return 전력 절감 데이터
	 */
	HashMap<String, Object> selectSavingResult();
	/**
	 * AI 상태 데이터를 조회한다.
	 * @return AI 상태 리스트
	 */
	List<HashMap<String, Object>> selectAiStatus();
	/**
	 * AI 상태를 업데이트한다.
	 * @param map 업데이트할 상태 정보를 포함하는 파라미터
	 */
	void updateAiStatus(HashMap<String, Object> map);
	/**
	 * 펌프 비상 정지 상태를 조회한다.
	 * @param pumpGrp 펌프 그룹
	 * @return 펌프 비상 정지 상태
	 */
	String selectPumpEmergencyStatus(String pumpGrp);
	/**
	 * AI 펌프 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return AI 펌프 데이터 리스트
	 */
	List<HashMap<String, Object>> selectAIPumpData(HashMap<String, Object> map);
	/**
	 * AI 펌프 사용 여부 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return AI 펌프 사용 여부 리스트
	 */
	List<HashMap<String, Object>> selectAIPumpYnData(HashMap<String, Object> map);

	/**
	 * 현재 펌프 예측 평균 전력 데이터를 조회한다.
	 * @return 펌프 예측 평균 전력 리스트
	 */
	List<HashMap<String, Object>> pumpPrdctAvgNowSelectList();

	/**
	 * 펌프 제어 이력 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 제어 이력 리스트
	 */
	List<HashMap<String, Object>> selectPumpCtrHistoryList(HashMap<String, Object> map);
	/**
	 * 펌프 제어 이력 데이터 개수를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 펌프 제어 이력 데이터 개수
	 */
	int selectPumpCtrHistoryCount(HashMap<String, Object> map);


	/**
	 * 마지막 펌프 사용 주파수 데이터를 설정한다.
	 * @param map 설정할 데이터를 포함하는 파라미터
	 * @return 마지막 펌프 사용 주파수 리스트
	 */
	List<HashMap<String, Object>> setLastCurPumpUseFreq(HashMap<String, Object> map);

	/**
	 * 마지막 펌프 사용 압력 데이터를 설정한다.
	 * @param map 설정할 데이터를 포함하는 파라미터
	 * @return 마지막 펌프 사용 압력 리스트
	 */
	List<HashMap<String, Object>> setLastCurPumpUsePri(HashMap<String, Object> map);
	/**
	 * 예측 펌프 조합 테이터를 조회한다.
	 * @return 예측 펌프 조합 테이터
	 */
	List<HashMap<String, Object>> selectDrvnPumpMaster();


	/**
	 * 시간별 전력 사용 데이터를 조회한다.
	 * @param map 조회 조건을 포함하는 파라미터
	 * @return 시간별 전력 사용 항목
	 */
	HashMap<String, Object> selectHourUsePwr(HashMap<String, Object> map);
	HashMap<String, Object> selectHourUsePwrPwi(HashMap<String, Object> map);

	/**
	 * 예측 결과 데이터를 삽입한다.
	 * @param map 삽입할 예측 결과 데이터를 포함하는 파라미터
	 */
	void insertPrdctResult(HashMap<String, Object> map);

	/**
	 * 펌프 예측 데이터를 계산을 위한 데이터
	 * @return 펌프 예측 데이터 리스트
	 */
	List<HashMap<String, Object>> pumpPrdctCalSelectList();

	List<HashMap<String, Object>> pumpPrdctCalSelectListPwi();

	/**
	 * 예측 조합 시간별 데이터를 조회한다.
	 * @param drvnParam 조회 조건을 포함하는 파라미터
	 * @return 예측 조합 시간별 데이터 항목
	 */
	HashMap<String, String> pumpDrvnMinute(HashMap<String, String> drvnParam);
	/**
	 * AI 펌프 시간을 조회한다.
	 * @return AI 펌프 시간
	 */
	String getAIPumpTime();

	List<HashMap<String, Object>> selectAiModeRstList(HashMap<String, Object> map);

	HashMap<String, String> selectAiModeRstItem(HashMap<String, String> map);


	void updateAiModeRst(HashMap<String, String> map);

	List<HashMap<String, Object>> selectAiModeList(HashMap<String, Object> map);

	List<String> getAiModeCount(HashMap<String, Object> param);
}

