package kr.co.mindone.ems.energy;
/**
 * packageName    : kr.co.mindone.ems.energy
 * fileName       : EnerSpendService
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.HashMap;
import java.util.List;

@Service
public class EnerSpendService {
	@Autowired
	private EnerSpendMapper enerSpendMapper;

	/**
	 * 시설의 전력 값 반환
	 * @param map 조회에 필요한 파라미터
	 * @return 시설의 전력 값 반환
	 */
	List<HashMap<String, Object>> selectFacUseList(HashMap<String, Object> map) {
		return enerSpendMapper.selectFacUseList(map);
	}

	/**
	 * 시설의 전력 합 값 반환
	 * @param map 조회에 필요한 파라미터
	 * @return 시설의 전력 합 값
	 */
	List<HashMap<String, Object>> selectFacUseList_sum(HashMap<String, Object> map) {
		return enerSpendMapper.selectFacUseList_sum(map);
	}

	/**
	 * 설비의 전력 값 반환
	 * @param map 조회에 필요한 파라미터
	 * @return 설비의 전력 값
	 */
	List<HashMap<String, Object>> selectZoneUseList(HashMap<String, Object> map) {
		return enerSpendMapper.selectZoneUseList(map);
	}
	
	/**
	 * 설비의 전력 합 값 반환
	 * @param map 조회에 필요한 파라미터
	 * @return 설비의 전력 합
	 */
	@Transactional
	public List<HashMap<String, Object>> selectZoneUseList_sum(HashMap<String, Object> map) {
		List<HashMap<String, Object>> selectZoneUseList_sum = enerSpendMapper.selectZoneUseList_sum(map);
		List<HashMap<String, Object>> nowElec = selectNowElec();
		HashMap<String, Object> pwiMap = new HashMap<>();
		pwiMap.put("zone_code", "총전력");
		pwiMap.put("y", (nowElec.get(0)).get("nowPwi"));
		selectZoneUseList_sum.add(pwiMap);
		double allPwq = enerSpendMapper.selectAllPwq(map);
		HashMap<String, Object> pwqMap = new HashMap<>();
		pwqMap.put("zone_code", "총전력량");
		pwqMap.put("y", allPwq);
		selectZoneUseList_sum.add(pwqMap);

		return selectZoneUseList_sum;
	}

	/**
	 * 시설 전력 순시 
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 전력 순시 
	 */
	public List<HashMap<String, Object>> sisul_sunsi(HashMap<String, Object> map) {
		return enerSpendMapper.sisul_sunsi(map);
	}

	/**
	 * 펌프 정보 리스트
	 * @param map 조회에 필요한 파라미터
	 * @return 펌프 가동 여부 및 정보
	 */
	List<HashMap<String, Object>> selectPumpPerformList(HashMap<String, Object> map) {
		return enerSpendMapper.selectPumpPerformList(map);
	}
	
	/**
	 * 산성 정수장 펌프 정보 리스트
	 * @param map 조회에 필요한 파라미터
	 * @return 산성 정수장 펌프 가동 여부 및 정보
	 */
	List<HashMap<String, Object>> selectPumpPerformList_ss_pwi(HashMap<String, Object> map) {
		return enerSpendMapper.selectPumpPerformList_ss_pwi(map);
	}

	/**
	 * 설비 정보 출력
	 * @param map 조회에 필요한 파라미터
	 * @return 설비 정보
	 */
	List<HashMap<String, Object>> selectFac(HashMap<String, Object> map) {
		return enerSpendMapper.selectFac(map);
	}

	/**
	 * 설비 순시 전력 차트 데이터
	 * @param map 조회에 필요한 파라미터
	 * @return 선비 순시 전력 차트 데이터
	 */
	List<HashMap<String, Object>> sunsiChart(HashMap<String, Object> map) {
		return enerSpendMapper.sunsiChart(map);
	}

	/**
	 * 시설 별 전력 순시
	 * @param map 조회에 필요한 파라미터
	 * @return 시설 별 전력 순시
	 */
	List<HashMap<String, Object>> selectFacSunsi(HashMap<String, Object> map) {	return enerSpendMapper.selectFacSunsi(map);	}

	/**
	 * 정수장 총 전력 순시 데이터
	 * @return 정수장 총 전력 순시 데이터
	 */
	@Transactional(propagation = Propagation.REQUIRES_NEW)
	List<HashMap<String, Object>> selectNowElec() {
		return enerSpendMapper.selectNowElec();
	}

	/**
	 * 현재 전력 피크 데이터 
	 * @return 현재 전력 피크 데이터
	 */
	List<HashMap<String, Object>> selectNowPeak() {
		return enerSpendMapper.selectNowPeak();
	}

	/**
	 * 전년, 전월, 전일 전력 데이터 출력
	 * @return 전년, 전월, 전일 전력 데이터 출력
	 */
	List<HashMap<String, Object>> selectYMD() {
		return enerSpendMapper.selectYMD();
	}

	/**
	 * 메인 화면 전력 절감량 데이터 출력
	 * @return 전력 절감량 데이터
	 */
	List<HashMap<String, Object>> baseElec() {
		return enerSpendMapper.baseElec();
	}

	/**
	 * 월별 전력 절감 데이터 출력
	 * @return 월별 전력 절감 데이터 출력
	 */
	List<HashMap<String, Object>> rstSavingTargetSum() {
		return enerSpendMapper.rstSavingTargetSum();
	}

	/**
	 * 요금제 정보에 따른 전력요금 출력
	 * @param map 조회에 필요한 데이터
	 * @return 요금제정보에 따른 전력요금
	 */
	List<HashMap<String, Object>> selectRateInfo(HashMap<String, Object> map) {
		return enerSpendMapper.selectRateInfo(map);
	}

	/**
	 * 시설별 전력 피크값 출력
	 * @param search 조회에 필요한 데이터
	 * @return 시설별 전력 피크 값
	 */
	List<HashMap<String, Object>> peakFac(String search) {
		return enerSpendMapper.peakFac(search);
	}

	/**
	 * 현재 전력 피크값 출력
	 * @return 현재 전력 피크
	 */
	public List<HashMap<String, Object>> nowPeak() {
		return enerSpendMapper.nowPeak();
	}

}
