package kr.co.mindone.ems.config.response;
/**
 * packageName    : kr.co.mindone.config
 * fileName       : ResponseObject
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import lombok.Getter;
import lombok.Setter;

/**
 * 정상 응답시
 * 데이터 및 코드, 메시지 송출 객체
 */
@Setter
@Getter
public class ResponseObject<O> {
	private int code;
	private String message;
	private O data;
}
