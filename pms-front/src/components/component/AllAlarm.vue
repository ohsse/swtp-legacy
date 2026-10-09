<template>
  <div class="q-dialog fullscreen no-pointer-events q-dialog--modal">
    <div class="q-dialog__backdrop fixed-full" aria-hidden="true"></div>
    <div
      class="q-dialog__inner flex no-pointer-events q-dialog__inner--minimized q-dialog__inner--standard fixed-full flex-center"
      tabindex="-1">
      <div class="q-card bg-default">
        <div class="q-card__section q-card__section--vert">
          <div class="text-h6">펌프모터 알람 이상 발생</div>
        </div>
        <div class="q-card__section q-card__section--vert q-pt-none">
          <!-- 대표적으로 첫번째 이상 펌프 보여주기 위해서 [0] 배열로 소스 구성함  -->
          {{ alarmData[0]?.grp_nm.substr(0, 3) }}
          {{ title.name }} #{{ alarmData[0]?.pump_idx }} 모터
          펌프모터 알람 이상 발생했습니다. <br />
          해당 장비를 확인 하시겠습니까?
        </div>
        <div class="q-card__actions justify-end q-card__actions--horiz row">
          <!-- <q-btn flat label="OK" color="primary" v-close-popup /> -->
          <button @click="monitorGo"
            class="q-btn q-btn-item non-selectable no-outline q-btn--flat q-btn--rectangle q-btn--actionable q-focusable q-hoverable confirm-btn"
            tabindex="0" type="button" role="button">
            <span class="q-focus-helper"></span><span
              class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><span
                class="block">확인</span></span>
          </button>
          <button @click="$emit('modalEvent')"
            class="q-btn q-btn-item non-selectable no-outline q-btn--flat q-btn--rectangle q-btn--actionable q-focusable q-hoverable confirm-btn"
            tabindex="0" type="button" role="button">
            <span class="q-focus-helper"></span><span
              class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><span
                class="block">취소</span></span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useStore } from "vuex";

export default {
  props: ['abnormalAlarm'],
  data() {
    let modalChange;
    const store = useStore();
    let alarmData = this.abnormalAlarm;
    return {
      store,
      modalChange, alarmData,
      title: { name: '' },
    }
  },
  mounted() {
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    this.store.state.monitor1.pickDate.from = oneWeekAgo.toISOString().split("T")[0]
    this.store.state.monitor1.pickDate.to = new Date().toISOString().split("T")[0]
    if (this.$route.path == '/PumpMonitoring') {
      this.store.state.alarmEvent = false
      this.store.dispatch('monitor1/alarm', { parameterName: this.alarmData[0].motor_id, motorParams: { id: this.alarmData[0].motor_id, endDate: this.store.state.monitor1.pickDate.to, startDate: this.store.state.monitor1.pickDate.from } });
    }
    this.titleChange();
  },
  methods: {
    monitorGo() {
      this.$emit('modalEvent');
      const alarmData = this.alarmData[0].motor_id; // 값 설정
      // console.log("alarmData 확인버튼", alarmData);
      this.$router.push({ name: "PumpMonitoring", query: { alarmData } });
    },
    titleChange() {
      const store = useStore();
      const area = store.state.area;
      // console.log("area", area);
      if (area == 'gosan') {
        this.title.name = ' 송수펌프모터'
      } else if (area == 'gumi') {
        this.title.name = ' 신평(생활)계통'
      } else if (area == 'hakya') {
        this.title.name = ' 임하가압장'
      }
    },
  },
}
</script>

<style></style>