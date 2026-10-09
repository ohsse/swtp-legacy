<template>
    <SmallTitle :title="'조합 설정'" />
    <b-row class="mt-3" :style="{ height: '300px' }">
        
            <b-col cols="12">
                <b-row class="gx-2 d-flex justify-content-center flex_center" style="flex-wrap: nowrap; max-width: 100%;"
                >
                    <template v-if="dataLoad" >
                        <PumpBox ref="pumpData" @update-data="handleUpdateData" @pumpData="setPumpData" v-for="item in tabData" :key="item" :pump="item" style="min-width: 150px; flex: 0 0 auto;"/>
                    </template>
                </b-row>
            </b-col>
        
        <!-- //row -->
    </b-row>
</template>
<script>
import PumpBox from './PumpBox.vue';
import { fetchFunc } from '@/util/fetchFunc';
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
export default {
    components: {
        PumpBox,
        SmallTitle
    },
    props: {
        selectedItem: {
            type: Object,
            required: false,
            default: null
        }
    },
    data() {
        return {
            pumpData: [],
            select: 'user',
            updatePumpData: [],
            pump: [],
            pumpLength: {},
            alertMsg: '',
            dataLoad: false,
            tabData: [],
            applyPump : null,
            nowCount : 0
        }
    },
    watch: {
    // selectedItem prop의 변화를 감지
        async selectedItem(newItem) {

            // 새로 전달된 newItem이 존재하는 경우 API 호출
            if (newItem) {
                
                this.pumpTab = new Set()
                const apiURL = this.$apiURL;
                this.tabData = (await fetchFunc(`${apiURL}/dr/getPumpCombinationItem/${newItem.PUMP_GRP}/${newItem.PUMP_COUNT}/${newItem.PUMP_PRIORITY}`)).data;
                this.dataLoad = true;
                this.firstCombination(this.tabData);
                this.lastCombination(this.tabData)
                    
                
            }
        }
    },
    methods: {
        handleUpdateData(data) {
            
            this.tabData.forEach((item) => {
                if (item.PUMP_IDX === data.pump) {
                    item.PUMP_YN = data.use_yn;  // PUMP_YN을 use_yn 값으로 변경
                }
            });

            
            this.lastCombination(this.tabData)
        },
        setPumpData(data) {
            // 자식 컴포넌트에서 전달된 데이터 처리


            // 필요하다면 데이터 상태 업데이트
            this.pumpData.push(data);
        },
        lastCombination(pump){
            this.nowCount = 0;
            this.applyPump = null;
            this.applyPump = pump
                .filter(element => element.PUMP_YN === 1)  // PUMP_YN이 1인 요소 필터링
                .map(element => {
                    this.nowCount += element.PUMP_SIZE;    // PUMP_SIZE 값을 nowCount에 더하기
                    return `#${element.PUMP_GRP_IDX}`;         // PUMP_IDX 앞에 # 붙이기
            })
            .join(" ");
            this.$emit('changePump', { applyPump: this.applyPump, nowCount: this.nowCount });
        },
        firstCombination(pump){
            let firstCount = 0;
            
            const firstPump = pump
                .filter(element => element.PUMP_YN === 1)  // PUMP_YN이 1인 요소 필터링
                .map(element => {
                    firstCount += element.PUMP_SIZE;    // PUMP_SIZE 값을 nowCount에 더하기
                    return `#${element.PUMP_GRP_IDX}`;         // PUMP_IDX 앞에 # 붙이기
            })
            .join(" ");
            this.$emit('firstPump', { firstPump: firstPump, firstCount: firstCount });
        },
        getTabData(){
            this.$emit('setTabData',{tabData:this.tabData})
        },
        /**
         * 적용 클릭 시 발생 함수(우선순위 인지 운영자인지 판별해 다음 함수 호출)
         */
        async save() {
            
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
</style>
