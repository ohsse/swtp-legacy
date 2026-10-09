<template>
   <!-- 구미 정수장 메인 -->
   <b-col class="position-relative">
      <div class="map-contents">

         <div class="waterwall_back_gumi">

            <!-- 착수정(좌측) -->
         <!-- <main-cube-text :style="{ top: '40px', left: '346px' }"
            :txtStyle="{ top: '-20px', left: '-30px' }"
            :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_get_left.png')"  /> -->
         <!-- 착수정(좌측) -->

         <!-- 약품투입동(생활) -->
         <main-cube-text :style="{ top: '92px', left: '324px' }"
            :txtStyle="{ top: '-4px', left: '-140px' }" :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_chemical_left.png')" cubeText="약품투입동(생활)" />
         <!-- 약품투입동(생활) -->

         <!-- 혼화 & 응집(좌측) -->
         <!-- <main-cube-text :style="{ top: '128px', left: '22px' }"
            :txtStyle="{ top: '84px', left: '20px' }"  :txtSubStyle="{ top: '84px', left: '180px' }"
            :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_mixsink_left.png')" /> -->
         <!-- 혼화 & 응집(좌측) -->

         <!-- 침전지 -->
         <!-- 침전지 -->

         <!-- 여과지(생활) -->
         <main-cube-text :style="{ top: '319px', left: '86px' }"
            :txtStyle="{ top: '36px', left: '24px' }" :backImg="require('@/assets/img/yeogwaji.png')" cubeText="여과지(생활)" />
         <!-- 여과지(생활) -->

         <!-- 역세펌프동(생활) -->
          <main-cube-text :style="{ top: '243px', left: '398px' }"
          :txtStyle="{ top: '-36px', left: '-8px' }" :backImg="require('@/assets/img/local_nakdong/gumi/building/life.png')" cubeText="역세펌프동(생활)" />
         <!-- 역세펌프동(생활) -->

         <!-- 관리본부 -->
          <!-- <main-cube-text :style="{ top: '424px', left: '245px' }"
          :txtStyle="{ top: '18px', left: '184px' }" :backImg="require('@/assets/img/local_nakdong/gumi/building/management.png')"  /> -->
         <!-- 관리본부 -->
         
         <!-- 착수정2(우측) -->
         <!-- <main-cube-text :style="{ top: '36px', left: '871px' }"
            :txtStyle="{ top: '-15px', left: '-26px' }" :backImg="require('@/assets/img/chagsujeong2.png')"/> -->
         <!-- //착수정2(우측) -->

         <!-- 약품투입동(공업) -->
         <main-cube-text :style="{ top: '54px', left: '1052px' }"
            :txtStyle="{ top: '-4px', left: '40px' }" :backImg="require('@/assets/img/yagpum2.png')" cubeText="약품투입동(공업)" />
         <!-- //약품투입동(공업) -->

         <!-- 혼화 & 응집2(우측) -->
         <!-- <main-cube-text :style="{ top: '136px', left: '866px' }"
            :txtStyle="{ top: '76px', left: '34px' }"  :txtSubStyle="{ top: '76px', left: '236px' }"
            :backImg="require('@/assets/img/local_nakdong/gumi/building/gu_mixsink_right.png')" /> -->
         <!-- //혼화 & 응집2(우측) -->

         <!-- 침전지2 -->
         <!-- //침전지2 -->

         <!-- 침전지3 -->
         <!-- <main-cube-text :style="{  top: '95px', left: '1310px' }"
            :txtStyle="{top: '-26px', left: '-4px' }" :backImg="require('@/assets/img/chimjeonji3.png')"  /> -->
         <!-- //침전지3 -->

         <!-- 송수펌프동(공업) -->
         <main-cube-text :style="{ top: '176px', left: '1494px' }" 
            :txtStyle="{ top: '70px', left: '-94px' }"
            :backImg="require('@/assets/img/songsu.png')" cubeText="송수펌프동(공업)" />
         <!-- <main-cube :style="{ top: '220px', left: '1185px' }" :nameText="grpList" /> -->
         <!-- 송수펌프동(공업) -->

         <!-- 탈수기동 -->
         <main-cube-text :style="{ top: '181px', right: '21px' }"
            :txtStyle="{ top: '-18px', left: '-30px' }" :backImg="require('@/assets/img/dehydrator.png')"
            cubeText="탈수기동" />
         <!-- 탈수기동 -->

         <!-- 차염투입동 -->
         <!-- <main-cube-text :style="{ top: '293px', left: '739px' }"
            :txtStyle="{ top: '-18px', left: '-123px' }"  :backImg="require('@/assets/img/sodog.png')" /> -->
         <!-- //차염투입동 -->

         <!-- 오존투입동 -->
         <main-cube-text :style="{ top: '409px', left: '724px' }"
            :txtStyle="{ top: '5px', left: '-106px' }" cubeText="오존투입동" :backImg="require('@/assets/img/ozone.png')" />
         <!-- //오존투입동 -->

         <!-- 활성탄여과지 -->
         <!-- <main-cube-text :style="{ top: '471px', left: '710px' }"
            :txtStyle="{ top: '58px', left: '0px' }" 
            :backImg="require('@/assets/img/gac_yeogwa.png')" /> -->
         <!-- //활성탄여과지 -->

         <!-- 여과지(4단지) -->
         <main-cube-text :style="{ top: '335px', left: '890px' }"
            :txtStyle="{ top: '18px', left: '-14px' }" cubeText="여과지(4단지)" :backImg="require('@/assets/img/yeogwa2.png')" />
         <!-- //여과지(4단지) -->

         <!-- 송수펌프동(4단지) -->
         <main-cube-text :style="{ top: '480px', left: '977px' }"
         :txtStyle="{ top: '-2px', left: '45px' }"
            cubeText="송수펌프동(4단지)" :backImg="require('@/assets/img/songsu2.png')" />
         <!-- <main-cube :style="{ top: '390px', left: '835px' }" :nameText="grpList" /> -->
         <!-- //송수펌프동(4단지) -->
         
         <!-- 송수펌프동(통합) -->
         <main-cube-text :style="{ top: '324px', left: '1338px' }" @popupShow="popupShow"
         @popupHide="popupHide" @click="this.$router.push('/PumpControl')" :txtStyle="{ top: '101px', left: '-79px' }"
         cubeText="송수펌프동(통합)" :backImg="require('@/assets/img/songsu3.png')"
         :hoverImg="require('@/assets/img/local_nakdong/gumi/building/gumi_center_up.png')" />
         <main-cube :style="{ top: '292px', left: '1292px' }" :nameText="nameText" />
         <!-- //송수펌프동(통합) -->

         </div>
         
         <!-- <div class="waterwall_back"></div> -->
      </div>
   </b-col>
   <!-- //구미 정수장 메인 -->
   <!-- hover 될 때 표시될 화면 -->
   <HoverPopup ref="popup" :hoverVal="nameText" :alarmHoverGrpList="alarmOldList" @songsuList="songsuList" />
   <!-- //hover 될 때 표시될 화면 -->
