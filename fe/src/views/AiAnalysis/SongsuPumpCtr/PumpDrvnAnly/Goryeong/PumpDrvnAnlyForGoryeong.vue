<template>
  <LoadingSpinner class="loading-container" v-if="isfetch"></LoadingSpinner>
  <!--송수펌프 가동이력 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <b-row>
        <b-col class="title_wrap">
          <BigTitle :title="'운전현황 분석'" />
        </b-col>
        <b-col xl="7" class="d-flex align-items-center">
          <MenuTab ref="MenuTab" @changeData="changeData" />
        </b-col>
        <b-col xl="3" class="d-flex align-items-center justify-content-end">
          <AiMode ref="AiMode" @getAiStatus="getAiStatus" :index="tabIndex + 1" />
        </b-col>
      </b-row>
      <!-- 타이틀 끝 -->

      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container ">
        <b-row cols="12" class="mt-4">
          <template v-if="optLevel && Object.keys(optLevel).length > 0">
            <b-col xl="5">
             <SmallTitle :title="'최적운전 모드 운영 중'" style="margin-bottom: 20px;" />
            </b-col>
            <b-col xl="1">
              <b-row>
                <span class="level_tite_text" style="position:relative; top:10px;">목표 배수지 수위</span>
              </b-row>
              <b-row class="justify-content-center">
                <span class="detail_value d-flex align-items-center"
                :style="{ width: 'auto', fontSize: '16px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px', 'margin-top':'10px' }">{{optLevelData}}</span>
              </b-row>
            </b-col>
            <b-col xl="1">
              <b-row v-for="(value, key) in optLevel" :key="key">
                <div class="d-flex justify-content-evenly align-items-center">
                  <div :style="{ color: '#3789b4', fontSize: '18px', fontWeight: 'bold' }">{{ key }}</div>
                  <span class="detail_value"
                      :style="{ width: 'auto', fontSize: '16px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">{{ value }} M
                  </span>
                </div>
              </b-row>
            </b-col>
            <b-col xl="3" class="d-flex align-items-center" style="padding-bottom: 20px;">
            <div class="d-flex flex-grow-1 align-items-center">
              <select v-model="selectedCycle" class="date_design" @change="handleSelectChange" :style="{
                'background-image': 'url(' + require('@/assets/img/select_btn.png') + ')',
                'background-repeat': 'no-repeat',
                'background-position': 'right'
              }">
                <option value="h">시간</option>
                <option value="m">분</option>
              </select>
            </div>

            <div class="d-flex">
              <button type="button" class="btn btn-sm" :class="{ 'active': isActiveFirTime }"
                @click="clickTime(firTime)">{{ firTime }}</button>
              <button type="button" class="btn btn-sm ml-2" :class="{ 'active': isActiveSecTime }"
                @click="clickTime(secTime)">{{ secTime }}</button>
              <button type="button" class="btn btn-sm ml-2" :class="{ 'active': isActiveThrTime }"
                @click="clickTime(thrTime)">{{ thrTime }}</button>
              <button type="button" class="btn btn-sm ml-2" :class="{ 'active': isActiveFouTime }"
                @click="clickTime(fouTime)">{{ fouTime }}</button>
              <button v-if="selectedCycle == 'h'" type="button" class="btn btn-sm ml-2"
                :class="{ 'active': isActiveFifTime }" @click="clickTime(fifTime)">{{ fifTime }}</button>
            </div>
           </b-col>  
          </template>
          <template v-else>
            <b-col xl="6">
             <SmallTitle :title="'최적운전 모드 운영 중'" style="margin-bottom: 20px;" />
            </b-col>
            <b-col xl="4" class="d-flex align-items-center" style="padding-bottom: 20px;">
            <div class="d-flex flex-grow-1 align-items-center" style="padding-left: 30%;">
              <select v-model="selectedCycle" class="date_design" @change="handleSelectChange" :style="{
                'background-image': 'url(' + require('@/assets/img/select_btn.png') + ')',
                'background-repeat': 'no-repeat',
                'background-position': 'right'
              }">
                <option value="h">시간</option>
                <option value="m">분</option>
              </select>
            </div>

            <div class="d-flex">
              <button type="button" class="btn btn-sm" :class="{ 'active': isActiveFirTime }"
                @click="clickTime(firTime)">{{ firTime }}</button>
              <button type="button" class="btn btn-sm ml-2" :class="{ 'active': isActiveSecTime }"
                @click="clickTime(secTime)">{{ secTime }}</button>
              <button type="button" class="btn btn-sm ml-2" :class="{ 'active': isActiveThrTime }"
                @click="clickTime(thrTime)">{{ thrTime }}</button>
              <button type="button" class="btn btn-sm ml-2" :class="{ 'active': isActiveFouTime }"
                @click="clickTime(fouTime)">{{ fouTime }}</button>
              <button v-if="selectedCycle == 'h'" type="button" class="btn btn-sm ml-2"
                :class="{ 'active': isActiveFifTime }" @click="clickTime(fifTime)">{{ fifTime }}</button>
            </div>
           </b-col>  
          </template>
          <b-col xl="2" class="d-flex align-items-center" style="padding-bottom: 20px; top:20px;">
            <button type="button" class="btn btn-sm" style="margin-left:30px;" @click="getExcel('pre')">
              예측 조회 <span v-if="preExcelLoading" class="spinner" style="margin-left:70px"></span>
            </button>
            <button type="button" class="btn btn-sm" style="margin-left:32px" @click="getExcel('anly')">분석이력
              다운로드 <span v-if="anlyExcelLoading" class="spinner" style="margin-left:119px"></span></button>
          </b-col>
        </b-row>
        <b-row class="mb-1">
          <b-col xl="4">
            <SmallTitle :title="'운영 현황'" :date="curDate"
              :style="{ textAign: 'center', marginBottom: '20px', marginTop: '0px' }" />
            <div class="d-flex flex-row justify-content-between" :style="{ marginTop: '0px' }">
              <div class="text_title_base" :style="{ width: '260px' }">
                <div class="w-100 d-flex flex_center_between" :style="{ height: '40px' }">
                  <div class="content__text-box text-center">
                    {{ pumpName }} <span class="blinking-text">{{ OnOff }}</span>
                  </div>
                </div>
                <div class="w-100 d-flex flex_center_between" :style="{ height: '50px' }">
                  <div class="animationTItle-two" :style="{ height: '30px', color: '#5cebfe' }">
                    <span :style="{ color: '#5cebfe' }">{{ dynamicCurPumpUseHz }}{{ curGongPres }}</span>
                  </div>
                </div>
              </div>
              <div class="plate_img"
                :style="{ width: '295px', height: '100px', backgroundSize: 'contain !important', backgroundPosition: '0 55%' }">
                <div class="d-flex d-flex justify-content-evenly align-items-center">
                  <span class="cal_tite_text">전력</span>
                  <span class="detail_value"
                    :style="{ width: 'auto', fontSize: '46px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">{{
                      isNaN(curPwr) ? 'No Data' : curPwr
                    }}</span>
                  <div :style="{ color: '#3789b4', fontSize: '18px', fontWeight: 'bold' }">kw</div>
                </div>
                <div class="d-flex d-flex justify-content-evenly align-items-center">
                  <span class="cal_tite_text">전력 원단위</span>
                  <span class="detail_value"
                    :style="{ width: 'auto', fontSize: '20px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">{{
                      pwrCurUnit
                    }}</span>
                  <div :style="{ color: '#3789b4', fontSize: '18px', fontWeight: 'bold' }">(kWh/㎥)</div>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-md-12">
                <div style="margin-top: 8px; text-align: center;">
                  <span class="content__text-box text-center"></span>
                  <span class="content__text-box text-center" style="margin-left: 10px; color: #5cebfe"></span>
                </div>
              </div>
              <div class="col-md-12">
                <div :style="{ height: '160px', position: 'relative' }">
                  <div class="btn-group" style="position: absolute; top: -2px; right: 40px; z-index: 1000;">
                    <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForDayAgo }"
                      style="height: 25px; padding-top:1px" @click="wonUnitChart('day')">전일</button>
                    <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForWeekAgo }"
                      style="height: 25px; padding-top:1px" @click="wonUnitChart('week')">지난주</button>
                    <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForMonthAgo }"
                      style="height: 25px; padding-top:1px" @click="wonUnitChart('month')">지난달 평균</button>
                  </div>
                  <LoadingSpinner class="loading-container" v-if="wonLoading"></LoadingSpinner>
                  <area-chart ref="AreaChart" />
                </div>
              </div>
            </div>
          </b-col>
          <b-col xl="4" class="d-flex justify-content-evenly">
            <div class="chart-container" :style="{ width: '600px', height: '367px' }">
              <PlotlyLineChart ref="PlotlyLineChart" />
            </div>
          </b-col>
          <b-col xl="4">
            <SmallTitle :title="'예측 결과'" :date="preDate" style="margin-bottom: 20px; margin-top:0px" />
            <div xl="4" class="d-flex flex-row justify-content-between" :style="{ marginTop: '0px' }">
              <template v-if="this.tabIndex == 0">
                <div class="text_title_base" :style="{ width: '275px', position:'relative', top:'-10px' }">
                  <div class="w-100 d-flex flex_center_between" :style="{ height: '40px' }">
                    <div class="content__text-box text-center" :style="{ position:'relative', top:'6px' }">{{ pumpName }}</div>
                  </div>
                  <div class="w-100 d-flex flex_center_between" :style="{ height: '50px' }">
                    <div class="animationTItle-two" :style="{ height: '30px', color: '#5cebfe' }">
                      {{ dynamicPrePumpUseHz }}
                    </div>
                  </div>
                  <div style="margin-bottom: 5px;">
                      <button type="button" class="btn btn-sm" @click="manualOper('up')">증가</button>
                      <button type="button" class="btn btn-sm" @click="manualOper('down')">감소</button>
                    </div>
                </div>
              </template>
              <template v-if="this.tabIndex == 1">
                <div class="text_title_base" :style="{ width: '260px' }">
                  <div class="w-100 d-flex flex_center_between" :style="{ height: '40px' }">
                    <div class="content__text-box text-center">
                      {{ pumpName }} <span class="blinking-text">{{ OnOff }}</span>
                    </div>
                  </div>
                  <div class="w-100 d-flex flex_center_between" :style="{ height: '50px' }">
                    <div class="animationTItle-two" :style="{ height: '30px', color: '#5cebfe' }">
                      <span :style="{ color: '#5cebfe' }">{{ dynamicPrePumpUseHz }}{{ preGongPres }}</span>
                    </div>
                  </div>
                </div>
              </template>
              <template v-if="this.tabIndex == 2">
                <div class="text_title_base" :style="{ width: '275px', position:'relative', top:'-10px' }">
                  <div class="w-100 d-flex flex_center_between" :style="{ height: '40px' }">
                    <div class="content__text-box text-center" :style="{ position:'relative', top:'6px' }">{{ pumpName }}</div>
                  </div>
                  <div class="w-100 d-flex flex_center_between" :style="{ height: '50px' }">
                    <div class="animationTItle-two" :style="{ height: '30px', color: '#5cebfe' }">
                      {{ dynamicPrePumpUseHz }}
                    </div>
                  </div>
                  <div style="margin-bottom: 5px;">
                      <button type="button" class="btn btn-sm" @click="pumpStop()">PUMP STOP</button>
                      <button type="button" class="btn btn-sm" @click="pumpStart()">PUMP START</button>
                    </div>
                </div>
              </template>
              <div class="plate_img"
                :style="{ width: '295px', height: '100px', backgroundSize: 'contain !important', backgroundPosition: '0 55%' }">
                <div class="d-flex d-flex justify-content-evenly align-items-center">
                  <span class="cal_tite_text">전력</span>
                  <span class="detail_value"
                    :style="{ width: 'auto', fontSize: '46px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">{{
                      isNaN(prePwr) ? 'No Data' : prePwr }}</span>
                  <div :style="{ color: '#3789b4', fontSize: '18px', fontWeight: 'bold' }">kw</div>
                </div>
                <div class="d-flex d-flex justify-content-evenly align-items-center">
                  <span class="cal_tite_text">전력 원단위</span>
                  <span class="detail_value"
                    :style="{ width: 'auto', fontSize: '20px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">{{
                      pwrPreUnit
                    }}</span>
                  <div :style="{ color: '#3789b4', fontSize: '18px', fontWeight: 'bold' }">(kWh/㎥)</div>
                  <span
                    :style="{ fontSize: '18px', fontWeight: 'bold', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">({{
                      ((pwrPreUnit - pwrCurUnit) / pwrCurUnit * 100).toFixed(2) }}%)</span>

                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-md-12">
                <div style="margin-top: 8px; text-align: center;">
                  <span class="content__text-box text-center">{{ load }}</span>
                  <span class="content__text-box text-center" style="margin-left: 10px; color: #5cebfe">{{ oprtn
                    }}</span>
                </div>
              </div>
              <div class="col-md-12">
                <div :style="{ height: '160px', position: 'relative' }">
                  <div class="btn-group" style="position: absolute; top: -2px; right: 35px; z-index: 1000;">
                    <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForDayAgo }"
                      style="height: 25px; padding-top:1px" @click="wonUnitChart('day')">전일</button>
                    <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForWeekAgo }"
                      style="height: 25px; padding-top:1px" @click="wonUnitChart('week')">지난주</button>
                    <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForMonthAgo }"
                      style="height: 25px; padding-top:1px" @click="wonUnitChart('month')">지난달 평균</button>
                  </div>
                  <LoadingSpinner class="loading-container" v-if="wonLoading"></LoadingSpinner>
                  <area-chart ref="AreaChart1" />
                </div>
              </div>
            </div>


          </b-col>
        </b-row>
        <b-row>
          <b-col>
          </b-col>

        </b-row>
        <b-row class="mt-3">
          <b-col xl="4" class="">
            <div class="bottom_line_bg" :style="{ height: '440px' }">
              <div class="btn-group mb-3">
                <button type="button" class="btn btn-sm" :class="{ 'active': false }">성능 및 저항곡선</button>
              </div>
              <div class=" w-100" :style="{ height: '85%', background: 'transparent', boxShadow: '0 0 0 0.1px white' }">
                <div class="chart-container" style="position: relative;">
                  <LoadingSpinner class="loading-container" v-if="isLoading"></LoadingSpinner>
                  <ScatterChart ref="ScatterChart1" :style="{ height: '410px', width: '100%' }" />
                </div>

              </div>
            </div>
          </b-col>
          <b-col xl="4" class="">
            <!-- TODO: 기능 정의되면 주석 해제 -->
            <!-- <div class="d-flex justify-content-evenly align-items-center"
              :style="{ height: '50px', marginBottom: '20px' }"> -->
            <!-- <button type="button" class="btn btn-sm active">펌프 성능곡선 업데이트</button>
              <button type="button" class="btn btn-sm">시스템 저항곡선</button>
              <button type="button" class="btn btn-sm">상세 관압(수요량) 조회</button> -->
            <!-- </div> -->
            <div class="d-flex justify-content-center">
              <div class="btn-group">
                <button type="button" class="btn btn-sm" :class="{ 'active': isFlowActive }"
                  @click="clickFlow()">수요량</button>
                <button type="button" class="btn btn-sm" :class="{ 'active': isPresActive }"
                  @click="clickPres()">관압</button>
                <button type="button" class="btn btn-sm" :class="{ 'active': isLevelActive }"
                  @click="clickLevel()">수위</button>
              </div>
            </div>
            <div class="row g-2">
              <b-row class="row-cols-1 g-2 text-center">
                <b-col xl="5" class="detail_text" style="width:41%">현재</b-col>
                <b-col xl="2" :style="{ color: '#3789b4' }">{{ unit }}</b-col>
                <b-col xl="5" :style="{ textShadow: '0 0 9px #ffff99', color: '#ffff99' }">예측</b-col>
              </b-row>
              <div class="row g-2"
                :style="{ overflowY: isPresActive === true && tabIndex === 1 ? 'scroll' : 'visible', height: botMidHeight }">
                <PumpDrvnAnlyBotMid ref="PumpDrvnAnlyBotMid" v-for="(item, i) in title" :key="i" :title=item
                  :cur="botMidCur[i]" :pre="botMidPre[i]" :rate="rate[i]" :botMidCellHeight="botMidCellHeight" />
              </div>
            </div>
          </b-col>
          <b-col xl="4" class="">
            <div class="bottom_line_bg" :style="{ height: '440px' }">
              <div class="btn-group mb-3">
                <button type="button" class="btn btn-sm" :class="{ 'active': false }">성능 및 저항곡선</button>
              </div>
              <div class="w-100" :style="{ height: '85%', background: 'transparent', boxShadow: '0 0 0 0.1px white' }">
                <div class="chart-container" style="position: relative;">
                  <LoadingSpinner class="loading-container" v-if="isLoading"></LoadingSpinner>
                  <ScatterChart ref="ScatterChart2" :style="{ height: '410px', width: '100%' }" />
                </div>
              </div>
            </div>
          </b-col>
        </b-row>

      </div>
    </b-container>

  </div>
