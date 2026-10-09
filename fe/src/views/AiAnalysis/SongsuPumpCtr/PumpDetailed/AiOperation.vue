<template>
    <div class="mt-2" style="width: 100%; height:40%;">
        <div class="d-flex" style="mix-blend-mode: color-dodge;">
            <img class="blinking" :src="require(`@/assets/img/ai_arrow_right.png`)"
                style="width: 70px;height: 100%;background: url('@\assets\img\ai_arrow_right.png');background-size: 80% 60%;float:left; mix-blend-mode:color-dodge;" />
            <div
                style="position: absolute;width: 5%;height: 43%;display: flex;justify-content: center;align-items: center;flex-direction: column;">
                <span class="ai_text">AI 운영</span>
                <div class="toggleBG_BIG" style="  margin-top: 10px;">
                    <button class="toggleFG_BIG" @click="aiBtn">OFF</button>
                </div>
                <div id="autoban_area" style="opacity: 0.2; margin-top: 30px;">
                    <input type="radio" :name="'name'+nameSet" :id="ai_auto" value="ai_auto" aria-selected="true">
                    <label :for="ai_auto" class="detail_text" style="font-size: 18px;">자동</label><br>
                    <input type="radio" :name="'name'+nameSet" :id="ai_banauto" value="ai_banauto" checked>
                    <label :for="ai_banauto" class="detail_text" style="font-size: 18px;">반자동</label><br>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
export default {
    props:{
        nameSet : {
            type:Number
        }
    },
    methods: {
      aiBtn(){
        alert("HMI 화면 작화 이후 작업 예정")
      }
    },
}
</script>
<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.pipes_wrap {
  width: 95%;
  height: 98%;
  /* margin-left: 2%; */
  float: left;
}

.table-bg {
  background: url(@/assets/img/analysis/table_bg_03.png) no-repeat;
}

.r-circle {
  background: url(@/assets/img/r_circle.png) no-repeat;
  background-position: center;
}

.img_circle {
  background: url(@/assets/img/r_circle.png) no-repeat;
  background-position: center;
}

.circle-dot {
  max-height: 85%;
  border-style: dotted;
  border-color: #546b7d;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 2%;
  white-space: normal;
}

.ai_text {
  margin-right: 2%;
  font-size: 25px;
  font-family: 'KHNPHDBold';
  color: white;
  text-shadow: 0 0 10px #000000;
}

.detail_text {
  /* width: 70%; */
  text-shadow: 0 0 9px #5cafff;
  color: #c3eaff;
}

.pump_img {
  background: url(@/assets/img/peakcontrol/pump_peakcontrol.png) no-repeat;
  background-size: 28%;
  background-position: center;
  text-align: left;
  text-indent: 20%;
  mix-blend-mode: color-dodge;
}

.pump_area_h4 {
  height: calc(100%/ 4);
  width: calc(100%);
}

.pump_area_h35 {
  height: 52%;
  width: 100%;
}

.input_design {
  width: 70px;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  font-family: LABDigital;
  text-align: center;
}

.blinking1 {
  -webkit-animation: blink1 5s linear infinite;
  -moz-animation: blink1 5s linear infinite;
  animation: blink1 5s linear infinite;
}

.blinking {
  -webkit-animation: blink 3s linear infinite;
  -moz-animation: blink 3s linear infinite;
  animation: blink 3s linear infinite;
}

.blinkingY1 {
  -webkit-animation: blinkY1 5s linear infinite;
  -moz-animation: blinkY1 5s linear infinite;
  animation: blinkY1 5s linear infinite;
}

