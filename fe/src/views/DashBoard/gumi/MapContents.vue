<template>
  <b-col class="position-relative" style="z-index: 0;">
    <div class="map-contents" style="height: 550px; width: 100%;">
      <div class="waterwall_back_gumi">
        <!-- 착수정 (왼쪽) -->
        <main-cube-text :style="{ top: '269px', left: '605px', opacity: '50%' }" :txtStyle="{ top: '-20px', left: '-30px'}"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_get_left.png')"/>
        <main-cube v-if="percentData.착수동 >= 0" :style="{ top: '158px', left: '662px' }" :cubeVal="percentData.착수동" />
        <!-- 착수정 -->

        <!-- 약품투입동(생활) -->
        <main-cube-text @mouseover="popupShow('약품투입동(생활)')" @mouseout="popupHide()" ref="cubeText"
          :style="{ top: '318px', left: '582px' }" @click="this.$refs.cubeText.goFac('약품투입동(생활)')"
          :txtStyle="{ top: '-25px', left: '-146px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_chemical_left.png')" cubeText="약품투입동(생활)" />
        <main-cube v-if="percentData['약품투입동(생활)'] >= 0" :style="{ top: '200px', left: '624px' }"
          :cubeVal="percentData['약품투입동(생활)']" />
        <!-- 약품투입동(생활) -->

        <!-- 혼화 & 응집 (왼쪽)-->
        <main-cube-text :style="{ top: '338px', left: '322px', opacity: '50%' }" :txtStyle="{ top: '84px', left: '20px' }"
          :txtSubStyle="{ top: '84px', left: '180px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_mixsink_left.png')" />
        <main-cube v-if="percentData['혼화/응집동'] >= 0" :style="{ top: '283px', left: '457px' }"
          :cubeVal="percentData['혼화/응집동']" />
        <!-- 혼화 & 응집 -->

        <!-- 응집침전지(생활) 왼쪽 첫번째 침전 -->
        <!-- <main-cube v-if="percentData.응집침전지 >= 0" :style="{ top: '172px', left: '236px' }" :cubeVal="percentData.응집침전지" /> -->
        <!-- // 응집침전지(생활) 왼쪽 첫번째 침전 -->

        <!-- 생활여과지 -->
        <main-cube-text @mouseover="popupShow('여과지(생활)')" @mouseout="popupHide()" ref="cubeText"
          @click="this.$refs.cubeText.goFac('여과지(생활)')" :style="{ top: '512px', left: '400px' }"
          :txtStyle="{ top: '16px', left: '32px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_filter_left.png')" cubeText="여과지(생활)" />
        <main-cube v-if="percentData['여과지(생활)'] >= 0" :style="{ top: '420px', left: '522px' }"
          :cubeVal="percentData['여과지(생활)']" />
        <!-- 생활여과지 -->

        <!-- 역세펌프동(생활) -->
        <main-cube-text @mouseover="popupShow('역세펌프동(생활)')" @mouseout="popupHide()" ref="cubeText"
          @click="this.$refs.cubeText.goFac('역세펌프동(생활)')" :style="{ top: '450px', left: '721px' }"
          :txtStyle="{ top: '-40px', left: '-2px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/life.png')" cubeText="역세펌프동(생활)" />
        <main-cube v-if="percentData['역세펌프동(생활)'] >= 0" :style="{ top: '333px', left: '793px' }"
          :cubeVal="percentData['역세펌프동(생활)']" />
        <!-- 역세펌프동(생활) -->

        <!-- 관리본관 -->
        <main-cube-text @mouseover="popupShow('관리본관')" @mouseout="popupHide()" ref="cubeText"
          @click="this.$refs.cubeText.goFac('관리본관')" :style="{ top: '591px', left: '565px', opacity: '50%'}"
          :txtStyle="{ top: '18px', left: '184px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/management.png')"/>
        <main-cube v-if="percentData.관리본관 >= 0" :style="{ top: '490px', left: '752px' }" :cubeVal="percentData.관리본관" />
        <!-- 관리본부 -->

        <!-- 착수정2 (오른쪽)-->
        <main-cube-text :style="{ top: '288px', left: '1197px', opacity: '50%' }" :txtStyle="{ top: '-15px', left: '-26px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_get_right.png')"/>
        <main-cube v-if="percentData.착수동 >= 0" :style="{ top: '208px', left: '1263px' }" :cubeVal="percentData.착수동" />
        <!-- //착수정2 -->

        <!-- 공업약품동 -->
        <main-cube-text @mouseover="popupShow('약품투입동(공업)')" @mouseout="popupHide()" ref="cubeText"
          :style="{ top: '311px', left: '1371px' }" @click="this.$refs.cubeText.goFac('약품투입동(공업)')"
          :txtStyle="{ top: '-23px', left: '56px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_chemical_right.png')" cubeText="약품투입동(공업)" />
        <main-cube v-if="percentData['약품투입동(공업)'] >= 0" :style="{ top: '208px', left: '1410px' }"
          :cubeVal="percentData['약품투입동(공업)']" />
        <!-- 공업약품동 -->

        <!-- 혼화 & 응집2 (오른쪽)-->
        <main-cube-text :style="{ top: '353px', left: '1179px', opacity: '50%' }" :txtStyle="{ top: '76px', left: '34px' }"
          :txtSubStyle="{ top: '76px', left: '236px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_mixsink_right.png')" />
        <main-cube v-if="percentData['혼화/응집동'] >= 0" :style="{ top: '296px', left: '1356px' }"
          :cubeVal="percentData['혼화/응집동']" />
        <!-- //혼화 & 응집2 -->

        <!-- 응집침전지 (공업) (중간 침전) -->
        <!-- <main-cube v-if="percentData.응집침전지 >= 0" :style="{ top: '160px', left: '898px' }" :cubeVal="percentData.응집침전지" /> -->
        <!-- //응집침전지 (공업) (중간 침전) -->

        <!-- 2차 침전지 -->
        <main-cube-text :style="{ top: '306px', left: '1630px', opacity: '50%' }" :txtStyle="{ top: '-26px', left: '-4px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_sink.png')"/>
        <main-cube v-if="percentData.응집침전지 >= 0" :style="{ top: '208px', left: '1727px' }" :cubeVal="percentData.침전지동" />
        <!--  2차 침전지 -->

        <!-- 송수펌프동(공업) -->
        <main-cube-text @mouseover="popupShow('송수펌프동(공업)')" @mouseout="popupHide()" ref="cubeText"
          @click="this.$refs.cubeText.goFac('송수펌프동(공업)')" :style="{ top: '390px', left: '1803px' }"
          :txtStyle="{ top: '69px', left: '-108px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_water_right.png')" cubeText="송수펌프동(공업)" />
        <main-cube v-if="percentData['송수펌프동(공업)'] >= 0" :style="{ top: '306px', left: '1869px' }"
          :cubeVal="percentData['송수펌프동(공업)']" />
        <!-- 송수펌프동(공업) -->

        <!-- 탈수기동 -->
        <main-cube-text @mouseover="popupShow('탈수기동')" @mouseout="popupHide()" ref="cubeText"
          @click="this.$refs.cubeText.goFac('탈수기동')" :style="{ top: '362px', right: '170px' }"
          :txtStyle="{ top: '5px', left: '-20px' }"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_circlearea.png')" cubeText="탈수기동" />
        <main-cube v-if="percentData.탈수기동 >= 0" :style="{ top: '247px', left: '2033px' }" :cubeVal="percentData.탈수기동" />
        <!-- 탈수기동 -->

        <!-- 차염투입동 -->
        <main-cube-text :style="{ top: '548px', left: '1071px', opacity: '50%' }" :txtStyle="{ top: '-18px', left: '-123px' }"
         :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_disinfection.png')" />
        <main-cube v-if="percentData.차염투입동 >= 0" :style="{ top: '436px', left: '1120px' }" :cubeVal="percentData.차염투입동" />
        <!-- //차염투입동 -->

        <!-- 오존투입동 -->
        <main-cube-text @mouseover="popupShow('오존투입동')" @mouseout="popupHide()" ref="cubeText"
          @click="this.$refs.cubeText.goFac('오존투입동')" :style="{ top: '614px', left: '1033px' }"
          :txtStyle="{ top: '-26px', left: '-105px' }" cubeText="오존투입동"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_ozon.png')" />
        <main-cube v-if="percentData.오존투입동 >= 0" :style="{ top: '511px', left: '1078px' }"
          :cubeVal="percentData.오존투입동" />
        <!-- 오존투입동 -->

        <!-- 활성탄여과지 -->
        <main-cube-text  ref="cubeText" :style="{ top: '671px', left: '1015px', opacity: '50%'}"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_GACfilter.png')" />
        <main-cube v-if="percentData.활성탄여과지동 >= 0" :style="{ top: '614px', left: '1105px' }"
          :cubeVal="percentData.활성탄여과지동" />
        <!-- //활성탄여과지 -->

        <!-- 여과지(4단지) -->
        <main-cube-text @mouseover="popupShow('여과지(4단지)')" @mouseout="popupHide()" ref="cubeText"
          :style="{ top: '534px', left: '1206px' }" @click="this.$refs.cubeText.goFac('여과지(4단지)')"
          :txtStyle="{ top: '22px', left: '-2px' }" cubeText="여과지(4단지)"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_filter_right.png')" />
        <main-cube v-if="percentData['여과지(4단지)'] >= 0" :style="{ top: '440px', left: '1272px' }"
          :cubeVal="percentData['여과지(4단지)']" />
        <!-- //여과지(4단지) -->

        <!-- 송수펌프동(4단지) -->
        <main-cube-text @mouseover="popupShow('송수펌프동(4단지)')" @mouseout="popupHide()" ref="cubeText"
          @click="this.$refs.cubeText.goFac('송수펌프동(4단지)')" :style="{ top: '641px', left: '1221px' }"
          :txtStyle="{ top: '54px', left: '26px' }" cubeText="송수펌프동(4단지)"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_water_left.png')" />
        <main-cube v-if="percentData['송수펌프동(4단지)'] >= 0" :style="{ top: '531px', left: '1388px' }"
          :cubeVal="percentData['송수펌프동(4단지)']" />
        <!-- //송수펌프동(4단지) -->

        <!-- 통합송수동 -->
        <main-cube-text @mouseover="popupShow('송수펌프동(통합)')" @mouseout="popupHide()" ref="cubeText"
          @click="this.$refs.cubeText.goFac('송수펌프동(통합)')" :style="{ top: '529px', left: '1637px'}"
          :txtStyle="{ top: '80px', left: '-106px' }" cubeText="송수펌프동(통합)"
          :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_water_center.png')" />
        <main-cube v-if="percentData['송수펌프동(통합)'] >= 0" :style="{ top: '500px', left: '1730px' }"
          :cubeVal="percentData['송수펌프동(통합)']" />
        <!-- //통합송수동 -->

        <!-- <div class="waterwall_back_gumi"></div> -->
      </div>
      <!-- <HoverPopup ref="popup" :hoverVal="hoverVal"/> -->
      <div class="gumi_bg"></div>
    </div>
    <!-- hover 될 때 표시될 화면 -->
    <HoverPopup ref="popup" :hoverVal="hoverVal" />
    <!-- //hover 될 때 표시될 화면 -->
  </b-col>
