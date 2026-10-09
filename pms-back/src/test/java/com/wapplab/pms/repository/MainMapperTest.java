package com.wapplab.pms.repository;

import static org.junit.jupiter.api.Assertions.*;

import com.wapplab.pms.config.MybatisAndDb;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

@MybatisAndDb
class MainMapperTest {

    @Autowired
    private MainMapper mainMapper;

    @Test
    void motorDataAll() {
        mainMapper.motorDataAll(1);
    }

    @Test
    void pumpBearingTempAll() {
        mainMapper.pumpBearingTempAll(1);
    }

    @Test
    void motorAlarm() {
        mainMapper.motorAlarm(1);
    }

}