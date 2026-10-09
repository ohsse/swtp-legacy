package kr.co.mindone.ems.setting;
/**
 * packageName    : kr.co.mindone.ems.setting
 * fileName       : SettingMapper
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
public interface SettingMapper {
    /**
     * 월간 사용 전력량 조회
     * @param map 필터 조건
     * @return 사용 전력량 데이터 목록
     */
    List<HashMap<String, Object>> getUsageData(HashMap<String, Object> map);

    /**
     * 월간 목표 전력량 조회
     * @param map 필터 조건
     * @return 목표 전력량 데이터 목록
     */
    List<HashMap<String, Object>> getGoalData(HashMap<String, Object> map);

    /**
     * 시설 목록 조회
     * @param map 필터 조건
     * @return 시설 목록
     */
    List<HashMap<String, Object>> selectZone(HashMap<String, Object> map);

    /**
     * 태그 목록 조회
     * @param map 필터 조건
     * @return 태그 목록
     */
    List<HashMap<String, Object>> selectTagList(HashMap<String, Object> map);

    /**
     * 전기요금제 정보 조회
     * @param params 필터 조건
     * @return 요금제 정보 목록
     */
    List<HashMap<String, Object>> selectRtInfo(HashMap<String, Object> params);

    /**
     * 계절별 요금 정보 조회
     * @param params 필터 조건
     * @return 계절별 요금 정보 목록
     */
    List<HashMap<String, Object>> selectRT_RATE_INF(HashMap<String, Object> params);

    /**
     * 펌프 마스터 정보 조회
     * @return 펌프 마스터 정보 목록
     */
    List<HashMap<String, Object>> selectCTR_PRF_PUMPMST_INF();



    /**
     * 펌프 전력 정보 병합
     * @param map 병합할 데이터
     */
    void mergePTR_STRTG_INF(HashMap<String , String> map);

    /**
     * 펌프 운영 정보 병합
     * @param params 병합할 데이터
     */
    void mergeOPER_INF(HashMap<String, Object> params);

    /**
     * 정수지 정보 조회
     * @param params 필터 조건
     * @return 정수지 정보 목록
     */
    List<HashMap<String, Object>> selectSuji(HashMap<String, Object> params);

    /**
     * 전력요금제 시간대 정보 갱신
     * @param parameterMap 갱신할 데이터
     */
    void update_time_RT_RATE_INF(HashMap<String, Object> parameterMap);

    /**
     * 경부하 요금 갱신
     * @param parameterMap 갱신할 데이터
     */
    void update_L_RT_RATE_INF(HashMap<String, Object> parameterMap);

    /**
     * 중간부하 요금 갱신
     * @param parameterMap 갱신할 데이터
     */
    void update_M_RT_RATE_INF(HashMap<String, Object> parameterMap);

    /**
     * 최대부하 요금 갱신
     * @param parameterMap 갱신할 데이터
     */
    void update_H_RT_RATE_INF(HashMap<String, Object> parameterMap);

    /**
     * 태그 정보 업데이트
     * @param map 업데이트할 태그 정보
     */
    void updateTagInfo(HashMap<String, Object> map);

    /**
     * 시설 정보 업데이트
     * @param map 업데이트할 시설 정보
     */
    void updateFac(HashMap<String, Object> map);

    /**
     * 목표 전력 설정 정보 조회
     * @return 설정 정보 목록
     */
    List<HashMap<String, Object>> selectGetSetting();

    /**
     * 목표 전력량 업데이트
     * @param params 업데이트할 데이터
     */
    void updateGoal(HashMap<String, Object> params);

    /**
     * 펌프 마스터 설정 업데이트
     * @param map 업데이트할 데이터
     */
    void updateSetCTR_PRF_PUMPMST_INF(HashMap<String, Object> map);

    /**
     * 전력 사용량 리포트 조회
     * @param params 필터 조건
     * @return 전력 사용량 데이터 목록
     */
    List<HashMap<String, Object>> selectReport_kwh(HashMap<String, Object> params);

    /**
     * 절감 정보 리포트 조회
     * @param params 필터 조건
     * @return 절감 정보 목록
     */
    List<HashMap<String, Object>> selectReport_saving(HashMap<String, Object> params);

    /**
     * 사용량 리포트 조회 (기준 2)
     * @param params 필터 조건
     * @return 사용량 데이터 목록
     */
    List<HashMap<String, Object>> selectReport2(HashMap<String, Object> params);

    /**
     * 사용량 리포트 조회 (기준 3)
     * @param params 필터 조건
     * @return 사용량 데이터 목록
     */
    List<HashMap<String, Object>> selectReport3(HashMap<String, Object> params);

    /**
     * 리포트 조회 (기준 4)
     * @param params 필터 조건
     * @return 리포트 데이터 목록
     */
    List<HashMap<String, Object>> selectReport4(HashMap<String, Object> params);

    /**
     * 리포트 조회 (기준 5)
     * @param params 필터 조건
     * @return 리포트 데이터 목록
     */
    List<HashMap<String, Object>> selectReport5(HashMap<String, Object> params);

    /**
     * 리포트 조회 (기준 6)
     * @param params 필터 조건
     * @return 리포트 데이터 목록
     */
    List<HashMap<String, Object>> selectReport6(HashMap<String, Object> params);

    /**
     * 리포트 조회 (기준 7)
     * @param params 필터 조건
     * @return 리포트 데이터 목록
     */
    List<HashMap<String, Object>> selectReport7(HashMap<String, Object> params);

    /**
     * 목표 피크 설정
     * @param params 목표 피크 설정 정보
     */
    void insertPeakGoal(Map<String, Object> params);

    /**
     * 목표 피크 조회
     * @return 목표 피크 정보 목록
     */
    List<HashMap<String, Object>> selectPeakGoal();

    /**
     * 월별, 계절 요금제 설정 조회
     * @return 월별, 계절 요금제 설정 목록
     */
    List<HashMap<String, Object>> selectMonthSeason();

    /**
     * 월별 계절 요금제 설정 업데이트
     * @param updateMap 업데이트할 데이터
     */
    void setMonthSeason(HashMap<String, Object> updateMap);

    /**
     * 계절별 요금 정보 조회
     * @param ssn 계절 정보
     * @return 계절별 요금 정보 목록
     */
    List<HashMap<String, Object>> selectRate(String ssn);

    /**
     * 계절 부하 정보 조회
     * @param ssn 계절 정보
     * @return 부하 정보 목록
     */
    List<HashMap<String, Object>> selectSeasonLoad(String ssn);

    /**
     * 계절 부하 설정
     * @param updateMap 업데이트할 부하 설정
     */
    void setSeasonLoad(HashMap<String, Object> updateMap);

    /**
     * 절감 목표 월별 부하 설정
     * @param updateMap 설정할 부하 정보
     */
    void setTargetMonthLoad(HashMap<String, Object> updateMap);

    /**
     * 전력 요금제 수정
     * @param updateMap 설정할 전력 요금제 정보
     */
    void setRateCost(Map<String, Object> updateMap);



    Double getAvgOneHourRaw(HashMap<String, String> tag);

    String getMaxRawDataTime();
    Double getAvgOneDayRaw(Map<String, Object> param);
}
