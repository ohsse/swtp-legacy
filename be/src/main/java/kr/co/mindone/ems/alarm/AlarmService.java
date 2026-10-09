package kr.co.mindone.ems.alarm;
/**
 * packageName    : kr.co.mindone.alarm
 * fileName       : AlarmService
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import kr.co.mindone.ems.ai.AiService;
import kr.co.mindone.ems.energy.EnerSpendMapper;
import kr.co.mindone.ems.setting.SettingMapper;
import org.apache.ibatis.annotations.Case;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import javax.management.ObjectName;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class AlarmService {
	@Autowired
	private AlarmMapper alarmMapper;
	@Autowired
	private SettingMapper settingMapper;
	@Autowired
	private EnerSpendMapper enerSpendMapper;
	@Autowired
	private AiService aiService;
	public static final String LOCALHOST;
	public static final String EMSPORT = ":10013";

	/**
	 * 알람 이동 url
	 */
	static {
		InetAddress localhost;
		try {
			localhost = InetAddress.getLocalHost();
		} catch (UnknownHostException e) {
			localhost = null;
			e.printStackTrace();
		}
		LOCALHOST = "http://" + localhost.getHostAddress() + EMSPORT;
	}

	/**
	 * 알람 생성 스케쥴링
	 */
	@Scheduled(cron = "30 * * * * ?")
	public void peakAlarm() {
		String url = "/PowerPeakAnalysis";

		ZoneId koreaZoneId = ZoneId.of("Asia/Seoul");
		ZonedDateTime koreaZonedDateTime = ZonedDateTime.now(koreaZoneId);
		int currentHour = koreaZonedDateTime.getHour();
		int currentMinute = koreaZonedDateTime.getMinute();
		if (currentMinute == 0 && currentHour == 0) {
			alarmMapper.updateAlarmPrdctData(null);
		}
		// Define the desired date-time format
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:00");
		DateTimeFormatter formatterDate = DateTimeFormatter.ofPattern("yyyy-MM-dd");
		// Format the ZonedDateTime using the formatter
		String formattedDateTime = koreaZonedDateTime.format(formatter);
		String formattedDate = koreaZonedDateTime.format(formatterDate);
		HashMap < String, Object > nowDateMap = new HashMap < > ();
		nowDateMap.put("date", formattedDate);
		//매 분마다
		List < HashMap < String, Object >> peakGoal = settingMapper.selectPeakGoal();
		String peakGoalStringValue = (String) peakGoal.get(0).get("value");

		//전력 알람 링크
		String pathLink = LOCALHOST + url;

		int peakGoalValue;
		try {
			peakGoalValue = Integer.parseInt(peakGoalStringValue);
		} catch (NumberFormatException e) {
			System.err.println("String을 int로 변환하는데 실패했습니다.");
			return;
		}

		//현재 시간
		LocalTime now = LocalTime.now();
		//		int minute = now.getMinute();
		int minute = koreaZonedDateTime.getMinute(); //매 분마다 목표피크 비교
		Double nowPeak = alarmMapper.alarmNowPeak(formattedDateTime);
		if (nowPeak != null) {
			if (peakGoalValue != 0) {
				List < HashMap < String, Object >> prdctList = aiService.pumpPrdctSelectList(nowDateMap);
				int prdctAlarmUse = alarmMapper.prdctAlarmUse();
				if (peakGoalValue < nowPeak) {
					String msg = "전력이 목표 피크치를 초과했습니다.";
					HashMap < String, String > alarmMsg = new HashMap < > ();
					alarmMsg.put("msg", msg);
					alarmMsg.put("nowDate", formattedDateTime);
					alarmMsg.put("link", pathLink);
					//					emsAlarmInsert(alarmMsg);
				}

				if (prdctAlarmUse == 1 && prdctList.size() > 7) {
					prdctList.subList(0, 6).clear();
					for (HashMap < String, Object > map: prdctList) {
						if (map.get("PEAK_YN").equals("Y")) {
							String msg = "예상전력이 " + map.get("DATE") + "에 목표피크를 초과합니다.";
							HashMap < String, String > alarmMsg = new HashMap < > ();
							alarmMsg.put("alr_typ", "PEAK");
							alarmMsg.put("msg", msg);
							alarmMsg.put("nowDate", formattedDateTime);
							alarmMsg.put("link", pathLink);
							emsAlarmInsert(alarmMsg);
							break;
						}
					}
				}
			}
		}
		if (minute == 0) {
			//한시간 뒤 예측 전력
			nowDateMap.put("type", "hour");
			Double hourPrdctPeak = alarmMapper.prdctPeak(nowDateMap);
			if (hourPrdctPeak != null) {

				if (peakGoalValue < hourPrdctPeak) {
					String msg = "1시간 후 예상전력이 목표 피크치를 초과합니다.";
					HashMap < String, String > alarmMsg = new HashMap < > ();
					alarmMsg.put("msg", msg);
					alarmMsg.put("nowDate", formattedDateTime);
					alarmMsg.put("link", pathLink);
					//					emsAlarmInsert(alarmMsg);
				}

			}

		} else if (minute == 50) {
			//10분 뒤 예측 전력
			nowDateMap.put("type", "minute");
			Double minute10PrdctPeak = alarmMapper.prdctPeak(nowDateMap);
			if (minute10PrdctPeak != null) {
				if (peakGoalValue < minute10PrdctPeak) {
					String msg = "10분후 예상전력이 목표 피크치를 초과합니다.";
					HashMap < String, String > alarmMsg = new HashMap < > ();
					alarmMsg.put("msg", msg);
					alarmMsg.put("nowDate", formattedDateTime);
					alarmMsg.put("link", pathLink);
					//					emsAlarmInsert(alarmMsg);
				}
			}

		}

	}

	/**
	 * 알람 Insert 메서드
	 * @param alarm 알람 정보
	 */
	public void emsAlarmInsert(HashMap < String, String > alarm) {
		alarmMapper.emsAlarmInsert(alarm);
	}

	/**
	 * 알람 호출 메서드
	 * @return 웹 전달 알람 데이터
	 */
	public List < HashMap < String, Object >> getAlarmList() {
		LocalDateTime currentTime = LocalDateTime.now();
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:00");
		String nowDate = currentTime.format(formatter);

		// 1단계: DB에서 모든 알람을 가져옵니다.
		List<HashMap<String, Object>> alarmListFromDB = alarmMapper.getAlarmList(nowDate);

		// 2단계: 'PEAK' 타입 알람의 메시지 중복을 제거합니다.
		Set<String> seenPeakMessages = new HashSet<>();
		List<HashMap<String, Object>> deduplicatedList = new ArrayList<>();
		for (HashMap<String, Object> alarm : alarmListFromDB) {
			String alarmType = (String) alarm.get("ALR_TYP");
			String message = (String) alarm.get("MSG");
			if ("PEAK".equals(alarmType)) {
				if (!seenPeakMessages.contains(message)) {
					deduplicatedList.add(alarm);
					seenPeakMessages.add(message);
				}
			} else {
				deduplicatedList.add(alarm);
			}
		}

		// --- 여기에 기존 'alarmCheck' 로직을 적용합니다 ---
		// 3단계: 중복 제거된 목록을 대상으로 '실시간 유효성'을 검증하고 최종 목록을 만듭니다.
		if (deduplicatedList.isEmpty()) {
			return deduplicatedList;
		}

		List<HashMap<String, Object>> finalList = new ArrayList<>(deduplicatedList);
		List<HashMap<String, Object>> alarmsToRemove = new ArrayList<>();

		for (HashMap<String, Object> alarm : finalList) {
			alarm.put("nowDate", nowDate);
			int checkCnt = alarmMapper.alarmCheck(alarm);
			if (checkCnt != 0) {
				alarmsToRemove.add(alarm); // 제거할 알람을 별도 리스트에 추가
				alarmMapper.updateAlarmPrdctData((String) alarm.get("MSG"));
			}
		}

		// 루프가 끝난 후, 유효하지 않은 알람들을 한 번에 제거
		if (!alarmsToRemove.isEmpty()) {
			finalList.removeAll(alarmsToRemove);
		}

		return finalList;
	}

	/**
	 * 알람 확인 메서드
	 * @param alarm 확인된 알람 정보
	 */
	public void checkAlarm(HashMap < String, Object > alarm) {
		alarmMapper.checkAlarm(alarm);
	}

	/**
	 * 펌프 모드에 따른 알람 생성 메서드
	 * @param modeType 모드에 따른 Insert 될 알람 정보
	 */
	public void modeAlarmCreate(int modeType) {
		String url = "/PumpControlDetailed";
		String pathLink = LOCALHOST + url;
		HashMap < String, String > alarmMsg = new HashMap < > ();
		alarmMsg.put("alr_type", "PUMP");
		if (modeType == 0) {
			String msg = "펌프 반자동상태 입니다.";
			alarmMsg.put("msg", msg);

		} else if (modeType == 1) {
			String msg = "펌프 자동상태 입니다.";
			alarmMsg.put("msg", msg);
		}
		alarmMsg.put("link", pathLink);
		emsAlarmInsert(alarmMsg);
	}

	/**
	 * 미확인 알람 FLAG 변경 처리 1->3
	 */
	@Scheduled(cron = "0 0 * * * ?")
	public void checkAlarmHour() {
		alarmMapper.checkAllAlarm();
	}
}