<template>
    <!-- 2개1묶음 표시 -->
    <div class="d-flex align-items-center" :style="{ width: '100%', height: '38%', marginTop: '20px' }">
        <div class="d-flex flex-column" :style="{ width: '24%', marginTop: '20px' }">
            <div class="pipe_name fL" :style="{ width: '100%' }">
                <span class="detail_text fL text-start" :style="{ fontSize: '15px', marginTop: '-130px' }">{{ item[0]?.title
                }}</span>
                <span class="detail_text fL text-start" :style="{ fontSize: '15px' }">{{ item[0]?.dmd_pri
                }}</span>
            </div>
            <div class="pipe_first_wrap fL" :style="{ width: '100%' }">
                <div class="pipe_first_wrap2" :style="{ width: '70%', marginBottom: '10px' }">유입유량
                    <div class="input_box2 fL first_box" :style="{ width: '120%', marginLeft: '0', }">
                        <span class="input_value">{{ item[0]?.inflowVal
                        }}</span>m3/h
                    </div>
                </div>
                <div class="pipe_first fL" :style="{ height: '12px', marginTop: '-20px', backgroundSize: '101% 15px' }">
                </div>
            </div>
        </div>
        <div class="pipeline-un-y" :style="{ width: '6%', backgroundSize: '35% 55% !important' }">
            <div class="pipe_first fL"
                :style="{ width: '100%', height: '50%', backgroundSize: '26px 12px', backgroundPosition: '100% 50%' }">
            </div>
            <div class="pipe_first fL"
                :style="{ width: '100%', height: '50%', backgroundSize: '26px 12px', backgroundPosition: '100% 50%' }">
            </div>
        </div>
        <div class="d-flex justify-content-center align-items-center flex-column" :style="{ width: '40%', height: '100%' }">
            <div class="pump_div"
                :style="{ width: '100%', height: '43%', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '13px', marginTop: '10px', position: 'relative', top: '-8px'/*, marginBottom: 150 / major.length + 'px'*/ }">
                <div :style="{ height: '100%', width: '100%' }">
                    <div class="pipe_con fL"
                        :style="{ width: '10%', backgroundSize: '100% 63%', backgroundPosition: '100% 93%' }"></div>
                    <div class="pipe_center_wrap fL" :style="{ width: '40%' }">
                        <div class="pipe_center_top fL">
                            <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                            </div>
                            <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                                <div class="input_box2 input_box_rate fL position-relative"
                                    :style="{ top: '0', left: '10px', width: '100% !important' }">
                                    <span class="input_value_rate">{{ item[0]?.valueRate }}</span>%
                                </div>
                                <div class="pipe_line fL"
                                    :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                    <div class="pipe_line_arrow blinking"
                                        :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="pipe_center_bottom fL" :style="{ marginTop: '-9%' }">
                            <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                            </div>
                            <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                                <div class="input_box2 input_box_rate fL position-relative"
                                    :style="{ top: '0', left: '10px', width: '100% !important' }">
                                    <span class="input_value_rate">{{ item[0]?.valueRate2 }}</span>%
                                </div>
                                <div class="pipe_line fL"
                                    :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                    <div class="pipe_line_arrow blinking"
                                        :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="pipe_last_wrap fL" :style="{ width: '51%' }">
                        <div class="water_wrap" :style="{ margin: '0', backgroundSize: '100% 90% !important' }">
                            <div class="input_box2 input_water_top fL"
                                :style="{ position: 'relative', top: '-50px', margin: 'unset !important' }">
                                <span class="input_value">{{ item[0]?.waterLevel }}</span>m
                            </div>
                            <div class="input_box2 input_water_bottom fL"
                                :style="{ position: 'relative', top: '-25px', margin: 'unset !important' }">
                                <span class="input_value">{{ item[0]?.waterLevel2 }}</span>m
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="pump_div"
                :style="{ width: '100%', height: '43%', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '13px', marginTop: '10px', position: 'relative', top: '-5px'/*, marginBottom: 150 / major.length + 'px'*/ }">
                <div :style="{ height: '100%', width: '100%' }">
                    <div class="pipe_con fL"
                        :style="{ width: '10%', backgroundSize: '100% 63%', backgroundPosition: '100% 93%' }"></div>
                    <div class="pipe_center_wrap fL" :style="{ width: '40%' }">
                        <div class="pipe_center_top fL">
                            <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                            </div>
                            <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                                <div class="input_box2 input_box_rate fL position-relative"
                                    :style="{ top: '0', left: '10px', width: '100% !important' }">
                                    <span class="input_value_rate">{{ item[1]?.valueRate }}</span>%
                                </div>
                                <div class="pipe_line fL"
                                    :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                    <div class="pipe_line_arrow blinking"
                                        :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="pipe_center_bottom fL" :style="{ marginTop: '-9%' }">
                            <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                            </div>
                            <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                                <div class="input_box2 input_box_rate fL position-relative"
                                    :style="{ top: '0', left: '10px', width: '100% !important' }">
                                    <span class="input_value_rate">{{ item[1]?.valueRate2 }}</span>%
                                </div>
                                <div class="pipe_line fL"
                                    :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                    <div class="pipe_line_arrow blinking"
                                        :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="pipe_last_wrap fL" :style="{ width: '51%' }">
                        <div class="water_wrap" :style="{ margin: '0', backgroundSize: '100% 90% !important' }">
                            <div class="input_box2 input_water_top fL"
                                :style="{ position: 'relative', top: '-50px', margin: 'unset !important' }">
                                <span class="input_value">{{ item[1]?.waterLevel }}</span>m
                            </div>
                            <div class="input_box2 input_water_bottom fL"
                                :style="{ position: 'relative', top: '-25px', margin: 'unset !important' }">
                                <span class="input_value">{{ item[1]?.waterLevel2 }}</span>m
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="pipeline-un-y-right" :style="{ width: '6%', backgroundSize: '35% 55% !important' }">
            <div class="pipe_first fL"
                :style="{ width: '100%', height: '50%', backgroundSize: '26px 12px', backgroundPosition: '0% 50%' }">
            </div>
            <div class="pipe_first fL"
                :style="{ width: '100%', height: '50%', backgroundSize: '26px 12px', backgroundPosition: '0% 50%' }">
            </div>
        </div>
        <div class="d-flex flex-column" :style="{ width: '24%', marginTop: '-50px' }">
            <div class="pipe_last_wrap fL" :style="{ width: '100%' }">
                <div class="pipe_last_wrap2" :style="{ width: '100%' }">유출유량
                    <div class="input_box2 bm10 fL" :style="{ width: '90%', marginLeft: '15px' }">
                        <span class="input_value">{{ item[0]?.outflowVal }}</span> m3/h
                    </div>
                    <div class="pipe_last fL" :style="{ width: '100%', marginLeft: '0' }">
                        <div class="pipe_last_arrow blinking"
                            :style="{ width: '50%', backgroundSize: '15% 100%', left: '40px' }">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- //2개1묶음 표시 -->
    <!-- 2개1묶음 표시 -->
    <div class="d-flex align-items-center" :style="{ width: '100%', height: '38%', marginTop: '10px' }">
        <div class="d-flex flex-column" :style="{ width: '24%', marginTop: '20px' }">
            <div class="pipe_name fL" :style="{ width: '100%' }">
                <span class="detail_text fL text-start" :style="{ fontSize: '15px', marginTop: '-130px' }">{{ item[2]?.title
                }}</span>
                <span class="detail_text fL text-start" :style="{ fontSize: '15px' }">{{ item[2]?.dmd_pri
                }}</span>
            </div>
            <div class="pipe_first_wrap fL" :style="{ width: '100%' }">
                <div class="pipe_first_wrap2" :style="{ width: '70%', marginBottom: '10px' }">유입유량
                    <div class="input_box2 fL first_box" :style="{ width: '120%', marginLeft: '0', }">
                        <span class="input_value">{{ item[2]?.inflowVal
                        }}</span>m3/h
                    </div>
                </div>
                <div class="pipe_first fL" :style="{ height: '12px', marginTop: '-20px', backgroundSize: '101% 15px' }">
                </div>
            </div>
        </div>
        <div class="pipeline-un-y" :style="{ width: '6%', backgroundSize: '35% 55% !important' }">
            <div class="pipe_first fL"
                :style="{ width: '100%', height: '50%', backgroundSize: '26px 12px', backgroundPosition: '100% 50%' }">
            </div>
            <div class="pipe_first fL"
                :style="{ width: '100%', height: '50%', backgroundSize: '26px 12px', backgroundPosition: '100% 50%' }">
            </div>
        </div>
        <div class="d-flex justify-content-center align-items-center flex-column" :style="{ width: '40%', height: '100%' }">
            <div class="pump_div"
                :style="{ width: '100%', height: '43%', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '13px', marginTop: '10px', position: 'relative', top: '-8px'/*, marginBottom: 150 / major.length + 'px'*/ }">
                <div :style="{ height: '100%', width: '100%' }">
                    <div class="pipe_con fL"
                        :style="{ width: '10%', backgroundSize: '100% 63%', backgroundPosition: '100% 93%' }"></div>
                    <div class="pipe_center_wrap fL" :style="{ width: '40%' }">
                        <div class="pipe_center_top fL">
                            <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                            </div>
                            <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                                <div class="input_box2 input_box_rate fL position-relative"
                                    :style="{ top: '0', left: '10px', width: '100% !important' }">
                                    <span class="input_value_rate">{{ item[2]?.valueRate }}</span>%
                                </div>
                                <div class="pipe_line fL"
                                    :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                    <div class="pipe_line_arrow blinking"
                                        :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="pipe_center_bottom fL" :style="{ marginTop: '-9%' }">
                            <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                            </div>
                            <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                                <div class="input_box2 input_box_rate fL position-relative"
                                    :style="{ top: '0', left: '10px', width: '100% !important' }">
                                    <span class="input_value_rate">{{ item[2]?.valueRate2 }}</span>%
                                </div>
                                <div class="pipe_line fL"
                                    :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                    <div class="pipe_line_arrow blinking"
                                        :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="pipe_last_wrap fL" :style="{ width: '51%' }">
                        <div class="water_wrap" :style="{ margin: '0', backgroundSize: '100% 90% !important' }">
                            <div class="input_box2 input_water_top fL"
                                :style="{ position: 'relative', top: '-50px', margin: 'unset !important' }">
                                <span class="input_value">{{ item[2]?.waterLevel }}</span>m
                            </div>
                            <div class="input_box2 input_water_bottom fL"
                                :style="{ position: 'relative', top: '-25px', margin: 'unset !important' }">
                                <span class="input_value">{{ item[2]?.waterLevel2 }}</span>m
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="pump_div"
                :style="{ width: '100%', height: '43%', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '13px', marginTop: '10px', position: 'relative', top: '-5px'/*, marginBottom: 150 / major.length + 'px'*/ }">
                <div :style="{ height: '100%', width: '100%' }">
                    <div class="pipe_con fL"
                        :style="{ width: '10%', backgroundSize: '100% 63%', backgroundPosition: '100% 93%' }"></div>
                    <div class="pipe_center_wrap fL" :style="{ width: '40%' }">
                        <div class="pipe_center_top fL">
                            <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                            </div>
                            <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                                <div class="input_box2 input_box_rate fL position-relative"
                                    :style="{ top: '0', left: '10px', width: '100% !important' }">
                                    <span class="input_value_rate">{{ item[3]?.valueRate }}</span>%
                                </div>
                                <div class="pipe_line fL"
                                    :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                    <div class="pipe_line_arrow blinking"
                                        :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="pipe_center_bottom fL" :style="{ marginTop: '-9%' }">
                            <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                            </div>
                            <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                                <div class="input_box2 input_box_rate fL position-relative"
                                    :style="{ top: '0', left: '10px', width: '100% !important' }">
                                    <span class="input_value_rate">{{ item[3]?.valueRate2 }}</span>%
                                </div>
                                <div class="pipe_line fL"
                                    :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                    <div class="pipe_line_arrow blinking"
                                        :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="pipe_last_wrap fL" :style="{ width: '51%' }">
                        <div class="water_wrap" :style="{ margin: '0', backgroundSize: '100% 90% !important' }">
                            <div class="input_box2 input_water_top fL"
                                :style="{ position: 'relative', top: '-50px', margin: 'unset !important' }">
                                <span class="input_value">{{ item[3]?.waterLevel }}</span>m
                            </div>
                            <div class="input_box2 input_water_bottom fL"
                                :style="{ position: 'relative', top: '-25px', margin: 'unset !important' }">
                                <span class="input_value">{{ item[3]?.waterLevel2 }}</span>m
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="pipeline-un-y-right" :style="{ width: '6%', backgroundSize: '35% 55% !important' }">
            <div class="pipe_first fL"
                :style="{ width: '100%', height: '50%', backgroundSize: '26px 12px', backgroundPosition: '0% 50%' }">
            </div>
            <div class="pipe_first fL"
                :style="{ width: '100%', height: '50%', backgroundSize: '26px 12px', backgroundPosition: '0% 50%' }">
            </div>
        </div>
        <div class="d-flex flex-column" :style="{ width: '24%', marginTop: '-50px' }">
            <div class="pipe_last_wrap fL" :style="{ width: '100%' }">
                <div class="pipe_last_wrap2" :style="{ width: '100%' }">유출유량
                    <div class="input_box2 bm10 fL" :style="{ width: '90%', marginLeft: '15px' }">
                        <span class="input_value">{{ item[2]?.outflowVal }}</span> m3/h
                    </div>
                    <div class="pipe_last fL" :style="{ width: '100%', marginLeft: '0' }">
                        <div class="pipe_last_arrow blinking"
                            :style="{ width: '50%', backgroundSize: '15% 100%', left: '40px' }">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- //2개1묶음 표시 -->
    <!-- 1개만 표시 -->
    <div class="d-flex align-items-center" :style="{ width: '100%', height: 'calc(100%/5)' }">
        <div :style="{ width: '30%' }">
            <div class="pipe_name fL" :style="{ width: '100%' }">
                <span class="detail_text fL text-start" :style="{ fontSize: '15px' }">{{ item[4]?.title }}</span>
                <span class="detail_text fL text-start" :style="{ fontSize: '15px' }">{{ item[4]?.dmd_pri }}</span>
            </div>
            <div class="pipe_first_wrap fL" :style="{ width: '100%' }">
                <div class="pipe_first_wrap2" :style="{ width: '70%', marginTop: '0' }">유입유량
                    <div class="input_box2 fL first_box" :style="{ width: '120%', marginLeft: '0' }">
                        <span class="input_value">{{ item[4]?.inflowVal }}</span>m3/h
                    </div>
                </div>
                <div class="pipe_first fL" :style="{ height: '12px', marginTop: '23px', backgroundSize: '101% 15px' }">
                </div>
            </div>
        </div>
        <div class="d-flex justify-content-center align-items-center flex-column" :style="{ width: '40%', height: '100%' }">
            <div :style="{ height: '100%', width: '100%', position: 'relative', top: '10px' }">
                <div class="pipe_con fL"
                    :style="{ width: '10%', backgroundSize: '100% 63%', backgroundPosition: '100% 93%' }"></div>
                <div class="pipe_center_wrap fL" :style="{ width: '40%' }">
                    <div class="pipe_center_top fL">
                        <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                        </div>
                        <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                            <div class="input_box2 input_box_rate fL position-relative"
                                :style="{ top: '2px', left: '10px', width: '100% !important' }">
                                <span class="input_value_rate">{{ item[4]?.valueRate }}</span>%
                            </div>
                            <div class="pipe_line fL"
                                :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                <div class="pipe_line_arrow blinking"
                                    :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="pipe_center_bottom fL" :style="{ marginTop: '-10%' }">
                        <div class="valve_on fL" :style="{ backgroundPosition: '22% 52%', backgroundSize: '100% 50%' }">
                        </div>
                        <div class="d-flex flex-column position-relative" :style="{ width: '50%', height: '100%' }">
                            <div class="input_box2 input_box_rate fL position-relative"
                                :style="{ top: '2px', left: '10px', width: '100% !important' }">
                                <span class="input_value_rate">{{ item[4]?.valueRate2 }}</span>%
                            </div>
                            <div class="pipe_line fL"
                                :style="{ width: '100%', backgroundPosition: '100% 82%', margin: '0' }">
                                <div class="pipe_line_arrow blinking"
                                    :style="{ backgroundPosition: '50% 67%', backgroundSize: '35% 23%' }">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="pipe_last_wrap fL" :style="{ width: '51%' }">
                    <div class="water_wrap" :style="{ margin: '0' }">
                        <div class="input_box2 input_water_top fL" :style="{ margin: '0 0 22% 0 !important' }">
                            <span class="input_value">{{ item[4]?.waterLevel }}</span>m
                        </div>
                        <div class="input_box2 input_water_bottom fL">
                            <span class="input_value">{{ item[4]?.waterLevel2 }}</span>m
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="d-flex flex-column" :style="{ width: '30%' }">
            <div class="pipe_last_wrap fL" :style="{ width: '100%' }">
                <div class="pipe_last_wrap2" :style="{ width: '100%' }">유출유량
                    <div class="input_box2 bm10 fL" :style="{ width: '90%', marginLeft: '15px' }">
                        <span class="input_value">{{ item[4]?.outflowVal }}</span> m3/h
                    </div>
                    <div class="pipe_last fL" :style="{ width: '100%', marginLeft: '0' }">
                        <div class="pipe_last_arrow blinking"
                            :style="{ width: '50%', backgroundSize: '15% 100%', left: '40px' }">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- //1개만 표시 -->
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
    /* justify-content: center; */
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

.pipeline-un-y {
    background-size: 35% 28% !important;
}

.pipeline-un-y-right {
    background-size: 35% 28% !important;
}
</style>