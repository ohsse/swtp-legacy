<template>
  <div class="d-flex justify-content-center align-items-center" v-bind:style="{ height: '100%', width: '100%' }">
    <span v-show="!noData">No Data</span>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { shallowRef } from 'vue';

export default {
  props: ['areaChartData'],
  data() {
    return {
      myChart: shallowRef(null),
      noData: true,
      checkData: true
    };
  },
  mounted() {
    if (this.areaChartData) {
      this.changeData(this.areaChartData);
    }
  },

  methods: {
    changeData(dataAll) {
      if (dataAll) {
        this.checkData = true
      } else {
        this.checkData = false
      }

      // 기존에 추가된 내용이 있다면 제거
      const existingAdditionalContent = this.$el.querySelector('.additional-content');
      if (existingAdditionalContent) {
        existingAdditionalContent.remove();
      }

      if (this.myChart != null && this.myChart != '' && this.myChart != undefined) {
        this.myChart.dispose();
      }
      if (this.checkData) {
        dataAll.series.forEach(element => {
          if (element.data && element.data.length > 0) {
            this.noData = true;
            this.myChart = echarts.init(this.$el);
            this.myChart.setOption(dataAll);
            window.onresize = () => {
              this.myChart.resize();
            };
          }
        });
      } else {
        // this.noData = false;
        const additionalContent = document.createElement('div');
        additionalContent.className = 'additional-content';
        additionalContent.innerHTML = '<p>No Data.</p>';
        this.$el.appendChild(additionalContent);
      }
    },
    resizeChart() {
      this.myChart.resize()
    }
  },
};
</script>
