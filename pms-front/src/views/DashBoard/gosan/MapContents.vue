<template>
  <!-- 고산 정수장 메인 -->
  <b-col class="position-relative">
    <div class="map-contents" :style="{ height: 'calc(100vh - 118px)' }">

      <div class="waterwall_back_gosan">

         <!-- 혼화/응집 & 침전-->
      <!-- <MainCubeText :style="{ top: '41px', left: '98px' }"
        :txtStyle="{ top: '90px', left: '37px' }" cubeText="혼화/응집" :txtSubStyle="{ top: '90px', left: '218px' }"
        cubeSubText="침전" :backImg="require('@/assets/img/local_geumgang/gosan/building/go_mixsink_left.png')" /> -->
      <!-- <MainCube :style="{top: '63px', left: '315px'}" :cubeVal="0"/> -->
      <!-- <MainCube :style="{top: '135px', left: '433px'}" :cubeVal="0"/> -->
      <!-- //혼화/응집 & 침전 -->

      <!-- 착수 -->
      <!-- <MainCubeText :style="{ top: '36px', left: '561px' }"
        :txtStyle="{ top: '13px', left: '-50px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_get.png')" cubeText="착수" /> -->
      <!-- <MainCube :style="{top: '54px', left: '711px'}" :cubeVal="0"/> -->
      <!-- //착수 -->

      <!-- 약품투입동 -->
      <div>
        <MainCubeText :style="{ top: '115px', left: '522px' }"
          :txtStyle="{ top: '12px', left: '-15px' }"
          :backImg="require('@/assets/img/local_geumgang/gosan/building/go_chemical.png')" cubeText="약품투입동" />
        <!-- <MainCube :style="{ top: '120px', left: '650px' }" :cubeVal="0" /> -->
      </div>
      <!-- //약품투입동 -->

      <!-- 차염투입동 -->
      <MainCubeText :style="{ top: '190px', left: '554px' }"
        :txtStyle="{ top: '5px', left: '-43px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_disinfection.png')" cubeText="차염투입동" />
      <!-- <MainCube :style="{top: '179px', left: '719px'}" :cubeVal="0"/> -->
      <!-- //차염투입동 -->

      <!-- 혼화/응집 & 침전(오른쪽) -->
      <!-- <MainCubeText :style="{ top: '42px', left: '677px' }"
        :txtStyle="{ top: '90px', left: '34px' }" cubeText="혼화/응집" :txtSubStyle="{ top: '90px', left: '204px' }"
        cubeSubText="침전" :backImg="require('@/assets/img/local_geumgang/gosan/building/go_mixsink_right.png')" /> -->
      <!-- <MainCube :style="{top: '63px', left: '924px'}" :cubeVal="0"/> -->
      <!-- <MainCube :style="{top: '135px', left: '1045px'}" :cubeVal="0"/> -->
      <!-- //혼화/응집 & 침전(오른쪽) -->

      <!-- 여과지 -->
      <!-- <MainCubeText :style="{ top: '239px', left: '39px' }"
        :txtStyle="{ top: '70px', left: '41px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_filter_left.png')" cubeText="여과지" /> -->
      <!-- <MainCube :style="{top: '289px', left: '280px'}" :cubeVal="0"/> -->
      <!-- //여과지 -->

      <!-- 송수펌프동(구) -->
      <MainCubeText :style="{ top: '348px', left: '316px' }" @popupShow="popupShow('oldList')"
        @popupHide="popupHide" @click="this.$router.push('/PumpControl')" :txtStyle="{ top: '8px', left: '132px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_water.png')"
        :hoverImg="require('@/assets/img/local_geumgang/gosan/building/gosan_up.png')" cubeText="송수펌프동(구)" />
      <!-- <img src="@/assets/img/local_geumgang/gosan/building/gosan_up.png" :style="{ top: '320px', left: '449px', width: '410px' }" :class="waterClass"> -->
      <MainCube :nameText="oldList" :style="{top: '257px', left: '600px'}" />
      <!-- //송수펌프동(구) --> 
      

      <!-- 여과지(오른쪽) -->
      <!-- <MainCubeText :style="{ top: '238px', left: '798px' }"
        :txtStyle="{ top: '70px', left: '30px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/go_filter_right.png')" cubeText="여과지" /> -->
      <!-- <MainCube :style="{top: '289px', left: '972px'}" :cubeVal="0"/> -->
      <!-- //여과지(오른쪽) -->

      <!-- 관리본부 -->
      <!-- <MainCubeText :style="{ top: '262px', left: '1025px'}"
        :txtStyle="{ top: '46px', left: '10px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/management.png')" cubeText="관리본부" />  -->
        <!-- <MainCube :style="{top: '455px', left: '469px'}" :cubeVal="0"/> -->
      <!-- //관리본부 -->

      <!-- 농축조 -->
      <!-- <MainCubeText :style="{ top: '521px', left: '159px' }"
        :txtStyle="{ top: '74px', left: '30px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/san_circles_area.png')" cubeText="농축조" /> -->
      <!-- <MainCube :style="{top: '455px', left: '469px'}" :cubeVal="0"/> -->
      <!-- //농축조 -->

      <!-- 탈수기동 -->
      <MainCubeText :style="{ top: '731px', left: '219px' }"
        :txtStyle="{ top: '50px', left: '8px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/san_large_building.png')" cubeText="탈수기동" />
      <!-- <MainCube :style="{top: '612px', left: '469px'}" :cubeVal="0"/> -->
      <!-- //탈수기동 -->

      <!-- 회수조 -->
      <MainCubeText :style="{ top: '521px', left: '542px' }"
        :txtStyle="{ top: '52px', left: '51px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/san_center_building.png')" cubeText="회수조" />
      <!-- <MainCube :style="{top: '485px', left: '746px'}" :cubeVal="0"/> -->
      <!-- //회수조 -->

      <!-- 송수펌프동(신) -->
      <MainCubeText :style="{ top: '643px', left: '1032px' }"  @popupShow="popupShow('newList')"
      @popupHide="popupHide" @click="this.$router.push('/PumpControl')"
        :txtStyle="{ top: '44px', left: '-44px' }"
        :backImg="require('@/assets/img/local_geumgang/gosan/building/san_small_building.png')" cubeText="송수펌프동(신)" />
      <MainCube :nameText="newList" :style="{top: '558px', left: '1015px'}" />
      <!-- //송수펌프동(신) -->

      </div>
     
      <!-- <div class="waterwall_back_gosan"></div> -->
    </div>
    <HoverPopup ref="popup" :hoverVal="grpList" :alarmHoverGrpList="alarmGrpList"  @songsuList="songsuList" />
  </b-col>
  <!-- //고산 정수장 메인 -->
