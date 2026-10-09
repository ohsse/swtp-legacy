<template>
  <!--송수펌프 제어 분석 트렌드 컴포넌트의 템플릿 부분 -->
  <LoadingSpinner class="loading-container" v-if="isLoading" />
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <BigTitle :title="'송수펌프 제어 트렌드'" />
      <!-- 타이틀 끝 -->
      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container">
        <select-box ref="selectBox" @selectDate="selectDate" />
        <b-row>
          <b-col xl="7" :style="{ height: '900px', overflowY: 'scroll' }">
            <area-chart v-for="item in areaChartData" :key="item" :areaChartData="item" :style="{ height: '16.6%' }" />
            <AreaChart ref="AreaChartForPri" :style="{ height: '330px', width: '1000px' }" />
            <OperationTrend ref="Trand" :style="{ height: '330px', width: '100%' }" />
          </b-col>
          <InstantaneousData :isTrand="true" :sunsi="sunsi" :info="info" :sunsiTitle="sunsiTitle"
            topTitle="주요 인자 순시값" />
        </b-row>
      </div>
    </b-container>
  </div>
</template>

<script>
import selectBox from "./PumpControlTrand/SelectBox.vue";
import InstantaneousData from "@/components/ComponentCommon/InstantaneousData.vue";
import AreaChart from "@/components/Chart/AreaChart.vue";
import ChartClass from "@/components/Chart/ChartClass";
import LoadingSpinner from "@/components/ComponentCommon/LoadingSpinner.vue";
import OperationTrend from "@/views/Report/DailyReport/DailyReport_OperationTrend.vue";
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"
export default {
  data() {
    return {
      tankList: [],
      from: "",
      to: "",
      selected: "",
      tankNum: "",
      areaChartData: [],
      sunsi: [],
      sunsiTitle: [],
      info: undefined,
      isLoading: false,
      pwmData: {},
      sunsiName: [],
    };
  },
  components: {
    selectBox,
    InstantaneousData,
    AreaChart,
    LoadingSpinner,
    OperationTrend,
    BigTitle
  },
  mounted() {
    this.$emit("onChangeBgClass", true);
    this.selectTankList();
  },
  methods: {
    selectDate(dateFrom, dateTo, selected, tankNum) {
      this.isLoading = true;
      this.from = dateFrom;
      this.to = dateTo;
      this.selected = selected;
      this.tankNum = tankNum;
      this.getGridData();
    },
    async selectTankList() {
      const apiURL = this.$apiURL;
      let res = await fetch(
        //TODO: 여기 이부분 확인하기!!! tnk_typ=1 맞는건가
        `${apiURL}/ai/selectTankList?tnk_typ=1`
      );
      let data = await res.json();
      this.tankList.push(data.data);
      this.$refs.selectBox.tankList(this.tankList);
    },
    async getGridData() {
      const apiURL = this.$apiURL;
      let res2 = await fetch(
        `${apiURL}/ai/selectWpTnkTagRangeList?tnk_grp_idx=${this.tankNum}&time_type=${this.selected}&start_date=${this.from}&end_date=${this.to}`
        // `${apiURL}/ai/selectWpTnkTagRangeList?tnk_grp_idx=3&start_date=2023-11-15&end_date=2023-11-16&time_type=h`
      );
      let data2 = await res2.json();
      let res3 = await fetch(`${apiURL}/es/selectPumpPerformList?start_date=${this.from}&end_date=${this.to}&time_type=${this.selected}`)
      // let res3 = await fetch(`${apiURL}/es/selectPumpPerformList?start_date=2023-11-15&end_date=2023-11-16&time_type=h`)
      let data3 = await res3.json();
      this.pwmData = data3.data

      for (let key in data2.data) {
        if (data2.data[key] && data2.data[key].length === 0) {
          delete data2.data[key];
        }
      }

      const pmbNames = [];
      const pmbXData = [];
      const pmbYData = [];
      this.pwmData?.PMB_TAG?.forEach((element) => {
        if (!pmbNames.includes(element.name)) {
          pmbNames.push(element.name);
        }

        if (!pmbXData.includes(element.ts)) {
          pmbXData.push(element.ts);
        }
      });

      pmbNames.forEach((element) => {
        let data = [];
        let useVal = [];
        this.pwmData?.PMB_TAG?.forEach((item) => {
          if (item.name == element) {
            if (Number(item.value) > 0) {
              useVal.push(item);
            }
            data.push(Number(item.value));
          }
        });
        pmbYData.push(data);
      });

      const priNames = [];
      const priXData = [];
      const priYData = [];
      this.pwmData?.PRI_TAG?.forEach((element) => {
        if (!priNames.includes(element.name)) {
          priNames.push(element.name);
        }

        if (!priXData.includes(element.ts)) {
          priXData.push(element.ts);
        }
      });

      priNames.forEach((element) => {
        let data = [];
        let useVal = [];
        this.pwmData?.PRI_TAG?.forEach((item) => {
          if (item.name == element) {
            if (Number(item.value) > 0) {
              useVal.push(item);
            }
            data.push(Number(item.value));
          }
        });

        priYData.push(data);
      });

      let chartClassForPri = new ChartClass(priXData, priYData, priNames, false, '날짜', '펌프 토출압력 (m)')
      chartClassForPri.setNameGap();
      chartClassForPri.legendOption('scroll', 'vertical', true, 'right', 0, '10%', 'auto')
      chartClassForPri.setGridSize('3%', '15%', '13%', 10, true)

      if (this.$refs.Trand) {
        this.$refs.Trand.initChart(pmbXData, pmbNames, pmbYData, this.selected, '펌프 가동이력');
      }
      if (this.$refs.AreaChartForPri) {
        this.$refs.AreaChartForPri.changeData(chartClassForPri);
      }
      if (data2.data) {
        this.sunsiTitle = Object.keys(data2?.data);
        this.info = data2?.data.info;
      }
      this.sunsiTitle?.forEach(item => {
        let flag = 0
        this.info?.forEach(element => {
          if (flag == 0) {
            if (item == element.TAG_NAME) {
              this.sunsiName.push(element.TAG_DCS)
              flag++;
            }
          }
        })
      })
      if (data2 !== null) {
        this.isLoading = false;
        let allData = [];
        let lastData = [];
        for (let index = 0; index < this.sunsiTitle.length; index++) {
          if (this.sunsiTitle[index] !== "info") {
            let dataX = [];
            let dataY = [];
            data2.data[this.sunsiTitle[index]]?.forEach((element) => {
              dataX.push(element.ts);
              dataY.push(element.value.replace(",", ""));
            });
            let chartClass = new ChartClass(
              dataX,
              [dataY],
              [this.sunsiName[index]],
              undefined,
              '날짜',
              "m"
            )
            chartClass.setNameGap()
            allData.push(
              chartClass
            );
            lastData.push(dataY[dataY.length - 1]);
          }
        }

        this.areaChartData = allData;
        this.sunsi = lastData;
      }
    },
  },
};
</script>

