<template>
  <b-col>
    <b-row class="px-3">
      <div class="bg" :style="{ height: '280px' }">
        <b-col class="mx-3 pt-3">
          <b-row>
            <div>
              <h5 class="dash_title" :style="{ width: '30%', lineHeight: '25px' }">펌프 현황</h5><br>
            </div>
          </b-row>
        </b-col>
        <!-- 펌프현황 생활&공업 펌프갯수 표시 -->
        <b-col>
          <div :style="{ width: '100%' }">
            <b-row class="row-cols-2 gx-2 h-100 px-3">
              <b-col xl="4" class="position-relative">
                <div class="position-absolute" :style="{ top: '-33px', right: '4px' }">
                  <span class="right_pump_title d-block m-auto"
                    :style="{ backgroundColor: 'rgba(139, 194, 240, 0.22)', borderRadius: '5px 5px 0 0', lineHeight: '33px' }">{{
                      this.name[0] }}</span>
                </div>
                <div class="h-100 p-2"
                  :style="{ backgroundColor: 'rgba(139, 194, 240, 0.22)', borderRadius: '5px 0 0 0' }">
                  <div class="row gx-1">
                    <PumpTab ref="PumTab1" :suji="this.firSuji" :tabIndex="1" :name="this.name[0]" :length=0
                      @clickTab="clickTab" />
                  </div>
                </div>
              </b-col>
              <b-col xl="4" class="position-relative">
                <div class="position-absolute" :style="{ top: '-33px', right: '4px' }">
                  <span class="right_pump_title d-block m-auto"
                    :style="{ backgroundColor: 'rgba(139, 194, 240, 0.22)', borderRadius: '5px 5px 0 0', lineHeight: '33px' }">{{
                      this.name[1] }}</span>
                </div>
                <div class="h-100 p-2"
                  :style="{ backgroundColor: 'rgba(139, 194, 240, 0.22)', borderRadius: '5px 0 0 0' }">
                  <div class="row gx-1">
                    <PumpTab ref="PumTab2" :suji="this.secSuji" :tabIndex="0" :name="this.name[1]"
                      :length="this.firSuji.length" @clickTab="clickTab" />
                  </div>
                </div>
              </b-col>
              <b-col xl="4" class="position-relative">
                <div class="position-absolute" :style="{ top: '-33px', right: '4px' }">
                  <span class="right_pump_title d-block m-auto"
                    :style="{ backgroundColor: 'rgba(139, 194, 240, 0.22)', borderRadius: '5px 5px 0 0', lineHeight: '33px' }">{{
                      this.name[2] }}</span>
                </div>
                <div class="h-100 p-2"
                  :style="{ backgroundColor: 'rgba(139, 194, 240, 0.22)', borderRadius: '5px 0 0 0' }">
                  <div class="row gx-1">
                    <PumpTab ref="PumTab3" :suji="this.thrSuji" :tabIndex="0" :name="this.name[2]"
                      :length="this.firSuji.length + this.secSuji.length" @clickTab="clickTab" />
                  </div>
                </div>
              </b-col>
            </b-row>
          </div>
        </b-col>
        <!-- //펌프현황 생활&공업 펌프갯수 표시 -->
        <b-col class="px-3" :style="{ height: '55%', overflow: 'hidden' }">
          <b-row>
            <b-col>
              <carousel ref="myCarousel" class="carousel_vertical" @slide-start="handleSlideStart">
                <slide v-for="(slide, i) in this.origin" :key="slide">
                  <div class="carousel__item">
                    <div class="position-absolute top-50 start-50 translate-middle">
                      <div v-if="this.origin[i].value === 'Off'" class="off_pump_img px-2" :style="{ width: '100%' }">비활성화
                      </div>
                    </div>
                    <div class="position-absolute w-100 h-100">
                      <span class="pump_name fontData">{{ this.kwData[i] }}</span>
                      <span class="pump_name_unit">kW</span>
                    </div>
                    <img src="@/assets/img/pump_00.png" alt="">
                  </div>
                </slide>
                <template #addons>
                  <Navigation />
                </template>
              </carousel>
            </b-col>
          </b-row>
        </b-col>
      </div>
    </b-row>
  </b-col>
</template>

<script>
import 'vue3-carousel/dist/carousel.css'
import { Carousel, Slide, Navigation } from 'vue3-carousel'
import PumpTab from '@/views/DashBoard/DashBoard/RightContents/PumpTab.vue'

export default {

  components: {
    Carousel,
    Slide,
    Navigation,
    PumpTab,
  },
  data() {
    return {
      name: new Set(),
      origin: [],
      kwData: [],
      firSuji: [],
      secSuji: [],
      thrSuji: [],
      activeTab: 1,
      activeFirTab: 1,
      activeSecTab: 0,
      activeThrTab: 0
    }
  },
  methods: {
    initData(data) {
      this.origin = data?.pumpStatus
      this.kwOrigin = data?.pwiStatus.sort((a, b) => a.PUMP_GRP - b.PUMP_GRP);
      this.firSuji = this.origin?.filter(item => item.PUMP_GRP === 1);
      this.secSuji = this.origin?.filter(item => item.PUMP_GRP === 2);
      this.thrSuji = this.origin?.filter(item => item.PUMP_GRP === 3);
      this.kwData = this.kwOrigin?.map(item => item.kW);
      const pumpGrpNmSet = new Set(this.origin?.map(item => item.PUMP_GRP_NM));
      this.name = [...pumpGrpNmSet];
    },
    handleSlideStart(data) {
      this.activeTab = data.slidingToIndex + 1
      if (this.activeTab <= this.firSuji.length) {
        this.activeSecTab = 0;
        this.activeThrTab = 0;
        this.activeFirTab = data.slidingToIndex + 1
        this.$refs.PumTab1.changeActiveTab(this.activeFirTab)
        this.$refs.PumTab2.changeActiveTab(this.activeSecTab)
        this.$refs.PumTab3.changeActiveTab(this.activeThrTab)
      }
      else if (this.activeTab <= this.firSuji.length + this.secSuji.length) {
        this.activeFirTab = 0;
        this.activeThrTab = 0;
        this.activeSecTab = (data.slidingToIndex + 1) - this.firSuji.length
        this.$refs.PumTab1.changeActiveTab(this.activeFirTab)
        this.$refs.PumTab2.changeActiveTab(this.activeSecTab)
        this.$refs.PumTab3.changeActiveTab(this.activeThrTab)
      }
      else {
        this.activeFirTab = 0;
        this.activeSecTab = 0;
        this.activeThrTab = (data.slidingToIndex + 1) - (this.firSuji.length + this.secSuji.length)
        this.$refs.PumTab1.changeActiveTab(this.activeFirTab)
        this.$refs.PumTab2.changeActiveTab(this.activeSecTab)
        this.$refs.PumTab3.changeActiveTab(this.activeThrTab)
      }
    },
    clickTab(index) {
      this.$refs.myCarousel.slideTo(index)
    }
  },
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

.selected_tab {
  color: #F8C314 !important;
  border: solid 1px #F8C314 !important;
  font-weight: bold;
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