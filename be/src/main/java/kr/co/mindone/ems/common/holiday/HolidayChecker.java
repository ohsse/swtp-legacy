package kr.co.mindone.ems.common.holiday;
/**
 * packageName    : kr.co.mindone.common.holiday
 * fileName       : HolidayChecker
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import com.ibm.icu.util.ChineseCalendar;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;
import java.util.stream.Collectors;

public class HolidayChecker {
	/**
	 * 설정된 공휴일 리스트 생성
	 * @return 공휴일 리스트
	 */
	private List<LocalDate> getHolidayList() {
		List<LocalDate> holidayList = new ArrayList<>();
		int year = LocalDate.now().getYear();

		Holiday[] holidays = Holiday.values();
		for (Holiday holiday : holidays) {
			if (holiday.isSunTypeCalendar()) { // 양력인 공휴일
				LocalDate localDate = LocalDate.of(year, holiday.getMonth(), holiday.getDay());

				// 공휴일을 추가
				holidayList.add(localDate);
			} else { // 음력인 공휴일
				LocalDate mainHoliday = transferToSunCalendarTypeDate(year, holiday);
				holidayList.add(mainHoliday);

				if (holiday != Holiday.BUDDHA_COMING_DAY) { // 석가탄신일이 아닌 경우에만 앞뒤 날 추가
					LocalDate plusOneMainHoliday = mainHoliday.plusDays(1);
					LocalDate minusOneMainHoliday = mainHoliday.minusDays(1);

					// 공휴일을 추가
					holidayList.add(plusOneMainHoliday);
					holidayList.add(minusOneMainHoliday);
				}
			}
		}

		return holidayList.stream().sorted().collect(Collectors.toList());
	}

	/**
	 * 양력 날짜 음력 변환
	 * @param year 년
	 * @param holiday 변환 날짜
	 * @return 음력 날짜
	 */
	private LocalDate transferToSunCalendarTypeDate(int year, Holiday holiday) {
		ChineseCalendar cc = new ChineseCalendar();
		Calendar cal = Calendar.getInstance();
		cc.set(ChineseCalendar.EXTENDED_YEAR, year + 2637);
		cc.set(ChineseCalendar.MONTH, holiday.getMonth() - 1);
		cc.set(ChineseCalendar.DAY_OF_MONTH, holiday.getDay());

		cal.setTimeInMillis(cc.getTimeInMillis());

		return LocalDate.ofInstant(cal.toInstant(), ZoneId.systemDefault());
	}

	/**
	 * 공휴일 체크
	 * @param dateStr 날짜 String
	 * @return 공휴일 Boolean 값
	 */
	public boolean isPassDay(String dateStr) {
		DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
		LocalDate dateTime = LocalDate.parse(dateStr, formatter);
		DayOfWeek dayOfWeek = dateTime.getDayOfWeek();

		HolidayChecker holidayChecker = new HolidayChecker();
		List<LocalDate> holidayList = holidayChecker.getHolidayList();
		return holidayList.contains(dateTime);
	}
}
