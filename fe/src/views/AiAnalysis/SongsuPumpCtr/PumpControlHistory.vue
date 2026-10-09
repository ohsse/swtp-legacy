<template>
    <div class="container-fluid">
        <b-row>
            <b-col xl="auto">
                <BigTitle :title="'송수펌프 제어 이력'"></BigTitle>
            </b-col>
            <b-col xl="auto" style="margin-top: 15px;">
                
                <MenuTab v-if="this.$area !== 'gosan'" @changeData="changeData" />
                <button v-else
                :class="{ 'custom-button': true}">
                    통합송수펌프
                </button>
            </b-col>
        </b-row>
        <div class="contents-container">
            <div class="div-big2" style="height: 98%; width: 100%; margin-top: 1rem;">
                <!-- 캘린더 영역 -->
                <div
                    style="display: inline-flex; height: 60px; width: 100%; padding: 0px 26px; justify-content: center; align-items: center; margin-top: 8px;">
                    <div
                        style="display: flex; flex-direction: row; align-items: center; width: 100%; gap: 1rem; justify-content: flex-end;">
                        <b-form-radio-group
                        v-model.number="dateRangeType"
                        :options="rangeOptions"
                        name="date-range-radios"
                        class="mb-2"
                        />
                        <CalendarBox @chartData="chartData" :isSelected="true" :dayAgo="dateRangeType" />
                    </div>
                </div>
                <SmallTitle :title="'AI 운영 현황'" />
                <div style="width: 100%; height: 365px; padding: 2rem;">
                     <b-row class="h-100">
                        <b-col class="h-100" xl="7">
                            <area-chart ref="AreaChart" style="width: 100%; height: 100%;"/>
                        </b-col>
                        <b-col class="h-100" xl="5">
                            <div class="custom-grid">
                                <div class="cell">전체</div>
                                <div class="cell cellVal">{{ count.total || 0 }}</div>
                                <div class="cell"></div>
                                <div class="cell">AI</div>
                                <div class="cell cellVal">{{ count.ai || 0 }}</div>
                                <div class="cell cellVal">{{ count.aiPer || 0 }} %</div>
                                <div class="cell">AI추천</div>
                                <div class="cell cellVal">{{ count.recom || 0 }}</div>
                                <div class="cell cellVal">{{ count.recomPer || 0 }} %</div>
                                <div class="cell">AI분석</div>
                                <div class="cell cellVal">{{ count.anal || 0 }}</div>
                                <div class="cell cellVal">{{ count.analPer || 0 }} %</div>
                            </div>
                        </b-col>
                    </b-row>
                </div>
                <!-- 캘린더 영역 -->
                <!-- Table 영역 -->
                <SmallTitle :title="'제어 이력'" />
                <!-- 군산: 송신 이력(대기열)과 5분 제어 판단 이력을 같은 자리에서 전환 -->
                <div v-if="$area === 'gunsan'" style="padding: 0 2rem;">
                    <b-form-radio-group v-model="historyView" :options="historyViewOptions"
                        name="history-view-radios" buttons button-variant="outline-primary" size="sm" />
                </div>
                <div style="width: 100%; height: 300px; padding: 2rem;">
                    <historyTable v-show="historyView === 'send'" ref="historyTable" />
                    <ctrlCmdHistoryTable v-if="$area === 'gunsan'" v-show="historyView === 'judge'"
                        ref="ctrlCmdHistoryTable" />
                </div>
                <!-- Table 영역 -->
            </div>
        </div>
    </div>
</template>

