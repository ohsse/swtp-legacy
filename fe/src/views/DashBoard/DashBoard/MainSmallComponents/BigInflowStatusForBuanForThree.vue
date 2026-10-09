<template>
    <div :style="{ height: '100px', width: '100%', marginTop: '25px' }">
        <div class="pipe_name fL">
            <span class="detail_text fL" :style="{ fontSize: '15px' }">{{
        item[0]?.title
    }}</span>
            <span class="detail_text fL" :style="{ fontSize: '15px' }">{{ item[0]?.dmd_pri
                }}</span>
        </div>
        <div class="pipe_first_wrap fL">
            <div class="pipe_first_wrap2">유입유량
                <div class="input_box2 fL first_box">
                    <span class="input_value">{{ item[0]?.inflowVal }}</span>m3/h
                </div>
            </div>
            <div class="pipe_first fL"></div>
        </div>
        <div class="pipe_con fL" :style="{ height: '100%', backgroundSize: '105% 53%', backgroundPosition: '50% 53%' }">
        </div>
        <div class="pipe_center_wrap fL">
            <div class="pipe_center_top fL">
                <div class="valve_on fL"></div>
                <div class="input_box2 input_box_rate fL">
                    <span class="input_value_rate">{{ item[0]?.valueRate }}</span>%
                </div>
                <div class="pipe_line fL">
                    <div class="pipe_line_arrow blinking" :style="{ backgroundSize: '15% 100%' }">
                    </div>
                </div>
            </div>
            <div class="pipe_center_bottom fL">
                <div class="valve_on fL"></div>
                <div class="input_box2 input_box_rate fL ">
                    <span class="input_value_rate">{{ item[0]?.valueRate2 }}</span>%
                </div>
                <div class="pipe_line fL">
                    <div class="pipe_line_arrow blinking" :style="{ backgroundSize: '15% 100%' }">
                    </div>
                </div>
            </div>
        </div>
        <div class="pipe_last_wrap fL">
            <div class="water_wrap">
                <div class="input_box2 input_water_top fL">
                    <span class="input_value">{{ item[0]?.waterLevel }}</span>m
                </div>
                <div class="input_box2 input_water_bottom fL">
                    <span class="input_value">{{ item[0]?.waterLevel2 }}</span>m
                </div>
            </div>
        </div>
        <div class="pipe_last_wrap fL" :style="{ marginTop: '-23px', marginLeft: '-8px' }">
            <div class="pipe_last_wrap2">유출유량
                <div class="input_box2 bm10 fL">
                    <span class="input_value">{{ item[0]?.outflowVal }}</span> m3/h
                </div>
                <div class="pipe_last fL">
                    <div class="pipe_last_arrow blinking"
                        :style="{ width: '50%', backgroundSize: '15% 100%', left: '40px' }">
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- 3개1묶음 표시 -->
    <div :style="{ height: '150px', width: '100%', display: 'flex', alignItems: 'center', marginTop: '30px' }">
        <div class="pipe_name fL">
            <span class="detail_text fL" :style="{ fontSize: '15px' }">{{ item[1]?.title
                }}</span>
            <span class="detail_text fL" :style="{ fontSize: '15px' }">{{ item[1]?.dmd_pri
                }}</span>
        </div>
        <div class="pipe_first_wrap fL">
            <div class="pipe_first_wrap2">유입유량
                <div class="input_box2 fL first_box">
                    <span class="input_value">{{ item[1]?.inflowVal }}</span>m3/h
                </div>
            </div>
            <div class="pipe_first fL"></div>
        </div>
        <div class="pipe_con2 fL"
            :style="{ position: 'relative', display: 'flex', alignItems: 'center', backgroundSize: '100% 66%', backgroundPosition: '50% 49%' }">
            <div class="pipe_line"
                :style="{ width: '100%', position: 'absolute', right: '0', display: 'flex', backgroundSize: '100% 13%', backgroundPosition: '50% 46%' }">
            </div>
        </div>
        <div class="pipe_center_wrap fL">
            <div class="pipe_center_top fL" :style="{ height: '33.33%' }">
                <div class="valve_on fL"></div>
                <div class="input_box2 input_box_rate fL">
                    <span class="input_value_rate">{{ item[1]?.valueRate }}</span>%
                </div>
                <div class="pipe_line fL">
                    <div class="pipe_line_arrow blinking" :style="{ backgroundSize: '15% 100%' }">
                    </div>
                </div>
            </div>
            <div class="pipe_center_bottom fL" :style="{ height: '33.33%' }">
                <div class="valve_on fL"></div>
                <div class="input_box2 input_box_rate fL ">
                    <span class="input_value_rate">{{ item[1]?.valueRate2 }}</span>%
                </div>
                <div class="pipe_line fL">
                    <div class="pipe_line_arrow blinking" :style="{ backgroundSize: '15% 100%' }">
                    </div>
                </div>
            </div>
            <div class="pipe_center_bottom fL" :style="{ height: '33.33%' }">
                <div class="valve_on fL"></div>
                <div class="input_box2 input_box_rate fL ">
                    <span class="input_value_rate">{{ item[1]?.valueRate3 }}</span>%
                </div>
                <div class="pipe_line fL">
                    <div class="pipe_line_arrow blinking" :style="{ backgroundSize: '15% 100%' }">
                    </div>
                </div>
            </div>
        </div>
        <div class="pipe_last_wrap fL">
            <div class="water_wrap"
                :style="{ position: 'relative', backgroundPosition: '50% 19%', backgroundSize: '100% 76%', justifyContent: 'unset !important' }">
                <div class="input_box2 input_water_top fL"
                    :style="{ position: 'absolute', top: '10px', marginBottom: '0 !important' }">
                    <span class="input_value">{{ item[1]?.waterLevel }}</span>m
                </div>
                <div class="input_box2 input_water_bottom fL"
                    :style="{ position: 'absolute', bottom: '75px', marginBottom: '0 !important' }">
                    <span class="input_value">{{ item[1]?.waterLevel2 }}</span>m
                </div>
                <div class="input_box2 input_water_bottom fL"
                    :style="{ position: 'absolute', bottom: '30px', marginBottom: '0 !important' }">
                    <span class="input_value">{{ item[1]?.waterLevel3 }}</span>m
                </div>
            </div>
        </div>
        <div class="pipe_last_wrap fL" :style="{ marginTop: '-23px', marginLeft: '-8px' }">
            <div class="pipe_last_wrap2">유출유량
                <div class="input_box2 bm10 fL">
                    <span class="input_value">{{ item[1]?.outflowVal }}</span> m3/h
                </div>
                <div class="pipe_last fL">
                    <div class="pipe_last_arrow blinking"
                        :style="{ width: '50%', backgroundSize: '15% 100%', left: '40px' }">
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- //3개1묶음 표시 -->
</template>

