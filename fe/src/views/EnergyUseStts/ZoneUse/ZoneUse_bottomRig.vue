<template>
  <b-col xl="6">
    <SmallTitle :title="'트렌드'" />
    <div class="d-flex justify-content-center align-items-center p-2">
      <area-chart ref="AreaChart" :style="{ height: '380px', width: '100%' }" />
    </div>
  </b-col>
</template>

<script>
import AreaChart from "@/components/Chart/AreaChart.vue";
import SingleChartClass from "@/components/Chart/SingleChartClass.js";
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
export default {
  components: { AreaChart, SmallTitle },
  props: ["items"],
  data() {
    return {
      index: 0,
    };
  },
  mounted() { },
  updated() { },
  methods: {
    createChart(data1, sumData) {
      let dataX = [];
      let dataY = [];
      let labels = [];
      let flag = false;
      let length = 0;
      sumData.forEach((element) => {
        const filteredData1 = data1?.filter(item => item.zone_code === element);
        if (filteredData1.length != 0) {
          length = filteredData1.length
        }
      })
      sumData.forEach((element, i) => {
        let tmpY = [];
        const filteredData1 = data1?.filter(item => item.zone_code === element);
        data1.forEach((item) => {
          if (element == item.zone_code) {
            if (flag == false) {
              this.index = i
              flag = true;
            }
          }
        })
        if (filteredData1.length == 0) {
          for (let j = 0; j < length; j++) {
            tmpY.push(0)
          }
        } else {
          filteredData1.forEach(element => {
            tmpY.push(element.y)
          })
        }
        dataY.push(tmpY);
      })
      const filteredData = data1?.filter(item => item.zone_code === sumData[this.index]);

      filteredData.forEach(element => {
        dataX.push(element.x)
      })
      this.items.forEach(item => {
        item.forEach(element => {
          if (element.title != "NO DATA") {
            labels.push(element.title)
          }
        })
      })
      let chartClass = new SingleChartClass(dataX, dataY, labels, false, '날짜', 'kWh', this.index)
      chartClass.legendOption('scroll', 'vertical', true, 'right', 0, '10%', 'auto')
      chartClass.setGridSize(20, '15%', '10%', 10, true)
      this.$refs.AreaChart.changeData(chartClass);
    },
  },
};
</script>

<style></style>
