<template>
  <b-col xl="3">
    <SmallTitle :title="'분포도'" />
    <div class="d-flex justify-content-center align-items-center p-2">
      <DoughnutChart ref="DoughnutChart" :style="{ height: '410px', width: '100%' }" />
    </div>
  </b-col>
</template>

<script>
import DoughnutChart from "@/components/Chart/DoughnutChart.vue";
import DoughnutChartClass from "@/components/Chart/DoughnutChartClass.js";
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
export default {
  components: { DoughnutChart, SmallTitle },
  data() {
    return {};
  },
  mounted() { },
  updated() { },
  methods: {
    createChart(data) {
      let chartData = [];
      let obj
      data.forEach((item) => {
        if (item.zone_code != '총전력' && item.zone_code != '총전력량') {
          obj = { value: item.y, name: item.zone_code };
          chartData.push(obj);
        }
      });
      let chartClass = new DoughnutChartClass(chartData, ["40%", "70%"], ['35%', '50%']);
      chartClass.changeLegendFontSize(13)
      chartClass.legendOption('scroll', 'vertical', true, 'right', 0, 'auto', 'auto')
      this.$refs.DoughnutChart.changeData(chartClass);
    },
  },
};
</script>

<style></style>
