package com.wapplab.pms.web;

import com.wapplab.pms.service.CommonService;
import com.wapplab.pms.service.MainService;
import com.wapplab.pms.web.common.Message;
import com.wapplab.pms.web.common.ResponseDTO;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;

@Api(tags = "메인 화면 API")
@RestController
@RequestMapping("/api/v1/main")
@RequiredArgsConstructor
public class MainController {

    @Autowired
    private MainService mainService;
    @Autowired
    private CommonService commonService;


    @GetMapping("motorDataAll")
    @ApiOperation("자율진단 송수펌프모터 펌프 부하, 반부하, 모터의 부하, 반부하 총 진동값")
    public ResponseEntity<ResponseDTO> motorDataAll() {
        return ResponseEntity.ok(ResponseDTO.ok(Message.SUCCESS.getMessage(), mainService.motorDataAll()));
    }

    @GetMapping("pumpBearingAll")
    @ApiOperation("송수펌프모터 베어링 온도")
    public ResponseEntity<ResponseDTO> pumpBearingTempAll() {
        return ResponseEntity.ok(ResponseDTO.ok(Message.SUCCESS.getMessage(), mainService.pumpBearingTempAll()));
    }

    @GetMapping("motorAlarm")
    @ApiOperation("송수펌프모터 알람")
    public ResponseEntity<ResponseDTO> motorAlarm() {
        return ResponseEntity.ok(ResponseDTO.ok(Message.SUCCESS.getMessage(), mainService.motorAlarm()));
    }


    @GetMapping("getPumpInf")
    @ApiOperation("펌프 정보 조회")
    public ResponseEntity<ResponseDTO> getPumpInf() {
        return ResponseEntity.ok(ResponseDTO.ok(Message.SUCCESS.getMessage(), mainService.getPumpInf()));
    }

    @GetMapping("getAllFacStats")
    @ApiOperation("장비 현황")
    public ResponseEntity<ResponseDTO> getAllFacStats() {
        return ResponseEntity.ok(ResponseDTO.ok(Message.SUCCESS.getMessage(), mainService.getAllFacStats()));
    }

    @GetMapping("kafkaTagList")
    @ApiOperation("카프카사용 태그리스트 호출")
    public ResponseEntity<ResponseDTO> kafkaTagList(){
        return ResponseEntity.ok(ResponseDTO.ok(Message.SUCCESS.getMessage(), commonService.kafkaTagList()));
    }


}
