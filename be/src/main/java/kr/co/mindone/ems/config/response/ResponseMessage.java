package kr.co.mindone.ems.config.response;
/**
 * packageName    : kr.co.mindone.config
 * fileName       : ResponseMessage
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
public class ResponseMessage {
	/**
	 * 에러 메세지
	 * Common Error Code로 사용.
	 */
	public static final String BAD_REQUEST = "요청에 문제가 있습니다.";
	public static final String METHOD_NOT_ALLOWED = "허락되지 않은 요청 방법입니다.";
	public static final String UNSUPPORTED_MEDIA_TYPE = "요청하신 미디어 포맷은 제공하지 않습니다.";
	public static final String FORBIDDEN = "사용권한이 없습니다.";
	public static final String NOT_FOUND = "요청 URL이 존재하지 않습니다.";
	public static final String NO_CONTENT = "데이터가 존재하지 않습니다.";
	public static final String INTERNAL_SERVER_ERROR = "서버내부 오류입니다.";

	/**
	 * 로그인 관련
	 */
	public static final String USER_NOT_EXIST = "사용자가 존재하지 않습니다.";
	public static final String UNAUTHORIZED = "잘못된 토큰입니다.";//403
	public static final String EXPIRED_TOKEN = "완료된 토큰입니다.";//410
	public static final String USER_DISABLED = "사용할 수 없는 사용자입니다.";
	public static final String PASSWORD_NOT_CORRECT = "비밀번호가 일치하지 않습니다.";
	public static final String LOGIN_TRY_COUNT_LIMIT = "로그인 시도 횟수를 초과했습니다.";
	public static final String LOGIN_SUCCESS = "로그인에 성공했습니다.";
	public static final String LOGOUT_SUCCESS = "로그아웃 되었습니다.";
	public static final String LOGIN_INFO_NOT_CORRECT = "사용자 정보나 비밀번호가 올바르지 않습니다.";
	public static final String SESSION_INVALID = "세션이 종료되었습니다.";
	public static final String USER_HAD = "이미 존재하는 사용자입니다.";
	/**
	 * CUD 관련
	 */
	public static final String SELECT_SUCCESS = "정상적으로 조회되었습니다.";
	public static final String INSERT_SUCCESS = "정상적으로 등록되었습니다.";
	public static final String SAVE_SUCCESS	= "정상적으로 저장되었습니다.";
	public static final String DELETE_SUCCESS = "정상적으로 삭제되었습니다.";
	public static final String INSERT_FAILURE = "데이터를 등록하는데 문제가 발생했습니다.";
	public static final String SAVE_FAILURE = "데이터를 저장하는데 문제가 발생했습니다.";
	public static final String DELETE_FAILURE = "데이터를 삭제하는데 문제가 발생했습니다.";

	/**
	 * 엑셀파일 읽기 관련
	 */
	public static final String IMPORT_EXCEL_FAILURE = "사용할 수 있는 양식이 아닙니다.";
}
