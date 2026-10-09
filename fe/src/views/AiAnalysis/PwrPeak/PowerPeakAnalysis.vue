<template>
  <!--전력피크 분석 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <div class="containerBar">
        <big-title :title="bigTitle" />
        <div>
          <span class="detail_text mx-3">피크치 설정</span>
          <input v-model="detline" class="textinput" style="margin-left: 50px" type="text" />
          <button class="search_btn_font search_btn mx-2" @click="insertPeakGoal">
            저장
          </button>
        </div>
      </div>
      <!-- 타이틀 끝 -->
      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container mt-3">
        <b-row>
          <majorel ref="Majorel" :sunsiPower="sunsiPower" :targetPower="targetPower" :costPower="costPower" />
          <b-col xl="8">
            <b-row>
              <totalUsage :sunsiPower="sunsiPower" :targetPower="songsuPower" :costPower="costPower" />
              <b-col v-if="this.songsu" class="d-flex align-items-center">
                <div class="star"></div>
              </b-col>
              <rightGrid v-if="this.songsu" />
              <peakTimeGrid @peakTime="peakTime" :costPower="costPower" />
            </b-row>
          </b-col>
        </b-row>
      </div>
      <!-- 본문 컨텐츠 끝 -->
    </b-container>
  </div>
</template>

<script>
import BigTitle from "@/components/ComponentCommon/BigTitle.vue";
import majorel from "@/views/AiAnalysis/PwrPeak/PowerPeakAnalysis/PowerPeakAnalysis_majorel.vue";
import totalUsage from "@/views/AiAnalysis/PwrPeak/PowerPeakAnalysis/PowerPeakAnalysis_totalUsage.vue";
import rightGrid from "@/views/AiAnalysis/PwrPeak/PowerPeakAnalysis/PowerPeakAnalysus_rightGrid.vue";
import peakTimeGrid from "@/views/AiAnalysis/PwrPeak/PowerPeakAnalysis/PowerPeakAnaysis_peakTimeGrid.vue";
import { getPowerPeakData } from "@/components/Func/PowerPeakFunc.js";
import Swal from 'sweetalert2'
export default {
  components: {
    peakTimeGrid,
    rightGrid,
    totalUsage,
    majorel,
    BigTitle,
  },
  data() {
    let bigTitle = "전력피크 분석";
    let sunsiPower;
    let targetPower;
    let costPower;
    let songsuPower;
    let songsu;
    return {
      bigTitle,
      sunsiPower,
      targetPower,
      costPower,
      songsuPower,
      songsu,
      detline: 0,
    };
  },
  mounted() {
    if (this.$area == 'hakya' || this.$area == 'jain') {
      this.songsu = false
    }
    else {
      this.songsu = true
    }
    this.$emit("onChangeBgClass", false);
    this.fetchData();
    this.fetchChartData();
  },
  methods: {
    peakTime(peakTime) {
      
      this.$refs.Majorel.peakTimeFunction(peakTime);
    },
    fetchData() {
      const apiURL = this.$apiURL;
      fetch(`${apiURL}/ai/selectPeakControl`)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to fetch");
          }
          return response.json();
        })
        .then((data) => {
          if (data !== null) {
            this.sunsiPower = data.data[0].allPwi;
            this.sunsiPower = Math.ceil(this.sunsiPower);
            this.sunsiPower = this.sunsiPower.toLocaleString();

            this.targetPower = data.data[0].goalPeak;
            this.targetPower = Math.ceil(parseFloat(this.targetPower));
            this.targetPower = this.targetPower.toLocaleString();

            this.costPower = data.data[0].costPwr;
            this.costPower = Math.ceil(this.costPower);
            this.costPower = this.costPower.toLocaleString();

            this.songsuPower = data.data[0].pumpPwi;
            this.songsuPower = Math.ceil(this.songsuPower);
            this.songsuPower = this.songsuPower.toLocaleString();

          } 
        })
        .catch(() => {
       
        });
    },
    async insertPeakGoal() {
      const confirmed = await Swal.fire({
        text: '저장하시겠습니까?',
        animation: false,
        showCancelButton: true,
        confirmButtonText: '저장',
        cancelButtonText: '취소'
      });



      if (confirmed.isConfirmed) {
        const apiURL = this.$apiURL;
        const requestData = {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: `peakValue=${encodeURIComponent(this.detline)}`,
        };

        try {
          const response = await fetch(
            `${apiURL}/st/insertPeakGoal`,
            requestData
          );
          await response.json();
          
          Swal.fire({
            animation: false,
            text: '저장되었습니다.',
          }).then(() => {
            location.reload();
          });
        } catch (error) {
          Swal.fire({
            animation: false,
            text: '저장에 실패하였습니다.',
          });
        }
      }
    },
    async fetchChartData() {
      let returnData = await getPowerPeakData(this.$apiURL);
      if (returnData) {
        this.detline = returnData.detline;
      }
    },
  },
};
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.containerBar {
  display: flex;
  justify-content: space-between;
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
  font-size: 17px;
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
}
</style>
