<template>
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="">
      <!-- 본문 컨텐츠 시작 -->
      <div class="content">
        <b-row>
          <b-col xl="3">
            <div class="title_wrap justify-content-center align-items-center rounded shadow"
              :style="{ marginBottom: '15px' }">정밀진단</div>
            <b-card class="rounded-5 shadow" :style="{ height: 'calc(100vh - 190px)', border: '0' }">
              <purification-plant v-for="(item, index) in store.state.precision.pumps" :key="index" :plantVal="item" />
            </b-card>
          </b-col>
          <b-col xl="9" class="position-relative">
            <b-row>
              <b-col>
                <b-row class="d-flex align-items-center border p-2"
                  :style="{ height: '50px', background: '#101320', border: '1px solid #0c2254 !important' }">
                  <b-col xl="9" class="d-flex justify-content-start align-items-center px-0">
                    <button class="btn bg-transparent btn-sm" @click="beforeClick"><i class="bi bi-caret-left-fill"
                        :style="{ fontSize: '16px' }"></i></button>
                    <b-form-input type="date" v-model="startDt" />
                    <span class="mx-3">~</span>
                    <b-form-input type="date" v-model="endDt" />
                    <b-form-select v-model="selectData" class="mx-2">
                      <b-form-select-option value="1w">1 Week</b-form-select-option>
                      <b-form-select-option value="2w">2 Weeks</b-form-select-option>
                      <b-form-select-option value="1M">1 Month</b-form-select-option>
                      <b-form-select-option value="3M">3 Months</b-form-select-option>
                      <b-form-select-option value="6M">6 Months</b-form-select-option>
                    </b-form-select>
                    <button class="btn bg-transparent btn-sm" @click="afterClick"><i class="bi bi-caret-right-fill"
                        :style="{ fontSize: '16px' }"></i></button>
                  </b-col>
                  <b-col xl="3" class="d-flex justify-content-end">
                    <button class="btn btn-primary btn-sm mx-1" @click="searchApi">Search</button>
                    <button class="btn btn-primary btn-sm" @click="changeEndDtToCur">Current</button>
                  </b-col>
                </b-row>
              </b-col>
            </b-row>
            <b-row>
              <b-col xl="12" class="mt-3">
                <!-- 차트영역 시작 -->
                <div class="border p-4" v-if="isChartShow"
                  :style="{ height: '340px', background: '#101320', border: '1px solid #0c2254 !important' }">
                  <Linechart :style="{ height: '275px' }" :title="store.state.precision.titles[0]"
                    :detailData="chartData[0].data" :yName="chartData[0].yName" :isTime="false" :isModal="true"
                    :nameGap="50" @chartClick="chartClick" :changeTime="store.state.precision.changeTime" />
                </div>
                <!-- //차트영역 끝 -->
              </b-col>
            </b-row>
            <b-row class="mt-4">
              <b-col xl="6">
                <!-- 차트영역 시작 -->
                <div class="border p-4"
                  :style="{ height: '397px', background: '#101320', border: '1px solid #0c2254 !important' }">
                  <Linechart :style="{ height: '280px' }" :title="store.state.precision.titles[1]"
                    :detailData="chartData[1].data" :yName="chartData[1].yName" :isModal="true" :isTime="false"
                    :nameGap="40" xName="초" :size="8" />
                </div>
                <!-- //차트영역 끝 -->
              </b-col>
              <b-col xl="6">
                <!-- 차트영역 시작 -->
                <div class="border p-4"
                  :style="{ height: '397px', background: '#101320', border: '1px solid #0c2254 !important' }">
                  <Linechart :style="{ height: '280px' }" :title="store.state.precision.titles[2]"
                    :detailData="chartData[2].data" :yName="chartData[2].yName" :isModal="true" :isTime="false"
                    :nameGap="40" :xLines="chartData[2]?.xLines" xName="주파수" :size="8" />
                </div>
                <!-- //차트영역 끝 -->
              </b-col>
            </b-row>
            <!-- 팝업 시작 -->
            <PurificationPopup v-if="store.state.precision.settingPump >= 0" />
            <!-- 팝업 끝 -->
          </b-col>
        </b-row>
      </div>
      <!-- //본문 컨텐츠 끝 -->
    </b-container>
    <!-- //템플릿 내용 -->
  </div>
</template>

<script>
//import { bottom } from '@popperjs/core';
import "bootstrap-icons/font/bootstrap-icons.css"
import PurificationPlant from "./PrecisionDiagnosis/PurificationPlant.vue";
import PurificationPopup from "./PrecisionDiagnosis/PurificationPopup.vue";
import { onMounted, ref, watch } from 'vue';
import { useStore } from "vuex";
import Linechart from "@/components/chart/monitoring/Linechart_d.vue";

