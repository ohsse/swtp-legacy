<template>
    <div :style="{ height: 'calc(100vh - 230px)' }">
        <div class="w-100 h-100" :style="{ textAlign: 'center', fontSize: '20px', color: 'white' }">
            <template v-if="firSuji.length > 0 && tabIndex === 0">
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '15px 0px 10px' }">
                    <DotCircleMain :data="firPump" :style="dotCircleStyle" />
                </div>
                <b-row :class="pumpClass" :style="{ padding: '0 15px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in firSuji" :key="item" :items="item" :index="index"
                        :length="firSuji.length" ref="FirPumpArea" />
                </b-row>
            </template>

            <template v-if="secSuji.length > 0 && tabIndex === 1">
                <!-- //관압&유량 -->
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '10px 0' }">
                    <div class="fL w-100"
                        :style="{ height: '55px', display: 'flex', alignItems: 'center', padding: '5px 0' }">
                        <DotCircleMain :data="secPump" :style="dotCircleStyle" />
                    </div>
                </div>
                <b-row :class="pumpClass" :style="{ padding: '0 15px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in secSuji" :key="item" :items="item" :index="index"
                        :length="secSuji.length" ref="SecPumpArea" />
                </b-row>
            </template>

            <template v-if="thrSuji.length > 0 && tabIndex === 2">
                <!-- //관압&유량 -->
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '10px 0' }">
                    <div class="fL w-100"
                        :style="{ height: '55px', display: 'flex', alignItems: 'center', padding: '5px 0' }">
                        <DotCircleMain :data="thrPump" :style="dotCircleStyle" />
                    </div>
                </div>
                <b-row :class="pumpClass" :style="{ padding: '0 15px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in thrSuji" :key="item" :items="item" :index="index"
                        :length="thrSuji.length" ref="ThrPumpArea" />
                </b-row>
            </template>

            <template v-if="fouSuji.length > 0 && tabIndex === 3">
                <!-- //관압&유량 -->
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '10px 0' }">
                    <div class="fL w-100"
                        :style="{ height: '55px', display: 'flex', alignItems: 'center', padding: '5px 0' }">
                        <DotCircleMain :data="fouPump" :style="dotCircleStyle" />
                    </div>
                </div>
                <b-row :class="pumpClass" :style="{ padding: '0 15px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in fouSuji" :key="item" :items="item" :index="index"
                        :length="fouSuji.length" ref="FouPumpArea" />
                </b-row>
            </template>

            <template v-if="fivSuji.length > 0 && tabIndex === 4">
                <!-- //관압&유량 -->
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '10px 0' }">
                    <div class="fL w-100"
                        :style="{ height: '55px', display: 'flex', alignItems: 'center', padding: '5px 0' }">
                        <DotCircleMain :data="fivPump" :style="dotCircleStyle" />
                    </div>
                </div>
                <b-row :class="pumpClass" :style="{ padding: '0 15px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in fivSuji" :key="item" :items="item" :index="index"
                        :length="fivSuji.length" ref="FivPumpArea" />
                </b-row>
            </template>
        </div>
    </div>
</template>

