<template>
  <b-col xl="5 px-4">
    <b-row>
      <small-title :title="title"></small-title>
    </b-row>
    <b-row v-bind:style="{ height: '95%', width: '100%' }">
      <b-col v-bind:style="{ height: '95%', width: '100%' }" class="d-flex justify-content-center align-items-center">
        <area-chart ref="AreaChart" />
      </b-col>
    </b-row>
  </b-col>
</template>

<script >
// import * as echarts from "echarts";
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
import AreaChart from "@/components/Chart/AreaChart.vue";
import ChartClass from "@/components/Chart/ChartClass.js";


export default {
  components: { SmallTitle, AreaChart },
  data() {
    return {
      title: "설비 트렌드",
      DATE: [],
      option: null,
      value: 0
    };
  },

  methods: {
    chartMake(dataX, dataY, legend) {
      if (dataX && dataY && legend) {
        let chartClass = new ChartClass(dataX, dataY, [legend], null, "날짜", "kWh")
        chartClass.changeSingleChart();
        chartClass.legendHide();
        chartClass.setGridSize('5%', '8%', '10%', 10, true)
        this.$refs.AreaChart.changeData(chartClass);
      } else {
        this.$refs.AreaChart.changeData();
      }

    },






  }


}
</script>