@-webkit-keyframes blinkY1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    top: 40%;
    transform: rotate(90deg);
  }

  24% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  36% {
    opacity: 1;
    transform: rotate(90deg);
  }

  48% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  60% {
    opacity: 0;
    top: 53%;
    transform: rotate(90deg);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@-moz-keyframes blinkY1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    top: 40%;
    transform: rotate(90deg);
  }

  24% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  36% {
    opacity: 1;
    transform: rotate(90deg);
  }

  48% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  60% {
    opacity: 0;
    top: 53%;
    transform: rotate(90deg);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@keyframes blinkY1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    top: 40%;
    transform: rotate(90deg);
  }

  24% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  36% {
    opacity: 1;
    transform: rotate(90deg);
  }

  48% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  60% {
    opacity: 0;
    top: 53%;
    transform: rotate(90deg);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@-webkit-keyframes blink1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    transform: translateX(-10px);
  }

  24% {
    opacity: 0.5;
    transform: translateX(-5px)
  }

  36% {
    opacity: 1;
    transform: translateX(0px);
  }

  48% {
    opacity: 0.5;
    transform: translateX(5px);
  }

  60% {
    opacity: 0;
    transform: translateX(10px);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@-moz-keyframes blink1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    transform: translateX(-10px);
  }

  24% {
    opacity: 0.5;
    transform: translateX(-5px)
  }

  36% {
    opacity: 1;
    transform: translateX(0px);
  }

  48% {
    opacity: 0.5;
    transform: translateX(5px);
  }

  60% {
    opacity: 0;
    transform: translateX(10px);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@keyframes blink1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    transform: translateX(-10px);
  }

  24% {
    opacity: 0.5;
    transform: translateX(-5px)
  }

  36% {
    opacity: 1;
    transform: translateX(0px);
  }

  48% {
    opacity: 0.5;
    transform: translateX(5px);
  }

  60% {
    opacity: 0;
    transform: translateX(10px);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

.pipe_line_arrow {
  background: url(@/assets/img/dashboard/water.png) no-repeat;
  width: 100%;
  height: 100%;
  mix-blend-mode: color-dodge;
  background-position: center;
}

.pipeline-un {
  background: url(@/assets/img/analysis/pipeline_un.png) no-repeat;
}

.pipeline-y {
  background: url(@/assets/img/ai_song/pipeline_y.png) no-repeat;
}

.song-middle {
  background: url(@/assets/img/ai_song/middle.png) no-repeat;
}

.pipeline-un-y {
  background: url(@/assets/img/ai_song/pipeline_un_y.png) no-repeat;
}

.pipe_big_gauge {
  background: url(@/assets/img/ai_song/pipe_big.png) no-repeat;
  width: 100%;
  height: 60%;
  background-size: 100% 91%;
  float: left;
}

.pipe_big_background {
  background: url(@/assets/img/ai_song/pipe_big.png) no-repeat;
  width: 20%;
  height: 100%;
  background-size: 100% 90%;
  background-position: center;
  float: right;
  display: flex;
  align-items: flex-end;
}

.sub_content_middle_value {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50%;
  width: 100%;
}

.sub_input_box {
  width: 70px;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  font-family: LABDigital;
  text-align: center;
  margin-right: 2%;
  float: left;
}

.sub_content_font {
  text-shadow: 0 0 9px #5cafff;
  font-size: 14px;
  font-family: KHNPHDRegular;
  letter-spacing: normal;
  color: #c3eaff;
  align-self: center;
  padding: 0 2% 0 0;
  float: left;
}

.sub_content_middle_value {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50%;
  width: 100%;
}

.pipe_background {
  height: calc(100% / 14);
  background: url(@/assets/img/ai_song/one_pump.png) no-repeat;
  background-size: 100% 100%;
}

.pipes_wrap {
  width: 100%;
  height: 100%;
  /* margin-left: 2%; */
  /* padding: 1% 2%; */
  float: left;
}

.pipe2_wrap {
  height: 50%;
}

.pipe_wrap {
  display: flex;
  width: 100%;
  height: 90%;
}

.pipe_left_wrap {
  width: 48%;
  height: calc(100% - 10px);
  margin-top: 5px;
  display: flex;
  flex-direction: column;
}

.pipe_left_line1 {
  height: calc(100% / 2);
  width: calc(100% - 27px);
  margin: 0 10px;
}

.pipe_left_line1-1 {
  width: calc(27% + 4px);
  height: calc(100% - 4px);
  float: left;
}

.pipe_left_line1-3 {
  height: calc(100% - 4px);
  font-size: 15px;
  line-height: 1.3;
  border-radius: 3px;
  float: right;
  width: 27%;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  text-align: center;
  font-family: 'LABDigital';
}

.pipe_left_line3 {
  height: calc(100% / 2);
  width: calc(100% - 27px);
  margin: 0 10px;
}

.pipe_left_line3-1 {
  height: calc(100% - 4px);
  font-size: 15px;
  line-height: 1.3;
  border-radius: 3px;
  float: left;
  width: 27%;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  text-align: center;
  font-family: 'LABDigital';
}

.pipe_left_line3-3 {
  height: calc(100% - 4px);
  font-size: 15px;
  line-height: 1.3;
  border-radius: 3px;
  float: right;
  width: 27%;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  text-align: center;
  font-family: 'LABDigital';
}

.pipe_center {
  width: 14%;
  background: url(@/assets/img/ai_song/tank.png) no-repeat;
  background-size: 100% 100%;
  background-position: -6px 0px;
}

.pipe_right_water {
  width: 12%;
  margin-left: 1%;
  height: calc(92% - 10px);
}

.pipe_right_wrap {
  width: 20%;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pipe3_wrap {
  height: calc(100% / 3);
}

.pipe_right_line1 {
  height: 40%;
  width: 100%;
  color: #fff;
  line-height: 1.5;
  font-family: 'KHNPHDRegular';
  font-size: 14px;
  margin-right: 770%;
  margin-top: 4px;
  text-shadow: 0 0 9px #5cafff;
  color: #c3eaff;
}

.pipe_right_line2 {
  height: 30%;
  width: 60%;
  font-size: 15px;
  line-height: 1.3;
  text-align: right;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  padding-right: 10px;
  border-radius: 3px;
  font-family: 'LABDigital';
}

.pipe2_background {
  height: calc(100% / 14 + 100% / 14);
  background: url(@/assets/img/ai_song/two_pump.png) no-repeat;
  background-size: 100% 100%;
}

.pipe3_background {
  height: calc(100% / 14 + 100% / 14 + 100% / 14);
  background: url(@/assets/img/ai_song/two_pump.png) no-repeat;
  background-size: 100% 100%;
}
.loading-container {
  position: fixed;
  /* 절대 위치 설정 */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  /* 반투명한 배경 */
  z-index: 9999;
  /* 다른 요소 위에 표시하기 위한 z-index 설정 */
  display: flex;
  justify-content: center;
  /* 수평 가운데 정렬 */
  align-items: center;
}
</style>
