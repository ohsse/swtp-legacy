<template>
  <div class="position-absolute top-0 end-0"
    :style="{ width: '25%', height: 'calc(100vh - 10.0rem)', right: '-1.5625rem !important' }">
    <b-row class="row-cols-1 h-100 table-bg-long" :style="{ paddingLeft: '.9375rem', paddingRight: '.9375rem' }">
      <div class="row-9">
        <PumpList ref="firPumpList" :bgHeight="firSujiHeight" :style="{ marginTop: marginTop }" :title="name[0]"
          :data="this.firSuji" index="1" @initAiData="initAiData" />
        <PumpList ref="secPumpList" v-show="isSecSuji" :bgHeight="secSujiHeight" :title="name[1]" :data="this.secSuji"
          index="2" :style="{ marginTop: marginTop }" @initAiData="initAiData" />
        <PumpList ref="thrPumpList" v-show="isThrSuji" :bgHeight="thrSujiHeight" :title="name[2]" :data="this.thrSuji"
          index="3" :style="{ marginTop: marginTop }" @initAiData="initAiData" />
        <PumpList ref="fouPumpList" v-show="isFouSuji" :bgHeight="fouSujiHeight" :title="name[3]" :data="this.fouSuji"
          index="4" :style="{ marginTop: marginTop }" @initAiData="initAiData" />
      </div>
      <div v-show="this.$area != 'buan'" class="row-3">
        <bottom-peak ref="bottomPeak"></bottom-peak>
      </div>
    </b-row>
  </div>
</template>

<script>

import BottomPeak from './BottomPeak.vue';
import PumpList from './PumpList.vue'
import { fetchFunc } from '@/util/fetchFunc';
export default {
  components: {
    BottomPeak,
    PumpList
  },
  data() {
    return {
      name: new Set(),
      firSujiHeight: 0,
      secSujiHeight: 0,
      thrSujiHeight: 0,
      fouSujiHeight: 0,
      isSecSuji: false,
      isThrSuji: false,
      isFouSuji: false,
      totalLength: 0,
      firSuji: [],
      secSuji: [],
      thrSuji: [],
      fouSuji: [],
      marginBottom: '20px',
      marginTop: '20px'
    }
  },
  mounted() {
    this.initAiData()
    setInterval(() => {
      this.initAiData();
    }, ((1000 * 60)));
  },
  updated() {
  },
  methods: {
    async initAiData() {
      const dataAi = await fetchFunc(`${this.$apiURL}/ai/selectAiStatus`);
      let firPumpStatus = dataAi?.data[0]?.AI_STATUS
      let secPumpStatus = dataAi?.data[1]?.AI_STATUS
      let thrPumpStatus = dataAi?.data[2]?.AI_STATUS
      let fouPumpStatus = dataAi?.data[3]?.AI_STATUS

      if (dataAi?.data[0]?.emergencyStatus == "1") {
        firPumpStatus = 2
      } else {
        firPumpStatus = dataAi?.data[0]?.AI_STATUS
      }
      if (dataAi?.data[1]?.emergencyStatus == "1") {
        secPumpStatus = 2
      } else {
        secPumpStatus = dataAi?.data[1]?.AI_STATUS
      } if (dataAi?.data[2]?.emergencyStatus == "1") {
        thrPumpStatus = 2
      } else {
        thrPumpStatus = dataAi?.data[2]?.AI_STATUS
      }
      if (dataAi?.data[3]?.emergencyStatus == "1") {
        fouPumpStatus = 2
      } else {
        fouPumpStatus = dataAi?.data[3]?.AI_STATUS
      }

      if (this.$refs.firPumpList) {
        this.$refs.firPumpList.changeAutoPart(firPumpStatus, dataAi?.data[0]?.emergencyStatus)
      }
      if (this.$refs.secPumpList) {
        this.$refs.secPumpList.changeAutoPart(secPumpStatus, dataAi?.data[1]?.emergencyStatus)
      }
      if (this.$refs.thrPumpList) {
        this.$refs.thrPumpList.changeAutoPart(thrPumpStatus, dataAi?.data[2]?.emergencyStatus)
      }
      if (this.$refs.fouPumpList) {
        this.$refs.fouPumpList.changeAutoPart(fouPumpStatus, dataAi?.data[3]?.emergencyStatus)
      }
    },
    initData(data, data1, goal) {
      this.origin = data1?.pumpStatus
      this.firSuji = this.origin?.filter(item => item.PUMP_GRP === 1);
      this.secSuji = this.origin?.filter(item => item.PUMP_GRP === 2);
      this.thrSuji = this.origin?.filter(item => item.PUMP_GRP === 3);
      this.fouSuji = this.origin?.filter(item => item.PUMP_GRP === 4);
      this.fivSuji = this.origin?.filter(item => item.PUMP_GRP === 5);
      this.fivSuji?.forEach(element => {
        this.fouSuji.push(element)
      });
      const pumpGrpNmSet = new Set(this.origin?.map(item => item.PUMP_NM.replace(/_\d+$/, '')));
      this.name = [...pumpGrpNmSet];

      if (this.secSuji?.length > 0) {
        if (this.$area === 'gosan') {
          this.isSecSuji = true
        }
        else if (this.$area === 'goryeong') {
          this.isSecSuji = true
          this.isThrSuji = true
        }
        else if (this.$area === 'buan') {
          this.isSecSuji = true
          this.isThrSuji = true
          this.isFouSuji = true
        }
        else {
          this.isSecSuji = false
        }
        if (this.$area === 'buan') {
          this.marginTop = '10px'
          this.totalLength = this.firSuji?.length + this.secSuji?.length + this.thrSuji?.length + this.fouSuji?.length
          this.firSujiHeight = 45 * this.firSuji?.length
          this.secSujiHeight = 52 * this.secSuji?.length
          this.thrSujiHeight = 52 * this.thrSuji?.length
          this.fouSujiHeight = 60 * this.fouSuji?.length
        }
        else if (this.$area === 'goryeong') {
          this.marginTop = '5px'
          this.totalLength = this.firSuji?.length + this.secSuji?.length + this.thrSuji?.length
          this.firSujiHeight = 55 * this.firSuji?.length
          this.secSujiHeight = 55 * this.secSuji?.length
          this.thrSujiHeight = 62 * this.thrSuji?.length
        }
        else {
          this.totalLength = this.firSuji?.length + this.secSuji?.length
          if (this.firSuji?.length > 4) {
            this.firSujiHeight = 48 * this.firSuji?.length
            this.secSujiHeight = 61 * this.secSuji?.length
          } else {
            this.marginTop = '40px'
            this.firSujiHeight = 62 * this.firSuji?.length
            this.secSujiHeight = 62 * this.secSuji?.length
          }
        }

      }
      else {
        this.totalLength = this.firSuji?.length
        this.firSujiHeight = 62 * this.firSuji?.length
      }
      if (this.$area != 'buan') {
        this.$refs.bottomPeak.initData(data, goal);
      }

    },
  },

}
</script>

