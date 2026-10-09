package kr.co.mindone.ems.common.holiday;
/**
 * packageName    : kr.co.mindone.common.holiday
 * fileName       : Holiday
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import lombok.Getter;

@Getter
public enum Holiday {
	/**
	 * 공휴일 날짜 지정
	 * 양력, 음력 구분
	 */
	NEW_YEAR_DAY(CalendarType.SUN, 1, 1),             //신정
	THREE_ONE_DAY(CalendarType.SUN, 3, 1),             //삼일절 - 대체 공휴일: 토요일, 일요일
	CHILDREN_DAY(CalendarType.SUN, 5, 5),              //어린이날 - 대체 공휴일: 토요일, 일요일
	MEMORIAL_DAY(CalendarType.SUN, 6, 6),             //현충일
	NATIONAL_LIBERATION_DAY(CalendarType.SUN, 8, 15),  //광복절 - 대체 공휴일: 토요일, 일요일
	NATIONAL_FOUNDATION_DAY(CalendarType.SUN, 10, 3),  //개천절 - 대체 공휴일: 토요일, 일요일
	HANGUL_DAY(CalendarType.SUN, 10, 9),               //한글날 - 대체 공휴일: 토요일, 일요일
	CHRISTMAS_DAY(CalendarType.SUN, 12, 25),          //크리스마스
	MOON_NEW_YEAR_DAY(CalendarType.MOON, 1, 1),        //설날 - 대체 공휴일: 일요일
	BUDDHA_COMING_DAY(CalendarType.MOON, 4, 8),       //부처님 오신날
	THANKSGIVING_DAY(CalendarType.MOON, 8, 15);

	private CalendarType calendarType;
	private int month;
	private int day;

	/**
	 * 날짜에 따른 공휴일 생성자
	 * @param calendarType 양력 음력 구분
	 * @param month 월
	 * @param day 일
	 */
	Holiday(CalendarType calendarType, int month, int day) {
		this.calendarType = calendarType;
		this.month = month;
		this.day = day;
	}

	/**
	 * 양력 부분
	 * @return 타입
	 */
	public boolean isSunTypeCalendar() {
		return this.calendarType == CalendarType.SUN;
	}
}
