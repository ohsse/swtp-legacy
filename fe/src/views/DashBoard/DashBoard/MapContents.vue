<template>
   <b-col class="position-relative">
      <div class="map-contents">
         <!-- 착수정 -->
         <main-cube-text :style="{ top: '76px', left: '326px', width: '97px', height: '46px' }"
            :txtStyle="{ top: '-48px', left: '-66px' }" :backImg="require('@/assets/img/chagsujeong.png')" cubeText="착수" />
         <main-cube :style="{ top: '7px', left: '374px' }" :cubeVal="0" />
         <!-- 착수정 -->
         <!-- 약품 -->
         <main-cube-text :style="{ top: '129px', left: '302px', width: '66px', height: '34px' }"
            :txtStyle="{ top: '-28px', left: '-4px' }" :backImg="require('@/assets/img/yagpum.png')" cubeText="약품" />
         <main-cube :style="{ top: '78px', left: '272px' }" :cubeVal="0" />
         <!-- 약품 -->
         <!-- 혼화 & 응집 -->
         <main-cube-text :style="{ top: '157px', left: '85px', width: '327px', height: '126px' }"
            :txtStyle="{ top: '-48px', left: '-57px' }" cubeText="혼화/응집" :txtSubStyle="{ top: '38px', left: '183px' }"
            cubeSubText="침전" :backImg="require('@/assets/img/chimjeonji.png')" />
         <main-cube :style="{ top: '90px', left: '164px' }" :cubeVal="0" />
         <!-- 혼화 & 응집 -->
         <!-- 침전지 -->
         <main-cube :style="{ top: '172px', left: '236px' }" :cubeVal="0" />
         <!-- 침전지 -->
         <!-- 여과지 -->
         <main-cube-text :style="{ top: '269px', left: '155px', width: '198px', height: '65px' }"
            :txtStyle="{ top: '20px', left: '57px' }" :backImg="require('@/assets/img/yeogwaji.png')" cubeText="여과지" />
         <main-cube :style="{ top: '269px', left: '182px' }" :cubeVal="0" />
         <!-- 여과지 -->
         <!-- 착수정2 -->
         <main-cube-text :style="{ top: '84px', left: '725px', width: '105px', height: '45px' }"
            :txtStyle="{ top: '-50px', left: '-105px' }" :backImg="require('@/assets/img/chagsujeong2.png')"
            cubeText="착수" />
         <main-cube :style="{ top: '13px', left: '733px' }" :cubeVal="0" />
         <!-- //착수정2 -->
         <!-- 약품2 -->
         <main-cube-text :style="{ top: '89px', left: '836px', width: '66px', height: '34px' }"
            :txtStyle="{ top: '-51px', left: '17px' }" :backImg="require('@/assets/img/yagpum2.png')" cubeText="약품" />
         <main-cube :style="{ top: '18px', left: '832px' }" :cubeVal="0" />
         <!-- //약품2 -->
         <!-- 혼화 & 응집2 -->
         <main-cube-text :style="{ top: '153px', left: '707px', width: '401px', height: '126px' }"
            :txtStyle="{ top: '-35px', left: '-133px' }" cubeText="혼화/응집" :txtSubStyle="{ top: '29px', left: '212px' }"
            cubeSubText="침전" :backImg="require('@/assets/img/chimjeonji2.png')" />
         <main-cube :style="{ top: '102px', left: '710px' }" :cubeVal="0" />
         <!-- //혼화 & 응집2 -->
         <!-- 침전지2 -->
         <main-cube :style="{ top: '160px', left: '898px' }" :cubeVal="0" />
         <!-- //침전지2 -->
         <!-- 침전지3 -->
         <main-cube-text :style="{ top: '121px', left: '1037px', width: '158px', height: '60px' }"
            :txtStyle="{ top: '-40px', left: '51px' }" :backImg="require('@/assets/img/chimjeonji3.png')" cubeText="침전" />
         <main-cube :style="{ top: '62px', left: '1067px' }" :cubeVal="0" />
         <!-- //침전지3 -->
         <!-- 송수 -->
         <main-cube-text :style="{ top: '183px', left: '1141px', width: '120px', height: '100px' }"
            :txtStyle="{ top: '10px', left: '-70px' }" :backImg="require('@/assets/img/songsu.png')" cubeText="송수(공업)" />
         <main-cube :style="{ top: '174px', left: '1185px' }" :cubeVal="0" />
         <!-- 송수 -->
         <!-- 탈수기동 -->
         <main-cube-text :style="{ top: '162px', right: '-210px', width: '84px', height: '63px' }"
            :txtStyle="{ top: '-43px', left: '-124px' }" :backImg="require('@/assets/img/dehydrator.png')"
            cubeText="탈수기동" />
         <main-cube :style="{ top: '100px', right: '-212px' }" :cubeVal="0" />
         <!-- 탈수기동 -->
         <!-- 소독 -->
         <main-cube-text :style="{ top: '290px', left: '628px', width: '82px', height: '44px' }"
            :txtStyle="{ top: '-48px', left: '-107px' }" cubeText="소독" :backImg="require('@/assets/img/sodog.png')" />
         <main-cube :style="{ top: '221px', left: '632px' }" :cubeVal="0" />
         <!-- //소독 -->
         <!-- 오존 -->
         <main-cube-text :style="{ top: '356px', left: '611px', width: '78px', height: '43px' }"
            :txtStyle="{ top: '-37px', left: '-115px' }" cubeText="오존" :backImg="require('@/assets/img/ozone.png')" />
         <main-cube :style="{ top: '302px', left: '609px' }" :cubeVal="0" />
         <!-- //소독 -->
         <!-- GAC여과 -->
         <main-cube-text :style="{ top: '400px', left: '601px', width: '147px', height: '96px' }"
            :txtStyle="{ top: '24px', left: '-92px' }" cubeText="GAC여과"
            :backImg="require('@/assets/img/gac_yeogwa.png')" />
         <main-cube :style="{ top: '402px', left: '643px' }" :cubeVal="0" />
         <!-- //GAC여과 -->
         <!-- 여과2 -->
         <main-cube-text :style="{ top: '293px', left: '741px', width: '112px', height: '78px' }"
            :txtStyle="{ top: '-29px', left: '-87px' }" cubeText="여과" :backImg="require('@/assets/img/yeogwa2.png')" />
         <main-cube :style="{ top: '244px', left: '764px' }" :cubeVal="0" />
         <!-- //여과2 -->
         <!-- 송수2 -->
         <main-cube-text :style="{ top: '387px', left: '754px', width: '180px', height: '42px' }"
            :txtStyle="{ top: '-46px', left: '-52px' }" cubeText="송수(4단지)"
            :backImg="require('@/assets/img/songsu2.png')" />
         <main-cube :style="{ top: '323px', left: '835px' }" :cubeVal="0" />
         <!-- //송수2 -->
         <!-- 송수3 -->
         <main-cube-text :style="{ top: '288px', left: '1040px', width: '92px', height: '103px' }"
            :txtStyle="{ top: '18px', left: '-92px' }" cubeText="송수(통합)" :backImg="require('@/assets/img/songsu3.png')" />
         <main-cube :style="{ top: '287px', left: '1062px' }" :cubeVal="0" />
         <!-- //송수3 -->
         <div class="waterwall_back"></div>
      </div>
      <!-- hover 될 때 표시될 화면 -->
      <hover-popup :hoverVal="hoverVal" />
      <!-- //hover 될 때 표시될 화면 -->
   </b-col>
</template>

<script>
import HoverPopup from './HoverPopup.vue'
import MainCube from './MainSmallComponents/MainCube.vue'
import MainCubeText from './MainSmallComponents/MainCubeText.vue'
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
         }
      }
   }
}
</script>

<style>
.map-contents {
   position: relative;
   top: -29px;
   left: 30px;
   margin: 0 auto;
   /* width: 1550px; */
   width: 1167px;
   height: 500px;
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

.hoverInfo {
   /* width: 31%;
   height: 40%; */
   width: 35%;
   height: 35%;
   position: absolute;
   float: left;
   top: 63%;
   left: -3.5%;
   display: none;
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
}</style>