<script>
import historyTable from "@/views/AiAnalysis/SongsuPumpCtr/PumpControlHistory/ControlHistory_list.vue"
import ctrlCmdHistoryTable from "@/views/AiAnalysis/SongsuPumpCtr/PumpControlHistory/CtrlCmdHistory_list.vue"
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"
import CalendarBox from '@/components/ComponentCommon/CalendarBoxHistory.vue';
import MenuTab from '@/views/Common/MenuTab.vue';
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
import AreaChart from "@/components/Chart/AreaChart.vue";
import BarChartClass from "@/components/Chart/BarChartClass.js"
import axios from 'axios'
export default {
    components: {
        historyTable, ctrlCmdHistoryTable, BigTitle, CalendarBox,MenuTab,
        SmallTitle, AreaChart
    },
    data() {
        return {
            dateFrom: null,
            dateTo: null,
            selected: 'time',
            datas: [],
            intervalId: null,
            pump_grp : 1,
            chartLabel : ['AI', 'AI 추천', 'AI 분석'],
            chartDataArray : [0 , 0, 0],
            count:{
                total : 0,
                ai : 0,
                aiPer : 0,
                recom : 0,
                recomPer : 0,
                anal : 0,
                analPer :0
            },
            historyView: 'send',
            historyViewOptions: [
                { value: 'send', text: '송신 이력' },
                { value: 'judge', text: '제어 판단 이력' }
            ],
            dateRangeType: 7,   // 기본값: 7일
            rangeOptions: [
                { value: 7, text: '7일' },
                { value: 30, text: '30일' },
                { value: 365, text: '1년' }
            ],
            
        }
    },
    watch: {
        
    },
    mounted() {
        this.setInterval();
        this.$emit("onChangeBgClass", false);
    },
    beforeUnmount() {
        if (this.intervalId) {
            clearInterval(this.intervalId)
        }
    },
    methods: {
        changeData(index){
            this.pump_grp = index+1;   

            this.getData();
        },
        async getData() {
            const params = {
                startDate: this.dateFrom,
                endDate: this.dateTo,
                offset: 0,
                pump_grp: this.pump_grp
            }
            const apiURL = this.$apiURL;
            const res = await axios.get(`${apiURL}/ai/selectPumpCtrHistoryList`, { params })
            const res2 = await axios.get(`${apiURL}/ai/getAiModeCount`, { params })
            const data = res.data.data
            const countData = res2.data.data
            
            
            this.chartDataArray = [countData.ai, countData.recom, countData.anal];
            this.count.total = countData.total || 0;
            this.count.ai    = countData.ai    || 0;
            this.count.recom = countData.recom || 0;
            this.count.anal  = countData.anal  || 0;

            const t = this.count.total || 1; // 0으로 나누는 것 방지

            this.count.aiPer    = t === 0 ? 0 : Math.round((this.count.ai    / t) * 1000) / 10;
            this.count.recomPer = t === 0 ? 0 : Math.round((this.count.recom / t) * 1000) / 10;
            this.count.analPer  = t === 0 ? 0 : Math.round((this.count.anal  / t) * 1000) / 10;
            this.initChart(this.chartDataArray, this.chartLabel)
            // 배열 초기화
            this.datas = []
            this.$refs.historyTable.setData([...this.datas])
            if (data != null) {
                for (let i = 0; i < data.length; i++) {
                    this.datas.push({
                        ORDER_TIME: data[i]?.ORDER_TIME,
                        PUMP_NM: data[i]?.PUMP_NM,
                        TAG: data[i]?.TAG,
                        ANLY_CD: data[i]?.ANLY_CD,
                        FLAG: data[i]?.FLAG,
                        UPDT_TIME: data[i]?.UPDT_TIME,
                        AI_STATUS: data[i]?.AI_STATUS,
                    })
                }
            }
            this.$refs.historyTable.setData([...this.datas])
            if (this.$area === 'gunsan') {
                await this.getCtrlCmdHistory()
            }
        },
        // 군산 5분 제어 판단 이력 (TB_CTRL_CMD_RST + 처리 추적). 명령이 있는 판단만 본다
        async getCtrlCmdHistory() {
            try {
                const params = {
                    from: `${this.dateFrom} 00:00:00`,
                    to: `${this.dateTo} 23:59:59`,
                    cmdOnly: 'Y'
                }
                const res = await axios.get(`${this.$apiURL}/ai/ctrl/history`, { params })
                this.$refs.ctrlCmdHistoryTable?.setData(res.data?.data || [])
            } catch (e) {
                this.$refs.ctrlCmdHistoryTable?.setData([])
            }
        },
        chartData(dateFrom, dateTo, selected) {
            this.dateFrom = dateFrom
            this.dateTo = dateTo
            this.selected = selected
            this.getData()
            this.setInterval();
        },
        setInterval() {
            const todayString = new Date(new Date().getTime() + 9 * 60 * 60 * 1000).toISOString().split("T")[0];
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }
            this.intervalId = setInterval(() => {
                if (this.dateFrom === todayString && this.dateTo === todayString) {
                    this.getData()
                } else {
                    clearInterval(this.intervalId);
                    this.intervalId = null;
                
                }
            }, 60000);
          
        },
        initChart(datas, labels) {
            if (datas && labels) {
                let barChart = new BarChartClass(datas, labels);
                barChart.axisChange("y");
                barChart.toggleDataLabels('right')
                barChart.setGridSize('10%', '10%', '10%', '10%')
                this.$refs.AreaChart.changeData(barChart);
            } else {
                this.$refs.AreaChart.changeData();
            }

        }
    },

}