<script>
import DotCircleMain from '@/views/AiAnalysis/SongsuPumpCtr/PumpSmallComponents/DotCircleMain.vue'
import PumpAreaH4WithInfo from '@/views/AiAnalysis/SongsuPumpCtr/PumpSmallComponents/PumpAreaH4WithInfo.vue'
import { addCommaNumber } from '@/util/addCommaNumber'
import { watch } from "vue";
import { useStore } from 'vuex';
export default {
    components: {
        DotCircleMain,
        PumpAreaH4WithInfo,
        // PumpAreaH35
    },
    props: ['data1', 'data2', 'data3', 'tabIndex', 'data6', 'data7', 'data10', 'data11', 'data12', 'daaa13', 'data15', 'data16'],
    data() {
        return {
            firPump: { title: '', sub: [{ title: '관압', value: "0", unit: "kg/cm2" }, { title: '유량', value: "0", unit: "m3/h" }] },
            secPump: { title: '', sub: [{ title: '관압', value: "0", unit: "kg/cm2" }, { title: '유량', value: "0", unit: "m3/h" }] },
            thrPump: { title: '', sub: [{ title: '관압', value: "0", unit: "kg/cm2" }, { title: '유량', value: "0", unit: "m3/h" }] },
            fouPump: { title: '', sub: [{ title: '관압', value: "0", unit: "kg/cm2" }, { title: '유량', value: "0", unit: "m3/h" }] },
            fivPump: { title: '', sub: [{ title: '관압', value: "0", unit: "kg/cm2" }, { title: '유량', value: "0", unit: "m3/h" }] },
            dotCircleStyle: { mainWidth: '20%', mainHeight: '100%', sub: '75%', row: '20%' },
            firSuji: [],
            secSuji: [],
            thrSuji: [],
            fouSuji: [],
            fivSuji: [],
            pumpClass: 'row-cols-1',
            firStatus: '',
            secStatus: '',
            store: useStore(),
            thrStatus: '',
            fouStatus: '',
            fivStatus: '',
        }
    },

    mounted() {
        watch(() => this.$store.state, function () {
            
            this.changePumpOnOff(this.$store.state.data6)
        });
    },
    updated() {
        if (this.$area === 'buan') {
            this.changePumpControlRig(this.firStatus, this.secStatus, this.thrStatus, this.fouStatus, this.fivStatus)
        }
        else {
            this.changePumpControlRig(this.firStatus, this.secStatus)
        }
    },
    beforeUpdate() {
        let firPressSum = 0;
        let firFluxSum = 0;
        let secPressSum = 0;
        let secFluxSum = 0;
        let thrPressSum = 0;
        let thrFluxSum = 0;
        let fouPressSum = 0;
        let fouFluxSum = 0;
        let fivPressSum = 0;
        let fivFluxSum = 0;
        if (this.data1.pumpStatus?.filter(item => item.PUMP_GRP === 1).length > 0) {
            this.firSuji = JSON.parse(JSON.stringify(this.data1?.pumpStatus?.filter(item => item.PUMP_GRP === 1)));
            this.firPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 1);
            this.firSpiTmp = this.data1.SPI?.filter(item => item.PUMP_GRP === 1);
            this.firSuji?.forEach((element, i) => {
                if (element?.PUMP_TYP == 2) {
                    if (this.data6?.length > 0) {
                        const data = this.data6
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.FREQ) == 0) {
                                    element.hz = parseFloat(item.FREQ).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.FREQ).toFixed(0)
                                }
                            }
                        })
                    }
                    else {
                        const data = this.firSpiTmp
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.value) == 0) {
                                    element.hz = parseFloat(item.value).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.value).toFixed(0)
                                }
                            }
                        })
                    }
                }
                if (element.value === "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else {
                    element.opacity = '1.0'
                    element.value = "On"
                }
                if (this.data6[i]?.value == "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else if (this.data6[i]?.value == "On") {
                    element.opacity = '1.0'
                    element.value = "On"
                }
            })
            this.firPump.title = this.data2?.data[0]?.PUMP_GRP_NM || this.firPressTmp[0]?.PUMP_GRP_NM;

            if (this.data2?.data?.length > 0) {
                this.data2?.data?.forEach(item => {
                    firPressSum += item?.TUBE_PRSR_PRDCT
                    firFluxSum += item?.PRDCT_MEAN
                    if (firPressSum === 0) {
                        this.firPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 1);
                        this.firPressTmp.forEach(item => {
                            firPressSum += Number(item.value)
                        })
                    }
                    if (firFluxSum === 0) {
                        this.firFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 1);
                        this.firFluxTmp.forEach(item => {
                            firFluxSum += Number(item.value)
                        })
                    }
                })
            }
            else {
                this.firPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 1);
                this.firPressTmp.forEach(item => {
                    firPressSum += Number(item.value)
                })
                this.firFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 1);
                this.firFluxTmp.forEach(item => {
                    firFluxSum += Number(item.value)
                })
            }
            this.firPump.sub[0].value = addCommaNumber(firPressSum)
            this.firPump.sub[1].value = addCommaNumber(firFluxSum)
            this.pumpClass = 'row-cols-1'
        }
        if (this.$area == 'gosan') {
            this.firSuji = this.firSuji.reverse()
        }
        if (this.data1.pumpStatus?.filter(item => item.PUMP_GRP === 2).length > 0) {
            this.secSuji = JSON.parse(JSON.stringify(this.data1?.pumpStatus?.filter(item => item.PUMP_GRP === 2)));
            this.secPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 2);
            this.secSpiTmp = this.data1.SPI?.filter(item => item.PUMP_GRP === 2);
            this.secSuji?.forEach((element, i) => {
                if (element?.PUMP_TYP == 2) {
                    if (this.data7?.length > 0) {
                        const data = this.data7
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.FREQ) == 0) {
                                    element.hz = parseFloat(item.FREQ).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.FREQ).toFixed(0)
                                }
                            }
                        })
                    }
                    else {
                        const data = this.secSpiTmp
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.value) == 0) {
                                    element.hz = parseFloat(item.value).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.value).toFixed(0)
                                }
                            }
                        })
                    }
                }
                if (element.value === "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else {
                    element.opacity = '1.0'
                    element.value = "On"
                }
                if (this.data7[i]?.value == "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else if (this.data7[i]?.value == "On") {
                    element.opacity = '1.0'
                    element.value = "On"
                }
            })
            this.secPump.title = this.data3?.data[0]?.PUMP_GRP_NM || this.secPressTmp[0]?.PUMP_GRP_NM
            if (this.data3?.data?.length > 0) {
                if (this.data3?.data[0] == null) {
                    this.secPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 2);
                    this.secPressTmp.forEach(item => {
                        secPressSum += Number(item.value)
                    })
                    this.secFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 2);
                    this.secFluxTmp.forEach(item => {
                        secFluxSum += Number(item.value)
                    })
                }
                else {
                    this.data3?.data?.forEach(item => {
                        secPressSum += item?.TUBE_PRSR_PRDCT
                        secFluxSum += item?.PRDCT_MEAN
                        if (secPressSum === 0) {
                            this.secPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 2);
                            this.secPressTmp.forEach(item => {
                                secPressSum += Number(item.value)
                            })
                        }
                        if (secFluxSum === 0) {
                            this.secFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 2);
                            this.secFluxTmp.forEach(item => {
                                secFluxSum += Number(item.value)
                            })
                        }
                    })
                }
            }
            else {
                this.secPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 2);
                this.secPressTmp.forEach(item => {
                    secPressSum += Number(item.value)
                })
                this.secFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 2);
                this.secFluxTmp.forEach(item => {
                    secFluxSum += Number(item.value)
                })
            }
            this.secPump.sub[0].value = addCommaNumber(secPressSum)
            this.secPump.sub[1].value = addCommaNumber(secFluxSum)
            this.pumpClass = 'row-cols-1'
        }
        if (this.data1.pumpStatus?.filter(item => item.PUMP_GRP === 3).length > 0) {
            this.thrSuji = JSON.parse(JSON.stringify(this.data1?.pumpStatus?.filter(item => item.PUMP_GRP === 3)));
            this.thrPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 3);
            this.thrSpiTmp = this.data1.SPI?.filter(item => item.PUMP_GRP === 3);
            this.thrSuji?.forEach((element, i) => {
                if (element?.PUMP_TYP == 2) {
                    if (this.data12?.length > 0) {
                        const data = this.data12
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.FREQ) == 0) {
                                    element.hz = parseFloat(item.FREQ).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.FREQ).toFixed(0)
                                }
                            }
                        })
                    }
                    else {
                        const data = this.thrSpiTmp
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.value) == 0) {
                                    element.hz = parseFloat(item.value).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.value).toFixed(0)
                                }
                            }
                        })
                    }
                }
                if (element.value === "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else {
                    element.opacity = '1.0'
                    element.value = "On"
                }
                if (this.data10[i]?.value == "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else if (this.data10[i]?.value == "On") {
                    element.opacity = '1.0'
                    element.value = "On"
                }
            })
            this.thrPump.title = this.data10?.data[0]?.PUMP_GRP_NM || this.thrPressTmp[0]?.PUMP_GRP_NM
            if (this.data10?.data?.length > 0) {
                if (this.data10.data[0] == null) {
                    this.thrPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 3);
                    this.thrPressTmp.forEach(item => {
                        thrPressSum += Number(item.value)
                    })
                    this.thrFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 3);
                    this.thrFluxTmp.forEach(item => {
                        thrFluxSum += Number(item.value)
                    })
                }
                else {
                    this.data10?.data?.forEach(item => {
                        thrPressSum += item?.TUBE_PRSR_PRDCT
                        thrFluxSum += item?.PRDCT_MEAN
                        if (thrPressSum === 0) {
                            this.thrPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 3);
                            this.thrPressTmp.forEach(item => {
                                thrPressSum += Number(item.value)
                            })
                        }
                        if (thrFluxSum === 0) {
                            this.thrFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 3);
                            this.thrFluxTmp.forEach(item => {
                                thrFluxSum += Number(item.value)
                            })
                        }
                    })
                }
            }
            else {
                this.thrPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 3);
                this.thrPressTmp.forEach(item => {
                    thrPressSum += Number(item.value)
                })
                this.thrFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 3);
                this.thrFluxTmp.forEach(item => {
                    thrFluxSum += Number(item.value)
                })
            }
            this.thrPump.sub[0].value = addCommaNumber(thrPressSum)
            this.thrPump.sub[1].value = addCommaNumber(thrFluxSum)
            this.pumpClass = 'row-cols-1'
        }
        if (this.data1.pumpStatus?.filter(item => item.PUMP_GRP === 4).length > 0) {
            this.fouSuji = JSON.parse(JSON.stringify(this.data1?.pumpStatus?.filter(item => item.PUMP_GRP === 4)));
            this.fouPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 4);
            this.fouSpiTmp = this.data1.SPI?.filter(item => item.PUMP_GRP === 4);
            this.fouSuji?.forEach((element, i) => {
                if (element?.PUMP_TYP == 2) {
                    if (this.data13?.length > 0) {
                        const data = this.data13
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.FREQ) == 0) {
                                    element.hz = parseFloat(item.FREQ).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.FREQ).toFixed(0)
                                }
                            }
                        })
                    }
                    else {
                        const data = this.fouSpiTmp
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.value) == 0) {
                                    element.hz = parseFloat(item.value).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.value).toFixed(0)
                                }
                            }
                        })
                    }
                }
                if (element.value === "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else {
                    element.opacity = '1.0'
                    element.value = "On"
                }
                if (this.data11[i]?.value == "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else if (this.data11[i]?.value == "On") {
                    element.opacity = '1.0'
                    element.value = "On"
                }
            })
            this.fouPump.title = this.data11?.data[0]?.PUMP_GRP_NM || this.fouPressTmp[0]?.PUMP_GRP_NM
            if (this.data11?.data?.length > 0) {
                if (this.data11.data[0] == null) {
                    this.fouPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 4);
                    this.fouPressTmp.forEach(item => {
                        fouPressSum += Number(item.value)
                    })
                    this.fouFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 4);
                    this.fouFluxTmp.forEach(item => {
                        fouFluxSum += Number(item.value)
                    })
                }
                else {
                    this.data11?.data?.forEach(item => {
                        fouPressSum += item?.TUBE_PRSR_PRDCT
                        fouFluxSum += item?.PRDCT_MEAN
                        if (fouPressSum === 0) {
                            this.fouPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 4);
                            this.fouPressTmp.forEach(item => {
                                fouPressSum += Number(item.value)
                            })
                        }
                        if (fouFluxSum === 0) {
                            this.fouFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 4);
                            this.fouFluxTmp.forEach(item => {
                                fouFluxSum += Number(item.value)
                            })
                        }
                    })
                }
            }
            else {
                this.fouPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 4);
                this.fouPressTmp.forEach(item => {
                    fouPressSum += Number(item.value)
                })
                this.fouFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 4);
                this.fouFluxTmp.forEach(item => {
                    fouFluxSum += Number(item.value)
                })
            }
            this.fouPump.sub[0].value = addCommaNumber(fouPressSum)
            this.fouPump.sub[1].value = addCommaNumber(fouFluxSum)
            this.pumpClass = 'row-cols-1'
        }

        if (this.data1.pumpStatus?.filter(item => item.PUMP_GRP === 5).length > 0) {
            this.fivSuji = JSON.parse(JSON.stringify(this.data1?.pumpStatus?.filter(item => item.PUMP_GRP === 5)));
            this.fivPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 5);
            this.fivSpiTmp = this.data1.SPI?.filter(item => item.PUMP_GRP === 5);
            this.fivSuji?.forEach((element, i) => {
                if (element?.PUMP_TYP == 2) {
                    if (this.data16?.length > 0) {
                        const data = this.data16
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.FREQ) == 0) {
                                    element.hz = parseFloat(item.FREQ).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.FREQ).toFixed(0)
                                }
                            }
                        })
                    }
                    else {
                        const data = this.fivSpiTmp
                        data.forEach(item => {
                            if (item.PUMP_GRP_IDX == element.PUMP_IDX) {
                                if (parseInt(item.value) == 0) {
                                    element.hz = parseFloat(item.value).toFixed(2)
                                } else {
                                    element.hz = parseFloat(item.value).toFixed(0)
                                }
                            }
                        })
                    }
                }
                if (element.value === "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else {
                    element.opacity = '1.0'
                    element.value = "On"
                }
                if (this.data15[i]?.value == "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else if (this.data15[i]?.value == "On") {
                    element.opacity = '1.0'
                    element.value = "On"
                }
            })
            this.fivPump.title = this.data15?.data[0]?.PUMP_GRP_NM || this.fivPressTmp[0]?.PUMP_GRP_NM
            if (this.data15?.data?.length > 0) {
                if (this.data15.data[0] == null) {
                    this.fivPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 5);
                    this.fivPressTmp.forEach(item => {
                        fivPressSum += Number(item.value)
                    })
                    this.fivFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 5);
                    this.fivFluxTmp.forEach(item => {
                        fivFluxSum += Number(item.value)
                    })
                }
                else {
                    this.data15?.data?.forEach(item => {
                        fivPressSum += item?.TUBE_PRSR_PRDCT
                        fivFluxSum += item?.PRDCT_MEAN
                        if (fivPressSum === 0) {
                            this.fivPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 5);
                            this.fivPressTmp.forEach(item => {
                                fivPressSum += Number(item.value)
                            })
                        }
                        if (fivFluxSum === 0) {
                            this.fivFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 5);
                            this.fivFluxTmp.forEach(item => {
                                fivFluxSum += Number(item.value)
                            })
                        }
                    })
                }
            }
            else {
                this.fivPressTmp = this.data1.PRI?.filter(item => item.PUMP_GRP === 5);
                this.fivPressTmp.forEach(item => {
                    fouPressSum += Number(item.value)
                })
                this.fivFluxTmp = this.data1.FRI?.filter(item => item.PUMP_GRP === 5);
                this.fivFluxTmp.forEach(item => {
                    fouFluxSum += Number(item.value)
                })
            }
            this.fivPump.sub[0].value = addCommaNumber(fivPressSum)
            this.fivPump.sub[1].value = addCommaNumber(fivFluxSum)
            this.pumpClass = 'row-cols-1'
        }
      
    },
    methods: {
        changePumpControlRig(firStatus, secStatus, thrStatus, fouStatus, fivStatus) {
            this.firStatus = firStatus
            this.secStatus = secStatus
            this.thrStatus = thrStatus
            this.fouStatus = fouStatus
            this.fivStatus = fivStatus
            if (this.tabIndex === 0) {
                this.firSuji?.forEach((item, index) => {
                    this.$refs.FirPumpArea[index]?.changeAutoPart(firStatus)
                })
            }
            if (this.tabIndex === 1) {
                this.secSuji?.forEach((item, index) => {
                    this.$refs.SecPumpArea[index]?.changeAutoPart(secStatus)
                })
            }
            if (this.tabIndex === 2) {
                this.thrSuji?.forEach((item, index) => {
                    this.$refs.ThrPumpArea[index]?.changeAutoPart(thrStatus)
                })
            }
            if (this.tabIndex === 3) {
                this.fouSuji?.forEach((item, index) => {
                    this.$refs.FouPumpArea[index]?.changeAutoPart(fouStatus)
                })
            }
            if (this.tabIndex === 4) {
                this.fivSuji?.forEach((item, index) => {
                    this.$refs.FivPumpArea[index]?.changeAutoPart(fivStatus)
                })
            }
        },
        changePumpOnOff(data) {
            
            this.firSuji?.forEach((element, i) => {
                if (data[i]?.value == "Off") {
                    element.opacity = '0.25'
                    element.value = "Off"
                } else if (data[i]?.value == "On") {
                    element.opacity = '1.0'
                    element.value = "On"
                }
            })
        }
    }
}
</script>

<style>
.pump_img {
    background: url("@/assets/img/peakcontrol/pump_peakcontrol.png") no-repeat;
    background-size: 34%;
    background-position: center;
    text-align: left;
    text-indent: 5%;
    mix-blend-mode: color-dodge;
}

.pump_area_h35 {
    height: 39%;
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

.detail_text {
    width: 70%;
    text-shadow: 0 0 9px #5cafff;
    color: #c3eaff;
}

.pump_area_h4 {
    height: calc(100%/ 4);
    width: calc(100%);
}

.detail_value {
    width: 30%;
    font-family: LAB디지털;
    text-align: right;
}

.detail_textWrap {
    width: calc(100% - 11px);
    display: flex;
    align-items: center;
    margin: 10px 15px;
    font-size: 18px;
    font-family: 'KHNPHDRegular';
    color: #fff;
}

.circle-dot {
    max-height: 85%;
    border-style: dotted;
    border-color: #546b7d;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 2%;
    white-space: normal;
}
</style>