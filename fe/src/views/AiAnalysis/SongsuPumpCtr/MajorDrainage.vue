
<template>
  <!--송수펌프 제어 분석 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <b-row>
        <b-col class="title_wrap">
          <BigTitle :title="'주요 배수지 수위 현황'" />
        </b-col>
      </b-row>
      <!-- 타이틀 끝 -->


      <!-- 본문 컨텐츠 시작 -->


      <div class="contents-container" style="display: block;">

        <b-row class="row-col-2 justify-content-center">

          <!-- 캘린더 및 조회 -->
          <b-col xl="12" style="height: 30px; margin-top: 30px; display: flex; justify-content: flex-end;">
            <OneCalendarBox @setDate="getDate" />
          </b-col>

          <!-- 콘텐츠 영역 -->
          <b-row>
            <b-col xl="2" style="height: 900px;" class="p-2">
              <SmallTitle :title="'배수지 현황'" />
              <LeftListVue ref="leftList" @selectItem="selectItem" />
            </b-col>
            <b-col xl="1" style="height: 700px; " class="p-2">
              <div class="blinking" style="width: 70%; height: 40%; float: left; margin-top: 180px;"></div>
            </b-col>
            <b-col xl="9" style="height: 700px;">

              <!-- 수위 트렌드, 배수지별 수위 분포, 배수지별 수위 순시 영역 -->
              <b-row>
                <b-col xl="8" style="height: 350px;" class="p-2 plate_img">
                  <SmallTitle :title="'수위 트렌드'" />
                  <TrandChart ref="trandChart" />
                </b-col>

                <b-col xl="4" style="height: 350px;" class="p-2 plate_img">
                  <SmallTitle :title="'배수지별 수위 분포'" />
                  <MajorPieChart ref="pie" style="height: 300px; display: flex;" />
                </b-col>


                <b-col xl="12" style="height: 530px;" class="p-2 plate_img">
                  <SmallTitle :title="'배수지별 수위 순시'" />
                  <BottomCardVue ref="botCard" />
                </b-col>
              </b-row>
            </b-col>
          </b-row>
        </b-row>

      </div>

    </b-container>



    <!-- <grid></grid>
    <optionVue></optionVue>
    <roundGrid></roundGrid>
    <waterLevelGrid></waterLevelGrid> -->
  </div>
</template>

<script>
import BigTitle from '@/components/ComponentCommon/BigTitle.vue';
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
import OneCalendarBox from '@/components/ComponentCommon/OneCalendarBox.vue';
import LeftListVue from './MajorDrainageComponents/LeftList.vue';
import BottomCardVue from './MajorDrainageComponents/BottomCard.vue';
import TrandChart from './MajorDrainageComponents/TrandChart.vue';
import MajorPieChart from './MajorDrainageComponents/MajorPieChart.vue';
import { fetchFunc } from '@/util/fetchFunc';
export default {
  components: {
    BigTitle,
    SmallTitle,
    OneCalendarBox,
    LeftListVue,
    BottomCardVue,
    TrandChart,
    MajorPieChart
    // grid,
    // optionVue,
    // roundGrid,
    // waterLevelGrid
  },
  data() {
    return {
      trandChartData: {
        fac_name: [],
        xData: [],
        yData: {}
      },
      selectFac: null
    }
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
    this.setList()
  },
  methods: {
    async setList() {
      const apiURL = this.$apiURL;
      const tankList = (await fetchFunc(`${apiURL}/ai/selectTankList?tnk_typ=1`)).data
      this.$refs.leftList.setList(tankList)
    },
    async getDate(date) {
      const apiURL = this.$apiURL;
      const tankData = (await fetchFunc(`${apiURL}/ai/selectTankDataHourList?TNK_TYP=1&date=${date}`)).data
      this.$refs.botCard.setData(tankData.tank_instn)

      const trandFacName = []
      const trandXData = []
      const trandYData = {}
      const trandPieDate = [];

      tankData.hour_list.forEach(element => {
        if (!trandFacName.includes(element.TNK_GRP_NM)) {
          trandFacName.push(element.TNK_GRP_NM)
        }

        if (!trandXData.includes(element.ts)) {
          trandXData.push(element.ts)
        }
      });

      trandFacName.forEach(element => {
        let data = [];
        tankData.hour_list.forEach((item) => {
          if (item.TNK_GRP_NM == element) {
            data.push(item.value)
          }
        })
        trandYData[element] = data;
      })

      tankData.sum_list.forEach(element => {
        trandPieDate.push({
          // name: element.TNK_GRP_NM + element.TNK_idx,
          name: element.TNK_GRP_NM,
          value: element.value
        })
      })


      this.trandChartData.fac_name = trandFacName;
      this.trandChartData.xData = trandXData;
      this.trandChartData.yData = trandYData;
      this.$refs.pie.createChart(trandPieDate);
      this.$refs.trandChart.setChartData(this.trandChartData)
    },
    async selectItem(item) {
      this.selectFac = item
      this.$refs.trandChart.selectFac(item)

    }
  }
};

</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.bottom_all1 {
  font-size: 20px;
  color: #fff;
  font-family: 'KHNPHDRegular';
  line-height: 100%;
}

.measure_font {
  font-size: 22px;
  font-family: LAB디지털;
  color: #fff;
}

.bottom_all2 {
  font-size: 18px;
  font-family: 'KHNPHDRegular';
  letter-spacing: normal;
  color: #c3eaff;
  font-weight: lighter;
  text-align: left;
}
</style>
