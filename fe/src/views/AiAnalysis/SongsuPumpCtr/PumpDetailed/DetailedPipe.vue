<template>
  <b-col xl="3" class="position-relative" style="height: 860px">
    <!-- 파이프 라인 -->
    <div class="position-absolute w-100" style="height: 77%; top: 155px; left: -15px;">
      <div :style="pipehidden" class="fL" style="width: 12%; height: 90%; margin-left: -3%;">
        <div class="fL pipeline-un"
          style=" width: 98%; height: 70%; background-size: 100% 30px; background-position: center; margin-top: -507%;">
          <div class="pipe_line_arrow blinking blinking1"></div>
        </div>
      </div>
      <div  class="fL" style="width: 12%; height: 100%; margin-left: -3%;">
        <div class="fL pipeline-un"
          style="width: 215%; height: 180%; background-size: 100% 30px; background-position: center; margin-left: -76%;">
          <div class="pipe_line_arrow blinking blinking1 fL" style="width: 50%"></div>
          <div class="pipe_line_arrow blinking blinking1 fL" style="width: 50%"></div>
        </div>
      </div>
      <div class="fL" style="width: 20%; height: 100%; margin-left: -8%;">
        <div :style="pipehidden" class="fL pipeline-y"
          style="width: 100%; height: 90%; background-size: 34px 101%;background-position: bottom;display: flex;flex-direction: column;margin-top: -14px; margin-left: -33%;">
          <div class="pipe_line_arrow blinking blinkingY1 fL"
            style="transform: rotate(90deg);height: 15%;position: relative;top: 45%;"></div>
          <div class="pipe_line_arrow blinking blinkingY1 fL"
            style="transform: rotate(90deg);height: 15%;position: relative;top: 45%;"></div>
          <div class="pipe_line_arrow blinking blinkingY1 fL"
            style="transform: rotate(90deg);height: 15%;position: relative;top: 45%;"></div>
        </div>
      </div>
      <div class="fL" style="width:50%;height: 97%;margin-left: -8%;">
        <div class="fL song-middle"
          style="width: 100%;height: 75%; background-size: 100% 100px;background-position: bottom;">
          <div style="width: 100%; height: calc(100% - 100px);"></div>
          <div style="width: 100%; height: 100px;">
            <PipeSubContent :data="branchPoint" />
          </div>
        </div>
        <div class="fL song-middle"
          style="width: 100%;height: 100px;margin-top: 35%;background-size: 100% 100px;background-position: center;">
          <div class="pipeline-un-y"
            style="position: absolute;width: 30px;height: 63px;margin-top:-62px; left: 43%; background-size: 100% 100%;">
          </div>
          <PipeSubContent :data="minimum" />
        </div>
      </div>
      <div class="fL" style="width: 9%;height: 100%;">
        <div class="fL" style=" width: 100%;   height: 75%; "></div>
        <div class="fL pipeline-un"
          style="width: 136%;height: 30%;background-size: 100% 30px;background-position: center;margin-left: -4%;">
          <div class="pipe_line_arrow blinking blinking1"></div>
        </div>
      </div>
    </div>
    <WaterGauge ref="gauge" />
    <!-- //물 수위 라인 -->
  </b-col>
</template>
<script>
import { addCommaNumber } from '@/util/addCommaNumber';
import PipeSubContent from '../PumpSmallComponents/PipeSubContent.vue';
import WaterGauge from '../PumpSmallComponents/WaterGauge.vue';
export default {
  components: {
    PipeSubContent,
    WaterGauge
  },
  props:{
    pipeShow:{
        type : Number
    },
  },
  data() {
    return {
      minimum: {
        title: '최소 요구 관압',
        value: 0
      },
      branchPoint: {
        title: '분기점 관압',
        value: 0
      },
      pipehidden:{}
    }
  },
  mounted() {
    // this.$refs.gauge.calculateHeight(0)//계산된 백분율 값을 넣으면 됨
    
    if(this.pipeShow == 1){
      this.pipehidden = { visibility: 'hidden'}
    }
  },
  methods: {

    getData(min_tube, bp_prsr) {
      this.minimum.value = addCommaNumber(min_tube)
      this.branchPoint.value = addCommaNumber(bp_prsr)
      if (Number(min_tube) == 0) {
        this.$refs.gauge.calculateHeight(0)//계산된 백분율 값을 넣으면 됨
      } else {
        const per = (Number(min_tube) / 80 * 100)
        this.$refs.gauge.calculateHeight(per)
      }
    }
  }
}
</script>
<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
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
    top: 3%;
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
</style>