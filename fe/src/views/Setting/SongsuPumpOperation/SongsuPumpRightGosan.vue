<template>
    <b-row>
        <b-col xl="12">
            <b-row>
                <b-col xl="11" class="p-0">
                    <SmallTitle :title="'적용 결과'" />
                </b-col>
                <b-col xl="1" class="p-0">
                    <b-button @click="save" id="btnSave" variant="secondary"
                        class="season_btn season_btn_font fs-6 px-3 float-end"
                        :style="{ height: '40px' }"><span>적용</span></b-button>
                </b-col>
            </b-row>
        </b-col>
        <b-col xl="5">
            <b-row style="margin-bottom: 10px; padding: 0 10px;">
                <div class="text_title_base" :style="{ width: '100%' }">
                    <div class="w-100 d-flex flex_center_between" :style="{ height: '60px' }">
                        <div class="content__text-box_comb text-center">현재 조합</div>
                        </div>
                        <div class="w-100 d-flex flex_center_between" :style="{ height: '70px' }">
                        <div class="animationTItle-two" :style="{ height: '60%', color: '#5cebfe', 'font-size':'2.5rem' }">
                            {{ firstPump }}
                        </div>
                    </div>
                </div>
            </b-row>
            <b-row class="mt-1 d-flex justify-content-center flex_center fontContent text-center" >
                <b-row class="d-flex justify-content-center flex_center fontContent text-center align-items-center" style="text-align: center; font-size: 1.4em;">
                    <b-col xl="5" class="cal_tite_text">
                    적용 대수
                    </b-col>
                    <b-col xl="6" class="detail_value"
                    :style="{ width: 'auto', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">
                        {{ selectCount }}
                    </b-col>
                </b-row>
                <b-row class="d-flex justify-content-center flex_center fontContent text-center align-items-center" style="text-align: center; font-size: 1.4em;">
                    <b-col xl="5" class="cal_tite_text">
                    현재 전력원단위
                    </b-col>
                    <b-col xl="5" class="detail_value"
                    :style="{ width: 'auto', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">
                    {{ selectPwrUnit }}
                        
                    </b-col>
                    <b-col xl="2" :style="{ color: '#3789b4', fontSize: '0.85rem', fontWeight: 'bold' }">
                        (kWh/㎥)
                    </b-col>
                </b-row>
            </b-row> 
                <!-- 구분선 추가 -->
            <b-row class="">
                <hr style="border-top: 2px solid #cccccc; width: 100%; margin: 10px 0;" />
            </b-row>
            <b-row class="" style="margin-bottom: 10px; padding: 0 10px;">
                <div class="text_title_base" :style="{ width: '100%' }">
                    <div class="w-100 d-flex flex_center_between" :style="{ height: '60px' }">
                        <div class="content__text-box_comb text-center">변경 조합</div>
                        </div>
                        <div class="w-100 d-flex flex_center_between" :style="{ height: '70px' }">
                        <div class="animationTItle-two" :style="{ height: '60%', color: '#ffff99', 'font-size':'2.5rem' }">
                            {{ applyPump }}
                        </div>
                    </div>
                </div>
            </b-row>
            <b-row class="mt-1 d-flex justify-content-center flex_center fontContent text-center" style="text-align: center;">
                <b-row class="d-flex justify-content-center flex_center fontContent text-center align-items-center" style="text-align: center; font-size: 1.4em;">
                    <b-col xl="5" class="cal_pre_tite_text">
                        변경 대수
                    </b-col>
                    <b-col xl="6" class="detail_value"
                    :style="{ width: 'auto', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">
                        {{ nowCount }}
                    </b-col>
                </b-row>
                <b-row class="d-flex justify-content-center flex_center fontContent text-center align-items-center" style="text-align: center; font-size: 1.4em;">
                    <b-col xl="5" class="cal_pre_tite_text">
                        변경 전력원단위
                    </b-col>
                    <b-col xl="5" class="detail_value"
                    :style="{ width: 'auto', textShadow: 'rgb(255, 255, 255) 0px 0px 3px' }">
                        {{ chagePwrUnit }}
                        
                    </b-col>
                    <b-col xl="2" :style="{ color: '#3789b4', fontSize: '0.85rem', fontWeight: 'bold' }">
                        (kWh/㎥)
                    </b-col>
                </b-row>
            </b-row> 
        </b-col>
        <b-col xl="7" style=" height: 460px">
            <ScatterChart ref="ScatterChart"/>
        </b-col>
    </b-row>


