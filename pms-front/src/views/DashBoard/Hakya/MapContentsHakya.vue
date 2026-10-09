<template>
    <div>
       
        <!-- 3D MAP 영역 -->
          <!-- 학야 정수장 메인 -->
            <div class="map-contents" :style="{ width: '1550px', height: 'calc(100vh-118px)' }">
              <div>
  
                <!-- 혼화 & 응집 -->
                    <MainCubeText :style="{ top: '65px', left: '-6px'}"
                    :txtStyle="{ top: '93px', left: '537px' }" cubeText="혼화응집지" 
                    :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_mixsink.png')" :hakya="hakya"/>
                    <!-- <MainCube :style="{ top: '324px', left: '496px'}" nameText="혼화기"/>
                    <MainCube :style="{ top: '232px', left: '746px'}" nameText="슬러지 수집기"/> -->
                <!-- //혼화 & 응집 -->
  
                <!-- 착수 -->
                    <MainCubeText :style="{ top: '373px', left: '-66px'}"
                    :txtStyle="{ top: '34px', left: '0px' }" 
                    :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_get.png')" :hakya="hakya"/>
                    <!-- <MainCube :style="{ top: '452px', left: '122px'}" nameText="유입 V"/> -->
                <!-- //착수 -->
  
                <!-- 약품투입동 -->
                    <MainCubeText :style="{ top: '391px', left: '161px'}"
                    :txtStyle="{ top: '75px', left: '58px' }" cubeText="약품투입동" 
                    :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_chemical.png')" :hakya="hakya"/>
                <!-- //약품투입동 -->
  
                <!-- 차염투입동 -->
                    <MainCubeText :style="{ top: '532px', left: '554px'}"
                    :txtStyle="{ top: '54px', left: '55px' }" cubeText="차염투입동" 
                    :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_disinfection.png')" :hakya="hakya"/>
                    <!-- <MainCube :style="{ top: '626px', left: '790px'}" nameText="차염 발생기"/> -->
                <!-- //차염투입동 -->
  
                <!-- 여과지동 -->
                    <MainCubeText :style="{ top: '-74px', left: '745px'}"
                    :txtStyle="{ top: '76px', left: '161px' }" cubeText="여과지동" 
                    :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_filter.png')" :hakya="hakya"/>
                    <!-- <MainCube :style="{ top: '46px', left: '1088px'}" nameText="역세 P"/>  -->
                <!-- //여과지동 -->
  
                <!-- 송수 -->
                    <MainCubeText :style="{ top: '158px', left: '1130px'}"
                    :txtStyle="{ top: '32px', left: '-1px' }" 
                    :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_water.png')" :hakya="hakya"/>
                    <!-- <img src="../../../assets/img/local_nakdong/hakya/building/hakyawater_up.png" style="top: 326px; left: 1270px; position: absolute;" class="building-visible up"> -->
                    <!-- <MainCube :style="{ top: '229px', left: '1304px'}" nameText="펌프 모터"/> -->
                <!-- //송수 -->

                  <!-- 배출수지 -->
                  <MainCubeText :style="{ top: '94px', left: '1283px'}"
                  :txtStyle="{ top: '32px', left: '-1px' }" cubeText="배출수지" 
                  :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_water.png')" :hakya="hakya"/>
                  <!-- <img src="../../../assets/img/local_nakdong/hakya/building/hakyawater_up.png" style="top: 326px; left: 1270px; position: absolute;" class="building-visible up"> -->
                  <!-- <MainCube :style="{ top: '229px', left: '1304px'}" nameText="펌프 모터"/> -->
                <!-- //배출수지 -->

                <!-- 가압장 -->
                    <MainCubeText :style="{ top: '406px', left: '890px'}" @popupShow="popupShow"
                    @popupHide="popupHide" @click="this.$router.push('/PumpControl')" :txtStyle="{ top: '74px', left: '61px' }"
                    cubeText="가압장"  :backImg="require('@/assets/img/local_nakdong/hakya/building/hak_chemical.png')"
                    :hoverImg="require('@/assets/img/local_nakdong/hakya/building/hakyachemical_up.png')" />
                    <MainCube :style="{ top: '353px', left: '982px'}" :nameText="nameText"/>
                <!-- //가압장 -->
                
                <div class="waterflow1 flow1 no1"></div>
                <div class="waterflow2 flow1 no2"></div>
                <div class="waterflow3 flow1 no3"></div>

                <div class="waterflow1 flow2 no1"></div>
                <div class="waterflow2 flow2 no2"></div>
                <div class="waterflow3 flow2 no3"></div>

                <div class="waterflow1 flow3 no1"></div>
                <div class="waterflow2 flow3 no2"></div>
                <div class="waterflow3 flow3 no3"></div>

                <div class="waterwall_back_hakya"></div>         

              </div>
            </div>
          <!-- //학야 정수장 메인 -->
        <!-- //3D MAP 영역 -->
        <HoverPopup ref="popup" :hoverVal="nameText" :alarmHoverGrpList="alarmOldList" @songsuList="songsuList" />
        <!--
        <MainCube/>
        <MainCubeText/> -->
    </div>
  </template>
  
  <script>
  import HoverPopup from '@/views/DashBoard/DashBoard/HoverPopup.vue'
  import MainCube from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCube.vue'
  import MainCubeText from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCubeText.vue'
