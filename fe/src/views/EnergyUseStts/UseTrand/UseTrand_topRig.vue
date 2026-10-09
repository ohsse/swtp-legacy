<template>
    <div class="box_bt_area"></div>
    <div class="top-contents-box" style="height: 330px;">
        <area-chart ref="AreaChart" :style="{ height: '330px', width: '100%' }" />
    </div>
</template>

<script>
import AreaChart from "@/components/Chart/AreaChart.vue";
import BarChartClass from "@/components/Chart/BarChartClass.js";
export default {
    components: {
        AreaChart,
    },
    data() {
        return {
        }
    },
    methods: {
        createChart(data) {
            let peakData = data.peak_max
            let chartData = []
            let labels = [];
            // this.array.forEach((element, i) => {
            //     if (peakData[i] != null) {
            //         chartData.push(peakData[i]['value'])
            //         labels.push(this.label[i])
            //     }
            // })

            peakData.forEach(element => {
                chartData.push(element.value);
                labels.push(element.peak_date)
            });
            let chartClass = new BarChartClass(chartData, labels, '날짜', 'kwh')
            chartClass.changeAxisLabelRotation(0)
            chartClass.setGridSize('10%', '10%', '10%', '10%')
            chartClass.toggleDataLabels('top')
            // chartClass.changeAxisLabel();
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