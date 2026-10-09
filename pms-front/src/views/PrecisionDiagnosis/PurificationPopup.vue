<template>
    <div class="position-absolute shadow" :style="{
        display: 'block',
        top: '0',
        left: '15px',
        width: '1200px',
        height: '600px',
        background: '#283046',
        border: '1px solid rgba(255, 255, 255, .5)',
    }">
        <div class="modal-wrap">
            <div class="modal-header">
                <span>설정</span>
                <button type="button" class="btn-close btn-close-white"
                    @click="store.state.precision.settingPump = -1"></button>
            </div>
            <div class="modal-body">
                <b-row class="h-100">
                    <b-col xl="4" class="h-100" :style="{ background: 'rgb(43 55 91)' }">
                        <ul class="btn-list-group">
                            <li>
                                <button class="btn btn-sm w-100">Pump</button>
                                <template v-for="(item, index) in this.pumpList" :key="item">
                                    <button class="btn btn-sm w-100" @click="clickPump(item.MOTOR_ID, index)" :style="{
                                        backgroundColor: getPumpColor(index),
                                        marginTop: '2px',
                                    }">
                                        {{ item.GRP_NM + " #" + item.MOTOR_ID.slice(-1) }}
                                    </button>
                                </template>
                            </li>
                            <li>
                                <button class="btn btn-sm w-100">Motor</button>
                                <template v-for="(item, index) in this.pumpList" :key="item">
                                    <button class="btn btn-sm w-100" @click="clickMotor(item.MOTOR_ID, index)" :style="{
                                        backgroundColor: getMotorColor(index),
                                        marginTop: '2px',
                                    }">
                                        {{ item.GRP_NM + " #" + item.MOTOR_ID.slice(-1) }}
                                    </button>
                                </template>
                            </li>
                        </ul>
                    </b-col>
                    <b-col xl="8" class="position-relative h-100">
                        <b-row>
                            <b-col>
                                <h6>{{ title }}</h6>
                                <ul class="d-inline-flex justify-content-start p-2 bg-black rounded">
                                    <li>
                                        <button class="btn btn-default btn-sm"
                                            :style="{ color: activeColor ? 'white' : 'black' }"
                                            @click="clickSecTab(this.fir)">
                                            {{ fir }}
                                        </button>
                                    </li>
                                    <li>
                                        <button class="btn btn-default btn-sm mx-1"
                                            :style="{ color: !activeColor ? 'white' : 'black' }"
                                            @click="clickSecTab(this.sec)">
                                            {{ sec }}
                                        </button>
                                    </li>
                                </ul>
                            </b-col>
                        </b-row>
                        <b-row :style="{
                            height: '400px',
                            overflow: 'hidden',
                            overflowY: 'auto',
                        }">
                            <b-col class="mt-3">
                                <b-row class="mb-3">
                                    <div v-for="item in selectedData" :key="item" class="mb-3">
                                        <b-col>
                                            <label :style="{ width: '90px' }">{{ item.PARM_NM }} </label>
                                            <input :style="{ width: '90px' }" type="text"
                                                class="bg-transparent border border-secondary" style="color: white"
                                                v-model="item.PARM_VALUE" @input="handleInput(item)" />
                                        </b-col>
                                    </div>
                                </b-row>
                                <b-row> </b-row>
                            </b-col>
                            <div class="position-absolute" :style="{ bottom: '10px' }">
                                <button class="btn btn-primary" @click="saveChange">
                                    Save change
                                </button>
                                <button class="btn btn-outline-secondary mx-1"
                                    @click="store.state.precision.settingPump = -1">
                                    close
                                </button>
                            </div>
                        </b-row>
                    </b-col>
                </b-row>
            </div>
        </div>
    </div>
