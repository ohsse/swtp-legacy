<template>
  <b-row class="px-3">
    <div class="" :style="{ height: '256px' }">
      <b-col class="pt-0">
        <h5 class="dash_title" :style="{ height: '50px' /*lineHeight: '25px'*/ }">피크 관리</h5>
      </b-col>
      <b-col class="mx-3 pt-3" :style="{ height: '200px' }">
        <AreaChart ref="AreaChart"></AreaChart>
      </b-col>

    </div>
  </b-row>
</template>

<script>
import AreaChart from "@/components/Chart/AreaChart.vue";
import ChartClass from "@/components/Chart/ChartClass.js";
export default {
  components: {
    AreaChart,
  },
  methods: {
    initData(data, goal) {
     
      // console.log("자식2 = " + data);
      if (data !== null) {
        // console.log("peakTime success");
        let dataX = [];
        let dataY = [[], []];
        for (let i = 0; i < data.data?.length; i++) {
          dataX.push(data.data[i]["DATE"]);
          let pwr = data.data[i]["PWR"];
          let prdctPwr = data.data[i]["PRDCT_PWR"];
          if (isNaN(prdctPwr)) {
            dataY[1].push(0);
          } else {
            dataY[1].push(prdctPwr);
          }
          if (isNaN(pwr)) {
            // dataY[0].push[0];
          } else {
            dataY[0].push(pwr);
          }
          dataY[0].slice(0, new Date().getHours() + 1)
          if (data.data[i]["PEAK_YN"] == "Y") {
            // console.log("peak_yn 값이 1일 경우 날짜" + data.data[i]["DATE"]);
            this.peakTime = data.data[i]["DATE"].substring(11);
            this.$emit("peakTime", this.peakTime);
            // console.log(this.peakTime);
          }
        }
        const detline = goal.data[0]["value"];

        let chartClass = new ChartClass(dataX, dataY, ["발생 전력", "예상 전력"], detline, "날짜", "kWh")
        chartClass.setGridSize('7%', '10%', '15%', '0%')
        chartClass.noDetLineName();
        this.$refs.AreaChart.changeData(chartClass);
      }
    }
  },
}
</script>

<style>
.waterwall_back_gosan {
  position: absolute;
  top: 143px;
  left: 0;
  width: 1590px;
  height: 690px;
  background: url(@/assets/img/local_geumgang/gosan/waterwall_gosan.png) no-repeat;
  background-size: 67% 97%;
  background-position: 56% 83%;
}

.offPump {
  background-color: #5b49491f !important;
}

.off_pump_img {
  width: 250px;
  height: 60px;
  background: #1A406F;
  opacity: 0.8;
  align-self: center;
  color: #F8C314;
  font-size: 21px;
  font-weight: bold;
  font-family: KHNPHDRegular;
  border: 2px solid #00C0FF;
  text-align: center;
  line-height: 57px;
  letter-spacing: 5px;
}

.pump_name {
  color: rgb(255, 255, 255);
  font-size: 21px;
  line-height: 57px;
  letter-spacing: 5px;
  position: absolute;
  bottom: 0;
  right: 56px;
  font-family: LAB디지털 !important;
}

.pump_name_unit {
  font-family: KHNPHDRegular;
  font-size: 17px;
  color: #c3eaff;
  margin-left: 2px;
  line-height: 57px;
  letter-spacing: 5px;
  position: absolute;
  bottom: 0;
  right: 15px;
}

.carousel_vertical .carousel__track {
  height: 150px;
}

.carousel__viewport {
  height: 100%;
}

.carousel_vertical .carousel__item {
  /* min-height: 200px; */
  width: 100%;
  height: 150px;
  background-color: var(--vc-clr-primary);
  color: var(--vc-clr-white);
  font-size: 20px;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.carousel__item img {
  width: 100%;
  height: 100%;
}

.carousel__prev,
.carousel__next {
  color: #007aff;
}

.slide-img-btn div {
  display: inline;
}

ul.slide-img-btn li:nth-child(3n) {
  margin-right: 0;
}




.green_round {
  width: 105px;
  height: 100%;
  color: #fff;
  text-shadow: 0 0 9px #5cafff;
  font-family: "KHNPHDRegular";
  background: url(@/assets/img/00_top_roundline_g.png) no-repeat;
  background-size: 100%;
  background-position: center;
  display: flex;
  font-size: 16px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.box-bg {
  background: url(@/assets/img/dash_top.png) no-repeat !important;
  background-size: 100% 100% !important;
  width: 270px;
  height: 100px;
  padding: 0px 25px;
  justify-content: unset;
}

.unit {
  font-size: 16px;
  color: #a4ceed;
  font-family: "KHNPHDRegular";
  margin-left: 5px;
}

.content__value-box {
  width: 140px;
  text-shadow: rgba(209, 250, 255, 0.5) 0px 0px 5px;
  font-size: 18px;
  text-align: right;
  color: rgb(242, 251, 255);
  font-family: LAB디지털 !important;
  background-position: center center;
}

.content__text-box {
  width: px;
  background-size: 100% 20px;
  background-position-y: bottom;
  text-shadow: 0 0 9px #5cafff;
  font-family: KHNPHUotfR;
  font-size: 16px;
  line-height: 1.5;
  text-align: left;
  color: #fff;
}

.animationTItle-two {
  width: 100%;
  display: flex;
  overflow: hidden;
  flex-direction: column-reverse;
  height: 48px;
}

.animationTItle {
  width: 100%;
  display: flex;
  overflow: hidden;
  flex-direction: column-reverse;
  height: 24px;
}


.right_box1 {
  width: 83%;
  height: 30%;
  align-self: center;
  display: flex;
}

.right_box2 {
  width: 83%;
  height: 33%;
  align-self: center;
}

.right_box3 {
  width: 83%;
  height: 30%;
  align-self: center;
}

.dash_right {
  height: 100%;
  width: 25%;
  float: left;
}

.div_right {
  width: 100%;
  height: 99%;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
}

.right_title_div {
  height: 18%;
  width: 100%;
}
</style>