<template>
  <div class="fullscreen no-pointer-events q-dialog--modal">
    <div class="q-dialog__backdrop fixed-full"></div>
    <div class="q-dialog__inner flex no-pointer-events fixed-full flex-center">
      <div class="q-card ">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"
            style="position: absolute; right: 30px; z-index:99; cursor:pointer;" @click="$emit('onlyColse')">
          <path fill-rule="evenodd" clip-rule="evenodd" d="M3.3334 16.6667C3.00796 16.3413 3.00796 15.8137 3.3334 15.4882L15.4882 3.3334C15.8137 3.00796 16.3413 3.00796 16.6667 3.3334C16.9922 3.65883 16.9922 4.18647 16.6667 4.51191L4.51191 16.6667C4.18647 16.9922 3.65883 16.9922 3.3334 16.6667Z" fill="#79869A"/>
          <path fill-rule="evenodd" clip-rule="evenodd" d="M16.6666 16.6667C16.992 16.3413 16.992 15.8137 16.6666 15.4882L4.51178 3.3334C4.18635 3.00796 3.65871 3.00796 3.33327 3.3334C3.00783 3.65883 3.00783 4.18647 3.33327 4.51191L15.4881 16.6667C15.8135 16.9922 16.3412 16.9922 16.6666 16.6667Z" fill="#79869A"/>
          </svg>
        <div class="q-card__section q-card__section--vert">
          <div class="text-h6" v-if="alarmData[0].ALR_TYP == 'PEAK'">전력피크알림</div>
          <div class="text-h6" v-if="alarmData[0].ALR_TYP == 'PUMP'">펌프제어알림</div>
        </div>
        <div class="q-card__section q-card__section--vert">
          확인 시간 : {{ alarmData[0].ALR_TIME }}
        </div>
        <div class="q-card__section q-card__section--vert" v-html="formatMessage(alarmData[0]?.MSG)">
        </div>
        <div class="q-card__section q-card__section--vert">
          {{ alarmData[0].ALR_TYP == 'PEAK' ? '전력피크페이지로 이동하시겠습니까?' : '' }} 
        </div>
        <button @click="$emit('allAlarmClose')" v-if="alarmData[0].ALR_TYP === 'PEAK'"
          style="width: 100px; border-radius: 5px; float: right; margin: 10px 20px 5px 0;" class="confirm-btn"
          type="button" role="button">
          <span class="block">취소</span>
        </button>
        <button @click="$emit('allPageAlarm', true)"
          style="width: 100px; border-radius: 5px; float: right; margin: 10px 20px 5px 0;" class="confirm-btn"
          type="button" role="button">
          <span class="block">확인</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['abnormalAlarm'],
  data() {
    let alarmData = this.abnormalAlarm;
    return {
      alarmData,
    }
  },
  watch: {
    abnormalAlarm(newVal) {
      this.alarmData = newVal;
    }
  },
  mounted() {

  },
  methods: {
    formatMessage(msg) {
      return msg ? msg.replace(/\|/g, '<br>') : '';
    }
  },
}
</script>

<style>
.no-pointer-events,
.no-pointer-events--children,
.no-pointer-events--children * {
  pointer-events: none !important
}

.fullscreen {
  height: 100%
}

.fixed-full,
.fullscreen {
  position: fixed
}

.fullscreen {
  z-index: 6000;
  border-radius: 0 !important;
  max-width: 100vw;
  max-height: 100vh
}

.fixed-full,
.fullscreen {
  top: 0;
  right: 0;
  bottom: 0;
  left: 0
}

.q-dialog__backdrop {
  z-index: -1;
  pointer-events: all;
  outline: 0;
  background: rgba(0, 0, 0, .4)
}

.q-dialog__inner {
  outline: 0
}

.q-dialog__inner>div {
  pointer-events: all;
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  will-change: scroll-position;
  border-radius: 4px
}

