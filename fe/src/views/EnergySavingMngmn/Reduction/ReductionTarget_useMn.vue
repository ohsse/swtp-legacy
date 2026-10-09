<template>
  <b-col class="table_s">
    <subTitle :title="title"></subTitle>
    <div class="bottom_bar"></div>
    <div class="bottom_middle_area">
      <div class="bottom_middle_gauge" v-bind:style="{ height: '155px', overflow: 'hidden' }">
        <div id="chart" class="pie_chart1"></div>
      </div>
      <img src="@/assets/img/gauge_f.png" class="bottom_middle_gauge" alt="게이지 배경 이미지" />
      <div class="bottom_cir"></div>
    </div>
    <div id="thisMonthPer" class="bottom_val">{{ percent }} %</div>
    <div class="bottom_line_val">
      <div
        v-bind:style="{ color: 'white', textAlign: 'center', fontSize: '20px', fontWeight: 'bolder', fontFamily: 'KHNPHUotfR' }">
        사용량&nbsp;
        <span id="thisMonthUsage">{{ useVal }} kWh</span>
        &nbsp;목표량&nbsp;&nbsp;
        <span id="thisMonthGoal">{{ targetVal }} kWh</span>
      </div>
    </div>
  </b-col>
</template>

<script>
import { addCommaNumber } from "@/util/addCommaNumber";
import subTitle from "@/views/EnergySavingMngmn/BottomTitle.vue"
export default {
  components: {
    subTitle
  },
  props: {
    title: {
      type: String,
      required: true
    }

  },
  data() {
    return {
      percent: 0,
      deg: 0,
      useVal: 0,
      targetVal: 0
    }
  },
  methods: {
    percentMake(useVal, targetVal) {
      this.useVal = addCommaNumber(useVal);
      this.targetVal = addCommaNumber(targetVal)
      let returnVal = useVal / targetVal * 100;
      if (returnVal != 0) {
        returnVal = parseFloat(returnVal.toFixed(1))
      } else {
        returnVal = parseFloat(returnVal)
      }
      this.deg = this.percentageToDegrees(returnVal)
      this.percent = addCommaNumber(returnVal)
      this.makePieChart()
    },
    percentageToDegrees(percentage) {
      if (percentage >= 0 && percentage <= 100) {
        return (percentage / 100) * 180;
      } else if (percentage >= 100) {
        return 180;
      } else {
        return 0
      }
    },
    makePieChart() {
      document.getElementById("chart").style.transform = `translate(-50%, -50%) rotate( ${this.deg}deg )`;
    }
  }
}
</script>


<style scoped>
.bottom_middle_gauge {
  width: 310px;
  opacity: 0.5;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  position: absolute;
}

.pie_chart1 {
  width: 305px;
  height: 305px;
  transition: 0.3s;
  display: block;
  position: absolute;
  top: 100%;
  border-radius: 50%;
  line-height: 200px;
  font-size: 30px;
  transform: translate(-50%, -50%) rotate(0deg);
  z-index: 1;
  left: 50%;
  background: linear-gradient(to top, rgba(72, 156, 242, 0.5) 50%, rgba(0, 0, 0, 1) 50%);
}

.bottom_title {
  width: 100%;
  height: 30%;
  font-size: 174%;
  color: white;
  text-align: center;
  line-height: 150px;
  font-family: 'KHNPHDRegular';
}

.bottom_bar {
  width: 3%;
  height: 45%;
  float: left;
  background: url(/src/assets/img/image_01.png);
  background-repeat: no-repeat;
}

.bottom_line_val {
  width: 96%;
  position: absolute;
  bottom: 40px;
}

.bottom_middle_area {
  width: 100%;
  height: 110px;
  position: relative;
  top: 28px;
}

.bottom_cir {
  background: #173770;
  display: block;
  position: absolute;
  top: 87%;
  left: 50%;
  width: 156px;
  height: 80px;
  border-radius: 150px 150px 0 0;
  text-align: center;
  line-height: 200px;
  font-size: 30px;
  transform: translate(-50%, -50%);
  z-index: 1;
}

.bottom_val {
  width: 98%;
  color: white;
  font-size: 44px;
  text-align: center;
  z-index: 1;
  position: absolute;
  font-family: 'LAB디지털';
}
</style>