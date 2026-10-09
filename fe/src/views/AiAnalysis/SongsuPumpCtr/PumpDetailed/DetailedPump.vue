<template>
    <b-col>
        <div :class="pumpClass" :style="pumpStyle">#{{ pump.PUMP_GRP_IDX }}</div>
        <div v-show="pump.FREQ" class="fL"
            style="background-size: 80%; height: 25px; width: 100%; display: flex; align-items: center; justify-content: center; font-size: 18px;">
            <span class="input_design" style="margin-right: 10px; height: 100%;">{{ pump.FREQ }}</span>Hz
        </div>
    </b-col>
</template>
<script>



export default {
    props: {
        pump: {
            type: Object
        },
        pumpHeight: {
            type: Number
        }
    },
    data() {
        return {
            pumpClass: 'pump_area_h4 pump_img flex_center fL',
            pumpStyle: {
                height: '100px',
                width: '100%',
                'background-size': '80%',
                opacity: 1,
                // 'margin-bottom' : '0'
            }
        }
    },
    mounted() {

        //정수장에 따라서 변경
        if (this.pumpHeight == 1) {
            this.pumpStyle.height = '170px'
            this.pumpStyle['margin-bottom'] = '12px'

        }
        if (this.pump.FREQ) {
            this.pumpClass = 'pump_area_h35 pump_img flex_center fL'
            this.pumpStyle.width = '125%'
            if (this.pumpHeight == 1) {
                this.pumpStyle.height = '160px'
            } else {
                this.pumpStyle.height = '80px'
            }
            this.pumpStyle['background-size'] = '65%'
        }
        if (Number(this.pump.use) != 1) {
            this.pumpStyle.opacity = 0.25
        }
    }
}
</script>
<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */


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
</style>