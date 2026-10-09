package kr.co.mindone.ems.drvn;
/**
 * packageName    : kr.co.mindone.ems.drvn
 * fileName       : DrvnMapper
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.context.annotation.Profile;

import java.util.HashMap;
import java.util.List;
import java.util.Set;

@Mapper
@Profile("!gm & !hp & !ji & !hy & !ss & !gm2 & !hp2 & !hy2 & !ji2" )
public interface DrvnMapper {
	
	HashMap<String, Object> selectPumpComb();
	
	/**
	 * 펌프 압력 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 펌프 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPumpPressure(HashMap<String, Object> param);
	/**
	 * 수두손실 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 수두손실 데이터를 반환
	 */
	Double selectHeadLoss(HashMap<String, Object> param);

	/**
	 * 펌프 유량 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 펌프 유량 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPumpFlow(HashMap<String, Object> param);

	/**
	 * 현재 펌프 사용 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 현재 펌프 사용 데이터를 반환
	 */
	List<HashMap<String, Object>> selectNowPumpUse(HashMap<String, Object> param);

	/**
	 * 현재 펌프 전력 사용 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 현재 펌프 전력 사용 데이터를 반환
	 */
	List<HashMap<String, Object>> selectNowPumpPwrUse(HashMap<String, Object> param);

	/**
	 * 수두손실 계산을 위한 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 수두손실 계산 데이터를 반환
	 */
	List<HashMap<String, Object>> selectForHeadLoss(HashMap<String, Object> param);

	/**
	 * 시스템 소개 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 시스템 소개 데이터를 반환
	 */
	List<HashMap<String, Object>> selectIntradotion(HashMap<String, Object> param);

	/**
	 * 성능 곡선 유량 및 압력 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 성능 곡선 유량 및 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPrdctFlowPressure(HashMap<String, Object> param);

	/**
	 * 현재 펌프 유량 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 현재 펌프 유량 데이터를 반환
	 */
	List<HashMap<String, Object>> selectCurFlowData(HashMap<String, Object> param);

	/**
	 * 펌프 조합 계산 데이터를 조회하는 메서드
	 * @return 펌프 조합 계산 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPumpCombCal();

	/**
	 * 성능 곡선 유량 및 압력 데이터를 조회하는 메서드
	 * @param map 조회 조건을 담은 맵
	 * @return 성능 곡선 유량 및 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> prdctFlowPressure(HashMap<String, Object> map);

	/**
	 * 탱크 유량 및 압력 데이터를 조회하는 메서드
	 * @param map 조회 조건을 담은 맵
	 * @return 탱크 유량 및 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPreTnkFlowPressure(HashMap<String, Object> map);

	/**
	 * 현재 탱크 유량 및 압력 데이터를 조회하는 메서드
	 * @param map 조회 조건을 담은 맵
	 * @return 현재 탱크 유량 및 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> selectCurTnkFlowPressure(HashMap<String, Object> map);

	/**
	 * EPANET 탱크 유량 및 압력 데이터를 조회하는 메서드
	 * @param map 조회 조건을 담은 맵
	 * @return EPANET 탱크 유량 및 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPreEPANETTnkFlowPressure(HashMap<String, Object> map);

	/**
	 * 수두손실 대상 이전 유량 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 수두손실 대상 이전 유량 데이터를 반환
	 */
	List<Double> selectHeadLossTargetPreFlow(HashMap<String, Object> param);

	/**
	 * 수두손실 대상 현재 유량 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 수두손실 대상 현재 유량 데이터를 반환
	 */
	List<Double> selectHeadLossTargetCurFlow(HashMap<String, Object> param);

	/**
	 * Drvn 펌프 사용 여부 데이터를 삽입하는 메서드
	 * @param map 삽입할 데이터를 담은 맵
	 */
	void insertDrvnPumpYnData(HashMap<String, Object> map);

	/**
	 * 펌프 사용 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 펌프 사용 데이터를 반환
	 */
	List<HashMap<String, Object>> getPumpUse(HashMap<String, Object> param);

	/**
	 * 부하 조회 데이터를 조회하는 메서드
	 * @return 부하 조회 데이터를 반환
	 */
	List<HashMap<String, String>> getLoadInquiry();

	/**
	 * 펌프 사용 여부 데이터를 삽입하는 메서드
	 * @param map 삽입할 데이터를 담은 맵
	 */
	void insertInQuiryPumpYnData(HashMap<String, Object> map);

	/**
	 * 생산 유량 및 압력 데이터를 삽입하는 메서드
	 * @param map 삽입할 데이터를 담은 맵
	 * @return 삽입된 생산 유량 및 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> getInsertUsePrdctFlowPressure(HashMap<String, Object> map);
	/**
	 * 펌프 조합 여부 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 펌프 조합 여부 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPrdctPumpCombYn(HashMap<String, Object> param);

	/**
	 * 그룹 펌프 조합 여부 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 그룹 펌프 조합 여부 데이터를 반환
	 */
	List<HashMap<String, Object>> selectGrpPrdctPumpCombYn(HashMap<String, Object> param);

	/**
	 * 현재 유량 및 압력 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 현재 유량 및 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> curFlowPressure(HashMap<String, Object> param);

	/**
	 * 이전 유량 및 압력 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 이전 유량 및 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> preFlowPressure(HashMap<String, Object> param);

	/**
	 * 최적 이전 펌프 사용 데이터를 조회하는 메서드
	 * @param pumpMap 펌프 데이터를 담은 파라미터
	 * @return 최적 이전 펌프 사용 데이터를 반환
	 */
	List<Integer> optPrePumpUse(HashMap<String, Object> pumpMap);

	/**
	 * 조회 데이터를 삭제하는 메서드
	 * @param map 삭제할 데이터를 담은 맵
	 */
	void deleteInquiryData(HashMap<String, Object> map);

	/**
	 * 현재 펌프 전력 데이터를 엑셀로 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 현재 펌프 전력 데이터를 반환
	 */
	List<HashMap<String, Object>> excelCurPumpPower(HashMap<String, Object> param);

	/**
	 * 이전 펌프 데이터를 엑셀로 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 이전 펌프 데이터를 반환
	 */
	List<HashMap<String, Object>> excelPrePumpData(HashMap<String, Object> param);

	/**
	 * 현재 펌프 유량 데이터를 엑셀로 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 현재 펌프 유량 데이터를 반환
	 */
	List<HashMap<String, Object>> excelCurPumpFlow(HashMap<String, Object> param);

	/**
	 * 현재 펌프 데이터를 엑셀로 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 현재 펌프 데이터를 반환
	 */
	List<HashMap<String, Object>> excelCurPumpPri(HashMap<String, Object> param);

	/**
	 * 현재 펌프 사용 여부 데이터를 엑셀로 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 현재 펌프 사용 여부 데이터를 반환
	 */
	List<HashMap<String, Object>> excelCurPumpYn(HashMap<String, Object> param);

	/**
	 * 이전 펌프 사용 여부 데이터를 엑셀로 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 이전 펌프 사용 여부 데이터를 반환
	 */
	List<HashMap<String, Object>> excelPrePumpYn(HashMap<String, Object> param);

	/**
	 * 이전 사용 펌프 문자열 데이터를 조회하는 메서드
	 * @param pumpUseParam 조회 조건을 담은 파라미터
	 * @return 이전 사용 펌프 문자열 데이터를 반환
	 */
	HashMap<String, String> getPreUsePumpString(HashMap<String, Object> pumpUseParam);
	/**
	 * 이전 사용 펌프 문자열 데이터를 조회하는 메서드
	 * @param pumpUseParam 조회 조건을 담은 파라미터
	 * @return 이전 사용 펌프 문자열 데이터를 반환
	 */
	HashMap<String, String> getCurUsePumpString(HashMap<String, Object> pumpUseParam);

	/**
	 * 실제 측정된 펌프 조합 데이터를 조회하는 메서드
	 * @param nowMap 조회 조건을 담은 파라미터
	 * @return 실제 측정된 펌프 조합 데이터를 반환
	 */
	List<HashMap<String, Object>> pumpActlMsrmCmbn(HashMap<String, Object> nowMap);

	/**
	 * 생성된 펌프 조합 데이터를 조회하는 메서드
	 * @param nowMap 조회 조건을 담은 파라미터
	 * @return 생성된 펌프 조합 데이터를 반환
	 */
	List<HashMap<String, Object>> pumpPrdcCmbn(HashMap<String, Object> nowMap);

	/**
	 * 펌프 전력 데이터를 조회하는 메서드
	 * @param nowMap 조회 조건을 담은 파라미터
	 * @return 펌프 전력 데이터를 반환
	 */
	List<Double> pumpInstPwr(HashMap<String, Object> nowMap);

	/**
	 * 펌프 유량 데이터를 조회하는 메서드
	 * @param nowMap 조회 조건을 담은 파라미터
	 * @return 펌프 유량 데이터를 반환
	 */
	List<Double> pumpInstFlowRate(HashMap<String, Object> nowMap);

	/**
	 * 펌프 조합 시간을 조회하는 메서드
	 * @param dateTime 조회할 날짜와 시간
	 * @return 펌프 조합 시간을 반환
	 */
	String getPumpCombTime();

	/**
	 * 12시간 내의 현재 펌프 유량 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 12시간 내의 현재 펌프 유량 데이터를 반환
	 */
	List<HashMap<String, Object>> select12HourCurPumpFlow(HashMap<String, Object> param);

	/**
	 * 12시간 내의 현재 펌프 압력 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 12시간 내의 현재 펌프 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> select12HourCurPumpPressure(HashMap<String, Object> param);

	/**
	 * 이전 압력 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 이전 압력 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPrePri(HashMap<String, Object> param);

	/**
	 * 이전 유량 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 이전 유량 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPreFlow(HashMap<String, Object> param);

	/**
	 * 이전 예측 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 이전 예측 데이터를 반환
	 */
	List<HashMap<String, Object>> selectPreWithDstrb(HashMap<String, Object> param);

	/**
	 * 펌프 주파수 사용 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 펌프 주파수 사용 데이터를 반환
	 */
	List<HashMap<String, Object>> getPumpFreqUse(HashMap<String, Object> param);

	/**
	 * 운문 주파수 인덱스를 조회하는 메서드
	 * @param ts 조회할 타임스탬프
	 * @return 운문 주파수 인덱스를 반환
	 */
	Integer getWMFreqIdx(String ts);

	/**
	 * 마지막 현재 주파수를 조회하는 메서드
	 * @param pump_idx 펌프 인덱스가 담긴 파라미터
	 * @return 마지막 현재 주파수를 반환
	 */
	Double getLastCurFreq(HashMap<String, Object> pump_idx);

	/**
	 * Raw 데이터를 조회하는 메서드
	 * @param rawParam 조회 조건을 담은 파라미터
	 * @return Raw 데이터를 반환
	 */
	Double selectRawData(HashMap<String, Object> rawParam);

	/**
	 * 운문 인버터 펌프 주파수 확인 메서드
	 * @param pumpMap 조회할 펌프 맵
	 * @return 펌프 주파수 데이터를 포함한 집합을 반환
	 */
	Set<Integer> wmInverterPumpFreqCheck(HashMap<String, Object> pumpMap);

	/**
	 * 성생된 펌프 조합 엑셀 데이터를 조회하는 메서드
	 * @param param 조회 조건을 담은 파라미터
	 * @return 성생된 펌프 조합 엑셀 데이터를 반환
	 */
	List<HashMap<String, String>> pumpDrvnCombExcelData(HashMap<String, Object> param);

	/**
	 * 고령 압력제어 압력데이터 반환
	 * @return 고령 압력제어 압력데이터 반환
	 */
	HashMap<String, Double> getGrLifePre();

	/**
	 * 고령 공업정수지 이전 예측 압력 데이터 반환
	 * @param combParam
	 * @return
	 */
	List<Double> selectPumpCombPressure(HashMap<String, Object> combParam);

	List<HashMap<String, Object>> grPreesureList(HashMap<String, Object> param);

	List<HashMap<String, Object>> grPrePressure(HashMap<String, Object> param);

	int checkManualOperLog(HashMap<String, Object> checkLogParam);

	List<String> guPumpStatusChange(HashMap<String, Object> statusParam);

	HashMap<String, String> getPreUsePumpStatus(HashMap<String, Object> pumpUseParam);

	void insertManualOperLog(HashMap<String, Object> logInsParma);

	String getPumpCombLogTime();

	Set<Integer> inverterPumpFreqCheck(HashMap<String, Object> pumpMap);

	Double select5MinuteAvgRawData(HashMap<String, Object> rawParam);

	Double getBaWppValveData(String func_typ);

	void setBaWppValveData(HashMap<String, Object> valveUpdateMap);

	void insertManualOperLogNew(HashMap<String, Object> logInsParma);

	HashMap<String, String> checkManualOperLogPump(HashMap<String, Object> manualOperLogParam);

	HashMap<String, String> getWppData(String func_typ);

	void setWppOnlyDate(HashMap<String, String> param);

	void setWppCombAndStatus(HashMap<String, String> param);

	Double select10MinuteAvgRawData(HashMap<String, Object> rawParam);

	List<HashMap<String, Integer>> getPumpCombination(HashMap<String, Object> combParam);

	List<HashMap<String, Object>> getInsertGsFlowPressure(HashMap<String, Object> map);

	Double getGosanOptLevel(int hour);

	List<HashMap<String, Object>> selectPumpCombCalGosan();

	List<HashMap<String, Object>> getPumpCombinationItem(HashMap<String, Object> map);

	List<HashMap<String, Object>> getGroupPumpCal(HashMap<String, Object> pumpGrp);

	void setPumpListYn(HashMap<String, Object> item);

	void disableGroupPumpCal(HashMap<String, Object> changeCal);

	void enableGroupPumpCal(HashMap<String, Object> changeCal);

	List<HashMap<String, Object>> getGrpFlPreTag(int pump_grp);

	List<HashMap<String, Object>> selectPumpCombList(HashMap<String, Object> params);

	void savePumpComb (HashMap<String, Object> params);

	void updatePumpCombItem (HashMap<String, Object> params);

	Double getHujaOptLevel(int hour);

	// drvnMapper.java
	Double selectAverageValueLast10Minutes(@Param("DSTRB_ID") String dstrbId, @Param("nowDateTime") String nowDateTime);

	List<HashMap<String, Object>> getGrpPumpComb(int grp);

	void insertCombPwrUnit(List<HashMap<String, Object>> insertArr);

	List<HashMap<String, Object>> selectGsAllLinkRange(HashMap<String, Object> param);

	List<HashMap<String, Object>> selectGsAllNodeRange(HashMap<String, Object> param);

	Double selectGsAllLinkFirst(HashMap<String, Object> param);

	Double selectGsAllNodeFirst(HashMap<String, Object> param);

	List<HashMap<String, Object>> selectGsAllCurLinkRange(HashMap<String, Object> param);

	List<HashMap<String, Object>> selectGsAllCurNodeRange(HashMap<String, Object> param);

	Double selectGsAllCurLinkFirst(HashMap<String, Object> param);

	Double selectGsAllCurNodeFirst(HashMap<String, Object> param);
}
