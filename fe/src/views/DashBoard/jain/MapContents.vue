<template>
  <!-- 자인 정수장 메인 -->
  <b-col class="position-relative" style="z-index: 0;">
    <!-- class -> map-contents 구미 정수장에서 받고 있음 -->
    <div class="map-contents" :style="{ width: '100%', height: '550px' }">
      <div class="waterwall_back_jain">

        <!-- 혼화 & 응집 -->
        <MainCubeText :style="{ top: '357px', left: '738px' }" :txtStyle="{ left: '342px', top: '62px' }"
          :backImg="require('@/assets/img/local_nakdong/jain/building/ja_mixsink.png')" 
          :txtSubStyle="{ top: '144px', left: '134px' }"/>
        <main-cube v-if="percentData.혼화/응집동 >= 0" :style="{ top: '305px', left: '1169px' }" :cubeVal="percentData['혼화/응집동']" />
        <main-cube v-if="percentData.침전동 >= 0" :style="{ top: '392px', left: '950px' }" :cubeVal="percentData.침전동" />
        <!-- //혼화 & 응집 -->

        <!--착수 -->
        <MainCubeText :style="{ top: '148px', left: '1240px' }" :txtStyle="{ top: '24px', left: '19px' }"
          :backImg="require('@/assets/img/local_nakdong/jain/building/ja_get.png')"/>
        <main-cube v-if="percentData.착수동 >= 0" :style="{ top: '59px', left: '1345px' }" :cubeVal="percentData.착수동" />
        <!-- //착수 -->

        <!-- 약품투입동 -->
        <!-- <div @mouseover="popupShow('약품투입동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '272px', left: '1293px' }" :txtStyle="{ top: '20px', left: '13px' }"
          :backImg="require('@/assets/img/local_nakdong/jain/building/ja_chemical.png')" cubeText="약품투입동" ref="cubeText"
          @click="this.$refs.cubeText.goFac('약품투입동')" @popupShow="popupShow('약품투입동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.약품투입동 >= 0" :style="{ top: '182px', left: '1396px' }" :cubeVal="percentData.약품투입동" />
        <!-- </div> -->
        <!-- //약품투입동 -->

        <!-- 수변전동 -->
        <MainCubeText :style="{ top: '204px', left: '1446px' }" :txtStyle="{ top: '20px', left: '13px' }"
          :backImg="require('@/assets/img/local_nakdong/jain/building/ja_chemical.png')" cubeText="수변전동" ref="cubeText"
          @click="this.$refs.cubeText.goFac('수변전동')" @popupShow="popupShow('수변전동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.수변전동 >= 0" :style="{ top: '112px', left: '1548px' }" :cubeVal="percentData.수변전동" />
        <!-- //수변전동 -->

        <!-- 여과지동 -->
        <MainCubeText :style="{ top: '587px', left: '494px' }" :txtStyle="{ top: '41px', left: '116px' }"
          :backImg="require('@/assets/img/local_nakdong/jain/building/ja_filter.png')" cubeText="여과지동"
          @click="this.$refs.cubeText.goFac('여과지동')" @popupShow="popupShow('여과지동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.여과지동 >= 0" :style="{ top: '516px', left: '700px' }" :cubeVal="percentData.여과지동" />
        <!-- //여과지동 -->

        <!-- 차염투입동 -->
        <MainCubeText :style="{ top: '542px', left: '307px' }" :txtStyle="{ top: '16px', left: '8px' }"
          :backImg="require('@/assets/img/local_nakdong/jain/building/ja_disinfection.png')" cubeText="차염투입동"
          @click="this.$refs.cubeText.goFac('차염투입동')" @popupShow="popupShow('차염투입동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.차염투입동 >= 0" :style="{ top: '447px', left: '402px' }" :cubeVal="percentData.차염투입동" />
        <!-- //차염투입동 -->

        <!-- 회수조동 -->
        <MainCubeText :style="{ top: '416px', left: '310px' }" :txtStyle="{ top: '13px', left: '11px' }"
          :backImg="require('@/assets/img/local_nakdong/jain/building/in_building1_deep.png')" cubeText="회수조동"
          @click="this.$refs.cubeText.goFac('회수조동')" @popupShow="popupShow('회수조동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.회수조동 >= 0" :style="{ top: '321px', left: '407px' }" :cubeVal="percentData.회수조동" />
        <!-- //회수조동 -->

        <!-- 탈수기동 -->
        <MainCubeText :style="{ top: '175px', left: '804px' }" :txtStyle="{ top: '23px', left: '42px' }" cubeText="탈수기동"
          :backImg="require('@/assets/img/local_nakdong/jain/building/in_building2_deep.png')"
          @click="this.$refs.cubeText.goFac('탈수기동')" @popupShow="popupShow('탈수기동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.탈수기동 >= 0" :style="{ top: '88px', left: '931px' }" :cubeVal="percentData.탈수기동" />
        <!-- //탈수기동 -->

        <!-- 조정조동 -->
        <MainCubeText :style="{ top: '326px', left: '535px' }" :txtStyle="{ top: '20px', left: '13px' }" cubeText="조정조동"
          :backImg="require('@/assets/img/local_nakdong/jain/building/jojeongjo.png')"
          @click="this.$refs.cubeText.goFac('조정조동')" @popupShow="popupShow('조정조동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.조정조동 >= 0" :style="{ top: '233px', left: '634px' }" :cubeVal="percentData.조정조동" />
        <!-- //조정조동 -->


        <div class="waterflow1 flow1 no1"></div>
        <div class="waterflow2 flow1 no2"></div>
        <div class="waterflow3 flow1 no3"></div>

        <div class="waterflow1 flow2 no1"></div>
        <div class="waterflow2 flow2 no2"></div>
        <div class="waterflow3 flow2 no3"></div>

        <div class="waterflow1 flow3 no1"></div>
        <div class="waterflow2 flow3 no2"></div>
        <div class="waterflow3 flow3 no3"></div>

        <div class="waterflow1 flow4 no1"></div>
        <div class="waterflow2 flow4 no2"></div>
        <div class="waterflow3 flow4 no3"></div>
        <div class="waterflow1 flow4 no4"></div>
        <div class="waterflow2 flow4 no5"></div>
        <div class="waterflow3 flow4 no6"></div>

        <!-- <div class="waterwall_back_jain"></div> -->
      </div>
      <div class="jain_bg"></div>
    </div>
    <HoverPopup ref="popup" :hoverVal="hoverVal" />
  </b-col>
  <!-- 자인 정수장 메인 -->
