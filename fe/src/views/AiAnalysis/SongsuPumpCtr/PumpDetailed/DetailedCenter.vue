<template>
    <b-col xl="4">
        <!--  펌프 영역 시작 -->
        <div class="" style="width: 100%; height:100%; text-align: center; font-size: 20px; color: white;">
            <div class="fL table-bg"
                style="height: calc(60% - 40px);width: 100%;margin-bottom: 10px; background-size: 101% 104%;  background-position: center;">
                <div class="fL" style="height: 95px; width: 100%;display: flex;align-items: center;padding: 15px 0 10px 0;">
                    <DotCircleMain :data="pump03" :style="dotCircleStyle" />
                </div>
                <div class="fL" style="height: calc(100% - 125px); width: calc(100% - 15px ); margin-left: 15px; ">
                    <PumpImg :className="'pump_area_h4 pump_img flex_center fL'" v-for="(item, index) in pumpImg01" :key="item" :num="'#'+(index+1)" :data="item"/>
                </div>
            </div>

            <div class="fL table-bg"
                style="height: 37%;width: 100%; background-size: 101% 104%; background-position: center;">
                <div class="fL" style="height: 95px; width: 100%;display: flex;align-items: center;padding: 15px 0 10px 0;">
                    <DotCircleMain :data="pump04" :style="dotCircleStyle" />
                </div>
                <div class="fL" style="height: calc(100% - 157px); width: calc(100% - 15px);  margin-left: 15px;">
                    <PumpImg :className="'pump_area_h35 pump_img flex_center fL'" v-for="(item, index) in pumpImg02" :key="item" :num="'#'+(index+1)" :data="item"/>
                </div>
            </div>
        </div>
        <!--  펌프 영역 끝 -->
    </b-col>
</template>
<script>
import DotCircleMain from '../PumpSmallComponents/DotCircleMain.vue';
import PumpImg from '../PumpSmallComponents/PumpImg.vue';
export default {
    components: {
        DotCircleMain,
        PumpImg
    },
    data() {
        return {
            dotCircleStyle: {
                mainWidth: '30%',
                mainHeight: '100%',
                sub: '70%',
                row: '30%',
            },
            pump03: {
                title: '평택',
                sub: [
                    {
                        title: '전력',
                        value: 0,
                        unit: 'kW'
                    },
                    {
                        title: '관압',
                        value: 0,
                        unit: 'kg/cm2'
                    },
                    {
                        title: '유량',
                        value: 0,
                        unit: 'm3'
                    }
                ]
            },
            pump04: {
                title: '송산',
                sub: [
                    {
                        title: '전력',
                        value: 0,
                        unit: 'kW'
                    },
                    {
                        title: '관압',
                        value: 0,
                        unit: 'kg/cm2'
                    },
                    {
                        title: '유량',
                        value: 0,
                        unit: 'm3'
                    }
                ]
            },
            pumpImg01:[
                    {
                        style : {
                            opacity: 0.25,
                        }
                    },
                    {
                        style : {
                            opacity: 0.25,
                        }
                    },
                    {
                        style : {
                            opacity: 1,
                        }
                    },
                    {
                        style : {
                            'background-size': '25%',
                            opacity: 1,
                        }
                    }
            ],
            pumpImg02:[
                    {
                        style : {
                            'background-size': '25%',
                            opacity: 0.25,
                        },
                        input:{
                            value : 0.00
                        }
                    },
                    {
                        style : {
                            'background-size': '25%',
                            opacity: 1,
                        },
                        input:{
                            value : 59.10
                        }
                    },
            ]


        }
    }
}
</script>
<style>
.table-bg {
    background: url(@/assets/img/analysis/table_bg_03.png) no-repeat;
}

.r-circle {
    background: url(@/assets/img/r_circle.png) no-repeat;
    background-position: center;
}

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
}</style>