<template>
  <div>
    <div class="position-relative mx-5" style="display: block">
      <!-- 전력소비 & 전력절감-->
      <b-row>
        <b-col class="position-relative">
          <div class="position-absolute bottom-0 start-0 px-3" :style="{ width: '416px', top: '-20px' }">
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
      <b-row class="align-items-center" :style="{ width: '100%', height: 'calc(100vh - 390px)' }">
        <!-- 자인 정수장 메인 -->
        <MapContents />
        <!-- //자인 정수장 메인 -->
      </b-row>
      <!-- //3D MAP 영역 -->
      <!-- 오른쪽 영역 -->
      <b-row class="row-cols-2 gx-3">
        <div class="col-6">
          <!-- <PumpBottomLeft ref="PumpBottomLeft"></PumpBottomLeft> -->
          <!-- <MajorBottomMid ref="MajorBottomMid"></MajorBottomMid> -->
        </div>
        <div class="col-6">
          <PeakBottomRig ref="PeakBottomRig"></PeakBottomRig>
        </div>
      </b-row>
      <!-- //오른쪽 영역 -->
    </div>
  </div>
</template>

<script>
import 'vue3-carousel/dist/carousel.css'
import MapContents from "@/views/DashBoard/jain/MapContents.vue"
import RotationContentsVue from '@/views/DashBoard/jain/RotationContents.vue'
import PeakBottomRig from "@/views/DashBoard/DashBoard/PeakBottomRig.vue";
import { fetchFunc } from '@/util/fetchFunc';
export default {
  name: 'App',
  components: {
    // PumpButton,
    MapContents,
    RotationContentsVue,
    PeakBottomRig
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
      // const data = await fetchFunc(`${apiURL}/ai/peakSelect?date=${todayTime}`);
      // const data1 = (await fetchFunc(`${apiURL}/ai/selectPumpStatus`)).data;
      // const data2 = (await fetchFunc(`${apiURL}/ai/selectValve`)).data;
      const goal = await fetchFunc(`${apiURL}/st/selectPeakGoal`);

      this.$refs.PeakBottomRig.initData(data, goal);
    }
  }
}
</script>

<style>
/* .waterwall_back_jain {
  position: absolute;
  top: -86px;
  left: -18px;
  width: 1342px;
  height: 893px;
  background: url(@/assets/img/local_nakdong/jain/waterwall_jain.png) no-repeat;
  background-size: 100% 100%;
  background-position: 30% 83%;
} */

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

.table-bg-long {
  background: url(@/assets/img/00_table_bg_long.png) no-repeat;
  background-size: 103% 103%;
  background-position: center;
}

.blue_round {
  width: 105px;
  height: 100px;
  color: #fff;
  text-shadow: 0 0 9px #5cafff;
  font-family: "KHNPHDRegular";
  background: url(@/assets/img/00_top_roundline_b.png) no-repeat;
  background-size: 100%;
  background-position: center;
  display: flex;
  font-size: 16px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
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