<style scoped>
.pumpLoading {
  margin-top: 350px;
}

/* 컴포넌트에만 적용되는 스타일 정의 */
.textinput {
  padding: 0px 10px;
  height: 30px;
  width: 150px;
  display: inline-block;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  font-family: LABDigital;
  font-size: 18px;
  text-align: right;
  letter-spacing: 4px;
  border-radius: 5px;
}

.search_btn_font {
  font-size: 14px;
  letter-spacing: normal;
  color: #fff;
  font-family: KHNPHDRegular;
  text-align: center;
}

.search_btn {
  height: 29px;
  width: 62px;
  align-self: center;
  border: solid 1px #b4dffa;
  background-color: rgba(139, 194, 240, 0.25);
  cursor: pointer;
  border-radius: 4px;
  align-items: center;
  justify-content: center;
  display: flex;
}

.spend_co1 {
  text-shadow: 0 0 9px #5cafff;
  font-size: 18px;
  font-family: KHNPHDRegular;
  letter-spacing: normal;
  color: #c3eaff;
  align-self: center;
}

.spend_value {
  width: 15%;
  font-family: "LAB디지털";
  font-size: 20px;
  text-align: right;
}

.spend_unit {
  width: 10%;
  margin-left: 10px;
  padding-right: 20px;
  text-align: left;
  text-shadow: 0 0 9px #5cafff;
  color: #c3eaff;
}

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

.form-select {
  border-color: #489cf2;
  background: #15284e url(@/assets/img/select_btn.png) center right no-repeat;
}

.date-select {
  border-color: #489cf2;
  background: #15284e url(@/assets/img/select_calendar_btn.png) center right no-repeat;
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
