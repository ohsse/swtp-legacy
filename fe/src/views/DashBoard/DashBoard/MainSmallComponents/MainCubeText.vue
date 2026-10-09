<template>
  <div class="position-absolute">
    <div v-if="cubeText" @mouseover=" this.$emit('popupShow')" @mouseout="this.$emit('popupHide')" ref="cubeText"
      class="contents-text position-absolute" :style="txtStyle">{{
        cubeText }}
    </div>
    <div v-if="this.$area === 'hakya'" @mouseover="this.$emit('popupShow')" @mouseout="this.$emit('popupHide')"
      ref="cubeText" class="events-text position-absolute" :style="dynamicStyle">
    </div>
    <div v-if="cubeSubText" class="contents-text position-absolute" :style="txtSubStyle">{{ cubeSubText }}</div>
    <div v-if="cubeSubSecoundText" class="contents-text position-absolute" :style="txtSubSecoundStyle">{{
      cubeSubSecoundText }}</div>
    <img v-if="backImg" :src="backImg" class="building-visible" :style="{ width: '100%', height: '100%' }" />
    <!-- <img v-if="!isHover" :src="backImg" :style="{ width: '100%', height: '100%' }"  :class="mainhover"/>
        <img v-if="isHover" :src="hoverImg" :style="{ width: '100%', height: '100%' }" class="up" /> -->
  </div>
</template>

<script>
export default {
  props: [
    'txtStyle', 'cubeText', 'backImg', 'txtSubStyle', 'cubeSubText', 'hoverImg', 'fullName', 'cubeSubSecoundText', 'txtSubSecoundStyle'
  ],
  data() {
    return {
      isHover: false,
      mainhover: 'building-visible',
      eventWidth: '0px',
      eventHeight: '0px',
      dynamicStyle: {},
    }
  },
  mounted() {
    if (this.$area === 'hakya') {
      this.dynamicStyle = JSON.parse(JSON.stringify(this.txtStyle));
      this.dynamicStyle.top = (parseInt(this.txtStyle.top) - 40) + 'px'
      this.dynamicStyle.left = (parseInt(this.txtStyle.left) - 40) + 'px'
      this.dynamicStyle.width = '250px'
      this.dynamicStyle.height = '120px'
    }
  },
  methods: {
    goFac(cubeText) {
      const newUrl = `${window.location.origin}/FacUse?selected=${cubeText}`;
      window.location.href = newUrl;
    },
    hover() {

      // if (this.hoverImg) {
      this.isHover = true
      this.mainhover = 'buildNone'

      this.$emit('buildingUp');
      this.$emit('popupShow', this.fullName)
      // } else {
      //     this.isHover = false
      // }

    },
    mouseout() {
      this.isHover = false
      this.$emit('popupHide');
    },
  }
}
</script>

<style>
.contents-text {
  width: 170px;
  height: 37px;
  opacity: 1;
  background-image: linear-gradient(to right, rgba(32, 80, 105, 0) 2%, rgba(2, 23, 52, 0.6) 36%, rgba(2, 23, 52, 0.6) 64%, rgba(32, 57, 105, 0));
  text-shadow: 0 0 9px #5cafff;
  font-family: KHNPUotfR;
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

.events-text {
  width: 170px;
  height: 37px;
  opacity: 1;
  text-shadow: 0 0 9px #5cafff;
  font-family: KHNPUotfR;
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
  mix-blend-mode: color-dodge;
  /* width: 100%;
    height: 100%; */
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
  animation: move-down-building 1s ease-in-out 0s normal forwards;
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