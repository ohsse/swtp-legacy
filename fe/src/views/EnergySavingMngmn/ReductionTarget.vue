
<template>
  <!--절감목표 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <div class="container-fluid">
      <!-- 타이틀 시작 -->
      <BigTitle :title="'절감목표 달성 현황'" />
      <!-- 타이틀 끝 -->
      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container">
        <top ref="top" :item="topData"></top>
        <b-row>
          <b-col>
            <b-row>
              <useMn ref="useMn" :title="useMnTargetTitle" />
              <targetRed ref="targetRed" :item="nowVal" :title="targetRedTitle" />
              <botChart ref="botChart" />
            </b-row>
          </b-col>
        </b-row>
      </div>
      <!-- 본문 컨텐츠 끝 -->
    </div>
  </div>
</template>

<script>
import top from "@/views/EnergySavingMngmn/Reduction/ReductionTarget_top.vue"
import useMn from "@/views/EnergySavingMngmn/Reduction/ReductionTarget_useMn.vue";
import targetRed from "@/views/EnergySavingMngmn/Reduction/ReductionTarget_targetRed.vue";
import botChart from "@/views/EnergySavingMngmn/Reduction/ReductionTarget_bottomRight.vue"
import { fetchFunc } from "@/util/fetchFunc";
import { addCommaNumber } from "@/util/addCommaNumber";
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"
export default {
  components: {
    top,
    useMn,
    targetRed,
    botChart,
    BigTitle
  },
  data() {
    return {
      fetchData: new Object(),
      nowVal: {
        useVal: 0,
        targetVal: 0
      },
      topData: new Array(),
      useMnTargetTitle: "금월 목표대비 사용량",
      targetRedTitle: "목표대비 탄소 절감량"
    }
  },
  mounted() {
    this.getData()

  },
  methods: {
    async getData() {
      const nowDate = new Date();

      //연도 (추후에 23년 데이터 들어올시 -1 제거 바람)
      const nowYear = nowDate.getFullYear();
      const usageData = (await this.getFetchData(nowYear, "st/getUsageData")).data


      const goalData = (await this.getFetchData(nowYear, "st/getGoalData")).data[0]



      //목표데이터랑 형식 맞추기..
      let usageObj = new Object();
      usageData.forEach((item) => {
        usageObj[item.month] = item.value;
      });

      //목표데이터 사용량데이터 병합
      const mergeData = Object.assign(usageObj, goalData);


      let topData = new Array();
      let month = new Array();
      let useData = new Array();
      let targetData = new Array();
      for (let i = 1; i <= 12; i++) {
        const obj = {
          month: i,
          useVal: addCommaNumber(parseFloat(this.toFixedCheck(mergeData[i]))),
          targetVal: addCommaNumber(parseFloat(this.toFixedCheck(mergeData[i + 'M']))),
          persent: addCommaNumber(parseFloat(this.toFixedCheck(mergeData[i] / mergeData[i + 'M'] * 100)))
        }

        month.push(i + '월')
        useData.push(mergeData[i])
        targetData.push(mergeData[i + 'M'])
        topData.push(obj)
      }


      //금월 값
      const nowMonth = nowDate.getMonth() + 1;
      //금월 목표량
      let targetVal = mergeData[nowMonth + 'M']


      let useVal = (mergeData[nowMonth])
      let use_co2 = (useVal * 0.4663);
      let goal_co2 = (targetVal * 0.4663);
      let goalVSco2 = (goal_co2 - use_co2);


      this.$refs.top.getTopData(topData);
      this.$refs.botChart.makeChart(month, [useData, targetData])
      this.$refs.useMn.percentMake(useVal, targetVal)
      this.$refs.targetRed.makeTargetRed(addCommaNumber(useVal), addCommaNumber(targetVal), addCommaNumber(this.toFixedCheck(use_co2)), addCommaNumber(this.toFixedCheck(goalVSco2)))
    },
    /**
     * 
     * @param {Number} year 조회 연도
     * @param {String} url api 주소
     */
    async getFetchData(year, url) {
      const apiURL = this.$apiURL;

      let res = await fetchFunc(`${apiURL}/${url}?year=${year}`)

      return res;
    },
    toFixedCheck(value) {
      // if (value !== 0 && value != null && value !== undefined && !isNaN(value)) {
      //   return value.toFixed(1)
      // } else if (!value.toString().includes('.')) {
      //   return value;
      // } else {
      //   return 0;
      // }
      return value
    }
  }
};
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.div-new {
  background-image: url(/src/assets/img/div_new.png);
  background-size: 100% 100%;
  display: inline-block;
}

