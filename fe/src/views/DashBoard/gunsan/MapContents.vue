<template>
  <!-- 군산 정수장 메인 -->
  <b-col class="position-relative" style="z-index: 0">
    <div class="map-contents" :style="{ width: '100%', height: '800px' }">
      <div class="waterwall_back_gunsan">
        <!-- 혼화 & 응집 -->
        <MainCubeText :style="{ top: '250px', left: '625px' }" :txtStyle="{ left: '500px', top: '96px' }" :txtSubStyle="{left: '154px', top: '156px'}"
        :backImg="require('@/assets/img/local_geumgang/gunsan/building/gun_mix_sink.png')" />>
        <main-cube v-if="percentData['혼화/응집동'] >= 0" :style="{ top: '294px', left: '867px' }" :cubeVal="percentData['혼화/응집동']" />
        <main-cube v-if="percentData.침전동 >= 0" :style="{ top: '235px', left: '1212px' }" :cubeVal="percentData.침전동" />

        <!-- //혼화 & 응집 -->

        <!-- 착수 -->
        <MainCubeText :style="{ top: '134px', left: '1093px' }" :txtStyle="{ left: '-20px', top: '10px' }" 
        :backImg="require('@/assets/img/local_geumgang/gunsan/building/get_disinfection_side_gun.png')"/>
        <main-cube v-if="percentData.착수동 >= 0" :style="{ top: '30px', left: '1161px' }" :cubeVal="percentData.착수동" />
        <!-- //착수 -->

        <!-- 약품 -->
        <!-- <div @mouseover="popupShow('약품동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '162px', left: '1307px' }" :txtStyle="{ left: '5px', top: '15px' }"
          :backImg="require('@/assets/img/local_geumgang/gunsan/building/gun_chemical.png')" cubeText="약품투입동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('약품동')" @popupShow="popupShow('약품동')"
          @popupHide="popupHide()" />
        <main-cube v-if="percentData.약품동 >= 0" :style="{ top: '62px', left: '1398px' }" :cubeVal="percentData.약품동" />
        <!-- </div> -->
        <!-- //약품 -->

        <!-- 소독 -->
        <MainCubeText :style="{ top: '282px', left: '634px' }" :txtStyle="{ left: '-20px', top: '10px' }"
        :backImg="require('@/assets/img/local_geumgang/gunsan/building/get_disinfection_side_gun.png')"/>
        <main-cube v-if="percentData.소독동 >= 0" :style="{ top: '178px', left: '702px' }" :cubeVal="percentData.소독동" />
        <!-- //소독 -->

        <!-- 송수 -->
        <!-- <div @mouseover="popupShow('송수동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '541px', left: '417px' }" :txtStyle="{ top: '40px', left: '128px' }"
          :backImg="require('@/assets/img/local_geumgang/gunsan/building/gun_water.png')" cubeText="송수펌프동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('송수동')" @popupShow="popupShow('송수동')"
          @popupHide="popupHide()" />
        <main-cube v-if="percentData.송수동 >= 0" :style="{ top: '469px', left: '633px' }" :cubeVal="percentData.송수동" />
        <!-- </div> -->
        <!-- //송수 -->

        <!-- 농축지동 -->
        <!-- <div @mouseover="popupShow('농축지동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '693px', left: '792px' }" :txtStyle="{ top: '74px', left: '235px' }"
          @click="this.$refs.cubeText.goFac('농축지동')"
          :backImg="require('@/assets/img/local_geumgang/gunsan/building/gun_nongchuk.png')" cubeText="농축지동"
          @popupShow="popupShow('농축지동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.농축지동 >= 0" :style="{ top: '656px', left: '1115px' }" :cubeVal="percentData.농축지동" />
        <!-- </div> -->
        <!-- 농축지동 -->

        <!-- 회수조동 -->
        <!-- <div @mouseover="popupShow('회수조동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '750px', left: '165px' }" :txtStyle="{ top: '82px', left: '160px' }"
          @click="this.$refs.cubeText.goFac('회수조동')"
          :backImg="require('@/assets/img/local_geumgang/gunsan/building/gs_hoesujo.png')" cubeText="회수조동"
          @popupShow="popupShow('회수조동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.회수조동 >= 0" :style="{ top: '718px', left: '414px' }" :cubeVal="percentData.회수조동" />
        <!-- </div> -->
        <!-- 회수조동 -->

        <!-- 탈수기동 -->
        <!-- <div @mouseover="popupShow('탈수기동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '750px', left: '1190px' }" :txtStyle="{ top: '43px', left: '124px' }"
          :backImg="require('@/assets/img/local_geumgang/gunsan/building/gun_water.png')" cubeText="탈수기동" ref="cubeText"
          @click="this.$refs.cubeText.goFac('탈수기동')" @popupShow="popupShow('탈수기동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.탈수기동 >= 0" :style="{ top: '680px', left: '1400px' }" :cubeVal="percentData.탈수기동" />
        <!-- </div> -->
        <!-- //탈수기동 -->

        <!-- 관리동 -->
        <!-- <div @mouseover="popupShow('관리동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '444px', left: '126px' }" :txtStyle="{ top: '83px', left: '62px' }"
          :backImg="require('@/assets/img/local_geumgang/gunsan/building/gs_gwalli.png')" cubeText="관리동" ref="cubeText"
          @click="this.$refs.cubeText.goFac('관리동')" @popupShow="popupShow('관리동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.관리동 >= 0" :style="{ top: '414px', left: '276px' }" :cubeVal="percentData.관리동" />
        <!-- </div> -->
        <!-- //관리동 -->


        <!-- 태양광
        <div @mouseover="popupShow('태양광')" @mouseout="popupHide()">
        <MainCubeText :style="{ top: '600px', left: '686px' }" :txtStyle="{ top: '35px', left: '-121px' }"
        @click="this.$refs.cubeText.goFac('태양광')" 
         cubeText="태양광" />
        <main-cube v-if="percentData.태양광 >= 0" :style="{ top: '530px', left: '648px' }" :cubeVal="percentData.태양광" />
          </div> -->
        <!-- 태양광 -->

        <!-- 기타설비 -->
        <!-- <MainCubeText :style="{ top: '480px', left: '1382px' }" :txtStyle="{ top: '35px', left: '-121px' }"
        cubeText="기타설비" />
        <main-cube v-if="percentData.기타설비 >= 0" :style="{ top: '402px', left: '1344px' }" :cubeVal="percentData.기타설비" /> -->
        <!-- 기타설비 -->



        <div class="waterflow1 flow01 no1"></div>
        <div class="waterflow2 flow01 no2"></div>
        <div class="waterflow3 flow01 no3"></div>
        <div class="waterflow1 flow01 no4"></div>
        <div class="waterflow2 flow01 no5"></div>
        <div class="waterflow3 flow01 no6"></div>

        <div class="waterflow1 flow02 no1"></div>
        <div class="waterflow2 flow02 no2"></div>
        <div class="waterflow3 flow02 no3"></div>

        <div class="waterflow1 flow03 no1"></div>
        <div class="waterflow2 flow03 no2"></div>
        <div class="waterflow3 flow03 no3"></div>

        <div class="waterflow1 flow04 no1"></div>
        <div class="waterflow2 flow04 no2"></div>
        <div class="waterflow3 flow04 no3"></div>
      </div>
      <div class="gunsan_bg"></div>
    </div>
    <HoverPopup ref="popup" :hoverVal="hoverVal" />
  </b-col>
  <!-- 군산 정수장 메인 -->
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

