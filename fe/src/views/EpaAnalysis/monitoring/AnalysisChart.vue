<template>
  <AreaChart ref="AreaChart"></AreaChart>
</template>
<script>
// import * as echarts from "echarts";
import AreaChart from '@/components/Chart/AreaChart.vue';
import ChartLineClass from '@/components/Chart/ChartLineClass';
export default {
  components: {
    AreaChart
  },
  mounted() {
    // this.initChart();
  },
  methods: {
    initChart(x, y, unit) {
      if(x.length > 0 ){
        let chartLineClass = new ChartLineClass(x, y, ["계측값", "분석값"], null, "날짜", unit);
        chartLineClass.legendOption('scroll', 'horizontal', true, 'center', 'auto', 5, 'auto')
        chartLineClass.setGridSize('3%', '5%', '13%', 10, true)
        this.$refs.AreaChart.changeData(chartLineClass);
      }else{
        this.$refs.AreaChart.changeData();
      }
    }
  },
}
</script>
<style>
.pumpLoading {
  margin-top: -50px;
}
</style>