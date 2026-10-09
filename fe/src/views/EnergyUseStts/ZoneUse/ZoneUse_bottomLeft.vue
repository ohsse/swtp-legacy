<template>
  <b-col xl="3">
    <SmallTitle :title="'합계'" />
    <div class="d-flex justify-content-center align-items-center p-2">
      <area-chart ref="AreaChart" :style="{ height: '410px', width: '100%' }" />
    </div>
  </b-col>
</template>

<script>
import AreaChart from "@/components/Chart/AreaChart.vue";
import BarChartClass from "@/components/Chart/BarChartClass.js";
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
export default {
  components: { AreaChart, SmallTitle },
  props: ["items"],
  data() {
    return {};
  },
  mounted() { },
  updated() { },
  methods: {
    createChart(data, sumData) {
      let chartData = []
      let labels = [];
      sumData.forEach((element) => {
        const filteredData = data?.filter(item => item.zone_code == element)
        if (filteredData.length == 0) {
          chartData.push(0)
        } else {
          chartData.push(filteredData[0].y)
        }
      });
      this.items.forEach(item => {
        item.forEach(element => {
          if (element.title != "NO DATA") {
            labels.push(element.title)
          }
        })
      })
      let chartClass = new BarChartClass(chartData, labels, 'kwh', '시설명')
      chartClass.axisChange("y");
      chartClass.changeLegendShow()
      chartClass.setGridSize('23%', '10%', '10%', '15%')
      chartClass.toggleDataLabels('right')
      chartClass.changeAxisLabelRotation(20)
      this.$refs.AreaChart.changeData(chartClass);

    },
  },
};
</script>

<style></style>
