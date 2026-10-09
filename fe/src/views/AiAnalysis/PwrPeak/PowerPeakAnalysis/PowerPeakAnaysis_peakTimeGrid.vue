<template>
  <b-container fluid class="main-content">
    <!-- 본문 컨텐츠 시작 -->
    <div class="contents-container mt-3" v-bind:style="{ width: '100%' }">
      <b-row>
        <b-col xl="12">
          <b-row>
            <b-col v-bind:style="{ height: '370px' }">
              <small-title :title="title"></small-title>
              <area-chart ref="AreaChart" />
            </b-col>
          </b-row>
        </b-col>
      </b-row>
    </div>
    <!-- 본문 컨텐츠 끝 -->
  </b-container>
</template>

<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
import AreaChart from "@/components/Chart/AreaChart.vue";
import ChartClass from "@/components/Chart/ChartClass.js";

export default {
  components: { SmallTitle, AreaChart },
  props: ['costPower'],
  data() {
    return {
      title: "전력 피크 예상 시간",
      DATE: [],
      option: null,
      value: 0,
      peakTime: [],
    };
  },
  mounted() {
    this.fetchChartData(); // selectData() 함수 호출
  },

  methods: {
    twoDigits(num) {
      return num.toString().padStart(2, "0");
    },
    async fetchChartData() {
      let now = new Date();
      var year2 = now.getFullYear();
      var month2 = this.twoDigits(now.getMonth() + 1);
      var date = this.twoDigits(now.getDate());
      let currentHour = now.getHours();
      let formattedHour = currentHour < 10 ? '0' + currentHour : currentHour;
      let currentMinute = now.getMinutes();
      let currentTime = `${year2}-${month2}-${date} ${formattedHour}:${currentMinute}`;
      // var timeFlag= min - min%15;
      let todayTime = year2 + "-" + month2 + "-" + date;
      const apiURL = this.$apiURL;
      let res = await fetch(
        // `${apiURL}/ai/peakSelect?date=${todayTime}&search2=${search2}&search3=${search3}`
        `${apiURL}/ai/selectPwrPrdctList?date=${todayTime}`
        // `${apiURL}/ai/peakSelect?date=${todayTime}`
      );
      let data = await res.json();
      // data = { "code": 200, "message": "정상적으로 조회되었습니다.", "data": [{ "DATE": "2024-05-30 10:00", "PRDCT_PWR": 4008.83, "PWR": 4078.22, "PEAK_YN": "N" }, { "DATE": "2024-05-30 11:00", "PRDCT_PWR": 4114.56, "PWR": 4013.42, "PEAK_YN": "N" }, { "DATE": "2024-05-30 12:00", "PRDCT_PWR": 4069.38, "PWR": 3995.68, "PEAK_YN": "N" }, { "DATE": "2024-05-30 13:00", "PRDCT_PWR": 4012.52, "PWR": 4070.98, "PEAK_YN": "N" }, { "DATE": "2024-05-30 14:00", "PRDCT_PWR": 4009.84, "PWR": 3986.21, "PEAK_YN": "N" }, { "DATE": "2024-05-30 15:00", "PRDCT_PWR": 3879.9, "PWR": 3679.66, "PEAK_YN": "N" }, { "DATE": "2024-05-30 16:00", "PRDCT_PWR": 3855.43, "PEAK_YN": "N" }, { "DATE": "2024-05-30 17:00", "PRDCT_PWR": 3850.95, "PEAK_YN": "N" }, { "DATE": "2024-05-30 18:00", "PRDCT_PWR": 3978.14, "PEAK_YN": "N" }, { "DATE": "2024-05-30 19:00", "PRDCT_PWR": 4009.16, "PEAK_YN": "N" }, { "DATE": "2024-05-30 20:00", "PRDCT_PWR": 4036.57, "PEAK_YN": "N" }, { "DATE": "2024-05-30 21:00", "PRDCT_PWR": 4082.26, "PEAK_YN": "N" }, { "DATE": "2024-05-30 22:00", "PRDCT_PWR": 4001.8, "PEAK_YN": "N" }, { "DATE": "2024-05-30 23:00", "PRDCT_PWR": 4351.76, "PEAK_YN": "N" }, { "DATE": "2024-05-31 00:00", "PRDCT_PWR": 4440.02, "PEAK_YN": "N" }, { "DATE": "2024-05-31 01:00", "PRDCT_PWR": 4551.88, "PEAK_YN": "N" }, { "DATE": "2024-05-31 02:00", "PRDCT_PWR": 4545.47, "PEAK_YN": "N" }, { "DATE": "2024-05-31 03:00", "PRDCT_PWR": 4538.05, "PEAK_YN": "N" }, { "DATE": "2024-05-31 04:00", "PRDCT_PWR": 4411.72, "PEAK_YN": "N" }, { "DATE": "2024-05-31 05:00", "PRDCT_PWR": 4492.64, "PEAK_YN": "N" }, { "DATE": "2024-05-31 06:00", "PRDCT_PWR": 4351.16, "PEAK_YN": "N" }, { "DATE": "2024-05-31 07:00", "PRDCT_PWR": 4341.31, "PEAK_YN": "N" }, { "DATE": "2024-05-31 08:00", "PRDCT_PWR": 4060.24, "PEAK_YN": "N" }, { "DATE": "2024-05-31 09:00", "PRDCT_PWR": 3931.21, "PEAK_YN": "N" }] }
      if (data !== null) {
        let dataX = [];
        let dataY = [[], []];
        for (let i = 0; i < data.data.length; i++) {
          dataX.push(data.data[i]["DATE"]);
          let pwr = data.data[i]["PWR"];
          let prdctPwr = data.data[i]["PRDCT_PWR"];
          if (isNaN(prdctPwr)) {
            // 숫자 변환이 실패한 경우
            // dataY[0].push(0);
          } else {
            dataY[1].push(prdctPwr);
          }
          if (isNaN(pwr)) {
            // dataY[1].push[0];
          } else {
            dataY[0].push(pwr);
          }
          if (data.data[i]["PEAK_YN"] == "Y" && data.data[i]["DATE"] >= currentTime) {
            this.peakTime.push(data.data[i]["DATE"].substring(11));
            this.$emit("peakTime", this.peakTime[0]);
          }
        }
        dataY[0].slice(0, new Date().getHours() + 1)
        let detline = [];
        // let code = 0;
        let res2 = await fetch(`${apiURL}/st/selectPeakGoal`);
        let data2 = await res2.json();
        if (data2 !== null) {
          // code = data2.code;
          detline.push(data2.data[0]["value"]);
          detline.push(this.costPower)
          // console.log("code = " + code);
        }
        let chartClass = new ChartClass(
          dataX,
          dataY,
          ["발생 전력", "예상 전력"],
          detline,
          "날짜",
          "kWh"
        )
        this.$refs.AreaChart.changeData(
          chartClass
        );
      }
    },
  },
};
</script>
