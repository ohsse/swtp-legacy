<template>
  <!-- 산성 정수장 메인 -->
  <b-col class="position-relative" style="z-index: 0;">
    <div class="map-contents" :style="{width: '100%',height: '550px'}">
      <div class="waterwall_back_sanseong">
        <!-- 혼화 & 응집 -->
        <MainCubeText :style="{ top: '263px', left: '333px'}"
          :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_mixsink.png')" />
        <main-cube v-if="percentData['혼화/응집동'] >= 0" :style="{ top: '373px', left: '667px' }" :cubeVal="percentData['혼화/응집동']" />
        <main-cube v-if="percentData.침전동 >= 0" :style="{ top: '293px', left: '864px' }" :cubeVal="percentData.침전동" />
        <!-- //혼화 & 응집 -->

        <!-- 착수 -->
        <MainCubeText :style="{ top: '757px', left: '294px'}" 
        :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_disinfection.png')" />
        <main-cube v-if="percentData.착수동 >= 0" :style="{ top: '671px', left: '398px' }" :cubeVal="percentData.착수동" />
        <!-- //착수 -->

        <!-- 약품 -->
        <MainCubeText :style="{ top: '615px', left: '488px'}"
          :txtStyle="{ left: '74px', top: '44px' }"
          :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_chemical_get.png')" cubeText="약품투입동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('약품투입동')" @popupShow="popupShow('약품투입동')"
          @popupHide="popupHide()" />
        <main-cube v-if="percentData.약품투입동 >= 0" :style="{ top: '546px', left: '648px' }" :cubeVal="percentData.약품투입동" />
        <!-- //약품 -->

        <!-- 약품옆 -->
        <MainCubeText :style="{ top: '615px', left: '337px'}"
        :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_chemical_left.png')" />
        <!-- //약품옆 -->

        <!-- 소독 -->
        <MainCubeText :style="{ top: '134px', left: '990px'}" 
        :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_disinfection.png')"  />
        <main-cube v-if="percentData.소독동 >= 0" :style="{ top: '48px', left: '1095px' }" :cubeVal="percentData.소독동" />
        <!-- //소독 -->

        <!-- 차염투입동 -->
        <MainCubeText :style="{ top: '103px', left: '861px'}" :txtStyle="{ left: '21px', top: '25px' }"
          :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_disinfection.png')" cubeText="차염투입동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('차염투입동')" @popupShow="popupShow('차염투입동')"
          @popupHide="popupHide()" />
        <main-cube v-if="percentData.차염투입동 >= 0" :style="{ top: '19px', left: '971px' }" :cubeVal="percentData.차염투입동" />
        <!-- 차염투입동-->

        <!-- 여과 -->
        <MainCubeText :style="{ top: '150px', left: '1189px'}" :txtStyle="{ left: '146px', top: '56px' }"
          :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_filter.png')" cubeText="여과지동"
          ref="cubeText" @click="this.$refs.cubeText.goFac('여과지동')" @popupShow="popupShow('여과지동')"
          @popupHide="popupHide()" />
        <main-cube v-if="percentData.여과지동 >= 0" :style="{ top: '94px', left: '1421px' }" :cubeVal="percentData.여과지동" />
        <!-- //여과 -->

        <!-- 회수 -->
        <MainCubeText :style="{ top: '110px', left: '1462px'}" :txtStyle="{ left: '100px', top: '42px' }" 
          @click="this.$refs.cubeText.goFac('회수펌프동')"
          :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_return.png')" cubeText="회수펌프동"
          @popupShow="popupShow('회수펌프동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.회수펌프동 >= 0" :style="{ top: '40px', left: '1648px' }" :cubeVal="percentData.회수펌프동" />
        <!-- //회수 -->

        <!-- 역세펌프동 -->
        <MainCubeText :style="{ top: '369px', left: '1698px'}" :txtStyle="{ left: '44px', top: '1px' }"
          :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_pump.png')"
          @click="this.$refs.cubeText.goFac('역세펌프동')" cubeText="역세펌프동" @popupShow="popupShow('역세펌프동')"
          @popupHide="popupHide()" />
        <main-cube v-if="percentData.역세펌프동 >= 0" :style="{ top: '278px', left: '1793px' }" :cubeVal="percentData.역세펌프동" />
        <!-- 역세펌프동 -->


        <!-- 정읍가압장 -->
        <MainCubeText :style="{ top: '782px', left: '752px'}" :txtStyle="{ left: '69px', top: '41px' }"
          :backImg="require('@/assets/img/local_geumgang/sanseong/building/san_chemical_get.png')" cubeText="정읍가압장"
          ref="cubeText" @click="this.$refs.cubeText.goFac('정읍가압장')" @popupShow="popupShow('정읍가압장')"
          @popupHide="popupHide()" />
        <main-cube v-if="percentData.정읍가압장 >= 0" :style="{ top: '709px', left: '909px' }" :cubeVal="percentData.정읍가압장" />
        <!-- 정읍가압장 -->



        <div class="waterflow1 get no1"></div>
        <div class="waterflow2 get no2"></div>
        <div class="waterflow3 get no3"></div>
        <!-- <div class="waterflow1 get no4"></div>
        <div class="waterflow2 get no5"></div>
        <div class="waterflow3 get no6"></div> -->

        <div class="waterflow1 gc no1"></div>
        <div class="waterflow2 gc no2"></div>
        <div class="waterflow3 gc no3"></div>

        <div class="waterflow1 cm no1"></div>
        <div class="waterflow2 cm no2"></div>
        <div class="waterflow3 cm no3"></div>
        <!-- <div class="waterflow1 cm no4"></div>
        <div class="waterflow2 cm no5"></div>
        <div class="waterflow3 cm no6"></div>
        <div class="waterflow1 cm no7"></div>
        <div class="waterflow2 cm no8"></div>
        <div class="waterflow3 cm no9"></div> -->

        <div class="waterflow1 fp no1"></div>
        <div class="waterflow2 fp no2"></div>
        <div class="waterflow3 fp no3"></div>
        <!-- <div class="waterflow1 fp no4"></div>
        <div class="waterflow2 fp no5"></div>
        <div class="waterflow3 fp no6"></div> -->

        <div class="waterflow1 sf no1"></div>
        <div class="waterflow2 sf no2"></div>
        <div class="waterflow3 sf no3"></div>
        <!-- <div class="waterflow1 sf no4"></div>
        <div class="waterflow2 sf no5"></div>
        <div class="waterflow3 sf no6"></div> -->

      </div>
      <div class="sanseong_bg"></div>
    </div>
    <HoverPopup ref="popup" :hoverVal="hoverVal" />
  </b-col>
  <!-- 산성 정수장 메인 -->
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

