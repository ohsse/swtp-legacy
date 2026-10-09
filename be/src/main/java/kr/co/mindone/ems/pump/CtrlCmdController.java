package kr.co.mindone.ems.pump;

import io.swagger.annotations.Api;
import kr.co.mindone.ems.config.base.BaseController;
import kr.co.mindone.ems.config.response.ResponseMessage;
import kr.co.mindone.ems.config.response.ResponseObject;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;

/**
 * 군산 5분 제어 판단의 화면 표출·승인 API.
 * 응답 본문 code: 200 성공 / 409 이미 처리·만료·모드 불일치·대기열 사용 중 / 422 게이트 탈락.
 */
@Api(tags = "CtrlCmd")
@RestController
@RequestMapping("ai/ctrl")
public class CtrlCmdController extends BaseController {

    @Autowired
    private CtrlCmdService ctrlCmdService;

    /** 최신 판단 1건 + 장치별 진행 상태 */
    @GetMapping("/latest")
    public ResponseObject<HashMap<String, Object>> latest() {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, ctrlCmdService.latest());
    }

    /** 승인 대기 목록 + 진행 중 대기열 수 */
    @GetMapping("/pending")
    public ResponseObject<HashMap<String, Object>> pending() {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, ctrlCmdService.pending());
    }

    /** 승인: {ctrlId, device, userId} */
    @PostMapping("/approve")
    public ResponseObject<HashMap<String, Object>> approve(@RequestBody HashMap<String, Object> body) {
        Long ctrlId = parseCtrlId(body);
        if (ctrlId == null) {
            return makeSuccessObj(409, "판단 번호(ctrlId)가 없거나 형식이 올바르지 않습니다.", null);
        }
        CtrlCmdService.Outcome o = ctrlCmdService.processDevice(
                ctrlId,
                String.valueOf(body.get("device")),
                true,
                body.get("userId") == null ? null : String.valueOf(body.get("userId")));
        return makeSuccessObj(codeOf(o), o.message, o.toMap());
    }

    /** 거절: {ctrlId, device, userId} */
    @PostMapping("/reject")
    public ResponseObject<HashMap<String, Object>> reject(@RequestBody HashMap<String, Object> body) {
        Long ctrlId = parseCtrlId(body);
        if (ctrlId == null) {
            return makeSuccessObj(409, "판단 번호(ctrlId)가 없거나 형식이 올바르지 않습니다.", null);
        }
        CtrlCmdService.Outcome o = ctrlCmdService.reject(
                ctrlId,
                String.valueOf(body.get("device")),
                body.get("userId") == null ? null : String.valueOf(body.get("userId")));
        return makeSuccessObj(codeOf(o), o.message, o.toMap());
    }

    /** 판단 이력: from, to (yyyy-MM-dd HH:mm:ss), cmdOnly=Y 면 명령 있는 행만 */
    @GetMapping("/history")
    public ResponseObject<List<HashMap<String, Object>>> history(@RequestParam String from,
                                                                  @RequestParam String to,
                                                                  @RequestParam(required = false, defaultValue = "N") String cmdOnly) {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, ctrlCmdService.history(from, to, "Y".equals(cmdOnly)));
    }

    private static Long parseCtrlId(HashMap<String, Object> body) {
        Object v = body == null ? null : body.get("ctrlId");
        if (v == null) {
            return null;
        }
        try {
            return Long.parseLong(v.toString().trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static int codeOf(CtrlCmdService.Outcome o) {
        switch (o.code) {
            case "ENQUEUED":
                return 200;
            case CtrlCmdService.REJECTED:
                return "USER_REJECT".equals(o.reason) ? 200 : 422;
            case CtrlCmdService.EXPIRED:
                return 422;
            default:
                return 409;
        }
    }
}
