<template>
  <LoadingSpinner class="loading-container" v-if="isLoading"></LoadingSpinner>
  <!--송수펌프 제어 분석 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <b-row>
        <b-col xl="2">
          <BigTitle :title="'송수펌프 제어 분석'" />
        </b-col>
        <b-col xl="7" class="d-flex align-items-center">
          <MenuTab @changeData="changeData" />
        </b-col>
        <b-col xl="3" class="d-flex align-items-center justify-content-end">
          <AiMode ref="AiMode" @changePumpControl="changePumpControl" :index="this.tabIndex + 1" />
        </b-col>
      </b-row>

      <!-- 타이틀 끝 -->
      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container mt-3">
        <b-row>
          <b-col xl="7">
            <b-row>
              <b-col xl="4">
                <SmallTitle :title="'운영현황'" />
                <!-- 펌프 시작 -->
                <PumpControlLeft ref="PumpControlLeft" :data="this.data1" :tabIndex="this.tabIndex"
                  @changePumpControl="changePumpControl" />
                <!-- 펌프 끝 -->
              </b-col>
              <b-col xl="8">
                <SmallTitle :title="'주요인자'" />
                <PumpControlMid :major="major" ref="PumpControlMid" />
              </b-col>
            </b-row>
          </b-col>

          <b-col xl="5">
            <b-row>
              <b-col xl="5">
                <b-row class="row-cols-1 h-100">
                  <b-col>
                    <!-- 배수지 요구 관압 -->
                    <div class="fL w-100">
                      <SmallTitle :title="'배수지 요구 관압'" />
                      <PumpControlRigTopLeftTop ref="PumpControlRigTopLeftTop" :data4="maxSpiData" />
                    </div>
                    <!-- //배수지 요구 관압 -->
                  </b-col>
                  <b-col>
                    <SmallTitle :title="'송수 펌프 제어'" />
                    <PumpControlRigTopLeftBot v-for="item, index in title" :key="item" :item="rigItem[index]"
                      :title="title[index]" :data="this.data1" :data4="this.data4" :presValue="this.presValue" />
                  </b-col>
                </b-row>
              </b-col>
              <b-col xl="1">
                <div class="d-flex justify-content-center align-items-center h-100">
                  <img class="blinking" :src="require(`@/assets/img/ai_arrow_right.png`)"
                    :style="{ width: '70px', height: '360px', background: 'url(src\assets\img\ai_arrow_right.png)', backgroundSize: '100% 100%', float: 'left', mixBlendMode: 'color-dodge' }" />
                </div>
              </b-col>
              <b-col xl="6">
                <!-- 분석 결과 -->
                <SmallTitle :title="'분석 결과'" />
                <b-row class="row-cols-1">
                  <b-col class="mb-2">
                    <PumpControlRig ref="PumpControlRig" :data1="this.$store.state.data1"
                      :data2="this.$store.state.data2" :data3="this.$store.state.data3" :data6="this.$store.state.data6"
                      :data7="this.$store.state.data7" :data10="this.$store.state.data10"
                      :data11="this.$store.state.data11" :data12="this.$store.state.data12"
                      :data13="this.$store.state.data13" :data15="this.$store.state.data15"
                      :data16="this.$store.state.data16" :tabIndex="tabIndex" @changePumpControl="changePumpControl" />
                  </b-col>
                </b-row>
                <!-- //분석 결과 -->
              </b-col>
            </b-row>
            <!-- <b-row>
              <b-col>
                <SmallTitle :title="'송수펌프 사용 예측 트렌드'" />
                <PumpControlRigBot ref="PumpControlRigBot" />
              </b-col>
            </b-row> -->
          </b-col>
        </b-row>
      </div>
      <!-- 본문 컨텐츠 끝 -->
    </b-container>
  </div>
</template>