.gunsan_bg{
  position: absolute;
  top: -90px;
  left: -84px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  z-index: -1;
}

.waterwall_back_gunsan {
  position: absolute;
  top: -90px;
  left: -172px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/local_geumgang/gunsan/waterwall_gunsan.png) no-repeat;
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
  height: 43%;
  position: absolute;
  float: left;
  top: 75%;
  left: 26%;
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

.waterflow1.flow01,
.waterflow2.flow01,
.waterflow3.flow01 {
  top: 302px;
  left: 698px;
  offset-path: path("M0.0 0 L 301 -188 L 416 -157");
  animation: waterflow 7.2S linear 0s infinite normal backwards;
}

.waterflow1.flow02,
.waterflow2.flow02,
.waterflow3.flow02 {
  top: 214px;
  left: 1334px;
  offset-path: path("M0.0 0 L -122 -30");
  animation: waterflow 2S linear 0s infinite normal backwards;
}

.waterflow1.flow03,
.waterflow2.flow03,
.waterflow3.flow03 {
  top: 190px;
  left: 1166px;
  offset-path: path("M0.0 0 L -166 108");
  animation: waterflow 3S linear 0s infinite normal backwards;
}

.waterflow1.flow04,
.waterflow2.flow04,
.waterflow3.flow04 {
  top: 600px;
  left: 1074px;
  offset-path: path("M0.0 0 L -108 80");
  animation: waterflow 2S linear 0s infinite normal backwards;
}

.waterflow1.flow01.no1 {
  animation-delay: 0s;
}

.waterflow2.flow01.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow01.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow01.no4 {
  animation-delay: 3.6s;
}

.waterflow2.flow01.no5 {
  animation-delay: 3.8s;
}

.waterflow3.flow01.no6 {
  animation-delay: 4.0s;
}


.waterflow1.flow02.no1 {
  animation-delay: 0s;
}

.waterflow2.flow02.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow02.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow03.no1 {
  animation-delay: 0s;
}

.waterflow2.flow03.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow03.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow04.no1 {
  animation-delay: 0s;
}

.waterflow2.flow04.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow04.no3 {
  animation-delay: 0.4s;
}
</style>