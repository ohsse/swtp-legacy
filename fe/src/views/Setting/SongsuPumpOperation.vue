<template>
  <div class="container-fluid">
    <!-- 템플릿 내용 -->
    <!-- 타이틀 -->
    <b-row>
      <b-col xl="auto">
        <BigTitle :title="'송수펌프 운영'"></BigTitle>
      </b-col>
      <b-col xl="auto" style="margin-top: 15px;">
        
        <MenuTab v-if="this.$area !== 'gosan'" @changeData="changeData" />
        <button v-else
        :class="{ 'custom-button': true}">
            통합송수펌프
        </button>
      </b-col>
    </b-row>
    <!-- //타이틀 -->
    <!-- 본문 컨텐츠 -->
    <div class="contents-container">
      
        
            <b-row style="width: 100%; height: 98%; margin-top: 15px">
                <b-row style="margin-bottom: 30px;">
                    <b-col class="area" xl="5" style="padding-right : 15px ; ">
                        <SmallTitle :title="'조합 목록'" />
                        <b-list-group class="list-custom-group left_bg fontContent d-flex align-items-center"
                        v-bind:style="{ height: '460px', overflowY: 'scroll', width: '100%' }">

                            <!-- 리스트 항목 반복 -->
                            <b-list-group-item v-for="(item, index) in this.combList" :key="index" :class="{ active: activeIndex === index }" class="my-2"
                                @click="toggleActive(index, item)" 
                                v-bind:style="{ width: '93%' }">
                                <b-row class="align-items-center text-center px-2">
                                    <b-col xl="3" class="text-center d-flex justify-content-center align-items-center">
                                        {{ item.PUMP_COUNT }}대
                                    </b-col>
                                    <b-col xl="5" class="text-center d-flex justify-content-center align-items-center">
                                        {{ item.COMB_NAME }}
                                    </b-col>
                                    <b-col xl="2" class="text-center d-flex justify-content-center align-items-center">
                                        {{ item.PUMP_PRIORITY }} 순위
                                    </b-col>
                                    
                                    <b-col xl="2" class="text-center d-flex justify-content-center align-items-center">
                                        <!-- SVG 요소가 item.PUMP_PRIORITY_DCS가 없거나 비어있을 때만 보이도록 v-if 적용 -->
                                        
                                        <svg 
                                            v-if="item.PUMP_PRIORITY_DCS !== null && item.PUMP_PRIORITY_DCS !== ''"
                                            id="info-icon"
                                            width="22"
                                            height="22"
                                            viewBox="0 0 22 22"
                                            xmlns="http://www.w3.org/2000/svg"
                                            class="hover-blue"
                                            @click="info(item)"
                                    
                                        >
                                            <path d="M11 16.75C11.1989 16.75 11.3897 16.671 11.5303 16.5303C11.671 16.3897 11.75 16.1989 11.75 16V10C11.75 9.80109 11.671 9.61032 11.5303 9.46967C11.3897 9.32902 11.1989 9.25 11 9.25C10.8011 9.25 10.6103 9.32902 10.4697 9.46967C10.329 9.61032 10.25 9.80109 10.25 10V16C10.25 16.414 10.586 16.75 11 16.75ZM11 6C11.2652 6 11.5196 6.10536 11.7071 6.29289C11.8946 6.48043 12 6.73478 12 7C12 7.26522 11.8946 7.51957 11.7071 7.70711C11.5196 7.89464 11.2652 8 11 8C10.7348 8 10.4804 7.89464 10.2929 7.70711C10.1054 7.51957 10 7.26522 10 7C10 6.73478 10.1054 6.48043 10.2929 6.29289C10.4804 6.10536 10.7348 6 11 6Z" />
                                            <path fill-rule="evenodd" clip-rule="evenodd" d="M0.25 11C0.25 5.063 5.063 0.25 11 0.25C16.937 0.25 21.75 5.063 21.75 11C21.75 16.937 16.937 21.75 11 21.75C5.063 21.75 0.25 16.937 0.25 11ZM11 1.75C8.54675 1.75 6.19397 2.72455 4.45926 4.45926C2.72455 6.19397 1.75 8.54675 1.75 11C1.75 13.4533 2.72455 15.806 4.45926 17.5407C6.19397 19.2754 8.54675 20.25 11 20.25C13.4533 20.25 15.806 19.2754 17.5407 17.5407C19.2754 15.806 20.25 13.4533 20.25 11C20.25 8.54675 19.2754 6.19397 17.5407 4.45926C15.806 2.72455 13.4533 1.75 11 1.75Z" />
                                        </svg>
                                        
                                    </b-col>

                                    
                                    
                                 
                                </b-row>
                            </b-list-group-item>

                        </b-list-group>

                    </b-col>
                    <b-col xl="7">
                        <SongsuPumpRight @save="combSave"
                        :applyPump="applyPump" :nowCount="nowCount" :selectCount="selectCount"/>
                    </b-col>
                </b-row>
                <b-row>
                    <b-col class="area" xl="12">
                        <SongsuPumpBottomVue @changePump="handleUpdateData" :selectedItem="selectedItem"
                        @setTabData="settingData"
                        ref="pumpBottom"
                        />
                    </b-col>
                </b-row>                    
            </b-row>
        
    </div>
    <optionVue/>
  </div>