</template>
<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
import ScatterChart from '@/components/Chart/ScatterChart.vue'
import ScatterChartClass from '@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/ScatterChartClass'
import { fetchFunc } from '@/util/fetchFunc';
export default {
    components :{
        SmallTitle,
        ScatterChart
    },
    props: {
        applyPump: {
            type: String,
            required: true
        },
        nowCount: {
            type: Number,
            required: true
        },
        firstPump: {
            type: String,
            required: true
        },
        firstCount: {
            type: Number,
            required: true
        },
        selectCount: {
            type: Number,
            required: true
        },
        selectedItem: {
            type: Object,
            required: false,
            default: null
        },
        pump_grp:{
            type: Number,
            required: false,
            default: null
        }
    },
    data(){
        return{
            calList:[],
            calData:[],
            activeIndex:null,
            stringComb:null,
            pwiPumpUnit :{
            },
            pwiGrpUnit : {
            },
            combList:[],
            grpFlowPressure :{},
            basePwr:0,
            selectPwr:0,
            changePwr:0,
            selectPwrUnit:0,
            chagePwrUnit:0,
            allFlow:0
        }
    },
    watch: {
    // selectedItem prop의 변화를 감지
        async selectedItem(newItem) {
            if (newItem) {
                this.selectPwr = 0;
                this.combList = new Array();
                this.pumpTab = new Set();
                const apiURL = this.$apiURL;
                const calOrigin = (await fetchFunc(`${apiURL}/dr/getGroupPumpCal/${newItem.PUMP_GRP}/${newItem.PUMP_COUNT}/${newItem.PUMP_PRIORITY}`)).data;
                this.calData = calOrigin;
                this.calList = calOrigin.filter(item => item.C_ORD === 1 && item.USE_YN === 1);


                // 선택된 PWR 값 계산
                this.calList.forEach(item => {
                    const numberList = item.PUMP_COMB.split(',').map(Number);
                    numberList.forEach(element => {
                        this.selectPwr += this.pwiPumpUnit[this.pump_grp][element];
                    });
                    this.stringComb = this.formatString(item.PUMP_COMB);
                });
                
                // BasePwr 추가
                this.selectPwr += this.basePwr;

                // allFlow가 0이 아닌 경우에만 selectPwrUnit 계산
                if (this.allFlow > 0) {
                    this.selectPwrUnit = (this.selectPwr / this.allFlow).toFixed(3);
                } else {
                    this.selectPwrUnit = 0; // 기본값 설정
                }

                const filteredData = calOrigin.filter(item => item.C_ORD === 1);

                // combList 구성
                filteredData.forEach(item => {
                    const numberList = item.PUMP_COMB.split(',').map(Number);
                    this.combList.push(numberList);
                });

                this.dataLoad = true;

                let ChartClass = new ScatterChartClass(null, this.stringComb, this.calData, true, true, true, 3);

                this.$nextTick(() => {
                    this.$refs.ScatterChart.changeData(ChartClass);
                });
            }
        },
        async pump_grp(newVal) {
            await this.handlePumpGrpChange(newVal);

            // handlePumpGrpChange 후 데이터 준비 확인
            if (this.allFlow > 0) {
                this.selectPwrUnit = (this.selectPwr / this.allFlow).toFixed(3);
            } else {
                this.selectPwrUnit = 0; // 기본값 설정
            }
        },
        applyPump(){
            this.calculateChangePwrUnit();
        }
    },
    mounted(){
         this.getPwrCalValue();
        // 기존 mounted 로직 유지
        if (this.pump_grp) {
            this.handlePumpGrpChange(this.pump_grp).then(() => {
                if (this.allFlow > 0) {
                    this.selectPwrUnit = (this.selectPwr / this.allFlow).toFixed(3);
                }
            });
        }

        // applyPump 초기값으로 chagePwrUnit 계산
        if (this.applyPump) {
            this.calculateChangePwrUnit(this.applyPump);
        }
    },
    methods:{
        async getPwrCalValue(){
            const apiURL = this.$apiURL;
            
            const pumpVal = await fetchFunc(`${apiURL}/dr/getPumpPwrVal`);
            // 받아온 데이터를 상태 변수에 반영
            
            if (this.$area === 'gosan') {
                // 모든 값(flatten) 합치기
                const merged = {};
                Object.values(pumpVal.data).forEach(obj => {
                    Object.entries(obj).forEach(([k, v]) => {
                        merged[k] = v;
                    });
                });
                this.pwiPumpUnit = { "0": merged };
            } else {
                this.pwiPumpUnit = pumpVal.data;
            }
            
            const grpCal = await fetchFunc(`${apiURL}/dr/getPumpPwrCal`);
            // 받아온 데이터를 상태 변수에 반영
            this.pwiGrpUnit = grpCal.data;

            
        },
        calculateChangePwrUnit() {
            this.changePwr = 0; // 초기화
            const numberList = this.applyPump
                .split('#') 
                .filter(Boolean) 
                .map(item => Number(item.trim())); 

            
            const pumpMap = this.pwiPumpUnit[this.pump_grp];

            if (!pumpMap) {
                // 데이터가 준비 안 됐으면 계산하지 않고 종료 (혹은 기본값)
                this.chagePwrUnit = 0;
                return;
            }

            // PWR 계산
            numberList.forEach(element => {
                this.changePwr += this.pwiPumpUnit[this.pump_grp][element];
            });
            this.changePwr += this.basePwr;

            // chagePwrUnit 계산
            if (this.allFlow > 0) {
                this.chagePwrUnit = (this.changePwr / this.allFlow).toFixed(3);
            } else {
                this.chagePwrUnit = 0; // 기본값 설정
            }
        },
        save(){
            this.$emit('save', this.combList)
        },
        toggleActive(index, item) {
            if (this.activeIndex !== index) {
                this.activeIndex = index;
            }
            this.stringComb = item.outputComb

            

        },
        formatString(input) {

            // 입력 문자열을 ','로 나누어 배열로 변환
            let numbers = input.split(",");
            
            // 각 요소에 '#'을 추가하고 다시 문자열로 합치기
            let formatted = numbers.map(num => `#${num.trim()}`).join(", ");
            
            return formatted;
        },
        async handlePumpGrpChange(pump_grp){
            this.basePwr = 0;
            this.allFlow = 0;
            const apiURL = this.$apiURL;
            const grpData = (await fetchFunc(`${apiURL}/dr/getGrpFlowPressure/${pump_grp}`)).data;
            const keys = Object.keys(grpData).map(key => Number(key));

            keys.forEach(element => {
                const setGrpData = grpData[element];
                const flow = setGrpData["flow"];
                this.allFlow += flow;
                const pressure = setGrpData["pressure"];
                const setGrpDefaultValue = this.pwiGrpUnit[element] 
                const defaultFlow = setGrpDefaultValue["prdctPwrFlow"]
                const defaultPressure = setGrpDefaultValue["prdctPwrPress"]
                const defaultNum = setGrpDefaultValue["prdctPwrDefault"]
                

                this.basePwr += (defaultFlow * flow) + (defaultPressure * pressure) + defaultNum
                
            });
            

            this.calculateChangePwrUnit();
            
        }
    }
}
</script>
<style scoped>
.season_btn {
    height: 33px;
    padding-top: 3px;
    padding-bottom: 3px;
    border: solid 1px #b4dffa;
    background-color: rgba(139, 194, 240, 0.25);
}

