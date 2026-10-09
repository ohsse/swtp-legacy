package com.wapplab.pms.web;

import com.wapplab.pms.service.AlarmService;
import com.wapplab.pms.web.common.DateForm;
import com.wapplab.pms.web.common.ResponseDTO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;

import static com.wapplab.pms.web.common.Message.SUCCESS;

@Slf4j
@RestController
@RequiredArgsConstructor
@Api(tags = "통계이력 및 알람")
@RequestMapping("/api/v1/alarm")
public class AlarmContoller {
	@Autowired
	AlarmService alarmService;
	@GetMapping("/alarmStatusDefect")
	@ApiOperation("조회기간 기준 결함 별 알람 현황의 카운트 반환")
	public ResponseEntity<ResponseDTO> alarmStatusDefect(@RequestParam HashMap<String, Object> map) {
		return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), alarmService.alarmStatusDefect(map)));
	}

	@GetMapping("/weeklyAlarmTrend")
	@ApiOperation("조회기간 기준 일간 진단 알람 현황의 카운트 반환")
	public ResponseEntity<ResponseDTO> weeklyAlarmTrend(@RequestParam HashMap<String, Object> map) {

		return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), alarmService.weeklyAlarmTrend(map)));
	}
	@GetMapping("/alarmList")
	@ApiOperation("조회기간 기준 알람리스트 반환")
	public ResponseEntity<ResponseDTO> alarmList(@RequestParam HashMap<String, String> map) {
		return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), alarmService.alarmList(map)));
	}
}
