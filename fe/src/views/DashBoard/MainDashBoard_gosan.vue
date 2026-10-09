<template>
  <div>
    <div class="position-relative mx-5" style="display: block">
      <!-- 전력소비 & 전력절감-->
      <b-row>
        <b-col class="position-relative">
          <div class="position-absolute bottom-0 px-3" :style="{ width: '416px', top: '495px', left: '-50px' }">
            <RotationContentsVue />
          </div>
        </b-col>
      </b-row>
      <!-- //전력소비 & 전력절감-->
      <div class="dash_right"></div>
      <div class="dash_border_img"></div>
      <div class="right_box1"></div>
      <div class="right_box2"></div>
      <div class="right_box3"></div>

      <!-- 3D MAP 영역 -->
      <b-row class="align-items-center" :style="{ width: '75%', height: 'calc(100vh - 118px)' }">
        <MapContents />
      </b-row>
      <!-- //3D MAP 영역 -->
      <!-- 오른쪽 영역 -->
      <RightContents ref="RightContents"></RightContents>
      <!-- //오른쪽 영역 -->
    </div>
  </div>
</template>

<script>

// import PumpButton from './Button/PumpButton.vue'
import MapContents from "@/views/DashBoard/gosan/MapContents.vue"
import RotationContentsVue from '@/views/DashBoard/gosan/RotationContents.vue'
import RightContents from './DashBoard/RightContents/RightContents.vue'
import { fetchFunc } from '@/util/fetchFunc';
export default {
  name: 'App',
  components: {
    // PumpButton,
    MapContents,
    RotationContentsVue,
    RightContents
  },
  data() {
    return {
    }
  },
  mounted() {
    this.initData();
    this.$emit("onChangeBgClass", false);
  },
  methods: {
    twoDigits(num) {
      return num.toString().padStart(2, '0');
    },
    async initData() {
      let now = new Date();
      var year2 = now.getFullYear();
      var month2 = this.twoDigits(now.getMonth() + 1);
      var date = this.twoDigits(now.getDate());
      let todayTime = year2 + "-" + month2 + "-" + date;
      const apiURL = this.$apiURL;
      const data = await fetchFunc(`${apiURL}/ai/selectPwrPrdctList?date=${todayTime}`);
      // const data1 = await fetchFunc(`${apiURL}/ai/peakSelect?date=${todayTime}`);
      const data1 = (await fetchFunc(`${apiURL}/ai/selectPumpStatus`)).data;
      // const data1 = { "code": 200, "message": "정상적으로 조회되었습니다.", "data": { "PRI": [{ "ts": "2024-01-30 18:47:00", "PUMP_IDX": 8, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_1", "value": "0.9613" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 9, "PUMP_GRP": 2, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_2", "value": "0.6075" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 10, "PUMP_GRP": 2, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_3", "value": "6.4675" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 11, "PUMP_GRP": 2, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_4", "value": "0.4988" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_1", "value": "0.3831" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 2, "PUMP_GRP": 1, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_2", "value": "6.0644" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 3, "PUMP_GRP": 1, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_3", "value": "0.3775" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_4", "value": "5.9663" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 5, "PUMP_GRP": 1, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_5", "value": "1.9563" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 6, "PUMP_GRP": 1, "PUMP_GRP_IDX": 6, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_6", "value": "5.9413" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 7, "PUMP_GRP": 1, "PUMP_GRP_IDX": 7, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_7", "value": "6.1350" }], "pwiStatus": [{ "ts": "2024-01-30 18:47:00", "PUMP_IDX": 8, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_1", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 9, "PUMP_GRP": 2, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_2", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 10, "PUMP_GRP": 2, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_3", "kW": 686.49 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_1", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 2, "PUMP_GRP": 1, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_2", "kW": 648.21 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 3, "PUMP_GRP": 1, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_3", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_4", "kW": 9.5 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 5, "PUMP_GRP": 1, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_5", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 6, "PUMP_GRP": 1, "PUMP_GRP_IDX": 6, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_6", "kW": 10.83 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 7, "PUMP_GRP": 1, "PUMP_GRP_IDX": 7, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_7", "kW": 886.69 }], "FRI": [{ "ts": "2024-01-30 18:47:00", "PUMP_IDX": 8, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_1", "value": "3343.5000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 9, "PUMP_GRP": 2, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_2", "value": "3343.5000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 10, "PUMP_GRP": 2, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_3", "value": "3343.5000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 11, "PUMP_GRP": 2, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_4", "value": "3343.5000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_1", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 2, "PUMP_GRP": 1, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_2", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 3, "PUMP_GRP": 1, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_3", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_4", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 5, "PUMP_GRP": 1, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_5", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 6, "PUMP_GRP": 1, "PUMP_GRP_IDX": 6, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_6", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 7, "PUMP_GRP": 1, "PUMP_GRP_IDX": 7, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_7", "value": "17928.0000" }], "SPI": [], "pumpStatus": [{ "PUMP_GRP": 2, "PUMP_NM": "(신)정수지_1", "PUMP_GRP_IDX": 1, "runCount": 5, "value": "Off", "PUMP_IDX": 8, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(신)정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "(신)정수지_2", "PUMP_GRP_IDX": 2, "runCount": 5, "value": "Off", "PUMP_IDX": 9, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(신)정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "(신)정수지_3", "PUMP_GRP_IDX": 3, "runCount": 5, "value": "On", "PUMP_IDX": 10, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(신)정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "(신)정수지_4", "PUMP_GRP_IDX": 4, "runCount": 5, "value": "Off", "PUMP_IDX": 11, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(신)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_1", "PUMP_GRP_IDX": 1, "runCount": 5, "value": "Off", "PUMP_IDX": 1, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_2", "PUMP_GRP_IDX": 2, "runCount": 5, "value": "On", "PUMP_IDX": 2, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_3", "PUMP_GRP_IDX": 3, "runCount": 5, "value": "Off", "PUMP_IDX": 3, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_4", "PUMP_GRP_IDX": 4, "runCount": 5, "value": "On", "PUMP_IDX": 4, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_5", "PUMP_GRP_IDX": 5, "runCount": 5, "value": "Off", "PUMP_IDX": 5, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_6", "PUMP_GRP_IDX": 6, "runCount": 5, "value": "On", "PUMP_IDX": 6, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_7", "PUMP_GRP_IDX": 7, "runCount": 5, "value": "On", "PUMP_IDX": 7, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }] } }.data

      // const data2 = (await fetchFunc(`${apiURL}/ai/selectValve`)).data;
      const goal = await fetchFunc(`${apiURL}/st/selectPeakGoal`);

      this.$refs.RightContents.initData(data, data1, goal);
    }
  }
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

.dash_border_img {
  background: url(@/assets/img/00_table_bg_long.png) no-repeat;
  background-position: center;
  background-size: 100% 110%;
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