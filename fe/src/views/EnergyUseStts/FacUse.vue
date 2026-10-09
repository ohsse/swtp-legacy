'
<template>
  <!--설비별사용량 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <BigTitle :title="'설비별 사용량'" />
      <!-- 타이틀 끝 -->

      <!-- 본문 컨텐츠 시작 -->

      <div class="contents-container">

        <CalendarBox v-model="DayFrom" @chartData="chartData" dark />

        <b-row class="gx-4 mb-4">
          <!--상단 목록 리스트(시설현황, 설비목록) -->
          <topList ref="topList" @getGroupId="getGroupId" @getSubGroupId="getSubGroupId" />

          <!--설비 트렌드 그래프 컴포넌트  -->
          <topGrid ref="topGrid" />

        </b-row>
        <b-row style="height: 250px">
          <!--설비별 합계 그래프 -->
          <bottomleft ref="bottomLeft" v-bind:facName="this.facName" v-bind:trandY="this.trandY" />

          <!-- 분포 그래프 -->
          <bottomMid ref="bottomMid" />

          <!--순시 전력 그래프 -->
          <bottomRig ref="bottomRig" />

        </b-row>
      </div>
    </b-container>
  </div>
</template>

<script>
import CalendarBox from '@/components/ComponentCommon/CalendarBox.vue';
import topList from "@/views/EnergyUseStts/FacUse/FacUse_topList.vue"
import topGrid from "@/views/EnergyUseStts/FacUse/FacUse_topGrid.vue"
import bottomleft from "@/views/EnergyUseStts/FacUse/FacUse_bottomleft.vue"
import bottomMid from "@/views/EnergyUseStts/FacUse/FacUse_bottomMid.vue"
import bottomRig from "@/views/EnergyUseStts/FacUse/FacUSe_bottomRig.vue"
import dayjs from 'dayjs'
import { fetchFunc } from '@/util/fetchFunc';
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"
// import { max } from 'date-fns';


export default {
  layout: 'default',
  name: 'MemberInfo',
  components: {
    CalendarBox,
    topGrid,
    topList,
    bottomleft,
    bottomMid,
    bottomRig,
    BigTitle
  },
  data() {
    return {
      apiURL: this.$apiURL,
      calendarFlag: false,
      selected: 'time',
      range: {
        start: dayjs().format('YYYY-MM-DD'),
        end: dayjs().format('YYYY-MM-DD'),
      },
      dpFrom: '',
      dpTo: '',
      trandY: [],
      facName: [],
      DayFrom: '',
      sunsiX: [],
      lpData: [],
      mccData: [],
      sunsiData: [],
      mccX: [],
      dateFrom: null,
      dateTo: null,
    }
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
    if (this.getUrlParam() != 'null') {
      this.selectedZoneData(this.getUrlParam());
    } else {
      this.zoneData()
    }
  },

  methods: {

    async zoneData() {
      const apiURL = this.$apiURL;
      let data = await fetchFunc(
        `${apiURL}/st/selectZone?use_yn=1`
      );
      const items = [];

      data?.data?.forEach((item) => {
        items.push(item.zone_name);
      });

      this.$refs.topList.zoneData(items);
    },
    async selectedZoneData(selectedZone) {
      let selectedIndex = 0
      const apiURL = this.$apiURL;
      let data = await fetchFunc(
        `${apiURL}/st/selectZone?use_yn=1`
      );
      const items = [];

      data?.data?.forEach((item, index) => {
        items.push(item.zone_name);
        if (selectedZone === item.zone_name) {
          selectedIndex = index
          return;
        }
      });
      this.$refs.topList.zoneData(items, selectedIndex);
    },

    chartData(dateFrom, dateTo, selected) {

      this.dateFrom = dateFrom
      this.dateTo = dateTo
      this.selected = selected
      this.$refs.topList.groupToss();
    },
    async bottomRigChart(value) {
      const sunsiData = (await fetchFunc(`${this.$apiURL}/es/selectFacSunsi?start_date=${this.dateFrom}&end_date=${this.dateTo}&zone_code=${value}&time_type=${this.selected}`)).data;
      let facName = [];
      let chartDate = [];
      sunsiData?.forEach((item) => {
        //설비명 정리
        if (!facName.includes(item.fac_name)) {
          facName.push(item.fac_name)
        }
        //차트 x축 정리
        if (!chartDate.includes(item.x)) {
          chartDate.push(item.x)
        }
      })
      let chartY = []
      facName?.forEach((item) => {
        let array = [];
        sunsiData.forEach((data) => {
          if (data.fac_name == item) {
            array.push(data.y)
          }
        })
        chartY.push(array)
      })
      this.$refs.bottomRig.initChart(chartDate, chartY, facName)

    },
    async bottomChart(value) {
      let data = (await fetchFunc(
        `${this.$apiURL}/es/selectFacUseList_sum?start_date=${this.dateFrom}&end_date=${this.dateTo}&zone_code=${value}&time_type=${this.selected}`)).data;
      let botLeftDatas = [], botLeftLabels = [], botMidDatas = [];
      if (data?.length > 0) {
        data.forEach((item) => {
          const labelString = item.FAC_CODE
          let label
          label = labelString
          let donutData = {
            name: label,
            value: item.y
          }
          botLeftDatas.push(item.y)

          botLeftLabels.push(label)
          botMidDatas.push(donutData);
        })
        this.$refs.bottomLeft.initChart(botLeftDatas, botLeftLabels);
        this.$refs.bottomMid.createChart(botMidDatas);
      } else {
        this.$refs.bottomMid.createChart();
        this.$refs.bottomLeft.initChart();
      }
    },
    getGroupId(value) {//시설현황 이벤트dec 값 가져옴
      this.bottomRigChart(value);
      this.bottomChart(value);
    },
    async getSubGroupId(value) {//설비목록 이벤트pac값 가져옴
      const apiURL = this.$apiURL;
      let data = await fetchFunc(
        `${apiURL}/es/selectFacUseList?start_date=${this.dateFrom}&end_date=${this.dateTo}&fac_code=${value}&time_type=${this.selected}`
      );
      if (data.data?.length > 0) {
        let topGridDataX = new Array();
        let topGridDataY = new Array();
        data.data?.forEach((item) => {
          topGridDataX.push(item.x)
          topGridDataY.push(item.y)
        })

        this.$refs.topGrid.chartMake(topGridDataX, [topGridDataY], data.data[0].fac_code)
      } else {
        this.$refs.topGrid.chartMake()
      }

    },
    getUrlParam() {
      const queryString = window.location.search;
      const urlParams = new URLSearchParams(queryString);
      const selectedValue = urlParams.get('selected');

      return decodeURIComponent(selectedValue);
    }
  }
}




</script>



<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.ai-arrow-right {
  position: relative;
}

.ai-arrow-right::after {
  display: inline;
  content: '';
  width: 73px;
  height: 318px;
  position: absolute;
  top: 10%;
  right: -8%;
  background: url(@/assets/img/ai_arrow_right.png);
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  -webkit-animation: blink 3s linear infinite;
  -moz-animation: blink 3s linear infinite;
  animation: blink 3s linear infinite;
}

.date_design {
  background-color: #15284e;
  color: #fff;
  width: 130px;
  font-size: 13px;
  margin-left: 10px;
  font-family: KHNPHDRegular;
}
</style>