</template>
<script>
    import BigTitle from '@/components/ComponentCommon/BigTitle.vue';
    import MenuTab from '@/views/Common/MenuTab.vue';
    import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
    import SongsuPumpBottomVue from '@/views/Setting/SongsuPumpOperation/SongsuPumpBottom.vue'
    import SongsuPumpRight from '@/views/Setting/SongsuPumpOperation/SongsuPumpRight.vue'
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
            
            swalInstance: null
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
            this.combList = (await fetchFunc(`${apiURL}/st/selectPumpCombList/${this.pump_grp}`)).data
            
            this.toggleActive(0,  this.combList[0]) 
            
        },
        toggleActive(index, item) {
            if (this.activeIndex !== index) {
                this.activeIndex = index;
            }
            
            // item 객체에 pump_grp 키를 추가하여 새로운 객체로 selectedItem에 할당
            this.selectedItem = { ...item, pump_grp: this.pump_grp };
            this.selectCount = this.selectedItem.PUMP_COUNT;
        },
        handleUpdateData(data){
            this.nowCount = data.nowCount;
            this.applyPump = data.applyPump;

            
        },
        async combSave(){
            await this.$refs.pumpBottom.getTabData();
            if(this.selectedItem.PUMP_COUNT == this.nowCount){
                if(this.$area === 'gosan'){
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

                    if (this.selectedItem.PUMP_COUNT === 4) {
                    
                        const matchingPumpSizeCount = this.tabData.filter(item => item.PUMP_SIZE === 0.5 && item.PUMP_YN === 1).length;

                        if(this.selectedItem.PUMP_PRIORITY == 1){
                            if (matchingPumpSizeCount > 0) {
                           
                           await Swal.fire({
                               animation : false,
                               text: "용량이 0.5인 펌프가 포함되면 안됩니다.",
                           })
                           
                           return;
                       }
                        }else if (this.selectedItem.PUMP_PRIORITY  == 2){
                            if (matchingPumpSizeCount !== 2) {
                           
                           await Swal.fire({
                               animation : false,
                               text: "용량이 0.5대인 펌프가 2대가 아닙니다.",
                           })
                           
                           return;
                       }
                        }
                       
                        
                    }
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
                    const requestOptions = {
                        method: 'POST',
                        headers: myHeaders,
                        body: JSON.stringify(this.tabData),
                    };
                    try {
                        const response = await fetch(`${apiURL}/st/savePumpComb`, requestOptions);
                        

                        if (response.ok) {
                            // 성공 시
                            await Swal.fire({
                                animation: false,
                                text: '저장되었습니다.',
                            });
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
.hover-blue {
  fill: white;
  transition: fill 0.3s ease;
}

.hover-blue:hover {
  fill: #007bff; /* 파란색으로 변경 */
}
</style>