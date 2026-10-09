<template>
  <!--일일보고서 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- <LoadingSpinner v-if="!isLoading" class="loading-container"></LoadingSpinner> -->

    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <BigTitle :title="'일일 보고서'" />
      <!-- 타이틀 끝 -->

      <div style="display: flex; float: right">
        <Vue3Datepicker :style="{
          height: '30px',
          color: '#ffffff',
          backgroundColor: '#15284e',
          'background-image':
            'url(' + require('@/assets/img/select_cal.png') + ')',
          'background-repeat': 'no-repeat',
          'background-position': 'right',
          outline: 'none',
          'border-width': '1px',
          borderColor: '#489cf2',
          borderRadius: '4px',
          'padding-left': '10px',
          margin: '0 10px',
        }" v-model="DayFrom" :locale="locale" :weekStartsOn="0" :inputFormat="inputFormat" />
        <span class="buttonArea" style="float: right"><span class="button" @click="selectClick(DayFrom)">조회</span></span>
        <span class="buttonArea" style="float: right"><span class="button" @click="onBtnExport(DayFrom)">엑셀</span></span>
      </div>
      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container">
        <div class="box_bt_area"></div>
        <b-col xl="12" v-bind:style="{ height: '920px', overflow: 'scroll' }">
          <SmallTitle :title="'전력 사용량'" />
          <div v-bind:style="{ height: '300px' }">
            <PowerConsumption ref="PowerConsumption" />
          </div>

          <SmallTitle :title="'시설별 사용량'" />
          <div v-bind:style="{ height: '250px' }">
            <UsageFacility ref="PumpList" />
          </div>

          <SmallTitle v-if="this.songsu" :title="'펌프 가동이력'" />
          <div v-if="this.songsu" v-bind:style="{ height: '380px' }">
            <PumpOperationHistory ref="TimeVue" />
          </div>

          <SmallTitle v-if="this.songsu" :title="'가동 트렌드'" />
          <div v-if="this.songsu" v-bind:style="{ height: '380px' }">
            <OperationTrend ref="Trand" />
          </div>

          <SmallTitle v-if="this.songsu" :title="'주요 배수지 수위(m)'" />
          <div v-if="this.songsu" v-bind:style="{ height: '240px' }">
            <MainWaterLevel ref="MainWaterLevel" />
          </div>

          <SmallTitle v-if="this.songsu" :title="'수위 트렌드'" />
          <div v-if="this.songsu" v-bind:style="{ height: '320px' }">
            <WaterLevelTrend ref="WaterLevelTrend" />
          </div>

          <SmallTitle :title="'시간대별 전력사용현황(kWh)'" />
          <span class="bottom_all2" style="margin-right: 80px">전력 피크값(kW)</span>
          <span style="padding: 35px">{{ peak_kwh }}</span>
          <span class="bottom_all2" style="margin-right: 80px">목표설정 피크값(kW)</span>
          <span>{{ peak_goal }}</span>
          <div v-bind:style="{ height: '350px' }">
            <PowerUsageStatus ref="PowerUsageStatus" />
          </div>
        </b-col>
      </div>
    </b-container>
  </div>
</template>

