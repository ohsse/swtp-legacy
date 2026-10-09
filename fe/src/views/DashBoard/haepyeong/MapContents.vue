<template>
  <!-- 고산 정수장 메인 -->
  <b-col class="position-relative" style="z-index: 0;">
    <!-- class -> map-contents 구미 정수장에서 받고 있음 -->
    <div class="map-contents" :style="{ width: '100%', height: '550px' }">
      <div class="waterwall_back_haepyeong">

        <!-- 혼화 & 응집 -->
        <MainCubeText :style="{ top: '248px', left: '718px' }" :txtStyle="{ top: '127px', left: '351px' }"
          :backImg="require('@/assets/img/local_nakdong/haepyeong/building/hae_mixsink.png')" />
        <main-cube v-if="percentData['혼화/응집동'] >= 0" :style="{ top: '266px', left: '1154px' }" :cubeVal="percentData['혼화/응집동']" />
        <!-- //혼화 & 응집 -->

        <!-- 착수 -->
        <MainCubeText :style="{ top: '115px', left: '1356px' }" :txtStyle="{ top: '25px', left: '19px' }"
          :backImg="require('@/assets/img/local_nakdong/haepyeong/building/hae_get.png')" />
        <main-cube v-if="percentData['착수동'] >= 0" :style="{ top: '26px', left: '1459px' }" :cubeVal="percentData.착수동" />
        <!-- //착수 -->

        <!-- 약품 -->
        <div @mouseover="popupShow('약품투입동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '181px', left: '1509px' }" :txtStyle="{ top: '38px', left: '87px' }"
            :backImg="require('@/assets/img/local_nakdong/haepyeong/building/hae_chemical.png')" cubeText="약품투입동"
            ref="cubeText" @click="this.$refs.cubeText.goFac('약품투입동')" />
          <main-cube v-if="percentData.약품투입동 >= 0" :style="{ top: '107px', left: '1680px' }"
            :cubeVal="percentData.약품투입동" />
        </div>
        <!-- //약품 -->

        <!-- 송수
        <div @mouseover="popupShow('송수동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '546px', left: '444px' }" :txtStyle="{ top: '24px', left: '28px' }"
            :backImg="require('@/assets/img/local_nakdong/haepyeong/building/hae_get.png')" cubeText="송수동" ref="cubeText"
            @click="this.$refs.cubeText.goFac('송수동')" />
          <main-cube v-if="percentData.송수동 >= 0" :style="{ top: '452px', left: '559px' }" :cubeVal="percentData.송수동" />
        </div>
        //송수 -->

        <!-- 송수 & 비상발전기 & 수변전실 -->
        <div @mouseover="popupShow('송수펌프동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '532px', left: '354px' }" :txtStyle="{ top: '85px', left: '272px' }"
            :backImg="require('@/assets/img/local_nakdong/haepyeong/building/water.png')" cubeText="송수펌프동"
            ref="cubeText" @click="this.$refs.cubeText.goFac('송수펌프동')" />
        </div>
        <div @mouseover="popupShow('비상발전기')" @mouseout="popupHide()">
          <MainCubeText :txtSubStyle="{ top: '587px', left: '506px' }" cubeSubText="비상발전기" ref="cubeText"
            @click="this.$refs.cubeText.goFac('비상발전기')" />
        </div>
        <div @mouseover="popupShow('수변전실')" @mouseout="popupHide()">
          <MainCubeText :txtSubSecoundStyle="{ top: '557px', left: '386px' }" cubeSubSecoundText="수변전실" ref="cubeText"
            @click="this.$refs.cubeText.goFac('수변전실')" />
        </div>
        <main-cube v-if="percentData.송수펌프동 >= 0" :style="{ top: '504px', left: '713px' }" :cubeVal="percentData.송수펌프동" />
        <main-cube v-if="percentData.비상발전기 >= 0" :style="{ top: '474px', left: '592px' }" :cubeVal="percentData.비상발전기" />
        <main-cube v-if="percentData.수변전실 >= 0" :style="{ top: '443px', left: '473px' }" :cubeVal="percentData.수변전실" />
        <!-- //송수 & 비상발전기 & 수변전실  -->

        <!-- 탈수기동 -->
        <div @mouseover="popupShow('탈수기동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '695px', left: '314px' }" :txtStyle="{ top: '38px', left: '76px' }"
            :backImg="require('@/assets/img/local_nakdong/haepyeong/building/mixsink.png')" cubeText="탈수기동"
            ref="cubeText" @click="this.$refs.cubeText.goFac('탈수기동')" />
          <main-cube v-if="percentData.탈수기동 >= 0" :style="{ top: '583px', left: '501px' }"
            :cubeVal="percentData.탈수기동" />
        </div>
        <!-- //탈수기동 -->

        <!-- 관리본부 -->
        <div @mouseover="popupShow('관리본부')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '658px', left: '218px' }" :txtStyle="{ top: '12px', left: '-2px' }"
            :backImg="require('@/assets/img/local_nakdong/haepyeong/building/management.png')"
            @click="this.$refs.cubeText.goFac('관리본부')" />
          <main-cube v-if="percentData.관리본부 >= 0" :style="{ top: '560px', left: '300px' }" :cubeVal="percentData.관리본부" />
        </div>
        <!-- //관리본부 -->

        <div class="waterflow1 flow1 no1"></div>
        <div class="waterflow2 flow1 no2"></div>
        <div class="waterflow3 flow1 no3"></div>

        <div class="waterflow1 flow2 no1"></div>
        <div class="waterflow2 flow2 no2"></div>
        <div class="waterflow3 flow2 no3"></div>

        <div class="waterflow1 flow3 no1"></div>
        <div class="waterflow2 flow3 no2"></div>
        <div class="waterflow3 flow3 no3"></div>
        <div class="waterflow1 flow3 no4"></div>
        <div class="waterflow2 flow3 no5"></div>
        <div class="waterflow3 flow3 no6"></div>

        <!-- <div class="waterflow1 flow4 no1"></div>
        <div class="waterflow2 flow4 no2"></div>
        <div class="waterflow3 flow4 no3"></div> -->

        <!-- <div class="waterwall_back_haepyeong"></div> -->
      </div>
      <div class="haepyeong_bg"></div>
    </div>
    <HoverPopup ref="popup" :hoverVal="hoverVal" />
  </b-col>
  <!-- //고산 정수장 메인 -->
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

