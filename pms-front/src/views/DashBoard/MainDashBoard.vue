<template>
  <div>
    <div>
      <div class="position-relative mx-5" style="display: block">

        <!-- 자율진단 영역 -->
        <self-part />
        <!-- 자율진단 영역 -->

        <!-- 설비현황 통계 -->
        <facility-box></facility-box>
        <!-- //설비현황 통계 -->

        <!-- 3D MAP 영역 -->
        <b-row class="align-items-center" :style="{ width: '75%', height: 'calc(100vh - 118px)' }">
          <MapContents />
        </b-row>
        <!-- //3D MAP 영역 -->
      </div>
    </div>
  </div>
</template>

<script>
import MapContents from "@/views/DashBoard/gosan/MapContents.vue"
import SelfPart from './DashBoard/SelfDiagnosis/SelfPart.vue'
import FacilityBox from './DashBoard/FacilityStatus/FacilityBox.vue'

export default {
  name: 'App',
  components: {
    // PumpButton,
    MapContents,
    SelfPart,
    FacilityBox
  },
  mounted() {
    setInterval(() => {
      location.reload(); // 페이지를 새로고침
    }, 5 * 60 * 1000);
  }
}
</script>

<style>
.waterwall_back_gosan {
  position: absolute;
  top: 143px;
  left: 0;
  width: 1590px;
  height: 690px;
  background: url(@/assets/img/local_geumgang/gosan/waterwall_gosan.png) no-repeat;
  background-size: 67% 97%;
  background-position: 56% 83%;
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

.hoverInfo {
  bottom: 10px;
  z-index: 100;
  position: absolute;
  right: 0;
  width: 540px;
  box-shadow: 0 0 10px 0 #accfff;
  background-color: #132f4e;
  animation: move-up-building 1s ease-in-out 0s normal backwards;
}

.hoverInfoNone {
  position: absolute;
  /* 박스를 아래로 내리도록 조정 */
  right: 0;
  width: 540px;
  box-shadow: 0 0 10px 0 #accfff;
  background-color: #132f4e;
  animation: move-down-popup 1s ease-in-out 0s normal forwards;
  /* 새로운 애니메이션 적용 */
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

/* 자율진단 */
.dashboard-info-container {
  background: url(@/assets/img/dashboard_info.3835e415.png) no-repeat;
  width: 450px;
  height: 516px;
  position: absolute;
  top: 375px;
  right: 0;
  flex-flow: column;
  background-size: 100% 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  /* align-items: center; */
}

/* 설비현황 통계 */
.pieChart-box {
  position: absolute;
  width: 450px;
  height: 350px;
  top: 0;
  right: 0;
  box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.3);
}

.charts {
  width: 100%;
  height: 100%;
  background: #05223b93;
  border: 1px solid #2660ab;
  border-radius: 12px;
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 10px 15px;
}

.charts .title-box {
  font-size: 18px;
  display: flex;
  align-items: center;
  height: 15%;
  color: #c8d7e9;
  text-shadow: 0px 0px 10px #24baff;
}

.charts .title-box img {
  width: 16px;
  margin-right: 8px;
}

.blur {
  filter: blur(3px);
  -webkit-filter: blur(3px);
  border-color: #24d3ff;
}

.top-L {
  top: -1px;
  left: -1px;
  border-top: 2px solid #2C80FF;
  border-left: 2px solid #2C80FF;
  border-top-left-radius: 12px;
}

.top-R {
  top: -1px;
  right: -1px;
  border-top: 2px solid #2C80FF;
  border-right: 2px solid #2C80FF;
  border-top-right-radius: 12px;
}

.box-edge {
  width: 15px;
  height: 15px;
  position: absolute;
}

.bottom-L {
  bottom: -1px;
  left: -1px;
  border-bottom: 2px solid #2C80FF;
  border-left: 2px solid #2C80FF;
  border-bottom-left-radius: 12px;
}

.bottom-R {
  bottom: -1px;
  right: -1px;
  border-bottom: 2px solid #2C80FF;
  border-right: 2px solid #2C80FF;
  border-bottom-right-radius: 12px;
}

.dashboard-info-container .box2 {
  /* height: 40%; */
  display: flex;
  flex-direction: column;
}

.dashboard-info-container .content-box .titleBox {
  position: relative;
  margin: 10px;
  font-size: 18px;
  color: white;
  width: 200px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dashboard-info-container .titleBox .title2 {
  text-shadow: 0 0 9px #5cafff;
  z-index: 1;
}

.dashboard-info-container .content-box .titleBox img {
  position: absolute;
  z-index: 0;
  bottom: -5px;
}

.dashboard-info-container .box2 .content3 {
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.dashboard-info-container .box2 .content3 .list-box {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 15px;
}

.dashboard-info-container .box2 .content3 .list-box .list1 {
  width: 65%;
}

.dashboard-info-container .box2 .content3 .list-box .itemList {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.dashboard-info-container .box2 .content3 .list-box .itemList .list-title {
  left: -87px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
}

.dashboard-info-container .box2 .content3 .list-box .itemList .list-title span {
  z-index: 1;
  text-shadow: 0 0 9px #5cafff;
  color: white;
  font-size: 14px;
}

.dashboard-info-container .box2 .content3 .list-box .itemList .list-title img {
  position: absolute;
  z-index: 0;
}

.dashboard-info-container .box2 .content3 .list-box .list2 {
  width: 35%;
}

.dashboard-info-container .box2 .content3 .list-box .itemList .item-box .item {
  width: 50%;
  background: rgba(139, 194, 240, 0.25);
  border: 1px solid #b4dffa;
  padding: 5px 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  z-index: 1;
  box-shadow: 0 0 10px 0 rgba(172, 207, 255, 0.7);
  background: rgba(139, 194, 240, 0.4);
  color: white;
  opacity: 0.4;
}

.dashboard-info-container .box2 .content3 .list-box .itemList .item-box {
  display: flex;
  gap: 10px;
  width: 100%;
}

.dashboard-info-container .box2 .content3 .list-box .itemList .item-box .item.selected {
  opacity: 1;
}

.dashboard-info-container .box2 .content3 .list-box .itemList .item-box .item.alarm {
  background: #ff5c5c66;
  border: solid 1px #ff5c5c;
}

.dashboard-info-container .box2 .content3 .motor-box {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.dashboard-info-container .box2 .content3 .motor-box img {
  width: 60%;
}

.dashboard-info-container .box2 .content3 .motor-box img.alert-ani {
  animation: alert-ani 1s infinite;
}

@keyframes alert-ani {
  from {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }

  to {
    opacity: 1;
  }
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area {
  position: absolute;
  top: 0;
  left: 0;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group {
  position: absolute;
  font-size: 12px;
  color: #fff;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group .val-1 {
  padding: 3px 0 2px;
  text-align: center;
  width: 70px;
  margin-bottom: 3px;
  border: solid 1px #b4dffa;
  color: white;
  border-radius: 2px;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group .val-2 {
  padding: 3px 0 2px;
  text-align: center;
  width: 70px;
  border: solid 1px #b4dffa;
  color: white;
  border-radius: 2px;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group .val-line {
  position: absolute;
  border: 1px dotted #fff;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group .val-icon {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 10px;
  background: radial-gradient(#0400ff, #5441ff);
  border: 1px solid #fff;
  box-shadow: 2px 2px 1px #000;
}

/* type1 */
.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type1 {
  top: 0px;
  left: 10px;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type1 .val-icon {
  top: 78px;
  left: 96px;
  background: #5470c6;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type1 .val-line {
  top: 20px;
  left: 75px;
  width: 27px;
  height: 58px;
  border-left: none;
  border-bottom: none;
}

/* type2 */
.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type2 {
  top: 112px;
  left: 10px;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type2 .val-icon {
  top: -60px;
  left: 217px;
  background: #91cc75;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type2 .val-line {
  top: -50px;
  left: 75px;
  width: 148px;
  height: 76px;
  border-left: none;
  border-top: none;
}

/* type3 */
.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type3 {
  top: 0px;
  left: 368px;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type3 .val-icon {
  top: 30px;
  left: -119px;
  background: #fac858;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type3 .val-line {
  top: 20px;
  left: -115px;
  width: 115px;
  height: 9px;
  border-right: none;
  border-bottom: none;
}

/* type4 */
.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type4 {
  top: 113px;
  left: 368px;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type4 .val-icon {
  top: -57px;
  left: -30px;
  background: #ee6666;
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group .val-icon.alert {
  background: radial-gradient(#ff1a1a, #ff6969);
}

.dashboard-info-container .box2 .content3 .motor-box .motor-value-area .group.type4 .val-line {
  top: -52px;
  left: -20px;
  width: 58px;
  height: 50px;
  border-left: none;
  border-bottom: none;
}
</style>