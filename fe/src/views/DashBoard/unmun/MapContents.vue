<template>
  <!-- 운문 정수장 메인 -->
  <b-col class="position-relative" style="z-index: 0;">
    <!-- class -> map-contents 구미 정수장에서 받고 있음 -->
    <div class="map-contents" :style="{ width: '100%', height: '800px' }">
      <div class="waterwall_back_unmun">

        <!-- 혼화 & 응집 -->
        <MainCubeText :style="{ top: '241px', left: '504px' }" :txtStyle="{ left: '436px', top: '30px' }"
        :backImg="require('@/assets/img/local_nakdong/unmun/building/un_mixsink.png')"/>
        <main-cube v-if="percentData['혼화/응집동'] >= 0" :style="{ top: '161px', left: '1035px' }" :cubeVal="percentData['혼화/응집동']" />
        <main-cube v-if="percentData['침전동'] >= 0" :style="{ top: '263px', left: '776px' }" :cubeVal="percentData.침전동" />
        <!-- //혼화 & 응집 -->

        <!-- 착수 -->
        <!-- <MainCubeText :style="{ top: '9px', left: '1050px' }" :txtStyle="{ left: '18px', top: '20px' }" /> -->
        <!-- <main-cube v-if="percentData['착수동'] >= 0" :style="{ top: '-77px', left: '1155px' }" :cubeVal="percentData['착수동']" /> -->
        <!-- //착수 -->

        <!-- 약품투입동 -->
        <!-- <div @mouseover="popupShow('약품투입동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '194px', left: '1239px' }" :txtStyle="{ left: '21px', top: '20px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/un_get_chemical.png')" cubeText="약품투입동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('약품투입동')" @popupShow="popupShow('약품투입동')"
          @popupHide="popupHide()">
        </MainCubeText>
        <main-cube v-if="percentData['약품투입동'] >= 0" :style="{ top: '106px', left: '1345px' }" :cubeVal="percentData.약품투입동" />
        <!-- </div> -->
        <!-- //약품투입동 -->

        <!-- 소석회동 -->
          <MainCubeText :style="{ top: '159px', left: '1098px' }" :txtStyle="{ left: '21px', top: '20px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/un_get_chemical.png')">
        </MainCubeText>
        <main-cube v-if="percentData['소석회동'] >= 0" :style="{ top: '70px', left: '1204px' }" :cubeVal="percentData.소석회동" />
        <!-- </div> -->
        <!-- //소석회동 -->

        <!-- 송수펌프동 -->
        <!-- <div @mouseover="popupShow('송수펌프동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '635px', left: '607px' }" :txtStyle="{ left: '86px', top: '55px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/un_waterlarge.png')" cubeText="송수펌프동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('송수펌프동')" @popupShow="popupShow('송수펌프동')"
          @popupHide="popupHide()">
        </MainCubeText>
        <main-cube v-if="percentData['송수펌프동'] >= 0" :style="{ top: '577px', left: '782px' }" :cubeVal="percentData.송수펌프동" />
        <!-- </div> -->
        <!-- //송수펌프동 -->

        <!-- 회수펌프동 -->
        <!-- <div @mouseover="popupShow('회수펌프동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '599px', left: '884px' }" :txtStyle="{ left: '14px', top: '27px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/un_watersmall.png')" cubeText="회수펌프동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('회수펌프동')" @popupShow="popupShow('회수펌프동')"
          @popupHide="popupHide()">
        </MainCubeText>
        <main-cube v-if="percentData['회수펌프동'] >= 0" :style="{ top: '515px', left: '983px' }" :cubeVal="percentData.회수펌프동" />
        <!-- </div> -->
        <!-- 회수펌프동 -->

        <!-- 여과지동 -->
        <!-- <div @mouseover="popupShow('여과지동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '486px', left: '265px' }" :txtStyle="{ left: '73px', top: '43px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/un_filter.png')" cubeText="여과지동" ref="cubeText"
          @click="this.$refs.cubeText.goFac('여과지동')" @popupShow="popupShow('여과지동')" @popupHide="popupHide()">
        </MainCubeText>
        <main-cube v-if="percentData['여과지동'] >= 0" :style="{ top: '417px', left: '425px' }" :cubeVal="percentData.여과지동" />
        <!-- </div> -->
        <!-- //여과지동 -->

        <!-- 차염투입동 -->
        <!-- <div @mouseover="popupShow('차염투입동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '617px', left: '159px' }" :txtStyle="{ left: '22px', top: '22px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/un_disinfection.png')" cubeText="차염투입동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('차염투입동')" @popupShow="popupShow('차염투입동')"
          @popupHide="popupHide()">
        </MainCubeText>
        <main-cube v-if="percentData['차염투입동'] >= 0" :style="{ top: '528px', left: '268px' }" :cubeVal="percentData.차염투입동" />
        <!-- </div> -->
        <!-- //차염투입동 -->

        <!-- 탈수기동 -->
        <!-- <div @mouseover="popupShow('탈수기동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '384px', left: '1234px' }" :txtStyle="{ left: '84px', top: '56px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/un_waterlarge.png')" cubeText="탈수기동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('탈수기동')" @popupShow="popupShow('탈수기동')"
          @popupHide="popupHide()">
        </MainCubeText>
        <main-cube v-if="percentData['탈수기동'] >= 0" :style="{ top: '327px', left: '1406px' }" :cubeVal="percentData.탈수기동" />
        <!-- </div> -->
        <!-- //탈수기동 -->

        <!-- none2 -->
        <!-- <MainCubeText :style="{ top: '351px', left: '924px' }" :txtStyle="{ left: '26px', top: '12px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/mun_m_deep.png')"  >
        </MainCubeText>
        <main-cube v-if="percentData['none2'] >= 0" :style="{ top: '258px', left: '1032px' }" :cubeVal="percentData['none2']" /> -->
        <!-- //none2 -->

        <!-- none3 -->
        <!-- <MainCubeText :style="{ top: '424px', left: '816px' }" :txtStyle="{ left: '42px', top: '22px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/mun_circle_deep.png')" >
        </MainCubeText>
        <main-cube v-if="percentData['none3'] >= 0" :style="{ top: '340px', left: '941px' }" :cubeVal="percentData['none3']" /> -->
        <!-- //none3 -->

        <!-- 관리동 -->
        <!-- <div @mouseover="popupShow('관리동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '113px', left: '642px' }" :txtStyle="{ left: '73px', top: '38px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/management.png')" cubeText="관리동" ref="cubeText"
          @click="this.$refs.cubeText.goFac('관리동')" @popupShow="popupShow('관리동')" @popupHide="popupHide()">
        </MainCubeText>
        <main-cube v-if="percentData['관리동'] >= 0" :style="{ top: '38px', left: '801px' }" :cubeVal="percentData.관리동" />
        <!-- </div> -->
        <!-- //관리동 -->

        <!-- 수변전동 -->
        <!-- <div @mouseover="popupShow('수변전동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '61px', left: '754px' }" :txtStyle="{ left: '-6px', top: '30px' }"
          :backImg="require('@/assets/img/local_nakdong/unmun/building/substation.png')" ref="cubeText"
          @click="this.$refs.cubeText.goFac('수변전동')" @popupShow="popupShow('수변전동')" @popupHide="popupHide()">
        </MainCubeText>
        <main-cube v-if="percentData['수변전동'] >= 0" :style="{ top: '-38px', left: '836px' }" :cubeVal="percentData.수변전동" />
        <!-- </div> -->
        <!-- //수변전동 -->

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

        <!-- <div class="waterwall_back_unmun"></div> -->
      </div>
      <div class="unmun_bg"></div>
    </div>
    <HoverPopup ref="popup" :hoverVal="hoverVal" />
  </b-col>
  <!-- 운문 정수장 메인 -->
