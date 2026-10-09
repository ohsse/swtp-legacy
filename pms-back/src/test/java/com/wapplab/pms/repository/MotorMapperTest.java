package com.wapplab.pms.repository;

import com.wapplab.pms.config.MybatisAndDb;
import com.wapplab.pms.web.common.DateForm;
import com.wapplab.pms.web.common.RequestForm;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

@MybatisAndDb
class MotorMapperTest {

    @Autowired
    private MotorMapper motorMapper;

    RequestForm motorForm = new RequestForm("motor_01", "2021-10-22 10:00:00",
        "2021-10-23 10:00:00");
    RequestForm scadaForm = new RequestForm("pump_scada_01", "2021-10-22 10:00:00",
        "2021-10-23 10:00:00");
    DateForm dateForm = new DateForm("2021-10-22 10:00:00", "2021-10-23 10:00:00");

    @Test
    void 송수펌프모터_알람() {
        motorMapper.alarm(1);
    }

    @Test
    void 송수펌프모터_가동중_조회() {
        motorMapper.runningInfo(1);
    }

//    @Test
//    void 분포도() {
//        motorMapper.distribution(scadaForm);
//    }

//    @Test
//    void 송수펌프모터_총진동량_조회_모든모터_그래프() {
//        motorMapper.vibrationGraph(dateForm);
//    }
/*
    @Test
    void 송수펌프모터_총진동량_조회_모든모터_값() {
        motorMapper.vibrationValues();
    }

    @Test
    void 총진동량_기간으로_조회() {
        motorMapper.vibrationFindById(motorForm);
    }

    @Test
    void 송수펌프모터_알람_상세화면() {
        motorMapper.alarmDetails();
    }

    @Test
    void 토출_흡입압력_조회() {
        motorMapper.scadaInfo();
    }

    @Test
    void 모터_상세_정보() {
        motorMapper.motorDetails(motorForm);
    }

    @Test
    void 모터_베어링_온도() {
        motorMapper.bearingTempInfo(scadaForm);
    }

    @Test
    void 모터_권선_온도() {
        motorMapper.windingTempInfo(scadaForm);
    }

    @Test
    void 유량_압력_상태_정보() {
        motorMapper.flowPressure("pump_scada_01");
    }*/
}