.title_show {
  background-image: url(/src/assets/img/dot_road.png);
  background-size: 100% 35%;
  background-repeat: no-repeat;
  background-position: center;
}

.month {
  color: white;
  height: 20px;
  display: inline-block;
  font-weight: bolder;
  font-size: 18px;
}

.showwant {
  background-image: url(/src/assets/img/soure_pump.png);
  height: 120px;
  background-repeat: no-repeat;
  background-size: 100% 100%;
}

.month_left {
  float: left;
  width: 67%;
  height: 50%;
}

.row1 {
  height: 100%;
  display: flex;
  align-items: center;
}

.posif {
  width: 29%;
  color: skyblue;
  display: inline-block;
  margin: 0px 0px 0px 10px;
  font-weight: bolder;
}

.bottom_middle_val {
  text-shadow: 0 0 9px #5cafff;
  font-size: 19px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  letter-spacing: normal;
  color: #fff;
  font-family: 'LAB디지털';
  text-align: right;
}

.month_right {
  float: left;
  width: 28%;
  height: 85%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.persent {
  color: white;
  font-size: 20px;
  font-weight: bolder;
}

.table_s {
  background-image: url(/src/assets/img/table_s.png);
  background-size: 100% 100%;
  height: 450px;
  width: 30.5%;
  margin: 5px 5px 0 0;
  padding: 0 10px 10px 10px;
  position: relative;
}

.table_s:last-child {
  margin-right: 0;
}

.bottom_title {
  width: 100%;
  height: 26%;
  font-size: 174%;
  color: white;
  text-align: center;
  line-height: 114px;
  font-family: 'KHNPHDRegular';
}

.bottom_bar {
  width: 3%;
  height: 45%;
  float: left;
  background: url(/src/assets/img/image_01.png);
  background-repeat: no-repeat;
}

.bottom_middle_gauge {
  width: 310px;
  opacity: 0.5;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  position: absolute;
}

.pie_chart1 {
  width: 305px;
  height: 305px;
  transition: 0.3s;
  display: block;
  position: absolute;
  top: 100%;
  border-radius: 50%;
  line-height: 200px;
  font-size: 30px;
  transform: translate(-50%, -50%) rotate(0deg);
  z-index: 1;
  left: 50%;
  background: linear-gradient(to top, rgba(72, 156, 242, 0.5) 50%, rgba(0, 0, 0, 1) 50%);
}

.bottom_middle_area {
  width: 100%;
  height: 110px;
  position: relative;
  top: 28px;
}

.bottom_cir {
  background: #173770;
  display: block;
  position: absolute;
  top: 87%;
  left: 50%;
  width: 156px;
  height: 80px;
  border-radius: 150px 150px 0 0;
  text-align: center;
  line-height: 200px;
  font-size: 30px;
  transform: translate(-50%, -50%);
  z-index: 1;
}

.bottom_val {
  width: 98%;
  color: white;
  font-size: 44px;
  text-align: center;
  z-index: 1;
  position: absolute;
  font-family: 'LAB디지털';
}

.bottom_line_val {
  width: 96%;
  position: absolute;
  bottom: 28px;
}

table.bottom_row1 td {
  padding: 7px 0;
}

.div-new {
  background-image: url(/src/assets/img/div_new.png);
  background-size: 100% 100%;
  height: 450px;
  width: 30.5%;
  margin: 5px 5px 0 0;
  padding: 0 10px 10px 10px;
  position: relative;
}

.bottom_col1 {
  text-shadow: 0 0 9px #5cafff;
  font-size: 19px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  letter-spacing: normal;
  color: #c3eaff;
  text-align: left;
  font-family: 'KHNPHUotfR';
  display: flex;
  align-items: flex-end;
}

.table_unit {
  font-size: 16px;
  color: #a4ceed;
  font-family: 'KHNPHDRegular';
  padding-left: 14px !important;
}
</style>
