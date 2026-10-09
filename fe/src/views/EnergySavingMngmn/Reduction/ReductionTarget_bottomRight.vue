<template>
  <b-col class="position-relative div-new">
    <div class="d-flex justify-content-center align-items-center p-2" v-bind:style="{ width: '94%', height: '100%' }">
      <BarChart ref="BarChart" />
    </div>
    <div class="position-absolute"
      v-bind:style="{ top: '0', right: '15px', width: '3%', height: '98%', display: 'inline-block' }">
      <img src="@/assets/img/image_01.png" v-bind:style="{ marginTop: '640%', float: 'right' }" alt="" />
    </div>
  </b-col>
</template>

<script>
import BarChart from "@/components/Chart/AreaChart.vue"
import BarChartClass from "@/components/Chart/BasicBarChartClass";
export default {
  components: {
    BarChart
  },
  methods: {
    makeChart(labels, datas) {
      let chartClass = new BarChartClass(datas, labels, ['사용량', '목표량']);
      chartClass.setGridSize('15%', '3%', '10%', '10%')
      this.$refs.BarChart.changeData(chartClass)
    }
  }
}
</script>
<style scoped>
.div-new {
  background-image: url(/src/assets/img/div_new.png);
  background-size: 100% 100%;
  display: inline-block;
}
</style>