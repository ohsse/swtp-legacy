<template>
  <b-col xl="3">
    <SmallTitle :title="'분포'" />
    <div class="d-flex justify-content-center align-items-center p-2" id="distGrid" v-bind:style="{ height: '410px' }">
      <DoughnutChart ref="DoughnutChart" :style="{ height: '100%', width: '100%' }" />
    </div>
  </b-col>
</template>

<script>
import DoughnutChart from "@/components/Chart/DoughnutChart.vue";
import DoughnutChartClass from "@/components/Chart/DoughnutChartClass.js";
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';

export default {
  components: {
    DoughnutChart,
    SmallTitle
  },
  mounted() {
  },
  methods: {
    createChart(data) {
      if (data) {
        let chartClass = new DoughnutChartClass(data, ["30%", "50%"], ['35%', '50%']);
        chartClass.changeLegendFontSize(9)
        chartClass.legendOption('scroll', 'vertical', true, 'right', 0, 'auto', 'auto')
        // chartClass.setGridSize(10,'70%','15%',10,true)
        this.$refs.DoughnutChart.changeData(chartClass);
      } else {
        this.$refs.DoughnutChart.changeData();
      }
    },
  }
}
</script>