/* .haepyeong_bg{
  position: absolute;
  top: -442px;
  left: -84px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  transform-origin: 50% 50%;
  transform: scale(1);
} */
.haepyeong_bg{
  position: absolute;
  top: -100px;
  left: -84px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  background-size: 100% 100%;
  z-index: -1;
}


/* .waterwall_back_haepyeong {
  position: absolute;
  top: 90px;
  left: -20px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/local_nakdong/haepyeong/waterwall_haepyeong.png) no-repeat;
} */
.waterwall_back_haepyeong {
  position: absolute;
  top: -100px;
  left: -84px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/local_nakdong/haepyeong/waterwall_haepyeong.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  transform-origin: 50% 50%;
  transform: scale(0.95);
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
  width: 40%;
  height: 62%;
  position: absolute;
  float: left;
  top: 53%;
  left: 62%;
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
  top: 212px;
  left: 1411px;
  offset-path: path("M0.0 0 L -68 28 L 146 86 L 50 127");
  animation: waterflow 4.2S linear 0s infinite normal backwards;
}

.waterflow1.flow2,
.waterflow2.flow2,
.waterflow3.flow2 {
  top: 556px;
  left: 1182px;
  offset-path: path("M0.0 0 L 90 22 L -253 168 L -402 131");
  animation: waterflow 6.5S linear 0s infinite normal backwards;
}

.waterflow1.flow3,
.waterflow2.flow3,
.waterflow3.flow3 {
  top: 703px;
  left: 583px;
  offset-path: path("M0.0 0 L -119 53 L 323 180 L 32 293");
  animation: waterflow 9.2S linear 0s infinite normal backwards;
}

/* .waterflow1.flow4,
.waterflow2.flow4,
.waterflow3.flow4 {
  top: 740px;
  left: 604px;
  offset-path: path("M0.0 0 L 338 98 L 49 213");
  animation: waterflow 3.8S linear 0s infinite normal backwards;
} */

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

.waterflow1.flow3.no4 {
  animation-delay: 4.6s;
}

.waterflow2.flow3.no5 {
  animation-delay: 4.8s;
}

.waterflow3.flow3.no6 {
  animation-delay: 5.0s;
}

/* .waterflow1.flow4.no1 {
  animation-delay: 0s;
}

.waterflow2.flow4.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow4.no3 {
  animation-delay: 0.4s;
} */
</style>