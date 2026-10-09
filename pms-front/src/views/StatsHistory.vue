<template lang="">
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="px-5">
      <!-- 본문 컨텐츠 시작 -->
      <div class="content">
        <b-row class="mb-3">
          <b-col md="12">
            <!-- 챠트영역 시작 -->
            <div class="chart-box">
              <!-- 종합 알람 현황 시작 -->
              <FacAlarmStatus />
              <DiagAlarmStatus/>
              <!-- 종합 알람 현황 끝 -->
              <!-- 주간 알람 현황 시작-->
              <DefectStatusAlarm/>
              <WeeklyAlarm />
              <!-- 주간 알람 현황 끝 -->
            </div>
            <!-- 챠트영역 끝 -->
          </b-col>
        </b-row>

        <!-- 알람 리스트 시작 -->
        <AlarmList />
        <!-- 알람 리스트 끝 -->
      </div>
      <!-- //본문 컨텐츠 시작 -->
    </b-container>
    <!-- //템플릿 내용 -->
  </div>
</template>
<script>
import AlarmList from "./StatsHistory/AlarmList.vue";
import DiagAlarmStatus from "./StatsHistory/DiagAlarmStatus.vue";
import FacAlarmStatus from './StatsHistory/FacAlarmStatus.vue';
import WeeklyAlarm from "./StatsHistory/WeeklyAlarm.vue";
import DefectStatusAlarm from './StatsHistory/DefectStatusAlarm.vue';

export default {
  components: { AlarmList, FacAlarmStatus, WeeklyAlarm, DiagAlarmStatus, DefectStatusAlarm },
  mounted() {
    setInterval(() => {
      location.reload(); // 페이지를 새로고침
    }, 5 * 60 * 1000);
  }
};
</script>
<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.content {
  /* padding: 20px; */
  height: calc(100vh - 80px);
  /* display: flex;
    gap: 20px; */
}

.chart-box {
  flex: 1;
  width: 100%;
  /* height: calc(100% / 2); */
  height: initial;
  display: flex;
  gap: 20px;
}
</style>
