package com.wapplab.pms.web.common;

import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

@Getter
@Setter
@ToString
public class ScadaDto {
    public String PUMP_SCADA_ID;
    public String CENTER_ID = "gosan";
    public String ACQ_DATE;
    public int EQ_ON = -1;
    public float FREQUENCY = -1;
    public float FLOW_RATE = -1;
    public float PRESSURE = -1;
    public float R_TEMP = -1;
    public float S_TEMP = -1;
    public float T_TEMP = -1;
    public float BRG_MOTOR_DE_TEMP = -1;
    public float BRG_MOTOR_NDE_TEMP = -1;
    public float BRG_PUMP_DE_TEMP = -1;
    public float BRG_PUMP_NDE_TEMP = -1;
    public float DISCHARGE_PRESSURE = -1;
    public float SUCTION_PRESSURE = -1;
    public int tryCount = 0;
}