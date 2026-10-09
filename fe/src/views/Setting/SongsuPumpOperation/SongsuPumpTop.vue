<template>
    <!-- 펌프운영관리 -->
    <b-row :style="{height : '50%'}">
        <!-- 서브 타이틀 -->
        <b-row class="align-items-center" :style="{ margin: '15px 0px' }">
            <b-col xl="11" class="p-0">
                <SmallTitle :title="'펌프 운영 관리'"></SmallTitle>
            </b-col>
            <b-col xl="1" class="p-0">
                <b-button id="btnSave" @click="pumpOperUpdate" variant="secondary"
                    class="season_btn season_btn_font fs-6 px-3 float-end"
                    :style="{ height: '40px' }"><span>적용</span></b-button>
            </b-col>
        </b-row>
        <!-- //서브 타이틀 -->
        <!-- 범례 및 조건 버튼 영역 -->
        <b-row class="mb-1">
            <!-- 왼쪽 영역 - 범례  -->
            <b-col xl="3">
                <div class="div_legend d-flex justify-content-center" :style="{ height: '70px' }">
                    <div class="div_legend_top align-self-center">
                        경부하<div class="div_legend_color" :style="{ backgroundColor: '#008000' }"></div>
                        중부하<div class="div_legend_color" :style="{ backgroundColor: '#ffff00' }"></div>
                        최대부하<div class="div_legend_color" :style="{ backgroundColor: '#ff0000' }"></div>
                    </div>
                </div>
            </b-col>
            <!-- //왼쪽 영역 - 범례  -->
            <b-col xl="9">
                <div :style="{ height: '75px' }">
                    <!-- top영역 -->
                    <div id="textAA"
                        :style="{ display: 'flex', justifyContent: 'center', marginBottom: '10px', marginRight: '10px', fontSize: '15px', color: '#fff', fontFamily: 'KHNPHDRegular', textShadow: '0 0 3px #4ebfff', alignItems: 'center' }">
                        현재 적용 중인 계절은 <span class="nowInfoText" id="nowSeason">{{ seasonText }}</span> 입니다.</div>
                </div>
                <!-- //top영역 -->
            </b-col>
        </b-row>
        <!-- //범례 및 조건 버튼 영역 -->
        <!-- 시간대 -->
        <b-row class="mb-3">
            <!-- 왼쪽 영역  -->
            <b-col xl="3">
                <div class="div_box_border d-flex justify-content-center" :style="{ height: '51px' }">
                    <b-row class="w-75 row-cols-1">
                        <b-col>
                            <b-form-group label-cols="4" label-cols-lg="4" label-size="sm" label="시간대" label-for="input-sm"
                                class="comboFont text-center mx-auto mt-2 mb-0">
                                <b-form-select id="zone" v-model="value" :options="options" @input="getTopData()" size="sm"
                                    class="mb-3" />
                            </b-form-group>
                        </b-col>
                    </b-row>
                </div>
            </b-col>
            <!-- //왼쪽 영역  -->
            <!-- 오른쪽 영역  -->
            <b-col xl="9">
                <b-row class="d-flex justify-content-center align-items-center div_box_border p-1 month_icon" id="col-time"
                    :style="{ height: '51px' }">
                    <template v-if="dataLoad">
                        <MonthIcon v-for="(item, index) in monthData" :data="item" :key="index" />
                    </template>
                </b-row>
            </b-col>
            <!-- //오른쪽 영역  -->
        </b-row>
        <!-- //시간대 -->
        <!-- 관압모드 -->
        <b-row class="mb-4">
            <!-- 왼쪽 영역  -->
            <b-col xl="3">
                <b-row class="g-2">
                    <b-col xl="7">
                        <div class="d-flex justify-content-center align-items-center div_box_border"
                            :style="{ height: '127px' }">
                            관압모드
                        </div>
                    </b-col>
                    <b-col xl="5">
                        <d-row class="d-flex align-items-start flex-column" :style="{ height: '127px' }">
                            <b-col
                                class="d-flex justify-content-center align-items-center div_box_border w-100 mb-2">고압</b-col>
                            <b-col class="d-flex justify-content-center align-items-center div_box_border w-100">저압</b-col>
                        </d-row>
                    </b-col>
                </b-row>
            </b-col>
            <!-- //왼쪽 영역  -->
            <!-- 오른쪽 영역  -->
            <b-col xl="9">
                <b-row class="row-cols-1" :style="{ height: '127px' }">
                    <b-col
                        class="d-flex justify-content-center align-items-center div_box_border w-100 mb-2 p-1 month_icon">
                        <template v-if="dataLoad">
                            <HourRadioVue v-for="hour in hours" :key="hour" :name="hour" :type="'top'"
                                :value="hourData['C' + hour]" @input="handleRadioInputChange" />
                        </template>
                    </b-col>
                    <b-col class="d-flex justify-content-center align-items-center div_box_border w-100 p-1 month_icon">
                        <template v-if="dataLoad">
                            <HourRadioVue v-for="hour in hours" :key="hour" :name="hour" :type="'bot'"
                                :value="hourData['C' + hour]" @input="handleRadioInputChange" />
                        </template>
                    </b-col>
                </b-row>
            </b-col>
            <!-- //오른쪽 영역  -->
        </b-row>
        <!-- //관압모드 -->
    </b-row>
    <!-- //펌프운영관리 -->
