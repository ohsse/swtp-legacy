<template>
    <!-- <div class="monitor-right">
        <div class="action-btn" v-on:click="select(4)">4</div>
        <div class="action-btn" v-on:click="select(3)">3</div>
        <div class="action-btn" v-on:click="select(2)">2</div>
        <div class="action-btn" v-on:click="select(1)">1</div>
        <div class="action-btn" v-on:click="selectReset()">reset</div>
    </div> -->
    <div class="monitor-1">
        <div class="content ">
            <div class="content-left">
                <!-- TODO : PMS 데이터 없을때 구미, 학야 확인하고 싶으면   v-if="store.state.monitor1.modelList[2]" <-- 이거 2 로 적용해서 css 맞춰보기  -->
                  <!--  고산정수장 하나로 나오는걸로 변경  -->
                <div class="content-panel" v-if="store.state.area == 'gosan'">
                     <PumpPipeWaterIcon v-for="(item, index) in store.state.monitor1.modelList[0]" :key="index"
                        :none="item" /> 
                     <div class="content-header">
                        <PumpContentHeader :title=title_one.name />
                    </div> 
                    <div class="content-container two" style="overflow-y:scroll" :class="heightCss">
                        <PumpContentContainer v-for="(item, index) in store.state.monitor1.modelList[0]" :key="index"
                            :item="item" :index="index" @openModal="openModal" :isPump="true" />
                            <PumpContentContainer v-for="(item, index) in store.state.monitor1.modelList[1]" :key="index"
                            :item="item" :index="index + 7" @openModal="openModal" :isPump="true" />
                    </div> 
                </div>
                <div class="content-panel" v-if="store.state.area == 'gumi' || store.state.area == 'hakya'">
                    <PumpPipeWaterIcon v-for="(item, index) in store.state.monitor1.modelList[0]" :key="index"
                        :none="item" /> 
                     <div class="content-header">
                        <PumpContentHeader :title=title_one.name />
                    </div> 
                    <div class="content-container two" style="overflow-y:scroll" :class="heightCss">
                        <PumpContentContainer v-for="(item, index) in store.state.monitor1.modelList[0]" :key="index"
                            :item="item" :index="index" @openModal="openModal" :isPump="true" />
                    </div> 
                </div>
            </div>
        </div>
    </div>
    <ModalComp ref="ModalComp" v-show="isModalOpen" @closeModal="closeModal"></ModalComp>
</template>

<script>
import { useStore } from "vuex";
import { onMounted, watch } from "vue";
import moment from "moment";
import axios from "axios";
import PumpPipeWaterIcon from "./PumpControl/PumpPipeWaterIcon.vue";
import PumpContentContainer from "./PumpControl/PumpContentContainer.vue";
//import PumpManageStatus from "./PumpControl/PumpManageStatus.vue";
import PumpContentHeader from "./PumpControl/PumpContentHeader.vue";
import bgPTKData from '@/assets/data/PTK.json';
import bgSSNData from '@/assets/data/SSN.json';
import ModalComp from "@/components/component/ModalComp.vue";