</template>

<script>
import LoadingSpinner from '@/components/ComponentCommon/LoadingSpinner.vue';
import BigTitle from '@/components/ComponentCommon/BigTitle.vue';
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
import ScatterChart from '@/components/Chart/ScatterChart.vue'
import ScatterChartClass from '@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/ScatterChartClass'
import { fetchFunc } from '@/util/fetchFunc';
import PumpDrvnAnlyBotMid from '@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/PumpDrvnAnlyBotMid.vue'
import { setPresData, setFlowData, setLevelData, ExcelDown } from '@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/PumpDrvnAnlyFunction'
import PlotlyLineChart from '@/components/Chart/PlotlyLineChartForHz.vue'
import MenuTab from '@/views/Common/MenuTab.vue';
import AiMode from '@/views/Common/AiMode.vue';
import { useStore } from "vuex";
import AreaChart from '@/components/Chart/AreaChart.vue';
import ChartClass from '@/components/Chart/LineBarChartClass';
import Swal from 'sweetalert2'
export default {
  components: {
    BigTitle,
    SmallTitle,
    ScatterChart,
    LoadingSpinner,
    PumpDrvnAnlyBotMid,
    PlotlyLineChart,
    AiMode,
    MenuTab,
    AreaChart
  },
  data() {
    return {
      store: useStore(),
      pumpName: '고령(생활)',
      tabIndex: 0,
      isLoading: false,
      preExcelLoading: false,
      anlyExcelLoading: false,
      selectedCycle: 'm',
      isActiveTab: true,
      isPresActive: false,
      isFlowActive: true,
      isLevelActive: false,
      isActiveFirTime: true,
      isActiveSecTime: false,
      isActiveThrTime: false,
      isActiveFouTime: false,
      isActiveFifTime: false,
      title: ["고령(생활)<br/>정수장", "다산면<br/>분기", "다산산단(생)<br/>분기", "고령통합<br/>분기", "선남<br/>가압장"],
      levelTitle: ["다산면<br/>배수지", "다산산단(생)<br/>배수지"],
      presTag: ["780-344-PRI-4001", "780-344-PRI-8012", "780-344-PRI-8019", "780-344-PRI-8007", "780-379-SWI-1003"],
      flowTag: ["780-344-FIT-2502", "780-344-FRI-8015", "780-344-FRI-8012", "780-344-FRI-8007", "780-344-FRI-5002"],
      levelTag: ["780-344-LEI-8023", "780-344-LEI-8020"],
      presThres: [],
      curDate: '',
      preDate: '',
      curPwr: 0,
      prePwr: 0,
      botMidCur: [],
      botMidCurFlow: [],
      botMidCurPres: [],
      botMidPre: [],
      rate: [],
      saving: '',
      firTime: '4시간',
      secTime: '12시간',
      thrTime: '24시간',
      fouTime: '48시간',
      fifTime: '30일',
      cycle: 5,
      range: 4,
      unit: 'unit',
      pwrCurUnit: '',
      pwrPreUnit: '',
      isActiveForDayAgo: true,
      isActiveForWeekAgo: false,
      isActiveForMonthAgo: false,
      curChartLabels: ["운영", "전일", "펌프 대수"],
      time: '',
      wonLoading: false,
      botMidHeight: '350px',
      dynamicCurPumpUseHz: null,
      dynamicCurPumpUseHzForB: null,
      dynamicPrePumpUseHz: null,
      dynamicPrePumpUseHzForB: null,
      load: '',
      oprtn: '',
      isfetch: false,
      botMidCellHeight: '68px',
      selectedPump: '',
      OnOff: '',
      curGongPres: '',
      preGongPres: '',
      optLevel: null,
      optLevelData : null
    }
  },
  mounted() {
    this.isLoading = true
    this.wonLoading = true
    this.fetchData();
    this.startTimer();
    setInterval(this.updateTime, 1000);
    this.updateTime();
    this.$emit("onChangeBgClass", false);
    this.getAiStatus()
    const now = new Date();
    const minutes = now.getMinutes();
    const seconds = now.getSeconds();
    const milliseconds = now.getMilliseconds();

    const nextRunInMinutes = 5 - (minutes % 5);
    const nextRunInMillis = (nextRunInMinutes * 60 * 1000) - (seconds * 1000) - milliseconds + 10000;

    setTimeout(async () => {
      await this.fetchData();
      setInterval(async () => {
        await this.fetchData();
      }, 5 * 60 * 1000);
      setInterval(() => {
        location.reload(true); // 페이지를 새로고침
      }, 6 * 60 * 60 * 1000); // 6시간 간격으로 실행되도록 새로운 setInterval을 설정
    }, nextRunInMillis);
  },
  methods: {
    async fetchChartData(params) {
      return await fetchFunc(`${this.$apiURL}/dr/systemResistanceCurves`, params);
    },
    async fetchData() {
      this.getAiStatus()
      this.isfetch = true
      this.time = await this.getDateParams()
      let paramPrefix = this.setParamPrefix()
      const ploty_xDate = []
      const ploty_flowData = []
      const ploty_presData = []
      const value = await Promise.allSettled([
        this.fetchChartData(this.createParams(this.time, 'cur', this.tabIndex + 1, ["A4", "A1", "A7"], this.cycle, this.range)),
        this.fetchChartData(this.createParams(this.time, 'pre', this.tabIndex + 1, ["A4", "A1", "A7"], this.cycle, this.range)),
        fetchFunc(`${this.$apiURL}/dr/getPumpUse?startDate=${this.time}&cycle=${this.cycle}&range=${this.range}&pump_grp=${this.tabIndex + 1}`),
        fetchFunc(`${this.$apiURL}/dr/predictionPumpCombination?startDate=${this.time}&cycle=${this.cycle}&range=${this.range}&pump_grp=${this.tabIndex + 1}`),
        fetchFunc(`${this.$apiURL}/dr/selectIntradotion?startDate=${this.time}&opt_idx=cur`),
        fetchFunc(`${this.$apiURL}/dr/selectIntradotion?startDate=${this.time}&opt_idx=pre`),
        fetchFunc(`${this.$apiURL}/dr/selectPumpCombCal`),
        fetchFunc(`${this.$apiURL}/dr/grOptLevel?pump_grp=${this.tabIndex + 1}`),
      ]);
      this[`${paramPrefix}CurData`] = value[0].status === 'fulfilled' ? value[0].value : null;
      this[`${paramPrefix}PreData`] = value[1].status === 'fulfilled' ? value[1].value : null;
      this.historyData = value[2].status === 'fulfilled' ? value[2].value.data : null;
      this.preHistoryData = value[3].status === 'fulfilled' ? value[3].value.data : null;
      const botMidCurData = value[4].status === 'fulfilled' ? value[4].value : null;
      const botMidPreData = value[5].status === 'fulfilled' ? value[5].value : null;
      this.pumpCombCal = value[6].status === 'fulfilled' ? value[6].value : null;
      
      if (value[7].status === 'fulfilled' && value[7].value.data) {
        const data = value[7].value.data;

       
        this.optLevelData = data.time || null;
        this.optLevel = { ...data };
        delete this.optLevel.time;
      } else {
        
        this.optLevel = null;
        this.optLevelData = null;
      }

      this.isfetch = false
      this.combCal = this.pumpCombCal.data.filter(item => item.PUMP_GRP == this.tabIndex + 1)

      Object.keys(this.historyData).forEach((item) => {
        if (this.historyData?.freq?.[item]) { // freq와 freq[item]이 존재하는지 확인
          this.historyData[item].forEach((element, i) => {
            if (this.historyData.freq[item][i] != 0) {
              if (element === 1) this.historyData[item][i] += this.historyData.freq[item][i] - 1
            } else {
              if (element === 1) this.historyData[item][i] += this.historyData.freq[item][i] - 0.0001
            }
          });
        }
        else if (item !== 'freq') {
          this.historyData[item].forEach((element, i) => {
            if (element === 1) this.historyData[item][i] -= 0.0001
          });
        }
      });
      delete this.historyData?.freq;

      Object.keys(this.preHistoryData).forEach((item) => {
        if (this.preHistoryData?.freq?.[item]) { // freq와 freq[item]이 존재하는지 확인
          this.preHistoryData[item].forEach((element, i) => {
            if (this.preHistoryData.freq[item][i] != 0) {
              if (element === 1) this.preHistoryData[item][i] += this.preHistoryData.freq[item][i] - 1.0001
            } else {
              if (element === 1) this.preHistoryData[item][i] += this.preHistoryData.freq[item][i] - 0.0002
            }
          });
        }
        else if (item !== 'freq') {
          this.preHistoryData[item].forEach((element, i) => {
            if (element === 1) this.preHistoryData[item][i] -= 0.0002
          });
        }
      });
      delete this.preHistoryData?.freq;
      this.curTs = botMidCurData.data?.ts
      this.preTs = botMidPreData.data?.ts
      this.botMidCurFlowData = botMidCurData.data?.flow
      this.botMidCurPresData = botMidCurData.data?.pressure
      this.botMidPreFlowData = botMidPreData.data?.flow
      this.botMidPrePresData = botMidPreData.data?.pressure
      this.botMidCurLevelData = botMidCurData.data?.level
      //방어 로직
      for (let key in this.botMidPrePresData) {
        if (Object.prototype.hasOwnProperty.call(this.botMidPrePresData, key)) {
          let value = this.botMidPrePresData[key];
          while (value.length < this.preTs.length) {
            value.push(value[value.length - 1])
          }
        }
      }
      for (let key in this.botMidPreFlowData) {
        if (Object.prototype.hasOwnProperty.call(this.botMidPreFlowData, key)) {
          let value = this.botMidPreFlowData[key];
          while (value.length < this.preTs.length) {
            value.push(value[value.length - 1])
          }
        }
      }
      this.setTopData();
      setFlowData.call(this);
      setPresData.call(this);
      this.clickFlow()
      this[`${paramPrefix}PreData`]?.data?.forEach(element => {
        ploty_xDate.push(element.date)
        ploty_flowData.push((element.flow).toFixed(0))
        ploty_presData.push((element.pressure).toFixed(2))
      })
      this.wonUnitChart('day')
      this.createChart(this[`${paramPrefix}CurData`], 'cur', paramPrefix)
      this.createChart(this[`${paramPrefix}PreData`], 'pre', paramPrefix)
      this.$refs.PlotlyLineChart.makeChart(ploty_xDate, Object.keys(this.historyData), Object.values(this.historyData), this.selectedCycle, '', ploty_flowData, ploty_presData, Object.values(this.preHistoryData))
    },
    //상단 데이터 설정 메소드 
    setTopData() {
      let paramPrefix = this.setParamPrefix()
      if (this[`${paramPrefix}CurData`]?.data) {
        this[`${paramPrefix}CurPwr`] = this[`${paramPrefix}CurData`]?.data[this[`${paramPrefix}CurData`]?.data?.length - 1]?.pwr;
        this[`${paramPrefix}CurPumpUse`] = this[`${paramPrefix}CurData`]?.data[this[`${paramPrefix}CurData`]?.data?.length - 1]?.pumpUse;
        this[`${paramPrefix}PrePwr`] = this[`${paramPrefix}PreData`]?.data[this[`${paramPrefix}PreData`]?.data?.length - 1]?.pwr;
        this[`${paramPrefix}PrePumpUse`] = this[`${paramPrefix}PreData`]?.data[this[`${paramPrefix}PreData`]?.data?.length - 1]?.pumpUse;
        this[`${paramPrefix}Load`] = this[`${paramPrefix}PreData`]?.data[this[`${paramPrefix}PreData`]?.data?.length - 1]?.load;
        this[`${paramPrefix}Oprtn`] = this[`${paramPrefix}PreData`]?.data[this[`${paramPrefix}PreData`]?.data?.length - 1]?.oprtn;
        this[`${paramPrefix}CurHz`] = this.getValues(this[`${paramPrefix}CurData`]?.data[this[`${paramPrefix}CurData`]?.data?.length - 1].freq, this[`${paramPrefix}CurPumpUse`]);
        this[`${paramPrefix}PreHz`] = this.getValues(this[`${paramPrefix}PreData`]?.data[this[`${paramPrefix}PreData`]?.data?.length - 1].freq, this[`${paramPrefix}PrePumpUse`]);
        this.settingUseHz();

        if (this[`${paramPrefix}Load`] === 'L') this[`${paramPrefix}Load`] = '경부하';
        if (this[`${paramPrefix}Load`] === 'M') this[`${paramPrefix}Load`] = '중부하';
        if (this[`${paramPrefix}Load`] === 'H') this[`${paramPrefix}Load`] = '최대부하';

        if (this[`${paramPrefix}Oprtn`] === 'none') this[`${paramPrefix}Oprtn`] = '';
        if (this[`${paramPrefix}Oprtn`] === 'high') this[`${paramPrefix}Oprtn`] = '펌프 추가운영';
        if (this[`${paramPrefix}Oprtn`] === 'low') this[`${paramPrefix}Oprtn`] = '펌프 절감운영';

        this.curDate = this[`${paramPrefix}CurData`]?.data[this[`${paramPrefix}CurData`]?.data?.length - 1].date;
        this.preDate = this[`${paramPrefix}PreData`]?.data[this[`${paramPrefix}PreData`]?.data?.length - 1].date;

        this.curPwr = this[`${paramPrefix}CurPwr`]?.toFixed(0);
        this.prePwr = this[`${paramPrefix}PrePwr`]?.toFixed(0);
        this[`${paramPrefix}CurPumpOrder`] = [];
        this[`${paramPrefix}PrePumpOrder`] = [];

        this[`${paramPrefix}CurPumpUse`]?.forEach(item => {
          let parts = item.split("#");
          this[`${paramPrefix}CurPumpOrder`].push(parts[1].toString());
        });

        this[`${paramPrefix}PrePumpUse`]?.forEach(item => {
          let parts = item.split("#");
          this[`${paramPrefix}PrePumpOrder`].push(parts[1].toString());
        });
        if (this.tabIndex == 2 && this[`${paramPrefix}CurPumpUse`].length == 0) {
          this.OnOff = '(가동중지)'
        }
        else {
          this.OnOff = ''
        }
        // console.log("curPres", this.botMidCurPresData['780-344-PRC-6004'][this.botMidCurPresData['780-344-PRC-6004'].length - 1]?.toFixed(1))
        // console.log("prePres", this.botMidPrePresData['780-344-PRC-6004'][this.botMidPrePresData['780-344-PRC-6004'].length - 1]?.toFixed(1))
        // if (Object.keys(this.botMidCurPresData).length != 0) {
        //   if (this.tabIndex == 1 && this.botMidCurPresData['780-344-PRC-6004'].length > 0) {
        //     this.curGongPres = '[' + this.botMidCurPresData['780-344-PRC-6004'][this.botMidCurPresData['780-344-PRC-6004'].length - 1]?.toFixed(1) + 'kgf/c㎡]'
        //     this.preGongPres = '[' + this.botMidPrePresData['780-344-PRC-6004'][this.botMidPrePresData['780-344-PRC-6004'].length - 1]?.toFixed(1) + 'kgf/c㎡]'
        //   }
        //   else {
        //     this.curGongPres = ''
        //     this.preGongPres = ''
        //   }
        // }
        this.saving = ((this.curPwr - this.prePwr) / this.curPwr * 100).toFixed(1)
        this.load = this[`${paramPrefix}Load`]
        this.oprtn = this[`${paramPrefix}Oprtn`]
      }
    },
    clickPres() {
      this.botMidHeight = '250px'
      this.unit = 'kgf/c㎡'
      this.title = this.getTitle(this.tabIndex).pres
      this.presTag = this.getTag(this.tabIndex).pres
      this.$nextTick(() => {
        setPresData.call(this);
      });
      this.isPresActive = true;
      this.isFlowActive = false;
      this.isLevelActive = false;
      if (this.tabIndex == 1) {
        this.botMidHeight = '350px'
        this.botMidCellHeight = '50px'
      } else {
        this.botMidCellHeight = '50px'
        this.botMidHeight = '250px'
      }
    },
    clickFlow() {
      this.botMidHeight = '250px'
      this.unit = 'm³/hr'
      this.title = this.getTitle(this.tabIndex).flow
      this.flowTag = this.getTag(this.tabIndex).flow
      this.$nextTick(() => {
        setFlowData.call(this);
      });
      this.isPresActive = false;
      this.isFlowActive = true;
      this.isLevelActive = false;
      this.botMidCellHeight = '50px'
    },
    clickLevel() {
      this.botMidHeight = '100px'
      this.unit = 'm'
      this.title = this.getTitle(this.tabIndex).level
      this.levelTag = this.getTag(this.tabIndex).level
      this.$nextTick(() => {
        setLevelData.call(this);
      });
      this.isPresActive = false;
      this.isFlowActive = false;
      this.isLevelActive = true;
      this.botMidCellHeight = '50px'
    },
    clickTime(time) {
      this.isLoading = true
      switch (time) {
        case '3일':
        case '4시간':
          this.setActiveTime(true, false, false, false, false, time === '3일' ? 60 : 5, time === '3일' ? 3 * 24 : 4);
          break;
        case '5일':
        case '12시간':
          this.setActiveTime(false, true, false, false, false, time === '5일' ? 60 : 5, time === '5일' ? 5 * 24 : 12);
          break;
        case '10일':
        case '24시간':
          this.setActiveTime(false, false, true, false, false, time === '10일' ? 60 : 5, time === '10일' ? 10 * 24 : 24);
          break;
        case '20일':
        case '48시간':
          this.setActiveTime(false, false, false, true, false, time === '20일' ? 60 : 5, time === '20일' ? 20 * 24 : 48);
          break;
        case '30일':
          this.setActiveTime(false, false, false, false, true, 60, 30 * 24);
          break;
        // default:
      }
    },
    async setActiveTime(isFir, isSec, isThr, isFou, isFif, cycleValue, rangeValue) {
      this.isActiveFirTime = isFir;
      this.isActiveSecTime = isSec;
      this.isActiveThrTime = isThr;
      this.isActiveFouTime = isFou;
      this.isActiveFifTime = isFif;
      this.cycle = cycleValue;
      this.range = rangeValue;
      await this.fetchData();
      this.isLoading = false
    },
    handleSelectChange(event) {
      const value = event.target.value;
      if (value === 'h') {
        this.firTime = '3일'
        this.secTime = '5일'
        this.thrTime = '10일'
        this.fouTime = '20일'
        this.fifTime = '30일'
      } else if (value === 'm') {
        this.firTime = '4시간'
        this.secTime = '12시간'
        this.thrTime = '24시간'
        this.fouTime = '48시간'
      }
      this.clickTime(this.firTime)
    },
    createChart(data, flag, tab) {
      let ChartClass
      // isA1, isA4, isA7 표시여부 없으면 true
      if (flag == 'cur') {
        ChartClass = new ScatterChartClass(data, this[`${tab}CurPumpUseHz`], this.combCal, true, true, true, 0.5)
        this.$refs.ScatterChart1.changeData(ChartClass)
      }
      else if (flag == 'pre') {
        ChartClass = new ScatterChartClass(data, this[`${tab}PrePumpUseHz`], this.combCal, true, true, true, 0.5)
        this.$refs.ScatterChart2.changeData(ChartClass)
      }
      this.isLoading = false
    },
    async createLineBarChart(time) {
      this.wonLoading = true
      this.time = await this.getDateParams()
      let curData = (await fetchFunc(`${this.$apiURL}/dr/pumpPwrSrcUnitData?opt_idx=cur&nowDate=${this.time}&time=${time}&pump_grp=${this.tabIndex + 1}`)).data;
      let preData = (await fetchFunc(`${this.$apiURL}/dr/pumpPwrSrcUnitData?opt_idx=pre&nowDate=${this.time}&time=${time}&pump_grp=${this.tabIndex + 1}`)).data;
      if (!isNaN(curData?.nowPwrCost)) this.pwrCurUnit = curData?.nowPwrCost?.toFixed(3)
      if (!isNaN(preData?.nowPwrCost)) this.pwrPreUnit = preData?.nowPwrCost?.toFixed(3)
      while (preData?.plusPwrCostLust.length < preData?.dateTime[0]?.length) {
        preData?.plusPwrCostLust.push(preData?.plusPwrCostLust[preData?.plusPwrCostLust.length - 1])
      }

      let dataY = []
      let preDataY = []
      let formattedDates = curData?.dateTime[0]?.map(dateTime => {
        const date = new Date(dateTime)
        return `${date.getDate()}일 ${String(date.getHours()).padStart(2, '0')}`;
      });

      dataY.push(curData?.nowPwrCostList)
      dataY.push(curData?.plusPwrCostLust)
      dataY.push(curData?.pumpComb)
      preDataY.push(preData?.nowPwrCostList)
      preDataY.push(preData?.plusPwrCostLust)
      preDataY.push(preData?.pumpComb)
      let chartClass
      chartClass = new ChartClass(formattedDates, dataY, this.curChartLabels, ' ', 'kWh/㎥', true)
      chartClass.setGridSize('2%', '-5%', '20%', '0%')

      let chartClassForPre
      let preChartLabels = ["운영", "예측", "펌프 대수"]
      chartClassForPre = new ChartClass(formattedDates, preDataY, preChartLabels, ' ', 'kWh/㎥', true, true)
      chartClassForPre.setGridSize('2%', '-5%', '20%', '0%')
      this.wonLoading = false
      this.$refs.AreaChart.changeData(chartClass)
      this.$refs.AreaChart1.changeData(chartClassForPre)
    },
    wonUnitChart(time) {
      if (time === 'day') {
        this.curChartLabels = ["운영", "전일", "펌프 대수"]
        this.createLineBarChart(time)
        this.isActiveForDayAgo = true
        this.isActiveForWeekAgo = false
        this.isActiveForMonthAgo = false
      } else if (time === 'week') {
        this.curChartLabels = ["운영", "지난주", "펌프 대수"]
        this.createLineBarChart(time)
        this.isActiveForDayAgo = false
        this.isActiveForWeekAgo = true
        this.isActiveForMonthAgo = false
      } else if (time === 'month') {
        this.curChartLabels = ["운영", "지난달", "펌프 대수"]
        this.createLineBarChart(time)
        this.isActiveForDayAgo = false
        this.isActiveForWeekAgo = false
        this.isActiveForMonthAgo = true
      }
    },
    updateTime() {
      let DayFrom = new Date();
      const year = DayFrom.getFullYear();
      const month = String(DayFrom.getMonth() + 1).padStart(2, "0");
      const day = String(DayFrom.getDate()).padStart(2, "0");
      const hour = DayFrom.getHours();
      const min = DayFrom.getMinutes();
      const preTime = new Date().setMinutes(new Date().getMinutes() + 5)
      const preYear = new Date(preTime).getFullYear();
      const preMonth = String(new Date(preTime).getMonth() + 1).padStart(2, "0");
      const preDay = String(new Date(preTime).getDate()).padStart(2, "0");
      const preHour = new Date(preTime).getHours();
      const preMin = new Date(preTime).getMinutes()
      const sec = DayFrom.getSeconds();
      const search = `${year}.${month}.${day} ${hour}:${min}:${sec}`;
      const preSearch = `${preYear}.${preMonth}.${preDay} ${preHour}:${preMin}:${sec}`;
      this.currentTime = search;
      this.preTime = preSearch;
    },
    startTimer() {
      this.timerInterval = setInterval(this.updateTimer, 1000);
    },
    updateTimer() {
      if (this.minutes === 0 && this.seconds === 0) {
        clearInterval(this.timerInterval);
      } else {
        if (this.seconds === 0) {
          this.minutes--;
          this.seconds = 59;
        } else {
          this.seconds--;
        }
      }
    },
    /**
     * @param {string} startDate 시작날짜
     * @param {string} opt_idx 'cur' or 'pre'
     * @param {int} pump_grp 펌프 그룹 번호
     * @param {array} grp_nm 수두손실 그룹 배열
     * @param {int} cycle 데이터 주기 (ex.60) 이면 1시간 주기
     * @param {int} range 총 데이터 시간 (ex.48) 이면 48시간 데이터
     */
    createParams(startDate, opt_idx, pump_grp, grp_nm, cycle, range) {
      return {
        "startDate": startDate,
        "opt_idx": opt_idx,
        "pump_grp": pump_grp,
        "grp_nm": grp_nm,
        "cycle": cycle,
        "range": range
      };
    },
    async getDateParams() {
      let time = (await fetchFunc(`${this.$apiURL}/dr/getServerTime`)).data
      return time
    },
    getExcel(type) {
      ExcelDown.call(this, type)
    },
    changeData(index) {
      this.tabIndex = index
      this.fetchData()
      let paramPrefix = this.setParamPrefix()
      this.curDate = this[`${paramPrefix}CurData`]?.data[this[`${paramPrefix}CurData`]?.data?.length - 1].date
      this.preDate = this[`${paramPrefix}PreData`]?.data[this[`${paramPrefix}PreData`]?.data?.length - 1].date
      this.curPwr = this[`${paramPrefix}CurPwr`]?.toFixed(0)
      this.prePwr = this[`${paramPrefix}PrePwr`]?.toFixed(0)
      setFlowData.call(this);
      setPresData.call(this);
      // setLevelData.call(this);
      this.clickFlow()
      this.getAiStatus()
      if (index == 0) {
        this.pumpName = '고령(생활)'
        this.$refs.AiMode.changeAuto(this.$store.state.firAiFlag)
      } else if (index == 1) {
        this.pumpName = '고령(공업)'
        this.$refs.AiMode.changeAuto(this.$store.state.secAiFlag)
      } else if (index == 2) {
        this.pumpName = '선남가압장'
        this.$refs.AiMode.changeAuto(this.$store.state.thrAiFlag)
      }
    },
    getValues(data, keys) {
      let array = []
      if (data) {
        keys.forEach(key => {
          if (key in data) {
            array.push(`${data[key].toFixed(0)}Hz`)
          } else {
            array.push(`0Hz`)
          }
        });
      }
      return array
    },
    settingUseHz() {
      let paramPrefix = this.setParamPrefix()
      this[`${paramPrefix}CurPumpUseHz`] = this[`${paramPrefix}CurPumpUse`]?.map((item, i) => {
        if (this[`${paramPrefix}CurHz`][i] != undefined && this[`${paramPrefix}CurHz`][i] != '0Hz') return `${item}(${this[`${paramPrefix}CurHz`][i]?.toString().replace(/,/g, ", ")})`;
        else return `${item}`;
      }).toString().replace("\"", "").replace(/,/g, ", ");
      this[`${paramPrefix}PrePumpUseHz`] = this[`${paramPrefix}PrePumpUse`]?.map((item, i) => {
        if (this[`${paramPrefix}PreHz`][i] != undefined && this[`${paramPrefix}PreHz`][i] != '0Hz') return `${item}(${this[`${paramPrefix}PreHz`][i]?.toString().replace(/,/g, ", ")})`;
        else return `${item}`;
      }).toString().replace("\"", "").replace(/,/g, ", ");
      this.dynamicCurPumpUseHz = this[`${this.setParamPrefix()}CurPumpUseHz`];
      this.dynamicPrePumpUseHz = this[`${this.setParamPrefix()}PrePumpUseHz`];
    },
    async getAiStatus() {
      const dataAi = await fetchFunc(`${this.$apiURL}/ai/selectAiStatus`);
      let firPumpStatus = dataAi?.data[0]?.AI_STATUS
      let secPumpStatus = dataAi?.data[1]?.AI_STATUS
      let thrPumpStatus = dataAi?.data[2]?.AI_STATUS

      this.$store.state.firAiFlag = parseInt(firPumpStatus)
      this.$store.state.secAiFlag = parseInt(secPumpStatus)
      this.$store.state.thrAiFlag = parseInt(thrPumpStatus)
      if (this.tabIndex === 0) this.$refs.AiMode.changeAuto(this.$store.state.firAiFlag)
      if (this.tabIndex === 1) this.$refs.AiMode.changeAuto(this.$store.state.secAiFlag)
      if (this.tabIndex === 2) this.$refs.AiMode.changeAuto(this.$store.state.thrAiFlag)
    },
    setParamPrefix() {
      let paramPrefix
      if (this.tabIndex === 0) paramPrefix = 'old'
      else if (this.tabIndex === 1) paramPrefix = 'new'
      else if (this.tabIndex === 2) paramPrefix = 'thr'
      else if (this.tabIndex === 3) paramPrefix = 'fou'

      return paramPrefix
    },
    getTitle(idx) {
      let title = {}
      if (idx === 0) {
        title.pres = ["고령(생활)<br/>정수장", "다산면<br/>분기", "다산산단(생)<br/>분기", "고령통합<br/>분기", "선남<br/>가압장"]
        title.flow = ["고령(생활)<br/>정수장", "다산면<br/>분기", "다산산단(생)<br/>분기", "고령통합<br/>분기", "선남<br/>가압장"]
        title.level = ["다산면<br/>배수지", "다산산단(생)<br/>배수지"]
      } else if (idx === 1) {
        title.pres = ["고령(공업)<br/>정수장", "(공)압력<br/>목표설정값", "달성1차<br/>분기", "테크노폴리스<br/>분기", "다산산단(공)<br/>분기", "달성2차<br/>분기"]
        title.flow = ["고령(공업)<br/>정수장", "달성1차<br/>분기", "테크노폴리스<br/>분기", "다산산단(공)<br/>분기"]
        title.level = ["달성1차<br/>배수지", "달성2차<br/>배수지", "다산산단(공)<br/>배수지"]
      } else if (idx === 2) {
        title.pres = ["선남<br/>가압장", "선남<br/>분기", "성주<br/>1분기", "성주<br/>2분기", "벽진<br/>분기"]
        title.flow = ["선남<br/>가압장", "선남<br/>분기", "성주<br/>1분기", "성주<br/>2분기", "벽진<br/>분기"]
        title.level = ["선남<br/>배수지", "성주통합<br/>배수지"]
      }
      return title
    },
    getTag(idx) {
      let tag = {}
      if (idx === 0) {
        tag.pres = ["780-344-PRI-4001", "780-344-PRI-8012", "780-344-PRI-8019", "780-344-PRI-8007", "780-379-SWI-1003"]
        tag.flow = ["780-344-FIT-2502", "780-344-FRI-8015", "780-344-FRI-8012", "780-344-FRI-8007", "780-344-FRI-5002"]
        tag.level = ["780-344-LEI-8023", "780-344-LEI-8020"]
      } else if (idx === 1) {
        tag.pres = ["780-344-PRI-6004", "780-344-PRC-6004", "780-344-PRI-8017", "780-344-PRI-8027", "780-344-PRI-8013", "780-344-PRI-8018"]
        tag.flow = ["780-344-FIT-2501", "780-344-FRI-8010", "780-344-FRI-8027", "780-344-FRI-8009"]
        tag.level = ["780-344-LEI-8001", "780-344-LEI-8017", "780-344-LEI-8012"]
      } else if (idx === 2) {
        tag.pres = ["780-379-PRI-1007", "780-344-PRI-8004", "780-344-PRI-8044", "780-344-PRI-8045", "780-344-PRI-8046"]
        tag.flow = ["780-344-FRI-5002", "780-344-FRI-8004", "780-344-FRI-8054", "780-344-FRI-8056", "780-344-FRI-8058"]
        tag.level = ["780-344-LEI-8038", "780-344-LEI-8040"]
      }
      return tag
    },
    async pumpStop() {
      const today = new Date();
      const day = today.getDate();

      if (day % 2 === 0) {
        this.selectedPump = 2
      } else {
        this.selectedPump = 3
      }

      const confirmed = await Swal.fire({
        text: `선남가압장 ${this.selectedPump}번 펌프를 중지하시겠습니까?`,
        animation: false,
        showCancelButton: true,
        confirmButtonText: '적용',
        cancelButtonText: '취소'
      });

      if (confirmed.isConfirmed) {
        await fetchFunc(`${this.$apiURL}/dr/pumpManualOperation/3/stop`)
          .then((response) => {
            if (!response.ok) {  // 상태 코드가 200-299 범위가 아닌 경우

              throw new Error(response.message || '명령 전송 실패');
            }

            // 명령 성공 처리
            Swal.fire({
              animation: false,
              text: "명령을 전송했습니다.",
            });
            this.fetchData();
          })
          .catch((error) => {

            Swal.fire({
              text: error.message || '마지막 제어 후 5분이 지나지 않았습니다.',
              animation: false,
              showCancelButton: false,
              confirmButtonText: '확인'
            });
          });
        fetchFunc(`${this.$apiURL}/ai/pumpStop?pump=${this.selectedPump}`)
          .then(() => {
            Swal.fire({
              animation: false,
              text: "펌프 제어 명령을 전송했습니다.",
            });

            setTimeout(() => {
              location.reload();
            }, 30000);
          })
          .catch(() => {

          });
      }
    }
    ,
    async pumpStart() {
      const today = new Date();
      const day = today.getDate();
      if (day % 2 === 0) {
        this.selectedPump = 2
      } else {
        this.selectedPump = 3
      }
      const confirmed = await Swal.fire({
        text: `선남가압장 ${this.selectedPump}번 펌프를 가동하시겠습니까?`,
        animation: false,
        showCancelButton: true,
        confirmButtonText: '적용',
        cancelButtonText: '취소'
      });
      if (confirmed.isConfirmed) {
        await fetchFunc(`${this.$apiURL}/dr/pumpManualOperation/3/up`)
          .then((response) => {
            if (!response.ok) {  // 상태 코드가 200-299 범위가 아닌 경우

              throw new Error(response.message || '명령 전송 실패');
            }

            // 명령 성공 처리
            Swal.fire({
              animation: false,
              text: "명령을 전송했습니다.",
            });
            this.fetchData();
          })
          .catch((error) => {

            Swal.fire({
              text: error.message || '마지막 제어 후 5분이 지나지 않았습니다.',
              animation: false,
              showCancelButton: false,
              confirmButtonText: '확인'
            });
          });
        fetchFunc(`${this.$apiURL}/ai/pumpStart?pump=${this.selectedPump}`)
          .then(() => {
            Swal.fire({
              animation: false,
              text: "펌프 제어 명령을 전송했습니다.",
            });
            setTimeout(() => {
              location.reload();
            }, 30000);
          })
          .catch(() => {
   
          });
      }
    },
    async manualOper(oper, grp = -1) {
   
      let pump_grp = (grp === -1) ? this.tabIndex + 1 : grp;

      let operText;
      if (oper == 'up') {
        operText = '증가'
      } else {
        operText = '감소'
      }
      const confirmed = await Swal.fire({
        text: `펌프 조합을 ${operText} 하시겠습니까?`,
        animation: false,
        showCancelButton: true,
        confirmButtonText: '적용',
        cancelButtonText: '취소'
      });

      if (confirmed.isConfirmed) {
        await fetchFunc(`${this.$apiURL}/dr/pumpManualOperation/${pump_grp}/${oper}`)
          .then((response) => {
            if (!response.ok) {  // 상태 코드가 200-299 범위가 아닌 경우
    
              throw new Error(response.message || '명령 전송 실패');
            }

            // 명령 성공 처리
            Swal.fire({
              animation: false,
              text: "명령을 전송했습니다.",
            });
            this.fetchData();
          })
          .catch((error) => {
   
            Swal.fire({
              text: error.message || '마지막 제어 후 5분이 지나지 않았습니다.',
              animation: false,
              showCancelButton: false,
              confirmButtonText: '확인'
            });
          });
      }
    }
  }
}
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.date_design {
  background-color: #15284e;
  color: #fff;
  width: 130px;
  height: 28px;
  font-size: 13px;
  margin-left: 10px;
  font-family: KHNPHDRegular;
  border-radius: 5px;
}

