<template>
  <!--송수펌프 가동이력 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <b-row>
        <b-col class="title_wrap">
          <BigTitle :title="'운전현황 분석'" />
        </b-col>
        <b-col xl="7">
        </b-col>
        <b-col xl="3" class="d-flex align-items-center justify-content-end">
          <AiMode ref="AiMode" @getAiStatus="getAiStatus" :index="1" />
        </b-col>

      </b-row>
      <!-- 타이틀 끝 -->

      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container ">
        <b-row cols="12" class="mt-4">
          <!-- 시간 선택 영역: 왼쪽에서 3칸 차지 -->
          <b-col xl="6" class="">
            <SmallTitle :title="'최적운전 모드 운영 중'" />
          </b-col>
          <!-- <b-col xl class="flex-grow-1" /> -->
          <b-col xl="3" class="d-flex align-items-center" style="padding-bottom: 20px;"> <!-- flexbox로 유연한 배치 -->
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
          <!-- 예측조회/분석이력 버튼: 오른쪽에서 두 번째 -->
          <b-col xl="auto" style="padding-bottom: 20px;" class="d-flex align-items-center">
            <button type="button" class="btn btn-sm" @click="getExcel('pre')">
              예측 조회 <span v-if="preExcelLoading" class="spinner"></span>
            </button>
            <button type="button" class="btn btn-sm ms-2" @click="getExcel('anly')">
              분석이력 다운로드 <span v-if="anlyExcelLoading" class="spinner"></span>
            </button>
          </b-col>

          <!-- EPA 모드: 오른쪽 끝 -->
          <b-col cols="auto" style="padding-bottom: 20px;">
            <EpaMode ref="EpaMode" @change="changeEpaMode" :epa="epaMode" />
          </b-col>
          <!-- <b-col xl="1" class="d-flex flex-column justify-content-center align-items-center" style="position: relative; top: -10px;">
            <button type="button" class="btn btn-sm" @click="manualOper('up')">증가</button>
            <button type="button" class="btn btn-sm mt-1" @click="manualOper('down')">감소</button>
          </b-col> -->
        </b-row>
        <b-row class="mb-1">
          <b-col xl="4">
            <SmallTitle :title="'운영 현황'" :date="curDate"
              :style="{ textAign: 'center', marginBottom: '20px', marginTop: '0px' }" />
            <div class="d-flex flex-row justify-content-between" :style="{ marginTop: '0px' }">
              <div class="text_title_base" :style="{ width: '160px' }">
                <div class="w-100 d-flex flex_center_between" :style="{ height: '40px' }">
                  <div class="content__text-box text-center">구송수펌프</div>
                </div>
                <div class="w-100 d-flex flex_center_between" :style="{ height: '50px' }">
                  <div class="animationTItle-two" :style="{ height: '30px', color: '#5cebfe' }">
                    {{ oldCurPumpUse?.toString().replace("\"", "").replace(/,/g, ", ") }}
                  </div>
                </div>
              </div>
              <!-- TODO: 신송수 추가시 주석 해제 -->
              <div class="text_title_base" :style="{ width: '115px' }">
                <div class="w-100 d-flex flex_center_between" :style="{ height: '40px' }">
                  <div class="content__text-box text-center">신송수펌프</div>
                </div>
                <div class="w-100 d-flex flex_center_between" :style="{ height: '50px' }">
                  <div class="animationTItle-two" :style="{ height: '30px', color: '#5cebfe' }">
                    {{ newCurPumpUse?.toString().replace("\"", "").replace(/,/g, ", ") }}
                  </div>
                </div>
              </div>
              <div class="plate_img"
                :style="{ width: '295px', height: '100px', backgroundSize: 'contain !important', backgroundPosition: '0 55%' }">
                <div class="d-flex d-flex justify-content-evenly align-items-center">
                  <span class="cal_tite_text">전력</span>
                  <span class="detail_value"
                    :style="{ width: 'auto', fontSize: '46px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">{{
                      curPwr
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
                  <div class="btn-group" style="position: absolute; top: -2px; right: 40px;z-index: 1000;">
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
              <div class="text_title_base" :style="{ width: '160px' }">
                <div class="w-100 d-flex flex_center_between" :style="{ height: '40px' }">
                  <div class="content__text-box text-center">구송수펌프</div>
                </div>
                <div class="w-100 d-flex flex_center_between" :style="{ height: '50px' }">
                  <div class="animationTItle-two" :style="{ height: '30px', color: '#5cebfe' }">
                    {{ oldPrePumpUse?.toString().replace("\"", "").replace(/,/g, ", ") }}
                  </div>
                </div>


              </div>
              <div class="text_title_base" :style="{ width: '115px' }">
                <div class="w-100 d-flex flex_center_between" :style="{ height: '40px' }">
                  <div class="content__text-box text-center">신송수펌프</div>
                </div>
                <div class="w-100 d-flex flex_center_between" :style="{ height: '50px' }">
                  <div class="animationTItle-two" :style="{ height: '30px', color: '#5cebfe' }">
                    {{ newPrePumpUse?.toString().replace("\"", "").replace(/,/g, ", ") }}
                  </div>
                </div>
              </div>

              <!-- </template> -->
              <div class="plate_img"
                :style="{ width: '295px', height: '100px', backgroundSize: 'contain !important', backgroundPosition: '0 55%' }">
                <div class="d-flex d-flex justify-content-evenly align-items-center">
                  <span class="cal_tite_text">전력</span>
                  <span class="detail_value"
                    :style="{ width: 'auto', fontSize: '46px', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">{{
                      prePwr }}</span>
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
                  <span class="content__text-box text-center">{{ oldLoad }}</span>
                  <span class="content__text-box text-center" style="margin-left: 10px; color: #5cebfe">{{ oldOprtn
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
                <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForIntCur }"
                  @click="handleClick('cur', 'int')">통합송수펌프</button>
                <!-- <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForOldCur }"
                  @click="handleClick('cur', 'old')">구송수펌프</button>
                <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForNewCur }"
                  @click="handleClick('cur', 'new')">신송수펌프</button> -->
              </div>
              <div class="w-100" :style="{ height: '85%', background: 'transparent', boxShadow: '0 0 0 0.1px white' }">
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
                :style="{ overflowY: isLevelActive == false ? 'scroll' : 'visible', height: '350px' }">
                <PumpDrvnAnlyBotMid ref="PumpDrvnAnlyBotMid" v-for="(item, i) in title" :key="i" :title=item
                  :cur="botMidCur[i]" :pre="botMidPre[i]" :rate="rate[i]" />
              </div>
            </div>
          </b-col>
          <b-col xl="4" class="">
            <div class="bottom_line_bg" :style="{ height: '440px' }">
              <div class="btn-group mb-3">
                <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForIntPre }"
                  @click="handleClick('pre', 'int')">통합송수펌프</button>
                <!-- <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForOldPre }"
                  @click="handleClick('pre', 'old')">구송수펌프</button>
                <button type="button" class="btn btn-sm" :class="{ 'active': isActiveForNewPre }"
                  @click="handleClick('pre', 'new')">신송수펌프</button> -->
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
import ScatterChartClassForOld from '@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/ScatterChartClass'
import ScatterChartClassForNew from '@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/ScatterChartClass'
import { fetchFunc } from '@/util/fetchFunc';
import PumpDrvnAnlyBotMid from '@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/PumpDrvnAnlyBotMid.vue'
import { setPresData, setFlowData, setLevelData, ExcelDown } from '@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/PumpDrvnAnlyFunction'
import PlotlyLineChart from '@/components/Chart/PlotlyLineChart.vue'
import AiMode from '@/views/Common/AiMode.vue';
import { useStore } from "vuex";
import AreaChart from '@/components/Chart/AreaChart.vue';
import ChartClass from '@/components/Chart/LineBarChartClass';
import Swal from 'sweetalert2'
import EpaMode from '@/views/Common/EpaMode.vue';
export default {
  components: {
    BigTitle,
    SmallTitle,
    ScatterChart,
    LoadingSpinner,
    PumpDrvnAnlyBotMid,
    PlotlyLineChart,
    AiMode,
    AreaChart,
    EpaMode
  },
  data() {
    return {
      store: useStore(),
      tabIndex: -1,
      isLoading: false,
      preExcelLoading: false,
      anlyExcelLoading: false,
      selectedCycle: 'm',
      isPresActive: false,
      isFlowActive: true,
      isLevelActive: false,
      isActiveForOldCur: false,
      isActiveForNewCur: false,
      isActiveForIntCur: false,
      isActiveForOldPre: false,
      isActiveForNewPre: false,
      isActiveForIntPre: false,
      isActiveFirTime: true,
      isActiveSecTime: false,
      isActiveThrTime: false,
      isActiveFouTime: false,
      isActiveFifTime: false,
      title: ["고산<br/>정수장", "(구)<br/>정수장", "(신)<br/>정수장", "신지<br/>분기", "전주<br/>분기", "봉동<br/>분기", "용진<br/>분기", "용봉<br/>분기"],
      levelTitle: ["(구)<br/>정수장", "(신)<br/>정수장", "천마<br/>배수지", "인후<br/>배수지", "효자<br/>배수지"],
      presTag: ["all", "701-367-PRI-4010", "701-367-PRI-4019", "701-367-PRI-8002", "701-367-PRI-8005", "701-367-PRI-8006", "701-367-PRI-8004", "701-367-PRI-8661"],
      flowTag: ["all", "701-367-FRI-4001", "701-367-FRI-4004", "701-367-FRI-8003", "701-367-FRI-8007", "701-367-FRI-8008", "701-367-FRI-8005", "701-367-FRI-8661"],
      levelTag: ["701-367-LEI-4011", "701-367-LEI-4008", "701-367-LEI-8001", "701-367-LEI-8006", "701-367-LEI-8009"],
      presThres: [],
      curDate: '',
      preDate: '',
      oldCurPumpOrder: [],
      oldPrePumpOrder: [],
      newCurPumpOrder: [],
      newPrePumpOrder: [],
      intCurPumpOrder: [],
      intPrePumpOrder: [],
      oldCurPumpUse: [],
      oldPrePumpUse: [],
      newCurPumpUse: [],
      newPrePumpUse: [],
      intCurPumpUse: [],
      intPrePumpUse: [],
      curPwr: 0,
      prePwr: 0,
      oldCurPwr: 0,
      oldPrePwr: 0,
      newCurPwr: 0,
      newPrePwr: 0,
      intPrePwr: 0,
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
      unit: 'm³/hr',
      isInt: true,
      pwrCurUnit: '',
      pwrPreUnit: '',
      oldLoad: '',
      oldOprtn: '',
      isActiveForDayAgo: true,
      isActiveForWeekAgo: false,
      isActiveForMonthAgo: false,
      curChartLabels: ["운영", "전일", "펌프 대수"],
      time: '',
      wonLoading: false,
      epaMode : 0
    }
  },
  created() {
    this.getEpaMode()
    console.log('created 호출됨 epa모드: '+this.epaMode);
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
    // setInterval(() => {
    //   this.fetchData();
    // }, (1 * (1000 * 1)));
  },
  methods: {
    async getEpaMode() {
      const response = await fetchFunc(`${this.$apiURL}/epa/getEpaModeInfo`);
      this.epaMode = response.data;
      console.log("🚀 ~ this.epaMode:", this.epaMode)
    },
    async fetchChartData(params) {
      return await fetchFunc(`${this.$apiURL}/dr/systemResistanceCurves`, params);
    },
    async fetchData() {
      this.getAiStatus()
      this.time = await this.getDateParams()
      const ploty_xDate = []
      const ploty_flowData = []
      const ploty_presData = []
      const value = await Promise.allSettled([
        this.fetchChartData(this.createParams(this.time, 'cur', 1, ["A4", "A1", "A7"], this.cycle, this.range)),
        this.fetchChartData(this.createParams(this.time, 'cur', 2, ["A4", "A1", "A7"], this.cycle, this.range)),
        this.fetchChartData(this.createParams(this.time, 'pre', 1, ["A4", "A1", "A7"], this.cycle, this.range)),
        this.fetchChartData(this.createParams(this.time, 'pre', 2, ["A4", "A1", "A7"], this.cycle, this.range)),
        this.fetchChartData(this.createParams(this.time, 'cur', 0, ["A4", "A1", "A7"], this.cycle, this.range)),
        this.fetchChartData(this.createParams(this.time, 'pre', 0, ["A4", "A1", "A7"], this.cycle, this.range)),
        fetchFunc(`${this.$apiURL}/dr/getPumpUse?startDate=${this.time}&cycle=${this.cycle}&range=${this.range}`),
        fetchFunc(`${this.$apiURL}/dr/predictionPumpCombination?startDate=${this.time}&cycle=${this.cycle}&range=${this.range}&pump_grp=0`),
        fetchFunc(`${this.$apiURL}/dr/selectIntradotion?startDate=${this.time}&opt_idx=cur`),
        fetchFunc(`${this.$apiURL}/dr/selectIntradotion?startDate=${this.time}&opt_idx=pre`),
        fetchFunc(`${this.$apiURL}/dr/selectPumpCombCal`),
      ]);

      this.oldCurData = value[0].status === 'fulfilled' ? value[0].value : null;
      this.newCurData = value[1].status === 'fulfilled' ? value[1].value : null;
      this.oldPreData = value[2].status === 'fulfilled' ? value[2].value : null;
      this.newPreData = value[3].status === 'fulfilled' ? value[3].value : null;
      this.intCurData = value[4].status === 'fulfilled' ? value[4].value : null;
      this.intPreData = value[5].status === 'fulfilled' ? value[5].value : null;
      this.historyData = value[6].status === 'fulfilled' ? value[6].value.data : null;
      this.preHistoryData = value[7].status === 'fulfilled' ? value[7].value.data : null;
      const botMidCurData = value[8].status === 'fulfilled' ? value[8].value : null;
      const botMidPreData = value[9].status === 'fulfilled' ? value[9].value : null;
      this.pumpCombCal = value[10].status === 'fulfilled' ? value[10].value : null;
      this.intCombCal = this.pumpCombCal.data.filter(item => item.PUMP_GRP == 0)
      this.oldCombCal = this.pumpCombCal.data.filter(item => item.PUMP_GRP == 1)
      this.newCombCal = this.pumpCombCal.data.filter(item => item.PUMP_GRP == 2)
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
      this.changeTab('cur', 'int')
      this.changeTab('pre', 'int')
      // this.oldPreData?.data.forEach(element => {
      //   ploty_xDate.push(element.date)
      //   ploty_flowData.push((element.flow).toFixed(0))
      //   ploty_presData.push((element.pressure).toFixed(2))
      // })
      this.intPreData?.data.forEach(element => {
        ploty_xDate.push(element.date)
        ploty_flowData.push((element.flow).toFixed(0))
        ploty_presData.push((element.pressure).toFixed(2))
      })
      this.createLineBarChart('day')
      this.createChart(this.intCurData, 'cur', 'int')
      this.createChart(this.intPreData, 'pre', 'int')
      this.$refs.PlotlyLineChart.makeChart(ploty_xDate, Object.keys(this.historyData), Object.values(this.historyData), this.selectedCycle, '', ploty_flowData, ploty_presData, Object.values(this.preHistoryData))
    },
    //상단 데이터 설정 메소드 
    setTopData() {
      if (this.oldCurData?.data) {
        this.oldCurPwr = this.oldCurData?.data[this.oldCurData?.data?.length - 1]?.pwr
        this.oldCurPumpUse = this.oldCurData?.data[this.oldCurData?.data?.length - 1]?.pumpUse
        this.oldPrePwr = this.oldPreData?.data[this.oldPreData?.data?.length - 1]?.pwr
        this.oldPrePumpUse = this.oldPreData?.data[this.oldPreData?.data?.length - 1]?.pumpUse
        this.oldLoad = this.oldPreData?.data[this.oldPreData?.data?.length - 1]?.load
        this.oldOprtn = this.oldPreData?.data[this.oldPreData?.data?.length - 1]?.oprtn
        if (this.oldLoad === 'L') this.oldLoad = '경부하'
        if (this.oldLoad === 'M') this.oldLoad = '중부하'
        if (this.oldLoad === 'H') this.oldLoad = '최대부하'

        if (this.oldOprtn === 'none') this.oldOprtn = ''
        if (this.oldOprtn === 'high') this.oldOprtn = '펌프 추가운영'
        if (this.oldOprtn === 'low') this.oldOprtn = '펌프 절감운영'
        this.newCurPwr = this.newCurData?.data[this.newCurData?.data?.length - 1].pwr
        this.newCurPumpUse = this.newCurData?.data[this.newCurData?.data?.length - 1].pumpUse
        this.newPrePwr = this.newPreData?.data[this.newPreData?.data?.length - 1].pwr
        this.newPrePumpUse = this.newPreData?.data[this.newPreData?.data?.length - 1].pumpUse
        this.intCurPwr = this.intCurData?.data[this.intCurData?.data?.length - 1].pwr
        this.intCurPumpUse = this.intCurData?.data[this.intCurData?.data?.length - 1].pumpUse
        this.intPrePwr = this.intPreData?.data[this.intPreData?.data?.length - 1].pwr
        this.intPrePumpUse = this.intPreData?.data[this.intPreData?.data?.length - 1].pumpUse

        this.curDate = this.intCurData?.data[this.intCurData?.data?.length - 1].date
        this.preDate = this.intPreData?.data[this.intPreData?.data?.length - 1].date

        this.curPwr = (this.oldCurPwr + this.newCurPwr).toFixed(0)
        this.prePwr = (this.oldPrePwr + this.newPrePwr).toFixed(0)
        this.oldCurPumpOrder = []
        this.newCurPumpOrder = []
        this.intCurPumpOrder = []
        this.oldPrePumpOrder = []
        this.newPrePumpOrder = []
        this.intPrePumpOrder = []

        this.oldCurPumpUse?.forEach(item => {
          // let parts = item.split("#");
          this.oldCurPumpOrder.push(item.toString());
          this.intCurPumpOrder.push(item.toString());
        })
        this.newCurPumpUse?.forEach(item => {
          // let parts = item.split("#");
          this.newCurPumpOrder.push(item.toString());
          this.intCurPumpOrder.push(item.toString());
        })
        // this.intCurPumpUse?.forEach(item => {
        //   let parts = item.split("#");
        //   this.intCurPumpOrder.push(parts[1].toString());
        // })

        this.oldPrePumpUse?.forEach(item => {
          // let parts = item.split("#");
          this.oldPrePumpOrder.push(item.toString());
          this.intPrePumpOrder.push(item.toString());
        })
        this.newPrePumpUse?.forEach(item => {
          // let parts = item.split("#");
          this.newPrePumpOrder.push(item.toString());
          this.intPrePumpOrder.push(item.toString());
        })
       
        // this.intPrePumpUse?.forEach(item => {
        //   let parts = item.split("#");
        //   this.intPrePumpOrder.push(parts[1].toString());
        // })
        this.saving = ((this.curPwr - this.prePwr) / this.curPwr * 100).toFixed(1)
      }
    },
    clickPres() {
      this.unit = 'kgf/c㎡'
      this.title = ["고산<br/>정수장", "(구)<br/>정수장", "(신)<br/>정수장", "신지<br/>분기", "전주<br/>분기", "봉동<br/>분기", "용진<br/>분기", "용봉<br/>분기"]
      this.$nextTick(() => {
        setPresData.call(this);
      });
      this.isPresActive = true;
      this.isFlowActive = false;
      this.isLevelActive = false;
    },
    clickFlow() {
      this.unit = 'm³/hr'
      this.title = ["고산<br/>정수장", "(구)<br/>정수장", "(신)<br/>정수장", "신지<br/>분기", "전주<br/>분기", "봉동<br/>분기", "용진<br/>분기", "용봉<br/>분기"]
      this.$nextTick(() => {
        setFlowData.call(this);
      });
      this.isPresActive = false;
      this.isFlowActive = true;
      this.isLevelActive = false;
    },
    clickLevel() {
      this.unit = 'm'
      this.title = ["(구)<br/>정수장", "(신)<br/>정수장", "천마<br/>배수지", "인후<br/>배수지", "효자<br/>배수지"]
      this.$nextTick(() => {
        setLevelData.call(this);
      });
      this.isPresActive = false;
      this.isFlowActive = false;
      this.isLevelActive = true;
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
      this.changeTab('cur', 'old')
      this.changeTab('pre', 'old')
      this.clickTime(this.firTime)
    },
    async handleClick(curType, dataType) {
      this.time = await this.getDateParams()
      const isActiveForOld = dataType === 'old';
      const isActiveForNew = dataType === 'new';
      const isActiveForInt = dataType === 'int';
      let data;

      if (curType === 'cur') {
        this.isActiveForOldCur = isActiveForOld;
        this.isActiveForNewCur = isActiveForNew;
        this.isActiveForIntCur = isActiveForInt;
        if (dataType === 'old') {
          data = await this.fetchChartData(this.createParams(this.time, curType, 1, ["A4", "A1", "A7"], this.cycle, this.range));
        } else if (dataType === 'new') {
          data = await this.fetchChartData(this.createParams(this.time, curType, 2, ["A4", "A1", "A7"], this.cycle, this.range));
        } else if (dataType === 'int') {
          data = await this.fetchChartData(this.createParams(this.time, curType, 0, ["A4", "A1", "A7"], this.cycle, this.range));
        }
      } else if (curType === 'pre') {
        this.isActiveForOldPre = isActiveForOld;
        this.isActiveForNewPre = isActiveForNew;
        this.isActiveForIntPre = isActiveForInt;
        if (dataType === 'old') {
          data = await this.fetchChartData(this.createParams(this.time, curType, 1, ["A4", "A1", "A7"], this.cycle, this.range));
        } else if (dataType === 'new') {
          data = await this.fetchChartData(this.createParams(this.time, curType, 2, ["A4", "A1", "A7"], this.cycle, this.range));
        } else if (dataType === 'int') {
          data = await this.fetchChartData(this.createParams(this.time, curType, 0, ["A4", "A1", "A7"], this.cycle, this.range));
        }
      }
      this.changeTab(curType, dataType)
      this.createChart(data, curType, dataType);
    },
    changeTab(curType, dataType) {
      const isActiveForOld = dataType === 'old';
      const isActiveForNew = dataType === 'new';
      const isActiveForInt = dataType === 'int';
      if (curType === 'cur') {
        this.isActiveForOldCur = isActiveForOld;
        this.isActiveForNewCur = isActiveForNew;
        this.isActiveForIntCur = isActiveForInt;
      } else if (curType === 'pre') {
        this.isInt = isActiveForInt
        this.isActiveForOldPre = isActiveForOld;
        this.isActiveForNewPre = isActiveForNew;
        this.isActiveForIntPre = isActiveForInt;
      }
    },
    createChart(data, flag, tab) {
      let ChartClass
      // isA1, isA4, isA7 표시여부 없으면 true
      if (tab == 'old') {
        if (flag == 'cur') {
          ChartClass = new ScatterChartClassForOld(data, this.oldCurPumpOrder.toString(), this.oldCombCal, true, true, true, 3)
          this.$refs.ScatterChart1.changeData(ChartClass)
        }
        else if (flag == 'pre') {
          ChartClass = new ScatterChartClassForOld(data, this.oldPrePumpOrder.toString(), this.oldCombCal, true, true, true, 3)
          this.$refs.ScatterChart2.changeData(ChartClass)
        }
      }
      else if (tab == 'new') {
        if (flag == 'cur') {
          ChartClass = new ScatterChartClassForNew(data, this.newCurPumpOrder.toString(), this.newCombCal, true, true, true, 2)
          this.$refs.ScatterChart1.changeData(ChartClass)
        }
        else if (flag == 'pre') {
          ChartClass = new ScatterChartClassForNew(data, this.newPrePumpOrder.toString(), this.newCombCal, true, true, true, 2)
          this.$refs.ScatterChart2.changeData(ChartClass)
        }
      }
      else if (tab == 'int') {
        if (flag == 'cur') {
          ChartClass = new ScatterChartClassForNew(data, this.intCurPumpOrder.toString(), this.intCombCal,  true, true, true, 2)
          this.$refs.ScatterChart1.changeData(ChartClass)
        }
        else if (flag == 'pre') {
          ChartClass = new ScatterChartClassForNew(data, this.intPrePumpOrder.toString(), this.intCombCal,  true, true, true, 2)
          this.$refs.ScatterChart2.changeData(ChartClass)
        }
      }
      this.isLoading = false
    },
    async createLineBarChart(time) {
      this.wonLoading = true
      this.time = await this.getDateParams()
      let curData = (await fetchFunc(`${this.$apiURL}/dr/pumpPwrSrcUnitData?opt_idx=cur&nowDate=${this.time}&time=${time}&pump_grp=0`)).data;
      let preData = (await fetchFunc(`${this.$apiURL}/dr/pumpPwrSrcUnitData?opt_idx=pre&nowDate=${this.time}&time=${time}&pump_grp=0`)).data;
      if (!isNaN(curData?.nowPwrCost)) this.pwrCurUnit = curData?.nowPwrCost?.toFixed(3)
      if (!isNaN(preData?.nowPwrCost)) this.pwrPreUnit = preData?.nowPwrCost?.toFixed(3)
      while (preData?.plusPwrCostLust.length < preData.dateTime[0].length) {
        preData?.plusPwrCostLust.push(preData?.plusPwrCostLust[preData?.plusPwrCostLust.length - 1])
      }

      let dataY = []
      let preDataY = []
      // const formattedDates = ts.map(dateString => {
      //   const date = new Date(dateString);
      //   return `${date.getDate()}일 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
      // });
      let formattedDates = curData.dateTime[0].map(dateTime => {
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
      // let time = "2024-11-12 13:27:00";
      return time
      // let currentDate = new Date('2024-05-15T15:00:00')
      // let targetDate
      // targetDate = new Date(currentDate.getTime() * 60 * 60 * 1000);
      // const hour = targetDate.getHours();
      // const minute = targetDate.getMinutes();
      // const year = targetDate.getFullYear();
      // const month = targetDate.getMonth() + 1; // January is 0
      // const day = targetDate.getDate();
      // const formattedHour = hour < 10 ? `0${hour}` : hour;
      // const formattedMinute = minute < 10 ? `0${minute}` : minute;
      // const formattedMonth = month < 10 ? `0${month}` : month;
      // const formattedDay = day < 10 ? `0${day}` : day;

      // return `${year}-${formattedMonth}-${formattedDay} ${formattedHour}:${formattedMinute}:00`;

    },
    getExcel(type) {
      ExcelDown.call(this, type)
    },
    async getAiStatus() {
      const dataAi = await fetchFunc(`${this.$apiURL}/ai/selectAiStatus`);
      let firPumpStatus = dataAi?.data[0]?.AI_STATUS

      this.$store.state.firAiFlag = parseInt(firPumpStatus)
      this.$refs.AiMode.changeAuto(this.$store.state.firAiFlag)
    },
    async manualOper(oper) {
   
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
        await fetchFunc(`${this.$apiURL}/dr/pumpManualOperation/1/${oper}`)
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
              text: error.message || '마지막 제어 후 30분이 지나지 않았습니다.',
              animation: false,
              showCancelButton: false,
              confirmButtonText: '확인'
            });
          });
      }
    },
    async changeEpaMode(mode){
      let operText;
      if(mode == 1){
        operText = '관망분석'
      } else {
        operText = '수요예측'
      }

      const confirmed = await Swal.fire({
        text: `펌프 조합을 ${operText}으로 생성하시겠습니까?`,
        animation: false,
        showCancelButton: true,
        confirmButtonText: '적용',
        cancelButtonText: '취소'
      });
      
      if(confirmed){
          try {
              // 수정된 fetchFunc 호출
              // 1. URL: 백엔드 API 경로와 PathVariable인 mode를 포함하여 생성
              // 2. data: PUT 요청이지만 본문(body)이 필요 없으므로 null 전달
              // 3. method: 'PUT'을 명시적으로 전달
              const response = await fetchFunc(`${this.$apiURL}/epa/setEpaMode/${mode}`, null, 'PUT');

              // API 호출 성공 여부 확인 (응답 구조에 따라 변경 필요)
              if (response.data === 'ok') { // 백엔드 응답이 ResponseObject 형태라고 가정
                  this.epaMode = mode;
                  Swal.fire(
                      '적용 완료',
                      `${operText} 모드로 성공적으로 변경되었습니다.`,
                      'success'
                  );
                  this.getEpaMode()
              } else {
                  // API가 에러 응답을 보냈을 때
                  Swal.fire(
                      '오류 발생',
                      '모드 변경에 실패했습니다: ' + (response.message || '알 수 없는 오류'),
                      'error'
                  );
              }
          } catch (error) {
              // 네트워크 오류 등 fetch 자체에서 에러가 발생했을 때
              console.error('Failed to change EPA mode:', error);
              Swal.fire(
                  '요청 실패',
                  '서버와 통신 중 오류가 발생했습니다.',
                  'error'
              );
          }
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
</style>