</template>
 
<script>
import HoverPopup from '@/views/DashBoard/DashBoard/HoverPopup.vue'
import MainCube from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCube.vue'
import MainCubeText from '@/views/DashBoard/DashBoard/MainSmallComponents/MainCubeText.vue'
export default {
   components: { MainCube, MainCubeText, HoverPopup }
   , data() {
      return {
         hoverVal: {
            title: "활성탄흡착지동", mainValue: 400, values: [
               { title: '활성탄흡착지 설비(MCC-501)', value: 323 },
               { title: '역세척펌프2호 설비(MCC-502)', value: 323 },
               { title: '활성탄흡착지 분전반(LP-501)', value: 128 },
            ]
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
      songsuList(grpList, alarmGrpList) {
         this.nameText = grpList[0];
         this.alarmOldList = alarmGrpList[0]
      }
   },
}
</script>
 
<style>
/* .map-contents {
   position: relative;
   top: -70px;
   left: 30px;
   margin: 0 auto;
   width: 1550px;
   width: 1167px;
   height: 500px;
} */

.map-contents {
  position: relative;
  top: 0px;
  left: 0px;
  width: 1840px;
  height: 650px;
  /* transform: scale(0.90, 0.90); */
  /* transform-origin: top; */
  margin: 0 auto;
}

.map-contents__chimjeonji .aurora_chimjeonji {
   pointer-events: none;
   top: -33px;
   left: 46px;
   -webkit-animation: blink-data-v-d79beb4e 3s infinite alternate;
   animation: blink-data-v-d79beb4e 3s infinite alternate;
}

.waterwall_back {
   position: absolute;
   top: 0;
   left: 0;
   width: 1550px;
   height: 500px;
   background: url(@/assets/img/waterwall_back.png) no-repeat;
   background-size: 71% 87%;
   background-position: 56% 85%;
}

.waterwall_back_gumi {
  position: absolute;
  top: -48px;
  left: 42px;
  width: 1757px;
  height: 646px;
  background: url(@/assets/img/local_nakdong/gumi/gumi_mapframe.png) no-repeat;
  /* background-size: 71% 87%;
  background-position: 56% 85%; */
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
}
</style>