.pump_box {
  height: 390px;
  padding: 15px 20px;
  width: 325px;
}

.chartbox {
  height: 100%;
  width: 100%;
  padding: 10px 30px;
  background-position: center;
  align-content: center;
  justify-items: center;
  display: block;

}

.div_chart {
  background: url(@/assets/img/chart_line.png) no-repeat;
  background-size: 100% 100%;
  width: 182px;
  height: 182px;
  justify-content: center;
  align-items: center;
  display: flex;
  mix-blend-mode: color-dodge;

}

.chartbase {
  background: url(@/assets/img/chart_based.png) no-repeat;
  background-size: 100% 100%;
  width: 100px;
  height: 100px;
  display: flex;
}

.chart_value {
  position: relative;
  height: 100%;
  font-size: 38px;
  text-align: center;
  text-indent: 5px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pump_name {
  background: url(@/assets/img/pump/text_input_bg.png) no-repeat;
  background-size: 100% 100%;
  width: 100%;
  height: 13%;
  text-align: center;
  align-items: center;
  justify-content: center;
  display: flex;
  mix-blend-mode: color-dodge;
  text-shadow: 0 0 9px #5cafff;
  text-align: center;
  color: #c3eaff;
  margin-bottom: 20px;
  position: unset;
}

.pump_value {
  text-align: center;
  margin-bottom: 5px;
}

.table_image {
  height: 62px;
  background-image: url(@/assets/img/div_new.png);
  background-size: 100% 100%;
  text-align: center;
  margin-bottom: 4px;
  align-items: center;
}

.top-contents-box {
  display: flex;
  align-content: flex-end;
  justify-content: center;
  flex-wrap: wrap;
  padding: 10px 10px 24px 10px;
}

.waterflow1 {
  background-image: url(@/assets/img/water.png);
  position: absolute;
  width: 18px;
  height: 18px;
  transform: scale(1.3);
}

.waterflow1.flow01,
.waterflow2.flow01,
.waterflow3.flow01 {
  top: 0;
  left: 984px;
  offset-path: path("M0.0 0 H 104");
  animation: waterflow-627c81ba 1.4S linear 0s infinite normal backwards;
}

.waterflow1.ms3.no1 {
  animation-delay: 0s;
}

@keyframes waterflow {
  0% {
    offset-distance: 0;
    display: none;
    opacity: 0;
  }

  1% {
    opacity: 1;
  }

  100% {
    offset-distance: 100%;
  }
}

.blue_round {
  width: 105px;
  height: 100px;
  color: #fff;
  text-shadow: 0 0 9px #5cafff;
  font-family: "KHNPHDRegular";
  background: url(@/assets/img/00_top_roundline_b.png) no-repeat;
  background-size: 100%;
  background-position: center;
  display: flex;
  font-size: 16px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.text_title_base {
  /*
	width: 65%;
	height: 78%;
	display: flex;
	flex-direction: column;
    */
  background: url(@/assets/img/peakcontrol/texttitle_based.png) no-repeat;
  background-size: 100% 100%;
  text-align: center;
}

.content__text-box {
  width: 100%;
  background-size: 100% 20px;
  background-position-y: bottom;
  text-shadow: 0 0 9px #5cafff;
  font-family: KHNPHUotfR;
  font-size: 16px;
  line-height: 1.5;
  text-align: left;
  color: #fff;
}

.box-bg {
  background: url(@/assets/img/dash_top.png) no-repeat !important;
  background-size: 100% 100% !important;
  width: 270px;
  height: 100px;
  padding: 0px 25px;
  justify-content: unset;
}

.cal_tite_text {
  text-shadow: 0 0 9px #5cafff;
  font-size: 16px;
  font-family: KHNPHDRegular;
  letter-spacing: normal;
  color: #c3eaff;
  /* line-height: 63px; */
  font-weight: bold;
}

.level_tite_text {
  text-shadow: 0 0 9px #5cafff;
  font-size: 18px;
  font-family: KHNPHDRegular;
  letter-spacing: normal;
  color: #c3eaff;
  /* line-height: 63px; */
  font-weight: bold;
}
.pipe_last_arrow {
  background: url(@/assets/img/analysis/pipeline_arrow.png) no-repeat;
  width: 100%;
  height: 100%;
  mix-blend-mode: color-dodge;
  position: relative;
  left: 40px;
}

.blinking {
  animation: blink 3s linear infinite;
}

.bottom_line_bg {
  background: url(@/assets/img/titleBar.png) no-repeat;
  background-size: 100% 2%;
  background-position: 0% 100%;
}

.area_title {
  background: linear-gradient(90deg, rgba(20, 65, 136, 0) 0%, rgba(20, 65, 136, 1) 20%, rgba(20, 65, 136, 1) 80%, rgba(20, 65, 136, 0) 100%);
}

.btn {
  background: #354573;
  border: 1px solid #9dc3e6;
  border-radius: 0 !important;
}

.btn.active,
.btn:hover {
  background: #627096;
  box-shadow: 0 0 5px #627096;
  border: 1px solid #9dc3e6;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  box-sizing: border-box;
  border-top-color: white;
  border-radius: 100%;

  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

.loading-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 90%;
  background-color: rgba(180, 180, 180, 0.1);
  /* 반투명한 배경 */
  z-index: 9999;
  /* 다른 요소 위에 표시하기 위한 z-index 설정 */
  display: flex;
  justify-content: center;
  /* 수평 가운데 정렬 */
  align-items: center;
}

@keyframes blink {

  0%,
  100% {
    color: red;
  }

  50% {
    color: white;
  }
}

.blinking-text {
  animation: blink 3s infinite;
}
</style>
