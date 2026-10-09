<template>
  <div class="location">
    <div class="search" style="display: inherit;">
      <div style="display: inherit">
        <Vue3Datepicker class="pickerClassStyle" v-model="from" :locale="locale" :weekStartsOn="0" />
        <span style="color: white;">~</span>

        <!-- :ref="inputs.DayTo" -->
        <Vue3Datepicker class="pickerClassStyle" v-model="to" :locale="locale" :weekStartsOn="0" />
      </div>

    </div>
    <button class="button" @click="searchDate">조회</button>
  </div>
</template>

<script>
import Vue3Datepicker from "vue3-datepicker";
import "vue3-datepicker/dist/vue3-datepicker.css";
import { useRouter } from "vue-router";
import { useStore } from "vuex";
import { ref, computed, reactive } from "vue";
import { ko } from "date-fns/locale";

export default {
  component: { Vue3Datepicker },
  props: ['alarmList'],
  data() {
    let alarmDate = this.alarmList;
    const now = new Date();
    now.setDate(now.getDate() - 7)
    const from = ref(now);
    const to = new Date();
    const locale = reactive(ko);
    const router = useRouter();
    const store = useStore();
    const state = reactive({
      model: store.state.monitor1.selectModel,
      options: computed(() => {
        let list = [];
        for (let i = 0; i < store.state.monitor1.modelList.length; i++) {
          list.push(store.state.monitor1.modelList[i]?.title);
        }
        return list;
      }),
      datePop: false,
      alert: false,
    });
    return {
      alarmDate,
      router,
      state,
      store,
      locale, from, to
    }
  },
  mounted() {
    this.alarmListInit();
  },
  methods: {
    back() {
      this.router.push("/PumpControl");
    },
    dateToNumber() {
      this.store.state.monitor1.searchDate = true
      this.store.state.monitor1.pickDate.from = new Date(this.from.getTime() + 9 * 60 * 60 * 1000).toISOString().split("T")[0]
      this.store.state.monitor1.pickDate.to = new Date(this.to.getTime() + 9 * 60 * 60 * 1000).toISOString().split("T")[0]
    },
    searchDate() {
      if (!this.alarmDate) {
        this.dateToNumber();
        this.store.dispatch("monitor1/bearingTempInfo");
        this.store.dispatch('monitor1/alarm', { parameterName: this.store.state.monitor1.id, motorParams: { id: this.store.state.monitor1.id, endDate: new Date(this.to.getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ").split(' ')[0], startDate: new Date(this.from.getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ").split(' ')[0] } });
        // this.store.dispatch("monitor1/motorDetails");
        // this.store.dispatch("monitor1/windingTempInfo");
        // store.dispatch('monitor1/handleDatePicker');
      } else {
        this.$emit('alarmListDate', this.from, this.to)
      }
    },
    alarmListInit() {
      if (this.alarmDate) {
        this.$emit('alarmListDate', this.from, this.to)
      }
    }
  },

}
</script>

<style>
.pickerClassStyle {
  height: 30px;
  color: #ffffff;
  background-color: #15284e;
  background-image: url("@/assets/img/select_cal.png");
  background-repeat: no-repeat;
  background-position: right;
  outline: none;
  border-width: 1px;
  border-color: #489cf2;
  border-radius: 4px;
  padding-left: 10px;
  margin: 0 10px;
}

.button {
  margin-right: 30px;
}
</style>