package kr.co.mindone.ems.energy;
/**
 * packageName    : kr.co.mindone.ems.energy
 * fileName       : EnerSpendMapper
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
public interface EnerSpendMapper {

	/**
	 * 시설 순시 시간대별 값을 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 순시 시간대별 값 리스트
	 */
	List<HashMap<String, Object>> selectZoneUseList(HashMap<String, Object> map);

	/**
	 * 시설 순시 합계를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 순시 합계 리스트
	 */
	List<HashMap<String, Object>> selectZoneUseList_sum(HashMap<String, Object> map);

	/**
	 * 현시각 시설 순시 데이터를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 현시각 시설 순시 데이터 리스트
	 */
	List<HashMap<String, Object>> sisul_sunsi(HashMap<String, Object> map);

	/**
	 * 설비 순시 시간대별 값을 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 설비 순시 시간대별 값 리스트
	 */
	List<HashMap<String, Object>> selectFacUseList(HashMap<String, Object> map);

	/**
	 * 설비 순시 합계를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 설비 순시 합계 리스트
	 */
	List<HashMap<String, Object>> selectFacUseList_sum(HashMap<String, Object> map);

	/**
	 * 펌프 성능 데이터를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 펌프 성능 데이터 리스트
	 */
	List<HashMap<String, Object>> selectPumpPerformList(HashMap<String, Object> map);

	/**
	 * 펌프 성능 데이터를 PWI 기준으로 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 펌프 성능 데이터 리스트
	 */
	List<HashMap<String, Object>> selectPumpPerformList_ss_pwi(HashMap<String, Object> map);

	/**
	 * 설비 정보를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 설비 정보 리스트
	 */
	List<HashMap<String, Object>> selectFac(HashMap<String, Object> map);

	/**
	 * 시설 순시 차트를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 순시 차트 리스트
	 */
	List<HashMap<String, Object>> sunsiChart(HashMap<String, Object> map);

	/**
	 * 시설 순시 데이터를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 순시 데이터 리스트
	 */
	List<HashMap<String, Object>> selectFacSunsi(HashMap<String, Object> map);

	/**
	 * 정수장의 현재 전력 사용량을 조회하는 메서드
	 * @return 정수장의 현재 전력 사용량 리스트
	 */
	List<HashMap<String, Object>> selectNowElec();

	/**
	 * 정수장의 현재 피크 목표치를 조회하는 메서드
	 * @return 정수장의 현재 피크 목표치 리스트
	 */
	List<HashMap<String, Object>> selectNowPeak();

	/**
	 * 정수장의 일, 월, 년 전기 사용량을 조회하는 메서드
	 * @return 정수장의 일, 월, 년 전기 사용량 리스트
	 */
	List<HashMap<String, Object>> selectYMD();

	/**
	 * 절감 결과를 조회하는 메서드
	 * @return 절감 결과 리스트
	 */
	List<HashMap<String, Object>> baseElec();

	/**
	 * 금년 절감량을 조회하는 메서드
	 * @return 금년 절감량 리스트
	 */
	List<HashMap<String, Object>> rstSavingTargetSum();

	/**
	 * 요금제 상세 정보를 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 요금제 상세 정보 리스트
	 */
	List<HashMap<String, Object>> selectRateInfo(HashMap<String, Object> map);

	/**
	 * 시설의 피크 값을 조회하는 메서드
	 * @param search 검색어
	 * @return 시설의 피크 값 리스트
	 */
	List<HashMap<String, Object>> peakFac(String search);

	/**
	 * 현재 피크 값을 조회하는 메서드
	 * @return 현재 피크 값 리스트
	 */
	List<HashMap<String, Object>> nowPeak();

	/**
	 * 총 전력 사용량을 조회하는 메서드
	 * @param map 조회에 필요한 파라미터
	 * @return 총 전력 사용량
	 */
	double selectAllPwq(HashMap<String, Object> map);
}
