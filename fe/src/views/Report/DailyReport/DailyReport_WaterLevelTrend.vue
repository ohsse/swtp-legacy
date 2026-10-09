<template>
  <div style="height: 300px; !important">
    <area-chart ref="AreaChart" />
  </div>
</template>

<script>
import AreaChart from "@/components/Chart/AreaChart.vue";
import ChartLineClass from '@/components/Chart/ChartLineClass';
export default {
  components: {
    AreaChart
  },
  data() {
    return {
      DATE: [],
      option: null,
      value: 0,
    };
  },

  methods: {
    initData(data) {
      // console.log("수위트렌드 그래프 ", data);
      if (data !== null) {
        let date = [];
        let label = []
        data.data.forEach((item) => {
          if (!date.includes(item.ts)) {
            date.push(item.ts)
          }
        })
        data.data.forEach((item) => {
          if (!label.includes(item.TNK_GRP_NM)) {
            label.push(item.TNK_GRP_NM)
          }
        })

        let chartY = [[], []]
        data.data.forEach((data) => {
          // 구정수지
          if (data.TNK_GRP_IDX == 1) {
            chartY[0].push(data.value)
          } else {
            chartY[1].push(data.value)
          }
        })

        this.$refs.AreaChart.changeData(
          new ChartLineClass(date, [chartY[0], chartY[1]], label, null, "날짜", "kWh")
        );
      }
    },
  }
}
</script>