</template>
<script>
import { fetchFunc } from '@/util/fetchFunc'
import HoverPopup from '@/views/DashBoard/DashBoard/HoverPopup.vue'
import MainCube from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCube.vue'
import MainCubeText from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCubeText.vue'
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

/* .unmun_bg{
  position: absolute;
  top: -493px;
  left: -100px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  transform-origin: 50% 50%;
  transform: scale(0.95, 0.95);
} */
.unmun_bg{
  position: absolute;
  top: -150px;
  left: -94px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  background-size: 100% 100%;
  z-index: -1;
}

/* .waterwall_back_unmun {
  position: absolute;
  top: 38px;
  left: -115px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/local_nakdong/unmun/waterwall_unmun.png) no-repeat;
} */
.waterwall_back_unmun {
  position: absolute;
  top: -25px;
  left: -213px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/local_nakdong/unmun/waterwall_unmun.png) no-repeat;
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
  height: 44%;
  position: absolute;
  float: left;
  top: 67%;
  left: 68%;
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
  top: 278px;
  left: 1300px;
  offset-path: path("M0.0 0 L -152 62");
  animation: waterflow 2.2S linear 0s infinite normal backwards;
}
.waterflow1.flow2,
.waterflow2.flow2,
.waterflow3.flow2 {
  top: 535px;
  left: 667px;
  offset-path: path("M0.0 0 L -100 40");
  animation: waterflow 1.5S linear 0s infinite normal backwards;
}
.waterflow1.flow3,
.waterflow2.flow3,
.waterflow3.flow3 {
  top: 689px;
  left: 318px;
  offset-path: path("M0.0 0 L 238 64");
  animation: waterflow 3.2S linear 0s infinite normal backwards;
}
.waterflow1.flow4,
.waterflow2.flow4,
.waterflow3.flow4 {
  top: 803px;
  left: 668px;
  offset-path: path("M0.0 0 L -498 199");
  animation: waterflow 6.6S linear 0s infinite normal backwards;
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
</style>