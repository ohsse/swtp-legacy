<template>
  <b-col v-bind:style="{ height: '95%', width: '100%' }" class="d-flex justify-content-center align-items-center">
    <!-- <AreaChart ref="AreaChart"/> -->
    <PlotlyHeatmapChart ref="HeatmapChart" />
  </b-col>
</template>
<script>
// import AreaChart from '@/components/Chart/AreaChart.vue';
// import FrqncBarChartClass from '@/components/Chart/FrqncBarChartClass';
import PlotlyHeatmapChart from '@/components/Chart/PlotlyHeatmapChart.vue';
export default {
  components: {
    // AreaChart,
    PlotlyHeatmapChart
  },
  methods: {
    initChart(dates, labels, datas, selected, desc) {

      // console.log("🚀 ~ file: HistoryBottomRight.vue:15 ~ initChart ~ dates, labels, datas:", dates, labels, datas)
      this.$refs.HeatmapChart.makeChart(dates, labels, datas, selected, desc)
    }
  }
}
</script>