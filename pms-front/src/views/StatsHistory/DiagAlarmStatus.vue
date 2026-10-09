<template>
  <div class="chart-area">
    <div class="chart-con">
      <div class="box-edge top-L blur" data-v-789da364=""></div>
      <div class="box-edge top-R blur" data-v-789da364=""></div>
      <div class="box-edge bottom-L blur" data-v-789da364=""></div>
      <div class="box-edge bottom-R blur" data-v-789da364=""></div>
      <div class="box-edge top-L" data-v-789da364=""></div>
      <div class="box-edge top-R" data-v-789da364=""></div>
      <div class="box-edge bottom-L" data-v-789da364=""></div>
      <div class="box-edge bottom-R" data-v-789da364=""></div>
      <div class="chart">
        <!-- 서브 타이틀 시작 -->
        <div class="title-box mb-3">
          <span class="mb-0" style="display: flex;">
            <img src="@/assets/img/circle.6d33197f.svg" alt="타이틀 블릿 이미지">
            <p class="mb-0">진단별 상태현황 </p>
          </span>
          <p class="mb-0" style="font-size: 13px;"> {{ dateTime[1] }} - {{ dateTime[0] }}</p>
        </div>
        <p>(진단 횟수 : {{ tot }}건 / 정상: {{ normal }} 건 / 알람: {{ alarm }}건)</p>
        <!-- 서브 타이틀 끝 -->
        <!-- 챠트 시작 -->
        <div style="height: 300px">
          <LoadingSpinner v-if="isLoading"></LoadingSpinner>
          <div v-if="!isLoading" :style="{ height: '100%' }">
            <PieChart_donut :labels="labels" :pieData="PieData" :legend="legend" />
          </div>
        </div>
        <!-- 챠트 끝 -->
      </div>
    </div>
  </div>
</template>

<script>

import LoadingSpinner from "@/components/component/LoadingSpinner.vue"
import { useStore } from 'vuex'
import axios from 'axios'
import PieChart_donut from '@/components/chart/history/PieChart_donut.vue'
export default {
  components: { PieChart_donut, LoadingSpinner },
  data() {
    const store = useStore();
    return {
      isLoading: true,
      legend: ['정상', '알람'],
      labels: ['정상', '알람'],
      Diagnosis: 0,
      PieData: [],
      tot: 0,
      alarm: 0,
      normal: 0,
      dateTime: [],
      store,
    }
  },
  mounted() {
    this.getStatus()
  },
  methods: {
    async getStatus() {
      // 현재 날짜 설정
      const now = new Date();
      const year = now.getFullYear();
      const month = ('0' + (now.getMonth() + 1)).slice(-2);
      const day = ('0' + now.getDate()).slice(-2);
      const nowDate = `${year}-${month}-${day}`;

      // 조회기간으로 표출할 날짜 지정
      const startDt = new Date(now)
      startDt.setMonth(startDt.getMonth()-3)
      console.log('startDt',startDt)
      const year_old = startDt.getFullYear();
      const month_old = ('0' + (startDt.getMonth() + 1)).slice(-2);
      const day_old = ('0' + startDt.getDate()).slice(-2);
      const startDate = `${year_old}-${month_old}-${day_old}`;

      this.dateTime.push(nowDate.replaceAll('-','/'), startDate.replaceAll('-','/'))

      // 파라미터로 보낼 값
      const params = {
        nowDate: nowDate,
        interval: 'month',
        range: 3
      }
      const res = await axios.get(
        `${this.store.state.globalIP}/api/v1/alarm/alarmStatusDefect`, { params }
      );

      const data = res.data.datas
      if (data != null) {
        this.isLoading = false
        this.tot = data.all_count
        this.alarm = data.alarm
        this.normal = data.all_count - data.alarm
        this.PieData.push(this.normal, this.alarm)
      }
    },
  },
}
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.title-box {
  font-size: 18px;
  display: flex;
  align-items: center;
  text-align: center;
  justify-content: space-between;
  /* height: 15%; */
  color: #c8d7e9;
  text-shadow: 0px 0px 10px #24baff;
}

.title-box img {
  width: 16px;
  margin-right: 8px;
}

.chart-area {
  position: relative;
  width: 50%;
  height: 100%;
  background: rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-con {
  position: relative;
  float: left;
  width: 100%;
  height: 100%;
  border: 1px solid #2660ab;
  border-radius: 12px;
  padding: 15px;
}

.top-L {
  top: -1px;
  left: -1px;
  border-top: 2px solid #2C80FF;
  border-left: 2px solid #2C80FF;
  border-top-left-radius: 12px;
}

.top-R {
  top: -1px;
  right: -1px;
  border-top: 2px solid #2C80FF;
  border-right: 2px solid #2C80FF;
  border-top-right-radius: 12px;
}

.box-edge {
  width: 15px;
  height: 15px;
  position: absolute;
}

.bottom-L {
  bottom: -1px;
  left: -1px;
  border-bottom: 2px solid #2C80FF;
  border-left: 2px solid #2C80FF;
  border-bottom-left-radius: 12px;
}

.bottom-R {
  bottom: -1px;
  right: -1px;
  border-bottom: 2px solid #2C80FF;
  border-right: 2px solid #2C80FF;
  border-bottom-right-radius: 12px;
}
</style>