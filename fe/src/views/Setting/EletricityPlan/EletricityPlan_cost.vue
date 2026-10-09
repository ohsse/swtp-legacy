<template>
  <b-col class="" :style="{height: '370px', paddingLeft: '3rem', paddingRight: '1rem' }">
    <b-row :style="{height: '280px'}">
      <b-col class="div_border mx-2">
        <SmallTitle :title="'기본요금'" />
        <div class="text-center mt-3" :style="{height: '185px'}">
          <input id="base_rate" type="text" class="top_textinput" v-model="BASE_RATE"><span class="topUnitFont">원</span>
          <div class="value_bottom_img"></div>
        </div>
      </b-col>
      <b-col class="div_border mx-2">
        <SmallTitle :title="'경부하'" />
        <div class="text-center mt-3" :style="{height: '185px'}">
          <input id="rate_L" type="text" class="top_textinput" v-model="L_RATE"><span class="topUnitFont">원</span>
          <div class="value_bottom_img"></div>
        </div>
      </b-col>
      <b-col class="div_border mx-2">
        <SmallTitle :title="'중간부하'" />
        <div class="text-center mt-3" :style="{height: '185px'}">
          <input id="rate_M" type="text" class="top_textinput" v-model="M_RATE"><span class="topUnitFont">원</span>
          <div class="value_bottom_img"></div>
        </div>
      </b-col>
      <b-col class="div_border mx-2">
        <SmallTitle :title="'최대부하'" />
        <div class="text-center mt-3" :style="{height: '185px'}">
          <input id="rate_H" type="text" class="top_textinput" v-model="H_RATE"><span class="topUnitFont">원</span>
          <div class="value_bottom_img"></div>
        </div>
      </b-col>
    </b-row>
  </b-col>
  </template>

<script>
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
export default {
  components : {SmallTitle},
  data() {
    return {
      BASE_RATE : '',
      L_RATE : '',
      M_RATE : '',
      H_RATE : '',
    }
  },
  methods:{
    setCost(selectRate){
      this.BASE_RATE = selectRate.BASE_RATE
      this.L_RATE = selectRate.L_RATE
      this.M_RATE = selectRate.M_RATE
      this.H_RATE = selectRate.H_RATE
    },
  }
}

</script>

<style>
.season_btn {
  height: 33px;
  padding-top: 3px;
  padding-bottom: 3px;
  border: solid 1px #b4dffa;
  background-color: rgba(139, 194, 240, 0.25);
}
.season_btn_font {
    text-shadow: 0 0 9px #5cafff;
    letter-spacing: normal;
    color: #fff;
    font-family: 'KHNPHDRegular';
}
.ai-arrow-right {
  position: relative;
}
.ai-arrow-right::after {
  display: inline;
  content: '';
  width: 40px;
  height: 318px;
  position: absolute;
  top: 18%;
  right: -40px;
  background: url(@/assets/img/ai_arrow_right.png);
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  -webkit-animation: blink 3s linear infinite;
  -moz-animation: blink 3s linear infinite;
  animation: blink 3s linear infinite;
}
.div_title {
  height: 40px;
  background: url(@/assets/img/title_bar.png) no-repeat;
  background-size: 100% 100%;
  color: #ffffff;
  font-family: KHNPHDRegular;
  font-size: 19px;
  text-shadow: 0 0 10px #000;
  line-height: 2;
  text-indent: 20px;
}
.div_border {
  background-image: url(@/assets/img/box_bg_small.png);
  background-size: 100% 100%;
}
.list-custom-group.list-group .list-group-item {
    border: 0;
    background: transparent;
    color: white;
    text-align: center;
    height: 57px;
    line-height: 42px;
}
.list-custom-group.list-group .list-group-item.active {
  background: url(@/assets/img/pump/text_input_bg.png);
  background-size: 100% 100%;
  background-repeat: no-repeat;
}
.bigListFont {
  font-family: KHNPHDRegular;
  font-size: 21px;
  color: white;
  text-shadow: 0 0 9px #5cafff;
}
.bottomContentsImg {
  height: calc(100% / 6);
  background: url(@/assets/img/one_pump.png) no-repeat;
  background-size: 100% 100%;
}
.top_textinput {
  height: 21%;
  width: 56%;
  display: inline-block;
  margin-top: 51px;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  font-family: LABDigital;
  text-align: center;
  font-size: 20px;
  letter-spacing: 4px;
}
.topUnitFont {
  color: #ffffff;
  font-family: 'KHNPHDRegular';
  font-size: 18px;
  text-shadow: 0 0 10px #000;
  margin-left: 10px;
}
.value_bottom_img {
    background-image: url(@/assets/img/bottom_aura.png);
    background-size: 100% 100%;
    background-repeat: no-repeat;
    height: 24%;
    width: 94%;
    display: inline-block;
}
.comboFont {
  color: #ffffff;
  font-family: 'KHNPHDRegular';
  font-size: 15px;
  text-shadow: 0 0 10px #000;
  margin-right: 30px;
  line-height: 47px;
}
/* 셀렉트 박스 (다크테마) */
.comboBox {
  background-color: #15284e;
  color: #fff;
  width: 169px;
  font-size: 15px;
  font-family: KHNPHDRegular;
  margin-top: 5px;
}
.k-select {
  border-color: #489cf2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.k-icon, .k-tool-icon {
  color: #489cf2;
  cursor: pointer;
  position: relative;
  display: inline-block;
  overflow: hidden;
  width: 1em;
  height: 1em;
  text-align: center;
  vertical-align: middle;
  background-image: none;
  font: 16px/1 WebComponentsIcons;
  speak: none;
  font-variant: normal;
  text-transform: none;
  text-indent: 0;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: inherit;
}
.k-icon:before {
  margin: auto;
  width: 1em;
  height: 1em;
  line-height: 1;
  display: inline-block;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
}
</style>