.box-bg-big {
    padding: 10px;
    background: url(@/assets/img/box_bg_big.png) no-repeat;
    background-size: 100% 100%;
}



.div_box_title_border {
    background: #067be6cc;
    border: 3px solid #0cc7f7b0;
    box-shadow: 0 0 5px #0cc7f7b0;
    justify-content: center;
    text-indent: 0;
    border-radius: 5px;
}

.div_box_border {
    border: 1px solid #489cf2d1;
    box-shadow: 0 0 3px #489cf2;
    background-color: #0947ae66;
    border-radius: 5px;
}
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
.text_title_base2 {
    background: linear-gradient(to right, rgba(139, 194, 240, 0) 20%, rgba(139, 194, 240, 0.25) 50%, rgba(139, 194, 240, 0) 80%);
    background-color: rgba(139, 194, 240, 0); /* fallback color for browsers that don’t support gradients */
    background-size: 100% 100%;
    text-align: center;
}

.content__text-box {
  width: 100%;
  background-size: 100% 20px;
  background-position-y: bottom;
  text-shadow: 0 0 9px #5cafff;
  font-family: KHNPHUotfR;
  font-size: 26px;
  line-height: 1.5;
  text-align: left;
  color: #fff;
}

.season_btn {
    height: 33px;
    padding-top: 3px;
    padding-bottom: 3px;
    border: solid 1px #b4dffa;
    background-color: rgba(139, 194, 240, 0.25);
}
.cal_tite_text {
  text-shadow: 0 0 9px #5cafff;
  
  font-family: KHNPHDRegular;
  letter-spacing: normal;
  color: #c3eaff;
  /* line-height: 63px; */
  font-weight: bold;
}
.cal_pre_tite_text {
  text-shadow: 0 0 9px #ffff99;
  
  font-family: KHNPHDRegular;
  letter-spacing: normal;
  color: #ececd0;
  /* line-height: 63px; */
  font-weight: bold;
}
.text_title_base {
  /*
	width: 65%;
	height: 78%;
	display: flex;
	flex-direction: column;
    */
  background: url(@/assets/img/peakcontrol/texttitle_based.png) no-repeat;
  background-size: 100% 100%;
  text-align: center;
}

.content__text-box_comb {
  width: 100%;
  background-size: 100% 20px;
  background-position-y: bottom;
  text-shadow: 0 0 9px #5cafff;
  font-family: KHNPHUotfR;
  font-size: 1.7rem;
  line-height: 1.5;
  text-align: left;
  color: #fff;
}
</style>