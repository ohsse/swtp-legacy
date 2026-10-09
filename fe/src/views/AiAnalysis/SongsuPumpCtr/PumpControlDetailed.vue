
<template>
  <LoadingSpinner class="loading-container" v-if="isLoading"></LoadingSpinner>
  <!--송수펌프 제어 분석 세부현황 컴포넌트의 템플릿 부분 -->
  <div>
    <!-- 템플릿 내용 -->
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <b-row class="detail_textWrap my-0">
        <b-col xl="9" style="padding-right: 30px;">
          <b-row class="align-items-center">
            <b-col xl="3" class="title_wrap">
              <SmallTitleVue :title="'송수펌프 제어 세부 현황'" />
            </b-col>
            <TopSubValuesVue :topData="topSubData" />
          </b-row>
        </b-col>
        <b-col xl="3">
          <b-row class="align-items-center"
            :style="{ textShadow: '0 0 9px #5cafff', color: '#c3eaff', fontSize: '14px' }">
            <b-col class="text-center">
              <span class="detail_text">유입유량</span>
            </b-col>
            <b-col class="text-end">
              <span class="detail_text">개도율</span>
            </b-col>
            <b-col class="text-end">
              <span class="detail_text">수위</span>
            </b-col>
            <b-col class="text-center">
              <span class="detail_text">유출유량</span>
            </b-col>
          </b-row>
        </b-col>
      </b-row>
      <!-- 타이틀 끝 -->
      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container mt-1">
        <b-row>
          <b-col xl="9">
            <!-- AI 펌프 영역 시작 -->
            <b-row>
              <b-col xl="9">
                <template v-if="pumpLoad">
                  <b-col>
                    <b-row class="mb-5" v-for="(item, index) in pumpMaster" :key="item" style="min-height:320px">
                      <b-col xl="5">
                        <template v-if="dataLoad">
                          <DetailedPumpBox :boxData="prdctBoxDatas[pumpGrpNm[index]]" :prdct="true"
                            :pumpWidth="pumpMaster.length" />
                        </template>
                      </b-col>
                      <b-col xl="2"
                        :class="{ 'd-flex align-items-center justify-content-center': pumpMaster.length === 1 }">
                        <AiOperationVue :nameSet="index" />
                      </b-col>
                      <b-col xl="5">
                        <div class="fL table-bg"
                          style="width: 100%; padding-bottom: 15px; margin-bottom: 10px; background-size: 101% 104%;  background-position: center;">
                          <template v-if="dataLoad">
                            <DetailedPumpBox :boxData="boxDatas[pumpGrpNm[index]]" :prdct="false"
                              :pumpWidth="pumpMaster.length" />
                          </template>
                        </div>
                      </b-col>
                    </b-row>
                  </b-col>
                </template>
              </b-col>
              <template v-if="pumpLoad">
                <DetailedPipeVue ref="Pipe" :pipeShow="pumpMaster.length" />
              </template>
            </b-row>
            <!-- //AI 펌프 영역 끝 -->
          </b-col>
          <b-col xl="3" style="height: 860px; overflow-y: scroll;">
            <div class="pipes_wrap">
              <template v-if="dataLoad">
                <DetailedRight v-for="item in drainedData" :key="item" :data="item" />
              </template>
            </div>
          </b-col>
        </b-row>
      </div>
    </b-container>
  </div>
</template>

<script>
import LoadingSpinner from '@/components/ComponentCommon/LoadingSpinner.vue';
import DetailedPipeVue from './PumpDetailed/DetailedPipe.vue'
import SmallTitleVue from '@/components/ComponentCommon/SmallTitle.vue'
import TopSubValuesVue from './PumpDetailed/TopSubValues.vue'
import DetailedRight from './PumpDetailed/DetailedRight.vue'
import { fetchFunc } from '@/util/fetchFunc'
import DetailedPumpBox from './PumpDetailed/DetailedPumpBox.vue'
import AiOperationVue from './PumpDetailed/AiOperation.vue';