</template>
<script>
import { useStore } from "vuex";
import { fetchFunc } from "@/util/fetchFunc";
export default {
    setup() {
        const store = useStore();
        return { store };
    },
    data() {
        return {
            title: "",
            fir: "PIV",
            sec: "POV",
            activeColor: true,
            selectedTab: "PIV",
            selectedData: [],
            settingData: [],
            pumpList: [],
            motorBackgroundColor: "#3a4456",
            pumpBackgroundColor: "#3a4456",
            clickedMotorIndex: null,
            clickedPumpIndex: 0,
        };
    },
    mounted() {
        this.getData();
    },
    methods: {
        clickMotor(motorId, index) {
            this.id = motorId;
            this.activeColor = true;
            this.fir = "MIV";
            this.sec = "MOV";
            this.title =
                this.pumpList[index].GRP_NM +
                " #" +
                this.pumpList[index].MOTOR_ID.slice(-1);

            this.clickedMotorIndex = index;
            this.clickedPumpIndex = null; // Motor 클릭 시 Pump 버튼 비활성화
            this.selectedMotorData = this.settingData.filter(
                (item) => item.MOTOR_ID === motorId && item.EQ_TYPE === "MOTOR"
            );
            this.selectedData = this.selectedMotorData.filter(
                (item) => item.CHANNEL_NM === this.fir
            );
        },
        clickPump(pumpId, index) {
            console.log(pumpId, index);
            this.id = pumpId;
            this.activeColor = true;
            this.fir = "PIV";
            this.sec = "POV";
            this.title =
                this.pumpList[index].GRP_NM +
                " #" +
                this.pumpList[index].MOTOR_ID.slice(-1);

            this.clickedPumpIndex = index;
            this.clickedMotorIndex = null; // Pump 클릭 시 Motor 버튼 비활성화
            console.log(this.settingData);
            this.selectedPumpData = this.settingData.filter(
                (item) => item.MOTOR_ID === pumpId && item.EQ_TYPE === "PUMP"
            );
            this.selectedData = this.selectedPumpData.filter(
                (item) => item.CHANNEL_NM === this.fir
            );
        },
        getMotorColor(index) {
            return this.clickedMotorIndex === index
                ? "#5E808F"
                : this.motorBackgroundColor;
        },
        getPumpColor(index) {
            return this.clickedPumpIndex === index
                ? "#5E808F"
                : this.pumpBackgroundColor;
        },
        async getData() {
            let param = {};
            let data = (
                await fetchFunc(
                    `${this.store.state.globalIP}api/v1/diagnosis/setting`,
                    param
                )
            ).datas;
            let pumpList = (
                await fetchFunc(`${this.store.state.globalIP}api/v1/diagnosis/pumpList`)
            ).datas;
            this.pumpList = pumpList[this.store.state.precision.settingPump - 1];
            this.id = this.pumpList[0].MOTOR_ID;
            this.settingData = data.filter(
                (item) =>
                    item.GRP_ID === this.store.state.precision.settingPump.toString()
            );
            this.selectedMotorData = this.settingData.filter(
                (item) =>
                    item.MOTOR_ID === this.pumpList[0].MOTOR_ID && item.EQ_TYPE === "PUMP"
            );
            this.selectedData = this.selectedMotorData.filter(
                (item) => item.CHANNEL_NM === this.selectedTab
            );
            this.title =
                this.selectedData[0].GRP_NM +
                " #" +
                this.selectedData[0].MOTOR_ID.slice(-1);
        },
        clickSecTab(tab) {
            this.activeColor = !this.activeColor;
            this.selectedTab = tab;
            this.clickedData = this.settingData.filter(
                (item) => item.MOTOR_ID === this.id
            );
            this.selectedData = this.clickedData.filter(
                (item) => item.CHANNEL_NM === this.selectedTab
            );
        },
        saveChange() {
            const settingParam = this.selectedData;
            fetchFunc(
                `${this.store.state.globalIP}api/v1/diagnosis/updateSettingParm`,
                settingParam
            );
            this.store.state.precision.settingPump = -1;
        },
        handleInput(item) {
            item.PARM_VALUE = item.PARM_VALUE.replace(/[^0-9.]/g, "");
        }
    },
};
</script>
<style></style>
