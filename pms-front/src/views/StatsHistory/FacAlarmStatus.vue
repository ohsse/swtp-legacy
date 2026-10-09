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
          <img src="@/assets/img/circle.6d33197f.svg" alt="타이틀 블릿 이미지">
          <p class="mb-0">설비별 상태현황 </p>
        </div>
        <p>(설비댓수 : {{ fac }}대 / 이상: {{ alarm }}건)</p>
        <!-- 서브 타이틀 끝 -->
        <!-- 챠트 시작 -->
        <div style="height: 300px">
          <LoadingSpinner v-if="isLoading"></LoadingSpinner>
          <div v-if="!isLoading" :style="{ height: '100%' }">
            <PieChart_donut :labels="labels" :legend="legend" :pieData="PieData" />
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
import PieChart_donut from "@/components/chart/history/PieChart_donut.vue";
import { fetchFunc } from '@/util/fetchFunc';
export default {
  components: { PieChart_donut, LoadingSpinner },
  data() {

    const store = useStore();
    return {
      isLoading: true,
      labels: [],
      PieData: [],
      legend: ['정상 댓수', '이상 댓수'],
      fac: 0,
      alarm: 0,
      store,
    }
  },
  mounted() {
    this.getAlarmData()
  },
  methods: {
    async getAlarmData() {
      const res = await fetchFunc(
        `${this.store.state.globalIP}/api/v1/motor/alarm`, { motorParams: { id: this.store.state.monitor1.id, endDate: new Date().toISOString().split("T")[0], startDate: new Date().toISOString().split("T")[0] } }
      );
      let grpNm = 0;
      let unNormal = 0
      let normal = 0
      const data = await res
      if (data != null) {
        this.isLoading = false
        data.datas?.forEach(grp => {
          grpNm = grpNm + grp.length
          this.fac = grpNm
          console.log('grp', grp)
          unNormal = unNormal + grp.filter(item => { return (item['Alarm'] == true) }).length
          normal = normal + grp.filter(item => { return item['Alarm'] == false }).length
          // unNormal = unNormal + isNormalFac.filter(item => item == 'true').length
          // normal = normal + isNormalFac.filter(item => item == 'false').length

        })
        this.PieData.push(normal, unNormal)
        this.alarm = unNormal
        this.labels = this.legend
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