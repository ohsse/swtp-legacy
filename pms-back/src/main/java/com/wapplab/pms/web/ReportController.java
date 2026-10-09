package com.wapplab.pms.web;

import com.wapplab.pms.service.ReportControlService;
import com.wapplab.pms.web.common.DateForm;
import com.wapplab.pms.web.common.RequestForm;
import com.wapplab.pms.web.common.ResponseDTO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import static com.wapplab.pms.web.common.Message.SUCCESS;

@RestController
@RequiredArgsConstructor
@Api(tags = "알림/이력 API")
@RequestMapping("/api/v1/reportControl")
public class ReportController {

    private final ReportControlService reportControlService;

    @GetMapping("/alarmCount/{dateType}")
    @ApiOperation("알람 수 확인"
            + " dateType : all, week 로 구분")
    public ResponseEntity<ResponseDTO> totalAlarm(@PathVariable String dateType) {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), reportControlService.alarmCount(dateType)));
    }

    @PostMapping("/alarmList")
    @ApiOperation(value = "알람 목록")
    public ResponseEntity<ResponseDTO> alarmList(@RequestBody DateForm dateForm) {
        return ResponseEntity.ok(
          ResponseDTO.ok(SUCCESS.getMessage(), reportControlService.alarmList(dateForm)));
    }

}
