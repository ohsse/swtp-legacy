import axios from "axios";
import PTK from "@/assets/data/PTK.json";
import SSN from "@/assets/data/SSN.json";
import sampleData from "@/assets/data/sample.json";
import ModelListClass from "@/views/PumpControl/ModelListClass.js";
import store from '@/store';

const monitor1 = {
    namespaced: true,
    state: {
        selectModel: '송수펌프모터',
        flag: true,
        alarmFlag: true,
        modelList: [],
        alarmList: {},
        detailData: {
            motor_de_rms_amp: [],
            motor_nde_rms_amp: [],
            motor_misalignment_amp: [],
            motor_unbalance_amp: [],
            motor_rotor_amp: [],
            motor_de_amp: [],
            motor_nde_amp: [],
            pump_de_rms_amp: [],
            pump_nde_rms_amp: [],
            pump_cavatation_amp: [],
            pump_impeller_amp: [],
            pump_de_amp: [],
            pump_nde_amp: [],
            //이름 필요
            P_NDE_bearing_temp: [],
            P_DE_bearing_temp: [],
            M_NDE_bearing_temp: [],
            M_DE_bearing_temp: [],
            //wind 필요
            winding_tempR: [],
            winding_tempT: [],
            winding_tempS: [],
            flag: true
        },
        id: "motor_o_1",
        scada_id: "pump_scada_01",
        // startDate: '',
        // endDate: '',
        startDate: "2023-10-21 10:00:00",
        endDate: "2021-10-30 16:00:00",
        pickDate: {
            from: 0,
            to: 0,
        },
        searchDate: false,
        scada_01: {
            flow_rate_val: 0,
            pressure_val: 0,
            data: [],
            running: 0,
            comp: PTK,
            flow_rate: [],
            pressure: [],
        },
        scada_05: {
            flow_rate_val: 0,
            pressure_val: 0,
            data: [],
            running: 0,
            comp: SSN,
            flow_rate: [],
            pressure: [],
        },
        sampleData: {
            motor_de_rms_amp: [],
            motor_nde_rms_amp: [],
            pump_de_rms_amp: [],
            pump_nde_rms_amp: [],
            motor: [],
            idx: "1",
        },
        mode: false,
    },
    getters: {
    },
    mutations: {
        setPumpList(state, payload) {
            const { datas, select, datas2 } = payload;
            state.modelList = [];
            const organizedData = {};

            datas.forEach((group) => {
                group.forEach((item, index) => {
                    const { grp_idx, grp_nm, motor_id } = item;
                    let modifiedMotorId;
                    const scada_id = motor_id.replace("motor", "pump_scada");
                    // motor_id 패턴에 따라 변경
                    if (item.grp_nm == "(신)송수펌프동") {
                        modifiedMotorId = `motor_n_${index + 1}`;
                    } else if (item.grp_nm == "(구)송수펌프동") {
                        modifiedMotorId = `motor_o_${index + 1}`;
                    } else {
                        modifiedMotorId = motor_id
                    }

                    let motor_name
                    if (store.state.area == 'gosan' || store.state.area == 'gumi') {
                        motor_name = `${grp_nm} 송수펌프모터 #${index + 1}`;
                    } else {
                        motor_name = `${grp_nm} 가압펌프 #${index + 1}`;
                    }

                    if (!organizedData[grp_idx]) {
                        organizedData[grp_idx] = [];
                    }
                    organizedData[grp_idx].push({ motor_name, motor_id: modifiedMotorId, scada_id });
                    // console.log("organizedData[grp_idx]", organizedData[grp_idx]);
                });
            });


            const organizedDataArray = Object.values(organizedData);
            let idx = 0
            // let isNewMotorProcessed = false; 
            organizedDataArray.forEach((item, i) => {
                state.modelList[i] = [];
                item.forEach((element, j) => {
                    // 고산 gosan 정수장 하나의 목록으로 나오도록 수정 
                    state.modelList[i][j] = new ModelListClass(element.motor_name, element.motor_id, element.scada_id, datas2, idx++)
                    // if(store.state.area == 'gosan'){
                    //     if (element.motor_name.includes("(구)")) {
                    //         const modelInstance = new ModelListClass(element.motor_name, element.motor_id, element.scada_id, datas2, idx++);
                    //         state.modelList[0].push(modelInstance); 
                    //     } else if(element.motor_name.includes("(신)")) {
                    //         if (!isNewMotorProcessed) {
                    //             idx = 7; 
                    //             isNewMotorProcessed = true; 
                    //         }
                    //         const modelInstance = new ModelListClass(element.motor_name, element.motor_id, element.scada_id, datas2, idx++);
                    //         state.modelList[0].push(modelInstance); 
                    //     }
                    // } else {
                    //     const modelInstance = new ModelListClass(element.motor_name, element.motor_id, element.scada_id, datas2, idx++);
                    //     state.modelList[0].push(modelInstance); 
                    // }
                })
            })
            if (select != undefined) {
                state.modelList.forEach(element => {
                    element.map((x) => (x.select = false));
                });
                state.modelList.forEach(element => {
                    element.forEach(item => {
                        if (item.id == select) {
                            item.select = true
                        }
                    })
                })
            }
        },
        bearingTempInfo(state, data) {
            state.detailData.P_NDE_bearing_temp = [];
            state.detailData.M_NDE_bearing_temp = [];
            state.detailData.M_DE_bearing_temp = [];
            state.detailData.P_DE_bearing_temp = [];
            let P_NDE_bearing_temp = [];
            let M_NDE_bearing_temp = [];
            let M_DE_bearing_temp = [];
            let P_DE_bearing_temp = [];
            let bearingDatas = data[0].datas;
            for (let i = 0; i < bearingDatas.length; i++) {
                // let date = new Date(bearingDatas[i].acq_date);
                P_NDE_bearing_temp.push([bearingDatas[i].acq_date, bearingDatas[i].P_NDE_bearing_temp]);
                M_NDE_bearing_temp.push([bearingDatas[i].acq_date, bearingDatas[i].M_NDE_bearing_temp]);
                M_DE_bearing_temp.push([bearingDatas[i].acq_date, bearingDatas[i].M_DE_bearing_temp]);
                P_DE_bearing_temp.push([bearingDatas[i].acq_date, bearingDatas[i].P_DE_bearing_temp]);
            }
            state.detailData.P_NDE_bearing_temp = P_NDE_bearing_temp;
            state.detailData.M_NDE_bearing_temp = M_NDE_bearing_temp;
            state.detailData.M_DE_bearing_temp = M_DE_bearing_temp;
            state.detailData.P_DE_bearing_temp = P_DE_bearing_temp;


            //windingTempInfo
            state.detailData.winding_tempR = [];
            state.detailData.winding_tempT = [];
            state.detailData.winding_tempS = [];
            let winding_tempR = [];
            let winding_tempT = [];
            let winding_tempS = [];
            let windingDatas = data[1].datas;
            for (let i = 0; i < windingDatas.length; i++) {
                // let date = new Date(windingDatas[i].acq_date);
                winding_tempR.push([windingDatas[i].acq_date, windingDatas[i].winding_tempR]);
                winding_tempT.push([windingDatas[i].acq_date, windingDatas[i].winding_tempT]);
                winding_tempS.push([windingDatas[i].acq_date, windingDatas[i].winding_tempS]);
            }
            state.detailData.winding_tempR = winding_tempR;
            state.detailData.winding_tempT = winding_tempT;
            state.detailData.winding_tempS = winding_tempS;
            //motorDetails
            //    m.DE_rms_amp : 모터 부하 총진동량
            //    m.NDE_rms_amp : 모터 반 부하 총진동량
            //    m.misalignment_amp : 모터 축정렬
            //    m.unbalance_amp : 모터 불평형
            //    m.rotor_amp : 모터 회전자
            //    m.de_amp : 모터 부하 베어링
            //    m.NDE_amp : 모터 반부하 베어링
            //    p.DE_rms_amp : 펌프 부하 총진동량
            //    p.NDE_rms_amp : 펌프 반 부하 총진동량
            //    p.cavitation_amp : 펌프 케비테이션
            //    p.impeller_amp : 펌프 임펠러
            //    p.DE_amp : 펌프 부하 베어링
            //    p.NDE_amp : 펌프 반부하 베어링
            state.detailData.motor_de_rms_amp = [];
            state.detailData.motor_nde_rms_amp = [];
            state.detailData.motor_misalignment_amp = [];
            state.detailData.motor_unbalance_amp = [];
            state.detailData.motor_rotor_amp = [];
            state.detailData.motor_de_amp = [];
            state.detailData.motor_nde_amp = [];
            state.detailData.pump_de_rms_amp = [];
            state.detailData.pump_nde_rms_amp = [];
            state.detailData.pump_cavatation_amp = [];
            state.detailData.pump_impeller_amp = [];
            state.detailData.pump_de_amp = [];
            state.detailData.pump_nde_amp = [];
            let motor_de_rms_amp = [];
            let motor_nde_rms_amp = [];
            let motor_misalignment_amp = [];
            let motor_unbalance_amp = [];
            let motor_rotor_amp = [];
            let motor_de_amp = [];
            let motor_nde_amp = [];
            let pump_de_rms_amp = [];
            let pump_nde_rms_amp = [];
            let pump_cavatation_amp = [];
            let pump_impeller_amp = [];
            let pump_de_amp = [];
            let pump_nde_amp = [];
            let motorDatas = data[2].datas;
            let lastTime = 0;
            // let lastObj = {};

            for (let i = 0; i < motorDatas.length; i++) {
                // let date = new Date(motorDatas[i].acq_date);
                motor_de_rms_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_de_rms_amp]);
                motor_nde_rms_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_nde_rms_amp]);
                motor_misalignment_amp.push([
                    motorDatas[i].acq_date,
                    motorDatas[i].motor_misalignment_amp,
                ]);
                motor_unbalance_amp.push([
                    motorDatas[i].acq_date,
                    motorDatas[i].motor_unbalance_amp,
                ]);
                motor_rotor_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_rotor_amp]);
                motor_de_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_de_amp]);
                motor_nde_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_nde_amp]);
                pump_de_rms_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_de_rms_amp]);
                pump_nde_rms_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_nde_rms_amp]);
                pump_cavatation_amp.push([
                    motorDatas[i].acq_date,
                    motorDatas[i].pump_cavatation_amp,
                ]);
                pump_impeller_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_impeller_amp]);
                pump_de_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_de_amp]);
                pump_nde_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_nde_amp]);
                if (i === motorDatas.length - 1) {
                    lastTime = motorDatas[i].acq_date;
                    // lastObj = datas[i];
                }
            }
            state.detailData.motor_de_rms_amp = motor_de_rms_amp;
            state.detailData.motor_nde_rms_amp = motor_nde_rms_amp;
            state.detailData.motor_misalignment_amp = motor_misalignment_amp;
            state.detailData.motor_unbalance_amp = motor_unbalance_amp;
            state.detailData.motor_rotor_amp = motor_rotor_amp;
            state.detailData.motor_de_amp = motor_de_amp;
            state.detailData.motor_nde_amp = motor_nde_amp;
            state.detailData.pump_de_rms_amp = pump_de_rms_amp;
            state.detailData.pump_nde_rms_amp = pump_nde_rms_amp;
            state.detailData.pump_cavatation_amp = pump_cavatation_amp;
            state.detailData.pump_impeller_amp = pump_impeller_amp;
            state.detailData.pump_de_amp = pump_de_amp;
            state.detailData.pump_nde_amp = pump_nde_amp;
            if (state.mode === true) {
                if (state.sampleData.idx === 0 || state.sampleData.idx === 1) {
                    state.sampleData.motor_de_rms_amp = [];
                    state.sampleData.motor_nde_rms_amp = [];
                    state.sampleData.pump_de_rms_amp = [];
                    state.sampleData.pump_nde_rms_amp = [];
                    state.sampleData.motor = [];
                    if (state.sampleData.motor_de_rms_amp.length === 0) {
                        // let addNum = 0;

                        for (let i = 0; i < sampleData.length; i++) {
                            let obj = sampleData[i];
                            let addTime = lastTime + 10 * 60 * 1000 * (i + 1);
                            // let addObj = lastObj;
                            // let random1 = (Math.random() * 4) / 30;
                            // let random2 = (Math.random() * 12) / 30;
                            // let random3 = (Math.random() * 3) / 30;
                            // let random4 = (Math.random() * 3) / 30;
                            let random5 = 1 + Math.random() * 0.5;
                            // val1 += random1;
                            // val2 += random2;
                            // val3 += random3;
                            // val4 += random4;
                            // val5 += random5;
                            // addNum += random2;
                            state.sampleData.motor_de_rms_amp.push([
                                addTime,
                                obj.motor_de_rms_amp,
                            ]);
                            state.sampleData.motor_nde_rms_amp.push([
                                addTime,

                                obj.motor_nde_rms_amp,
                            ]);
                            state.sampleData.pump_de_rms_amp.push([
                                addTime,
                                obj.pump_de_rms_amp,
                            ]);
                            state.sampleData.pump_nde_rms_amp.push([
                                addTime,
                                obj.pump_nde_rms_amp,
                            ]);
                            state.sampleData.motor.push([addTime, random5]);
                        }
                    }

                    /////////////////

                    state.detailData.pump_de_rms_amp =
                        state.detailData.pump_de_rms_amp.concat(
                            state.sampleData.pump_de_rms_amp
                        );
                    state.detailData.pump_nde_rms_amp =
                        state.detailData.pump_nde_rms_amp.concat(
                            state.sampleData.pump_nde_rms_amp
                        );
                    state.detailData.motor_de_rms_amp =
                        state.detailData.motor_de_rms_amp.concat(
                            state.sampleData.motor_de_rms_amp
                        );
                    state.detailData.motor_nde_rms_amp =
                        state.detailData.motor_nde_rms_amp.concat(
                            state.sampleData.motor_nde_rms_amp
                        );
                    // state.detailData.motor_nde_rms_amp = state.detailData.motor_nde_rms_amp.concat(
                    //     state.sampleData.motor_nde_rms_amp
                    // );
                    state.detailData.motor_misalignment_amp =
                        state.detailData.motor_misalignment_amp.concat(
                            state.sampleData.motor
                        );
                }
            }
        },
        windingTempInfo(state, windingData) {
            state.detailData.winding_tempR = [];
            state.detailData.winding_tempT = [];
            state.detailData.winding_tempS = [];
            let winding_tempR = [];
            let winding_tempT = [];
            let winding_tempS = [];
            let windingDatas = windingData.datas;
            for (let i = 0; i < windingDatas.length; i++) {
                // let date = new Date(windingDatas[i].acq_date);
                winding_tempR.push([windingDatas[i].acq_date, windingDatas[i].winding_tempR]);
                winding_tempT.push([windingDatas[i].acq_date, windingDatas[i].winding_tempT]);
                winding_tempS.push([windingDatas[i].acq_date, windingDatas[i].winding_tempS]);
            }
            state.detailData.winding_tempR = winding_tempR;
            state.detailData.winding_tempT = winding_tempT;
            state.detailData.winding_tempS = winding_tempS;
        },
        motorDetails(state, MotorData) {
            //    m.DE_rms_amp : 모터 부하 총진동량
            //    m.NDE_rms_amp : 모터 반 부하 총진동량
            //    m.misalignment_amp : 모터 축정렬
            //    m.unbalance_amp : 모터 불평형
            //    m.rotor_amp : 모터 회전자
            //    m.de_amp : 모터 부하 베어링
            //    m.NDE_amp : 모터 반부하 베어링
            //    p.DE_rms_amp : 펌프 부하 총진동량
            //    p.NDE_rms_amp : 펌프 반 부하 총진동량
            //    p.cavitation_amp : 펌프 케비테이션
            //    p.impeller_amp : 펌프 임펠러
            //    p.DE_amp : 펌프 부하 베어링
            //    p.NDE_amp : 펌프 반부하 베어링
            state.detailData.motor_de_rms_amp = [];
            state.detailData.motor_nde_rms_amp = [];
            state.detailData.motor_misalignment_amp = [];
            state.detailData.motor_unbalance_amp = [];
            state.detailData.motor_rotor_amp = [];
            state.detailData.motor_de_amp = [];
            state.detailData.motor_nde_amp = [];
            state.detailData.pump_de_rms_amp = [];
            state.detailData.pump_nde_rms_amp = [];
            state.detailData.pump_cavatation_amp = [];
            state.detailData.pump_impeller_amp = [];
            state.detailData.pump_de_amp = [];
            state.detailData.pump_nde_amp = [];
            let motor_de_rms_amp = [];
            let motor_nde_rms_amp = [];
            let motor_misalignment_amp = [];
            let motor_unbalance_amp = [];
            let motor_rotor_amp = [];
            let motor_de_amp = [];
            let motor_nde_amp = [];
            let pump_de_rms_amp = [];
            let pump_nde_rms_amp = [];
            let pump_cavatation_amp = [];
            let pump_impeller_amp = [];
            let pump_de_amp = [];
            let pump_nde_amp = [];
            let motorDatas = MotorData.datas;
            let lastTime = 0;
            // let lastObj = {};

            for (let i = 0; i < motorDatas.length; i++) {
                // let date = new Date(motorDatas[i].acq_date);
                motor_de_rms_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_de_rms_amp]);
                motor_nde_rms_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_nde_rms_amp]);
                motor_misalignment_amp.push([
                    motorDatas[i].acq_date,
                    motorDatas[i].motor_misalignment_amp,
                ]);
                motor_unbalance_amp.push([
                    motorDatas[i].acq_date,
                    motorDatas[i].motor_unbalance_amp,
                ]);
                motor_rotor_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_rotor_amp]);
                motor_de_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_de_amp]);
                motor_nde_amp.push([motorDatas[i].acq_date, motorDatas[i].motor_nde_amp]);
                pump_de_rms_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_de_rms_amp]);
                pump_nde_rms_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_nde_rms_amp]);
                pump_cavatation_amp.push([
                    motorDatas[i].acq_date,
                    motorDatas[i].pump_cavatation_amp,
                ]);
                pump_impeller_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_impeller_amp]);
                pump_de_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_de_amp]);
                pump_nde_amp.push([motorDatas[i].acq_date, motorDatas[i].pump_nde_amp]);
                if (i === motorDatas.length - 1) {
                    lastTime = motorDatas[i].acq_date;
                    // lastObj = datas[i];
                }
            }
            state.detailData.motor_de_rms_amp = motor_de_rms_amp;
            state.detailData.motor_nde_rms_amp = motor_nde_rms_amp;
            state.detailData.motor_misalignment_amp = motor_misalignment_amp;
            state.detailData.motor_unbalance_amp = motor_unbalance_amp;
            state.detailData.motor_rotor_amp = motor_rotor_amp;
            state.detailData.motor_de_amp = motor_de_amp;
            state.detailData.motor_nde_amp = motor_nde_amp;
            state.detailData.pump_de_rms_amp = pump_de_rms_amp;
            state.detailData.pump_nde_rms_amp = pump_nde_rms_amp;
            state.detailData.pump_cavatation_amp = pump_cavatation_amp;
            state.detailData.pump_impeller_amp = pump_impeller_amp;
            state.detailData.pump_de_amp = pump_de_amp;
            state.detailData.pump_nde_amp = pump_nde_amp;
            if (state.mode === true) {
                if (state.sampleData.idx === 0 || state.sampleData.idx === 1) {
                    state.sampleData.motor_de_rms_amp = [];
                    state.sampleData.motor_nde_rms_amp = [];
                    state.sampleData.pump_de_rms_amp = [];
                    state.sampleData.pump_nde_rms_amp = [];
                    state.sampleData.motor = [];
                    if (state.sampleData.motor_de_rms_amp.length === 0) {
                        // let addNum = 0;

                        for (let i = 0; i < sampleData.length; i++) {
                            let obj = sampleData[i];
                            let addTime = lastTime + 10 * 60 * 1000 * (i + 1);
                            // let addObj = lastObj;
                            // let random1 = (Math.random() * 4) / 30;
                            // let random2 = (Math.random() * 12) / 30;
                            // let random3 = (Math.random() * 3) / 30;
                            // let random4 = (Math.random() * 3) / 30;
                            let random5 = 1 + Math.random() * 0.5;
                            // val1 += random1;
                            // val2 += random2;
                            // val3 += random3;
                            // val4 += random4;
                            // val5 += random5;
                            // addNum += random2;
                            state.sampleData.motor_de_rms_amp.push([
                                addTime,
                                obj.motor_de_rms_amp,
                            ]);
                            state.sampleData.motor_nde_rms_amp.push([
                                addTime,

                                obj.motor_nde_rms_amp,
                            ]);
                            state.sampleData.pump_de_rms_amp.push([
                                addTime,
                                obj.pump_de_rms_amp,
                            ]);
                            state.sampleData.pump_nde_rms_amp.push([
                                addTime,
                                obj.pump_nde_rms_amp,
                            ]);
                            state.sampleData.motor.push([addTime, random5]);
                        }
                    }

                    /////////////////

                    state.detailData.pump_de_rms_amp =
                        state.detailData.pump_de_rms_amp.concat(
                            state.sampleData.pump_de_rms_amp
                        );
                    state.detailData.pump_nde_rms_amp =
                        state.detailData.pump_nde_rms_amp.concat(
                            state.sampleData.pump_nde_rms_amp
                        );
                    state.detailData.motor_de_rms_amp =
                        state.detailData.motor_de_rms_amp.concat(
                            state.sampleData.motor_de_rms_amp
                        );
                    state.detailData.motor_nde_rms_amp =
                        state.detailData.motor_nde_rms_amp.concat(
                            state.sampleData.motor_nde_rms_amp
                        );
                    // state.detailData.motor_nde_rms_amp = state.detailData.motor_nde_rms_amp.concat(
                    //     state.sampleData.motor_nde_rms_amp
                    // );
                    state.detailData.motor_misalignment_amp =
                        state.detailData.motor_misalignment_amp.concat(
                            state.sampleData.motor
                        );
                }
            }
            state.monitor1.flag = true
        },
        handleGraphData(state, { datas, index, array }) {
            state.modelList[array][index].motor_de_amp = [];
            state.modelList[array][index].motor_nde_amp = [];
            state.modelList[array][index].pump_de_amp = [];
            state.modelList[array][index].pump_nde_amp = [];
            let motor_de_amp = [];
            let motor_nde_amp = [];
            let pump_de_amp = [];
            let pump_nde_amp = [];
            let lastTime = 0;
            // let lastObj = {};
            for (let i = 0; i < datas.length; i++) {
                // let date = new Date(datas[i].acq_date);

                motor_de_amp.push([datas[i].acq_date, datas[i].motor_de_rms_amp]);
                motor_nde_amp.push([datas[i].acq_date, datas[i].motor_nde_rms_amp]);

                pump_de_amp.push([datas[i].acq_date, datas[i].pump_de_rms_amp]);
                pump_nde_amp.push([datas[i].acq_date, datas[i].pump_nde_rms_amp]);
                if (i === datas.length - 1) {
                    lastTime = datas[i].acq_date;
                    // lastObj = datas[i];
                }
            }

            if (state.sampleData.motor_de_rms_amp.length === 0) {
                // let addNum = 0;
                // let val1 = 0;
                // let val2 = 0;
                // let val3 = 0;
                // let val4 = 0;
                // let val5 = 0;
                for (var i = 0; i < sampleData.length; i++) {
                    let obj = sampleData[i];
                    let addTime = lastTime + 10 * 60 * 1000 * (i + 1);
                    // let addObj = lastObj;
                    // let random1 = (Math.random() * 4) / 30;
                    // let random2 = (Math.random() * 12) / 30;
                    // let random3 = (Math.random() * 3) / 30;
                    // let random4 = (Math.random() * 3) / 30;
                    let random5 = 1 + Math.random() * 0.5;
                    state.sampleData.motor_de_rms_amp.push([
                        addTime,
                        // addObj.motor_de_rms_amp + random1,
                        obj.motor_de_rms_amp,
                    ]);
                    state.sampleData.motor_nde_rms_amp.push([
                        addTime,
                        // addObj.motor_nde_rms_amp + random4,
                        obj.motor_nde_rms_amp,
                    ]);
                    state.sampleData.pump_de_rms_amp.push([
                        addTime,
                        // addObj.pump_de_rms_amp + random3,
                        obj.pump_de_rms_amp,
                    ]);
                    state.sampleData.pump_nde_rms_amp.push([
                        addTime,
                        // addObj.pump_nde_rms_amp + random2,
                        obj.pump_nde_rms_amp,
                    ]);
                    // state.sampleData.motor.push([addTime, random5]);
                    state.sampleData.motor.push([addTime, random5]);
                }
                // console.log(state.sampleData);
            }
            if (datas.length !== 0) {
                state.modelList[array][index].motor_de_amp_val = Number(
                    motor_de_amp[datas.length - 1][1]
                ).toFixed(2);
                state.modelList[array][index].motor_nde_amp_val = Number(
                    motor_nde_amp[datas.length - 1][1]
                ).toFixed(2);
                state.modelList[array][index].pump_de_amp_val = Number(
                    pump_de_amp[datas.length - 1][1]
                ).toFixed(2);
                state.modelList[array][index].pump_nde_amp_val = Number(
                    pump_nde_amp[datas.length - 1][1]
                ).toFixed(2);
            } else {
                state.modelList[array][index].motor_de_amp_val = 0;
                state.modelList[array][index].motor_nde_amp_val = 0;
                state.modelList[array][index].pump_de_amp_val = 0;
                state.modelList[array][index].pump_nde_amp_val = 0;
            }

            state.modelList[array][index].motor_de_amp = motor_de_amp;
            state.modelList[array][index].motor_nde_amp = motor_nde_amp;
            state.modelList[array][index].pump_de_amp = pump_de_amp;
            state.modelList[array][index].pump_nde_amp = pump_nde_amp;
        },
        runningInfo(state, datas) {
            let cnt = 0;
            let cnt2 = 0;
            datas.forEach((item, index) => {
                for (let i = 0; i < item.length; i++) {
                    if (index == 0) {
                        state.modelList[0][i].eq_on = item[i].eq_on;
                        if (item[i].eq_on) cnt++;
                    } else if (index == 1) {
                        state.modelList[1][i].eq_on = item[i].eq_on;
                        if (item[i].eq_on) cnt2++;
                    }
                }
            })
            state.scada_01.running = cnt;
            state.scada_05.running = cnt2;
        },
        // alramIsTrue(state, datas) {
        //     datas.forEach((element, i) => {
        //         element.forEach((item, j) => {
        //             if (item.Alram === 1) {
        //                 state.modelList[i][j].alarm = true;
        //             }
        //         })
        //     })
        // },
        alarmIsTrue(state, { datas, parameterName }) {
            // console.log("alarmIsTrue datas", datas);
            // console.log("parameterName", parameterName);
            let mid
            let first
            let number
            console.log("alarmIsTrue", parameterName)
            if (store.state.area == 'gosan' && parameterName !== undefined && parameterName.length == 8) {
                first = parameterName.substr(0, 6)
                mid = Number(parameterName.substr(-2))
                mid = mid > 8 ? 'n_' : 'o_'
                number = Number(parameterName.substr(-2))
                if (number == 8) {
                    number = 1
                } else if (number == 9) {
                    number = 2
                } else if (number == 10) {
                    number = 3
                } else if (number == 11) {
                    number = 4
                }
                parameterName = first + mid + number
            } else {
                parameterName
            }

            datas.forEach((element,) => {
                element.forEach((item,) => {
                    console.log("item.motor_id =====", item.motor_id, "parameterName", parameterName);
                    if (item.motor_id == parameterName) {
                        // 펌프 부하, 반부하 총진동량
                        if (item.p_de_rms_alarm || item.p_nde_rms_alarm) {
                            state.alarmList.pump_rms_alarm = true
                        } else {
                            state.alarmList.pump_rms_alarm = false
                        }
                        // 펌프 임펠러 결함
                        if (item.p_impeller_alarm) {
                            state.alarmList.pump_impeller_alarm = true
                        } else {
                            state.alarmList.pump_impeller_alarm = false
                        }
                        // 펌프 케비테이션 결함
                        if (item.p_cavitation_alarm) {
                            state.alarmList.pump_cavitation_alarm = true
                        } else {
                            state.alarmList.pump_cavitation_alarm = false
                        }
                        // 펌프모터 축정렬 불량 
                        if (item.m_misalignment_alarm) {
                            state.alarmList.pumpMotor_misalignment_alarm = true
                        } else {
                            state.alarmList.pumpMotor_misalignment_alarm = false
                        }
                        // 모터-부하/반부하 총진동량 
                        if (item.m_de_rms_alarm || item.m_nde_rms_alarm) {
                            state.alarmList.motor_rms_alarm = true
                        } else {
                            state.alarmList.motor_rms_alarm = false
                        }
                        // 모터 회전자 결함 
                        if (item.m_rotor_alarm) {
                            state.alarmList.motor_rotor_alarm = true
                        } else {
                            state.alarmList.motor_rotor_alarm = false
                        }
                        // 모터 권선온도 
                        if (item.winding_temp_t_alarm || item.winding_temp_r_alarm || item.winding_temp_s_alarm) {
                            state.alarmList.winding_temp_alarm = true
                        } else {
                            state.alarmList.winding_temp_alarm = false
                        }
                        // 펌프 모터 베어링 온도
                        if (item.m_de_bearing_temp_alarm || item.p_de_bearing_temp_alarm || item.m_nde_bearing_temp_alarm) {
                            state.alarmList.pumpMotor_bearing_temp_alarm = true
                        } else {
                            state.alarmList.pumpMotor_bearing_temp_alarm = false
                        }
                        // 펌프모터 질량 불평형 
                        if (item.m_unbalance_alarm) {
                            state.alarmList.pumpMotor_unbalance_alarm = true
                        } else {
                            state.alarmList.pumpMotor_unbalance_alarm = false
                        }
                        // 모터-부하/반부하 베어링 결함
                        if (item.m_de_bpfo_alarm || item.m_de_bpfi_alarm || item.m_de_bsf_alarm || item.m_de_ftf_alarm) {
                            state.alarmList.motor_bearing_alarm = true
                        } else {
                            state.alarmList.motor_bearing_alarm = false
                        }
                        // 모터-부하/반부하 베어링 결함
                        if (item.m_nde_bpfo_alarm || item.m_nde_bpfi_alarm || item.m_nde_bsf_alarm || item.m_nde_ftf_alarm) {
                            state.alarmList.motor_half_bearing_alarm = true
                        } else {
                            state.alarmList.motor_half_bearing_alarm = false
                        }
                        // 펌프-부하/반부하 베어링 결함
                        if (item.p_de_bpfo_alarm || item.p_de_bpfi_alarm || item.p_de_bsf_alarm || item.p_de_ftf_alarm) {
                            state.alarmList.pump_bearing_alarm = true
                        } else {
                            state.alarmList.pump_bearing_alarm = false
                        }
                        // 펌프-부하/반부하 베어링 결함
                        if (item.p_nde_bpfo_alarm || item.p_nde_bpfi_alarm || item.p_nde_bsf_alarm || item.p_nde_ftf_alarm) {
                            state.alarmList.pump_half_bearing_alarm = true
                        } else {
                            state.alarmList.pump_half_bearing_alarm = false
                        }

                        const { Alarm, Alram, ...itemText } = item;
                        console.log(Alarm, Alram);

                        const values = Object.values(itemText);
                        // const trueCount = values.filter(value => value === true).length;
                        const trueCount = values.filter(value => value === true).length;
                        state.alarmList.Alarm = trueCount >= 1 ? true : false;
                    }
                })
            })

            datas.forEach((element, i) => {
                element.forEach((item, j) => {
                    const trueKey = Object.keys(item).find(key => item[key] === true);
                    // if (trueKey && state.modelList?.at(i)?.includes(j)) {
                    //     state.modelList[i][j].alarm = true;
                    // }
                    // console.log("alarmIsTrue modelList", state.modelList[i][j]);

                    if (trueKey && state.modelList?.[i]?.[j]) {
                        state.modelList[i][j].alarm = true;
                    }
                })
            })
        },
        flowPressure(state, { datas }) {
            // console.log("datas ::::: " + datas.length);
            datas.forEach((item, index) => {
                if (index == 0) {
                    if (datas.length === 0) {
                        state.scada_01.pressure = 0;
                        state.scada_01.flow_rate = 0;
                    } else {
                        state.scada_01.pressure_val = item.pressure;
                        state.scada_01.flow_rate_val = item.flow_rate;
                    }
                }
                else if (index == 1) {
                    if (datas.length === 0) {
                        state.scada_05.pressure_val = 0;
                        state.scada_05.flow_rate_val = 0;
                    } else {
                        state.scada_05.pressure_val = item.pressure;
                        state.scada_05.flow_rate_val = item.flow_rate;
                    }
                }
            });
        },
        distribution(state, { datas }) {
            // console.log("datas :: " + datas.length);
            // console.log("str :: " + type);
            datas.forEach((item, index) => {
                if (index == 0) {
                    if (datas.length === 0) {
                        state.scada_01.flow_rate = [];
                        state.scada_01.pressure = [];
                        state.scada_01.data = [];
                    } else {
                        state.scada_01.flow_rate = [];
                        state.scada_01.pressure = [];
                        state.scada_01.data = [];
                        for (let i = 0; i < datas.length; i++) {
                            let obj = datas[i];
                            if (i % 2 == 0) {
                                state.scada_01.data.push([obj.flow_rate, obj.pressure]);
                            }
                        }
                    }
                }
                else if (index == 1) {
                    if (datas.length === 0) {
                        state.scada_05.flow_rate = [];
                        state.scada_05.pressure = [];
                        state.scada_05.data = [];
                    } else {
                        state.scada_05.flow_rate = [];
                        state.scada_05.pressure = [];
                        for (let i = 0; i < datas.length; i++) {
                            let obj = datas[i];
                            if (i % 2 == 0) {
                                state.scada_05.data.push([obj.flow_rate, obj.pressure]);
                            }
                        }
                    }
                }
            })
        },
    },


    actions: {
        flowPressure({ rootState, commit }) {
            axios
                .get(`${rootState.globalIP}/api/v1/motor/flowPressure`)
                .then((data) =>
                    commit("flowPressure", {
                        datas: data.data.datas,
                    })
                );
        },
        distribution({ rootState, state, commit }) {
            const params = {
                endDate: state.endDate,
                startDate: state.startDate,
            };
            axios
                .post(`${rootState.globalIP}/api/v1/motor/distribution`, params)
                .then((data) => {
                    const datas = data.data.datas;
                    commit("distribution", {
                        datas: datas,
                    });
                });
        },
        bearingTempInfo({ rootState, state, commit }) {
            console.log(state)
            let scada_id = state.id.replace("motor", "pump_scada");
            if (scada_id == "pump_scada_n_1") scada_id = "pump_scada_08"
            if (scada_id == "pump_scada_n_2") scada_id = "pump_scada_09"
            if (scada_id == "pump_scada_n_3") scada_id = "pump_scada_10"
            if (scada_id == "pump_scada_n_4") scada_id = "pump_scada_11"
            let id
            if (store.state.area != 'gosan') {
                id = state.id.replace('o_', '0').replace('n_', '0')
            } else {
                scada_id = scada_id.replace('o_', '0').replace('n_', '0');
                id = state.id
            }
            this.state.monitor1.flag = false
            // let startDate;
            let params;
            let motorParams;

            if (!state.searchDate) {
                // startDate = new Date(state.pickDate.from);
                // startDate.setDate(startDate.getDate() + 5);
                params = {
                    endDate: state.pickDate.to,
                    // startDate: startDate.toISOString().slice(0, 10),
                    startDate: state.pickDate.from,
                    id: scada_id,
                };
                motorParams = {
                    endDate: state.pickDate.to,
                    // startDate: startDate.toISOString().slice(0, 10),
                    startDate: state.pickDate.from,
                    id: id,
                };
            } else {
                params = {
                    endDate: state.pickDate.to,
                    startDate: state.pickDate.from,
                    id: scada_id,
                };
                motorParams = {
                    endDate: state.pickDate.to,
                    startDate: state.pickDate.from,
                    id: id,
                };
            }

            // Create an array of promises for each API call
            const promises = [
                axios.post(`${rootState.globalIP}/api/v1/motor/bearingTempInfo`, params),
                axios.post(`${rootState.globalIP}/api/v1/motor/windingTempInfo`, params),
                axios.post(`${rootState.globalIP}/api/v1/motor/motorDetails`, motorParams)
            ];

            // Use Promise.all to handle the promises concurrently
            Promise.all(promises)
                .then((responses) => {
                    // Extract the data from each response
                    const bearingData = responses[0].data.datas;
                    const windingData = responses[1].data.datas;
                    const motorData = responses[2].data.datas;

                    let dataArr_1 = [];
                    for (let i = 0; i < bearingData.length; i++) {
                        let obj = bearingData[i];
                        dataArr_1.push(obj);
                    }

                    let dataArr_2 = [];
                    for (let i = 0; i < windingData.length; i++) {
                        let obj = windingData[i];
                        dataArr_2.push(obj);
                    }

                    let dataArr_3 = [];
                    for (let i = 0; i < motorData.length; i++) {
                        let obj = motorData[i];
                        dataArr_3.push(obj);
                    }
                    commit("bearingTempInfo", [{ datas: dataArr_1, index: state.scada_id },
                    { datas: dataArr_2, index: state.scada_id }, { datas: dataArr_3, index: state.id }]);
                    this.state.monitor1.flag = true
                })
                .catch((error) => {
                    console.error("Error:", error);
                });
        },
        windingTempInfo({ rootState, state, commit }) {
            const scada_id = state.scada_id.replace('o_', '0').replace('n_', '0');

            // let startDate;
            let params;
            if (!state.searchDate) {
                // startDate = new Date(state.pickDate.from);
                // startDate.setDate(startDate.getDate() + 5);
                params = {
                    endDate: state.pickDate.to,
                    id: scada_id,
                    startDate: state.pickDate.from,
                    // startDate : startDate.toISOString().slice(0, 10),
                };
            } else {
                params = {
                    endDate: state.pickDate.to,
                    id: scada_id,
                    startDate: state.pickDate.from,
                };
            }
            axios
                .post(`${rootState.globalIP}/api/v1/motor/windingTempInfo`, params)
                .then((data) => {
                    const datas = data.data.datas;
                    let dataArr_1 = [];
                    for (let i = 0; i < datas.length; i++) {
                        let obj = datas[i];
                        dataArr_1.push(obj);
                    }
                    commit("windingTempInfo", {
                        datas: dataArr_1,
                        index: state.scada_id,
                    });
                });
        },
        motorDetails({ rootState, state, commit }) {
            // let startDate;
            let motorParams;
            if (!state.searchDate) {
                // startDate = new Date(state.startDate.split(" ")[0]);
                //  startDate.setDate(startDate.getDate() + 5);
                motorParams = {
                    endDate: state.pickDate.to,
                    id: state.id,
                    //  startDate: startDate.toISOString().slice(0, 10)
                    startDate: state.pickDate.from,
                };
            } else {
                motorParams = {
                    endDate: state.pickDate.to,
                    id: state.id,
                    startDate: state.pickDate.from,
                };
            }

            axios
                .post(`${rootState.globalIP}/api/v1/motor/motorDetails`, motorParams)
                .then((data) => {
                    const datas = data.data.datas;
                    let dataArr_1 = [];
                    for (let i = 0; i < datas.length; i++) {
                        let obj = datas[i];
                        dataArr_1.push(obj);
                    }
                    commit("motorDetails", {
                        datas: dataArr_1,
                        index: state.id,
                    });
                });
        },
        handleGraphData({ rootState, state, commit }) {
            let endDate = state.endDate.split(" ")[0]
            let startDate = state.startDate.split(" ")[0]
            // let startDate;
            let params;
            if (!state.searchDate) {
                // startDate = new Date(state.startDate.split(" ")[0]);
                // startDate.setDate(startDate.getDate() + 5);
                params = {
                    endDate: endDate,
                    startDate: startDate
                    // startDate: startDate.toISOString().slice(0, 10)
                };
            } else {
                startDate = state.startDate.split(" ")[0]
                params = {
                    endDate: endDate,
                    startDate: startDate
                };
            }
            axios
                .post(`${rootState.globalIP}/api/v1/motor/vibrationGraph`, params)
                .then((data) => {
                    const datas = data.data.datas;
                    let dataArr_1 = [];
                    let dataArr_2 = [];
                    let dataArr_3 = [];
                    let dataArr_4 = [];
                    let dataArr_5 = [];
                    let dataArr_6 = [];
                    let dataArr_7 = [];
                    let dataArr_8 = [];
                    let dataArr_9 = [];
                    let dataArr_10 = [];
                    let dataArr_11 = [];
                    datas.forEach(item => {
                        for (let i = 0; i < item.length; i++) {
                            let obj = item[i];
                            let idName = obj.motor_id;
                            if (store.state.area == "gosan") {
                                if (idName === "motor_o_1") dataArr_1.push(obj);
                                if (idName === "motor_o_2") dataArr_2.push(obj);
                                if (idName === "motor_o_3") dataArr_3.push(obj);
                                if (idName === "motor_o_4") dataArr_4.push(obj);
                                if (idName === "motor_o_5") dataArr_5.push(obj);
                                if (idName === "motor_o_6") dataArr_6.push(obj);
                                if (idName === "motor_o_7") dataArr_7.push(obj);
                                if (idName === "motor_n_1") dataArr_8.push(obj);
                                if (idName === "motor_n_2") dataArr_9.push(obj);
                                if (idName === "motor_n_3") dataArr_10.push(obj);
                                if (idName === "motor_n_4") dataArr_11.push(obj);
                            } else {
                                if (idName === "motor_01") dataArr_1.push(obj);
                                if (idName === "motor_02") dataArr_2.push(obj);
                                if (idName === "motor_03") dataArr_3.push(obj);
                                if (idName === "motor_04") dataArr_4.push(obj);
                                if (idName === "motor_05") dataArr_5.push(obj);
                                if (idName === "motor_06") dataArr_6.push(obj);
                                if (idName === "motor_07") dataArr_7.push(obj);
                                if (idName === "motor_08") dataArr_8.push(obj);
                                if (idName === "motor_09") dataArr_9.push(obj);
                                if (idName === "motor_10") dataArr_10.push(obj);
                                if (idName === "motor_11") dataArr_11.push(obj);
                            }
                        }
                    })
                    if (store.state.area == "gosan") {
                        commit("handleGraphData", {
                            datas: dataArr_1,
                            index: 0,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_2,
                            index: 1,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_3,
                            index: 2,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_4,
                            index: 3,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_5,
                            index: 4,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_6,
                            index: 5,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_7,
                            index: 6,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_8,
                            index: 0,
                            array: 1,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_9,
                            index: 1,
                            array: 1,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_10,
                            index: 2,
                            array: 1,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_11,
                            index: 3,
                            array: 1,
                        });
                    }
                    else if (store.state.area == "gumi") {
                        commit("handleGraphData", {
                            datas: dataArr_1,
                            index: 0,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_2,
                            index: 1,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_3,
                            index: 2,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_4,
                            index: 3,
                            array: 0,
                        });
                    } else if (store.state.area == "hakya") {
                        commit("handleGraphData", {
                            datas: dataArr_1,
                            index: 0,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_2,
                            index: 1,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_3,
                            index: 2,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_4,
                            index: 3,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_5,
                            index: 4,
                            array: 0,
                        });
                        commit("handleGraphData", {
                            datas: dataArr_6,
                            index: 5,
                            array: 0,
                        });
                    }

                });
        },
        //가동중 조회
        runningInfo({ rootState, commit }) {
            axios
                .get(`${rootState.globalIP}/api/v1/motor/runningInfo`)
                .then((data) => {
                    commit("runningInfo", data.data.datas)
                });
        },
        alarm({ rootState, commit }, payload) {
            let parameterName = payload?.parameterName
            if (store.state.area != 'gosan') {
                let motor_id = payload?.motorParams.id.replace('o_', '0').replace('n_', '0')
                payload.motorParams.id = motor_id
            }
            axios.post(`${rootState.globalIP}/api/v1/motor/alarm`, payload?.motorParams).then((data) => {
                const datas = data.data.datas;
                this.state.monitor1.alarmData = datas
                if (datas.length !== 0) {
                    console.log(this.state.monitor1.alarmFlag)
                    this.state.monitor1.alarmFlag = !this.state.monitor1.alarmFlag
                    commit("alarmIsTrue", { datas, parameterName });
                }
            });
        },
        getPumpList({ rootState, commit }, select) {
            // axios.get(`${rootState.globalIP}/api/v1/main/motorDataAll`)
            // Promise.all([
            //     axios.get(`${rootState.globalIP}/api/v1/main/motorDataAll`),
            //     axios.get(`${rootState.globalIP}/api/v1/motor/selectGraphThreshold`) // 두 번째 API URL 예시
            // ])

            let promiseArray = [
                axios.get(`${rootState.globalIP}/api/v1/main/motorDataAll`)
            ];

            // 만약 select가 'area'가 아닌 경우에만 두 번째 API 호출 추가
            if (store.state.area !== 'hakya') {
                promiseArray.push(axios.get(`${rootState.globalIP}/api/v1/motor/selectGraphThreshold`));
            }

            return Promise.all(promiseArray)
                .then(([response1, response2]) => {
                    let datas = response1.data.datas;
                    // let datas2 = response2.data.datas;
                    let datas2 = response2 ? response2.data.datas : null;

                    let updatedData = [];

                    if (datas.length !== 0) {

                        // 각 그룹의 데이터를 순회
                        for (const groupData of datas) {
                            // motor_id 변경 로직 적용
                            const updatedGroup = groupData.map((item, index) => {
                                const prefix = (item.grp_idx === 1) ? "motor_" : "motor_";
                                const newIndex = index + 1 + ((item.grp_idx === 2) ? 7 : 0);
                                const newMotorId = `${prefix}${(newIndex < 10) ? '0' : ''}${newIndex}`;
                                return { ...item, "motor_id": newMotorId };
                            });

                            // 변경된 데이터를 결과 배열에 추가
                            updatedData.push(updatedGroup);
                        }
                        datas = updatedData
                        commit("setPumpList", { datas, select, datas2 })
                    }
                });
        },
    },
};

export default monitor1;