</template>
<script>
import { fetchFunc } from '@/util/fetchFunc'
import HoverPopup from '@/views/DashBoard/DashBoard/HoverPopup.vue'
import MainCube from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCube.vue'
import MainCubeText from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCubeText.vue'
import 'vue3-carousel/dist/carousel.css'
export default {
  components: {
    HoverPopup,
    MainCube,
    MainCubeText
  },
  data() {
    return {
      hoverVal: {
        title: "활성탄흡착지동",
        mainValue: 400
      },
      percentData: {},
    }
  },
  mounted() {
    this.percentList();
  },
  methods: {
    async percentList() {
      const apiURL = this.$apiURL;
      let res = await fetch(
        `${apiURL}/cm/selectWppPwrPercentList`
      );
      let data = await res.json();
      for (let i = 0; i < data.data.length; i++) {
        const key = Object.keys(data.data[i])[0]; // 현재 데이터의 첫 번째 키를 가져옴
        const value = data.data[i][key];

        this.percentData[key] = (value > "0.00" && value <= "1") ? value : (value === "0.00" ? 0 : Math.floor(value));
      }
    },
    async popupShow(target) {
      const apiURL = this.$apiURL;
      const nowDate = new Date()
      const nowYear = nowDate.getFullYear()
      const nowMonth = nowDate.getMonth() + 1 < 10 ? `0${nowDate.getMonth() + 1}` : nowDate.getMonth() + 1
      const nowDay = nowDate.getDate() < 10 ? `0${nowDate.getDate()}` : nowDate.getDate()
      const todayDate = `${nowYear}-${nowMonth}-${nowDay}`
      let top3Data = (await fetchFunc(`${apiURL}/ai/getTop3?date=${todayDate}&zone_code=${target}`)).data
      let top3Array = []
      top3Data.forEach((item) => {
        if ('dcs' in item && 'value' in item) {
          let top3Obj = {
            title: item.dcs,
            value: item.value,
          }
          top3Array.push(top3Obj)
        }
      });
      this.hoverVal.title = target;
      if (top3Data?.length > 0) {
        this.hoverVal.mainValue = top3Data[0]?.value
        this.hoverVal.total = top3Data[top3Data.length - 1]?.total
      }
      this.$refs.popup.setData(top3Array)
      this.$refs.popup.show();
    },
    popupHide() {
      this.$refs.popup.hide();
    }

  }
}
</script>
<style scoped>