<script>
export default {
    props: ['inflowVal'],
    data() {
        return {
            item: []
        }
    },
    mounted() {
    },
    methods: {
        settingData(data) {
            this.item = data[0]
        }
    }
}
</script>

<style>
.water_wrap {
    width: 100%;
    height: 100%;
    background: url("@/assets/img/analysis/watertank_big.png") no-repeat;
    background-size: 100% 66%;
    background-position: 50% 36%;
    margin: 0 0 0 -24%;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: center;
}

.right_title_font {
    font-size: 21px;
    font-weight: bold;
    color: #5180b4;
    line-height: 44px;
    font-family: 'KHNPHDRegular';
}

.input_water_top {
    width: 72% !important;
    margin: 0 0 25% 0 !important;
    background-color: #15284e54 !important;
}

.input_water_bottom {
    width: 72% !important;
    margin: 0 0 25% 0 !important;
    background-color: #15284e54 !important;
}

.input_box_rate {
    width: 40% !important;
    height: 36% !important;
    margin: 3px 0 0 -10%;
}

.input_box2 {
    height: 25px;
    width: 150%;
    margin-left: -16px;
    font-size: 12px;
    border-radius: 3px;
    border: 1px solid #489cf2;
    background-color: #15284e;
    color: #a4ceed;
    text-align: center;
    font-family: 'KHNPHDRegular';
    display: flex;
    align-items: center;
    justify-content: center;
}

