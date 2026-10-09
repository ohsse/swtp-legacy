<template>
  <!-- 학야 정수장 메인 -->
  <b-col class="position-relative" style="z-index: 0;">
    <!-- class -> map-contents 구미 정수장에서 받고 있음 -->
    <div class="map-contents" :style="{ width: '100%', height: '550px' }">
      <div class="waterwall_back_hakya">

        <!-- 혼화응집지 -->
        <!-- <div @mouseover="popupShow('혼화응집지')" @mouseout="popupHide()"> -->
          <MainCubeText :style="{ top: '240px', left: '152px' }" :txtStyle="{ left: '489px', top: '128px' }"
            :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_mixsink.png')" cubeText="혼화응집지"
            ref="cubeText" @click="this.$refs.cubeText.goFac('혼화응집지')"
            @popupShow="popupShow('혼화응집지')" @popupHide="popupHide()"
            />
          <main-cube v-if="percentData.혼화응집지 >= 0" :style="{ top: '255px', left: '726px' }" :cubeVal="percentData.혼화응집지" />
        <!-- </div> -->
        <!-- //혼화응집지-->

        <!-- 착수 -->
        <MainCubeText :style="{ top: '549px', left: '92px' }" :txtStyle="{ top: '28px', left: '0px' }"
          :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_get.png')"/>
        <main-cube v-if="percentData.착수동 >= 0" :style="{ top: '454px', left: '176px' }" :cubeVal="percentData.착수동" />
        <!-- //착수 -->

        <!-- 약품투입동 -->
        <!-- <div @mouseover="popupShow('약품투입동')" @mouseout="popupHide()"> -->
          <MainCubeText :style="{ top: '570px', left: '288px' }" :txtStyle="{ top: '55px', left: '56px' }"
            :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_chemical.png')" cubeText="약품투입동"
            ref="cubeText" @click="this.$refs.cubeText.goFac('약품투입동')" 
            @popupShow="popupShow('약품투입동')" @popupHide="popupHide()"/>
          <main-cube v-if="percentData.약품투입동 >= 0" :style="{ top: '514px', left: '432px' }" :cubeVal="percentData.약품투입동" />
        <!-- </div> -->
        <!-- //약품투입동 -->

        <!-- 차염투입동 -->
        <!-- <div @mouseover="popupShow('차염투입동')" @mouseout="popupHide()"> -->
          <MainCubeText :style="{ top: '710px', left: '713px' }" :txtStyle="{ top: '35px', left: '55px' }"
            :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_disinfection.png')" cubeText="차염투입동"
            ref="cubeText" @click="this.$refs.cubeText.goFac('차염투입동')"
            @popupShow="popupShow('차염투입동')" @popupHide="popupHide()" />
          <main-cube v-if="percentData.차염투입동 >= 0" :style="{ top: '633px', left: '853px' }" :cubeVal="percentData.차염투입동" />
        <!-- </div> -->
        <!-- //차염투입동 -->

        <!-- 여과 -->
        <!-- <div @mouseover="popupShow('여과지동')" @mouseout="popupHide()"> -->
          <MainCubeText :style="{ top: '113px', left: '945px' }" :txtStyle="{ top: '61px', left: '159px' }"
            :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_filter.png')" cubeText="여과지동"
            ref="cubeText" @click="this.$refs.cubeText.goFac('여과지동')" 
            @popupShow="popupShow('여과지동')" @popupHide="popupHide()" />
          <main-cube v-if="percentData.여과지동 >= 0" :style="{ top: '63px', left: '1188px' }" :cubeVal="percentData.여과지동" />
        <!-- </div> -->
        <!-- //여과 -->

        <!-- 정수지 -->
        <!-- <div @mouseover="popupShow('정수지')" @mouseout="popupHide()"> -->
        <div>
          <MainCubeText :style="{ top: '315px', left: '1299px' }" :txtStyle="{ top: '28px', left: '0px' }"
            :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_water.png')" ref="cubeText"
            @click="this.$refs.cubeText.goFac('정수지')" />
          <main-cube v-if="percentData.정수지 >= 0" :style="{ top: '219px', left: '1385px' }" :cubeVal="percentData.정수지" />
        </div>
        <!-- //정수지 -->

        <!-- 회수동 -->
        <!-- <div @mouseover="popupShow('회수동')" @mouseout="popupHide()"> -->
          <MainCubeText :style="{ top: '251px', left: '1453px' }" :txtStyle="{ top: '16px', left: '0px' }"
            :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_water.png')" cubeText="회수동" ref="cubeText"
            @click="this.$refs.cubeText.goFac('회수동')" 
            @popupShow="popupShow('회수동')" @popupHide="popupHide()" />
          <main-cube v-if="percentData.회수동 >= 0" :style="{ top: '156px', left: '1539px' }" :cubeVal="percentData.회수동" />
        <!-- </div> -->
        <!-- //회수동 -->

        <!-- none1 -->
        <!-- <div @mouseover="popupShow('none1')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '22px', left: '1227px' }" :txtStyle="{ top: '48px', left: '116px' }"
            :backImg="require('@/assets/img/local_nakdong/hakya/building/ya_building_deep.png')" cubeText="none1" ref="cubeText"
            @click="this.$refs.cubeText.goFac('회수동')" />
          <main-cube v-if="percentData.none1 >= 0" :style="{ top: '-36px', left: '1426px' }" :cubeVal="percentData.none1" />
        </div> -->
        <!-- //none1 -->

        <!-- none2 -->
        <!-- <div @mouseover="popupShow('non2')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '32px', left: '1577px' }" :txtStyle="{ top: '218px', left: '106px' }"
            :backImg="require('@/assets/img/local_nakdong/hakya/building/ya_bg_deep.png')" cubeText="none2" ref="cubeText"
            @click="this.$refs.cubeText.goFac('회수동')" />
          <main-cube v-if="percentData.none2 >= 0" :style="{ top: '144px', left: '1767px' }" :cubeVal="percentData.none2" />
        </div> -->
        <!-- //none2 -->

        <div class="waterflow1 flow1 no1"></div>
        <div class="waterflow2 flow1 no2"></div>
        <div class="waterflow3 flow1 no3"></div>

        <div class="waterflow1 flow2 no1"></div>
        <div class="waterflow2 flow2 no2"></div>
        <div class="waterflow3 flow2 no3"></div>

        <div class="waterflow1 flow3 no1"></div>
        <div class="waterflow2 flow3 no2"></div>
        <div class="waterflow3 flow3 no3"></div>

        <!-- <div class="waterwall_back_hakya"></div> -->
      </div>
      <div class="hakya_bg"></div>
    </div>
    <HoverPopup ref="popup" :hoverVal="hoverVal" />
  </b-col>
  <!-- 학야 정수장 메인 -->
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

