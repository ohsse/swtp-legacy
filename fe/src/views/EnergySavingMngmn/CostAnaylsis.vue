<template>
  <!--최적요금제분석 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <!-- 타이틀 시작 -->
    <div class="container-fluid">
      <b-row>
        <BigTitle :title="'최적요금제 분석'" />
      </b-row>
      <!-- 타이틀 끝 -->
      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container mt-3">
        <b-row class="">
          <b-col>
            <div class="costBg p-5" v-bind:style="{ height: '900px' }">
              <b-row class="my-5" v-bind:style="{ height: '88%' }">
                <usage ref="usage" @setDate="getMonthDate" />
                <b-col xl="6">
                  <b-row class="gy-3">
                    <totalcost ref="total" />
                    <list ref="list" />
                  </b-row>
                </b-col>
                <right ref="right" @select="setSelect" />
              </b-row>
            </div>
          </b-col>
        </b-row>
      </div>
      <!-- 본문 컨텐츠 끝 -->
    </div>
  </div>
</template>

<script>
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"
import totalcost from "@/views/EnergySavingMngmn/Cost/CostAnaysis_totalcost.vue";
import right from "@/views/EnergySavingMngmn/Cost/CostAnaysis_right.vue";
import usage from "@/views/EnergySavingMngmn/Cost/CostAnaylsis_usage.vue";
import list from "@/views/EnergySavingMngmn/Cost/CostAnaysis_list.vue"
import { fetchFunc } from '@/util/fetchFunc';


export default {
  components: {
    BigTitle,
    totalcost,
    right,
    list,
    usage
  },
  data() {
    return {
      monthDate: null,
      select: 1,
      selected1: new Object(),
      selected2: new Object(),
      selected3: new Object(),
      selectData: new Object(),
      season: null,
      month: null,
      seasonData1: new Array(),
      seasonData2: new Array(),
      seasonData3: new Array(),
      seasonData: new Array()
    }
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
  },
  methods: {
    getMonthDate(date) {

      const getDate = new Date(date);
      const year = getDate.getFullYear()
      let month = getDate.getMonth() + 1;
      if (month >= 11 || month <= 2) {
        this.season = '겨울철'
      } else if (month <= 5 && month >= 3) {
        this.season = '봄철'
      } else if (month <= 8 && month >= 6) {
        this.season = '여름철'
      } else {
        this.season = '가을철'
      }
      if (month < 10) {
        month = `0${month}`
      }
      this.month = month
      this.monthDate = `?ymnth=${year}${month}`
      this.$refs.list.setSeason(this.season)
      this.$refs.usage.setMonth(month)
      this.$refs.total.setMonth(month);
      this.getData()
    },
    async getData() {
      const apiURL = this.$apiURL;
      let selectRtRate = (await fetchFunc(`${apiURL}/ai/selectRtRate${this.monthDate}`)).data

      if(selectRtRate.length==0){
        this.selected1 = this.noData()
        this.selected2 = this.noData()
        this.selected3 = this.noData()
      }else{
        selectRtRate.forEach((item) => {
          switch (item.SMALL_CTGRY) {
            case "선택I":
              this.selected1 = item;
              break;
            case "선택II":
              this.selected2 = item;
              break;
            case "선택III":
              this.selected3 = item;
              break;
          }
        });
      }


      let seasonData = (await fetchFunc(`${apiURL}/es/selectRateInfo`)).data
      let targetData = new Array()
      seasonData.forEach((item) => {
        if (item.MNTH == this.month) {
          targetData.push(item)
        }
      })
      this.seasonData1 = []
      this.seasonData2 = []
      this.seasonData3 = []
      targetData.forEach((item) => {
        switch (item.RATE_IDX) {
          case 1:
            this.seasonData1.push(item);
            break;
          case 2:
            this.seasonData2.push(item);
            break;
          case 3:
            this.seasonData3.push(item);
            break;
        }
      })


      this.setData()
    },
    setSelect(num) {
      this.select = num;
      this.setData()
    },
    setData() {
      switch (this.select) {
        case 1:
          this.selectData = this.selected1;
          this.seasonData = this.seasonData1;
          break;
        case 2:
          this.selectData = this.selected2;
          this.seasonData = this.seasonData2;
          break;
        case 3:
          this.selectData = this.selected3;
          this.seasonData = this.seasonData3;
          break;
      }

      this.$refs.list.setRow(this.seasonData)
      this.selectData.selectCost = `${this.selectData.MIDDLE_CTGRY} ${this.selectData.SMALL_CTGRY}`
      this.$refs.usage.setValueData(this.selectData)
      this.$refs.right.setValueData(this.selectData)
      this.$refs.total.setTotal(this.selectData.TOT_FEE)
    },
    noData(){
      return {
        "LARGE_CTGRY":"산업용(을)",
        "PWR":0,
        "DATA_MSN_PRCNT":0,
        "TOT_PWR":0,
        "L_PWR":0,
        "M_PWR":0,
        "H_PWR":0,
        "TOT_FEE":0,
        "BASE_FEE":0,
        "ETC_FEE":0,
        "L_ELCTR_FEE":0,
        "M_ELCTR_FEE":0,
        "H_ELCTR_FEE":0
      }
      
    }
  }

};
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.costBg {
  height: 95%;
  background: url(/src/assets/img/cost_bg.png) no-repeat;
  background-size: 100% 100%;
}
</style>
