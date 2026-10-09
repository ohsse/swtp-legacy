<template>
  <div>
    <div class="mx-5" style="display: block">
      <!-- 전력소비 & 전력절감-->
      <b-row>
        <b-col class="position-relative">
          <div class="position-absolute bottom-0 start-0 px-3" :style="{ width: '416px', top: '-4px !important' }">
            <!-- 소비 현황 시작 -->
            <MainDataViewRotation :dataType="pwr" />
            <!-- 소비 현황 끝 -->
            <!-- 절감 현황 시작 -->
            <MainDataViewRotation :dataType="kwh" />
            <MainDataViewRotation :dataType="co2" />
            <!-- 절감 현황 끝 -->
          </div>
        </b-col>
      </b-row>
      <!-- //전력소비 & 전력절감-->
      <!-- 3D MAP 영역 -->
      <b-row class="align-items-center" :style="{
        width: '85%',
        height: 'calc(100vh - 390px)',
        margin: '0 auto',
      }">
        <MapContents></MapContents>
      </b-row>
      <!-- //3D MAP 영역 -->
      <b-row class="row-cols-3 gx-3">
        <PumpRight></PumpRight>
        <MajorRight></MajorRight>
        <PeakRight></PeakRight>
      </b-row>
    </div>
  </div>
</template>

<script>
import MapContents from "@/views/DashBoard/DashBoard/MapContents.vue";
import PumpRight from "@/views/DashBoard/DashBoard/PumpRight.vue";
import MajorRight from "@/views/DashBoard/DashBoard/MajorRight.vue";
import PeakRight from "@/views/DashBoard/DashBoard/PeakRight.vue";
import MainDataViewRotation from "@/views/DashBoard/DashBoard/MainSmallComponents/MainDataViewRotation.vue";
import { addCommaNumber } from '@/util/addCommaNumber';
import { fetchFunc } from '@/util/fetchFunc';