export default {
    components: {
        PumpPipeWaterIcon,
        PumpContentContainer,
        // PumpManageStatus,
        PumpContentHeader,
        ModalComp,
    },
    setup() {
        const store = useStore();
        const visibleToggle = () => {
            store.state.alertVisible = !store.state.alertVisible;
        };
        const scatterPTKData = bgPTKData
        const scatterSSNData = bgSSNData
        onMounted(() => {
            console.log("store.state.monitor1.modelList[0]",store.state.monitor1.modelList[0]);
            console.log("store.state.monitor1.modelList[1]",store.state.monitor1.modelList[1]);
            let isLocal = false;
            if (!isLocal) {
                let currentTime = new Date();
                let startDate = moment(
                    currentTime.getTime() - 7 * 24 * 60 * 60 * 1000
                ).format("yyyy-MM-DD HH:mm:ss");
                let endDate = moment(currentTime.getTime()).format(
                    "yyyy-MM-DD HH:mm:ss"
                );
                store.state.monitor1.startDate = startDate;
                store.state.monitor1.endDate = endDate;
            }
            store.dispatch("monitor1/getPumpList")
        });
        watch(() => store.state.monitor1.modelList, function () {
            store.dispatch("monitor1/runningInfo");
            store.dispatch("monitor1/alarm", { motorParams: { id: store.state.monitor1.id, endDate: store.state.monitor1.endDate.split(' ')[0], startDate: store.state.monitor1.startDate.split(' ')[0] } });
            store.dispatch("monitor1/handleGraphData");
            store.dispatch("monitor1/flowPressure");
            store.dispatch("monitor1/distribution");
        });
        watch(() => store.state.monitor1.alarmFlag, function () {
            store.state.monitor1.alarmData?.forEach(alarmElement => {
                alarmElement.forEach(alarmItem => {
                    store.state.monitor1.modelList.forEach(element => {
                        element.forEach(item => {
                            if (item.id === alarmItem.motor_id)
                                item.alarm = alarmItem.Alarm
                        })
                    });
                })
            });
        })
        const select = (idx) => {
            let val = idx - 1;
            store.state.monitor1.sampleData.idx = val;
            store.state.monitor1.modelList[0][val].alarm = true;
            store.state.monitor1.modelList[0][val].motor_de_amp =
                store.state.monitor1.modelList[0][idx - 1].motor_de_amp.concat(
                    store.state.monitor1.sampleData.motor_de_rms_amp
                );
            store.state.monitor1.modelList[0][val].motor_nde_amp =
                store.state.monitor1.modelList[0][val].motor_nde_amp.concat(
                    store.state.monitor1.sampleData.motor_nde_rms_amp
                );
            store.state.monitor1.modelList[0][val].pump_de_amp =
                store.state.monitor1.modelList[0][val].pump_de_amp.concat(
                    store.state.monitor1.sampleData.pump_de_rms_amp
                );
            store.state.monitor1.modelList[0][val].pump_nde_amp =
                store.state.monitor1.modelList[0][val].pump_nde_amp.concat(
                    store.state.monitor1.sampleData.pump_nde_rms_amp
                );
            store.state.monitor1.mode = true;

            // axios.get('http://localhost:35000/siyeon?songsu=' + idx);
        };
        const selectReset = () => {
            store.state.monitor1.mode = false;
            axios.get(`http://${store.state.globalIP}/reset`);
            window.location.reload(true);
        };

        return {
            visibleToggle,
            select,
            selectReset,
            store,
            scatterPTKData,
            scatterSSNData
        };
    },
    data() {
        return {
            title_one: { name: '' },
            title_two: { name: '' },
            StatusTitle_one: { name: '' },
            StatusTitle_two: { name: '' },
            heightCss: '',
            isModalOpen: false
        }
    },
    mounted() {
        this.namechange();
        setInterval(() => {
            location.reload(); // 페이지를 새로고침
        }, 5 * 60 * 1000);
    },
    methods: {
        namechange() {
            const store = useStore();
            const area = store.state.area;
            if (area == 'gosan') {
                this.title_one.name = '고산정수장 송수펌프모터'
                this.title_two.name = '고산정수장 송수펌프모터'
                this.StatusTitle_one.name = '(구)정수지 운영현황'
                this.StatusTitle_two.name = '(신)정수지 운영현황'
                this.heightCss = 'heightCssStyleForGosan'
            } else if (area == 'gumi') {
                this.title_one.name = '신평(생활)계통'
                this.StatusTitle_one.name = '신평(생활)계통 운영현황'
                this.heightCss = 'heightCssStyleForGumi'
            } else if (area == 'hakya') {
                this.title_one.name = '임하가압장'
                this.StatusTitle_one.name = '임하가압장 운영현황'
                this.heightCss = 'heightCssStyleForHakya'
            }
        },
        openModal(dataAll, title) {
            this.isModalOpen = true;
            this.$refs.ModalComp.createChart(dataAll, title)
        },
        closeModal() {
            this.isModalOpen = false;
        },
    },


};
</script>

<style>
.heightCssStyleForHakya {
    height: 100% !important;
}

.heightCssStyleForGumi {
    height: 100% !important;
}
.heightCssStyleForGosan{
    height: 850px !important;
}
</style>
