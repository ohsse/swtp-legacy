<template>
  <MainDataViewRotation :dataType="pwr" />
  <MainDataViewRotation :dataType="kwh" />
  <MainDataViewRotation :dataType="co2" />
</template>

<script>
import MainDataViewRotation from "@/views/DashBoard/DashBoard/MainSmallComponents/MainDataViewRotation.vue";
import RotationContentsClass from "../DashBoard/RotationContentsClass";
import { addCommaNumber } from '@/util/addCommaNumber';
import { fetchFunc } from '@/util/fetchFunc';
export default {
  components: {
    MainDataViewRotation,
  },
  data() {
    return {
      pwr: new RotationContentsClass('소비', '현황', 'blue_round', '전력소비', 0, 'kW', [], true),
      kwh: new RotationContentsClass('절감', '현황', 'green_round', '전력절감', 0, 'kW', []),
      co2: {
        subTitle: '탄소절감',
        subValue: 0,
        subUnit: 'kg',
        innerData: []
      },
    }
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
      const afterDate = new Date()
      afterDate.setDate(nowDate.getDate() - 1);
      const savingAfterDate = afterDate.toISOString().split('T')[0]
      const savingTodayDate = nowDate.toISOString().split('T')[0]
      const lastDate = (new Date(nowDate.getFullYear(), nowDate.getMonth() + 1, 0)).getDate()
      const afterDayLastDate = (new Date(afterDate.getFullYear(), afterDate.getMonth() + 1, 0)).getDate()

      //api 호출
      const values = await Promise.all([fetchFunc(`${apiURL}/es/selectNowElec`), fetchFunc(`${apiURL}/es/selectNowPeak`),
      fetchFunc(`${apiURL}/es/selectYMD`), fetchFunc(`${apiURL}/es/baseElec`), fetchFunc(`${apiURL}/es/rstSavingTargetSum`)])

      //api 호출 데이터 정리
      const selectNowElec = values[0].data[0]
      const selectNowPeak = values[1].data[0]
      const selectYMD = values[2].data[0]
      const baseElec = values[3].data
      const rstSavingTargetSum = values[4].data

      //금월 목표량
      const goalMonth = selectNowPeak[`month${nowDate.getMonth() + 1}`]
      //금일 목표량
      const goalDay = goalMonth / lastDate
      //전일 목표량
      const goalAfter = selectNowPeak[`month${afterDate.getMonth() + 1}`] / afterDayLastDate
      //금년 목표량
      const goalMonthArr = Object.values(selectNowPeak)
      const goalYear = goalMonthArr.reduce((accumulator, item) => {
        return accumulator + item;
      }, 0);
      //전일 절감량
      const afterSavingTarget = baseElec.find(item => item.date === savingAfterDate)
      //금일 절강럄
      const todaySavingTarget = baseElec.find(item => item.date === savingTodayDate)

      //금월 절감량
      let monthSavingCo2 = 0;
      let monthSavingKwh = 0;
      baseElec.forEach(item => {
        const targetMonth = new Date(item.date).getMonth() + 1
        if (targetMonth === nowDate.getMonth() + 1) {
          monthSavingCo2 += item.savingCo2
          monthSavingKwh += item.savingKwh
        }
      });
      //금년 절감량
      const yearSavingTarget = rstSavingTargetSum.find(item => Number(item.date) === nowDate.getFullYear());

      //컨텐츠 출력 텍스트 지정
      const innerTitle = ['금일', '금월', '금년', '전일'];
      let pwrVal = []
      let pwrSubVal = []

      //사용량
      pwrVal.push(addCommaNumber(selectYMD?.todayPwr))
      pwrVal.push(addCommaNumber(selectYMD?.monthPwr?.toFixed(0)))
      pwrVal.push(addCommaNumber(selectYMD?.yearPwr?.toFixed(0)))
      pwrVal.push(addCommaNumber(selectYMD?.afterPwr))

      //목표대비 백분율 (( 사용량 / 목표량 ) * 100)
      pwrSubVal.push(addCommaNumber((selectYMD?.todayPwr / goalDay) * 100))
      pwrSubVal.push(addCommaNumber((selectYMD?.monthPwr / goalMonth) * 100))
      pwrSubVal.push(addCommaNumber((selectYMD?.yearPwr / goalYear) * 100))
      pwrSubVal.push(addCommaNumber((selectYMD?.afterPwr / goalAfter) * 100))
      const pwrSubTitle = ['목표대비', '목표대비', '목표대비', '목표대비']
      this.pwr.subValue = addCommaNumber(selectNowElec?.nowPwi)
      this.pwr.innerData = this.twoRowRotation(innerTitle, pwrVal, 'kWh', pwrSubTitle, pwrSubVal, '%', 4)

      //절감량
      let kwhVal = []
      kwhVal.push(addCommaNumber(todaySavingTarget?.savingKwh))
      kwhVal.push(addCommaNumber(monthSavingKwh.toFixed(0)))
      kwhVal.push(addCommaNumber(yearSavingTarget?.savingKwh))
      kwhVal.push(addCommaNumber(afterSavingTarget?.savingKwh))
      this.kwh.innerData = this.oneRowRoataion(innerTitle, kwhVal, 'kWh', 4)


      //co2 절감량
      let co2Val = []
      co2Val.push(addCommaNumber(todaySavingTarget?.savingCo2))
      co2Val.push(addCommaNumber(monthSavingCo2))
      co2Val.push(addCommaNumber(yearSavingTarget?.savingCo2.replace(',', '')))
      co2Val.push(addCommaNumber(afterSavingTarget?.savingCo2))
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
}
</script>

<style scoped></style>