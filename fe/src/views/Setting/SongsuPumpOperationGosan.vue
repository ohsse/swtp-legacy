<template>
    <div class="container-fluid">
        <!-- 템플릿 내용 -->
        <!-- 타이틀 -->
        <b-row>
            <b-col xl="auto">
                <BigTitle :title="'송수펌프 운영'"></BigTitle>
            </b-col>
            <b-col xl="auto" style="margin-top: 15px;">

                <MenuTab v-if="this.$area !== 'gosan' && this.$area !== 'goryeong'" @changeData="changeData" />
                <button v-else-if="this.$area == 'gosan'" :class="{ 'custom-button': true }">
                    통합송수펌프
                </button>
                <button v-else-if="this.$area == 'goryeong'" :class="{ 'custom-button': true }">
                    생활정수지
                </button>
            </b-col>
        </b-row>
        <!-- //타이틀 -->
        <!-- 본문 컨텐츠 -->
        <div class="contents-container">


            <b-row style="width: 100%; height: 98%; margin-top: 15px">
                <b-row style="margin-bottom: 30px;">
                    <b-col class="area" xl="4" style="padding-right : 15px ; ">
                        <SmallTitle :title="'조합 목록'" />
                        <b-list-group class="list-custom-group left_bg fontContent d-flex align-items-center oper-list"
                            v-bind:style="{ height: '460px', overflowY: 'scroll', width: '100%', 'font-size': '1.0em' }">

                            <!-- 리스트 항목 반복 -->
                            <b-list-group-item v-for="(item, index) in this.combList" :key="index"
                                :class="{ active: activeIndex === index }" class="my-2"
                                @click="toggleActive(index, item)" v-bind:style="{ width: '93%' }">
                                <b-row class="align-items-center text-center px-2">
                                    <b-col xl="3" class="text-center d-flex justify-content-center align-items-center">
                                        {{ item.PUMP_COUNT }}대
                                    </b-col>
                                    <b-col xl="4" class="text-center d-flex justify-content-center align-items-center">
                                        {{ item.COMB_NAME }}
                                    </b-col>
                                    <b-col xl="2" class="text-center d-flex justify-content-center align-items-center">
                                        {{ item.PUMP_PRIORITY }} 순위
                                    </b-col>
                                    <b-col v-if="this.$area != 'goryeong'" xl="3"
                                        class="d-flex justify-content-center align-items-center div_box_border px-3 mb-2 text-nowrap">
                                        <b-form-select v-model="item.USE_YN" :options="selectOptions" size="sm"
                                            style="font-size: 1em;"></b-form-select>
                                    </b-col>



                                </b-row>
                            </b-list-group-item>

                        </b-list-group>

                    </b-col>
                    <b-col xl="8">
                        <SongsuPumpRight @save="combSave" :applyPump="applyPump" :nowCount="nowCount"
                            :selectCount="selectCount" :selectedItem="selectedItem" :firstPump="firstPump"
                            :firstCount="firstCount" :pump_grp="pump_grp" ref="pumpRight" />
                    </b-col>
                </b-row>
                <b-row>
                    <b-col class="area" xl="12">
                        <SongsuPumpBottomVue @changePump="handleUpdateData" :selectedItem="selectedItem"
                            @setTabData="settingData" @firstPump="setChangeFirstData" ref="pumpBottom" />
                    </b-col>
                </b-row>
            </b-row>

        </div>
        <optionVue />
    </div>
</template>
<script>
    import BigTitle from '@/components/ComponentCommon/BigTitle.vue';
    import MenuTab from '@/views/Common/MenuTab.vue';
    import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
    import SongsuPumpBottomVue from '@/views/Setting/SongsuPumpOperation/SongsuPumpBottom.vue'
    import SongsuPumpRight from '@/views/Setting/SongsuPumpOperation/SongsuPumpRightGosan.vue'
    import { fetchFunc } from '@/util/fetchFunc';
    import Swal from 'sweetalert2'
