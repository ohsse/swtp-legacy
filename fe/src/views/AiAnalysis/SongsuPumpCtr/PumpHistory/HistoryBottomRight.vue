<template>
    <b-col v-bind:style="{ height: '95%', width: '100%' }" class="d-flex justify-content-center align-items-center">
        <PlotlyHeatmapChart ref="HeatmapChart"/>
    </b-col>
</template>
<script>
import PlotlyHeatmapChart from '@/components/Chart/PlotlyHeatmapChart.vue';
export default {
    components:{
        PlotlyHeatmapChart
    },
    methods:{
        initChart(dates, labels, datas, selected, xAxisCount){
            
            this.$refs.HeatmapChart.makeChart(dates, labels, datas, selected, xAxisCount)
        }
    }
}
</script>