</template>
<script>
import HoverPopup from '@/views/DashBoard/DashBoard/HoverPopup.vue'
import MainCube from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCube.vue'
import MainCubeText from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCubeText.vue'
// import 'vue3-carousel/dist/carousel.css'
// import { fetchFunc } from '@/util/fetchFunc';
export default {
  components: {
    HoverPopup,
    MainCube,
    MainCubeText
  },
  data() {
    return {
      currentImageSrc: require('@/assets/img/local_geumgang/gosan/building/go_water.png'),
      waterClass: 'basicImg',
      buildClass: '',
      grpList: [],
      oldList : [],
      newList : [],
      alarmOldList : [],
      alarmNewList : []
    }
  },
  mounted() {
    this.initPopupHide();
  },
  methods: {
    popupShow(item) {
      if(item == 'oldList'){
        this.grpList = this.oldList
        this.alarmGrpList = this.alarmOldList
      }else {
        this.grpList = this.newList
        this.alarmGrpList = this.alarmNewList
      }
      this.$refs.popup.show();
    },
    popupHide() {
      this.$refs.popup.hide();
    },
    initPopupHide() {
      this.$refs.popup.initHide();
    },
    songsuList(grpList, alarmGrpList) {
      this.oldList = grpList[0]
      this.newList = grpList[1]
      this.alarmOldList = alarmGrpList[0]
      this.alarmNewList = alarmGrpList[1]
      // this.grpList = grpList
    }

  }
}
</script>
<style scoped>
.basicImg {
  top: 320px;
  left: 449px;
  width: 410px;
}

.map-contents {
  position: relative;
  top: 30px;
  left: 0px;
  transform: scale(0.90, 0.90);
  transform-origin: top;
  margin: 0 auto;
}

/* .waterwall_back_gosan {
  position: absolute;
  top: 143px;
  left: 0;
  width: 1590px;
  height: 690px;
  background: url(@/assets/img/local_geumgang/gosan/waterwall_gosan.png) no-repeat;
  background-size: 67% 97%;
  background-position: 56% 83%;
} */

.waterwall_back_gosan{
  position: absolute;
  top: -15px;
  left: 100px;
  width: 1314px;
  height: 972px;
  background: url(@/assets/img/local_geumgang/gosan/gosan_mapframe.png) no-repeat;
  background-size: 100% 100%;
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


.building-visible {
  display: block !important;
}

.building-unvisible {
  display: none !important;
}

.up img {
  position: absolute;
  animation: building-up 1s ease-in-out 0s normal forwards;
}

@keyframes building-up {
  from {
    transform: translateY(0px)
  }

  to {
    transform: translateY(-30px)
  }
}

.buildNone img {
  animation: move-down-building 1s ease-in-out 0s normal forwards;
  /* 새로운 애니메이션 적용 */
}

@keyframes move-down-building {
  from {
    transform: translateY(-30px)
  }

  to {
    transform: translateY(0px)
  }
}
</style>