<script>
// import LoadingSpinner from "@/components/ComponentCommon/LoadingSpinner.vue";
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"
import PowerConsumption from "@/views/Report/DailyReport/DailyReport_PowerConsumption.vue";
import UsageFacility from "@/views/Report/DailyReport/DailyReport_UsageFacility.vue";
import PumpOperationHistory from "@/views/Report/DailyReport/DailyReport_PumpOperationHistory.vue";
import OperationTrend from "@/views/Report/DailyReport/DailyReport_OperationTrend.vue";
import MainWaterLevel from "@/views/Report/DailyReport/DailyReport_MainWaterLevel.vue";
import WaterLevelTrend from "@/views/Report/DailyReport/DailyReport_WaterLevelTrend.vue";
import PowerUsageStatus from "@/views/Report/DailyReport/DailyReport_PowerUsageStatus.vue";
import { fetchFunc } from "@/util/fetchFunc";
import { addCommaNumber } from "@/util/addCommaNumber";
import Vue3Datepicker from "vue3-datepicker";
import "vue3-datepicker/dist/vue3-datepicker.css";
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
// import { ref } from 'vue';
export default {
  components: {
    // LoadingSpinner,
    PowerConsumption,
    UsageFacility,
    PumpOperationHistory,
    OperationTrend,
    MainWaterLevel,
    WaterLevelTrend,
    PowerUsageStatus,
    Vue3Datepicker,
    BigTitle,
    SmallTitle
  },
  data() {
    let DayFrom = new Date();
    const inputFormat = "yyyy-MM-dd";
    // 어제 날짜 계산
    DayFrom.setDate(DayFrom.getDate() - 1);

    const yesterday = new Date(DayFrom);
    yesterday.setDate(DayFrom.getDate() - 1);

    const year = DayFrom.getFullYear();
    const month = String(DayFrom.getMonth() + 1).padStart(2, "0");
    const day = String(DayFrom.getDate()).padStart(2, "0");

    const yesterday_Day = String(yesterday.getDate()).padStart(2, "0");

    const search = `${year}-${month}-${day}`;
    const search2 = `${year}-${month}-${yesterday_Day}`;
    return {
      inputFormat,
      DayFrom,
      filed: new Array(),
      rowData: new Array(),
      search,
      search2,
      peak_kwh: 0,
      peak_goal: 0,
      isLoading: false,
      trand_data: [],
      songsu: true,
    };
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
    this.selectZone();
    this.selectPumpList();
    this.selectClick(this.DayFrom);
    if (this.$area == 'gumi' || this.$area == 'haepyeong' || this.$area == 'hakya' || this.$area == 'jain') {
      this.songsu = false
    }
    else {
      this.songsu = true
    }
  },
  methods: {
    async selectClick(e) {

   
      const year = e.getFullYear();
      const month = String(e.getMonth() + 1).padStart(2, "0");
      const day = String(e.getDate()).padStart(2, "0");
      const yesterday = new Date(e);
      yesterday.setDate(e.getDate() - 1);
      const yesterday_Day = String(yesterday.getDate()).padStart(2, "0");
      const search = `${year}-${month}-${day}`;
      const search2 = `${year}-${month}-${yesterday_Day}`;



      const apiURL = this.$apiURL;
      const requests = [
        fetchFunc(`${apiURL}/st/selectReport?date=${search}&type=1`).then(res => res).then(data => this.$refs.PowerConsumption.initData(data)),
        fetchFunc(`${apiURL}/st/selectReport?date=${search}&type=2`).then(res => res).then(data => this.$refs.PumpList.setGridRow(data)),
        fetchFunc(`${apiURL}/st/selectReport?date=${search}&type=3`).then(res => res).then(data => this.$refs.TimeVue.setGridRow(data)),
        // fetchFunc(`${apiURL}/es/selectPumpPerformList?start_date=${search2}&end_date=${search}&time_type=h`).then(res => res).then(data => this.pumpData = data.data),
        fetchFunc(`${apiURL}/es/selectPumpPerformList}?
                start_date=${search2}&end_date=${search}&time_type=h`)
          .then(res => res).then(data => this.pumpData = data.data),
        fetchFunc(`${apiURL}/st/selectReport?date=${search}&type=4`).then(res => res).then(data => this.$refs.MainWaterLevel.setGridFiled(data)),
        fetchFunc(`${apiURL}/st/selectReport?date=${search}&type=5`).then(res => res).then(data => this.$refs.WaterLevelTrend.initData(data)),
        fetchFunc(`${apiURL}/st/selectReport?date=${search}&type=6`).then(res => res).then(data => this.$refs.PowerUsageStatus.setGridRow(data)),
        fetchFunc(`${apiURL}/st/selectReport?date=${search}&type=7`).then(res => res).then(data => {
          this.peak_kwh = data.data[0];
          if (this.peak_kwh != null) {
            this.peak_kwh = data.data[0].peak;
          } else {
            this.peak_kwh = "No Data";
          }
        }),
        fetchFunc(`${apiURL}/st/selectPeakGoal`).then(res => res).then(data => {
          this.isLoading = true;
          this.peak_goal = data.data[0].value;
          if (this.peak_goal != null) {
            this.peak_goal = data.data[0].value;
          } else {
            this.peak_goal = "No Data";
          }
        })
      ];

      await Promise.allSettled(requests);

      const pwmNames = [];
      const pwmXData = [];
      const pwmYData = [];
      const pwmPer = {};
      this.pumpData?.PMB_TAG?.forEach((element) => {
        if (!pwmNames.includes(element.name)) {
          pwmNames.push(element.name);
        }

        if (!pwmXData.includes(element.ts)) {
          pwmXData.push(element.ts);
        }
      });

      pwmNames.forEach((element) => {
        let data = [];
        let useVal = [];
        this.pumpData?.PMB_TAG?.forEach((item) => {
          if (item.name == element) {
            if (Number(item.value) > 0) {
              useVal.push(item);
            }
            data.push(Number(item.value));
          }
        });

        pwmYData.push(data);
        pwmPer[element] = addCommaNumber((useVal.length / data.length) * 100);
      });

      this.$refs.Trand.initChart(pwmXData, pwmNames, pwmYData, this.selected);
      // 가동 트렌드 그래프 끝

      this.isLoading = false;
    },
    async selectZone() {
      const apiURL = this.$apiURL;
      let res = await fetch(`${apiURL}/st/selectZone`);
      let data = await res.json();
      this.$refs.PumpList.setGridFiled(data);
    },

    async selectPumpList() {
      const apiURL = this.$apiURL;
      let res = await fetch(`${apiURL}/ai/selectPumpList`);
      let data = await res.json();
      this.$refs.TimeVue.setGridFiled(data);
    },
    async onBtnExport(e) {
      const year = e.getFullYear();
      const month = String(e.getMonth() + 1).padStart(2, "0");
      const day = String(e.getDate()).padStart(2, "0");
      const search = `${year}-${month}-${day}`;
      const apiURL = this.$apiURL;
      window.location.href = `${apiURL}/cm/download?date=${search}`

    }


  },
};
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */

/* -----Content Layout----- */
.box_bt_area {
  height: 40px;
  display: flex;
  align-items: center;
  margin: 5px 0;
  justify-content: flex-end;
}

.bottom_all2 {
  font-size: 16px;
  font-family: "KHNPHDRegular";
  letter-spacing: normal;
  color: #c3eaff;
  font-weight: normal;
}

.space {
  margin-top: 15px;
  margin-bottom: 35px;
  display: block;
  width: 100%;
  height: 100px;
  background-color: white;
}

.loading-container {
  position: fixed;
  /* 절대 위치 설정 */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  /* 반투명한 배경 */
  z-index: 9999;
  /* 다른 요소 위에 표시하기 위한 z-index 설정 */
  display: flex;
  justify-content: center;
  /* 수평 가운데 정렬 */
  align-items: center;
}
</style>
