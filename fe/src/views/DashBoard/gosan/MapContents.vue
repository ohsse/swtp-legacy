<template>
  <!-- 고산 정수장 메인 -->
  <b-col class="position-relative" style="z-index: 0;">
    <div class="map-contents" :style="{ height: 'calc(100vh - 118px)' }">

      <div class="gosan_bg">

        <!-- 혼화/응집 & 침전-->
        <!-- ✅✅ 비활성화 전력일 경우 backImg 건물 지우기, cubeText,cubeSubText 지울 경우 건물명 없어져요 ✅✅  -->
        <MainCubeText :style="{ top: '308px', left: '640px'}"
        :txtStyle="{ top: '90px', left: '37px' }" :txtSubStyle="{ top: '90px', left: '218px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_mixsink_left.png')" />
        <!-- //혼화/응집 & 침전 -->

        <!-- 착수 -->
        <MainCubeText :style="{ top: '306px', left: '1106px'}"
        :txtStyle="{ top: '13px', left: '-50px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_get.png')"/>
        <!-- //착수 -->

        <!-- 약품투입동 -->
        <!-- <div @popupShow="popupShow('약품투입동')" @popupHide="popupHide()"> -->
        <MainCubeText :style="{ top: '380px', left: '1062px' }" ref="cubeText" @click="this.$refs.cubeText.goFac('약품투입동')"
          :txtStyle="{ top: '12px', left: '-65px' }"
          :backImg="require('@/assets/img/local_geumgang/gosan/building/go_chemical.png')" cubeText="약품투입동"
          @popupShow="popupShow('약품투입동')" @popupHide="popupHide()" />
        <MainCube v-if="percentData.약품투입동" :style="{ top: '266px', left: '1085px' }" :cubeVal="percentData.약품투입동" />
        <!-- </div> -->
        <!-- //약품투입동 -->

        <!-- 차염투입동 -->
        <!-- <div @popupShow="popupShow('차염투입동')" @popupHide="popupHide()"> -->
        <MainCubeText :style="{ top: '448px', left: '1088px' }" ref="cubeText"
          @click="this.$refs.cubeText.goFac('차염투입동')" :txtStyle="{ top: '6px', left: '5px' }"
          :backImg="require('@/assets/img/local_geumgang/gosan/building/go_disinfection.png')" cubeText="차염투입동"
          @popupShow="popupShow('차염투입동')" @popupHide="popupHide()" />
        <MainCube v-if="percentData.차염투입동"  :style="{ top: '323px', left: '1185px' }" :cubeVal="percentData.차염투입동" />
        <!-- </div> -->
        <!-- //차염투입동 -->

        <!-- 혼화/응집 & 침전(오른쪽) -->
        <MainCubeText :style="{ top: '304px', left: '1214px'}"
        :txtStyle="{ top: '90px', left: '34px' }" :txtSubStyle="{ top: '90px', left: '204px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_mixsink_right.png')" />
        <!-- //혼화/응집 & 침전(오른쪽) -->

        <!-- 여과 -->
        <MainCubeText :style="{ top: '502px', left: '608px'}"
        :txtStyle="{ top: '70px', left: '41px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_filter_left.png')"/>
        <!-- //여과 -->

        <!-- 송수 -->
        <!-- <div @popupShow="popupShow('송수동(구)')" @popupHide="popupHide()"> -->
        <MainCubeText :style="{ top: '632px', left: '855px' }" ref="cubeText"
          @click="this.$refs.cubeText.goFac('송수동(구)')" :txtStyle="{ top: '8px', left: '132px' }"
          :backImg="require('@/assets/img/local_geumgang/gosan/building/go_water.png')" cubeText="송수동(구)"
          @popupShow="popupShow('송수동(구)')" @popupHide="popupHide()" />
        <MainCube v-if="percentData['송수동(구)']" :style="{ top: '513px', left: '1072px' }"
          :cubeVal="percentData['송수동(구)']" />
        <!-- </div> -->
        <!-- //송수 -->

        <!-- 여과(오른쪽) -->
        <MainCubeText :style="{ top: '498px', left: '1326px'}"
        :txtStyle="{ top: '70px', left: '30px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_filter_right.png')"/>
        <!-- //여과(오른쪽) -->

        <!-- 관리본부 -->
        <MainCubeText :style="{ top: '522px', left: '1545px'}"
        :txtStyle="{ top: '46px', left: '10px' }" 
        :backImg="require('@/assets/img/local_geumgang/gosan/building/management.png')"/> 
        <!-- //관리본부 -->

        <!-- 농축조 -->
        <MainCubeText :style="{ top: '770px', left: '700px'}"
        :txtStyle="{ top: '74px', left: '30px'}"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/san_circles_area.png')"  />
        <!-- //농축조 -->

        <!-- 탈수기동 -->
        <!-- <div @popupShow="popupShow('탈수기동')" @popupHide="popupHide()"> -->
        <MainCubeText :style="{ top: '968px', left: '758px' }" :txtStyle="{ top: '50px', left: '8px' }" ref="cubeText"
          @click="this.$refs.cubeText.goFac('탈수기동')"
          :backImg="require('@/assets/img/local_geumgang/gosan/building/san_large_building.png')" cubeText="탈수기동"
          @popupShow="popupShow('탈수기동')" @popupHide="popupHide()" />
        <MainCube v-if="percentData.탈수기동" :style="{ top: '896px', left: '857px' }" :cubeVal="percentData.탈수기동" />
        <!-- </div> -->
        <!-- //탈수기동 -->

        <!-- 회수펌프동 -->
        <!-- <div @popupShow="popupShow('회수펌프동')" @popupHide="popupHide()"> -->
        <MainCubeText :style="{ top: '752px', left: '1080px' }" :txtStyle="{ top: '52px', left: '51px' }" ref="cubeText"
          @click="this.$refs.cubeText.goFac('회수펌프동')"
          :backImg="require('@/assets/img/local_geumgang/gosan/building/san_center_building.png')" cubeText="회수펌프동"
          @popupShow="popupShow('회수펌프동')" @popupHide="popupHide()" />
        <MainCube v-if="percentData.회수펌프동" :style="{ top: '683px', left: '1209px' }" :cubeVal="percentData.회수펌프동" />
        <!-- </div> -->
        <!-- //회수펌프동 -->

        <!-- 송수펌프동(신) 전기실  -->
        <!-- TODO : 송수펌프동(신) 어떻게 들어오는지 확인하기    -->
        <!-- <div @popupShow="popupShow('송수동(신)')" @popupHide="popupHide()"> -->
        <MainCubeText :style="{ top: '910px', left: '1562px' }" :txtStyle="{ top: '44px', left: '-44px' }"
          ref="cubeText" @click="this.$refs.cubeText.goFac('송수동(신)')"
          :backImg="require('@/assets/img/local_geumgang/gosan/building/san_small_building.png')" cubeText="송수동(신)"
          @popupShow="popupShow('송수동(신)')" @popupHide="popupHide()" />
        <MainCube v-if="percentData['송수동(신)']" :style="{ top: '831px', left: '1603px' }"
          :cubeVal="percentData['송수동(신)']" />
        <!-- </div> -->
        <!-- 송수펌프동(신) 전기실  -->

         <!-- 건물1 -->
         <MainCubeText :style="{ top: '704px', left: '1690px'}" 
        :backImg="require('@/assets/img/local_geumgang/gosan/building/san_layer_h.png')"/>
        
        <!-- //건물1 -->

         <!-- 건물2 -->
         <MainCubeText :style="{ top: '756px', left: '1751px'}" 
        :backImg="require('@/assets/img/local_geumgang/gosan/building/san_layer_v.png')"/>
        
        <!-- //건물2 -->


        <div>
          <div class="waterflow1 fwleft no1"></div>
          <div class="waterflow2 fwleft no2"></div>
          <div class="waterflow3 fwleft no3"></div>

          <div class="waterflow1 fwright no1"></div>
          <div class="waterflow2 fwright no2"></div>
          <div class="waterflow3 fwright no3"></div>

          <div class="waterflow1 gmleft no1"></div>
          <div class="waterflow2 gmleft no2"></div>
          <div class="waterflow3 gmleft no3"></div>

          <div class="waterflow1 gmright no1"></div>
          <div class="waterflow2 gmright no2"></div>
          <div class="waterflow3 gmright no3"></div>

          <div class="waterflow1 ms1 no1"></div>
          <div class="waterflow2 ms1 no2"></div>
          <div class="waterflow3 ms1 no3"></div>
          <div class="waterflow1 ms1 no4"></div>
          <div class="waterflow2 ms1 no5"></div>
          <div class="waterflow3 ms1 no6"></div>
          <div class="waterflow1 ms1 no7"></div>
          <div class="waterflow2 ms1 no8"></div>
          <div class="waterflow3 ms1 no9"></div>

          <div class="waterflow1 ms2 no1"></div>
          <div class="waterflow2 ms2 no2"></div>
          <div class="waterflow3 ms2 no3"></div>
          <!-- <div class="waterflow1 ms2 no4"></div>
        <div class="waterflow2 ms2 no5"></div>
        <div class="waterflow3 ms2 no6"></div>
        <div class="waterflow1 ms2 no7"></div>
        <div class="waterflow2 ms2 no8"></div>
        <div class="waterflow3 ms2 no9"></div>
        <div class="waterflow1 ms2 no10"></div>
        <div class="waterflow2 ms2 no11"></div>
        <div class="waterflow3 ms2 no12"></div> -->

          <div class="waterflow1 ms3 no1"></div>
          <div class="waterflow2 ms3 no2"></div>
          <div class="waterflow3 ms3 no3"></div>

          <div class="waterflow1 mfleft no1"></div>
          <div class="waterflow2 mfleft no2"></div>
          <div class="waterflow3 mfleft no3"></div>

          <div class="waterflow1 mfright no1"></div>
          <div class="waterflow2 mfright no2"></div>
          <div class="waterflow3 mfright no3"></div>

          <div class="waterflow1 water no1"></div>
          <div class="waterflow2 water no2"></div>
          <div class="waterflow3 water no3"></div>
          <div class="waterflow1 water no4"></div>
          <div class="waterflow2 water no5"></div>
          <div class="waterflow3 water no6"></div>
          <div class="waterflow1 water no7"></div>
          <div class="waterflow2 water no8"></div>
          <div class="waterflow3 water no9"></div>
          <!-- <div class="waterflow1 water no10"></div>
        <div class="waterflow2 water no11"></div>
        <div class="waterflow3 water no12"></div>
        <div class="waterflow1 water no13"></div>
        <div class="waterflow2 water no14"></div>
        <div class="waterflow3 water no15"></div> -->
        </div>
        <div class="waterwall_back_gosan"></div>
      </div>
      
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
    buildingUp() {
      this.$refs.popup.show();
    },
    popupHide() {
      this.$refs.popup.hide();
    }

  }
}
</script>

