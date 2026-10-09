<template>
  <!-- 고령 정수장 메인 -->
  <b-col class="position-relative" style="z-index: 0;">
    <!-- class -> map-contents 구미 정수장에서 받고 있음 -->
    <div class="map-contents" :style="{ width: '100%', height: '800px' }">
      <div class="waterwall_back_goryeong">

        <!-- 혼화 & 응집 3 -->
        <MainCubeText :style="{ top: '292px', left: '378px' }" :txtStyle="{ top: '119px', left: '258px' }"
          :txtSubStyle="{ top: '149px', left: '293px' }" cubeText="혼화응집지"
          :backImg="require('@/assets/img/local_nakdong/goryeong/building/mixsink_3.png')"/>
          <MainCube v-if="percentData.혼화응집지3 >= 0" :style="{ top: '300px', left: '727px' }" :cubeVal="percentData.혼화응집지3" />
        <!-- 전오존동 추가 전 :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_mixsink_3.png')" :style="{ top: '170px', left: '234px' }"  -->
        <!-- 전오존동 추가 후 :backImg="require('@/assets/img/local_nakdong/goryeong/building/mixsink_3.png')" :style="{ top: '132px', left: '323px' }" -->
        <!-- //혼화 & 응집 3 -->

        <!-- 혼화 & 응집 4 -->
        <MainCubeText :style="{ top: '433px', left: '678px' }" :txtStyle="{ top: '105px', left: '323px' }"
          :txtSubStyle="{ top: '140px', left: '240px' }" cubeText="혼화응집지"
          :backImg="require('@/assets/img/local_nakdong/goryeong/building/mixsink_4.png')" />
          <MainCube v-if="percentData.혼화응집지4 >= 0" :style="{ top: '427px', left: '1087px' }" :cubeVal="percentData.혼화응집지4" />
        <!-- 전오존동 추가 전 :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_mixsink_4.png')" :style="{ top: '299px', left: '638px' }" -->
        <!-- 전오존동 추가 후 :backImg="require('@/assets/img/local_nakdong/goryeong/building/mixsink_4.png')" :style="{ top: '280px', left: '645px' }" -->
        <!-- //혼화 & 응집 4 -->

        <!-- 착수 -->
        <MainCubeText :style="{ top: '258px', left: '1190px' }" :txtStyle="{ top: '22px', left: '-9px' }"
        :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_get.png')"/>
        <MainCube v-if="percentData.착수동 >= 0" :style="{ top: '168px', left: '1265px' }" :cubeVal="percentData.착수동" />
        <!-- :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_get.png')"  -->
        <!-- //착수 -->

        <!-- 약품투입동 -->
        <div @mouseover="popupShow('약품동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '332px', left: '1034px' }" :txtStyle="{ top: '22px', left: '9px' }"
            :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_chemical.png')" ref="cubeText"
            @click="this.$refs.cubeText.goFac('약품동')" cubeText="약품투입동" />
          <MainCube v-if="percentData.약품동 >= 0" :style="{ top: '238px', left: '1108px' }" :cubeVal="percentData.약품동" />
        </div>
        <!-- //약품투입동 -->

        <!-- 차염투입동 -->
        <MainCubeText :style="{ top: '250px', left: '840px' }" :txtStyle="{ top: '16px', left: '-12px' }"
        :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_disinfection.png')"/>
        <MainCube v-if="percentData.차염투입동 >= 0" :style="{ top: '152px', left: '917px' }" :cubeVal="percentData.차염투입동" />
        <!-- //차염투입동 -->

        <!-- 모래여과지동 -->
        <div @mouseover="popupShow('여과지동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '507px', left: '302px' }" :txtStyle="{ top: '32px', left: '59px' }"
            :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_filter.png')" ref="cubeText"
            @click="this.$refs.cubeText.goFac('여과지동')" cubeText="모래여과지동" />
          <MainCube v-if="percentData.여과지동 >= 0" :style="{ top: '424px', left: '450px' }" :cubeVal="percentData.여과지동" />
        </div>
        <!-- //모래여과지동 -->

        <!-- 활성탄여과지동 -->
        <div @mouseover="popupShow('활성탄여과지')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '579px', left: '182px' }" :txtStyle="{ top: '15px', left: '-23px' }"
            :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_ozon.png')" ref="cubeText"
            @click="this.$refs.cubeText.goFac('활성탄여과지')" cubeText="활성탄여과지동" />
          <MainCube v-if="percentData.활성탄여과지 >= 0" :style="{ top: '482px', left: '247px' }" :cubeVal="percentData.활성탄여과지" />
        </div>
        <!-- //활성탄여과지동 -->

        <!-- 이산화탄소투입동 -->
        <MainCubeText :style="{ top: '619px', left: '322px' }" :txtStyle="{ top: '15px', left: '-23px' }"
        :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_ozon.png')"/>
        <MainCube v-if="percentData.이산화탄소투입동 >= 0" :style="{ top: '521px', left: '388px' }" :cubeVal="percentData.이산화탄소투입동"/>
        <!-- :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_ozon.png')"  -->
        <!-- //이산화탄소투입동 -->

        <!-- 탈수기동 -->
        <div @mouseover="popupShow('탈수기동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '690px', left: '100px' }" :txtStyle="{ top: '30px', left: '60px' }"
            :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_GACfilter.png')" ref="cubeText"
            @click="this.$refs.cubeText.goFac('탈수기동')" cubeText="탈수기동" />
          <MainCube v-if="percentData.탈수기동 >= 0" :style="{ top: '608px', left: '244px' }" :cubeVal="percentData.탈수기동"/>
        </div>
        <!-- //탈수기동 -->

        <!-- 공업송수동 -->
        <div @mouseover="popupShow('공업송수동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '673px', left: '868px' }" :txtStyle="{ top: '37px', left: '-15px' }"
            :backImg="require('@/assets/img/local_nakdong/goryeong/building/gongup.png')" ref="cubeText"
            @click="this.$refs.cubeText.goFac('공업송수동')" cubeText="공업송수동" />
          <MainCube v-if="percentData.공업송수동 >= 0" :style="{ top: '597px', left: '938px' }" :cubeVal="percentData.공업송수동" />
        </div>
        <!-- //공업송수동 -->

        <!-- 생활송수동 -->
        <div @mouseover="popupShow('생활송수동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '770px', left: '556px' }" :txtStyle="{ top: '26px', left: '43px' }"
            :backImg="require('@/assets/img/local_nakdong/goryeong/building/saenghwal.png')" ref="cubeText"
            @click="this.$refs.cubeText.goFac('생활송수동')" cubeText="생활송수동" />
          <MainCube v-if="percentData.생활송수동 >= 0" :style="{ top: '683px', left: '686px' }" :cubeVal="percentData.생활송수동" />
        </div>
        <!-- //생활송수동 -->

        <!-- 전오존동 -->
        <div @mouseover="popupShow('전오존동')" @mouseout="popupHide()">
          <MainCubeText :style="{ top: '201px', left: '1310px' }" :txtStyle="{ top: '23px', left: '-12px' }"
            :backImg="require('@/assets/img/local_nakdong/goryeong/building/go_get.png')" ref="cubeText"
            @click="this.$refs.cubeText.goFac('전오존동')" cubeText="전오존동" />
          <MainCube v-if="percentData.전오존동 >= 0" :style="{ top: '111px', left: '1385px' }" :cubeVal="percentData.전오존동" />
        </div>
        <!-- //전오존동 -->

        <!-- 관로 애니메이션  -->
        <!-- 전오존동 추가 후 -->
        <div class="waterflow1 flow1 no1"></div>
        <div class="waterflow2 flow1 no2"></div>
        <div class="waterflow3 flow1 no3"></div>

        <div class="waterflow1 flow2L no1"></div>
        <div class="waterflow2 flow2L no2"></div>
        <div class="waterflow3 flow2L no3"></div>

        <div class="waterflow1 flow2R no1"></div>
        <div class="waterflow2 flow2R no2"></div>
        <div class="waterflow3 flow2R no3"></div>

        <div class="waterflow1 flow3L no1"></div>
        <div class="waterflow2 flow3L no2"></div>
        <div class="waterflow3 flow3L no3"></div>

        <div class="waterflow1 flow3R no1"></div>
        <div class="waterflow2 flow3R no2"></div>
        <div class="waterflow3 flow3R no3"></div>

        <div class="waterflow1 flow4 no1"></div>
        <div class="waterflow2 flow4 no2"></div>
        <div class="waterflow3 flow4 no3"></div>

        <div class="waterflow1 flow5 no1"></div>
        <div class="waterflow2 flow5 no2"></div>
        <div class="waterflow3 flow5 no3"></div>

        <div class="waterflow1 flow6U no1"></div>
        <div class="waterflow2 flow6U no2"></div>
        <div class="waterflow3 flow6U no3"></div>

        <div class="waterflow1 flow6D no1"></div>
        <div class="waterflow2 flow6D no2"></div>
        <div class="waterflow3 flow6D no3"></div>

        <div class="waterflow1 flowO no1"></div>
        <div class="waterflow2 flowO no2"></div>
        <div class="waterflow3 flowO no3"></div>

        <!-- <div class="waterwall_back_goryeong"></div> -->
      </div>
      <div class="goryeong_bg"></div>
    </div>
    <HoverPopup ref="popup" :hoverVal="hoverVal" />
  </b-col>
  <!-- 고령 정수장 메인 -->
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

