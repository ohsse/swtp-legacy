package kr.co.mindone.ems.epa;

import io.swagger.annotations.Api;
import io.swagger.v3.oas.annotations.Operation;
import kr.co.mindone.ems.config.base.BaseController;
import kr.co.mindone.ems.config.response.ResponseMessage;
import kr.co.mindone.ems.config.response.ResponseObject;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@Slf4j
@Api(tags = "EPA System")
@RequestMapping("epa")
@RestController
public class EpaController extends BaseController {
	@Autowired
	private EpaService epaService;

	@Operation(summary = "epa 펌프상태 확인", description = "epa/getEpaModeInfo")
	@GetMapping("/getEpaModeInfo")
	public ResponseObject<Integer> getEpaModeInfo(){
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, epaService.getEpaModeInfo());
	}

	@Operation(summary = "epa 모드 변경", description = "epa/setEpaMode")
	@PutMapping("/setEpaMode/{mode}")
	public ResponseObject<String> setEpaMode(@PathVariable int mode){
		epaService.setEpaMode(mode);

		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "ok");
	}
}
