<template>
  <div class="d-flex justify-content-center align-items-center" v-bind:style="{ height: '100%', width: '100%' }">
  </div>
</template>

<script>
import * as echarts from "echarts";
import { shallowRef } from "vue";
export default {
  components: {},
  props: ["areaChartData", "isModalChart", "isModalChartDia"],
  data() {
    return {
      myChart: shallowRef(null),
    };
  },
  watch: {
    areaChartData: function () {
      this.changeData(this.areaChartData);
    },
    isModalChart: function () {
      this.toggleToolbox();
    },
  },
  mounted() {
    const myChart = echarts.init(this.$el);
    myChart.showLoading("default", {
      text: "Loading...",
      textColor: "#fff",
      maskColor: "rgba(22, 30, 55, 0.8)",
    });
    if (this.areaChartData) {
      this.changeData(this.areaChartData);
    }
  },
  updated() { },
  methods: {
    toggleToolbox() {
      if (this.isModalChart == true) {
        // If isModalChart is true, hide the toolbox
        this.myChart.setOption({
          toolbox: {
            show: true,
            iconStyle: {
              borderColor: "#fff",
            },
            feature: {
              dataZoom: { show: true },
            },
          },
        });
      } else if(this.isModalChartDia == true){

        this.myChart.setOption({
          toolbox: {
            show: true,
            iconStyle: {
              borderColor: "#fff",
            },
            feature: {
              dataZoom: { show: true },
              myExcel: {
                  show: true,
                  title: "CSV Download",
                  icon: "path://M0 11.5H12M6 0V8.5M6 8.5L2.5 5.5M6 8.5L9.5 5.5",
                  onclick: () => {
                    this.$emit('downloadCSV')
                  },
                },
            },
          },
        });
      } 
      
      
      else {
        // If isModalChart is false, show the toolbox
        this.myChart.setOption({
          toolbox: {
            top : '-3%',
            itemSize : 10,
            show: true,
            iconStyle: {
              borderColor: "#fff",
            },
            feature: {
              dataZoom: { show: true },
              myModal: {
                show: true,
                title: "Open Chart",
                icon: "path://M5 0.5H0.5V6.5M11.5 7V11.5H5.5M7 0.5H11.5M11.5 0.5V5M11.5 0.5L7.5 4.5M0.5 6.5V11.5H5.5M0.5 6.5H5.5V11.5",
                onclick: () => {
                  this.$emit('modalClick', this.areaChartData)
                },
              },
              myExcel: {
                show: true,
                title: "CSV Download",
                icon: "path://M0 11.5H12M6 0V8.5M6 8.5L2.5 5.5M6 8.5L9.5 5.5",
                onclick: () => {
                  this.$emit('downloadCSV')
                },
              },
            },
          },
        });
      }
    },
    changeData(dataAll) {
      if (this.myChart != null && this.myChart != "" && this.myChart != undefined) {
        this.myChart.dispose();
      }

      this.myChart = echarts.init(this.$el);
      this.myChart.setOption(dataAll);
      const chartOptions = this.myChart.getOption();

      if (chartOptions && chartOptions.series && chartOptions.series.length > 0) {
        // If there is data, hide the loading animation (if it's visible)
        this.myChart.hideLoading();
      } else {
        this.myChart.hideLoading();
        this.myChart.setOption({
          graphic: [
            {
              type: "text",
              left: "center",
              top: "center",
              style: {
                text: "No Data",
                fill: "#fff",
                fontSize: 16,
              },
            },
          ],
          xAxis: {
            show: false, // Hide the X-axis
          },
          yAxis: {
            show: false, // Hide the Y-axis
          },
        });
      }
      this.toggleToolbox();
      window.onresize = () => {
        this.myChart.resize();
      };
      this.myChart.on('click', (p)=>{
        this.myChart.dispatchAction({
          type: 'highlight',
          seriesIndex: 0,
          dataIndex: p.dataIndex
        });
        this.$emit('chartClick', p.name);
      })
    },
    disposeData() {
      if (this.myChart != null) {
        this.myChart.dispose();
      }
    },
    resizeChart() {
      this.myChart.resize();
    },
  },
};
</script>

<style></style>
