<template>
  <b-col xl="3">
    <small-title :title="title"></small-title>
    <!-- <p>{{facName}}</p>
    <p>{{trandY}}</p> -->
    <div class="d-flex justify-content-center align-items-center p-2" id="sumGrid" v-bind:style="{ height: '500px' }">
      <!-- <span>라인 챠트 영역</span> -->
      <area-chart ref="AreaChart" />
    </div>
  </b-col>
</template>

<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
import AreaChart from "@/components/Chart/AreaChart.vue";
import BarChartClass from "@/components/Chart/BarChartClass.js"
export default {
  components: { SmallTitle, AreaChart },
  props: {
    facName: Array,
    trandY: Array,
  },
  data() {
    return {
      title: "설비별 평균",
    }
  },
  methods: {
    initChart(datas, labels) {

      
      if (datas && labels) {
        let barChart = new BarChartClass(datas, labels);
        barChart.axisChange("y");
        barChart.toggleDataLabels('right')
        barChart.setGridSize('30%', '10%', '10%', '33%')
        this.$refs.AreaChart.changeData(barChart);
      } else {
        this.$refs.AreaChart.changeData();
      }

    }
  }
}
</script>