export default {
  components: {
    SmallTitleVue,
    LoadingSpinner,
    DetailedPipeVue,
    TopSubValuesVue,
    DetailedRight,
    DetailedPumpBox,
    AiOperationVue
  },
  data() {
    return {
      isLoading: true,
      topSubData: {
        dataTime: null,
        sequence: null,
        optMode: null

      },
      prdctBoxDatas: [],
      boxDatas: {},
      dataLoad: false,
      drainedData: [],
      pumpGrpNm: [],
      pumpMaster: [],
      pumpLoad: false
    }
  },
  mounted() {

    this.$emit("onChangeBgClass", false);
    this.getData()
  },
  methods: {
    async getData() {
      this.isLoading = true
      const apiURL = this.$apiURL;
      const prdctData = (await fetchFunc(`${apiURL}/ai/selectPumpPrdct`)).data
      const interpuppt = (await fetchFunc(`${apiURL}/ai/interpuppt`)).data
      const tagValList = (await fetchFunc(`${apiURL}/ai/selectSongsuTagValueList`)).data
      this.pumpMaster = (await fetchFunc(`${apiURL}/ai/selectPumpMaster`)).data
      this.pumpLoad = true;
      for await (const pump of this.pumpMaster) {
        const targetPump = ((await fetchFunc(`${apiURL}/ai/pumpSelect?pump_grp=${pump.PUMP_GRP}`)).data).data
        this.makePrdctData(targetPump);
      }
      // const pumpSelect1 = ((await fetchFunc(`${apiURL}/ai/pumpSelect?pump_grp=1`)).data).data
      // const pumpSelect2 = ((await fetchFunc(`${apiURL}/ai/pumpSelect?pump_grp=2`)).data).data

      // //예상 펌프 데이터 전처리
      // this.makePrdctData(pumpSelect1)
      // this.makePrdctData(pumpSelect2)


      //상단 데이터 수집시간
      this.getPumpMinDate(interpuppt.selectPumpOnOffStatus)


      this.$refs.Pipe.getData(prdctData.MIN_RQRD_TUB, prdctData.BP_PRSR)
      this.topSubData.optMode = prdctData.optMode

      this.makeBoxData(tagValList.pumpList)
      this.makeTagData(tagValList.tnkList)

      this.dataLoad = true
      this.isLoading = false
    },
    /**
     * 데이터수집기간을 구하는 함수
     * @param {interpuppt.selectPumpOnOffStatus} data 
     */
    getPumpMinDate(data) {
      if (data.length == 0) {
        this.topSubData.dataTime
        return
      }
      let minDate = new Date(data[0]?.ts)
      let returnDate = data[0].ts
      for (const item of data) {
        const curDate = new Date(item.ts)
        if (curDate < minDate) {
          minDate = curDate
          returnDate = item.ts
        }
      }
      this.topSubData.dataTime = returnDate

    },
    makePrdctData(pumpDatas) {
      const prprcPump = pumpDatas.filter((pump) => pump.PRDCT_TIME_DIFF == 1440)
      const pumpGrp = prprcPump[0]?.PUMP_GRP
      const grpNm = prprcPump[0]?.PUMP_GRP_NM
      this.pumpGrpNm.push(grpNm)
      let cnt = 1;
      const returnObj = {
        title: grpNm,
        pumpDatas: [],
        sub: {
          grp_idx: pumpGrp,
          value: {
            [`${pumpGrp}_PWR_PRDCT`]: 0,
            [`${pumpGrp}_TUBE_PRSR_PRDCT`]: 0,
            [`${pumpGrp}_PRDCT_MEAN`]: 0
          }
        }
      }
      for (const pump of prprcPump) {
        returnObj.pumpDatas.push({
          PUMP_GRP_IDX: cnt,
          use: pump.PUMP_YN
        })

        if (this.$area == 'sanseong') {
          returnObj.sub.value[`${pumpGrp}_PWR_PRDCT`] += 0
          returnObj.sub.value[`${pumpGrp}_TUBE_PRSR_PRDCT`] += 0
          returnObj.sub.value[`${pumpGrp}_PRDCT_MEAN`] += 0
        } else {
          returnObj.sub.value[`${pumpGrp}_PWR_PRDCT`] += pump.PWR_PRDCT
          returnObj.sub.value[`${pumpGrp}_TUBE_PRSR_PRDCT`] += pump.TUBE_PRSR_PRDCT
          returnObj.sub.value[`${pumpGrp}_PRDCT_MEAN`] += pump.PRDCT_MEAN
        }

        cnt = cnt + 1
      }
      this.prdctBoxDatas[grpNm] = returnObj
      // return returnObj
    },
    makeBoxData(pumpData) {
      let pumpBoxObj = {}
      let runPump = 0
      pumpData.forEach(item => {
        if (Number(item.PMB_VALUE) == 1) {
          runPump = runPump + 1;
        }
        if (!(item.PUMP_GRP_NM in pumpBoxObj)) {
          pumpBoxObj[item.PUMP_GRP_NM] = {
            title: item.PUMP_GRP_NM,
            pumpDatas: [],
            sub: {
              grp_idx: item.PUMP_GRP,
              value: {
                [`${item.PUMP_GRP}_PWR_PRDCT`]: 0,
                [`${item.PUMP_GRP}_TUBE_PRSR_PRDCT`]: 0,
                [`${item.PUMP_GRP}_PRDCT_MEAN`]: 0
              }
            },
          }
        }
        pumpBoxObj[item.PUMP_GRP_NM].sub.value[`${item.PUMP_GRP}_PWR_PRDCT`] += Number(item.PWI_VALUE ?? 0)

        pumpBoxObj[item.PUMP_GRP_NM].sub.value[`${item.PUMP_GRP}_TUBE_PRSR_PRDCT`] += Number(item.PRI_VALUE ?? 0)

        pumpBoxObj[item.PUMP_GRP_NM].sub.value[`${item.PUMP_GRP}_PRDCT_MEAN`] += Number(item.FRI_VALUE ?? 0)
        let pumpDataObj = {
          PUMP_GRP_IDX: item.PUMP_GRP_IDX,
          use: Number(item.PMB_VALUE)
        }



        pumpBoxObj[item.PUMP_GRP_NM].pumpDatas.push(pumpDataObj)
      })
      this.topSubData.sequence = runPump;
      this.boxDatas = pumpBoxObj

    },
    makeTagData(data) {
      let tagList = []
      // let tagType = ['유입유량', '유출유량', '수위']
      let tagType = []
      // let tagDepth = ['수위1', '수위2']
      let tagDepth = []
      data.forEach(element => {
        if (!tagList.includes(element.TNK_GRP_NM)) {
          tagList.push(element.TNK_GRP_NM)
        }
        if (!tagType.includes(element.tag_dcs)) {
          tagType.push(element.tag_dcs)
        }
        if (!tagDepth.includes(element.TNK_NM)) {
          tagDepth.push(element.TNK_NM)
        }

      });


      let tagDataArr = []
      let cnt = 0
      tagList.forEach(tag => {

        let tagList = []
        tagDepth.forEach(depth => {
          let tagObj = {
            'tag_nm': tag.replace('배수지', ''),
            'depth': depth,
          }
          data.forEach(data => {
            if (data.TNK_GRP_NM == tag && data.TNK_NM == depth) {
              tagType.forEach(type => {
                if (data.tag_dcs == type) {
                  tagObj[type] = Number(data.value)
                }
              })

            }
          })
          if (tagObj['수위'] != null) {



            tagList.push(tagObj)
          }
        })
        const grpArr = []

        let drainedObj = {
          drainedTitle: tag.replace('배수지', '')
        }

        for (const grp of tagList) {
          const num = Number((grp.depth).slice(-1)) % 2 === 0 ? 2 : 1

          const keys = Object.keys(grp)
          for (const key of keys) {
            drainedObj[`${key}${num}`] = grp[key]
          }
          if (num / 2 != 1) {
            if (grp == tagList[tagList.length - 1]) {
              grpArr.push(drainedObj)
              drainedObj = {}
            }
          } else {
            grpArr.push(drainedObj)
            drainedObj = {}
          }
        }
        cnt = cnt + 1
        tagDataArr.push(grpArr)
      })

      this.drainedData = tagDataArr
    },
    drainedInput(data, num) {
      let returnObj = {}
      // returnObj["key"] = cnt
      const keys = Object.keys(data)
      for (const key of keys) {
        returnObj[`${key}${num}`] = data[key]
      }
      return returnObj
    }

  }
}
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.pipes_wrap {
  width: 95%;
  height: 98%;
  /* margin-left: 2%; */
  float: left;
}