/* .jain_bg{
  position: absolute;
  top: -401px;
  left: -95px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  transform-origin: 50% 50%;
  transform: scale(0.95, 0.95);
} */
.jain_bg{
  position: absolute;
  top: -90px;
  left: -74px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  z-index: -1;
}

/* .waterwall_back_jain {
  position: absolute;
  top: 30px;
  left: 0px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/local_nakdong/jain/waterwall_jain.png) no-repeat;
} */
.waterwall_back_jain {
  position: absolute;
  top: -90px;
  left: -74px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/local_nakdong/jain/waterwall_jain.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  transform-origin: 50% 50%;
  transform: scale(1);
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

.hoverInfo {
  /* width: 40%;
  height: 32%; */
  width: 35%;
  height: 62%;
  position: absolute;
  float: left;
  top: 51%;
  left: 67%;
  display: none;
}

.waterflow1 {
  background-image: url(@/assets/img/water.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.3);
}

.waterflow2 {
  background-image: url(@/assets/img/water2.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.3);
}

.waterflow3 {
  background-image: url(@/assets/img/water3.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.3);
}

@keyframes waterflow {
  0% {
    offset-distance: 0;
    display: none;
    opacity: 0;
  }

  1% {
    opacity: 1;
  }

  100% {
    offset-distance: 100%;
  }
}

.waterflow1.flow1,
.waterflow2.flow1,
.waterflow3.flow1 {
  top: 176px;
  left: 1362px;
  offset-path: path("M0.0 0 L 67 -29 L 318 44 L 92 152");
  animation: waterflow 7.8S linear 0s infinite normal backwards;
}
.waterflow1.flow2,
.waterflow2.flow2,
.waterflow3.flow2 {
  top: 371px;
  left: 1357px;
  offset-path: path("M0.0 0 L -110 50");
  animation: waterflow 1.6S linear 0s infinite normal backwards;
}
.waterflow1.flow3,
.waterflow2.flow3,
.waterflow3.flow3 {
  top: 596px;
  left: 870px;
  offset-path: path("M0.0 0 L -124 56");
  animation: waterflow 1.8S linear 0s infinite normal backwards;
}
.waterflow1.flow4,
.waterflow2.flow4,
.waterflow3.flow4 {
  top: 718px;
  left: 676px;
  offset-path: path("M0.0 0 L -225 106 L 206 229");
  animation: waterflow 8.2S linear 0s infinite normal backwards;
}

.waterflow1.flow1.no1{
  animation-delay: 0s;
}
.waterflow2.flow1.no2{
  animation-delay: 0.2s;
}
.waterflow3.flow1.no3{
  animation-delay: 0.4s;
}

.waterflow1.flow2.no1{
  animation-delay: 0s;
}
.waterflow2.flow2.no2{
  animation-delay: 0.2s;
}
.waterflow3.flow2.no3{
  animation-delay: 0.4s;
}

.waterflow1.flow3.no1{
  animation-delay: 0s;
}
.waterflow2.flow3.no2{
  animation-delay: 0.2s;
}
.waterflow3.flow3.no3{
  animation-delay: 0.4s;
}

.waterflow1.flow4.no1{
  animation-delay: 0s;
}
.waterflow2.flow4.no2{
  animation-delay: 0.2s;
}
.waterflow3.flow4.no3{
  animation-delay: 0.4s;
}
.waterflow1.flow4.no4{
  animation-delay: 4.1s;
}
.waterflow2.flow4.no5{
  animation-delay: 4.3s;
}
.waterflow3.flow4.no6{
  animation-delay: 4.5s;
}
</style>