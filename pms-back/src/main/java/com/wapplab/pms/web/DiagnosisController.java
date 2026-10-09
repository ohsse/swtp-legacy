package com.wapplab.pms.web;

import com.wapplab.pms.service.DiagnosisService;
import com.wapplab.pms.web.common.*;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;

import static com.wapplab.pms.web.common.Message.SUCCESS;
import static com.wapplab.pms.web.common.Message.ERROR;

@Api(tags = "정밀진단 화면 API")
@RestController
@RequestMapping("/api/v1/diagnosis")
@RequiredArgsConstructor
public class DiagnosisController {

    @Autowired
    private DiagnosisService diagnosisService;

    @GetMapping("/pumpList")
    @ApiOperation("정밀진단 펌프의 대상 센서조회")
    public ResponseEntity<ResponseDTO> selectPumpChannelList() {
        return ResponseEntity.ok(ResponseDTO.ok(Message.SUCCESS.getMessage(), diagnosisService.selectPumpChannelList()));
    }

    @PostMapping("/rms")
    @ApiOperation("rms 그래프 데이터 호출 {\"motor_id\":\"motor_o_1\", \"channel_nm\":\"PIV\", \"endDate\": \"2024-04-18 16:08:00\", \"startDate\": \"2024-04-16 16:08:00\"}")
    public ResponseEntity<ResponseDTO> selectRMSList(@RequestBody RMSForm rmsForm) {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), diagnosisService.selectRMSList(rmsForm)));
    }

    @PostMapping("/timewave")
    @ApiOperation("timewave 그래프 데이터 호출")
    public ResponseEntity<ResponseDTO> selectTimeWaveList(@RequestBody ChannelForm channelForm) {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), diagnosisService.selectTimeWaveList(channelForm)));
    }

    @PostMapping("/spectrum")
    @ApiOperation("spectrum 그래프 데이터 호출")
    public ResponseEntity<ResponseDTO> selectSpectrumList(@RequestBody ChannelForm channelForm) {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), diagnosisService.selectSpectrumList(channelForm)));
    }

    @PostMapping("/spectrumFreq")
    @ApiOperation("spectrum 1x 데이터 호출")
    public ResponseEntity<ResponseDTO> selectSpectrumFreqList(@RequestBody ChannelForm channelForm) {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), diagnosisService.selectSpectrumFreqList(channelForm)));
    }

    @PostMapping("/setting")
    @ApiOperation("설정 값 데이터 호출")
    public ResponseEntity<ResponseDTO> selectSettingParmList(@RequestBody SettingForm settingForm) {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), diagnosisService.selectSettingParmList(settingForm)));
    }

    @PostMapping("/updateSettingParm")
    @ApiOperation("설정 값 데이터 호출")
    public ResponseEntity<ResponseDTO> updateSettingParm(@RequestBody List<HashMap<String, String>> settingForms) {
        int result = diagnosisService.updateSettingParm(settingForms);
        if(result == 1)
        {
            return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), "SUCCESS"));
        }
        else {
            return ResponseEntity.ok(ResponseDTO.ok(ERROR.getMessage(),"ERROR" ));
        }
    }


}