.table-bg {
  background: url(@/assets/img/analysis/table_bg_03.png) no-repeat;
}

.r-circle {
  background: url(@/assets/img/r_circle.png) no-repeat;
  background-position: center;
}

.img_circle {
  background: url(@/assets/img/r_circle.png) no-repeat;
  background-position: center;
}

.circle-dot {
  max-height: 85%;
  border-style: dotted;
  border-color: #546b7d;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 2%;
  white-space: normal;
}

.ai_text {
  margin-right: 2%;
  font-size: 25px;
  font-family: 'KHNPHDBold';
  color: white;
  text-shadow: 0 0 10px #000000;
}

.detail_text {
  /* width: 70%; */
  text-shadow: 0 0 9px #5cafff;
  color: #c3eaff;
}

.pump_img {
  background: url(@/assets/img/peakcontrol/pump_peakcontrol.png) no-repeat;
  background-size: 28%;
  background-position: center;
  text-align: left;
  text-indent: 20%;
  mix-blend-mode: color-dodge;
}

.pump_area_h4 {
  height: calc(100%/ 4);
  width: calc(100%);
}

.pump_area_h35 {
  height: 52%;
  width: 100%;
}

.input_design {
  width: 70px;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  font-family: LABDigital;
  text-align: center;
}

.blinking1 {
  -webkit-animation: blink1 5s linear infinite;
  -moz-animation: blink1 5s linear infinite;
  animation: blink1 5s linear infinite;
}

