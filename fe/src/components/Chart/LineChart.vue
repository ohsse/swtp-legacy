<template>
    <div class="d-flex justify-content-center align-items-center p-3" id="peakChart"
        v-bind:style="{ height: '340px', width: '1140px' }">
        <span v-show="this.dataAll?.length === 0">라인 챠트 영역</span>
    </div>
</template>

<script>
import * as echarts from "echarts";
import ChartClass from './ChartClass.js';

export default {
    props: {
        dataAll: ChartClass,
    },
    data() {
        let chartTrand = this.dataAll
        return chartTrand
    },

    methods: {
        initChart() {
            let myChart = echarts.init(document.getElementById('peakChart'));
            if (myChart != null && myChart != '' && myChart != undefined) {
                myChart.dispose(); //차트돔이 먼저 생성된 경우 기존 돔을 삭제해준다
            }

            myChart = echarts.init(document.getElementById('peakChart'));


            myChart.setOption(this.chartTrand);
            window.onresize = () => {
                myChart.resize();
            };
        },
        changeData(dataAll) {
            this.chartTrand = dataAll;
            this.initChart();
        }
    },

}
</script>

<style></style>