/* .goryeong_bg{
  position: absolute;
  top: -522px;
  left: -94px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  transform-origin: 50% 50%;
  transform: scale(1);
} */
.goryeong_bg{
  position: absolute;
  top: -132px;
  left: -94px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/Default_bg.png) no-repeat;
  z-index: -1;
}

/* .waterwall_back_goryeong {
  position: absolute; 
  top: 0px;
  left: -20px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/local_nakdong/goryeong/waterwall_goryeong.png) no-repeat;
} */
.waterwall_back_goryeong {
  position: absolute; 
  top: -112px;
  left: -118px;
  width: 1920px;
  height: 1080px;
  background: url(@/assets/img/local_nakdong/goryeong/waterwall_goryeong.png) no-repeat;
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
  height: 40%;
  position: absolute;
  float: left;
  top: 71%;
  left: 66%;
  display: none;
  animation: move-up-building 1s ease-in-out 0s normal backwards;
}

.hoverInfoNone {
  position: absolute;
  /* 박스를 아래로 내리도록 조정 */
  right: 0;
  width: 35%;
  animation: move-down-popup 1s ease-in-out 0s normal forwards;
  /* 새로운 애니메이션 적용 */
}

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

.waterflow1.flow1,
.waterflow2.flow1,
.waterflow3.flow1 {
  top: 327px;
  left: 1247px;
  offset-path: path("M0.0 0 L -82 35");
  animation: waterflow 1.2S linear 0s infinite normal backwards;
}

