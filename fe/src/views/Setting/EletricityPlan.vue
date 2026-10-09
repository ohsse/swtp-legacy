<template>
  <!--전력요금제 컴포넌트의 템플릿 부분 -->
  <div class="container-fluid">
    <!-- 템플릿 내용 -->
    <!-- 타이틀 -->
    <BigTitle :title="'전력 요금제'"></BigTitle>
    <!-- //타이틀 -->
    <!-- 본문 컨텐츠 시작 -->
    <div class="contents-container">
      <b-row>
        <b-col class="d-flex justify-content-end">
          <b-button id="btnSave" variant="secondary" class="season_btn season_btn_font fs-6 px-5"
            @click="paramData()">적용</b-button>
        </b-col>
      </b-row>
      <b-row class="mt-2">
        <b-col xl="3">
          <b-row class="row-cols-1 gy-3 ai-arrow-right">
            <eletricity_plan_option :result="result" @getCostData="getCostData" @postMonthSSN="postMonthSSN" />
            <eletricity_plan_season @getCostData="getCostData" :initSSN="initSSN" ref="season" />
          </b-row>
        </b-col>
        <b-col xl="9">
          <b-row class="row-cols-1 gy-3">
            <eletricity_plan_cost ref="EletricityPlanCost" />
            <eletricity_plan_timeSet ref="eletricity_plan_timeSet" @paramData="paramData"
              @handleOptionsChange="handleOptionsChange" />
          </b-row>
        </b-col>
      </b-row>
    </div>
    <!-- 본문 컨텐츠 끝 -->
  </div>
</template>

<script>
import BigTitle from '@/components/ComponentCommon/BigTitle.vue'
import eletricity_plan_season from "@/views/Setting/EletricityPlan/ElectricityPlan_season.vue";
import eletricity_plan_timeSet from "@/views/Setting/EletricityPlan/ElectricityPlan_timeSet.vue";
import eletricity_plan_cost from "@/views/Setting/EletricityPlan/EletricityPlan_cost.vue";
import eletricity_plan_option from "@/views/Setting/EletricityPlan/EletricityPlan_option.vue";
import { fetchFunc } from "@/util/fetchFunc";
import Swal from 'sweetalert2'
export default {
  components: {
    BigTitle,
    eletricity_plan_season,
    eletricity_plan_timeSet,
    eletricity_plan_cost,
    eletricity_plan_option,
  },
  data() {
    return {
      result: [],
      rateIdx: 1,
      ssn: "봄철",
      timezone: [],
      initData: [],
      newData: [],
      initSSN: '',
      monthClickSsn: ''
    };
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
    this.getData();
  },

  methods: {
    // 왼쪽 상단 월별 데이터 동작 
    async getData() {
      const index = new Date().getMonth()
      const apiURL = this.$apiURL;
      let data = await fetchFunc(`${apiURL}/st/selectMonthSeason`);
      this.result = data.data;
      this.initSSN = this.result[index].SSN
      this.ssn = this.result[index].SSN
      this.monthClickSsn = this.result[index].SSN
      this.initCostData(this.initSSN);
    },
    async initCostData(initSSN) {
      const apiURL = this.$apiURL;
      let data = await fetchFunc(
        `${apiURL}/st/selectRateSeason?ssn=${initSSN}`
      );
      let selectRate = {}
      selectRate.BASE_RATE = data.data.BASE_RATE
      selectRate.H_RATE = data.data.H
      selectRate.M_RATE = data.data.M
      selectRate.L_RATE = data.data.L

      let selectSeasonLoad = data.data.selectSeasonLoad
      this.initData = selectSeasonLoad
      this.$refs.EletricityPlanCost.setCost(selectRate);
      this.$refs.eletricity_plan_timeSet.getData(selectSeasonLoad);
    },

    // 계절 변경시 api 동작 
    async getCostData(ssn) {
      const apiURL = this.$apiURL;
      this.monthClickSsn = ssn
      this.$refs.season.updateSeason(ssn);

      let data = await fetchFunc(
        `${apiURL}/st/selectRateSeason?ssn=${ssn}`
      );
      let selectRate = {}
      selectRate.BASE_RATE = data.data.BASE_RATE
      selectRate.H_RATE = data.data.H
      selectRate.M_RATE = data.data.M
      selectRate.L_RATE = data.data.L
      let selectSeasonLoad = data.data.selectSeasonLoad
      this.initData = selectSeasonLoad
      this.$refs.EletricityPlanCost.setCost(selectRate);
      this.$refs.eletricity_plan_timeSet.getData(selectSeasonLoad);
    },

    postMonthSSN(option) {
      // this.result.at(option.month).SSN = option.options
      this.result[option.month].SSN = option.options
    },
    async paramData() {
    

      const apiURL = this.$apiURL;
      const BASE_RATE = parseFloat(this.$refs.EletricityPlanCost.BASE_RATE);
      const L_RATE = this.$refs.EletricityPlanCost.L_RATE;
      const M_RATE = this.$refs.EletricityPlanCost.M_RATE;
      const H_RATE = this.$refs.EletricityPlanCost.H_RATE;

      let paramRate = {
        "base_rate": BASE_RATE,
        "rate_L": L_RATE,
        "rate_M": M_RATE,
        "rate_H": H_RATE,
        "ssn": this.monthClickSsn
      };
      let params = [];

      for (var i = 0; i < 24; i++) {
        let obj = {
          stn_tm: i.toString().padStart(2, "0"),
          timezone: this.initData[i].TIMEZONE,
          ssn: this.monthClickSsn,
        };
        params.push(obj);
      }

      let paramMonth = []
      for (var index = 0; index < 12; index++) {
        let obj = {
          ssn: this.result[index].SSN,
          month: this.result[index].MNTH,
        };
        paramMonth.push(obj);
      }


      const confirmed = await Swal.fire({
        text: '적용하시겠습니까?',
        animation : false,
        showCancelButton: true,
        confirmButtonText: '저장',
        cancelButtonText: '취소'
      });
     
      if (confirmed.isConfirmed) {
        // 값이 비어있는지 확인하여 알림창을 띄웁니다.
        if (!BASE_RATE || !L_RATE || !M_RATE || !H_RATE) {
          await Swal.fire({
            animation : false,
            text: '요금을 입력해주세요.',
          });
          return;
        }
        var myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");


        var requestOptionsMonth = {
          method: "POST",
          headers: myHeaders,
          body: JSON.stringify(paramMonth),
        };
     

        // 변경된 월별 계절 변경 
        await fetch(`${apiURL}/st/setMonthSeason`, requestOptionsMonth)
          .then((response) => response.text());


        var requestOptionRate = {
          method: "POST",
          headers: myHeaders,
          body: JSON.stringify(paramRate),
        };

        

        // 요금제 api 
        await fetch(`${apiURL}/st/setRateCost`, requestOptionRate)
          .then((response) => response.text());

        var requestOptions = {
          method: "POST",
          headers: myHeaders,
          body: JSON.stringify(params),
        };

       

        // 시간대별 api 
        await fetch(`${apiURL}/st/setSeasonLoad`, requestOptions)
          .then((response) => response.text());
          await Swal.fire({
          animation: false,
          text: '저장되었습니다.',
          confirmButtonText: '확인'
        }).then(() => {
          location.reload(); 
        });
      } else {
        await Swal.fire({
          animation : false,
          text: '저장이 취소되었습니다.',
        });
      }
    },

    handleOptionsChange(selectedOptions) {
      // 여기에서 변경된 options에 대한 처리를 수행할 수 있습니다.
      // this.initData.at(selectedOptions.index).TIMEZONE = selectedOptions.options
      this.initData[selectedOptions.index].TIMEZONE = selectedOptions.options
    },
  },
};
</script>