</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.contents-container {
    height: 93%;
    width: 100%;
}
.custom-button {
    width: 120px;
    height: 40px;
    align-self: center;
    border: solid 1px #b4dffa;
    background-color: rgb(67, 91, 121);
    border: 1px solid rgb(168, 210, 236, 1);
    color: white;
    cursor: pointer;
    border-radius: 4px;
    margin-left: 20px;
    text-shadow: 0 0 9px #5cafff;
    font-family: 'KHNPHDBold';
    font-weight: normal;
}
.div-new {
    background-image: url(/src/assets/img/div_new.png);
    background-size: 100% 100%;
    display: inline-block;
}

.top_textinput {
    height: 85%;
    width: 100%;
    display: inline-block;
    border: 1px solid #489cf2;
    background-color: #15284e;
    color: #fff;
    font-family: KHNPHDRegular;
    font-size: 14px;
    text-align: center;
    letter-spacing: 4px;
    border-radius: 5px;
}

.searchTag1 {
    height: 36%;
    margin-left: 12px;
}

.searchBox {
    display: flex;
    height: 100%;
    flex-direction: column;
    justify-content: center;
}

.search_btn_font {
    text-shadow: 0 0 9px #5cafff;
    font-size: 17px;
    letter-spacing: normal;
    color: #fff;
    font-family: KHNPHDRegular;
    text-align: center;
    line-height: 2;
}

.search_btn {
    width: 80px;
    align-self: center;
    border: solid 1px #b4dffa;
    background-color: rgba(139, 194, 240, 0.25);
    cursor: pointer;
    border-radius: 4px;
    align-items: center;
    justify-content: center;
    display: flex;
}
.custom-grid {
  display: grid;
  grid-template-columns: 20% 40% 40%;
  grid-template-rows: repeat(4, 1fr);
  height: 100%;
  width: 100%;
  gap: 0; /* 셀 사이 간격 제거 */
  border: 1px solid #fff; /* 전체 외곽선(흰색) */
  background: transparent;
}
.cell {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  height: 100%;
  font-size: 1.7rem;
  /* border: none; → 아래에서 개별적으로 지정 */
}

/* 세로선(가로줄 오른쪽, 마지막 열은 제외) */
.cell:not(:nth-child(3n)) {
  border-right: 1px solid #fff;
}
/* 가로선(세로줄 아래, 마지막 행은 제외) */
.cell:not(:nth-last-child(-n+3)) {
  border-bottom: 1px solid #fff;
}

.cellVal{
    font-size: 2rem;
}
.custom-radio .custom-control-input:checked ~ .custom-control-label {
  color: #228be6;
  font-weight: bold;
}
</style>