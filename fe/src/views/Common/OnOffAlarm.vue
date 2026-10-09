<template>
  <div class="fullscreen no-pointer-events q-dialog--modal">
    <div class="q-dialog__backdrop fixed-full"></div>
    <div class="q-dialog__inner flex no-pointer-events fixed-full flex-center">
      <div class="q-card ">
        <div class="q-card__section q-card__section--vert" style="margin-top:10px">
          <div class="text-h6">펌프 상태가 변경되었습니다.</div>
        </div>
        <div class="q-card__section q-card__section--vert" style="margin-top:10px">
          <div class="text-h2">확인시간: {{ alarmTime }}</div>
        </div>
        <div style="white-space: nowrap;">
          <div v-if="message1 != ``" class="q-card__section q-card__section--vert q-pt-none"
            style="display: inline-flex;">
            <input type="checkbox" v-if="this.$store.state.mode0 == 1" v-model="pump_grp" value="1">
            {{ message1[0] }}
            <AiMode ref="firAimode" v-if="this.$store.state.mode0 == 1" :isPopup="true" :index="1"
              style="margin-left:10px" />
          </div>
        </div>
        <div v-if="message1 != ``" class="q-card__section q-card__section--vert q-pt-none">
          <div v-html="message1[1]"></div>
        </div>
        <div style="white-space: nowrap;">
          <div v-if="message2 != ``" class="q-card__section q-card__section--vert q-pt-none"
            style="display: inline-flex;">
            <input type="checkbox" v-if="this.$store.state.mode1 == 1" v-model="pump_grp" value="2">
            {{ message2[0] }}
            <AiMode ref="secAimode" v-if="this.$store.state.mode1 == 1" :isPopup="true" :index="2"
              style="margin-left:10px" />
          </div>
        </div>
        <div v-if="message2 != ``" class="q-card__section q-card__section--vert q-pt-none">
          <div v-html="message2[1]"></div>
        </div>
        <div style=" white-space: nowrap;">
          <div v-if="message3 != ``" class="q-card__section q-card__section--vert q-pt-none"
            style="display: inline-flex;">
            <input type="checkbox" v-if="this.$store.state.mode2 == 1" v-model="pump_grp" value="3">
            {{ message3[0] }}
            <AiMode ref="thrAimode" v-if="this.$store.state.mode2 == 1" :isPopup="true" :index="3" />
          </div>
        </div>
        <div v-if="message3 != ``" class="q-card__section q-card__section--vert q-pt-none">
          <div v-html="message3[1]"></div>
        </div>
        <div style="white-space: nowrap;">
          <div v-if="message4 != ``" class="q-card__section q-card__section--vert q-pt-none"
            style="display: inline-flex;">
            <input type="checkbox" v-if="this.$store.state.mode3 == 1" v-model="pump_grp" value="4">
            {{ message4[0] }}
            <AiMode ref="fouAimode" v-if="this.$store.state.mode3 == 1" :isPopup="true" :index="4" />
          </div>
        </div>
        <div v-if="message4 != ``" class="q-card__section q-card__section--vert q-pt-none">
          <div v-html="message4[1]"></div>
        </div>
        <div style="white-space: nowrap;">
          <div v-if="message5 != ``" class="q-card__section q-card__section--vert q-pt-none"
            style="display: inline-flex;">
            <input type="checkbox" v-if="this.$store.state.mode4 == 1" v-model="pump_grp" value="5">
            {{ message5[0] }}
            <AiMode ref="fivAimode" v-if="this.$store.state.mode4 == 1" :isPopup="true" :index="5" />
          </div>
        </div>
        <div v-if="message5 != ``" class="q-card__section q-card__section--vert q-pt-none">
          <div v-html="message5[1]"></div>
        </div>

        <!-- <button @click="$emit('confirmAiMode')"
          style="width: 100px; border-radius: 5px; float: right; margin: 0 20px 25px 0;" class="confirm-btn"
          type="button" role="button">
          <span class="block">취소</span>
        </button> -->
        <button v-if="!test && !isAnly" @click="$emit('cancelBtn')"
          style="width: 100px; border-radius: 5px; float: right; margin: 0 20px 25px 0;" class="confirm-btn"
          type="button" role="button">
          <span class="block">취소</span>
        </button>
        <button v-if="test && !isAnly" @click="$emit('testPopup', false)"
          style="width: 100px; border-radius: 5px; float: right; margin: 0 20px 25px 0;" class="confirm-btn"
          type="button" role="button">
          <span class="block">취소.</span>
        </button>
        <button v-if="!test && !isAnly" @click="handleCloseBtn(this.pump_grp)"
          :disabled="isLoading"
          style="width: 100px; border-radius: 5px; float: right; margin: 0 20px 25px 0;" class="confirm-btn"
          type="button" role="button">
          
          <span class="block">적용</span>
        </button>
        <button v-if="test && !isAnly" @click="testApi"
          style="width: 100px; border-radius: 5px; float: right; margin: 0 20px 25px 0;" class="confirm-btn"
          type="button" role="button">
          <span class="block">적용.</span>
        </button>
        <button v-if="isAnly" @click="$emit('cancelBtn')"
          style="width: 100px; border-radius: 5px; float: right; margin: 0 20px 25px 0;" class="confirm-btn"
          type="button" role="button">
          <span class="block">닫기</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import AiMode from '@/views/Common/AiMode.vue'