<style>
.waterwall_back_gosan {
  position: absolute;
  top: 8.9375rem;
  left: 0;
  width: 99.375rem;
  height: 43.125rem;
  background: url(@/assets/img/local_geumgang/gosan/waterwall_gosan.png) no-repeat;
  background-size: 67% 97%;
  background-position: 56% 83%;
}

.offPump {
  background-color: #5b49491f !important;
}

.off_pump_img {
  width: 15.625rem;
  height: 3.75rem;
  background: #1A406F;
  opacity: 0.8;
  align-self: center;
  color: #F8C314;
  font-size: 1.3125rem;
  font-weight: bold;
  font-family: KHNPHDRegular;
  border: .125rem solid #00C0FF;
  text-align: center;
  line-height: 3.5625rem;
  letter-spacing: .3125rem;
}

.pump_name {
  color: rgb(255, 255, 255);
  font-size: 1.3125rem;
  line-height: 3.5625rem;
  letter-spacing: .3125rem;
  position: absolute;
  bottom: 0;
  right: 3.5rem;
  font-family: LAB디지털 !important;
}

.pump_name_unit {
  font-family: KHNPHDRegular;
  font-size: 1.0625rem;
  color: #c3eaff;
  margin-left: .125rem;
  line-height: 3.5625rem;
  letter-spacing: .3125rem;
  position: absolute;
  bottom: 0;
  right: .9375rem;
}

.carousel_vertical .carousel__track {
  height: 9.375rem;
}

.carousel__viewport {
  height: 100%;
}

.carousel_vertical .carousel__item {
  /* min-height: 12.5rem; */
  width: 100%;
  height: 9.375rem;
  background-color: var(--vc-clr-primary);
  color: var(--vc-clr-white);
  font-size: 1.25rem;
  border-radius: .5rem;
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
  background: url(@/assets/img/rectangle_box.png) no-repeat !important;
  background-size: contain !important;
  background-position: 100% 100%;
}

.blue_round {
  width: 6.5625rem;
  height: 6.25rem;
  color: #fff;
  text-shadow: 0 0 .5625rem #5cafff;
  font-family: "KHNPHDRegular";
  background: url(@/assets/img/00_top_roundline_b.png) no-repeat;
  background-size: 100%;
  background-position: center;
  display: flex;
  font-size: 1rem;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.green_round {
  width: 6.5625rem;
  height: 100%;
  color: #fff;
  text-shadow: 0 0 .5625rem #5cafff;
  font-family: "KHNPHDRegular";
  background: url(@/assets/img/00_top_roundline_g.png) no-repeat;
  background-size: 100%;
  background-position: center;
  display: flex;
  font-size: 1rem;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.box-bg {
  background: url(@/assets/img/dash_top.png) no-repeat !important;
  background-size: 100% 100% !important;
  width: 16.875rem;
  height: 6.25rem;
  padding: 0rem 1.5625rem;
  justify-content: unset;
}

.unit {
  font-size: 1rem;
  color: #a4ceed;
  font-family: "KHNPHDRegular";
  margin-left: .3125rem;
}

.content__value-box {
  width: 8.75rem;
  text-shadow: rgba(209, 250, 255, 0.5) 0rem 0rem .3125rem;
  font-size: 1.125rem;
  text-align: right;
  color: rgb(242, 251, 255);
  font-family: LAB디지털 !important;
  background-position: center center;
}

.content__text-box {
  width: px;
  background-size: 100% 1.25rem;
  background-position-y: bottom;
  text-shadow: 0 0 .5625rem #5cafff;
  font-family: KHNPHUotfR;
  font-size: 1rem;
  line-height: 1.5;
  text-align: left;
  color: #fff;
}

.animationTItle-two {
  width: 100%;
  display: flex;
  overflow: hidden;
  flex-direction: column-reverse;
  height: 3rem;
}

.animationTItle {
  width: 100%;
  display: flex;
  overflow: hidden;
  flex-direction: column-reverse;
  height: 1.5rem;
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