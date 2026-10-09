<template>
    <b-col xl="3" v-bind:style="{ height: '95%' }">
        <div class="position-relative border-small border_img p-3">
            <div class="div-line-top"></div>
            <table class="table table-borderless mx-auto mb-0" v-bind:style="{ width: '90%' , height: '84%' , marginTop:'38px'}">
                <colgroup>
                    <col width="45%">
                    <col width="45%">
                    <col width="10%">
                </colgroup>
                <tbody>
                    <TdRow v-for="(item) in listRow" :key="item" :setting="item" :value="value"/>
                </tbody>
            </table>
            <div class="div-line-bottom"></div>
        </div>
    </b-col>
</template>

<script>
import TdRow from "@/views/EnergySavingMngmn/Cost/TdRow.vue"
// import TdHeader from "@/views/EnergySavingMngmn/Cost/TdHeader.vue"
export default {
    components: {
        TdRow,
        // TdHeader
    },
    data() {
        return {
            purpose: {
                text: "추천 요금제",
                key: "selectCost"
            },
            listRow: [
                {
                    text: "전체 요금",
                    unit: "원",
                    key: "TOT_FEE"
                },
                {
                    text: "기본 요금",
                    unit: "원",
                    key: "BASE_FEE"
                },
                {
                    text: "기타 요금",
                    unit: "원",
                    key: "ETC_FEE"
                },
                {
                    text: "경부하 전력요금",
                    unit: "원",
                    key: "L_ELCTR_FEE"
                },
                {
                    text: "중간부하 전력요금",
                    unit: "원",
                    key: "M_ELCTR_FEE"
                },
                {
                    text: "최대부하 전력요금",
                    unit: "원",
                    key: "H_ELCTR_FEE"
                },
            ],
            value: {}
        }
    },
    methods: {
        setValueData(data) {
            this.value = data;
        },
        // 선택 버튼 관련 이벤트 
        // selectBtn(num) {
        //     for (let i = 1; i <= 3; i++) {
        //         document.getElementById(`ctgry${i}`).classList.remove('selected');
        //     }
        //     document.getElementById(`ctgry${num}`).classList.add('selected');
        //     this.$emit("select", num);
        // }
    }
}
</script>
<style scoped>
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

.right_title_row {
    height: 15%;
    margin-top: 1%;
}

.select_btn_area {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
}

.select_btn_font {
    text-shadow: 0 0 9px #5cafff;
    font-size: 22px;
    color: #fff;
    font-family: 'KHNPHDBold';
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
}

.select_btn {
    width: 33.33%;
    height: 45%;
    align-self: center;
    border: solid 1px #b4dffa;
    background-color: rgb(138 154 168 / 25%);
    cursor: pointer;
    border-radius: 4px;
    margin-right: 2%;
    margin-left: 2%;
    line-height: 36px;

}

.selected {
    box-shadow: 0 0 10px 0 rgb(132 141 154 / 94%);
    background-color: rgb(226 242 255 / 40%) !important;
}
</style>