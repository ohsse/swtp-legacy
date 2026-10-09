package kr.co.mindone.ems.alarm;
/**
 * packageName    : kr.co.mindone.alarm
 * fileName       : AlarmController
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import io.swagger.annotations.Api;
import io.swagger.v3.oas.annotations.Operation;
import kr.co.mindone.ems.config.base.BaseController;
import kr.co.mindone.ems.config.response.ResponseMessage;
import kr.co.mindone.ems.config.response.ResponseObject;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;

@Slf4j
@Api(tags = "AlarmSystem")
@RequestMapping("alarm")
@RestController
public class AlarmController extends BaseController {
	@Autowired
	private AlarmService alarmService;

	/**
	 * 미확인 알람 리스트 반환 API
	 * @return 확인되지 않은 알람 정보
	 */
	@Operation(summary = "미확인 알람 리스트 호출", description = "alarm/getAlarmList")
	@GetMapping("/getAlarmList")
	public ResponseObject<List<HashMap<String, Object>>> getAlarmList(){
		//web 조회 사용 service
		String webCall = "1";
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, alarmService.getAlarmList());
	}

	/**
	 * 확인된 알람 정보
	 * @param alarm 확인된 알람 정보
	 * @return 전송 완료 메세지
	 */
	@Operation(summary = "확인 알람 update", description = "alarm/checkAlarm")
	@PostMapping("/checkAlarm")
	public ResponseObject<String> checkAlarm(@RequestBody HashMap<String, Object> alarm){
		//web 조회시 업데이트 될 flag 값
		alarm.put("flag", "2");
		alarmService.checkAlarm(alarm);
		return makeSuccessObj(ResponseMessage.SAVE_SUCCESS, "알람 확인 완료");
	}

	/**
	 * 펌프 모드 변경 알람 등록
	 * @param modeType 모드 정보
	 * @return 전송 완료 메세지
	 */
	@Operation(summary = "펌프 모드 변경시 알람 등록 API(0:반자동, 1:자동)", description = "alarm/modeAlarmCreate?modeType = 0")
	@GetMapping("/modeAlarmCreate")
	public ResponseObject<String> modeAlarmCreate(@RequestParam int modeType){
		alarmService.modeAlarmCreate(modeType);
		return makeSuccessObj(ResponseMessage.SAVE_SUCCESS, "알람 등록 완료");
	}
}
