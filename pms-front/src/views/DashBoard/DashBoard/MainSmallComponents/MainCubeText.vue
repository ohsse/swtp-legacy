<template>
  <div class="position-absolute">
    <div  @mouseover="hover" @mouseout="mouseout" class="contents-text position-absolute" :style="txtStyle">{{ cubeText }}</div>
    <div v-if="cubeSubText" class="contents-text position-absolute" :style="txtSubStyle">{{ cubeSubText }}</div>
    <img v-if="hakya" :src="backImg" :style="{ width: '100%', height: '100%', opacity: '00%' }"/>
    <img v-if="!isHover  && !hakya" :src="backImg" :style="{ width: '100%', height: '100%' }"  :class="mainhover" class=""/>
    <img v-if="isHover" :src="hoverImg" :style="{ width: '100%', height: '100%' }" class="up" />
  </div>
</template>

<script>
export default {
  props: [
    'txtStyle', 'cubeText', 'backImg', 'txtSubStyle', 'cubeSubText', 'hoverImg', 'hakya'
  ],
  data() {
    return {
      isHover: false,
      mainhover: 'building-visible'
    }
  },
  methods: {
    hover() {
      if (this.hoverImg) {
        this.isHover = true
        this.mainhover = 'buildNone'
        this.$emit('popupShow');
      } else {
        this.$emit('popupShow')
        this.isHover = false
      }

    },
    mouseout() {
      this.isHover = false
      this.$emit('popupHide');
    },
  },
}
</script>

<style>
.contents-text {
  width: 170px;
  height: 37px;
  opacity: 0.8;
  background-image: linear-gradient(to right, rgba(32, 80, 105, 0) 2%, rgba(2, 23, 52, 0.6) 36%, rgba(2, 23, 52, 0.6) 64%, rgba(32, 57, 105, 0));
  text-shadow: 0 0 9px #5cafff;
  font-size: 20px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 2;
  letter-spacing: normal;
  text-align: center;
  color: #fff;
  z-index: 10;
  cursor: pointer;
}

.building-visible {
  display: block !important;
}

.back {
  position: absolute;
}

.mode{
  mix-blend-mode: color-dodge;
}

.up {
  animation: building-up 1s ease-in-out 0s normal forwards;
}

@keyframes building-up {
  from {
    transform: translateY(0px)
  }

  to {
    transform: translateY(-30px)
  }
}

.buildNone {
  animation: move-down-building 0.8s ease-in-out 0s normal forwards;
  /* 새로운 애니메이션 적용 */
}

@keyframes move-down-building {
  from {
    transform: translateY(-30px)
  }

  to {
    transform: translateY(0px)
  }
}
</style>