export default {
    components: {
        BigTitle,
        MenuTab,
        SmallTitle,
        SongsuPumpBottomVue,
        SongsuPumpRight
    },
    data(){
        return{
            combList:[],
            pump_grp: null,
            activeIndex: -1,
            selectedItem: null,
            applyPump : null,
            nowCount : null,
            selectCount : null,
            tabData : null,
            firstCount : null,
            firstPump : null,
            swalInstance: null,
            selectOptions: [
                { value: 1, text: "사용" },
                { value: 0, text: "미사용" },
            ],
            item:null
        }
    },
    mounted(){
        this.getCombList();
    },
    methods:{
        changeData(index){
            this.pump_grp = index+1;   

            this.getCombList()         ;
        },
        async getCombList(){
            const apiURL = this.$apiURL;
            if(this.pump_grp === null){
                if(this.$area === 'gosan'){
                    this.pump_grp = 0;
                }else{
                    this.pump_grp = 1;
                }
            }
            this.combList = (await fetchFunc(`${apiURL}/dr/selectPumpCombList/${this.pump_grp}`)).data
            
            this.toggleActive(0,  this.combList[0]) 
            
        },
        toggleActive(index, item) {
            if (this.activeIndex !== index) {
                this.activeIndex = index;
            }
            this.item = item;
            // item 객체에 pump_grp 키를 추가하여 새로운 객체로 selectedItem에 할당
            this.selectedItem = { ...item, pump_grp: this.pump_grp };
            this.selectCount = this.selectedItem.PUMP_COUNT;
        },
        handleUpdateData(data){
            this.nowCount = data.nowCount;
            this.applyPump = data.applyPump;

            
        },
        setChangeFirstData(data){
            this.firstCount = data.firstCount;
            this.firstPump = data.firstPump;

            
        },
        async combSave(){
            const area = this.$area;
            await this.$refs.pumpBottom.getTabData();
            
            if(this.selectedItem.PUMP_COUNT == this.nowCount){
                if(area === 'gosan'){
                    const range1to7Missing = !this.tabData.some(
                        item => item.PUMP_IDX >= 1 && item.PUMP_IDX <= 7 && item.PUMP_YN === 1
                    );

                    // 8~11 범위에서 PUMP_YN이 1인 항목이 없는지 확인
                    const range8to11Missing = !this.tabData.some(
                        item => item.PUMP_IDX >= 8 && item.PUMP_IDX <= 11 && item.PUMP_YN === 1
                    );
                    let msg;
                    // 결과 출력 또는 처리
                    if (range1to7Missing) {
                        msg = '(구)송수펌프를 선택해주세요.'
                    }
                    if (range8to11Missing) {
                        msg = '(신)송수펌프를 선택해주세요.'
                    }

                    if(range1to7Missing || range8to11Missing){
                        await Swal.fire({
                            animation : false,
                            text: msg,
                        })
                        
                        return;
                    }
                    // const pumpIdxArray = this.tabData
                    //     .filter(item => item.PUMP_YN === 1) // PUMP_YN이 1인 항목 필터링
                    //     .map(item => item.PUMP_IDX); // PUMP_IDX 값만 추출

                    // combList에 동일한 배열이 있는지 검사
                    // const isMatch = combList.some(combArray => {
                    //     // 두 배열이 같은 요소를 가지고 있는지 검사 (순서 무관)
                    //     return combArray.length === pumpIdxArray.length &&
                    //         combArray.every(value => pumpIdxArray.includes(value));
                    // });

                    // if(!isMatch){
                    //     await Swal.fire({
                    //         animation : false,
                    //         text: "해당 조합이 포함된 성능곡선이 없습니다.",
                    //     })
                        
                    //     return;
                    // }
                    
                }
                // else if(area === 'goryeong' && this.pump_grp == 1){
                //     let msg;
                //     const inverterFind = !this.tabData.some(
                //         item => item.PUMP_TYP === 2 && item.PUMP_YN === 1
                //     );
                //      if (inverterFind) {
                //         msg = '인버터 펌프를 선택해주세요.';
                //     }

                //     if(inverterFind){
                //         await Swal.fire({
                //             animation : false,
                //             text: msg,
                //         })
                        
                //         return;
                //     }
                // }
                const isBlock = this.combList.every(item => item.USE_YN === 0);
                if (isBlock) {
                        await Swal.fire({
                            animation : false,
                            text: "모든 조합이 미사용으로 지정돼 있습니다.",
                        })
                        
                        return;
                }
                const confirmed = await Swal.fire({
                    text: '적용 하시겠습니까?',
                    animation : false,
                    showCancelButton: true,
                    confirmButtonText: '적용',
                    cancelButtonText: '취소'
                });
                if (confirmed.isConfirmed) {
                    const myHeaders = new Headers();
                    myHeaders.append("Content-Type", "application/json");
                    const apiURL = this.$apiURL;
                    const requestOptions1 = {
                        method: 'POST',
                        headers: myHeaders,
                        body: JSON.stringify(this.tabData),
                    };
                    
                    
                    const requestOptions2 = {
                        method: 'POST',
                        headers: myHeaders,
                        body: JSON.stringify(this.combList),
                    };
                    try {
                        
                        
                        const response1 = await fetch(`${apiURL}/dr/savePumpComb`, requestOptions1);
                        
                        
                        const response2 = await fetch(`${apiURL}/dr/setPumpListYn`, requestOptions2);
                        if (response1.ok && response2.ok) {
                            // 성공 시
                            await Swal.fire({
                                animation: false,
                                text: '저장되었습니다.',
                            });
                            this.selectedItem = { ...this.item, pump_grp: this.pump_grp };
                        } else {
                            // 실패 시
                            await Swal.fire({
                                animation: false,
                                text: '서버 오류',
                            });
                        }
                    } catch (error) {
                        // 네트워크 오류 등 fetch 자체의 오류 처리
                        
                        await Swal.fire({
                            animation: false,
                            text: error,
                        });
                    }
                    
                }else {
                    await Swal.fire({
                        animation : false,
                        text: '저장이 취소되었습니다.',
                    })
                }
            }else{
                await Swal.fire({
                        animation : false,
                        text: '조합의 펌프 대수가 동일하지 않습니다',
                })
            }

        },
        settingData(data){
            this.tabData = data.tabData;
           
        },
        async info(data){           
            this.swalInstance = Swal.fire({
                title: data.COMB_NAME,
                html: `
                    <p>${data.PUMP_PRIORITY_DCS}</p>
                    <p style="color: gray; font-size: 0.9em;"">${data.PUMP_RULES}</p> <!-- 서브텍스트 추가 -->
                `,
                showConfirmButton: false,
                allowOutsideClick: false,
                showCancelButton: true,
                allowEscapeKey: false,
                cancelButtonText: '확인'
            });
        }
    }
}
</script>
<style scoped>
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
    cursor: default;
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
    background-color: rgba(139, 194, 240, 0);
    /* fallback color for browsers that don’t support gradients */
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

.hover-blue {
    fill: white;
    transition: fill 0.3s ease;
}

.hover-blue:hover {
    fill: #007bff;
    /* 파란색으로 변경 */
}

.b-form-select {
    display: inline-block;
    /* Prevent block-level behavior */
    width: auto;
    /* Adjust width to fit content */
    min-width: auto;
    max-width: 100%;
}

.list-custom-group.list-group .list-group-item.active {
    height: 12%;
    /* 높이를 콘텐츠에 맞춤 */
}
</style>