</template>

<script>
import { fetchFunc } from '@/util/fetchFunc'
import HoverPopup from '@/views/DashBoard/DashBoard/HoverPopup.vue'
import MainCube from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCube.vue'
import MainCubeText from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCubeText.vue'
export default {
  components: { MainCube, MainCubeText, HoverPopup }
  , data() {
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

<style>
/* 수정 주의!! 구미 map-contents 변경시 전 정수장 반영됨 */
/* .map-contents {
  position: relative;
  top: 0;
  left: 0;
  margin: 0 auto;
  width: 1920px;
  height: 1080px;
} */
/* .map-contents {
  position: relative;
  top: -120px;
  left: -70px;
  margin: 0 auto;
  width: 1920px;
  height: 500px;
} */
.map-contents {
  position: relative;
  top: 0px;
  left: 0px;
  margin: 0 auto;
}

.map-contents__chimjeonji .aurora_chimjeonji {
  pointer-events: none;
  top: -33px;
  left: 46px;
  -webkit-animation: blink-data-v-d79beb4e 3s infinite alternate;
  animation: blink-data-v-d79beb4e 3s infinite alternate;
}

/* .gumi_bg{
  position: absolute;
  top: -518px;
  left: -450px;
  width: 2260px;
  height: 1271px;
  background: url(@/assets/img/local_nakdong/gumi/gumi_bg.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  transform-origin: 50% 50%;
  transform: scale(0.98, 0.98);
} */
.gumi_bg{
  position: absolute;
  top: -246px;
  left: -341px;
  width: 2260px;
  height: 1271px;
  background: url(@/assets/img/local_nakdong/gumi/gumi_bg.png) no-repeat;
  z-index: -1;
}

/* .waterwall_back_gumi{
  position: absolute;
  top: 0px;
  left: 0px;
  width: 2260px;
  height: 1271px;
  background: url(@/assets/img/local_nakdong/gumi/waterwall_gumi.png) no-repeat;
} */
.waterwall_back_gumi{
  position: absolute;
  top: -246px;
  left: -341px;
  width: 2260px;
  height: 1271px;
  background: url(@/assets/img/local_nakdong/gumi/waterwall_gumi.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  transform-origin: 50% 50%;
  transform: scale(1);
}

.cube {
  z-index: 5;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  width: 80px;
  height: 80px;
  -webkit-animation: updown-data-v-d79beb4e 2s ease-in-out 0s infinite alternate;
  animation: updown-data-v-d79beb4e 2s ease-in-out 0s infinite alternate;
}

.cube-ani-stop {
  -webkit-animation: none !important;
  animation: none !important;
}

.cube__inner {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url(@/assets/img/cube__inner.png);
}

.cube__noimg {
  width: 80px;
  height: 80px;
  -webkit-transform-style: preserve-3d;
  -webkit-transform: rotateX(0) rotateY(0) rotateZ(0);
  transform-style: preserve-3d;
  transform: rotateX(0) rotateY(0) rotateZ(0);
}

.cube__front_logo {
  width: 80px;
  height: 80px;
  /* background-image: url(/img/cube_ai_icon.721ecad2.png); */
  background-position: center;
  background-size: cover;
  position: absolute;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cube__back_logo {
  width: 80px;
  height: 80px;
  background-position: center;
  position: absolute;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  transform: rotateY(180deg);
  -webkit-transform: rotateY(180deg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.main_per_font {
  font-family: LABDigital !important;
  font-size: 20px;
  color: #c3eaff;
  letter-spacing: 1px;
  line-height: 111px;
}

.main_per_unit {
  font-family: LABDigital !important;
  font-size: 22px;
  color: #c3eaff;
  letter-spacing: 1px;
  line-height: 106px;
}


.main_info_up {
  -webkit-animation: up 0.5s linear;
  -moz-animation: up 0.5s linear;
  animation: up 0.5s linear;
}

.main_info_down {
  -webkit-animation: down 0.5s forwards;
  -moz-animation: down 0.5s forwards;
  animation: down 0.5s forwards;
}

.div_small {
  height: 100%;
  display: flex;
  align-items: center;
  text-align: center;
  flex-direction: column;
}

.dash_border_img {
  background: url(@/assets/img/00_table_bg.png) no-repeat;
  background-position: center;
  background-size: 100% 110%;
}

.fL {
  float: left;
}

.fR {
  float: right;
}

.elec_use_unit_font {
  font-family: KHNPHDRegular;
  font-size: 14px;
  color: #fff;
  margin-right: 20px;
}

.bottom_fac_font_num {
  font-family: 'LABDigital' !important;
  font-size: 17px;
  color: #c3eaff;
  letter-spacing: 4px;
  line-height: 76px;
}

.bottom_fac_font_unit {
  font-family: KHNPHDRegular;
  font-size: 13px;
  color: #fff !important;
  line-height: 90px;
}

.bottom_all4 {
  width: 87%;
  height: 49%;
  font-size: 15px;
  font-family: 'KHNPHDRegular';
  letter-spacing: normal;
  color: #c3eaff;
}

.bottom_all3_1 {
  height: 43%;
  text-align: left;
  margin: 10px 5px;
}

.chart_bar_base {
  position: absolute;
  background: url(@/assets/img/percent_bar_bg.png);
  background-size: 100% 100%;
  width: 100%;
  height: 100%;
  z-index: 4;
}

.chart_bar {
  position: absolute;
  background: url(@/assets/img/percent_bar.png);
  background-size: 21% 100%;
  width: 100%;
  height: 100%;
  z-index: 5;
  background-repeat: no-repeat;
  transition: all linear .3s;
}

/* .hoverInfo {
  width: 32%;
  height: 60%;
  position: absolute;
  float: left;
  top: 109%;
  left: 18%;
  display: none;
  animation: move-up-building 1s ease-in-out 0s normal backwards;
} */
.hoverInfo {
  width: 30%;
  height: 58%;
  position: absolute;
  float: left;
  top: 97%;
  left: 21.5%;
  display: none;
  animation: move-up-building 1s ease-in-out 0s normal backwards;
  z-index: 2;
}

.hoverInfoNone {
  position: absolute;
  /* 박스를 아래로 내리도록 조정 */
  right: 0;
  width: 30%;
  animation: move-down-popup 1s ease-in-out 0s normal forwards;
  /* 새로운 애니메이션 적용 */
}
</style>