</template>
<script>
// import Multiselect from '@vueform/multiselect'
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue'
import MonthIcon from '@/views/Setting/SongsuPumpOperation/HourIcon.vue'
import HourRadioVue from '@/views/Setting/SongsuPumpOperation/HourRadio.vue'
import { fetchFunc } from '@/util/fetchFunc'
import Swal from 'sweetalert2'
export default {
    components: {
        // Multiselect,
        SmallTitle,
        MonthIcon,
        HourRadioVue
    },
    data() {
        return {
            nowMonth: 1,
            seasonText: null,
            value: null,
            options: [
                { value: '봄철', text: '봄' },
                { value: '여름철', text: '여름' },
                { value: '가을철', text: '가을' },
                { value: '겨울철', text: '겨울' }
            ],
            monthData: [],
            monthRefs: [],
            hours: [],
            hourData: {},
            mode: {},
            dataLoad: false
        }
    },
    mounted() {
        this.firstSet()
        // this.setMonthIcon()
    },
    methods: {
        firstSet() {
            const nowDate = new Date();
            const nowMonth = nowDate.getMonth() + 1;
            this.nowMonth = nowMonth;
            if (nowMonth >= 11 || nowMonth <= 2) {
                this.value = '겨울철'
            } else if (nowMonth <= 5 && nowMonth >= 3) {
                this.value = '봄철'
            } else if (nowMonth <= 8 && nowMonth >= 6) {
                this.value = '여름철'
            } else {
                this.value = '가을철'
            }
            for (let i = 0; i < 24; i++) {
                this.hours.push(String(i))
            }
            this.getTopData();
        },
        async getTopData() {
            this.monthData = [];
            this.mode = {};
            const apiURL = this.$apiURL;
            let params = {
                rate: 1, //default 값
                ssn: this.value
            }


            this.monthData = (await fetchFunc(`${apiURL}/st/selectRT_RATE_INF?rate_idx=${params.rate}&ssn=${params.ssn}`)).data;
            this.hourData = (await fetchFunc(`${apiURL}/st/selectSuji?ssn=${params.ssn}`)).data[0];

            this.mode = this.hourData;

            this.seasonText = (params.ssn).slice(0, -1)
            this.dataLoad = true
        },
        handleRadioInputChange(hour, type) {
            switch (type) {
                case 'top':
                    this.mode['C' + hour] = "0"
                    break;
                case 'bot':
                    this.mode['C' + hour] = "1"
                    break;
            }
        },
        async pumpOperUpdate() {
            const apiURL = this.$apiURL;
            //태그 정보 필요
            const tag = '745-617-EMS-14';
            const confirmed = await Swal.fire({
                text: '모드를 저장하시겠습니까?',
                animation : false,
                showCancelButton: true,
                confirmButtonText: '저장',
                cancelButtonText: '취소'
            });

            if (confirmed.isConfirmed) {
                let ptrInfo = [];
                for (let i = 0; i < 24; i++) {
                    let tagHour;
                    if (i < 10) {
                        tagHour = `${tag}0${i}`;
                    } else {
                        tagHour = `${tag}${i}`;
                    }
                    let obj = {
                        no: tagHour,
                        value: this.mode["C" + i],
                        ssn_id: this.value,
                        ssn: this.value
                    }
                    ptrInfo.push(obj)
                }
                await fetchFunc(`${apiURL}/st/mergeOPER_INF`, this.mode)
                await fetchFunc(`${apiURL}/st/mergePTR_STRTG_INF`, ptrInfo)
                await Swal.fire({
                    animation : false,
                    text: '저장되었습니다.',
                })
            }else{
                await Swal.fire({
                    animation : false,
                    text: '저장이 취소되었습니다.',
                })
            }
        }
    }
}
</script>
<style src="@vueform/multiselect/themes/default.css"></style>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.selectBar .multiselect__clear {
    display: none;
}