// import src from '@vueform/multiselect';
//   import Percentage from '@/views/DashBoard/DashBoard/IconPopup.vue'

  // import 'vue3-carousel/dist/carousel.css'
  // import { fetchFunc } from '@/util/fetchFunc';
  export default {
    components: {
      HoverPopup,
      MainCube,
      MainCubeText,
    //   Percentage
    },
    data() {
      return {
        hakya : true,
        hoverVal: {
          title: "활성탄흡착지동",
          mainValue: 400
        },
        grpList: '',
        nameText : [],
        alarmOldList : []
      }
    },
    mounted() {
      this.initPopupHide();
    },
    methods: {
      async popupShow() {
        this.$refs.popup.show();
      },
      popupHide() {
        this.$refs.popup.hide();
      },
      initPopupHide() {
        this.$refs.popup.initHide();
      },
    songsuList(grpList,alarmGrpList) {
         this.nameText = grpList[0]
         this.alarmOldList = alarmGrpList[0]
      }
  
    }
  }
  </script>
  
  <style>

  /* .waterwall_back_hakya {
    position: absolute;
    top: -200px;
    left: -100px;
    width: 2706px;
    height: 817px;
    background: url(@/assets/img/local_nakdong/hakya/waterwall_hakya.png) no-repeat;
    background-size: 100% 100%;
    background-position: 30% 83%;
  } */

  .waterwall_back_hakya {
  position: absolute;
  top: -197px;
  left: -182px;
  width: 2763px;
  height: 893px;
  background: url(@/assets/img/local_nakdong/hakya/hakya_mapframe.png) no-repeat;
  background-size: 100%;
  opacity: 40%;
}

.building-visible {
  display: block !important;
}
.building-unvisible{
  display: none !important;
}
 

.waterflow1 {
  background-image: url(@/assets/img/water.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.5, 1.2);
}

.waterflow2 {
  background-image: url(@/assets/img/water2.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.5, 1.2);
}

.waterflow3 {
  background-image: url(@/assets/img/water3.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.5, 1.2);
}

.waterflow1.flow1,
.waterflow2.flow1,
.waterflow3.flow1{
  top: 635px;
  left: -152px;
  offset-path: path("M0.0 0 L 196 -94 L 66 -133 L 128 -163");
  animation: waterflow 3.6S linear 0s infinite normal backwards;
}

.waterflow1.flow2,
.waterflow2.flow2,
.waterflow3.flow2{
  top: 427px;
  left: 84px;
  offset-path: path("M0.0 0 L 188 -78");
  animation: waterflow 2.2S linear 0s infinite normal backwards;
}

.waterflow1.flow3,
.waterflow2.flow3,
.waterflow3.flow3{
  top: 129px;
  left: 763px;
  offset-path: path("M0.0 0 L 107 -44");
  animation: waterflow 1.5S linear 0s infinite normal backwards;
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
  animation-delay: 0.12s;
}
.waterflow3.flow1.no3 {
  animation-delay: 0.24s;
}

.waterflow1.flow2.no1 {
  animation-delay: 0s;
}
.waterflow2.flow2.no2 {
  animation-delay: 0.15s;
}
.waterflow3.flow2.no3 {
  animation-delay: 0.3s;
}

.waterflow1.flow3.no1 {
  animation-delay: 0s;
}
.waterflow2.flow3.no2 {
  animation-delay: 0.18s;
}
.waterflow3.flow3.no3 {
  animation-delay: 0.36s;
}
  
</style>