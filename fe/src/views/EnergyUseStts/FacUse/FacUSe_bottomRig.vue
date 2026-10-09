<template>
  <b-col xl="6">
    <SmallTitle :title="'순시 전력'" />
    <AreaChart ref="AreaChart" v-bind:style="{ height: '380px' }"></AreaChart>
  </b-col>
</template>

<script>
// import * as echarts from "echarts";
import AreaChart from '@/components/Chart/AreaChart.vue';
import ChartLineClass from '@/components/Chart/ChartLineClass';
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
export default {
  components: {
    AreaChart,
    SmallTitle
  },
  mounted() {
    // this.initChart();
  },
  methods: {
    initChart(x, y, fac_name) {
      if(x.length > 0 ){
        let chartLineClass = new ChartLineClass(x, y, fac_name, null, "날짜", "kW");
        chartLineClass.legendOption('scroll', 'vertical', true, 'right', 0, 30, 'auto')
        chartLineClass.setGridSize('10%', '25%', '13%', 10, true)
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