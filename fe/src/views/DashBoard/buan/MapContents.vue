<template>
  <!-- 부안 정수장 메인 -->
  <b-col class="position-relative" style="z-index: 0">
    <div class="map-contents" :style="{ width: '100%', height: '900px' }">
      <div class="waterwall_back_buan">
        <!-- 혼화 & 응집 -->
        <MainCubeText :style="{ top: '441px', left: '799px' }" :txtStyle="{ left: '105px', top: '236px' }"
          :txtSubStyle="{ top: '138px', left: '379px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/bu_mixsink.png')" />
        <MainCube v-if="percentData['혼화/응집동'] >= 0" :style="{ top: '466px', left: '1263px' }"
          :cubeVal="percentData['혼화/응집동']" />
        <MainCube v-if="percentData.침전동 >= 0" :style="{ top: '560px', left: '992px' }" :cubeVal="percentData.침전동" />
        <!-- //혼화 & 응집 -->

        <!-- 착수 -->
        <MainCubeText :style="{ top: '844px', left: '668px' }" :txtStyle="{ left: '2px', top: '45px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/bu_get.png')" />
        <main-cube v-if="percentData.착수동 >= 0" :style="{ top: '777px', left: '756px' }" :cubeVal="percentData.착수동" />
        <!-- //착수 -->

        <!-- 약품 -->
        <!-- <div @mouseover="popupShow('약품동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '673px', left: '690px' }" :txtStyle="{ left: '34px', top: '58px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/bu_chemical.png')" cubeText="약품" ref="cubeText"
          @click="this.$refs.cubeText.goFac('약품동')" @popupShow="popupShow('약품동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.약품동 >= 0" :style="{ top: '618px', left: '810px' }" :cubeVal="percentData.약품동" />
        <!-- </div> -->
        <!-- //약품 -->

        <!-- 소독 -->
        <MainCubeText :style="{ top: '291px', left: '1276px' }" :txtStyle="{ top: '28px', left: '8px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/bu_disinfection.png')" />
        <main-cube v-if="percentData.소독동 >= 0" :style="{ top: '207px', left: '1371px' }" :cubeVal="percentData.소독동" />
        <!-- //소독 -->

        <!-- 여과 -->
        <!-- <div @mouseover="popupShow('여과지동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '346px', left: '1404px' }" :txtStyle="{ top: '82px', left: '125px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/bu_filter.png')" cubeText="여과" ref="cubeText"
          @click="this.$refs.cubeText.goFac('여과지동')" @popupShow="popupShow('여과지동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.여과지동 >= 0" :style="{ top: '314px', left: '1616px' }" :cubeVal="percentData.여과지동" />
        <!-- </div> -->
        <!-- //여과 -->

        <!-- 탈수기동 -->
        <!-- <div @mouseover="popupShow('탈수기동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '390px', left: '1803px' }" :txtStyle="{ top: '32px', left: '38px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/bu_talsu.png')" cubeText="탈수기동"
          @click="this.$refs.cubeText.goFac('탈수기동')" @popupShow="popupShow('탈수기동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.탈수기동 >= 0" :style="{ top: '313px', left: '1930px' }" :cubeVal="percentData.탈수기동" />
        <!-- </div> -->
        <!-- 탈수기동 -->

        <!-- 배출수동 -->
        <MainCubeText :style="{ top: '203px', left: '1527px' }" :txtStyle="{ top: '10px', left: '-21px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/bu_baechul.png')" />
        <main-cube v-if="percentData.배출수동 >= 0" :style="{ top: '102px', left: '1594px' }" :cubeVal="percentData.배출수동" />
        <!-- 배출수동 -->

        <!-- 배출동근처 시설(배경) -->
        <MainCubeText :style="{ top: '211px', left: '1465px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/an_dc.png')" />
        <!-- 배출동근처 시설(배경) -->

        <!-- 송수펌프동 -->
        <!-- <div @mouseover="popupShow('송수동')" @mouseout="popupHide()"> -->
        <MainCubeText :style="{ top: '960px', left: '1385px' }" :txtStyle="{ top: '84px', left: '225px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/an_main_side_deep.png')" cubeText="송수동"
          @click="this.$refs.cubeText.goFac('송수동')" @popupShow="popupShow('송수동')" @popupHide="popupHide()" />
        <main-cube v-if="percentData.송수동 >= 0" :style="{ top: '938px', left: '1693px' }" :cubeVal="percentData.송수동" />
        <!-- </div> -->
        <MainCubeText :style="{ top: '765px', left: '1405px' }"
          :backImg="require('@/assets/img/local_geumgang/buan/building/an_main_building.png')" />
        <!-- 송수펌프동 -->

        <div class="waterflow1 flow01 no1"></div>
        <div class="waterflow2 flow01 no2"></div>
        <div class="waterflow3 flow01 no3"></div>

        <div class="waterflow1 flow02 no1"></div>
        <div class="waterflow2 flow02 no2"></div>
        <div class="waterflow3 flow02 no3"></div>

        <div class="waterflow1 flow03 no1"></div>
        <div class="waterflow2 flow03 no2"></div>
        <div class="waterflow3 flow03 no3"></div>

        <div class="waterflow1 flow04 no1"></div>
        <div class="waterflow2 flow04 no2"></div>
        <div class="waterflow3 flow04 no3"></div>
        <div class="waterflow1 flow04 no4"></div>
        <div class="waterflow2 flow04 no5"></div>
        <div class="waterflow3 flow04 no6"></div>

        <div class="waterflow1 flow05 no1"></div>
        <div class="waterflow2 flow05 no2"></div>
        <div class="waterflow3 flow05 no3"></div>

        <div class="waterflow1 flow06 no1"></div>
        <div class="waterflow2 flow06 no2"></div>
        <div class="waterflow3 flow06 no3"></div>

        <div class="waterflow1 flow07 no1"></div>
        <div class="waterflow2 flow07 no2"></div>
        <div class="waterflow3 flow07 no3"></div>

        <!-- <div class="waterwall_back_buan"></div> -->
      </div>
      <div class="buan_bg"></div>

    </div>
    <HoverPopup ref="popup" :hoverVal="hoverVal" />
  </b-col>
  <!-- 부안 정수장 메인 -->
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
      top3Data?.forEach((item) => {
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
.buan_bg {
  position: absolute;
  top: -258px;
  left: -614px;
  width: 2485px;
  height: 1615px;
  background: url(@/assets/img/local_geumgang/buan/buan_bg.png) no-repeat;
  transform: scale(0.9, 0.9);
  opacity: 80%;
  z-index: -1;
}

.waterwall_back_buan {
  position: absolute;
  top: -274px;
  left: -627px;
  width: 2485px;
  height: 1615px;
  background: url(@/assets/img/local_geumgang/buan/waterwall_buan.png) no-repeat;
  background-size: 100% 100%;
  transform-origin: 50% 50%;
  mix-blend-mode: color-dodge;
  transform: scale(0.9, 0.9);
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
  width: 37%;
  height: 40%;
  position: absolute;
  float: left;
  top: 63%;
  left: 30%;
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
  top: 1061px;
  left: 448px;
  offset-path: path("M0.0 0 L 266 -108");
  animation: waterflow 3.8S linear 0s infinite normal backwards;
}

.waterflow1.flow02,
.waterflow2.flow02,
.waterflow3.flow02 {
  top: 887px;
  left: 688px;
  offset-path: path("M0.0 0 L -58 -58 L 28 -89");
  animation: waterflow 2.4S linear 0s infinite normal backwards;
}

.waterflow1.flow03,
.waterflow2.flow03,
.waterflow3.flow03 {
  top: 747px;
  left: 1316px;
  offset-path: path("M0.0 0 L 160 112");
  animation: waterflow 2.6S linear 0s infinite normal backwards;
}

.waterflow1.flow04,
.waterflow2.flow04,
.waterflow3.flow04 {
  top: 723px;
  left: 1398px;
  offset-path: path("M0.0 0 L 90 64 L 460 -110 L 348 -182");
  animation: waterflow 8.6S linear 0s infinite normal backwards;
}

.waterflow1.flow05,
.waterflow2.flow05,
.waterflow3.flow05 {
  top: 433px;
  left: 1441px;
  offset-path: path("M0.0 0 L -68 -44");
  animation: waterflow 1.2S linear 0s infinite normal backwards;
}

.waterflow1.flow06,
.waterflow2.flow06,
.waterflow3.flow06 {
  top: 348px;
  left: 1474px;
  offset-path: path("M0.0 0 L 92 -30");
  animation: waterflow 1.4S linear 0s infinite normal backwards;
}

.waterflow1.flow07,
.waterflow2.flow07,
.waterflow3.flow07 {
  top: 268px;
  left: 1710px;
  offset-path: path("M0.0 0 L 219 -76");
  animation: waterflow 3.4S linear 0s infinite normal backwards;
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

.waterflow1.flow04.no4 {
  animation-delay: 4.3s;
}

.waterflow2.flow04.no5 {
  animation-delay: 4.5s;
}

.waterflow3.flow04.no6 {
  animation-delay: 4.7s;
}

.waterflow1.flow05.no1 {
  animation-delay: 0s;
}

.waterflow2.flow05.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow05.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow06.no1 {
  animation-delay: 0s;
}

.waterflow2.flow06.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow06.no3 {
  animation-delay: 0.4s;
}

.waterflow1.flow07.no1 {
  animation-delay: 0s;
}

.waterflow2.flow07.no2 {
  animation-delay: 0.2s;
}

.waterflow3.flow07.no3 {
  animation-delay: 0.4s;
}
</style>