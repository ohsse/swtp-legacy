<template>
  <div class="chart">
    <v-chart class="piechart" :option="option" style="height: 300px" autoresize />
  </div>
</template>
<script>
import VChart from 'vue-echarts'
import { onMounted, reactive } from 'vue'
export default {
  props: ['pieData', 'labels', 'legend'],
  components: { 'v-chart': VChart },
  setup(props) {
    const option = reactive({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        data: props.legend, // 범례 항목 설정
        textStyle: {
          color: "#fff", // 범례 텍스트 색상 설정
        },
      },
      series: []
    });

    onMounted(() => {
      drawChart()
    })

    const drawChart = () => {
      const datas = []
      props.pieData?.map((item, i) => {
        datas.push({ value: item, name: props.legend[i] })
      })
      let seriesObj = {
        data: datas,
        type: 'pie',
        radius: ['40%', '65%'],
        name: { show: false },
        label: {
          show: false,
          position: 'top',
          formatter: '{b}: {d}%'
        },
        emphasis: {
          scale: true
        }
      }
      option.series = seriesObj
      console.log('option', option.series)
    }
    return {
      option
    }
  }
}
</script>
<style></style>
