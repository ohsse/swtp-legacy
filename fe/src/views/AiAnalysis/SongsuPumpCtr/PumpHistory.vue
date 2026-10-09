<template>
  <!--송수펌프 가동이력 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <b-row>
        <b-col class="title_wrap">
          <BigTitle :title="'송수펌프 가동이력'" />
        </b-col>
      </b-row>
      <!-- 타이틀 끝 -->

      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container ">
        <CalendarBox @chartData="chartData" :excelDown="true" @excelDown="excelDown" />
        <Top ref="top" />
        <b-row cols="2" style="height: 440px; margin-top: 10px; margin-left: -30px; margin-right: 10px;">
          <b-col xl="6">
            <SmallTitle :title="reSmallTitle" />
            <HistoryAreaChart :style="chartHeight" ref="pwiChart" />
            <SmallTitle :title="spiSmallTitle" v-show="spiData" />
            <HistoryAreaChart :style="chartHeight" ref="spiChart" v-show="spiData" />

          </b-col>
          <b-col xl="6" :style="heatMapHeight">
            <SmallTitle :title="'송수펌프 가동이력'" style="margin-bottom: 20px;" />
            <HistoryBottomRight ref="botRight" />
          </b-col>
        </b-row>
      </div>
    </b-container>

  </div>
</template>