.sanseong_bg{
  position: absolute;
  top: -439px;
  left: 14px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  background-size: 100% 100%;
  z-index: -1;
}

.waterwall_back_sanseong {
  position: absolute;
  top: -88px;
  left: -174px;
  width: 2130px;
  height: 1080px;
  background: url(@/assets/img/local_geumgang/sanseong/waterwall_sanseong2.png) no-repeat;
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
  height: 59%;
  position: absolute;
  float: left;
  top: 50%;
  left: 49%;
  display: none;
}

/* .waterflow1 {
  background-image: url(@/assets/img/water.png);
  position: absolute;
  width: 13px;
  height: 21px;
  background-size: 100% 100%;
}

.waterflow2 {
  background-image: url(@/assets/img/water2.png);
  position: absolute;
  width: 13px;
  height: 21px;
  background-size: 100% 100%;
}

.waterflow3 {
  background-image: url(@/assets/img/water3.png);
  position: absolute;
  width: 13px;
  height: 21px;
  background-size: 100% 100%;
} */

.waterflow1 {
  background-image: url(@/assets/img/water.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.5);
}

.waterflow2 {
  background-image: url(@/assets/img/water2.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.5);
}

.waterflow3 {
  background-image: url(@/assets/img/water3.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.5);
}

.waterflow1.get,
.waterflow2.get,
.waterflow3.get {
  top: 955px;
  left: 107px;
  offset-path: path("M0.0 0 L 248 -113");
  animation: waterflow 3S linear 0s infinite normal backwards;
}

.waterflow1.gc,
.waterflow2.gc,
.waterflow3.gc {
  top: 784px;
  left: 420px;
  offset-path: path("M0.0 0 L 122 -56");
  animation: waterflow 1.6S linear 0s infinite normal backwards;
}

.waterflow1.cm,
.waterflow2.cm,
.waterflow3.cm {
  top: 729px;
  left: 718px;
  offset-path: path("M0.0 0 L 129 42 L 350 -56 L 206 -101");
  animation: waterflow 6.6S linear 0s infinite normal backwards;
}

.waterflow1.sf,
.waterflow2.sf,
.waterflow3.sf {
  top: 342px;
  left: 1065px;
  offset-path: path("M0.0 0 L 90 -38 L 246 2 L 317 -30");
  animation: waterflow 4.4S linear 0s infinite normal backwards;
}

.waterflow1.fp,
.waterflow2.fp,
.waterflow3.fp {
  top: 325px;
  left: 1523px;
  offset-path: path("M0.0 0 L 150 49");
  animation: waterflow 2S linear 0s infinite normal backwards;
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

.waterflow1.get.no1 {
  animation-delay: 0s;
}

.waterflow2.get.no2 {
  animation-delay: 0.2s;
}

.waterflow3.get.no3 {
  animation-delay: 0.4s;
}

.waterflow1.get.no4 {
  animation-delay: 1.8s;
}

.waterflow2.get.no5 {
  animation-delay: 2.0s;
}

.waterflow3.get.no6 {
  animation-delay: 2.2s;
}

.waterflow1.gc.no1 {
  animation-delay: 3.0s;
}

.waterflow2.gc.no2 {
  animation-delay: 3.2s;
}

.waterflow3.gc.no3 {
  animation-delay: 3.4s;
}


.waterflow1.cm.no1 {
  animation-delay: 4.6s;
}

.waterflow2.cm.no2 {
  animation-delay: 4.8s;
}

.waterflow3.cm.no3 {
  animation-delay: 5.0s;
}

.waterflow1.cm.no4 {
  animation-delay: 6.75s;
}

.waterflow2.cm.no5 {
  animation-delay: 7.0s;
}

.waterflow3.cm.no6 {
  animation-delay: 7.25s;
}

.waterflow1.cm.no7 {
  animation-delay: 6.0s;
}

.waterflow2.cm.no8 {
  animation-delay: 6.2s;
}

.waterflow3.cm.no9 {
  animation-delay: 6.4s;
}

.waterflow1.sf.no1 {
  animation-delay: 11.2s;
}

.waterflow2.sf.no2 {
  animation-delay: 11.4s;
}

.waterflow3.sf.no3 {
  animation-delay: 11.6s;
}

.waterflow1.fp.no1 {
  animation-delay: 15.6s;
}

.waterflow2.fp.no2 {
  animation-delay: 15.8s;
}

.waterflow3.fp.no3 {
  animation-delay: 16s;
}
</style>