.custom-radio input {
    margin: 0;
    padding: 0;
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
}

.radioBg {
    background-image: url(@/assets/img/pump/pump_on.png);
}

.custom-radio input:active+.radio-shape {
    opacity: .9;
}

.custom-radio input:checked+.radio-shape {
    -webkit-filter: none;
    -moz-filter: none;
    filter: none;
}

.radio-shape {
    cursor: pointer;
    background-size: contain;
    background-repeat: no-repeat;
    display: inline-block;
    width: 40px;
    height: 40px;
    -webkit-transition: all 100ms ease-in;
    -moz-transition: all 100ms ease-in;
    transition: all 100ms ease-in;
    -webkit-filter: brightness(1.8) grayscale(1) opacity(.4);
    -moz-filter: brightness(1.8) grayscale(1) opacity(.4);
    filter: brightness(1.8) grayscale(1) opacity(.4);
}

.season_btn {
    height: 33px;
    padding-top: 3px;
    padding-bottom: 3px;
    border: solid 1px #b4dffa;
    background-color: rgba(139, 194, 240, 0.25);
}

.comboFont {
    color: #ffffff;
    font-family: 'KHNPHDRegular';
    font-size: 15px;
    text-shadow: 0 0 10px #000;
    margin-right: 30px;
    line-height: 47px;
}

.div_content_col {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-family: 'KHNPHDRegular';
    font-size: 15px;
    text-align: center;
    background-color: #0080008f;
    border: 2px solid #ffffff8f;
    border-radius: 5px;
    color: #fff;
}

.div_content_col2 {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background-color: #0a4cba8f;
    border: 2px solid #0A5AAE8f;
    border-radius: 5px;
    color: #fff;
}


.div_legend {
    padding: 15px;
    background: url(@/assets/img/div_new.png) center no-repeat;
    background-size: 100% 100%;
    display: flex;
    color: #c3eaff;
    box-shadow: 0 0 5px #0cc7f7b0;
    font-family: 'KHNPHDRegular';
    flex-direction: column;
}

.div_legend_top {
    /* width: 100%;
    height: 50%;
    float: left; */
    display: flex;
    /* flex-direction: row; */
    align-items: center;
    justify-content: center;
}

.div_legend_color {
    width: 20px;
    height: 20px;
    margin: 0 10px;
    border: 2px solid #ffffff8f;
    border-radius: 5px;
}

.div_box_border {
    border: 1px solid #489cf2d1;
    box-shadow: 0 0 3px #489cf2;
    background-color: #0947ae66;
    border-radius: 5px;
}

.nowInfoText {
    color: #489cf2;
    font-size: 20px;
    font-weight: bold;
    text-shadow: none;
    margin: 0 5px;
}

.month_icon>*:first-child {
    margin-left: 0 !important;
}

.month_icon>*:last-child {
    margin-right: 0 !important;
}
</style>