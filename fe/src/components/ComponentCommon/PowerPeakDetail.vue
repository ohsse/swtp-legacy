<!--전력피크 분석 세부현황 컴포넌트의 템플릿 부분 -->
<template>
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <big-title :title="bigTitle" />
      <!-- 타이틀 끝 -->

      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container mt-3">
        <b-row class="mt-3">
          <b-col class="d-flex align-items-center">
            <span v-if="isGoal" class="detail_text mx-3">피크치 설정</span>
            <input v-if="isGoal" v-model="detline" class="textinput" style="margin-left: 50px" type="text" />
            <button v-if="isGoal" class="search_btn_font search_btn mx-2" @click="insertPeakGoal">
              저장
            </button>
            <span class="refresh_img"></span>
            <span class="font_timer" id="MyTimer">{{ formattedTime }}</span>
          </b-col>
        </b-row>

        <b-row>
          <!--왼쪽 그래프 컴포넌트-->
          <b-col xl="7" v-bind:style="{ height: '860px' }">
            <area-chart ref="AreaChart" />
          </b-col>

          <!--오른쪽 그래프 컴포넌트 -->
          <InstantaneousData />
        </b-row>
      </div>
      <!-- 본문 컨텐츠 끝 -->
    </b-container>
  </div>
</template>

<script>
import BigTitle from "@/components/ComponentCommon/BigTitle.vue";
import InstantaneousData from "@/components/ComponentCommon/InstantaneousData.vue";
import AreaChart from "@/components/Chart/AreaChart.vue";
import {
  getPowerPeakData,
  twoDigits,
} from "@/components/Func/PowerPeakFunc.js";
import ChartClass from "@/components/Chart/ChartClass";

export default {
  components: {
    AreaChart,
    BigTitle,
    InstantaneousData,
  },
  mounted() {
    this.$emit("onChangeBgClass", true);
    this.startTimer();
    this.fetchChartData();
    this.urlChange();
  },
  updated() {
    this.urlChange();
  },
  data() {
    let url = window.location.href;
    let bigTitle = "전력피크 세부현황";
    let isGoal = false;

    return {
      url,
      timeRemaining: 900, // 15:00 (15 minutes in seconds)
      bigTitle,
      isGoal,
      detline: 0,
    };
  },
  methods: {
    urlChange() {
      
      if (this.$route.path.endsWith("TargetStategyPeak")) {
        this.isGoal = true;
        this.bigTitle = "목표 전력피크";
      } else {
       
        this.isGoal = false;
        this.bigTitle = "전력피크 세부현황"
      }
    },


    startTimer() {
      setInterval(() => {
        if (this.timeRemaining > 0) {
          this.timeRemaining--;

          if (this.timeRemaining === 0) {
            location.reload(); // 새로고침
          }
        }
      }, 1000);
    },
    async fetchChartData() {
      let returnData = await getPowerPeakData(this.$apiURL);
      if (returnData) {
        this.detline = returnData.detline;
        let chartObj = new ChartClass(
          returnData.dataX,
          returnData.dataY,
          ["발생 전력", "예상 전력"],
          returnData.detline,
          "날짜",
          "kWh"
        );
        this.$refs.AreaChart.changeData(chartObj);
      }
    },
    async insertPeakGoal() {
      if (confirm("저장하시겠습니까?")) {
        const apiURL = this.$apiURL;
        const requestData = {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: `peakValue=${encodeURIComponent(this.detline)}`,
        };

        try {
          await fetch(
            `${apiURL}/st/insertPeakGoal`,
            requestData
          );
          
          alert("저장되었습니다.");
          location.reload();
        } catch (error) {
          alert("저장에 실패하였습니다.");
        }
      }
    },
  },
  computed: {
    formattedTime() {
      const minutes = Math.floor(this.timeRemaining / 60);
      const seconds = this.timeRemaining % 60;
      return `${twoDigits(minutes)}:${twoDigits(seconds)}`;
    },
  },
};
</script>
<style scoped>
.detail_text {
  font-size: 16px;
  font-family: "KHNPHDRegular";
  letter-spacing: 0.1rem;
  color: #c3eaff;
  font-weight: normal;
  text-shadow: 0 0 9px #5cafff;
}

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

.refresh_img {
  display: inline-block;
  background: url(/src/assets/img/refresh.png) no-repeat;
  background-size: 100% 100%;
  background-position: center;
  width: 55px;
  height: 55px;
  margin-left: 560px;
}
</style>
