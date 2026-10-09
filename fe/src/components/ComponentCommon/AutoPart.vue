<template>
  <ui class="container" style="display: flex; width:150px">
    <li :class="autoCss" :style="{ fontSize: '13px', marginRight: '20px' }">자동</li>
    <li :class="halfAutoCss" :style="{ fontSize: '13px' }">반자동</li>
  </ui>
</template>

<script>

export default {
  props: ['autoData'],
  data() {
    let num = 0;
    return {
      num,
      autoCss: '',
      halfAutoCss: ''
    }
  },
  mounted() {
    if (this.autoData != undefined) {
      this.pumpOnOff(this.autoData)
    }
  },
  updated() {
  },
  methods: {
    pumpOnOff(autoData) {
      // 0 일때 자동, 1일면 반자동 활성화 하기 
      if (autoData === 0) {
        this.autoCss = 'activeCss'
        this.halfAutoCss = 'noActiveCss'
      } else if (autoData === 1) {
        this.autoCss = 'noActiveCss'
        this.halfAutoCss = 'activeCss'
      }
      else {
        this.autoCss = 'noActiveCss'
        this.halfAutoCss = 'noActiveCss'
      }
    },
  },
}
</script>

<style>
.container {
  display: inline-flex;
  font-family: KHNPHDRegular;
}

.halfCss {
  margin-left: 20px;
}

.activeCss {
  color: white;
}

.noActiveCss {
  color: gray;
}
</style>