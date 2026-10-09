<template lang="">
    <b-row class="row-cols-1 g-2 text-center" >
      <b-col xl="3">
          <area-chart ref="AreaChart" :style="{ height: botMidCellHeight ? botMidCellHeight : '50px', width: '100%' }" />
      </b-col>
        <b-col xl="2">
          <div class="plate_img p-3" :style="{ height: botMidCellHeight ? botMidCellHeight : '50px', backgroundSize: 'contain !important' }">
            <span class="detail_value"
              :style="{ width: 'auto', fontSize: '20px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">{{cur}}</span>
          </div>
        </b-col>
        <b-col xl="2"
          class="d-flex justify-content-center align-items-center area_title"><span style="font-size: 14px;" v-html="title"></span>
        </b-col>
          <b-col xl="3">
            <area-chart ref="AreaChart1" :style="{ height: botMidCellHeight ? botMidCellHeight : '50px', width: '100%' }" />
        </b-col>
        <b-col xl="2" class="position-relative">
          <div class="plate_img w-100 p-3" :style="{ height: botMidCellHeight ? botMidCellHeight : '50px', backgroundSize: 'contain !important' }">
            <span class="detail_value"
              :style="{ width: 'auto', fontSize: '20px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">{{pre}}</span>
          </div>
          <div class="position-absolute start-50 translate-middle-x" :style="{ bottom: '-22px' }"><span
              :style="{ fontSize: '14px', fontWeight: 'bold', color: 'rgb(100 202 255)' }">{{rate}}%</span></div>
        </b-col>
      </b-row>
</template>

<script>
import AreaChart from '@/components/Chart/AreaChart.vue';
import ChartClass from '@/components/Chart/ChartClass';
export default {
  components: {
    AreaChart,
  },
  props: ['title', 'cur', 'pre', 'rate', 'botMidCellHeight'],
  mounted() {
  },
  methods: {
    createChart(data, ts, max, min) {
      let dataY = data;
      const formattedDates = ts.map(dateString => {
        const date = new Date(dateString);
        return `${date.getDate()}일 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
      });
      let chartClass
      if (min || max) {
        chartClass = new ChartClass(formattedDates, [dataY], [""], false, '날짜', 'kWh', null, false, max, min)
      } else {
        chartClass = new ChartClass(formattedDates, [dataY], [""], false, '날짜', 'kWh', null, false)
      }
      chartClass.setGridSize('0%', '3%', '15%', '0%')
      this.$refs.AreaChart.changeData(chartClass)
    },
    createPreChart(curData, preData, ts) {
      let dataY = [curData, preData]
      const formattedDates = ts.map(dateString => {
        const date = new Date(dateString);
        return `${date.getDate()}일 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
      });
      let chartClass
      chartClass = new ChartClass(formattedDates, dataY, [""], false, '반투명', 'kWh', null, false)
      chartClass.setGridSize('0%', '3%', '15%', '0%')
      this.$refs.AreaChart1.changeData(chartClass)
    }
  }
}
</script>
<style>
.area_title {
  background: linear-gradient(90deg, rgba(20, 65, 136, 0) 0%, rgba(20, 65, 136, 1) 20%, rgba(20, 65, 136, 1) 80%, rgba(20, 65, 136, 0) 100%);
}
</style>