export default {
  components: { PurificationPlant, PurificationPopup, Linechart },
  setup() {
    let isChartShow = true;
    const store = useStore();
    const selectData = ref('1w')
    const endDt = ref(new Date().toISOString().split('T')[0]);
    const startDate = new Date()
    startDate.setDate(new Date().getDate() - 7)
    const startDt = ref(startDate.toISOString().split('T')[0])
    const chartClick = (xName) => {
      isChartShow = false
      console.log('isChartShow', isChartShow);
      lastDate = xName.replaceAll('-', '.')
      store.commit('precision/changeTime', lastDate)
      store.commit('precision/titles', [chartData[0].title, chartData[1].title + (lastDate ? `- (${lastDate})` : ''), chartData[2].title + (lastDate ? `- (${lastDate})` : '')])
      store.dispatch('precision/getTimeWaveChart', { acq_date: xName })
      store.dispatch('precision/getSpectrumChart', { acq_date: xName })
    }
    // const detailData= [[1,2,3,4,5], [1,2,3,4,5]]
    const setStartDt = (v, endParam = endDt.value, isPlus) => {
      let defaultDis = new Date(endParam);
      switch (v) {
        case '1w':
          defaultDis.setDate(defaultDis.getDate() + (isPlus === true ? +7 : -7))
          break
        case '2w':
          defaultDis.setDate(defaultDis.getDate() + (isPlus === true ? +14 : 14))
          break;
        case '1M':
          defaultDis.setMonth(defaultDis.getMonth() + (isPlus === true ? +1 : -1))
          break;
        case '3M':
          defaultDis.setMonth(defaultDis.getMonth() + (isPlus === true ? +3 : -3))
          break;
        case '6M':
          defaultDis.setMonth(defaultDis.getMonth() + (isPlus === true ? +6 : -6))
          break
      }
      return defaultDis.toISOString().split('T')[0];
    }
    watch(selectData, (v) => {
      startDt.value = setStartDt(v)
    })
    watch(endDt, (v) => [
      startDt.value = setStartDt(selectData.value, v)
    ])
    watch(() => [startDt.value, endDt.value], (v) => {
      store.commit("precision/setDate", { startDate: v[0], endDate: v[1] })
    })
    watch(() => [store.state.precision.choiceMoter, store.state.precision.choiceChannel], () => {
      searchApi()
    })
    onMounted(() => {
      store.dispatch("precision/getPumps")
      searchApi()
    });
    const beforeClick = () => {
      endDt.value = setStartDt(selectData.value)
    }
    const afterClick = () => {
      endDt.value = setStartDt(selectData.value, endDt.value, true)
    }
    const searchApi = () => {
      store.dispatch("precision/getMainChart", { endDate: endDt.value, startDate: startDt.value })
    }
    let chartData = store.state.precision.chartDatas
    store.commit('precision/titles', [store.state.precision.chartDatas[0].title, store.state.precision.chartDatas[1].title, store.state.precision.chartDatas[2].title])
    let lastDate = undefined;
    watch(() => store.state.precision.chartDatas[0].data, () => {
      const data1 = store.state.precision.chartDatas[0].data
      chartData[0].data = data1
      lastDate = data1[data1.length - 1]?.at(data1[data1.length - 1].length - 1)?.at(0)?.replaceAll('-', '.')
      store.commit('precision/changeTime', lastDate)
      store.commit('precision/titles', [chartData[0].title, chartData[1].title + (lastDate ? `- (${lastDate})` : ''), chartData[2].title + (lastDate ? `- (${lastDate})` : '')])
      store.dispatch("precision/getTimeWaveChart", { acq_date: data1[data1.length - 1]?.at(data1[data1.length - 1].length - 1)?.at(0) })
      store.dispatch("precision/getSpectrumChart", { acq_date: data1[data1.length - 1]?.at(data1[data1.length - 1].length - 1)?.at(0) })
    })
    watch(() => [store.state.precision.chartDatas[1].data, store.state.precision.chartDatas[2].data], () => {
      chartData[1].data = store.state.precision.chartDatas[1].data
      chartData[2].data = store.state.precision.chartDatas[2].data
    })
    watch(() => [store.state.precision.chartDatas[2].xLines], () => {
      chartData[2].xLines = store.state.precision.chartDatas[2].xLines
    })
    const changeEndDtToCur = () => {
      endDt.value = new Date().toISOString().split('T')[0]
    }
    return {
      store, selectData, startDt, endDt, beforeClick, afterClick, searchApi, chartClick, chartData, changeEndDtToCur, isChartShow
    }
  }
}
</script>

<style>
.ti BtnListtle_wrap {
  height: 40px;
  color: #87a2b5;
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  background: linear-gradient(180deg, rgba(59, 69, 87, 1) 0%, rgba(41, 48, 65, 1) 100%);
}

.card-body {
  background: #171a27;
  border: none;
  padding: 18px 12px !important;
}

ul.btn-list {
  display: flex;
  padding: 3px 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 10px;
}

ul.btn-list li {
  float: left;
}

ul.btn-list li:first-child {
  margin-left: 15px;
}

.btn-default {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 15px;
  color: #000;
  background: #3a4456;
}

.btn-default:hover {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 15px;
  color: #bdc6d8;
  background: #545f75;
}

.btn-default.active {
  background: #4f59d3;
  border: 1px solid #4f59d3;
}

.btn-primary {
  color: #fff;
  background: #0d6ae4;
}

.title_wrap {
  font-size: 20px;
  font-weight: 600;
  color: #8394a0;
  background: #394355;
}

.title-round {
  width: 100%;
  height: 32px;
  text-align: center;
  background: url(@/assets/img/title_tab_round.png) 0 100% no-repeat;
  background-size: 32% 100% !important;
}

.sub-title {
  font-size: 16px;
  font-weight: 400;
  color: #c3eaff;
  padding: 3px 8px;
}

/* 모달 */
.modal-wrap {
  height: 100%;
}

.modal-body {
  height: calc(100% - 31px);
}

.modal-header {
  padding: 5px 10px;
  background: #161d31;
}

.modal-body {
  overflow: hidden;
  padding: 10px 10px 0 10px;
}

.btn-list-group li {
  margin-bottom: 5px;
}

.btn-list-group button {
  color: #fff;
  background: #4c41bb;
}

.btn-list-group button:hover {
  background: #7367f0;
}

.form-control {
  height: 28px;
  font-size: 12px;
  color: #a9abae;
  background-color: #101320;
  border-color: #263650;
  padding: 2px;
}

.form-select {
  height: 28px;
  font-size: 12px;
  background-color: #101320;
  border-color: #263650;
  padding: 2px;
}
</style>