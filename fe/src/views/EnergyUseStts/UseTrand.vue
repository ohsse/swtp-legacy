<template>
  <LoadingSpinner class="loading-container" v-if="isLoading"></LoadingSpinner>
  <div class="container-fluid">
    <BigTitle :title="'사용량 트렌드'" />

    <div class="contents-container">

      <b-row class="top-row-style">

        <b-col xl="7" class="plate_img" style="margin-right: 10px;">
          <SmallTitle :title="'전력 사용량'" />
          <div class="box_bt_area">
            <CalendarBox @chartData="chartData" :noMount="true" />
          </div>
          <UseTrand_topLeft ref="UseTrand_topLeft" :noMount="true" />
        </b-col>

        <b-col xl="5" class="plate_img">
          <SmallTitle :title="'최대 피크 현황'" />
          <UseTrand_topRig ref="UseTrand_topRig" />
        </b-col>

      </b-row>

      <b-row class="bottom-row-style">
        <UseTrand_bottom ref="UseTrand_bottomLeft" :time="'금일'" />
        <UseTrand_bottom ref="UseTrand_bottomMid" :time="'금월'" />
        <UseTrand_bottom ref="UseTrand_bottomRig" :time="'금년'" />
      </b-row>

    </div>
  </div>
</template>

<script>
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
import CalendarBox from '@/components/ComponentCommon/CalendarBox.vue';
import UseTrand_bottom from './UseTrand/UseTrand_bottom.vue';
import UseTrand_topLeft from './UseTrand/UseTrand_topLeft.vue';
import UseTrand_topRig from './UseTrand/UseTrand_topRig.vue';
import LoadingSpinner from '@/components/ComponentCommon/LoadingSpinner.vue';
import { fetchFunc } from '@/util/fetchFunc.js'
import Swal from 'sweetalert2'
export default {
  components: {
    BigTitle,
    SmallTitle,
    CalendarBox,
    UseTrand_bottom,
    UseTrand_topLeft,
    UseTrand_topRig,
    LoadingSpinner,
  },
  data() {
    return {
      apiURL: this.$apiURL,
      isLoading: false,
      data1: '',
      data2: '',
      data3: '',
      initFlag: true,
    }
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
  },
  created() {
    const now = new Date();
    const DayFrom = new Date(now.setDate(now.getDate()));
    const DayTo = new Date(now.setDate(now.getDate() + 1));
    let dateFrom = this.formattedDate(DayFrom);
    let dateTo = this.formattedDate(DayTo);
    this.initData(dateFrom, dateTo, "h");
  },
  updated() {

  },
  methods: {
    async initData(dateFrom, dateTo, selected) {
      this.isLoading = true;

      const requests = [
        fetchFunc(`${this.apiURL}/ai/selectUseTrandRangeCostList?start_date=${dateFrom}&end_date=${dateTo}&time_type=${selected}`),
        fetchFunc(`${this.apiURL}/ai/selectUseTrandList?start_date=${dateFrom}&end_date=${dateTo}&time_type=${selected}`),
        fetchFunc(`${this.apiURL}/ai/peakMax`)
      ]
      try {
        const responses = await Promise.allSettled(requests);
        this.data1 = responses[0].status === 'fulfilled' ? await responses[0].value : null;
        this.data2 = responses[1].status === 'fulfilled' ? await responses[1].value : null;
        this.data3 = responses[2].status === 'fulfilled' ? await responses[2].value : null;

      } catch (error) {
        Swal.fire({
          animation : false,
          text: 'No Data',
        });
      }
      this.isLoading = false
      
      await this.setBottomComponentData();
      await this.setTopComponentData();
      
    },

    async getData(dateFrom, dateTo, selected) {
      this.isLoading = true;
      const requests = [
        fetchFunc(`${this.apiURL}/ai/selectUseTrandList?start_date=${dateFrom}&end_date=${dateTo}&time_type=${selected}`)
      ];

      try {
        const responses = await Promise.all(requests);
        this.data1 = await responses[0];

      } catch (error) {
        Swal.fire({
          animation : false,
          text: 'No Data',
        });
      }
      this.isLoading = false
      this.$refs.UseTrand_topLeft.createChart(this.data1.data)
    },
    chartData(dateFrom, dateTo, selected) {
      this.getData(dateFrom, dateTo, selected);
    },
    formattedDate(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    },
    updateData() {
      this.$refs.UseTrand_bottomLeft.settingData(this.data1.data, 'day')
      this.$refs.UseTrand_bottomMid.settingData(this.data1.data, 'month')
      this.$refs.UseTrand_bottomRig.settingData(this.data1.data, 'year')
    },
    async setBottomComponentData() {
      
      await this.$refs.UseTrand_bottomLeft.settingData(this.data1.data, 'day');
      await this.$refs.UseTrand_bottomMid.settingData(this.data1.data, 'month');
      await this.$refs.UseTrand_bottomRig.settingData(this.data1.data, 'year');
      
    },
    async setTopComponentData() {
     
      await this.$refs.UseTrand_topLeft.createChart(this.data2.data);
      await this.$refs.UseTrand_topRig.createChart(this.data2.data);
      
    }
  },
  emits: ['onChangeBgClass']
};



</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */

/* -----Content Start Position----- */
.contents-container {
  height: 93%;
  width: 100%;
}

/* -----Row Style----- */
.top-row-style {
  padding: 0 10px 10px 10px;
  margin-bottom: 10px;
  flex-flow: row;
  height: calc(55% - 10px);
  width: calc(100% - 20px);
}

.bottom-row-style {
  padding: 0 10px 10px 10px;
  margin-top: 10px;
  flex-flow: row;
  height: calc(45% - 10px);
  width: calc(100% - 20px);
}

/* -----Font Setting----- */

.text-align-right {
  text-align: right;
  padding-right: 24px;
}

.button {
  width: 60px;
  height: 30px;
  border: solid 1px #b4dffa;
  background-color: rgba(139, 194, 240, 0.25);
  cursor: pointer;
  border-radius: 4px;
  font-family: 'KHNPHDRegular';
  font-size: 16px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  letter-spacing: normal;
  text-align: center;
  color: #fff;

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
