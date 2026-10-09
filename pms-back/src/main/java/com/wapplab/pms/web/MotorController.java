package com.wapplab.pms.web;

import static com.wapplab.pms.web.common.Message.SUCCESS;

import com.wapplab.pms.service.MotorService;
import com.wapplab.pms.web.common.DateForm;
import com.wapplab.pms.web.common.PumpForm;
import com.wapplab.pms.web.common.RequestForm;
import com.wapplab.pms.web.common.ResponseDTO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;

@Slf4j
@RestController
@RequiredArgsConstructor
@Api(tags = "송수 펌프 모터 API")
@RequestMapping("/api/v1/motor")
public class MotorController {

    private final MotorService motorService;

    @PostMapping("/alarm")
    @ApiOperation("송수펌프모터 설비별 알람"
        + "알람이 있는 설비만 검색(위의 motor id 참조), 검색안된 설비는 정상")
    public ResponseEntity<ResponseDTO> alarm(@RequestBody RequestForm requestForm) {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), motorService.alarm(requestForm)));
    }

    @GetMapping("/alarmTemp")
    @ApiOperation("송수펌프모터 설비별 온도 알람"
        + "알람이 있는 설비만 검색(위의 motor id 참조), 검색안된 설비는 정상")
    public ResponseEntity<ResponseDTO> alarmTemp() {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), motorService.alarmTemp()));
    }

    @GetMapping("/runningInfo")
    @ApiOperation("가동중 조회")
    public ResponseEntity<ResponseDTO> runningInfo() {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), motorService.runningInfo()));
    }

    @PostMapping("/distribution")
    @ApiOperation("분포도 scadaId 필요 flow_rate : 토출"
        + " pressure : 흡입")
    public ResponseEntity<ResponseDTO> distribution(@RequestBody DateForm dateForm) {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), motorService.distribution(dateForm)));
    }

    @PostMapping("/vibrationGraph")
    @ApiOperation("총진동량 조회 모든 모터 한번에 조회 - 그래프"
        + " motor_de_amp : 모터 부하"
        + " motor_nde_amp : 모터 반부하"
        + " pump_de_amp : 펌프 부하"
        + " pump_nde_amp : 펌프 반부하")
    public ResponseEntity<ResponseDTO> totalVibrationAll(@RequestBody DateForm dateForm) {
        return ResponseEntity.ok(
            ResponseDTO.ok(SUCCESS.getMessage(), motorService.vibrationGraph(dateForm)));
    }

    @GetMapping("/flowPressure")
    @ApiOperation("상태정보 - 유량, 압력"
        + " pump_scada_01 : 평택"
        + " flow_rate : 토출"
        + " pressure : 흡입")
    public ResponseEntity<ResponseDTO> flowPressure() {
        return ResponseEntity.ok(ResponseDTO.ok(SUCCESS.getMessage(), motorService.flowPressure()));
    }

    @PostMapping("/motorDetails")
    @ApiOperation("모터 부하 총진동량, 모터 반부하 총진동량 ~ 펌프 반부하 총진동량"
        + "m.DE_rms_amp : 모터 부하 총진동량"
        + " m.NDE_rms_amp : 모터 반 부하 총진동량"
        + " m.misalignment_amp : 모터 축정렬"
        + " m.unbalance_amp : 모터 불평형"
        + " m.rotor_amp : 모터 회전자"
        + " m.de_amp : 모터 부하 베어링"
        + " m.NDE_amp : 모터 반부하 베어링"
        + " p.DE_rms_amp : 펌프 부하 총진동량"
        + " p.NDE_rms_amp : 펌프 반 부하 총진동량"
        + " p.cavitation_amp : 펌프 케비테이션"
        + " p.impeller_amp : 펌프 임펠러"
        + " p.DE_amp : 펌프 부하 베어링"
        + " p.NDE_amp : 펌프 반부하 베어링")
    public ResponseEntity<ResponseDTO> motorDetails(@RequestBody RequestForm requestForm) {
        return ResponseEntity.ok(
            ResponseDTO.ok(SUCCESS.getMessage(), motorService.motorDetails(requestForm)));
    }

    @PostMapping("/bearingTempInfo")
    @ApiOperation("모터 베어링 온도 scadaId 필요")
    public ResponseEntity<ResponseDTO> bearingTempInfo(@RequestBody RequestForm requestForm) {
        return ResponseEntity.ok(
            ResponseDTO.ok(SUCCESS.getMessage(), motorService.bearingTempInfo(requestForm)));
    }

    @PostMapping("/windingTempInfo")
    @ApiOperation("모터 권선 온도 scadaId 필요")
    public ResponseEntity<ResponseDTO> windingTempInfo(@RequestBody RequestForm requestForm) {
        return ResponseEntity.ok(
            ResponseDTO.ok(SUCCESS.getMessage(), motorService.windingTempInfo(requestForm)));
    }


    @GetMapping("/dstrbChart")
    @ApiOperation("분포도 JSON 데이터 계통 순번순으로 출력")
    public ResponseEntity<ResponseDTO> dstrbChart(){
        return ResponseEntity.ok(
                ResponseDTO.ok(SUCCESS.getMessage(), motorService.dstrbChart())
        );
    }

    @PostMapping("/selectPumpDstrb/{pump_id}")
    @ApiOperation("json")
    public ResponseEntity<ResponseDTO> selectPumpDstrb(@PathVariable String pump_id) {
       return ResponseEntity.ok(
           ResponseDTO.ok(SUCCESS.getMessage(), motorService.selectPumpDstrb(pump_id)));
   }

    @GetMapping("/selectGraphThreshold")
    @ApiOperation("그래프 임계값 출력")
    public ResponseEntity<ResponseDTO> selectGraphThreshold(){
        return ResponseEntity.ok(
                ResponseDTO.ok(SUCCESS.getMessage(), motorService.selectGraphThreshold())
        );
    }


}
