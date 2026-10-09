<template>
  <div>
    <div class="position-relative mx-5" style="display: block">
      <!-- 전력소비 & 전력절감-->
      <b-row>
        <b-col class="position-relative">
          <div class="position-absolute bottom-0 start-0 px-3" :style="{ width: '416px', top: '-4px !important' }">
            <!-- 소비 현황 시작 -->
            <div class="row mb-3">
              <div class="col-xl-3">
                <div class="blue_round m-auto">
                  <span style="margin-bottom: -2px;">소비</span>
                  <span style="margin-top: -5px;">현황</span>
                </div>
              </div>
              <div class="col-xl-9">
                <div class="blue_round box-bg" style="width: 510px;">
                  <div class="w-100 d-flex flex_center_between" style="height: 30px;">
                    <div class="content__text-box">전력소비</div>
                    <div class="content__value-box" style="width: 200px;">
                      <span style="font-size: 22px;">0</span>
                      <span class="unit">kW</span>
                    </div>
                  </div>

                  <div class="w-100 d-flex flex_center_between" style="height: 70px;">
                    <div class="animationTItle-two">
                      <div class="fL animationItem-two" style="display: block;">
                        <div class="d-flex">
                          <div class="w-50">
                            <div class="flex_center_between justify_start">
                              <div class="content__text-box" style="width: 60px;">금일</div>
                              <div class="content__value-box">
                                <span>0</span>
                                <span class="unit">kWh</span>
                              </div>
                            </div>
                          </div>
                          <div class="w-50">
                            <div class="flex_center_between justify_start">
                              <div class="content__text-box">목표대비</div>
                              <div class="content__value-box">
                                <span>0</span>
                                <span class="unit">%</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div class="fL animationItem-two" style="display: block;">
                        <div class="d-flex">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">금월</div>
                            <div class="content__value-box">
                              <span>0</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>

                          <div class="flex_center_between justify_start">
                            <div class="content__text-box">목표대비</div>
                            <div class="content__value-box">
                              <span>0</span>
                              <span class="unit">%</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div class="fL animationItem-two" style="display: block;">
                        <div class="d-flex">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">금년</div>
                            <div class="content__value-box">
                              <span>0</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>

                          <div class="flex_center_between justify_start">
                            <div class="content__text-box">목표대비</div>
                            <div class="content__value-box">
                              <span>0</span>
                              <span class="unit">%</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div class="fL animationItem-two" style="display: block;">
                        <div class="d-flex ">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">전일</div>
                            <div class="content__value-box">
                              <span>0</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>

                          <div class="flex_center_between justify_start">
                            <div class="content__text-box">목표대비</div>
                            <div class="content__value-box">
                              <span>0</span>
                              <span class="unit">%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 소비 현황 끝 -->

            <!-- 절감 현황 시작 -->
            <div class="row mb-3">
              <div class="col-xl-3">
                <div class="green_round m-auto">
                  <span style="margin-bottom: -2px;">절감</span>
                  <span style="margin-top: -5px;">현황</span>
                </div>
              </div>
              <div class="col-xl-9" style="display: flex;">
                <div class="blue_round box-bg" style="width: 250px; margin-right: 10px;">
                  <div class="w-100 d-flex flex_center_between" style="height: 30px;">
                    <div class="content__text-box" style="width: 90px;">전력절감</div>
                    <div class="content__value-box" style="width: 112px;">
                      <span style="font-size: 22px;">0</span>
                      <span class="unit">kW</span>
                    </div>
                  </div>
                  <div class="w-100 d-flex flex_center_between" style="height: 70px;">
                    <div class="animationTItle">
                      <div class="fL animationItem" style="display: block;">
                        <div class="d-flex flex-column">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">금일</div>
                            <div class="content__value-box">
                              <span>1,762</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>
                          <!--v-if-->
                        </div>
                      </div>
                      <div class="fL animationItem" style="display: block;">
                        <div class="d-flex flex-column">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">금월</div>
                            <div class="content__value-box">
                              <span>7,549</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>
                          <!--v-if-->
                        </div>
                      </div>
                      <div class="fL animationItem" style="display: block;">
                        <div class="d-flex flex-column">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">금년</div>
                            <div class="content__value-box">
                              <span>10,582</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>
                          <!--v-if-->
                        </div>
                      </div>
                      <div class="fL animationItem" style="display: block;">
                        <div class="d-flex flex-column">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">전일</div>
                            <div class="content__value-box">
                              <span>1,762</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>
                          <!--v-if-->
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="blue_round box-bg" style="width: 250px;">
                  <div class="w-100 d-flex flex_center_between" style="height: 30px;">
                    <div class="content__text-box" style="width: 90px;">탄소절감</div>
                    <div class="content__value-box" style="width: 112px;">
                      <span style="font-size: 22px;">0</span>
                      <span class="unit">kW</span>
                    </div>
                  </div>
                  <div class="w-100 d-flex flex_center_between" style="height: 70px;">
                    <div class="animationTItle">
                      <div class="fL animationItem" style="display: block;">
                        <div class="d-flex flex-column">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">금일</div>
                            <div class="content__value-box">
                              <span>1,762</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>
                          <!--v-if-->
                        </div>
                      </div>
                      <div class="fL animationItem" style="display: block;">
                        <div class="d-flex flex-column">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">금월</div>
                            <div class="content__value-box">
                              <span>7,549</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>
                          <!--v-if-->
                        </div>
                      </div>
                      <div class="fL animationItem" style="display: block;">
                        <div class="d-flex flex-column">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">금년</div>
                            <div class="content__value-box">
                              <span>10,582</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>
                          <!--v-if-->
                        </div>
                      </div>
                      <div class="fL animationItem" style="display: block;">
                        <div class="d-flex flex-column">
                          <div class="flex_center_between justify_start">
                            <div class="content__text-box" style="width: 60px;">전일</div>
                            <div class="content__value-box">
                              <span>1,762</span>
                              <span class="unit">kWh</span>
                            </div>
                          </div>
                          <!--v-if-->
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            </div>
            <!-- 절감 현황 끝 -->
          </div>
        </b-col>
      </b-row>
      <!-- //전력소비 & 전력절감-->
      <div class="dash_right"></div>
      <div class="dash_border_img"></div>
      <div class="right_box1"></div>
      <div class="right_box2"></div>
      <div class="right_box3"></div>
      <!-- 3D MAP 영역 -->
      <b-row class="align-items-center" :style="{ width: '75%', height: 'calc(100vh - 118px)' }">
        <!-- 고산 정수장 메인 -->
        <b-col class="position-relative">
          <div class="map-contents" :style="{ width: '1550px', height: 'calc(100vh - 118px)' }">
            asdfqwerqwerwer
            <div class="waterwall_back_gosan"></div>
          </div>
        </b-col>
        <!-- //고산 정수장 메인 -->
      </b-row>
      <!-- //3D MAP 영역 -->
      <!-- 오른쪽 영역 -->
      <div class="position-absolute top-0 end-0"
        :style="{ width: '25%', height: 'calc(100vh - 118px)', right: '-25px !important' }">
        <b-row class="row-cols-1 h-100 table-bg-long" :style="{ padding: '15px' }">
          <b-col>
            <b-row class="px-3">
              <div class="bg" :style="{ height: '256px' }">
                <b-col class="mx-3 pt-3">
                  <b-row>
                    <h5 class="dash_title" :style="{ width: '30%', lineHeight: '25px' }">펌프 현황</h5>
                    <div :style="{ width: '70%' }">
                      <b-row class="row-cols-2 gx-2 h-100">
                        <b-col xl="7">
                          <div class="h-100 p-2"
                            :style="{ backgroundColor: 'rgba(139, 194, 240, 0.22)', borderRadius: '5px 5px 0 0' }">
                            <span class="right_pump_title d-block m-auto" style="line-height: 33px;">생활</span>
                            <div class="row row-cols-3 gx-1">
                              <div class="col">
                                <div class="dash_pump_tab pump_number selected_tab">1</div>
                              </div>
                              <div class="col">
                                <div class="dash_pump_tab pump_number">2</div>
                              </div>
                              <div class="col">
                                <div class="dash_pump_tab pump_number">3</div>
                              </div>
                            </div>
                          </div>
                        </b-col>
                        <b-col xl="5">
                          <div class="h-100 p-2"
                            :style="{ backgroundColor: 'rgba(139, 194, 240, 0.22)', borderRadius: '5px 5px 0 0' }">
                            <span class="right_pump_title d-block m-auto" style="line-height: 33px;">공업</span>
                            <div class="row row-cols-2 gx-1">
                              <div class="col">
                                <div class="dash_pump_tab pump_number selected_tab">1</div>
                              </div>
                              <div class="col">
                                <div class="dash_pump_tab pump_number">2</div>
                              </div>
                            </div>
                          </div>
                        </b-col>
                      </b-row>
                    </div>
                  </b-row>
                </b-col>
                <b-col class="px-3" :style="{ height: '55%', overflow: 'hidden' }">
                  <b-row>
                    <b-col>
                      <carousel class="carousel_vertical" v-for="slide in 10" :key="slide">
                        <slide v-for="slide in 5" :key="slide">
                          <div class="carousel__item">
                            <div class="position-absolute top-50 start-50 translate-middle">
                              <div class="off_pump_img px-2" :style="{ width: '100%' }">비활성화</div>
                            </div>
                            <div class="position-absolute w-100 h-100">
                              <span class="pump_name fontData">0</span>
                              <span class="pump_name_unit">kW</span>
                            </div>
                            <img src="@/assets/img/pump_00.png" alt="">
                          </div>
                        </slide>
                        <template #addons>
                          <navigation />
                        </template>
                      </carousel>
                    </b-col>
                  </b-row>

                </b-col>
              </div>
            </b-row>
          </b-col>
          <b-col>
            <b-row class="px-3">
              <div class="bg" :style="{ height: '256px' }">
                <b-col class="title_wrap d-flex align-items-center mx-3">
                  <h5 class="mb-0 dash_title me-auto">주요배수지 현황</h5>
                  <ul class="nav default-tabs">
                    <li class="nav-item">
                      <a class="nav-link active" data-bs-toggle="tab" href="#menu1">봉담2</a>
                    </li>
                    <li class="nav-item">
                      <a class="nav-link" data-bs-toggle="tab" href="#menu2">남양6</a>
                    </li>
                    <li class="nav-item">
                      <a class="nav-link" data-bs-toggle="tab" href="#menu3">마도</a>
                    </li>
                  </ul>
                </b-col>
                <b-col class="mx-3">
                  <div class="tab-content">
                    <div class="tab-pane fade active show" id="menu1">
                      <div class="pump_div"
                        :style="{ height: '200px', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '13px', marginTop: '10px' }">
                        <inflow-status :inflowVal="item" v-for="item in majorData1" v-bind:key="item" />
                      </div>
                    </div>
                    <div class="tab-pane fade" id="menu2">
                      <div class="pump_div" id="menu2"
                        :style="{ height: '200px', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '13px', marginTop: '10px' }">
                        <inflow-status :inflowVal="item" v-for="item in majorData2" v-bind:key="item" />
                      </div>
                    </div>
                    <div class="tab-pane fade" id="menu3">
                      <div class="pump_div"
                        :style="{ height: '200px', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '13px', marginTop: '10px' }">
                        <inflow-status :inflowVal="item" v-for="item in majorData3" v-bind:key="item" />
                      </div>
                    </div>
                  </div>
                </b-col>
              </div>
            </b-row>
          </b-col>
          <b-col>
            <b-row class="px-3">
              <div class="bg" :style="{ height: '256px' }">
                <b-col class="mx-3 pt-3">
                  <h5 class="dash_title" :style="{ lineHeight: '25px' }">피크 제어</h5>
                </b-col>
                <b-col class="mx-3">
                  <div style="display: block; color: white; height: 210px;">차트 영역</div>
                </b-col>
              </div>
            </b-row>
          </b-col>
        </b-row>
      </div>
      <!-- //오른쪽 영역 -->
    </div>
  </div>
</template>

<script>
// If you are using PurgeCSS, make sure to whitelist the carousel CSS classes
import 'vue3-carousel/dist/carousel.css'
import { Carousel, Slide, Navigation } from 'vue3-carousel'
// import PumpButton from './Button/PumpButton.vue'

export default {
  name: 'App',
  components: {
    Carousel,
    Slide,
    Navigation,
    // PumpButton,
  },

}
</script>

<style>
.waterwall_back_gosan {
  position: absolute;
  top: 183px;
  left: 0;
  width: 1590px;
  height: 690px;
  background: url(@/assets/img/local_geumgang/gosan/waterwall_gosan.png) no-repeat;
  background-size: 67% 100%;
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

</style>