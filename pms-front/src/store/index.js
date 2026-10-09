// import * as mutations from './mutations';
import axios from 'axios';
// import * as actions from './actions';

import monitor1 from './modules/monitor1';
import dashboard from './modules/dashboard';

import { createStore } from 'vuex';
import precision from './modules/precision';

export default createStore({
    state: {
        selectedBuildingIndex: 0,
        idx: 0,
        dataReload: 0,
        area: 'gosan',
        // area: 'gumi',
        // area: 'hakya',
        globalIP: 'http://localhost:4040/',
        leftDrawerOpen: true,
        alertVisible: false,
        process: [
            // {
            //     title: '착수',
            //     normal: 10,
            //     err: 0,
            //     selected: true,
            //     img: 'icon1',
            // },
            // {
            //     title: '약품',
            //     normal: 10,
            //     err: 0,
            //     selected: false,
            //     img: 'icon2',
            // },
            // {
            //     title: '혼화/응집',
            //     normal: 66,
            //     err: 0,
            //     selected: false,
            //     img: 'icon3',
            // },
            // {
            //     title: '침전',
            //     normal: 8,
            //     err: 0,
            //     selected: false,
            //     img: 'icon4',
            // },
            // {
            //     title: '오존',
            //     normal: 11,
            //     err: 0,
            //     selected: false,
            //     img: 'icon5',
            // },
            // {
            //     title: '여과',
            //     normal: 6,
            //     err: 0,
            //     selected: false,
            //     img: 'icon5',
            // },
            // {
            //     title: 'GAC여과',
            //     normal: 3,
            //     err: 0,
            //     selected: false,
            //     img: 'icon6',
            // },
            // {
            //     title: '소독',
            //     normal: 2,
            //     err: 0,
            //     selected: false,
            //     img: 'icon7',
            // },
            {
                title: '송수',
                normal: 11,
                err: 0,
                selected: false,
                img: 'icon8',
            },
        ],
        pumpMotor: [
            {
                name: '1',
                status: false,
                list: '송수모터/펌프 #1',
            },
            {
                name: '2',
                status: true,
                list: '송수모터/펌프 #2',
            },
            {
                name: '3',
                status: true,
                list: '송수모터/펌프 #3',
            },
            {
                name: '4',
                status: true,
                list: '송수모터/펌프 #4',
            },
            {
                name: '5',
                status: true,
                list: '송수모터/펌프 #5',
            },
            {
                name: '6',
                status: true,
                list: '송수모터/펌프 #6',
            },
            {
                name: '7',
                status: true,
                list: '송수모터/펌프 #7',
            },
            {
                name: '8',
                status: true,
                list: '송수모터/펌프 #8',
            },
            {
                name: '9',
                status: true,
                list: '송수모터/펌프 #9',
            },
            {
                name: '10',
                status: true,
                list: '송수모터/펌프 #10',
            },
        ],
        alertList: [
            // {
            //     num: 1,
            //     time: '2021-06-15 15:00',
            //     list: '착수정 유입 조절 밸브 #1',
            //     info: '-',
            //     status: '전압이상',
            // },
            // {
            //     num: 2,
            //     time: '2021-06-15 15:00',
            //     list: '착수정 유입 조절 밸브 #2',
            //     info: '-',
            //     status: '전압이상',
            // },
            // {
            //     num: 3,
            //     time: '2021-06-15 15:00',
            //     list: '착수정 유입 조절 밸브 #3',
            //     info: '-',
            //     status: '전압이상',
            // },
            // {
            //     num: 4,
            //     time: '2021-06-15 15:00',
            //     list: '착수정 유입 조절 밸브 #4',
            //     info: '-',
            //     status: '전압이상',
            // },
        ],
        pieNormalData: 0,
        pieErrData: 0,
        motors: [
            {
                id: 'motor_01',
                scada_id: 'pump_scada_01',
                name: '평택계통 #1',
                select: true,
            },
            {
                id: 'motor_02',
                scada_id: 'pump_scada_02',
                name: '평택계통 #2',
                select: false,
            },
            {
                id: 'motor_03',
                scada_id: 'pump_scada_03',
                name: '평택계통 #3',
                select: false,
            },
            {
                id: 'motor_04',
                scada_id: 'pump_scada_04',
                name: '평택계통 #4',
                select: false,
            },
            {
                id: 'motor_05',
                scada_id: 'pump_scada_05',
                name: '송산계통 #5',
                select: false,
            },
            {
                id: 'motor_06',
                scada_id: 'pump_scada_06',
                name: '송산계통 #6',
                select: false,
            },
        ],
    },
    getters: {
        normalValue: (state) => {
            let normal = state.process
                .map((data) => {
                    if (data.selected) {
                        return data.normal;
                    }
                })
                .filter((x) => x !== undefined);
            return (state.pieNormalData = normal[0]);
        },
        errValue: (state) => {
            let err = state.process
                .map((data) => {
                    if (data.selected) {
                        return data.err;
                    }
                })
                .filter((x) => x !== undefined);
            return (state.pieErrData = err[0]);
        },
    },
    mutations: {
        updateGlobalIP(state, newIP) {
            state.globalIP = newIP;
        }
    },
    actions: {
        getAllFacStats({ rootState, }) {
            console.log("rootState.globalIP", rootState.globalIP, "rootState.area", rootState.area);
            axios.get(`${rootState.globalIP}/api/v1/main/getAllFacStats`).then((data) => {
                const datas = data.data.datas;
                if (datas?.length !== 0) {
                    this.state.process[0].err = datas?.total_sum
                    this.state.process[0].normal = datas?.sensor_count - this.state.process[0].err
                    // commit("getAllFacStats", datas)
                }
            });
        },
        setGlobalIP({ commit, state }) {
            // state.area 값에 따라 IP 주소를 설정합니다.
            let newIP = '';
            if (state.area === 'gosan') {
                newIP = 'http://localhost:4040/';
                // newIP = 'http://localhost:10016/';
            } else if (state.area === 'gumi') {
                newIP = 'http://localhost:4040/';
                // newIP = 'http://localhost:10016/';
            } else if (state.area === 'hakya') {
                newIP = 'http://localhost:4040/';
                // newIP = 'http://localhost:10016/';
            }
            commit('updateGlobalIP', newIP);
        }
    },
    modules: {
        dashboard,
        monitor1,
        precision
    },
});
