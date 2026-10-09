package kr.co.mindone.ems.alarm;
/**
 * packageName    : kr.co.mindone.alarm
 * fileName       : AlarmMapper
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
public interface AlarmMapper {
	/**
	 * 알람에서 확인하는 전력 예측 피크 정보
	 * @param map 현재 시간정보
	 * @return 예측 피크 데이터
	 */
	Double prdctPeak(HashMap<String, Object> map);

	/**
	 * 알람 등록
	 * @param alarm 등록될 알람 정보
	 */
	void emsAlarmInsert(HashMap<String, String> alarm);

	/**
	 * 확인되지 않은 알람 리스트
	 * @param nowDate 현재 시간 정보
	 * @return 미확인 알람 리스트
	 */
	List<HashMap<String, Object>> getAlarmList(String nowDate);

	/**
	 * 확인된 알람 정보
	 * @param alarm 확인표시 될 알람 정보
	 */
	void checkAlarm(HashMap<String, Object> alarm);

	/**
	 * 알람에서 확인될 현재 피크 값
	 * @param nowDate 현재 시간 정보
	 * @return 현재 전체 전력 피크 값
	 */
	Double alarmNowPeak(String nowDate);

	/**
	 * 알람 생성 허용 값
	 * @return 앎람 생성 유무 값
	 */
	int prdctAlarmUse();

	/**
	 * 알람 Flag 값 변경
	 * @param msg 메세지 값
	 */
	void updateAlarmPrdctData(String msg);

	/**
	 * 동일 알람 확인
	 * @param alarm 알람 정보
	 * @return 동일 알람 갯수
	 */
	int alarmCheck(HashMap<String, Object> alarm);

	void checkAllAlarm();
}