.blinking {
  -webkit-animation: blink 3s linear infinite;
  -moz-animation: blink 3s linear infinite;
  animation: blink 3s linear infinite;
}

.blinkingY1 {
  -webkit-animation: blinkY1 5s linear infinite;
  -moz-animation: blinkY1 5s linear infinite;
  animation: blinkY1 5s linear infinite;
}

@-webkit-keyframes blinkY1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    top: 40%;
    transform: rotate(90deg);
  }

  24% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  36% {
    opacity: 1;
    transform: rotate(90deg);
  }

  48% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  60% {
    opacity: 0;
    top: 53%;
    transform: rotate(90deg);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@-moz-keyframes blinkY1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    top: 40%;
    transform: rotate(90deg);
  }

  24% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  36% {
    opacity: 1;
    transform: rotate(90deg);
  }

  48% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  60% {
    opacity: 0;
    top: 53%;
    transform: rotate(90deg);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@keyframes blinkY1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    top: 40%;
    transform: rotate(90deg);
  }

  24% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  36% {
    opacity: 1;
    transform: rotate(90deg);
  }

  48% {
    opacity: 0.5;
    transform: rotate(90deg);
  }

  60% {
    opacity: 0;
    top: 53%;
    transform: rotate(90deg);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@-webkit-keyframes blink1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    transform: translateX(-10px);
  }

  24% {
    opacity: 0.5;
    transform: translateX(-5px)
  }

  36% {
    opacity: 1;
    transform: translateX(0px);
  }

  48% {
    opacity: 0.5;
    transform: translateX(5px);
  }

  60% {
    opacity: 0;
    transform: translateX(10px);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@-moz-keyframes blink1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    transform: translateX(-10px);
  }

  24% {
    opacity: 0.5;
    transform: translateX(-5px)
  }

  36% {
    opacity: 1;
    transform: translateX(0px);
  }

  48% {
    opacity: 0.5;
    transform: translateX(5px);
  }

  60% {
    opacity: 0;
    transform: translateX(10px);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

@keyframes blink1 {
  0% {
    opacity: 0;
  }

  12% {
    opacity: 0;
    transform: translateX(-10px);
  }

  24% {
    opacity: 0.5;
    transform: translateX(-5px)
  }

  36% {
    opacity: 1;
    transform: translateX(0px);
  }

  48% {
    opacity: 0.5;
    transform: translateX(5px);
  }

  60% {
    opacity: 0;
    transform: translateX(10px);
  }

  72% {
    opacity: 0;
  }

  84% {
    opacity: 0;
  }

  100% {
    opacity: 0;
  }
}

.pipe_line_arrow {
  background: url(@/assets/img/dashboard/water.png) no-repeat;
  width: 100%;
  height: 100%;
  mix-blend-mode: color-dodge;
  background-position: center;
}

.pipeline-un {
  background: url(@/assets/img/analysis/pipeline_un.png) no-repeat;
}

.pipeline-y {
  background: url(@/assets/img/ai_song/pipeline_y.png) no-repeat;
}

.song-middle {
  background: url(@/assets/img/ai_song/middle.png) no-repeat;
}

.pipeline-un-y {
  background: url(@/assets/img/ai_song/pipeline_un_y.png) no-repeat;
}

.pipe_big_gauge {
  background: url(@/assets/img/ai_song/pipe_big.png) no-repeat;
  width: 100%;
  height: 60%;
  background-size: 100% 91%;
  float: left;
}

.pipe_big_background {
  background: url(@/assets/img/ai_song/pipe_big.png) no-repeat;
  width: 20%;
  height: 100%;
  background-size: 100% 90%;
  background-position: center;
  float: right;
  display: flex;
  align-items: flex-end;
}

.sub_content_middle_value {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50%;
  width: 100%;
}

.sub_input_box {
  width: 70px;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  font-family: LABDigital;
  text-align: center;
  margin-right: 2%;
  float: left;
}

.sub_content_font {
  text-shadow: 0 0 9px #5cafff;
  font-size: 14px;
  font-family: KHNPHDRegular;
  letter-spacing: normal;
  color: #c3eaff;
  align-self: center;
  padding: 0 2% 0 0;
  float: left;
}

.sub_content_middle_value {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50%;
  width: 100%;
}

.pipe_background {
  height: calc(100% / 14);
  background: url(@/assets/img/ai_song/one_pump.png) no-repeat;
  background-size: 100% 100%;
}

.pipes_wrap {
  width: 100%;
  height: 100%;
  /* margin-left: 2%; */
  /* padding: 1% 2%; */
  float: left;
}

.pipe2_wrap {
  height: 50%;
}

.pipe_wrap {
  display: flex;
  width: 100%;
  height: 90%;
}

.pipe_left_wrap {
  width: 48%;
  height: calc(100% - 10px);
  margin-top: 5px;
  display: flex;
  flex-direction: column;
}

.pipe_left_line1 {
  height: calc(100% / 2);
  width: calc(100% - 27px);
  margin: 0 10px;
}

.pipe_left_line1-1 {
  width: calc(27% + 4px);
  height: calc(100% - 4px);
  float: left;
}

.pipe_left_line1-3 {
  height: calc(100% - 4px);
  font-size: 15px;
  line-height: 1.3;
  border-radius: 3px;
  float: right;
  width: 27%;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  text-align: center;
  font-family: 'LABDigital';
}

.pipe_left_line3 {
  height: calc(100% / 2);
  width: calc(100% - 27px);
  margin: 0 10px;
}

.pipe_left_line3-1 {
  height: calc(100% - 4px);
  font-size: 15px;
  line-height: 1.3;
  border-radius: 3px;
  float: left;
  width: 27%;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  text-align: center;
  font-family: 'LABDigital';
}

.pipe_left_line3-3 {
  height: calc(100% - 4px);
  font-size: 15px;
  line-height: 1.3;
  border-radius: 3px;
  float: right;
  width: 27%;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  text-align: center;
  font-family: 'LABDigital';
}

.pipe_center {
  width: 14%;
  background: url(@/assets/img/ai_song/tank.png) no-repeat;
  background-size: 100% 100%;
  background-position: -6px 0px;
}

.pipe_right_water {
  width: 12%;
  margin-left: 1%;
  height: calc(92% - 10px);
}

.pipe_right_wrap {
  width: 20%;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.pipe3_wrap {
  height: calc(100% / 3);
}

.pipe_right_line1 {
  height: 40%;
  width: 100%;
  color: #fff;
  line-height: 1.5;
  font-family: 'KHNPHDRegular';
  font-size: 14px;
  margin-right: 770%;
  margin-top: 4px;
  text-shadow: 0 0 9px #5cafff;
  color: #c3eaff;
}

.pipe_right_line2 {
  height: 30%;
  width: 60%;
  font-size: 15px;
  line-height: 1.3;
  text-align: right;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  padding-right: 10px;
  border-radius: 3px;
  font-family: 'LABDigital';
}

.pipe2_background {
  height: calc(100% / 14 + 100% / 14);
  background: url(@/assets/img/ai_song/two_pump.png) no-repeat;
  background-size: 100% 100%;
}

.pipe3_background {
  height: calc(100% / 14 + 100% / 14 + 100% / 14);
  background: url(@/assets/img/ai_song/two_pump.png) no-repeat;
  background-size: 100% 100%;
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
  backdrop-filter: blur(7px) brightness(0.3)
}
</style>
