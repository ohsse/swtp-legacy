<template>
    <div class="top-contents-box" style="height: 330px;">
        <area-chart ref="AreaChart" :style="{ height: '330px', width: '100%' }" />
    </div>
</template>

<script>
import AreaChart from '@/components/Chart/AreaChart.vue';
import ChartClass from '@/components/Chart/ChartClass';
export default {
    components: {
        AreaChart,
    },
    methods: {
        createChart(data) {
            let dataX = [];
            let dataY = [];

            data?.trand_list?.forEach(element => {
                dataX.push(element.ts)
                dataY.push(element.value)
            })
            let chartClass = new ChartClass(dataX, [dataY], [""], false, '날짜', 'kWh')
            this.$refs.AreaChart.changeData(chartClass)
        }
    }
}
</script>

<style>
.box_bt_area {
    height: 40px;
    display: flex;
    align-items: center;
    margin: 5px 0;
    justify-content: flex-end;
}

.top-contents-box {
    display: flex;
    align-content: flex-end;
    justify-content: center;
    flex-wrap: wrap;
    padding: 10px 10px 24px 10px;

}
</style>