.waterflow1.flow2L,
.waterflow2.flow2L,
.waterflow3.flow2L {
  top: 385px;
  left: 1051px;
  offset-path: path("M0.0 0 L -78 -22 L -176 20");
  animation: waterflow 2.4S linear 0s infinite normal backwards;
}

.waterflow1.flow2R,
.waterflow2.flow2R,
.waterflow3.flow2R {
  top: 410px;
  left: 1161px;
  offset-path: path("M0.0 0 L 198 52 L 70 111");
  animation: waterflow 4.5S linear 0s infinite normal backwards;
}

.waterflow1.flow3L,
.waterflow2.flow3L,
.waterflow3.flow3L {
  top: 498px;
  left: 551px;
  offset-path: path("M0.0 0 L -96 39");
  animation: waterflow 1.4S linear 0s infinite normal backwards;
}

.waterflow1.flow3R,
.waterflow2.flow3R,
.waterflow3.flow3R {
  top: 628px;
  left: 872px;
  offset-path: path("M0.0 0 L -112 44 L -320 -10");
  animation: waterflow 4S linear 0s infinite normal backwards;
}

.waterflow1.flow4,
.waterflow2.flow4,
.waterflow3.flow4 {
  top: 594px;
  left: 338px;
  offset-path: path("M0.0 0 L -58 28");
  animation: waterflow 0.9S linear 0s infinite normal backwards;
}

.waterflow1.flow5,
.waterflow2.flow5,
.waterflow3.flow5 {
  top: 640px;
  left: 228px;
  offset-path: path("M0.0 0 L -129 52 L -52 73");
  animation: waterflow 2.8S linear 0s infinite normal backwards;
}

.waterflow1.flow6U,
.waterflow2.flow6U,
.waterflow3.flow6U {
  top: 791px;
  left: 364px;
  offset-path: path("M0.0 0 L 56 12 L 294 -78 L 350 -65");
  animation: waterflow 4.5S linear 0s infinite normal backwards;
}

.waterflow1.flow6D,
.waterflow2.flow6D,
.waterflow3.flow6D {
  top: 810px;
  left: 315px;
  offset-path: path("M0.0 0 L 124 33");
  animation: waterflow 1.6S linear 0s infinite normal backwards;
}

.waterflow1.flowO,
.waterflow2.flowO,
.waterflow3.flowO {
  top: 272px;
  left: 1366px;
  offset-path: path("M0.0 0 L -82 35");
  animation: waterflow 1.2S linear 0s infinite normal backwards;
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

.waterflow1.flow2L.no1 {
  animation-delay: 0s;
}

.waterflow2.flow2L.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow2L.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow2R.no1 {
  animation-delay: 0s;
}

.waterflow2.flow2R.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow2R.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow3L.no1 {
  animation-delay: 0s;
}

.waterflow2.flow3L.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow3L.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow3R.no1 {
  animation-delay: 0s;
}

.waterflow2.flow3R.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow3R.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow4.no1 {
  animation-delay: 0s;
}

.waterflow2.flow4.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow4.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow5.no1 {
  animation-delay: 0s;
}

.waterflow2.flow5.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow5.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow6U.no1 {
  animation-delay: 0s;
}

.waterflow2.flow6U.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow6U.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow6D.no1 {
  animation-delay: 0s;
}

.waterflow2.flow6D.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow6D.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flowO.no1 {
  animation-delay: 0s;
}

.waterflow2.flowO.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flowO.no3 {
  animation-delay: 0.4s;
}
</style>