.bm10 {
    margin-bottom: 10%;
}

.input_value {
    font-family: 'LAB디지털' !important;
    margin-right: 2px;
    font-size: 15px;
    color: #fff;
}

.input_value_rate {
    font-family: 'LAB디지털' !important;
    margin-right: 2px;
    font-size: 12px;
    color: #fff;
}

.pipe_line {
    width: 47%;
    height: 36%;
    text-align: center;
    background: url("@/assets/img/analysis/pipeline_un.png") no-repeat;
    background-size: 100% 12px;
    background-position: center;
    margin: 0 0 0 -14%;
}

.pipe_line_arrow {
    background: url("@/assets/img/analysis/pipeline_arrow.png") no-repeat;
    width: 100%;
    height: 100%;
    mix-blend-mode: color-dodge;
    background-position: center;
}

.pipe_first_wrap {
    width: 18%;
    height: 100%;
    text-align: center;
    display: flex;
    align-items: center;
}

.pipe_first_wrap2 {
    width: 70%;
    margin-top: -23%;
    z-index: 1;
}

.blinking {
    -webkit-animation: blink 3s linear infinite;
    -moz-animation: blink 3s linear infinite;
    animation: blink 3s linear infinite;
}

.pipe_last_wrap {
    width: 15%;
    height: 100%;
    text-align: center;
    display: flex;
    align-items: flex-end;
}

.pipe_last_wrap2 {
    width: 87%;
    height: 70%;
}

.pipe_center_wrap {
    height: 100%;
    width: 20%;
    margin-left: -1%;
}

.pipe_center_top {
    width: 100%;
    height: 50%;
    text-align: center;
}

.pipe_center_bottom {
    width: 100%;
    height: 50%;
    text-align: center;
    margin-top: -6%;
}

.pipe_name {
    width: 15%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.pipe_first {
    width: 30%;
    height: 25px;
    background: url("@/assets/img/analysis/pipeline_un.png") no-repeat;
    background-size: 100% 15px;
}

.pipe_con {
    width: 5%;
    height: 77.5%;
    text-align: center;
    background: url("@/assets/img/analysis/pipeline_two.png") no-repeat;
    background-size: 105% 59%;
    background-position: 50% 86%
}

.pipe_last {
    width: 152%;
    margin: 0 0 0 -20%;
    height: 12px;
    background: url("@/assets/img/analysis/pipeline_un.png") no-repeat;
    background-size: 100% 12px;
}

.pipe_last_arrow {
    background: url("@/assets/img/analysis/pipeline_arrow.png") no-repeat;
    width: 100%;
    height: 100%;
    mix-blend-mode: color-dodge;
    position: relative;
    left: 40px;
}

/* 밸브색상 */
.valve_on {
    width: 50%;
    height: 100%;
    text-align: center;
    background: url("@/assets/img/analysis/03_2_valve_active.png") no-repeat;
    background-position: 22% 47%;
    background-size: 65% 50%;
}

.valve_off {
    width: 50%;
    height: 100%;
    text-align: center;
    background: url("@/assets/img/analysis/03_2_valve_disable2.png") no-repeat;
    background-position: 22% 47%;
    background-size: 65% 50%;
}

.detail_text {
    width: 100%;
    text-shadow: 0 0 9px #5cafff;
    color: #c3eaff;
    text-align: center;
}

.pipe_con2 {
    width: 5%;
    height: 100%;
    text-align: center;
    background: url("@/assets/img/analysis/03_2_pipeline_curve.png") no-repeat;
    background-size: 100% 50%;
    background-position: 50% 50%
}
</style>