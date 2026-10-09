package kr.co.mindone.ems.config.base;
/**
 * packageName    : kr.co.mindone.ems.config.base
 * fileName       : BaseController
 * date           : 24. 9. 23.
 * description    : 모든 컨트롤러의 기본 동작을 제공하는 추상 클래스
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        -            최초 생성
 */
import kr.co.mindone.ems.config.response.ResponseObject;

public abstract class BaseController {
	/**
	 * 파일을 나타내는 상수
	 */
	public final static String file = "file";

	/**
	 * 멀티파트 폼 데이터를 나타내는 상수
	 */
	public final static String multiFile = "multipart/form-data";
	protected <T> ResponseObject<T> makeSuccessObj(String message, T data) {
		// 코드가 없는 경우 기본값 200 사용
		return makeSuccessObj(200, message, data);
	}
	/**
	 * 응답 객체를 생성하는 메서드
	 *
	 * @param message 응답 메시지
	 * @param data 응답 데이터
	 * @param <T> 응답 데이터의 타입
	 * @return 성공 응답 객체
	 */
	protected <T> ResponseObject<T> makeSuccessObj(int code, String message, T data) {
		ResponseObject<T> responseObject = new ResponseObject<>();
		responseObject.setCode(code); // 주어진 코드 사용
		responseObject.setMessage(message);
		responseObject.setData(data);
		return responseObject;
	}

}

