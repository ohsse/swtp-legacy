<template>
    <div class="align-itmes-center justify-content-center">
        <DoughnutChart ref="DoughnutChart" :style="{ height: '100%', width: '100%' }"/>
    </div>
</template>
<script>
import DoughnutChart from "@/components/Chart/DoughnutChart.vue";
import DoughnutChartClass from "@/components/Chart/DoughnutChartClass.js";
export default {
    components:{
        DoughnutChart
    },
    methods:{
        createChart(data){
            let chartClass = new DoughnutChartClass(data, ["40%", "90%"], ['35%', '50%']);
            chartClass.changeLegendFontSize(9)
            chartClass.legendOption('scroll','vertical',true,'right',0,'auto','auto')
            this.$refs.DoughnutChart.changeData(chartClass);
        }
    }
}
</script>