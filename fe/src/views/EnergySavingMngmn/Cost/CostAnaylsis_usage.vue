<template>
    <b-col xl="3" v-bind:style="{ height: '95%' }">
        <div class="position-relative border-small border_img p-3">
            <div class="div-line-top"></div>
            <div class="cal_title_row text-center">
                <span id="monthText" class="cal_tite_text">{{ month }}</span>
                <span class="cal_tite_text"> 월 전력 사용량</span>
            </div>
            <table class="table table-borderless mx-auto mb-0" v-bind:style="{ width: '90%' }">
                <colgroup>
                    <col width="65%">
                    <col width="30%">
                    <col width="5%">
                </colgroup>
                <thead>
                    <TdHeader :setting="purpose" :value="value" />
                </thead>
                <tbody>
                    <TdRow v-for="(item) in listRow" :key="item" :setting="item" :value="value" :usage="true" />
                    <tr>
                        <td class="cal-title-font align-middle">사용 기간</td>
                        <td colspan="2" class="align-middle">
                            <b-input-group size="sm">
                                <Vue3Datepicker
                                    :style="{ 'height': '30px', color: '#ffffff', backgroundColor: '#15284e', 'background-image': 'url(' + require('@/assets/img/select_cal.png') + ')', 'background-repeat': 'no-repeat', 'background-position': 'right', outline: 'none', 'border-width': '1px', 'borderColor': '#489cf2', borderRadius: '4px', 'padding-left': '10px', 'margin': '0 10px' }"
                                    input-class="input-class" minimum-view="month"
                                    @update:modelValue="handleMonthPageChanged()" :inputFormat="dateFormat.format"
                                    :locale="dateFormat.locale" v-model="selectedDate" />
                            </b-input-group>
                        </td>
                    </tr>
                </tbody>
            </table>
            <input id="inputHidden" class="hidden"/>
            <div class="div-line-bottom"></div>
        </div>
    </b-col>
</template>

<script>
import { ref } from 'vue';
import TdRow from "@/views/EnergySavingMngmn/Cost/TdRow.vue"
import TdHeader from "@/views/EnergySavingMngmn/Cost/TdHeader.vue"
import Vue3Datepicker from 'vue3-datepicker';
import { ko } from 'date-fns/locale';
import 'vue3-datepicker/dist/vue3-datepicker.css';
export default {
    components: {
        TdRow,
        TdHeader,
        Vue3Datepicker
    },
    setup(props, { emit }) {
        const selectedDate = ref(new Date());

        const handleMonthPageChanged = () => {
            setTimeout(() => {
                const getDate = selectedDate.value;
                emit("setDate", getDate)
            }, 10)
            const inputHidden = document.getElementById('inputHidden');
            if (inputHidden) {
                inputHidden.focus();
            }
        };
        return {
            selectedDate,
            handleMonthPageChanged,
        };
    },
    data() {
        return {
            dateFormat: {
                locale: ko,
                format: 'yyyy-MM',

            },
            monthDate: new Date(),
            selDate: null,
            purpose: {
                text: "용도",
                key: "LARGE_CTGRY"
            },
            listRow: [
                {
                    text: "요금 적용 전력<br/>(계약 전력)",
                    unit: "kw",
                    key: "PWR"
                },
                {
                    text: "데이터 누락율",
                    unit: "%",
                    key: "DATA_MSN_PRCNT"
                },
                {
                    text: "전력 사용량",
                    unit: "kWh",
                    key: "TOT_PWR"
                },
                {
                    text: "경부하 사용량",
                    unit: "kWh",
                    key: "L_PWR"
                },
                {
                    text: "중간부하 사용량",
                    unit: "kWh",
                    key: "M_PWR"
                },
                {
                    text: "최대부하 사용량",
                    unit: "kWh",
                    key: "H_PWR"
                },
            ],
            value: {},
            month: null
        }
    },
    mounted() {
        this.firstSet()
    },
    methods: {
        firstSet() {
            const nowDate = new Date();
            const firstDate = `${nowDate.getFullYear()}-${nowDate.getMonth() + 1}`;
            this.selDate = firstDate
            this.handleMonthPageChanged();
        },
        setValueData(data) {
            this.value = data;
        },
        setMonth(month) {
            this.month = month
        }
    }
}
</script>
<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.cal_tite_text {
    text-shadow: 0 0 9px #5cafff;
    font-size: 28px;
    font-family: KHNPHDRegular;
    letter-spacing: normal;
    color: #c3eaff;
    line-height: 63px;
    font-weight: bold;
}

.div-line-top {
    position: absolute;
    top: 0;
    left: 0;
    height: 5px;
    background: url(/src/assets/img/spark_x.png) no-repeat;
    background-size: 100% 100%;
    mix-blend-mode: color-dodge;
}

.div-line-bottom {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 15px;
    background: url(/src/assets/img/spark_x.png) no-repeat;
    background-size: 100% 100%;
    mix-blend-mode: color-dodge;
}
.hidden{
    opacity: 0;
}
</style>