/* .hakya_bg{
  position: absolute;
  top: -411px;
  left: -52px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  transform-origin: 50% 50%;
  transform: scale(1);
} */
.hakya_bg{
  position: absolute;
  top: -90px;
  left: -60px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  z-index: -1;
}

/* .waterwall_back_hakya{
  position: absolute;
  top: 104px;
  left: -51px;
  width: 2706px;
  height: 817px;
  background: url(@/assets/img/local_nakdong/hakya/waterwall_hakya.png) no-repeat;
} */
.waterwall_back_hakya{
  position: absolute;
  top: -20px;
  left: -110px;
  width: 2706px;
  height: 817px;
  background: url(@/assets/img/local_nakdong/hakya/waterwall_hakya.png) no-repeat;
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
  height: 60%;
  position: absolute;
  float: left;
  top: 55%;
  left: 67%;
  display: none;
}

.waterflow1 {
  background-image: url(@/assets/img/water.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(2, 1.5);
}

.waterflow2 {
  background-image: url(@/assets/img/water2.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(2, 1.5);
}

.waterflow3 {
  background-image: url(@/assets/img/water3.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(2, 1.5);
}

.waterflow1.flow1,
.waterflow2.flow1,
.waterflow3.flow1 {
  top: 808px;
  left: 5px;
  offset-path: path("M0.0 0 L 196 -94 L 65 -134 L 128 -164");
  animation: waterflow 4.6S linear 0s infinite normal backwards;
}

.waterflow1.flow2,
.waterflow2.flow2,
.waterflow3.flow2 {
  top: 602px;
  left: 235px;
  offset-path: path("M0.0 0 L 188 -78");
  animation: waterflow 2.2S linear 0s infinite normal backwards;
}

.waterflow1.flow3,
.waterflow2.flow3,
.waterflow3.flow3 {
  top: 303px;
  left: 920px;
  offset-path: path("M0.0 0 L 107 -44");
  animation: waterflow 1.3S linear 0s infinite normal backwards;
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

.waterflow1.flow1.no1 {
  animation-delay: 0s;
}

.waterflow2.flow1.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow1.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow2.no1 {
  animation-delay: 0s;
}

.waterflow2.flow2.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow2.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow3.no1 {
  animation-delay: 0s;
}

.waterflow2.flow3.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow3.no3 {
  animation-delay: 0.4s;
}
</style>