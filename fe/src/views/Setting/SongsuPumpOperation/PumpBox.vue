<template>
    <b-col xl="auto" style="width: 165px;">
        <div class="d-flex align-items-start flex-column box-bg-big fontContent" :style="{ height: '290px' }">
            <b-col class="d-flex align-items-center div_box_title_border w-100 px-1 mb-2"
                style="text-align: center; font-size: 0.95em;">{{ `${pump.PUMP_NM}` }}</b-col>
            <b-col class="d-flex align-items-center div_box_border w-100 px-3"
                style="text-align: center; font-size: 1em;">{{ type }}</b-col>
            <b-col class="d-flex align-items-center div_box_border w-100 px-3"
                style="text-align: center; font-size: 1em;">{{ `${pump.PUMP_SIZE} 대` }}</b-col>
            <b-col class="d-flex align-items-center div_box_border w-100 px-3 mb-2">
                <b-form-select v-model="use_yn" :options="selectOpt" @input="pumpUse()" size="sm"
                    style="font-size: 1em;"></b-form-select>
            </b-col>

        </div>
    </b-col>
</template>
<script>
import { notNumReplace } from '@/util/replace';
export default {
    props: {
        pump: {
            type: Object,
            required: true
        },
    },
    data() {
        return {
            use_yn: this.pump.PUMP_YN,
            pump_typ: this.pump.PUMP_TYP,
            type: null,
            selectOpt: [
                {
                    value: 1,
                    text: "사용"
                },
                {
                    value: 0,
                    text: "미사용"
                }
            ],
            isDisabled: false
        }
    },
    mounted() {

        if (this.pump_typ == '1') {
            this.type = '정속'
        } else {
            this.type = '인버터'
        }
        
    },
    methods: {
        handleInput(event) {
            const inputElement = event.target;

            notNumReplace(inputElement);
        },
        getPumpData() {
            let pumpObj = this.pump;
            pumpObj.PUMP_YN = this.use_yn
            
            this.$emit('pumpData', pumpObj)
        },
        pumpUse() {
            this.$emit('update-data', { pump: this.pump.PUMP_IDX, use_yn: this.use_yn });
        }
    }
}
</script>
<style scoped>
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

.form-control:disabled {
    opacity: 0.5;
    backdrop-filter: blur(5px) brightness(.5);
    background-color: #7d8b99;
}
</style>