.q-dialog__inner>.q-card>.q-card__actions .q-btn--rectangle {
  min-width: 64px
}

.q-dialog__backdrop {
  z-index: -1;
  pointer-events: all;
  outline: 0;
  background: rgba(0, 0, 0, .4)
}

body.platform-android:not(.native-mobile) .q-dialog__inner--minimized>div,
body.platform-ios .q-dialog__inner--minimized>div {
  max-height: calc(100vh - 108px)
}

body.q-ios-padding .q-dialog__inner {
  padding-top: 20px !important;
  padding-top: env(safe-area-inset-top) !important;
  padding-bottom: env(safe-area-inset-bottom) !important
}

body.q-ios-padding .q-dialog__inner>div {
  max-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom)) !important
}

@media (max-width:599.98px) {

  .q-dialog__inner--bottom,
  .q-dialog__inner--top {
    padding-left: 0;
    padding-right: 0
  }

  .q-dialog__inner--bottom>div,
  .q-dialog__inner--top>div {
    width: 100% !important
  }
}

@media (min-width:600px) {
  .q-dialog__inner--minimized>div {
    max-width: 560px
  }
}

.flex,
.row {
  display: flex;
  flex-wrap: wrap
}

.column.inline,
.flex.inline,
.row.inline {
  display: inline-flex
}

.flex-center,
.justify-center {
  justify-content: center
}

.flex-center,
.items-center {
  align-items: center
}

.q-dialog__inner>.q-card>.q-card__actions .q-btn--rectangle {
  min-width: 64px
}

.q-btn-toggle,
.q-card {
  position: relative
}

.q-card {
  box-shadow: 0 1px 5px rgba(0, 0, 0, .2), 0 2px 2px rgba(0, 0, 0, .14), 0 3px 1px -2px rgba(0, 0, 0, .12);
  border-radius: 4px;
  vertical-align: top;
  background: #fff
}

.q-card>div:first-child,
.q-card>img:first-child {
  border-top: 0;
  border-top-left-radius: inherit;
  border-top-right-radius: inherit
}

.q-card>div:last-child,
.q-card>img:last-child {
  border-bottom: 0;
  border-bottom-left-radius: inherit;
  border-bottom-right-radius: inherit
}

.q-card>div:not(:first-child),
.q-card>img:not(:first-child) {
  border-top-left-radius: 0;
  border-top-right-radius: 0
}

.q-card>div:not(:last-child),
.q-card>img:not(:last-child) {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0
}

.q-card>div {
  border-left: 0;
  border-right: 0;
  box-shadow: none
}

.q-card--bordered {
  border: 1px solid rgba(0, 0, 0, .12)
}

.q-card__section {
  position: relative
}

.q-card__section--vert {
  padding: 16px
}

.q-card__actions {
  padding: 8px;
  align-items: center
}

.q-card__actions .q-btn--rectangle {
  padding: 0 8px
}

.q-card__actions--horiz>.q-btn-group+.q-btn-item,
.q-card__actions--horiz>.q-btn-item+.q-btn-group,
.q-card__actions--horiz>.q-btn-item+.q-btn-item {
  margin-left: 8px
}







.q-card {
  background: url('@/assets/alert_box.png') !important;
  background-size: 100% 100% !important;
  padding: 30px;
  color: #b4dffb !important;
  font-family: 'KHNPHUotfR', sans-serif !important;
  font-size: 18px !important;
  line-height: 28px ip !important;
}

.large {
  font-size: 20px;
}

.text-h6 {
  font-size: 24px;
  color: #b4dffb;
}

.confirm-btn {
  color: #fff !important;
  border: 1px solid #b4dffa !important;
  background: rgba(239, 194, 240, 0.25) !important;
}

.bg-default {
  background: url('@/assets/alert_box.png') !important;
  background-size: 100% 100% !important;
  color: #b4dffb !important;
  font-family: 'KHNPHUotfR', sans-serif !important;
}
</style>