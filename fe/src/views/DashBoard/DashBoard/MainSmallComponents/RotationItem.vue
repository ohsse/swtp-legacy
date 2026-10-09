<template>
  <div :class="className" :style="{ display: 'block' }">
    <div class="d-flex flex-column">
      <div class="flex_center_between justify_start">
        <div class="content__text-box" :style="{ width: '60px' }">{{ data.title }}</div>
        <div class="content__value-box">
          <span>{{ data.value }}</span><span class="unit">{{ data.unit }}</span>
        </div>
      </div>
      <div class="flex_center_between justify_start" v-if="data.sub">
        <div class="content__text-box">{{ data.sub.title }}</div>
        <div class="content__value-box">
          <span>{{ data.sub.value }}</span><span class="unit">{{ data.sub.unit }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: [
    'data'
  ],
  data() {
    return {
      className: this.data.sub ? 'fL animationItem-two' : 'fL animationItem'
    }
  },
  mounted() {
  }
};
</script>

<style>
.content__value-box {
  width: 140px;
  text-shadow: rgba(209, 250, 255, 0.5) 0px 0px 5px;
  font-size: 18px;
  text-align: right;
  color: rgb(242, 251, 255);
  font-family: LAB디지털 !important;
  background-position: center center;
}

.animationItem-two {
  -webkit-animation: scroll 12s infinite;
  animation: scroll 12s infinite;
}

.animationItem {
  -webkit-animation: scroll1 12s infinite;
  animation: scroll1 12s infinite;
}

.unit {
  font-size: 16px;
  color: #a4ceed;
  font-family: "KHNPHDRegular";
  margin-left: 5px;
}

@-webkit-keyframes scroll {
  0.0% {
    -webkit-transform: translateY(0px);
    transform: translateY(0px);
  }

  12.3% {
    -webkit-transform: translateY(0px);
    transform: translateY(0px);
  }

  24.9% {
    -webkit-transform: translateY(55px);
    transform: translateY(55px);
  }

  41.5% {
    -webkit-transform: translateY(55px);
    transform: translateY(55px);
  }

  58.1% {
    -webkit-transform: translateY(110px);
    transform: translateY(110px);
  }

  74.7% {
    -webkit-transform: translateY(110px);
    transform: translateY(110px);
  }

  91.7% {
    -webkit-transform: translateY(165px);
    transform: translateY(165px);
  }

  95.0% {
    -webkit-transform: translateY(165px);
    transform: translateY(165px);
  }
}

@keyframes scroll {
  0.0% {
    -webkit-transform: translateY(0px);
    transform: translateY(0px);
  }

  12.5% {
    -webkit-transform: translateY(0px);
    transform: translateY(0px);
  }

  25% {
    -webkit-transform: translateY(55px);
    transform: translateY(55px);
  }

  37.5% {
    -webkit-transform: translateY(55px);
    transform: translateY(55px);
  }

  50% {
    -webkit-transform: translateY(110px);
    transform: translateY(110px);
  }

  62.5% {
    -webkit-transform: translateY(110px);
    transform: translateY(110px);
  }

  75% {
    -webkit-transform: translateY(165px);
    transform: translateY(165px);
  }

  98% {
    -webkit-transform: translateY(165px);
    transform: translateY(165px);
  }

  100% {
    -webkit-transform: translateY(220px);
    transform: translateY(220px);
  }
}

@-webkit-keyframes scroll1 {
  0.0% {
    -webkit-transform: translateY(0px);
    transform: translateY(0px);
  }

  12.3% {
    -webkit-transform: translateY(0px);
    transform: translateY(0px);
  }

  24.9% {
    -webkit-transform: translateY(28px);
    transform: translateY(28px);
  }

  41.5% {
    -webkit-transform: translateY(28px);
    transform: translateY(28px);
  }

  58.1% {
    -webkit-transform: translateY(56px);
    transform: translateY(56px);
  }

  74.7% {
    -webkit-transform: translateY(56px);
    transform: translateY(56px);
  }

  91.7% {
    -webkit-transform: translateY(84px);
    transform: translateY(84px);
  }

  100% {
    -webkit-transform: translateY(84px);
    transform: translateY(84px);
  }

}

@keyframes scroll1 {
  0.0% {
    -webkit-transform: translateY(0px);
    transform: translateY(0px);
  }

  12.3% {
    -webkit-transform: translateY(0px);
    transform: translateY(0px);
  }

  24.9% {
    -webkit-transform: translateY(28px);
    transform: translateY(28px);
  }

  41.5% {
    -webkit-transform: translateY(28px);
    transform: translateY(28px);
  }

  58.1% {
    -webkit-transform: translateY(56px);
    transform: translateY(56px);
  }

  74.7% {
    -webkit-transform: translateY(56px);
    transform: translateY(56px);
  }

  91.7% {
    -webkit-transform: translateY(84px);
    transform: translateY(84px);
  }

  100% {
    -webkit-transform: translateY(84px);
    transform: translateY(84px);
  }

}
</style>