<style scoped>
/* .map-contents {
  position: relative;
  top: -160px;
  left: -232px;
  transform: scale(1.15, 1.25);
  transform-origin: top;
  margin: 0 auto;
} */

.map-contents {
  position: relative;
  top: 30px;
  left: 13px;
  transform: scale(0.90, 0.90);
  transform-origin: top;
  margin: 0 auto;
}

/* .waterwall_back_gosan {
  position: absolute;
  top: 106px;
  left: 378px;
  width: 1314px;
  height: 972px;
  background: url(@/assets/img/local_geumgang/gosan/gosan_mapframe.png) no-repeat;
  mix-blend-mode: color-dodge;
  background-size: 85% 85%;
} */

.waterwall_back_gosan {
  position: absolute;
  top: 0px;
  left: 0px;
  width: 2464px;
  height: 1386px;
  background: url(@/assets/img/local_geumgang/gosan/waterwall_gosan.png) no-repeat;
  background-size: 100% 100%;
}

.gosan_bg{
  position: absolute;
  top: -268px;
  left: -459px;
  width: 2464px;
  height: 1386px;
  background: url(@/assets/img/local_geumgang/gosan/gosan_bg.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
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
  height: 32%;
  position: absolute;
  float: left;
  top: 70%;
  left: 55%;
  display: none;
}

/* .waterflow1 {
  background-image: url(@/assets/img/water.png);
  position: absolute;
  width: 10px;
  height: 18px;
  background-size: 100% 100%;
}

.waterflow2 {
  background-image: url(@/assets/img/water2.png);
  position: absolute;
  width: 10px;
  height: 18px;
  background-size: 100% 100%;
}

.waterflow3 {
  background-image: url(@/assets/img/water3.png);
  position: absolute;
  width: 10px;
  height: 18px;
  background-size: 100% 100%;
} */

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

.waterflow1.fwleft,
.waterflow2.fwleft,
.waterflow3.fwleft {
  top: 540px;
  left: 818px;
  offset-path: path("M0.0 0 H 82");
  animation: waterflow 1.5S linear 0s infinite normal backwards;
}

.waterflow1.fwright,
.waterflow2.fwright,
.waterflow3.fwright {
  top: 544px;
  left: 1358px;
  offset-path: path("M0.0 0 H -110");
  animation: waterflow 2S linear 0s infinite normal backwards;
}

.waterflow1.gmleft,
.waterflow2.gmleft,
.waterflow3.gmleft {
  top: 342px;
  left: 1116px;
  offset-path: path("M0.0 0 H -78");
  animation: waterflow 1.2S linear 0s infinite normal backwards;
}

.waterflow1.gmright,
.waterflow2.gmright,
.waterflow3.gmright {
  top: 339px;
  left: 1168px;
  offset-path: path("M0.0 0 H 78");
  animation: waterflow 1.6S linear 0s infinite normal backwards;
}

.waterflow1.ms1,
.waterflow2.ms1,
.waterflow3.ms1 {
  top: 465px;
  left: 1034px;
  offset-path: path("M0.0 0 L 38 0 L 38 36 L 258 36 L 279 276 L 29 278 L 26 355 L -40 356");
  animation: waterflow 12S linear 0s infinite normal backwards;
}

.waterflow1.ms2,
.waterflow2.ms2,
.waterflow3.ms2 {
  top: 468px;
  left: 1216px;
  offset-path: path("M0.0 0 L -28 0 L -28 28");
  animation: waterflow 1S linear 0s infinite normal backwards;
}

.waterflow1.ms3,
.waterflow2.ms3,
.waterflow3.ms3 {
  top: 866px;
  left: 984px;
  offset-path: path("M0.0 0 H 104");
  animation: waterflow 1.4S linear 0s infinite normal backwards;
}

.waterflow1.mfleft,
.waterflow2.mfleft,
.waterflow3.mfleft {
  top: 464px;
  left: 739px;
  offset-path: path("M0.0 0 L -12 52");
  animation: waterflow 1S linear 0s infinite normal backwards;
}

.waterflow1.mfright,
.waterflow2.mfright,
.waterflow3.mfright {
  top: 462px;
  left: 1354px;
  offset-path: path("M0.0 0 L 5 59");
  animation: waterflow 1S linear 0s infinite normal backwards;
}

.waterflow1.water,
.waterflow2.water,
.waterflow3.water {
  top: 682px;
  left: 999px;
  offset-path: path("M0.0 0 L -2 32 L 641 32 L 693 346");
  animation: waterflow 10S linear 0s infinite normal backwards;
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

.waterflow1.fwleft.no1 {
  animation-delay: 0s;
}

.waterflow2.fwleft.no2 {
  animation-delay: 0.3s;
}

.waterflow3.fwleft.no3 {
  animation-delay: 0.6s;
}

.waterflow1.fwright.no1 {
  animation-delay: 0s;
}

.waterflow2.fwright.no2 {
  animation-delay: 0.25s;
}

.waterflow3.fwright.no3 {
  animation-delay: 0.5s;
}

.waterflow1.gmleft.no1 {
  animation-delay: 0s;
}

.waterflow2.gmleft.no2 {
  animation-delay: 0.25s;
}

.waterflow3.gmleft.no3 {
  animation-delay: 0.5s;
}

.waterflow1.gmright.no1 {
  animation-delay: 0s;
}

.waterflow2.gmright.no2 {
  animation-delay: 0.25s;
}

.waterflow3.gmright.no3 {
  animation-delay: 0.5s;
}

.waterflow1.ms2.no1 {
  animation-delay: 0s;
}

.waterflow2.ms2.no2 {
  animation-delay: 0.2s;
}

.waterflow3.ms2.no3 {
  animation-delay: 0.4s;
}

/* .waterflow1.ms2.no4 {
  animation-delay: 4.5s;
}

.waterflow2.ms2.no5 {
  animation-delay: 4.75s;
}

.waterflow3.ms2.no6 {
  animation-delay: 5.0s;
}

.waterflow1.ms2.no7 {
  animation-delay: 9.0s;
}

.waterflow2.ms2.no8 {
  animation-delay: 9.25s;
}

.waterflow3.ms2.no9 {
  animation-delay: 9.5s;
}

.waterflow1.ms2.no10 {
  animation-delay: 13.5s;
}

.waterflow2.ms2.no11 {
  animation-delay: 13.75s;
}

.waterflow3.ms2.no12 {
  animation-delay: 14.0s;
} */

.waterflow1.ms1.no1 {
  animation-delay: 0s;
}

.waterflow2.ms1.no2 {
  animation-delay: 0.2s;
}

.waterflow3.ms1.no3 {
  animation-delay: 0.4s;
}

.waterflow1.ms1.no4 {
  animation-delay: 4.0s;
}

.waterflow2.ms1.no5 {
  animation-delay: 4.2s;
}

.waterflow3.ms1.no6 {
  animation-delay: 4.4s;
}

.waterflow1.ms1.no7 {
  animation-delay: 8.0s;
}

.waterflow2.ms1.no8 {
  animation-delay: 8.2s;
}

.waterflow3.ms1.no9 {
  animation-delay: 8.4s;
}

.waterflow1.ms3.no1 {
  animation-delay: 0s;
}

.waterflow2.ms3.no2 {
  animation-delay: 0.2s;
}

.waterflow3.ms3.no3 {
  animation-delay: 0.4s;
}

.waterflow1.mfleft.no1 {
  animation-delay: 0s;
}

.waterflow2.mfleft.no2 {
  animation-delay: 0.35s;
}

.waterflow3.mfleft.no3 {
  animation-delay: 0.7s;
}

.waterflow1.mfright.no1 {
  animation-delay: 0s;
}

.waterflow2.mfright.no2 {
  animation-delay: 0.35s;
}

.waterflow3.mfright.no3 {
  animation-delay: 0.7s;
}

.waterflow1.water.no1 {
  animation-delay: 0s;
}

.waterflow2.water.no2 {
  animation-delay: 0.15s;
}

.waterflow3.water.no3 {
  animation-delay: 0.3s;
}

.waterflow1.water.no4 {
  animation-delay: 3.3s;
}

.waterflow2.water.no5 {
  animation-delay: 3.45s;
}

.waterflow3.water.no6 {
  animation-delay: 3.6s;
}

.waterflow1.water.no7 {
  animation-delay: 6.6s;
}

.waterflow2.water.no8 {
  animation-delay: 6.75s;
}

.waterflow3.water.no9 {
  animation-delay: 6.9s;
}

/* .waterflow1.water.no10 {
  animation-delay: 11.2s;
}

.waterflow2.water.no11 {
  animation-delay: 11.4s;
}

.waterflow3.water.no12 {
  animation-delay: 11.6s;
}
.waterflow1.water.no13 {
  animation-delay: 15.2s;
}
.waterflow2.water.no14 {
  animation-delay: 15.4s;
}
.waterflow3.water.no15 {
  animation-delay: 15.6s;
} */
</style>