<style src="@vueform/multiselect/themes/default.css"></style>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.contents-container {
  height: 93%;
  width: 99%;
}

.season_btn {
  height: 33px;
  padding-top: 3px;
  padding-bottom: 3px;
  border: solid 1px #b4dffa;
  background-color: rgba(139, 194, 240, 0.25);
}

.season_btn_font {
  text-shadow: 0 0 9px #5cafff;
  letter-spacing: normal;
  color: #fff;
  font-family: "KHNPHDRegular";
}

.ai-arrow-right {
  position: relative;
  left: 30px;
}

.ai-arrow-right::after {
  display: inline;
  content: "";
  width: 40px;
  height: 318px;
  position: absolute;
  top: 28%;
  right: 74px;
  background: url(@/assets/img/ai_arrow_right.png);
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  -webkit-animation: blink 3s linear infinite;
  -moz-animation: blink 3s linear infinite;
  animation: blink 3s linear infinite;
}

.div_title {
  height: 40px;
  background: url(@/assets/img/title_bar.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: color-dodge;
  color: #ffffff;
  font-family: KHNPHDRegular;
  font-size: 19px;
  text-shadow: 0 0 10px #000;
  line-height: 2;
  text-indent: 20px;
}

.div_border {
  background-image: url(@/assets/img/box_bg_small.png);
  background-size: 100% 100%;
}

.list-custom-group.list-group .list-group-item {
  border: 0;
  background: transparent;
  color: white;
  text-align: center;
  height: 57px;
  line-height: 42px;
}

.list-custom-group.list-group .list-group-item.active {
  background: url(@/assets/img/pump/text_input_bg.png);
  background-size: 100% 100%;
  background-repeat: no-repeat;
}

.bigListFont {
  font-family: KHNPHDRegular;
  font-size: 21px;
  color: white;
  text-shadow: 0 0 9px #5cafff;
}

.bottomContentsImg {
  height: calc(100% / 6);
  background: url(@/assets/img/one_pump.png) no-repeat;
  background-size: 100% 100%;
}

.top_textinput {
  height: 21%;
  width: 56%;
  display: inline-block;
  margin-top: 51px;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  font-family: LABDigital;
  text-align: center;
  font-size: 20px;
  letter-spacing: 4px;
}

.topUnitFont {
  color: #ffffff;
  font-family: "KHNPHDRegular";
  font-size: 18px;
  text-shadow: 0 0 10px #000;
  margin-left: 10px;
}

.value_bottom_img {
  background-image: url(@/assets/img/bottom_aura.png);
  background-size: 100% 100%;
  background-repeat: no-repeat;
  height: 24%;
  width: 94%;
  display: inline-block;
}

.comboFont {
  color: #ffffff;
  font-family: "KHNPHDRegular";
  font-size: 15px;
  text-shadow: 0 0 10px #000;
  margin-right: 30px;
  line-height: 47px;
}

/* 셀렉트 박스 (다크테마) */
.comboBox {
  background-color: #15284e;
  color: #fff;
  width: 169px;
  font-size: 15px;
  font-family: KHNPHDRegular;
  margin-top: 5px;
}

.k-select {
  border-color: #489cf2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.k-icon,
.k-tool-icon {
  color: #489cf2;
  cursor: pointer;
  position: relative;
  display: inline-block;
  overflow: hidden;
  width: 1em;
  height: 1em;
  text-align: center;
  vertical-align: middle;
  background-image: none;
  font: 16px/1 WebComponentsIcons;
  speak: none;
  font-variant: normal;
  text-transform: none;
  text-indent: 0;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: inherit;
}

.k-icon:before {
  margin: auto;
  width: 1em;
  height: 1em;
  line-height: 1;
  display: inline-block;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
}
</style>