import { fetchFunc } from '@/util/fetchFunc'
import Swal from 'sweetalert2'

export default {
  components: { AiMode },
  props: ['message1', 'message2', 'message3', 'message4', 'message5', 'test'],
  data() {
    return {
      alarmTime: '',
      isAnly: false,
      pump_grp: [],
      isLoading: false,
    }
  },
  mounted() {
    // console.log(this.message)
    let DayFrom = new Date();
    const year = DayFrom.getFullYear();
    const month = String(DayFrom.getMonth() + 1).padStart(2, "0");
    const day = String(DayFrom.getDate()).padStart(2, "0");
    const hour = DayFrom.getHours();
    const min = DayFrom.getMinutes();
    this.alarmTime = `${year}.${month}.${day} ${hour}:${min}`;
    if (this.$store.state.mode0 == 1 || this.$store.state.mode1 == 1 || this.$store.state.mode2 == 1 || this.$store.state.mode3 == 1 || this.$store.state.mode4 == 1) {
      this.isAnly = false
    }
    else {
      this.isAnly = true
    }
    if (this.message1 != `` && this.$store.state.mode0 == 1) this.pump_grp.push(1)
    if (this.message2 != `` && this.$store.state.mode1 == 1) this.pump_grp.push(2)
    if (this.message3 != `` && this.$store.state.mode2 == 1) this.pump_grp.push(3)
    if (this.message4 != `` && this.$store.state.mode3 == 1) this.pump_grp.push(4)
    if (this.message5 != `` && this.$store.state.mode4 == 1) this.pump_grp.push(5)
  },
  methods: {
    async handleCloseBtn(pump_grp) {
      // API 호출이 이미 진행 중이면 무시
      if (this.isLoading) return;

      this.isLoading = true; // API 호출 시작
      
      try {
        // 상위 컴포넌트의 closeBtn 메서드 호출
        this.$emit('closeBtn', pump_grp);
      } finally {
        // API 호출이 완료되면 로딩 상태 해제
        this.isLoading = false;
      }
    },
    changeMode() {
      if (this.$refs.firAimode) {
        this.$refs.firAimode.changeTabForPopUp("2", 1)
      }
      if (this.$refs.secAimode) {
        this.$refs.secAimode.changeTabForPopUp("2", 2)
      }
      if (this.$refs.thrAimode) {
        this.$refs.thrAimode.changeTabForPopUp("2", 3)
      }
      if (this.$refs.fouAimode) {
        this.$refs.fouAimode.changeTabForPopUp("2", 4)
      }
      if (this.$refs.fivAimode) {
        this.$refs.fivAimode.changeTabForPopUp("2", 5)
      }
      // this.$emit('testPopup', false)
    },
    async testApi() {
      const confirmed = await Swal.fire({
        animation: false,
        text: "펌프제어 명령을 전송하시겠습니까?",
        showCancelButton: true,
        confirmButtonText: '적용',
        cancelButtonText: '취소',
        confirmButtonColor: 'rgba(239, 194, 240, 0.25)',
        cancelButtonColor: 'rgba(239, 194, 240, 0.25)'
      });
      if (confirmed.isConfirmed) {

        let res = (await fetchFunc(`${this.$apiURL}/ai/pumpCommandStatus`)).data;
        if (res.isRunning == false && res.data?.length > 0) {

          await fetchFunc(`${this.$apiURL}/ai/pumpCommand?pump_grp=${this.pump_grp}`);

          Swal.fire({
            animation: false,
            text: '정상적으로 수정되었습니다.'
          });
          this.$emit('testPopup', false)
        }
      } else {
        Swal.fire({
          animation: false,
          text: '이전 작업이 실행중입니다.'
        });
        this.$emit('testPopup', false)
      }
    },
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
  padding-top: 8px;
  padding-bottom: 2px;
  padding-left: 16px;
  padding-right: 16px;
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

.select_btn_font {
  /*text-shadow: 0 0 9px #5cafff;*/
  font-size: 13px;
  color: #000;
  font-family: 'KHNPHDBold';
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.select_btn {
  width: fit-content;
  height: 26px;
  padding: 5px 10px;
  align-self: center;
  color: #939cb0;
  font-weight: 400 !important;
  background-color: #2f4161;
  cursor: pointer;
  border: 1px solid #b4dffa;
  margin-left: 5px;
}

.select_btnForOnOff {
  width: 77px;
  height: 30px;
  align-self: center;
  border: solid 1px #b4dffa;
  background-color: rgba(40, 41, 41, 0.25);
  cursor: pointer;
  border: none;
  border-radius: 4px;
  margin-left: 5px;
}
</style>