export default {
  components: {
    MainDataViewRotation,
    MapContents,
    PeakRight,
    PumpRight,
    MajorRight,
  },
  data() {
    return {
      pwr: {
        title: '소비',
        title2: '현황',
        color: 'blue_round',
        subTitle: '전력소비',
        subValue: 0,
        subUnit: 'kW',
        innerData: [
          {
            sub: {}
          }
        ]
      },
      kwh: {
        title: '절감',
        title2: '현황',
        color: 'green_round',
        subTitle: '전력절감',
        subValue: 0,
        subUnit: 'kW',
        innerData: []
      },
      co2: {
        subTitle: '탄소절감',
        subValue: 0,
        subUnit: 'kg',
        innerData: []
      },
    };
  },
  mounted() {
    this.rotation();
    setInterval(() => {
      this.rotation();
    }, 1 * (1000 * 60));
  },
  methods: {
    async rotation() {
      const apiURL = this.$apiURL;
      const nowDate = new Date()
      const nowYear = nowDate.getFullYear();
      const nowMonth = nowDate.getMonth() + 1;
      const nowDay = nowDate.getDate() < 10 ? `0${nowDate.getDate()}` : nowDate.getDate()
      const afterDay = nowDate.getDate() - 1 < 10 ? `0${nowDate.getDate() - 1}` : nowDate.getDate() - 1
      const dateMonth = nowMonth < 10 ? `0${nowMonth}` : nowMonth;

      const savingAfterDate = `${nowYear}-${dateMonth}-${afterDay}`;
      const savingTodayDate = `${nowYear}-${dateMonth}-${nowDay}`;

      const lastDate = (new Date(nowDate.getFullYear(), nowMonth, 0)).getDate()

      const selectNowElec = (await fetchFunc(`${apiURL}/es/selectNowElec`)).data[0]
      const selectNowPeak = (await fetchFunc(`${apiURL}/es/selectNowPeak`)).data[0]
      const selectYMD = (await fetchFunc(`${apiURL}/es/selectYMD`)).data[0]
      const baseElec = (await fetchFunc(`${apiURL}/es/baseElec`)).data
      const rstSavingTargetSum = (await fetchFunc(`${apiURL}/es/rstSavingTargetSum`)).data

      const goalMonth = selectNowPeak[`month${nowMonth}`]
      const goalDay = goalMonth / lastDate
      const goalMonthArr = Object.values(selectNowPeak)
      const goalYear = goalMonthArr.reduce((accumulator, item) => {
        return accumulator + item;
      }, 0);


      const afterSavingTarget = baseElec.find(item => item.date === savingAfterDate)

      const todaySavingTarget = baseElec.find(item => item.date === savingTodayDate)
      let monthSavingCo2 = 0;
      let monthSavingKwh = 0;
      baseElec.forEach(item => {
        monthSavingCo2 += Number(item.savingCo2.replace(',', ''));
        monthSavingKwh += Number(item.savingKwh.replace(',', ''));
      });
      const yearSavingTarget = rstSavingTargetSum.find(item => Number(item.date) === nowYear);





      const innerTitle = ['금일', '금월', '금년', '전일'];
      let pwrVal = []
      let pwrSubVal = []
      pwrVal.push(addCommaNumber(selectYMD.todayPwr))
      pwrVal.push(addCommaNumber(selectYMD.monthPwr))
      pwrVal.push(addCommaNumber(selectYMD.yearPwr))
      pwrVal.push(addCommaNumber(selectYMD.afterPwr))
      pwrSubVal.push(addCommaNumber((selectYMD.todayPwr * 100) / goalDay))
      pwrSubVal.push(addCommaNumber((selectYMD.monthPwr * 100) / goalMonth))
      pwrSubVal.push(addCommaNumber((selectYMD.yearPwr * 100) / goalYear))
      pwrSubVal.push(addCommaNumber((selectYMD.afterPwr * 100) / goalDay))
      const pwrSubTitle = ['목표대비', '목표대비', '목표대비', '목표대비']
      this.pwr.subValue = addCommaNumber(selectNowElec?.nowPwi)
      this.pwr.innerData = this.twoRowRotation(innerTitle, pwrVal, 'kWh', pwrSubTitle, pwrSubVal, '%', 4)


      let kwhVal = []
      kwhVal.push(addCommaNumber(todaySavingTarget.savingKwh.replace(',', '')))
      kwhVal.push(addCommaNumber(monthSavingKwh))
      kwhVal.push(addCommaNumber(yearSavingTarget.savingKwh.replace(',', '')))
      kwhVal.push(addCommaNumber(afterSavingTarget.savingKwh.replace(',', '')))
      this.kwh.innerData = this.oneRowRoataion(innerTitle, kwhVal, 'kWh', 4)



      let co2Val = []
      co2Val.push(addCommaNumber(todaySavingTarget.savingCo2.replace(',', '')))
      co2Val.push(addCommaNumber(monthSavingCo2))
      co2Val.push(addCommaNumber(yearSavingTarget.savingCo2.replace(',', '')))
      co2Val.push(addCommaNumber(afterSavingTarget.savingCo2.replace(',', '')))
      this.co2.innerData = this.oneRowRoataion(innerTitle, co2Val, 'kg', 4)
    },
    /**
     * @param {List} title main 타이틀
     * @param {List} value main 값
     * @param {String} unit main 단위
     * @param {Number} cnt 갯수(반복문을 위한)
     */
    oneRowRoataion(title, value, unit, cnt) {
      let returnData = []
      for (let i = 0; i < cnt; i++) {
        let returnObj = {
          title: title[i],
          value: value[i],
          unit: unit,
        }
        returnData.push(returnObj)
      }
      return returnData
    },
    /**
     * @param {List} title main 타이틀
     * @param {List} value main 값
     * @param {String} unit main 단위
     * @param {List} subTitle sub 타이틀
     * @param {List} subValue sub 값
     * @param {String} subUnit sub 단위
     * @param {Number} cnt 갯수(반복문을 위한)
     */
    twoRowRotation(title, value, unit, subTitle, subValue, subUnit, cnt) {
      let returnData = []
      for (let i = 0; i < cnt; i++) {
        let returnObj = {
          title: title[i],
          value: value[i],
          unit: unit,
          sub: {
            title: subTitle[i],
            value: subValue[i],
            unit: subUnit
          }
        }
        returnData.push(returnObj)
      }
      return returnData
    }
  }
};
</script>

<style></style>