<script>
import LoadingSpinner from '@/components/ComponentCommon/LoadingSpinner.vue';
import BigTitle from '@/components/ComponentCommon/BigTitle.vue';
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
import PumpControlLeft from '@/views/AiAnalysis/SongsuPumpCtr/PumpControlAnly/PumpControlLeft.vue'
import PumpControlMid from '@/views/AiAnalysis/SongsuPumpCtr/PumpControlAnly/PumpControlMid.vue'
import PumpControlRig from '@/views/AiAnalysis/SongsuPumpCtr/PumpControlAnly/PumpControlRig.vue'
import PumpControlRigTopLeftTop from './PumpControlAnly/PumpControlRigTopLeftTop.vue';
import PumpControlRigTopLeftBot from './PumpControlAnly/PumpControlRigTopLeftBot.vue';
// import PumpControlRigBot from './PumpControlAnly/PumpControlRigBot.vue';
import MenuTab from '@/views/Common/MenuTab.vue';
import AiMode from '@/views/Common/AiMode.vue'
import { fetchFunc } from '@/util/fetchFunc';
import { useStore } from "vuex";
export default {
  components: {
    BigTitle,
    SmallTitle,
    PumpControlLeft,
    PumpControlMid,
    PumpControlRig,
    PumpControlRigTopLeftBot,
    PumpControlRigTopLeftTop,
    // PumpControlRigBot,
    LoadingSpinner,
    MenuTab,
    AiMode
  },
  data() {
    return {
      isLoading: false,
      sujiList: [],
      data: {},
      data1: {},
      data2: {},
      data3: {},
      data4: {},
      presValue: [],
      maxSpiData: [],
      activeTab: 0,
      major: [],
      majorData: [],
      title: ['정수장 토출 관압', '펌프 가동 대수'],
      rigItem: [],
      tabIndex: 0,
      onOffStatus: [],
      store: useStore(),
    }
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
    this.initData()
    this.changePumpControl()
    setInterval(() => {
      this.changePumpControl();
    }, ((1000 * 600)));
  },
  updated() {
  },
  methods: {
    changeData(index) {
      this.tabIndex = index
      this.changePumpControl()
      this.major = []
      if (this.tabIndex === 0) {
        this.sortingData(this.data)
        this.maxSpiData.name = this.data[0]?.TNK_GRP_NM?.replace('배수지', '')
        this.maxSpiData.point = this.data[0]?.최소요구관압?.toFixed(2)
        this.maxSpiData.pres = this.data[0]?.최소요구관압?.toFixed(2)
        this.$refs.PumpControlRigTopLeftTop.settingValue(this.maxSpiData)
      }
      else if (this.tabIndex === 1) {
        this.sortingData(this.data5)
        this.maxSpiData.name = this.data5[0]?.TNK_GRP_NM?.replace('배수지', '')
        this.maxSpiData.point = this.data5[0]?.최소요구관압?.toFixed(2)
        this.maxSpiData.pres = this.data5[0]?.최소요구관압?.toFixed(2)
        this.$refs.PumpControlRigTopLeftTop.settingValue(this.maxSpiData)
      }
      else if (this.tabIndex === 2) {
        this.sortingData(this.data8)
        this.maxSpiData.name = this.data8[0]?.TNK_GRP_NM?.replace('배수지', '')
        this.maxSpiData.point = this.data8[0]?.최소요구관압?.toFixed(2)
        this.maxSpiData.pres = this.data8[0]?.최소요구관압?.toFixed(2)
        this.$refs.PumpControlRigTopLeftTop.settingValue(this.maxSpiData)
      }
      else if (this.tabIndex === 3) {
        this.sortingData(this.data9)
        this.maxSpiData.name = this.data9[0]?.TNK_GRP_NM?.replace('배수지', '')
        this.maxSpiData.point = this.data9[0]?.최소요구관압?.toFixed(2)
        this.maxSpiData.pres = this.data9[0]?.최소요구관압?.toFixed(2)
        this.$refs.PumpControlRigTopLeftTop.settingValue(this.maxSpiData)
      }
      else if (this.tabIndex === 4) {
        this.sortingData(this.data14)
        this.maxSpiData.name = this.data14[0]?.TNK_GRP_NM?.replace('배수지', '')
        this.maxSpiData.point = this.data14[0]?.최소요구관압?.toFixed(2)
        this.maxSpiData.pres = this.data14[0]?.최소요구관압?.toFixed(2)
        this.$refs.PumpControlRigTopLeftTop.settingValue(this.maxSpiData)
      }
    },
    async initData() {
      this.isLoading = true;
      const apiURL = this.$apiURL;
      const fetchUrls = [
        `${apiURL}/ai/selectValve?pump_grp=1`,
        `${apiURL}/ai/selectPumpStatus`,
        `${apiURL}/ai/pumpSelect?pump_grp=1`,
        `${apiURL}/ai/pumpSelect?pump_grp=2`,
        `${apiURL}/cm/selectWppTagCodeList?func_typ=PumpControl`,
        `${apiURL}/ai/selectValve?pump_grp=2`,
        `${apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=1`,
        `${apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=2`,
        `${apiURL}/ai/selectValve?pump_grp=3`,
        `${apiURL}/ai/selectValve?pump_grp=4`,
        `${apiURL}/ai/pumpSelect?pump_grp=3`,
        `${apiURL}/ai/pumpSelect?pump_grp=4`,
        `${apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=3`,
        `${apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=4`,
        `${apiURL}/ai/selectValve?pump_grp=5`,
        `${apiURL}/ai/pumpSelect?pump_grp=5`,
        `${apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=5`,
      ];

      // const sanseongFetchUrls = [
      //   `${apiURL}/ai/selectValve?pump_grp=1`,
      //   `${apiURL}/ai/selectPumpStatus`,
      //   `${apiURL}/ai/pumpSelect_new?pump_grp=1`,
      //   `${apiURL}/ai/pumpSelect_new?pump_grp=2`,
      //   `${apiURL}/cm/selectWppTagCodeList?func_typ=PumpControl`,
      //   `${apiURL}/ai/pumpSelectList_new?pump_grp=1`,
      //   `${apiURL}/ai/pumpSelectList_new?pump_grp=2`,
      //   `${apiURL}/ai/selectValve?pump_grp=2`,
      //   `${apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=1`,
      //   `${apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=2`,
      // ];

      const fetchPromises = (fetchUrls.map(async (url) => {
        const res = await fetch(url);
        const data = await res.json();
        return data.data;
      }));

      const results = await Promise.allSettled(fetchPromises);

      this.data = results[0].status === 'fulfilled' ? results[0].value : null;
      // this.data = { "code": 200, "message": "정상적으로 조회되었습니다.", "data": [{ "TNK_GRP_IDX": 3, "TNK_IDX": 2, "TNK_GRP_NM": "오식도배수지", "TNK_NM": "수위2", "IN_FO_TAG": "", "OUT_FO_TAG": "", "IN_FC_TAG": "", "OUT_FC_TAG": "", "IN_POI_TAG": "", "OUT_POI_TAG": "", "LEI_TAG": "891-365-LEI-8653", "수위": "4.1428", "IN_FLW_TAG": "891-365-FRI-8652", "유입유량": "2825.6250", "OUT_FLW_TAG": "891-365-FRI-8653", "유출유량": "3354.3750" }] }.data
      this.data1 = results[1].status === 'fulfilled' ? results[1].value : null;
      // this.data1 = { "code": 200, "message": "정상적으로 조회되었습니다.", "data": { "PRI": [{ "ts": "2024-07-08 17:22:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "생활정수지", "PUMP_NM": "생활(정)_1", "PRI_T_TAG": "780-344-PRI-4001", "value": "9.6781" }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 5, "PUMP_GRP": 2, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "공업정수지", "PUMP_NM": "공업(정)_1", "PRI_T_TAG": "780-344-PRI-6004", "value": "7.1938" }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 9, "PUMP_GRP": 3, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "선남가압장", "PUMP_NM": "선남(가)_1", "PRI_T_TAG": "780-379-PRI-1007", "value": "8.0306" }], "pwiStatus": [{ "ts": "2024-07-08 17:22:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "생활정수지", "PUMP_NM": "생활(정)_1", "kW": 182.06 }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 2, "PUMP_GRP": 1, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "생활정수지", "PUMP_NM": "생활(정)_2", "kW": 0.0 }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 3, "PUMP_GRP": 1, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "생활정수지", "PUMP_NM": "생활(정)_3", "kW": 183.7 }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "생활정수지", "PUMP_NM": "생활(정)_4", "kW": 0.0 }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 5, "PUMP_GRP": 2, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "공업정수지", "PUMP_NM": "공업(정)_1", "kW": 0.0 }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 6, "PUMP_GRP": 2, "PUMP_GRP_IDX": 6, "PUMP_GRP_NM": "공업정수지", "PUMP_NM": "공업(정)_2", "kW": 0.0 }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 7, "PUMP_GRP": 2, "PUMP_GRP_IDX": 7, "PUMP_GRP_NM": "공업정수지", "PUMP_NM": "공업(정)_3", "kW": 173.59 }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 8, "PUMP_GRP": 2, "PUMP_GRP_IDX": 8, "PUMP_GRP_NM": "공업정수지", "PUMP_NM": "공업(정)_4", "kW": 0.0 }], "FRI": [{ "ts": "2024-07-08 17:22:00", "PUMP_IDX": 5, "PUMP_GRP": 2, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "공업정수지", "PUMP_NM": "공업(정)_1", "FRI_TAG": "780-344-FIT-2501", "value": "571.0000" }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "생활정수지", "PUMP_NM": "생활(정)_1", "FRI_TAG": "780-344-FIT-2502", "value": "971.0000" }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 9, "PUMP_GRP": 3, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "선남가압장", "PUMP_NM": "선남(가)_1", "FRI_TAG": "780-344-FRI-5002", "value": "396.0000" }], "SPI": [{ "ts": "2024-07-08 17:22:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "생활정수지", "PUMP_NM": "생활(정)_4", "SPI_TAG": "780-344-SPI-4004", "value": "0.1241" }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 7, "PUMP_GRP": 2, "PUMP_GRP_IDX": 7, "PUMP_GRP_NM": "공업정수지", "PUMP_NM": "공업(정)_3", "SPI_TAG": "780-344-SWI-6000", "value": "51.5419" }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 9, "PUMP_GRP": 3, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "선남가압장", "PUMP_NM": "선남(가)_1", "SPI_TAG": "780-379-SWI-1001", "value": "0.0000" }, { "ts": "2024-07-08 17:22:00", "PUMP_IDX": 11, "PUMP_GRP": 3, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "선남가압장", "PUMP_NM": "선남(가)_3", "SPI_TAG": "780-379-SWI-1002", "value": "0.0000" }], "pumpStatus": [{ "PUMP_GRP": 1, "PUMP_NM": "생활(정)_1", "PUMP_TYP": 1, "runCount": 3, "value": "On", "PUMP_IDX": 1, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "생활정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "생활(정)_2", "PUMP_TYP": 1, "runCount": 3, "value": "Off", "PUMP_IDX": 2, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "생활정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "생활(정)_3", "PUMP_TYP": 1, "runCount": 3, "value": "On", "PUMP_IDX": 3, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "생활정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "생활(정)_4", "PUMP_TYP": 2, "runCount": 3, "value": "Off", "PUMP_IDX": 4, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "생활정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "공업(정)_1", "PUMP_TYP": 1, "runCount": 3, "value": "Off", "PUMP_IDX": 5, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "공업정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "공업(정)_2", "PUMP_TYP": 1, "runCount": 3, "value": "Off", "PUMP_IDX": 6, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "공업정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "공업(정)_3", "PUMP_TYP": 2, "runCount": 3, "value": "On", "PUMP_IDX": 7, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "공업정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "공업(정)_4", "PUMP_TYP": 1, "runCount": 3, "value": "Off", "PUMP_IDX": 8, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "공업정수지" }, { "PUMP_GRP": 3, "PUMP_NM": "선남(가)_1", "PUMP_TYP": 2, "runCount": 3, "value": "Off", "PUMP_IDX": 1, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "선남가압장" }, { "PUMP_GRP": 3, "PUMP_NM": "선남(가)_2", "PUMP_TYP": 1, "runCount": 3, "value": "Off", "PUMP_IDX": 2, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "선남가압장" }, { "PUMP_GRP": 3, "PUMP_NM": "선남(가)_3", "PUMP_TYP": 2, "runCount": 3, "value": "Off", "PUMP_IDX": 3, "ts": "2024-07-08 17:22:00", "PUMP_GRP_NM": "선남가압장" }] } }.data
      // this.data1 = { "code": 200, "message": "정상적으로 조회되었습니다.", "data": { "PRI": [{ "ts": "2024-06-26 16:59:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "부안정수장", "PUMP_NM": "부안(정)_1", "PRI_T_TAG": "892-360-PRI-4500", "value": "5.0588" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 7, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "주산가압장", "PUMP_NM": "주산(가)_1", "PRI_T_TAG": "892-480-PRI-8000", "value": "5.2300" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 11, "PUMP_GRP": 3, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "신림가압장", "PUMP_NM": "신림(가)_1", "PRI_T_TAG": "892-481-PRI-8000", "value": "6.8525" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 15, "PUMP_GRP": 4, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "무장가압장(A)", "PUMP_NM": "무장(가)(A)_1", "PRI_T_TAG": "892-482-PRI-8000", "value": "7.1200" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 17, "PUMP_GRP": 5, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "무장가압장(B)", "PUMP_NM": "무장(가)(B)_3", "PRI_T_TAG": "892-482-PRI-8002", "value": "5.6350" }], "pwiStatus": [{ "ts": "2024-06-26 16:59:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "부안정수장", "PUMP_NM": "부안(정)_1", "kW": 0.0 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 2, "PUMP_GRP": 1, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "부안정수장", "PUMP_NM": "부안(정)_2", "kW": 0.0 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 3, "PUMP_GRP": 1, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "부안정수장", "PUMP_NM": "부안(정)_3", "kW": 0.0 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "부안정수장", "PUMP_NM": "부안(정)_4", "kW": 247.68 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 5, "PUMP_GRP": 1, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "부안정수장", "PUMP_NM": "부안(정)_5", "kW": 229.45 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 6, "PUMP_GRP": 1, "PUMP_GRP_IDX": 6, "PUMP_GRP_NM": "부안정수장", "PUMP_NM": "부안(정)_6", "kW": 0.0 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 7, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "주산가압장", "PUMP_NM": "주산(가)_1", "kW": 150.32 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 8, "PUMP_GRP": 2, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "주산가압장", "PUMP_NM": "주산(가)_2", "kW": 148.31 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 9, "PUMP_GRP": 2, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "주산가압장", "PUMP_NM": "주산(가)_3", "kW": 0.0 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 10, "PUMP_GRP": 2, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "주산가압장", "PUMP_NM": "주산(가)_4", "kW": 0.0 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 11, "PUMP_GRP": 3, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "신림가압장", "PUMP_NM": "신림(가)_1", "kW": 0.0 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 12, "PUMP_GRP": 3, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "신림가압장", "PUMP_NM": "신림(가)_2", "kW": 127.29 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 13, "PUMP_GRP": 3, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "신림가압장", "PUMP_NM": "신림(가)_3", "kW": 0.0 }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 14, "PUMP_GRP": 3, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "신림가압장", "PUMP_NM": "신림(가)_4", "kW": 132.08 }], "FRI": [{ "ts": "2024-06-26 16:59:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "부안정수장", "PUMP_NM": "부안(정)_1", "FRI_TAG": "892-360-FRI-4500", "value": "2394.3750" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 7, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "주산가압장", "PUMP_NM": "주산(가)_1", "FRI_TAG": "892-480-FRI-8000", "value": "1546.5000" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 11, "PUMP_GRP": 3, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "신림가압장", "PUMP_NM": "신림(가)_1", "FRI_TAG": "892-481-FRI-8000", "value": "902.7188" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 15, "PUMP_GRP": 4, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "무장가압장(A)", "PUMP_NM": "무장(가)(A)_1", "FRI_TAG": "892-482-FRI-8000", "value": "216.5625" }], "SPI": [{ "ts": "2024-06-26 16:59:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "부안정수장", "PUMP_NM": "부안(정)_4", "SPI_TAG": "892-360-SPI-4502", "value": "59.9888" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 7, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "주산가압장", "PUMP_NM": "주산(가)_1", "SPI_TAG": "892-480-SPI-8500", "value": "58.0000" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 8, "PUMP_GRP": 2, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "주산가압장", "PUMP_NM": "주산(가)_2", "SPI_TAG": "892-480-SPI-8501", "value": "58.0000" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 9, "PUMP_GRP": 2, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "주산가압장", "PUMP_NM": "주산(가)_3", "SPI_TAG": "892-480-SPI-8502", "value": "0.0000" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 16, "PUMP_GRP": 4, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "무장가압장(A)", "PUMP_NM": "무장(가)(A)_2", "SPI_TAG": "892-482-SPI-6002", "value": "57.8213" }, { "ts": "2024-06-26 16:59:00", "PUMP_IDX": 17, "PUMP_GRP": 5, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "무장가압장(B)", "PUMP_NM": "무장(가)(B)_3", "SPI_TAG": "892-482-SPI-6003", "value": "0.0000" }], "pumpStatus": [{ "PUMP_GRP": 1, "PUMP_NM": "부안(정)_1", "PUMP_TYP": 1, "runCount": 8, "value": "Off", "PUMP_IDX": 1, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "부안정수장" }, { "PUMP_GRP": 1, "PUMP_NM": "부안(정)_2", "PUMP_TYP": 1, "runCount": 8, "value": "Off", "PUMP_IDX": 2, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "부안정수장" }, { "PUMP_GRP": 1, "PUMP_NM": "부안(정)_3", "PUMP_TYP": 1, "runCount": 8, "value": "Off", "PUMP_IDX": 3, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "부안정수장" }, { "PUMP_GRP": 1, "PUMP_NM": "부안(정)_4", "PUMP_TYP": 2, "runCount": 8, "value": "On", "PUMP_IDX": 4, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "부안정수장" }, { "PUMP_GRP": 1, "PUMP_NM": "부안(정)_5", "PUMP_TYP": 1, "runCount": 8, "value": "On", "PUMP_IDX": 5, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "부안정수장" }, { "PUMP_GRP": 1, "PUMP_NM": "부안(정)_6", "PUMP_TYP": 1, "runCount": 8, "value": "Off", "PUMP_IDX": 6, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "부안정수장" }, { "PUMP_GRP": 2, "PUMP_NM": "주산(가)_1", "PUMP_TYP": 2, "runCount": 8, "value": "On", "PUMP_IDX": 1, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "주산가압장" }, { "PUMP_GRP": 2, "PUMP_NM": "주산(가)_2", "PUMP_TYP": 2, "runCount": 8, "value": "On", "PUMP_IDX": 2, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "주산가압장" }, { "PUMP_GRP": 2, "PUMP_NM": "주산(가)_3", "PUMP_TYP": 2, "runCount": 8, "value": "Off", "PUMP_IDX": 3, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "주산가압장" }, { "PUMP_GRP": 2, "PUMP_NM": "주산(가)_4", "PUMP_TYP": 1, "runCount": 8, "value": "Off", "PUMP_IDX": 4, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "주산가압장" }, { "PUMP_GRP": 3, "PUMP_NM": "신림(가)_1", "PUMP_TYP": 1, "runCount": 8, "value": "Off", "PUMP_IDX": 1, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "신림가압장" }, { "PUMP_GRP": 3, "PUMP_NM": "신림(가)_2", "PUMP_TYP": 1, "runCount": 8, "value": "On", "PUMP_IDX": 2, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "신림가압장" }, { "PUMP_GRP": 3, "PUMP_NM": "신림(가)_3", "PUMP_TYP": 1, "runCount": 8, "value": "Off", "PUMP_IDX": 3, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "신림가압장" }, { "PUMP_GRP": 3, "PUMP_NM": "신림(가)_4", "PUMP_TYP": 1, "runCount": 8, "value": "On", "PUMP_IDX": 4, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "신림가압장" }, { "PUMP_GRP": 4, "PUMP_NM": "무장(가)(A)_1", "PUMP_TYP": 1, "runCount": 8, "value": "On", "PUMP_IDX": 1, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "무장가압장(A)" }, { "PUMP_GRP": 4, "PUMP_NM": "무장(가)(A)_2", "PUMP_TYP": 2, "runCount": 8, "value": "On", "PUMP_IDX": 2, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "무장가압장(A)" }, { "PUMP_GRP": 5, "PUMP_NM": "무장(가)(B)_3", "PUMP_TYP": 2, "runCount": 8, "value": "Off", "PUMP_IDX": 3, "ts": "2024-06-26 16:59:00", "PUMP_GRP_NM": "무장가압장(B)" }] } }.data
      // this.data1 = { "code": 200, "message": "정상적으로 조회되었습니다.", "data": { "PRI": [{ "ts": "2024-01-30 18:47:00", "PUMP_IDX": 8, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_1", "value": "0.9613" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 9, "PUMP_GRP": 2, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_2", "value": "0.6075" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 10, "PUMP_GRP": 2, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_3", "value": "6.4675" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 11, "PUMP_GRP": 2, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_4", "value": "0.4988" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_1", "value": "0.3831" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 2, "PUMP_GRP": 1, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_2", "value": "6.0644" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 3, "PUMP_GRP": 1, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_3", "value": "0.3775" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_4", "value": "5.9663" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 5, "PUMP_GRP": 1, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_5", "value": "1.9563" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 6, "PUMP_GRP": 1, "PUMP_GRP_IDX": 6, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_6", "value": "5.9413" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 7, "PUMP_GRP": 1, "PUMP_GRP_IDX": 7, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_7", "value": "6.1350" }], "pwiStatus": [{ "ts": "2024-01-30 18:47:00", "PUMP_IDX": 8, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_1", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 9, "PUMP_GRP": 2, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_2", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 10, "PUMP_GRP": 2, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_3", "kW": 686.49 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_1", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 2, "PUMP_GRP": 1, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_2", "kW": 648.21 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 3, "PUMP_GRP": 1, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_3", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_4", "kW": 9.5 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 5, "PUMP_GRP": 1, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_5", "kW": 0.0 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 6, "PUMP_GRP": 1, "PUMP_GRP_IDX": 6, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_6", "kW": 10.83 }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 7, "PUMP_GRP": 1, "PUMP_GRP_IDX": 7, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_7", "kW": 886.69 }], "FRI": [{ "ts": "2024-01-30 18:47:00", "PUMP_IDX": 8, "PUMP_GRP": 2, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_1", "value": "3343.5000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 9, "PUMP_GRP": 2, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_2", "value": "3343.5000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 10, "PUMP_GRP": 2, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_3", "value": "3343.5000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 11, "PUMP_GRP": 2, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(신)정수지", "PUMP_NM": "(신)정수지_4", "value": "3343.5000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 1, "PUMP_GRP": 1, "PUMP_GRP_IDX": 1, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_1", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 2, "PUMP_GRP": 1, "PUMP_GRP_IDX": 2, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_2", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 3, "PUMP_GRP": 1, "PUMP_GRP_IDX": 3, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_3", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 4, "PUMP_GRP": 1, "PUMP_GRP_IDX": 4, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_4", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 5, "PUMP_GRP": 1, "PUMP_GRP_IDX": 5, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_5", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 6, "PUMP_GRP": 1, "PUMP_GRP_IDX": 6, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_6", "value": "17928.0000" }, { "ts": "2024-01-30 18:47:00", "PUMP_IDX": 7, "PUMP_GRP": 1, "PUMP_GRP_IDX": 7, "PUMP_GRP_NM": "(구)정수지", "PUMP_NM": "(구)정수지_7", "value": "17928.0000" }], "SPI": [], "pumpStatus": [{ "PUMP_GRP": 2, "PUMP_NM": "(신)정수지_1", "PUMP_GRP_IDX": 1, "runCount": 5, "value": "Off", "PUMP_IDX": 8, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(신)정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "(신)정수지_2", "PUMP_GRP_IDX": 2, "runCount": 5, "value": "Off", "PUMP_IDX": 9, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(신)정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "(신)정수지_3", "PUMP_GRP_IDX": 3, "runCount": 5, "value": "On", "PUMP_IDX": 10, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(신)정수지" }, { "PUMP_GRP": 2, "PUMP_NM": "(신)정수지_4", "PUMP_GRP_IDX": 4, "runCount": 5, "value": "Off", "PUMP_IDX": 11, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(신)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_1", "PUMP_GRP_IDX": 1, "runCount": 5, "value": "Off", "PUMP_IDX": 1, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_2", "PUMP_GRP_IDX": 2, "runCount": 5, "value": "On", "PUMP_IDX": 2, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_3", "PUMP_GRP_IDX": 3, "runCount": 5, "value": "Off", "PUMP_IDX": 3, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_4", "PUMP_GRP_IDX": 4, "runCount": 5, "value": "On", "PUMP_IDX": 4, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_5", "PUMP_GRP_IDX": 5, "runCount": 5, "value": "Off", "PUMP_IDX": 5, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_6", "PUMP_GRP_IDX": 6, "runCount": 5, "value": "On", "PUMP_IDX": 6, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }, { "PUMP_GRP": 1, "PUMP_NM": "(구)정수지_7", "PUMP_GRP_IDX": 7, "runCount": 5, "value": "On", "PUMP_IDX": 7, "ts": "2024-01-30 18:47:00", "PUMP_GRP_NM": "(구)정수지" }] } }.data
      // this.data = { "code": 200, "message": "정상적으로 조회되었습니다.", "data": [{ "TNK_GRP_IDX": 1, "TNK_IDX": 2, "TNK_GRP_NM": "다산면배수지", "TNK_NM": "수위2", "IN_FO_TAG": "780-344-VVB-801B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-801C", "IN_FC": "0.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8008", "IN_POI": "34.3500", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8022", "수위": "2.6292", "IN_FLW_TAG": "780-344-FRI-8015", "유입유량": "226.9876", "OUT_FLW_TAG": "780-344-FRI-8016", "유출유량": "228.5499", "최소요구관압": 8.5 }, { "TNK_GRP_IDX": 1, "TNK_IDX": 1, "TNK_GRP_NM": "다산면배수지", "TNK_NM": "수위1", "IN_FO_TAG": "780-344-VVB-801B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-801C", "IN_FC": "0.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8008", "IN_POI": "34.3500", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8023", "수위": "5.0270", "IN_FLW_TAG": "780-344-FRI-8015", "유입유량": "226.9876", "OUT_FLW_TAG": "780-344-FRI-8017", "유출유량": "6.4000", "최소요구관압": 8.5 }, { "TNK_GRP_IDX": 2, "TNK_IDX": 1, "TNK_GRP_NM": "다산산단배수지(생활)", "TNK_NM": "수위1", "IN_FO_TAG": "780-344-VVB-821B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-821C", "IN_FC": "0.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8013", "IN_POI": "21.1750", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8020", "수위": "2.7230", "IN_FLW_TAG": "780-344-FRI-8012", "유입유량": "50.4404", "OUT_FLW_TAG": "780-344-FRI-8018", "유출유량": "44.0000", "최소요구관압": 8.8 }, { "TNK_GRP_IDX": 2, "TNK_IDX": 2, "TNK_GRP_NM": "다산산단배수지(생활)", "TNK_NM": "수위2", "IN_FO_TAG": "780-344-VVB-821B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-821C", "IN_FC": "0.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8013", "IN_POI": "21.1750", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8021", "수위": "2.7100", "IN_FLW_TAG": "780-344-FRI-8012", "유입유량": "50.4404", "OUT_FLW_TAG": "780-344-FRI-8018", "유출유량": "44.0000", "최소요구관압": 8.8 }, { "TNK_GRP_IDX": 6, "TNK_IDX": 1, "TNK_GRP_NM": "성주통합배수지", "TNK_NM": "수위1", "IN_FO_TAG": "780-344-VVB-827B", "IN_FO": "1.0000", "OUT_FO_TAG": "780-344-VVB-829B", "OUT_FO": "1.0000", "IN_FC_TAG": "780-344-VVB-827C", "IN_FC": "0.0000", "OUT_FC_TAG": "780-344-VVB-829C", "OUT_FC": "0.0000", "IN_POI_TAG": "780-344-POI-8018", "IN_POI": "100.0000", "OUT_POI_TAG": "780-344-POI-8020", "OUT_POI": "100.0000", "LEI_TAG": "780-344-LEI-8040", "수위": "3.0700", "IN_FLW_TAG": "780-344-FRI-8053", "유입유량": "259.2000", "OUT_FLW_TAG": "780-344-FRI-8035", "유출유량": "197.0000", "최소요구관압": 1.79 }, { "TNK_GRP_IDX": 6, "TNK_IDX": 2, "TNK_GRP_NM": "성주통합배수지", "TNK_NM": "수위2", "IN_FO_TAG": "780-344-VVB-828B", "IN_FO": "1.0000", "OUT_FO_TAG": "780-344-VVB-830B", "OUT_FO": "1.0000", "IN_FC_TAG": "780-344-VVB-828C", "IN_FC": "0.0000", "OUT_FC_TAG": "780-344-VVB-830C", "OUT_FC": "0.0000", "IN_POI_TAG": "780-344-POI-8019", "IN_POI": "99.0000", "OUT_POI_TAG": "780-344-POI-8021", "OUT_POI": "100.0000", "LEI_TAG": "780-344-LEI-8041", "수위": "2.9800", "IN_FLW_TAG": "780-344-FRI-8053", "유입유량": "259.2000", "OUT_FLW_TAG": "780-344-FRI-8035", "유출유량": "197.0000", "최소요구관압": 1.79 }, { "TNK_GRP_IDX": 19, "TNK_IDX": 1, "TNK_GRP_NM": "개포통합배수지", "TNK_NM": "수위1", "IN_FO_TAG": "801-506-208-VVC-83AB", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "801-506-208-VVC-83AC", "IN_FC": "0.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "801-506-208-VVI-803A", "IN_POI": "37.2250", "OUT_POI_TAG": "801-506-208-VVI-803C", "OUT_POI": "0.0000", "LEI_TAG": "780-344-LEI-8010", "수위": "2.8688", "IN_FLW_TAG": "801-506-208-FRI-8030", "유입유량": "54.0500", "OUT_FLW_TAG": "801-506-208-FRI-2006", "유출유량": "61.0130", "최소요구관압": 3.81 }, { "TNK_GRP_IDX": 19, "TNK_IDX": 2, "TNK_GRP_NM": "개포통합배수지", "TNK_NM": "수위2", "IN_FO_TAG": "801-506-208-VVC-83BB", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "801-506-208-VVC-83BC", "IN_FC": "0.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "801-506-208-VVI-803B", "IN_POI": "18.5500", "OUT_POI_TAG": "801-506-208-VVI-803D", "OUT_POI": "0.0000", "LEI_TAG": "780-344-LEI-8013", "수위": "2.8738", "IN_FLW_TAG": "801-506-208-FRI-8030", "유입유량": "54.0500", "OUT_FLW_TAG": "801-506-208-FRI-2006", "유출유량": "61.0130", "최소요구관압": 3.81 }] }.data
      // this.data5 = { "code": 200, "message": "정상적으로 조회되었습니다.", "data": [{ "TNK_GRP_IDX": 3, "TNK_IDX": 1, "TNK_GRP_NM": "다산산단배수지(공업)", "TNK_NM": "수위1", "IN_FO_TAG": "780-344-VVB-822B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-822C", "IN_FC": "1.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8009", "IN_POI": "98.5250", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8012", "수위": "2.4620", "IN_FLW_TAG": "780-344-FRI-8009", "유입유량": "35.9557", "OUT_FLW_TAG": "780-344-FRI-8038", "유출유량": "0.0000", "최소요구관압": 6.7 }, { "TNK_GRP_IDX": 3, "TNK_IDX": 2, "TNK_GRP_NM": "다산산단배수지(공업)", "TNK_NM": "수위2", "IN_FO_TAG": "780-344-VVB-822B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-822C", "IN_FC": "1.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8009", "IN_POI": "98.5250", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8027", "수위": "2.4990", "IN_FLW_TAG": "780-344-FRI-8009", "유입유량": "35.9557", "OUT_FLW_TAG": "780-344-FRI-8038", "유출유량": "0.0000", "최소요구관압": 6.7 }, { "TNK_GRP_IDX": 5, "TNK_IDX": 1, "TNK_GRP_NM": "달성1차배수지", "TNK_NM": "수위1", "IN_FO_TAG": "780-344-VVB-812B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-812C", "IN_FC": "0.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8011", "IN_POI": "17.9250", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8001", "수위": "3.1529", "IN_FLW_TAG": "780-344-FRI-8010", "유입유량": "455.6023", "OUT_FLW_TAG": "780-344-FRI-8029", "유출유량": "4350.9000", "최소요구관압": 6.6 }, { "TNK_GRP_IDX": 5, "TNK_IDX": 2, "TNK_GRP_NM": "달성1차배수지", "TNK_NM": "수위2", "IN_FO_TAG": "780-344-VVB-812B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-812C", "IN_FC": "0.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8011", "IN_POI": "17.9250", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8002", "수위": "3.0993", "IN_FLW_TAG": "780-344-FRI-8010", "유입유량": "455.6023", "OUT_FLW_TAG": "780-344-FRI-8029", "유출유량": "4350.9000", "최소요구관압": 6.6 }, { "TNK_GRP_IDX": 8, "TNK_IDX": 1, "TNK_GRP_NM": "달성2차배수지", "TNK_NM": "수위1", "IN_FO_TAG": "780-344-VVB-813B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-813C", "IN_FC": "1.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8012", "IN_POI": "0.0000", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8017", "수위": "0.2206", "IN_FLW_TAG": "780-344-FRI-8011", "유입유량": "0.0000", "OUT_FLW_TAG": "780-344-FRI-8028", "유출유량": "6.2500", "최소요구관압": 3.8 }, { "TNK_GRP_IDX": 8, "TNK_IDX": 2, "TNK_GRP_NM": "달성2차배수지", "TNK_NM": "수위2", "IN_FO_TAG": "780-344-VVB-813B", "IN_FO": "0.0000", "OUT_FO_TAG": "", "IN_FC_TAG": "780-344-VVB-813C", "IN_FC": "1.0000", "OUT_FC_TAG": "", "IN_POI_TAG": "780-344-POI-8013", "IN_POI": "20.7500", "OUT_POI_TAG": "", "LEI_TAG": "780-344-LEI-8018", "수위": "1.9712", "IN_FLW_TAG": "780-344-FRI-8011", "유입유량": "0.0000", "OUT_FLW_TAG": "780-344-FRI-8028", "유출유량": "6.2500", "최소요구관압": 3.8 }, { "TNK_GRP_IDX": 12, "TNK_IDX": 1, "TNK_GRP_NM": "넥센대합배수지", "TNK_NM": "수위1", "IN_FO_TAG": "780-344-VVB-834,780-344-VVB-834,780-344-VVB-834,780-344-VVB-834", "IN_FO": "0.0000,0.0000,0.0000,0.0000", "OUT_FO_TAG": ",,,", "IN_FC_TAG": "780-344-VVB-835,780-344-VVB-835,780-344-VVB-835,780-344-VVB-835", "IN_FC": "1.0000,1.0000,1.0000,1.0000", "OUT_FC_TAG": ",,,", "IN_POI_TAG": "780-344-POI-8024,780-344-POI-8024,780-344-POI-8024,780-344-POI-8024", "IN_POI": "0.0000,0.0000,0.0000,0.0000", "OUT_POI_TAG": ",,,", "LEI_TAG": "780-344-LEI-8036", "수위": "3.2500", "IN_FLW_TAG": "780-344-FRI-8031", "유입유량": "21.9000", "OUT_FLW_TAG": "780-344-FRI-8041", "유출유량": "0.0000", "최소요구관압": 4.5 }, { "TNK_GRP_IDX": 12, "TNK_IDX": 2, "TNK_GRP_NM": "넥센대합배수지", "TNK_NM": "수위2", "IN_FO_TAG": "780-344-VVB-842,780-344-VVB-842,780-344-VVB-842,780-344-VVB-842", "IN_FO": "0.0000,0.0000,0.0000,0.0000", "OUT_FO_TAG": ",,,", "IN_FC_TAG": "780-344-VVB-843,780-344-VVB-843,780-344-VVB-843,780-344-VVB-843", "IN_FC": "1.0000,1.0000,1.0000,1.0000", "OUT_FC_TAG": ",,,", "IN_POI_TAG": "780-344-POI-8025,780-344-POI-8025,780-344-POI-8025,780-344-POI-8025", "IN_POI": "0.0000,0.0000,0.0000,0.0000", "OUT_POI_TAG": ",,,", "LEI_TAG": "780-344-LEI-8037", "수위": "3.2600", "IN_FLW_TAG": "780-344-FRI-8031", "유입유량": "21.9000", "OUT_FLW_TAG": "780-344-FRI-8041", "유출유량": "0.0000", "최소요구관압": 4.5 }] }.data
      this.data2 = results[2].status === 'fulfilled' ? results[2].value : null;
      this.data3 = results[3].status === 'fulfilled' ? results[3].value : null;
      this.data4 = results[4].status === 'fulfilled' ? results[4].value : null;
      this.data5 = results[5].status === 'fulfilled' ? results[5].value : null;
      this.data6 = results[6].status === 'fulfilled' ? results[6].value : null;
      this.data7 = results[7].status === 'fulfilled' ? results[7].value : null;
      this.data8 = results[8].status === 'fulfilled' ? results[8].value : null;
      this.data9 = results[9].status === 'fulfilled' ? results[9].value : null;
      this.data10 = results[10].status === 'fulfilled' ? results[10].value : null;
      this.data11 = results[11].status === 'fulfilled' ? results[11].value : null;
      this.data12 = results[12].status === 'fulfilled' ? results[12].value : null;
      this.data13 = results[13].status === 'fulfilled' ? results[13].value : null;
      this.data14 = results[14].status === 'fulfilled' ? results[14].value : null;
      this.data15 = results[15].status === 'fulfilled' ? results[15].value : null;
      this.data16 = results[16].status === 'fulfilled' ? results[16].value : null;
      this.isLoading = false
      this.$store.state.data1 = this.data1
      this.$store.state.data2 = this.data2
      this.$store.state.data3 = this.data3
      this.$store.state.data6 = this.data6
      this.$store.state.data7 = this.data7
      this.$store.state.data10 = this.data10
      this.$store.state.data11 = this.data11
      this.$store.state.data12 = this.data12
      this.$store.state.data13 = this.data13
      this.$store.state.data14 = this.data14
      this.$store.state.data15 = this.data15
      this.$store.state.data16 = this.data16
      this.sortingData(this.data)
      this.settingData()
      for (let i = 1; i <= 5; i++) {
        this.presValue.push(this.data1?.PRI?.filter(item => item?.PUMP_GRP === i)[0]?.value);
      }
      this.maxSpiData.name = this.data[0]?.TNK_GRP_NM?.replace('배수지', '')
      this.maxSpiData.point = this.data[0]?.최소요구관압?.toFixed(2)
      this.maxSpiData.pres = this.data[0]?.최소요구관압?.toFixed(2)
      this.$refs.PumpControlRigTopLeftTop.settingValue(this.maxSpiData)
    },
    settingData() {
      const tmpPUMP_GRP_NM = new Set();
      // const defaultItem = { name: '', unit: '' };
      this.data1?.PRI.forEach(element => {
        tmpPUMP_GRP_NM.add(element.PUMP_GRP_NM)
      })
      const selectedPUMP_GRP_NM = Array.from(tmpPUMP_GRP_NM)

      if (selectedPUMP_GRP_NM.length == 2) {
        this.rigItem.push([{ name: '', unit: '' }, { name: '', unit: '' }], [{ name: '', unit: '' }, { name: '', unit: '' }])
      }
      else if (selectedPUMP_GRP_NM.length == 1) {
        this.rigItem.push([{ name: '', unit: '' }], [{ name: '', unit: '' }])
      }
      else if (selectedPUMP_GRP_NM.length == 3) {
        this.rigItem.push([{ name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }], [{ name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }])
      }
      else if (selectedPUMP_GRP_NM.length == 4) {
        this.rigItem.push([{ name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }], [{ name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }])
      }
      else if (selectedPUMP_GRP_NM.length == 5) {
        this.rigItem.push([{ name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }], [{ name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }, { name: '', unit: '' }])
      }

      this.rigItem?.forEach((subArray, i) => {
        subArray.forEach((item, j) => {
          const name = selectedPUMP_GRP_NM[j] + ((i === 0 || i % 2 === 0) ? ' 관압' : ' 펌프');
          const unit = (i === 0 || i % 2 === 0) ? 'kg/cm²' : '대';

          if (name.startsWith('undefined')) {
            item.name = "No Data"
          } else {
            item.name = name;
          }
          item.unit = unit;
        });
      });
    },
    sortingData(data) {
      data?.sort((a, b) => a.TNK_GRP_IDX - b.TNK_GRP_IDX);

      const selectedTNK_GRP_IDX = new Set();
      const filteredData = [];

      for (const item of data) {
        // if (selectedTNK_GRP_IDX.size >= 5 && !selectedTNK_GRP_IDX.has(item.TNK_GRP_IDX)) {
        //   break;
        // }

        selectedTNK_GRP_IDX.add(item.TNK_GRP_IDX);
        filteredData.push(item);
      }
      const groupedData = [];

      const groupMap = new Map();

      filteredData?.forEach(item => {
        const TNK_GRP_IDX = item.TNK_GRP_IDX;

        if (!groupMap?.has(TNK_GRP_IDX)) {
          groupMap.set(TNK_GRP_IDX, []);
        }

        groupMap?.get(TNK_GRP_IDX).push(item);
      });
      groupMap?.forEach(group => {
        groupedData.push(group);
      });
      this.sujiList = Array.from(new Set(filteredData?.map(item => item.TNK_GRP_NM?.replace('배수지', ''))));
      groupedData?.forEach((element, index) => {
        if (element.length <= 1) {
          this.majorData.push(
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[0]?.유입유량 || 0)?.toFixed(2),
              valueRate: parseFloat(element[0]?.IN_FO || 0)?.toFixed(2),
              waterLevel: parseFloat(element[0]?.수위 || 0)?.toFixed(2),
              outflowVal: parseFloat(element[0]?.유출유량 || 0)?.toFixed(2),
              dmd_pri: parseFloat(element[0]?.최소요구관압 || 0)?.toFixed(2), // 최소요구관압
            }
          )
        }
        else if (element.length <= 2) {
          this.majorData.push(
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[0]?.유입유량 || 0)?.toFixed(2),
              valueRate: parseFloat(element[0]?.IN_FO || 0)?.toFixed(2),
              valueRate2: parseFloat(element[1]?.IN_FO || 0)?.toFixed(2),
              waterLevel: parseFloat(element[0]?.수위 || 0)?.toFixed(2),
              waterLevel2: parseFloat(element[1]?.수위 || 0)?.toFixed(2),
              outflowVal: parseFloat(element[1]?.유출유량 || 0)?.toFixed(2),
              dmd_pri: parseFloat(element[0]?.최소요구관압 || 0)?.toFixed(2), // 최소요구관압
            }
          )
        }
        else if (element.length <= 3) {
          this.majorData.push(
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[0]?.유입유량 || 0)?.toFixed(2),
              valueRate: parseFloat(element[0]?.IN_FO || 0)?.toFixed(2),
              valueRate2: parseFloat(element[1]?.IN_FO || 0)?.toFixed(2),
              valueRate3: parseFloat(element[2]?.IN_FO || 0)?.toFixed(2),
              waterLevel: parseFloat(element[0]?.수위 || 0)?.toFixed(2),
              waterLevel2: parseFloat(element[1]?.수위 || 0)?.toFixed(2),
              waterLevel3: parseFloat(element[2]?.수위 || 0)?.toFixed(2),
              outflowVal: parseFloat(element[1]?.유출유량 || 0)?.toFixed(2),
              dmd_pri: parseFloat(element[0]?.최소요구관압 || 0)?.toFixed(2), // 최소요구관압
            }
          )
        }
        else if (element.length <= 5) {
          this.majorData.push(
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[0]?.유입유량 || 0)?.toFixed(2),
              valueRate: parseFloat(element[0]?.IN_FO || 0)?.toFixed(2),
              valueRate2: parseFloat(element[1]?.IN_FO || 0)?.toFixed(2),
              waterLevel: parseFloat(element[0]?.수위 || 0)?.toFixed(2),
              waterLevel2: parseFloat(element[1]?.수위 || 0)?.toFixed(2),
              outflowVal: parseFloat(element[1]?.유출유량 || 0)?.toFixed(2),
              dmd_pri: parseFloat(element[0]?.최소요구관압 || 0)?.toFixed(2), // 최소요구관압
            },
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[2]?.유입유량 || 0)?.toFixed(2),
              valueRate: parseFloat(element[2]?.IN_FO || 0)?.toFixed(2),
              valueRate2: parseFloat(element[3]?.IN_FO || 0)?.toFixed(2),
              valueRate3: parseFloat(element[4]?.IN_FO || 0)?.toFixed(2),
              waterLevel: parseFloat(element[2]?.수위 || 0)?.toFixed(2),
              waterLevel2: parseFloat(element[3]?.수위 || 0)?.toFixed(2),
              waterLevel3: parseFloat(element[4]?.수위 || 0)?.toFixed(2),
              outflowVal: parseFloat(element[3]?.유출유량 || 0)?.toFixed(2),
              dmd_pri: parseFloat(element[2]?.최소요구관압 || 0)?.toFixed(2), // 최소요구관압
            }
          )
        }
        else {
          this.majorData.push(
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[0]?.유입유량 || 0)?.toFixed(2),
              valueRate: parseFloat(element[0]?.IN_FO || 0)?.toFixed(2),
              valueRate2: parseFloat(element[1]?.IN_FO || 0)?.toFixed(2),
              waterLevel: parseFloat(element[0]?.수위 || 0)?.toFixed(2),
              waterLevel2: parseFloat(element[1]?.수위 || 0)?.toFixed(2),
              outflowVal: parseFloat(element[1]?.유출유량 || 0)?.toFixed(2),
              dmd_pri: parseFloat(element[0]?.최소요구관압 || 0)?.toFixed(2), // 최소요구관압
            },
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[2]?.유입유량 || 0)?.toFixed(2),
              valueRate: parseFloat(element[2]?.IN_FO || 0)?.toFixed(2),
              valueRate2: parseFloat(element[3]?.IN_FO || 0)?.toFixed(2),
              waterLevel: parseFloat(element[2]?.수위 || 0)?.toFixed(2),
              waterLevel2: parseFloat(element[3]?.수위 || 0)?.toFixed(2),
              outflowVal: parseFloat(element[3]?.유출유량 || 0)?.toFixed(2),
              dmd_pri: parseFloat(element[2]?.최소요구관압 || 0)?.toFixed(2), // 최소요구관압
            },
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[4]?.유입유량 || 0)?.toFixed(2),
              valueRate: parseFloat(element[4]?.IN_FO || 0)?.toFixed(2),
              valueRate2: parseFloat(element[5]?.IN_FO || 0)?.toFixed(2),
              waterLevel: parseFloat(element[4]?.수위 || 0)?.toFixed(2),
              waterLevel2: parseFloat(element[5]?.수위 || 0)?.toFixed(2),
              outflowVal: parseFloat(element[5]?.유출유량 || 0)?.toFixed(2),
              dmd_pri: parseFloat(element[4]?.최소요구관압 || 0)?.toFixed(2), // 최소요구관압
            },
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[6]?.유입유량 || 0)?.toFixed(2),
              valueRate: parseFloat(element[6]?.IN_FO || 0)?.toFixed(2),
              valueRate2: parseFloat(element[7]?.IN_FO || 0)?.toFixed(2),
              waterLevel: parseFloat(element[6]?.수위 || 0)?.toFixed(2),
              waterLevel2: parseFloat(element[7]?.수위 || 0)?.toFixed(2),
              outflowVal: parseFloat(element[7]?.유출유량 || 0)?.toFixed(2),
              dmd_pri: parseFloat(element[6]?.최소요구관압 || 0)?.toFixed(2), // 최소요구관압
            }
          )
        }
      });
      this.major.push(this.majorData)
      this.$refs.PumpControlMid.sendingData(this.major, this.tabIndex)
      this.majorData = []
    },

    async changePumpControl() {
      const dataAi = await fetchFunc(`${this.$apiURL}/ai/selectAiStatus`);
      let firPumpStatus = dataAi?.data[0]?.AI_STATUS
      let secPumpStatus = dataAi?.data[1]?.AI_STATUS
      let thrPumpStatus = dataAi?.data[2]?.AI_STATUS
      let fouPumpStatus = dataAi?.data[3]?.AI_STATUS
      let fivPumpStatus = dataAi?.data[4]?.AI_STATUS
      if (dataAi?.data[0]?.emergencyStatus == "1") {
        firPumpStatus = 2
      } else {
        firPumpStatus = dataAi?.data[0]?.AI_STATUS
      }
      if (dataAi?.data[1]?.emergencyStatus == "1") {
        secPumpStatus = 2
      } else {
        secPumpStatus = dataAi?.data[1]?.AI_STATUS
      }
      if (dataAi?.data[2]?.emergencyStatus == "1") {
        thrPumpStatus = 2
      } else {
        thrPumpStatus = dataAi?.data[2]?.AI_STATUS
      }
      if (dataAi?.data[3]?.emergencyStatus == "1") {
        fouPumpStatus = 2
      } else {
        fouPumpStatus = dataAi?.data[3]?.AI_STATUS
      }
      if (dataAi?.data[4]?.emergencyStatus == "1") {
        fouPumpStatus = 2
      } else {
        fivPumpStatus = dataAi?.data[4]?.AI_STATUS
      }
      this.$store.state.firAiFlag = parseInt(firPumpStatus)
      this.$store.state.secAiFlag = parseInt(secPumpStatus)
      this.$store.state.thrAiFlag = parseInt(thrPumpStatus)
      this.$store.state.fouAiFlag = parseInt(fouPumpStatus)
      this.$store.state.fivAiFlag = parseInt(fivPumpStatus)

      if (this.$area === 'buan') {
        if (this.tabIndex === 0) {
          this.$refs.AiMode.changeAuto(parseInt(firPumpStatus), parseInt(dataAi?.data[0]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
        } else if (this.tabIndex === 1) {
          this.$refs.AiMode.changeAuto(parseInt(secPumpStatus), parseInt(dataAi?.data[1]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
        } else if (this.tabIndex === 2) {
          this.$refs.AiMode.changeAuto(parseInt(thrPumpStatus), parseInt(dataAi?.data[2]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
        } else if (this.tabIndex === 3) {
          this.$refs.AiMode.changeAuto(parseInt(fouPumpStatus), parseInt(dataAi?.data[3]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
        } else if (this.tabIndex === 4) {
          this.$refs.AiMode.changeAuto(parseInt(fivPumpStatus), parseInt(dataAi?.data[4]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus, thrPumpStatus, fouPumpStatus, fivPumpStatus)
        }
      }
      else if (this.$area === 'goryeong') {
        if (this.tabIndex === 0) {
          this.$refs.AiMode.changeAuto(parseInt(firPumpStatus), parseInt(dataAi?.data[0]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus, thrPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus, thrPumpStatus)
        } else if (this.tabIndex === 1) {
          this.$refs.AiMode.changeAuto(parseInt(secPumpStatus), parseInt(dataAi?.data[1]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus, thrPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus, thrPumpStatus)
        } else if (this.tabIndex === 2) {
          this.$refs.AiMode.changeAuto(parseInt(thrPumpStatus), parseInt(dataAi?.data[2]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus, thrPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus, thrPumpStatus)
        }
      }
      else {
        if (this.tabIndex === 0) {
          this.$refs.AiMode?.changeAuto(parseInt(firPumpStatus), parseInt(dataAi?.data[0]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus)
        } else {
          this.$refs.AiMode?.changeAuto(parseInt(secPumpStatus), parseInt(dataAi?.data[1]?.emergencyStatus))
          this.$refs.PumpControlLeft.changePumpControlLeft(firPumpStatus, secPumpStatus)
          this.$refs.PumpControlRig.changePumpControlRig(firPumpStatus, secPumpStatus)
        }
      }
    }
  },
  emits: ['onChangeBgClass']
}
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.r-circle {
  background: url("@/assets/img/r_circle.png") no-repeat;
  background-position: center;
  background-size: contain;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pump_area_h4 {
  height: calc(100%/ 4);
  width: calc(100%);
}

.pump_area_h35 {
  height: 39%;
  width: 100%;
}

span {
  color: #FFF;
  font-size: 18px;
}

.pump_img {
  background: url("@/assets/img/peakcontrol/pump_peakcontrol.png") no-repeat;
  background-size: 34%;
  background-position: center;
  text-align: left;
  text-indent: 5%;
  mix-blend-mode: color-dodge;
}


.detail_text {
  width: 70%;
  text-shadow: 0 0 9px #5cafff;
  color: #c3eaff;
}

.detail_value {
  width: 30%;
  font-family: LAB디지털;
  text-align: right;
}

/* 주요인자 */
.water_wrap {
  width: 100%;
  height: 100%;
  background: url("@/assets/img/analysis/watertank_big.png") no-repeat;
  background-size: 100% 80%;
  background-position: 50% 50%;
  margin: 0 0 0 -24%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
}

.right_title_font {
  font-size: 21px;
  font-weight: bold;
  color: #5180b4;
  line-height: 44px;
  font-family: 'KHNPHDRegular';
}

.input_water_top {
  width: 72% !important;
  margin: 0 0 5% 0 !important;
  background-color: #15284e54 !important;
}

.input_water_bottom {
  width: 72% !important;
  margin: 0 0 20% 0 !important;
  background-color: #15284e54 !important;
}

.input_box {
  height: 25px;
  width: 100%;
  font-size: 11px;
  border-radius: 3px;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #a4ceed;
  text-align: center;
  font-family: 'KHNPHDRegular';
  display: flex;
  align-items: center;
  justify-content: center;
}

.input_box_rate {
  width: 40% !important;
  height: 36% !important;
  margin: 3px 0 0 -10%;
}

.bm10 {
  margin-bottom: 10%;
}

.input_value {
  font-family: 'LAB디지털' !important;
  margin-right: 2px;
  font-size: 15px;
  color: #fff;
}

.input_value_rate {
  font-family: 'LAB디지털' !important;
  margin-right: 2px;
  font-size: 12px;
  color: #fff;
}

.pipe_line {
  width: 47%;
  height: 41%;
  text-align: center;
  background: url(@/assets/img/analysis/pipeline_un.png) no-repeat;
  background-size: 100% 15px;
  background-position: center;
  /* margin: 1.5% 0 0 -7%; */
}

.pipe_line_arrow {
  background: url("@/assets/img/analysis/pipeline_arrow.png") no-repeat;
  width: 100%;
  height: 15px;
  mix-blend-mode: color-dodge;
  background-position: center;
  background-position: center;
  margin-top: 7px;
}

.pipe_first_wrap {
  width: 18%;
  height: 100%;
  text-align: center;
  display: flex;
  align-items: center;
}

.pipe_first_wrap2 {
  width: 70%;
  margin-top: -13%;
  z-index: 1;
}

.blinking {
  -webkit-animation: blink 3s linear infinite;
  -moz-animation: blink 3s linear infinite;
  animation: blink 3s linear infinite;
}

.pipe_last_wrap {
  width: 15%;
  height: 100%;
  text-align: center;
  display: flex;
  align-items: flex-end;
}

.pipe_last_wrap2 {
  width: 87%;
  height: 70%;
}

.pipe_center_wrap {
  height: 100%;
  width: 20%;
  margin-left: -1%;
}

.pipe_center_top {
  width: 100%;
  height: 50%;
  text-align: center;
}

.pipe_center_bottom {
  width: 100%;
  height: 50%;
  text-align: center;
  /* margin-top: -6%; */
}

.pipe_name {
  width: 18%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  /* background: url(@/assets/img/r_circle.png) no-repeat;
    background-position: center; */
  margin-right: 2%;
  display: flex !important;
  align-items: center !important;
}

.circle-dot {
  max-height: 85%;
  border-style: dotted;
  border-color: #546b7d;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 2%;
  white-space: normal;
}

.pipe_first {
  width: 30%;
  height: 19px;
  background: url("@/assets/img/analysis/pipeline_un.png") no-repeat center center;
  background-size: 100% 15px;
}

.pipe_con {
  width: 5%;
  height: 100%;
  text-align: center;
  background: url("@/assets/img/analysis/pipeline_two.png") no-repeat;
  background-size: 100% 50%;
  background-position: 50% 50%
}

.pipe_last {
  width: 152%;
  margin: 0 0 0 -20%;
  height: 12px;
  background: url("@/assets/img/analysis/pipeline_un.png") no-repeat;
  background-size: 100% 12px;
}

.pipe_last_arrow {
  background: url("@/assets/img/analysis/pipeline_arrow.png") no-repeat;
  width: 100%;
  height: 100%;
  mix-blend-mode: color-dodge;
  position: relative;
  left: 40px;
}

.pipeline-un-y {
  text-align: center;
  background: url("@/assets/img/analysis/pipeline_un_y.png") no-repeat;
  background-size: 100% 50%;
  background-position: 50% 50%
}

/* 밸브색상 */
.valve_on {
  width: 50%;
  height: 100%;
  text-align: center;
  background: url("@/assets/img/analysis/03_2_valve_active.png") no-repeat;
  background-position: 22% 38%;
  background-size: 65% 50%;
}

.valve_off {
  width: 50%;
  height: 100%;
  text-align: center;
  background: url("@/assets/img/analysis/03_2_valve_disable2.png") no-repeat;
  background-position: 22% 47%;
  background-size: 65% 50%;
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
