<template>
    <div class="content-container-row" :style="gumiHeight">
        <PumpMotorImg :item="item.title" :error="item.alarm" :none="!item.eq_on" :index="index" :number="item.scada_id.slice(-2)"/>

        <div class="chart-area" :style="gumiChartArea">
            <div class="alert-icon">
                <PumpStateArea :error="item.eq_on" :area="this.area" />
                <PumpValueArea :pumpValue="item.threshold" :motorValue="item.threshold" :area="this.area" />
                <PumpTitleArea :item="item" :area="this.area" />
            </div>
                <div class="chart-con" :style="gumiChartCon">
                    <Frame /> 
                    <LineChart :name1='["펌프 부하", "펌프 반부하","모터 부하", "모터 반부하"]'
                    :detailData="[item.pump_de_amp, item.pump_nde_amp, item.motor_de_amp, item.motor_nde_amp]"
                    :threshold = "threshold"
                    :chartTitle="item.title" :isPump="isPump"
                    :yName="'rms(mm/s)'" @showModal="showModal" :fixY="1" />
                </div>
        </div>
    </div>
</template>
<script>
import PumpMotorImg from '@/views/PumpControl/PumpContentContainer/PumpMotorImg.vue';
import PumpStateArea from '@/views/PumpControl/PumpContentContainer/PumpStateArea.vue';
import PumpValueArea from '@/views/PumpControl/PumpContentContainer/PumpValueArea.vue';
import PumpTitleArea from '@/views/PumpControl/PumpContentContainer/PumpTitleArea.vue';
import Frame from '@/components/component/BoxFrame.vue';
import LineChart from '@/components/chart/monitoring/Linechart_d.vue';
import { useStore } from 'vuex';
export default {
    components: {
        PumpMotorImg,
        PumpStateArea,
        PumpValueArea,
        PumpTitleArea,
        Frame,
        LineChart,
    },
    props: ['item', 'index','isPump'],
    data() {
        // api 받는 기준선 
        // let threshold = this.item.threshold?.filter(thItem=>{
        //     if(thItem.graph_type == 'de_rms_amp'){
        //         thItem.koTitle = thItem.eq_type == 'pump'?'펌프 부하':thItem.eq_type == 'motor'?'모터 부하':undefined
        //         return thItem.koTitle !== undefined;
        //     }
        //     return false;
        // })
        let threshold = [
            {"koTitle" : '주의' , "value" : 4.2},
            {"koTitle" : '경고' , "value" : 6.1},
        ]
        return {
            gumiHeight: '',
            gumiChartArea: '',
            gumiChartCon: '',
            area: '',
            threshold : threshold,
        }
    },
    mounted() {
        const store = useStore();
        this.area = store.state.area;
        if (this.area === 'gumi') {
            this.gumiHeight = 'height:210px'
            this.gumiChartArea = 'width:1530px'
            this.gumiChartCon = 'width:1010px; height:190px'
        } else {
            this.gumiHeight = ''
            this.gumiStyle = ''
            this.gumiChartArea = ''
        }
    },
    methods: {
        showModal(dataAll) {
            this.$emit('openModal', dataAll, this.item.title)
        },
    }

}
</script>
<style >
.downloadBtn{
    border: solid 1px #b4dffa;
    background-color: rgba(139, 194, 240, 0.25);
    cursor: pointer;
    color: #fff;
    width: 47px;
    border-radius: 4px;
}
</style>