<script>
import BigTitle from '@/components/ComponentCommon/BigTitle.vue';
import CalendarBox from '@/components/ComponentCommon/CalendarBox.vue';
import Top from './PumpHistory/PumpHistoryTop.vue';
import HistoryAreaChart from './PumpHistory/HistoryAreaChart.vue';
import { fetchFunc } from '@/util/fetchFunc';
import { addCommaNumber } from '@/util/addCommaNumber';
import HistoryBottomRight from './PumpHistory/HistoryBottomRight.vue';
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
export default {
  components: {
    BigTitle,
    SmallTitle,
    CalendarBox,
    Top,
    HistoryAreaChart,
    HistoryBottomRight
  },
  data() {
    return {
      dateFrom: null,
      dateTo: null,
      selected: 'time',
      spiData: false,
      chartHeight: {
        height: '340px;'
      },
      chartLoad: false,
      reSmallTitle: '송수펌프 전력',
      spiSmallTitle: '',
      heatMapHeight: {
        'height': '440px'
      }
    }
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
  },
  methods: {
    chartData(dateFrom, dateTo, selected) {
      this.dateFrom = dateFrom
      this.dateTo = dateTo
      this.selected = selected
      this.getData()
    },
    async getData() {
      const apiURL = this.$apiURL;
      const pumpData = (await fetchFunc(`${apiURL}/es/selectPumpPerformList?start_date=${this.dateFrom}&end_date=${this.dateTo}&time_type=${this.selected}`)).data
      const boxData = (await fetchFunc(`${apiURL}/ai/selectPumpList`)).data
      // ========================= [수정된 부분 시작] =========================

      // PWI_TAG 배열에서 중복되지 않는 ts 값들의 개수를 계산합니다.
      const uniquePwiTs = [...new Set(pumpData?.PWI_TAG.map(item => item.ts))];
      const uniquePwiTsCount = uniquePwiTs.length;
      
      // 개수가 6개를 초과하면 6으로, 그렇지 않으면 실제 개수를 사용합니다.
      const xAxisCount = Math.min(uniquePwiTsCount, 6);
      

      // ========================= [수정된 부분 끝] =========================

      const pwmNames = []
      const pwmXData = []
      const pwmYData = []
      const pwmPer = {}
      // 중복 제거를 위해 Set을 사용
      const uniquePumpGrpNmSet = new Set(boxData.map(item => item.PUMP_GRP_NM));

      // Set을 배열로 변환
      const uniquePumpGrpNmArray = Array.from(uniquePumpGrpNmSet);
      const boxArr = []
      uniquePumpGrpNmArray.forEach(uniqueValue => {
        // boxData 배열에서 PUMP_GRP_NM이 uniqueValue와 일치하는 요소들을 필터링하여 새로운 배열을 생성
        const filteredArray = boxData.filter(item => item.PUMP_GRP_NM === uniqueValue);

        // boxArr 배열에 필터링된 배열을 추가
        boxArr.push(filteredArray);
      });

      // boxData.splice(boxData.length)
      this.$refs.top.setData(boxArr, pwmPer)
      if (pumpData?.SPI_TAG.length > 0) {
        this.spiData = true
      }
      pumpData?.PMB_TAG.forEach(element => {
        if (!pwmNames.includes(element.name)) {
          pwmNames.push(element.name)
        }

        if (!pwmXData.includes(element.ts)) {
          pwmXData.push(element.ts)
        }
      });

      pwmNames.forEach(element => {
        let data = []
        let useVal = []
        pumpData?.PMB_TAG.forEach((item) => {
          if (item.name == element) {
            if (Number(item.value) > 0) {
              useVal.push(item);
            }
            data.push(Number(item.value))
          }
        })

        pwmYData.push(data)
        pwmPer[element] = addCommaNumber((useVal.length / data.length) * 100)
      })

      this.$refs.botRight.initChart(pwmXData, pwmNames, pwmYData, this.selected, xAxisCount)



      const pwiNames = []
      const pwiXData = []
      const pwiYData = []
      pumpData?.PWI_TAG.forEach(element => {
        if (!pwiNames.includes(element.name)) {
          pwiNames.push(element.name)
        }

        if (!pwiXData.includes(element.ts)) {
          pwiXData.push(element.ts)
        }
      });

      pwiNames.forEach(element => {
        let data = []
        pumpData?.PWI_TAG.forEach((item) => {
          if (item.name == element) {
            data.push(Number(item.value))
          }
        })

        pwiYData.push(data)
      })
      let plusHeight = 0;
      let chartHeight = 440;
      if (boxArr.length == 1) {
        plusHeight = 100;
        chartHeight = 440 + (plusHeight * 2)
        this.heatMapHeight.height = '640px'
      }


      this.chartHeight.height = chartHeight + "px"
      this.chartHeight['padding-top'] = '15px'

      if (pumpData?.SPI_TAG.length > 0) {
        this.spiSmallTitle = '송수펌프 주파수'
        this.spiData = true
        chartHeight = 200 + (plusHeight) + "px"
        this.chartHeight.height = chartHeight
        const spiNames = []
        const spiXData = []
        const spiYData = []
        pumpData?.SPI_TAG.forEach(element => {
          if (!spiNames.includes(element.name)) {
            spiNames.push(element.name)
          }

          if (!spiXData.includes(element.ts)) {
            spiXData.push(element.ts)
          }
        });

        spiNames.forEach(element => {
          let data = []
          pumpData?.SPI_TAG.forEach((item) => {
            if (item.name == element) {
              data.push(item.value)
            }
          })
          spiYData.push(data)
        })

        this.$refs.pwiChart.initChart(pwiXData, pwiYData, pwiNames, 'area', 'kWh', chartHeight)
        this.$refs.spiChart.initChart(spiXData, spiYData, spiNames, 'line', 'Hz', chartHeight)
      } else {
        this.spiData = false;
        this.reSmallTitle = '송수펌프 전력'
        this.chartLoad = true;
        this.$refs.pwiChart.initChart(pwiXData, pwiYData, pwiNames, 'area', 'kWh', chartHeight)

      }
    },
    async excelDown(startDate, endDate) {
      const dateFrom = new Date(startDate.getTime() + 9 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0];
      const dateTo = new Date(endDate.getTime() + 9 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0];
      try {
        const response = await fetch(`${this.$apiURL}/dr/pumpCombinationExcel?startDate=${dateFrom}&endDate=${dateTo}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) {
          // 응답이 200-299 범위가 아닌 경우
          if (response.status === 400) {
            const errorMessage = await response.text(); // 서버에서 보낸 에러 메시지를 읽음
            alert(errorMessage); // 에러 메시지를 알림으로 표시
          } else {
            alert('엑셀 다운로드 실패: 서버 에러');
          }
          return; // 파일 다운로드가 진행되지 않도록 리턴
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(new Blob([blob]));
        const a = document.createElement('a');
        a.href = url;
        a.download = `가동이력.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } catch (error) {
      
        alert('엑셀 다운로드 실패');
      } }


  }
};
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
</style>
