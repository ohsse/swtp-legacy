<template>
  <div class="q-pa-md">
    <!-- <q-date
      v-model="date"
      default-view="Years"
    /> -->
    <b-row class="d-flex justify-content-end">
      <div class="d-flex justify-content-end mb-3">
        <select v-if="!isSelected" v-model="selected" class="d-inline date_design" @change="handleSelectChange" :style="{
          'background-image':
            'url(' + require('@/assets/img/select_btn.png') + ')',
          'background-repeat': 'no-repeat',
          'background-position': 'right',
        }">
          <option value="h">시</option>
          <option value="d">일</option>
          <option value="m">월</option>
          <option value="y">년</option>
        </select>

        <!-- 옵션 시, 일 선택시 달력 표시  -->
        <!-- :ref="inputs.DayFrom" -->
        <div style="display: inherit">
          <Vue3Datepicker class="pickerClassStyle" :minimumView="minimumView" v-model="from" :locale="locale"
            :weekStartsOn="0" :inputFormat="inputFormat" @update:modelValue="tossEvent()" />
          <span>~</span>

          <!-- :ref="inputs.DayTo" -->
          <Vue3Datepicker class="pickerClassStyle" :minimumView="minimumView" v-model="to" :locale="locale"
            :weekStartsOn="0" :inputFormat="inputFormat" @update:modelValue="tossEvent()" />
        </div>
        <!-- @change="selectTankList(tankListDataValue)" -->
        <select v-model="tankListDataValue" class="d-inline date_design" v-if="tankListDataValue" :style="{
          'background-image':
            'url(' + require('@/assets/img/select_btn.png') + ')',
          'background-repeat': 'no-repeat',
          'background-position': 'right',
        }">
          <option v-for="(value, key) in tankListData" :key="key" :value="value">
            {{ key }}
          </option>
        </select>

        <span class="buttonArea" style="float: right"><span class="button"
            @click="getCalValue(selected, tankListDataValue)">조회</span></span>
        <span v-if="excelDown" class="buttonArea" style="float: right"><span class="button" style="width: 120px;"
            @click="this.$emit('excelDown', from, to)">다운로드</span></span>
        <input id="inputHidden" class="hidden" />
      </div>
    </b-row>
  </div>
</template>

<script>
import Vue3Datepicker from "vue3-datepicker";
import "vue3-datepicker/dist/vue3-datepicker.css";
import { ref, reactive } from "vue";
import { ko } from "date-fns/locale";
import Swal from 'sweetalert2'
export default {
  props: ["noMount", "tankListData", "excelDown", "isSelected", "dayAgo"],
  data() {
    let tankNum = "";
    let selected = "h";
    let selectedEvent = null;
    let tankListDataValue = undefined;
    const picked = ref(new Date());
    const locale = reactive(ko);
    let inputFormat = ref("yyyy-MM-dd");
    const now = new Date();
    let from
    if (this.dayAgo) {
      from = ref(new Date(now.setDate(now.getDate() - this.dayAgo)));
    } else {
      from = ref(new Date(now.setDate(now.getDate())));
    }
    const to = ref(new Date());  // 현재 날짜로 설정
    // [from, to]'s value before changing value
    let oldVal = "";
    let minimumView = undefined;
    return {
      tankNum,
      selected,
      tankListDataValue,
      picked,
      locale,
      inputFormat,
      from,
      to,
      oldVal,
      minimumView,
      selectedEvent
    };
  },
  component: {
    Vue3Datepicker,
  },
  mounted() {
    if (!this.noMount) {
      this.getCalValue(this.selected, this.tankListDataValue);
    }
  },
  updated() {
    // this.tankListDataValue =
    //   this.tankListData[Object.keys(this.tankListData)[0]];
    // this.getCalValue(this.selected, this.tankListDataValue);
  },
  watch: {
    dayAgo: {
      immediate: true,
      handler(newVal) {
        const days = parseInt(newVal);
        // this.to가 undefined/null일 때는 오늘로 기본값 처리
        const toDate = this.to instanceof Date ? this.to : new Date();
        if (days > 0) {
          const fromDate = new Date(toDate); // 복사
          fromDate.setDate(toDate.getDate() - days);
          this.from = fromDate;
        }
      }
    }
  },
  methods: {
    tossEvent() {
      const inputHidden = document.getElementById('inputHidden');
      if (inputHidden) {
        inputHidden.focus();
      }
    },

    getCalValue(selected, tankListDataValue) {
      const dateFrom = new Date(this.from.getTime() + 9 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0];
      const dateTo = new Date(this.to.getTime() + 9 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0];


      const dateFromMon = dateFrom.slice(0, 7)
      const dateToMon = dateTo.slice(0, 7)

      const dateFromYear = dateFrom.slice(0, 4)
      const dateToYear = dateTo.slice(0, 4)
      if (dateFrom > dateTo) {
        Swal.fire({
          animation: false,
          text: "앞 날짜가 뒷날짜보다 미래일순 없습니다.",
        });
      } else {
        if (!tankListDataValue) {
          if (this.selectedEvent == 'm') {
            this.$emit("chartData", dateFromMon, dateToMon, selected);
          } else if (this.selectedEvent == 'y') {
            this.$emit("chartData", dateFromYear, dateToYear, selected);
          } else {
            this.$emit("chartData", dateFrom, dateTo, selected);
          }
        } else {
          if (this.selectedEvent == 'm') {
            this.$emit("chartData", dateFromMon, dateToMon, selected, tankListDataValue);
          } else if (this.selectedEvent == 'y') {
            this.$emit("chartData", dateFromYear, dateToYear, selected, tankListDataValue);
          } else {
            this.$emit("chartData", dateFrom, dateTo, selected, tankListDataValue);
          }
        }
      }


    },
    handleSelectChange(event) {
      this.selectedEvent = event.target.value;
     
      if (event.target.value == "h" || event.target.value == "d") {
        this.inputFormat = "yyyy-MM-dd";
        this.minimumView = undefined;
      } else if (event.target.value == "m") {
        this.inputFormat = "yyyy-MM";
        this.minimumView = "month";
        let now = new Date();
        now.setMonth(now.getMonth() - 1);
        this.from = ref(now);
      } else if (event.target.value == "y") {
        this.inputFormat = "yyyy";
        this.minimumView = "year";
        let now = new Date();
        now.setFullYear(now.getFullYear() - 1);
        this.from = ref(now);
      }
    },
  },
};
</script>

<style>
.year-only .vue3-datepicker-days,
.year-only .vue3-datepicker-months {
  display: none;
}

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

.hidden {
  opacity: 0;
  width: 0.1px;
}
</style>
