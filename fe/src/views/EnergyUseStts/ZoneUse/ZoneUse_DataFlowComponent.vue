<template>
  <b-col :xl="items[0].isFirst || items[0].isLast ? boxSize : ''"
    :class="items[0].isFirst ? 'left_box' : items[0].isLast ? 'right_box' : 'middle_box'">
    <b-row>
      <b-col xl="5" v-if="items[0].isFirst">
        <div class="box" :style="{
    margin: '37px 0px 13px 0',
    height: 'calc(50% - 80px)',
    padding: '0 15px',
    width: 'calc(100% - 0)',
  }">
          <!-- class="contents-box-other" -->
          <div class="bottom-information">순시전력</div>
          <div class="bottom-information">전력량</div>
          <div class="bottom-information">시간당 최대전력</div>
          <div class="bottom-information">최대 전력 시간대</div>
        </div>
      </b-col>
      <b-col :xl="items[0].isFirst || items[0].isLast ? '7' : ''">
        <div class="m-auto h-100">
          <ZoneUseComponent isUpper="true" :items="items[0]" :data="this.data" @emitModal="emitModal" />
          <ZoneUseComponent :items="items[1]" :data="this.data" @emitModal="emitModal" />
        </div>
      </b-col>
      <b-col xl="5" v-if="items[0].isLast">
        <!-- contents-box-other -->
        <div class="box" style="
          margin: 60px 0 0 0;
          height: calc(50% - 60px);
          padding: 0 0 0 25px;
          width: calc(100% - 25px);
        ">
          <div class="box-top-title">총 순시 전력</div>
          <div class="box-bottom">
            <div class="box-bottom__value">{{ this.commaSunsi }}</div>
            <div class="box-bottom__sunsi_unit">kW</div>
          </div>
        </div>
        <div class="box" style="
        margin: 30px 0 0 0;
        height: calc(50% - 60px);
        padding: 0 0 0 25px;
        width: calc(100% - 25px);
      ">
          <div class="box-top-title">총 전력량</div>
          <div class="box-bottom">
            <div class="box-bottom__value">{{ this.commaTotal }}</div>
            <div class="box-bottom__unit">kWh</div>
          </div>
        </div>
      </b-col>
    </b-row>

  </b-col>
</template>

<script>
import ZoneUseComponent from "@/views/EnergyUseStts/ZoneUse/ZoneUseComponent.vue"
import { addCommaNumber } from "@/util/addCommaNumber";
export default {
  components: {
    ZoneUseComponent,
  },
  props: [
    'items',
    'total',
    'data',
    'length',
    'sunsiTotal'
  ],
  data() {
    return {
      commaTotal: this.total,
      boxSize: 4
    }
  },
  mounted() {
    if (this.length == 2) {
      this.boxSize = 6
    }
    else if (this.length == 3) {
      this.boxSize = 5
    }
    else if (this.length == 6 || this.length == 5 || this.length == 7) {
      this.boxSize = 3
    }
    this.setComma()
  },
  methods: {
    setComma() {
      this.commaTotal = addCommaNumber(this.total.toFixed(2))
      this.commaSunsi = addCommaNumber(this.sunsiTotal.toFixed(2))
    },
    emitModal(title) {
      this.$emit('showChartModal', title);
    },
  }
};
</script>

<style>
.contents {
  display: flex;
  width: 100%;
  height: calc(60% - 90px);
}

.left_box {
  background: url(@/assets/img/left_box.png);
  background-size: 100% 100%;
}

.middle_box {
  background: url(@/assets/img/middle_box.png);
  background-size: 100% 100%;
}

.right_box {
  background: url(@/assets/img/right_box.png);
  background-size: 100% 100%;
}

.contents-container .box {
  display: flex;
  flex-flow: column;
  align-items: center;
  width: 100%;
  height: 50%;
  margin: -26px 0 55px 0;
}

.contents-container .box .box-contents-title {
  height: 32px;
  background: url(@/assets/img/title_bar.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: luminosity;
  color: #ffffff;
  font-family: "KHNPHDBold";
  font-size: 18px;
  text-shadow: 0 0 10px #000;
  line-height: 2;
  text-indent: 3%;
  width: 100%;
  text-align: center;
}

.contents-container .box .box-value-contents {
  display: flex;
  width: 100%;
  height: 27px;
}

.contents-container .box .box-value-contents__value {
  width: 50%;
  text-shadow: 0 0 9px #5cafff;
  font-size: 19px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.56;
  letter-spacing: normal;
  text-align: right;
  color: #fff;
  font-family: "LAB디지털" !important;
}

.contents-container .box .box-value-contents__unit {
  width: 25%;
  margin-left: 15.5px;
  font-size: 18px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.79;
  letter-spacing: normal;
  text-align: left;
  color: #a4ceed;
}

.date_text {
  color: #c3eaff !important;
  font-size: 18px !important;
}

.box_bottom {
  justify-content: flex-end;
  margin: -17px 0 -15px 0 !important;
}

.chartIcon {
  background-image: url(@/assets/img/chartIcon.png);
  background-size: 100% 100%;
  width: 35px;
  height: 25px;
  margin-top: 5px;
  cursor: pointer;
}

.contents-container .box .box-top-title {
  text-shadow: 0 0 9px #5cafff;
  font-size: 20px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.56;
  letter-spacing: normal;
  text-align: right;
  width: 85%;
  color: #fff;
}

.contents-container .box .box-bottom {
  display: flex;
  width: 100%;
  height: 43px;
  margin-top: 10px;
  -o-object-fit: contain;
  object-fit: contain;
  border: solid 1px rgb(72 156 242);
  border-radius: 5px;
}

.contents-container .box .box-bottom__value {
  width: 100%;
  text-shadow: 0 0 5px rgb(209 250 255/ 50%);
  font-family: "LAB디지털" !important;
  font-size: 24px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.6;
  letter-spacing: normal;
  text-align: right;
  color: #ffffff;
}

.contents-container .box .box-bottom__unit {
  margin: 0 -35px 0 10px;
  font-size: 16px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 2.7;
  letter-spacing: normal;
  text-align: left;
  color: #417db9;
}

.box-bottom__sunsi_unit {
  margin: 0 -35px 0 20px;
  font-size: 16px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 2.7;
  letter-spacing: normal;
  text-align: left;
  color: #417db9;
}

.contents-container .box .bottom-information {
  width: 100%;
  background-position-y: center;
  background-position-x: 20px;
  text-shadow: 0 0 9px #5cafff;
  font-size: 16px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.7;
  letter-spacing: normal;
  text-align: right;
  color: #ffffff;
}
</style>
