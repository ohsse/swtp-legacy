<template>
  <div class="chart">
    <v-chart class="BarChart" :option="option" style="height: 335px" autoresize />
  </div>
</template>

<script>
import { reactive, onMounted } from "vue";
import VChart from 'vue-echarts';

export default {
  props: ['BarData', 'labels', 'legend'],
  components: { VChart },
  setup(props) {
    const option = reactive({
      tooltip: {
        trigger: 'item'
      },
      xAxis: {
        data: props.labels,
        type: "category",
        axisLine: {
          show: true,
          lineStyle: {
            color: "#FFFFFF",
          },
        },
        axisLabel: {
          rotate: 35,
          color: "#fff",
          fontSize: 10,
          interval: 0
        },
      },
      yAxis: {
        type: "value",
        splitLine: {
          show: false, // 구분선을 표시하지 않도록 설정
        },
        axisLine: {
          show: true,
          lineStyle: {
            color: "#FFFFFF",
          },
        },
        axisLabel: {
          color: "#fff",
          fontSize: 13,
        },
      },
      legend: {
        data: props.legend, // 범례 항목 설정
        textStyle: {
          color: "#fff", // 범례 텍스트 색상 설정
        },
      },
      series: [],
    });

    onMounted(() => {
      // 그래프 초기화 및 렌더링 작업
      let series = [];
      props.BarData.forEach((element, i) => {
        let seriesObj = {
          data: element,
          type: 'bar',
          name: props.legend[i],
          label: {
            show: true,
            position: 'top',
            color: "#fff",
          },
        };
        series.push(seriesObj);
      });
      option.series = series;
    });


    return { option, };
  },
};
</script>

<style></style>
