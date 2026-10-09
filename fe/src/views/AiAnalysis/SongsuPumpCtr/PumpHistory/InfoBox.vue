<template>
  <b-col>
    <div class="fL pump_box">
      <div class="div-line-top"></div>
      <div class="div-small" style="align-items: center; justify-content: center;">
        <div class="chartbox" style="display: flex; flex-direction: column; justify-content: center; align-items: center;">
          <div :style="nameStyle" class="pump_name fontContent">{{ name }}</div>
          <div :style="percentStyle" class="chart_value fontData">
            {{ perData + '%' }}
          </div>
          <div class="pump_value fontContent">정격양정 :
            <span class="fontData">{{ data.DUTY_H }}</span>
          </div>
          <div class="pump_value fontContent">정격유량 :
            <span class="fontData">{{ value }} m³</span>
          </div>
        </div>

      </div>
      <div class="div-line-bottom"></div>
    </div>
  </b-col>
</template>
<script>
import { addCommaNumber } from '@/util/addCommaNumber'
export default {
  props: {
    data: {
      type: Object,
      required: true
    },
    perDatas: {
      type: Object,
      required: true
    },
    boxLength:{
      type: Number,
      required: true
    }
  },
  computed: {
    name() {
      return `${this.data.PUMP_NM}`;
    },
    value() {
      return addCommaNumber(this.data.DUTY_Q);
    },
    perData() {
      return this.perDatas[`${this.data.PUMP_GRP_NM}${this.data.PUMP_GRP_IDX}`];
    }
    
  },
  data(){
    return{
      nameStyle : null,
      percentStyle : null
    }
  },
  mounted(){

    if(this.boxLength == 1){
      this.nameStyle = {
        'font-size':'2rem',
        'height': '30%'
      }
      this.percentStyle = {
        'font-size':'4.5rem',
      }
    }
  }
}
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.date_design {
  background-color: #15284e;
  color: #fff;
  width: 130px;
  height: 28px;
  font-size: 13px;
  margin-left: 10px;
  font-family: KHNPHDRegular;
  border-radius: 5px;
}

.pump_box {
  height: 95%;
  /* padding-bottom: 20px; */
  /* /* padding: 15px 20px; */
  /* margin: 15px 20px; */
  width: 100%;
  padding: 0 0;
}

.chartbox {
  height: 100%;
  width: 100%;
  padding: 10px;
  background-position: center;
  align-content: center;
  justify-items: center;
  display: block;

}

.div_chart {
  background: url(@/assets/img/chart_line.png) no-repeat;
  background-size: 100% 100%;
  width: 182px;
  height: 182px;
  justify-content: center;
  align-items: center;
  display: flex;
  mix-blend-mode: color-dodge;

}

.chartbase {
  background: url(@/assets/img/chart_based.png) no-repeat;
  background-size: 100% 100%;
  width: 100px;
  height: 100px;
  display: flex;
}

.chart_value {
  position: relative;
  height: 100%;
  font-size: 38px;
  text-align: center;
  text-indent: 5px;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.pump_name {
  background: url(@/assets/img/pump/text_input_bg.png) no-repeat;
  background-size: 100% 100%;
  width: 100%;
  height: 40px;
  text-align: center;
  align-items: center;
  justify-content: center;
  display: flex;
  mix-blend-mode: color-dodge;
  text-shadow: 0 0 9px #5cafff;
  text-align: center;
  color: #c3eaff;
  position: unset;
  font-size: 1vw;
  padding: 0 5px;
}

.pump_value {
  text-align: center;
  margin-bottom: 5px;
}
</style>
