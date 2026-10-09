<template>
    <div :style="{ height: 'calc(100vh - 230px)' }">
        <div class="w-100 h-100" :style="{ textAlign: 'center', fontSize: '20px', color: 'white' }">
            <div v-if="firSuji.length > 0 && tabIndex === 0" class="fL w-100" :style="{ height: '56%' }">
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '15px 0 10px 0' }">
                    <DotCircleMain :data="firPump" :style="dotCircleStyle" />
                </div>
                <b-row :class="[pumpClass, 'fL', 'w-100']" :style="{ padding: '0px 0px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in firSuji" :key="item" :items="item" :index="index"
                        :length="firSuji.length" ref="FirPumpArea" />
                </b-row>

            </div>
            <div v-if="secSuji.length > 0 && tabIndex === 1" class="fL"
                :style="{ height: 'calc(39% - 2px)', width: 'calc(100% - 2px)' }">
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '10px 0' }">
                    <div class="fL w-100"
                        :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '15px 0 10px 0' }">
                        <DotCircleMain :data="secPump" :style="dotCircleStyle" />
                    </div>
                </div>
                <b-row :class="[pumpClass, 'fL', 'w-100']" :style="{ padding: '0px 0px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in secSuji" :key="item" :items="item" :index="index"
                        :length="secSuji.length" ref="SecPumpArea" />
                </b-row>
            </div>
            <div v-if="thrSuji.length > 0 && tabIndex === 2" class="fL"
                :style="{ height: 'calc(39% - 2px)', width: 'calc(100% - 2px)' }">
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '10px 0' }">
                    <div class="fL w-100"
                        :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '15px 0 10px 0' }">
                        <DotCircleMain :data="thrPump" :style="dotCircleStyle" />
                    </div>
                </div>
                <b-row :class="[pumpClass, 'fL', 'w-100']" :style="{ padding: '0px 0px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in thrSuji" :key="item" :items="item" :index="index"
                        :length="thrSuji.length" ref="ThrPumpArea" />
                </b-row>
            </div>
            <div v-if="fouSuji.length > 0 && tabIndex === 3" class="fL"
                :style="{ height: 'calc(39% - 2px)', width: 'calc(100% - 2px)' }">
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '10px 0' }">
                    <div class="fL w-100"
                        :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '15px 0 10px 0' }">
                        <DotCircleMain :data="fouPump" :style="dotCircleStyle" />
                    </div>
                </div>
                <b-row :class="[pumpClass, 'fL', 'w-100']" :style="{ padding: '0px 0px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in fouSuji" :key="item" :items="item" :index="index"
                        :length="fouSuji.length" ref="FouPumpArea" />
                </b-row>
            </div>
            <div v-if="fivSuji?.length > 0 && tabIndex === 4" class="fL"
                :style="{ height: 'calc(39% - 2px)', width: 'calc(100% - 2px)' }">
                <div class="fL w-100"
                    :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '10px 0' }">
                    <div class="fL w-100"
                        :style="{ height: '80px', display: 'flex', alignItems: 'center', padding: '15px 0 10px 0' }">
                        <DotCircleMain :data="fivPump" :style="dotCircleStyle" />
                    </div>
                </div>
                <b-row :class="[pumpClass, 'fL', 'w-100']" :style="{ padding: '0px 0px' }">
                    <PumpAreaH4WithInfo v-for="(item, index) in fivSuji" :key="item" :items="item" :index="index"
                        :length="fivSuji.length" ref="FivPumpArea" />
                </b-row>
            </div>
        </div>
    </div>
</template>

<script>
import DotCircleMain from '@/views/AiAnalysis/SongsuPumpCtr/PumpSmallComponents/DotCircleMain.vue'
import PumpAreaH4WithInfo from '@/views/AiAnalysis/SongsuPumpCtr/PumpSmallComponents/PumpAreaH4WithInfo.vue'
import { addCommaNumber } from '@/util/addCommaNumber'
export default {
    components: {
        DotCircleMain,
        PumpAreaH4WithInfo,
    },
    props: ['data', 'tabIndex'],
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
            thrStatus: '',
            fouStatus: '',
            fivStatus: '',
        }
    },
    mounted() {
    },
    updated() {
        if (this.$area === 'buan') {
            this.changePumpControlLeft(this.firStatus, this.secStatus, this.thrStatus, this.fouStatus, this.fivStatus)
        }
        else {
            this.changePumpControlLeft(this.firStatus, this.secStatus)
        }
    },
    beforeUpdate() {
        let firPressSum = 0
        let firFluxSum = 0
        let secPressSum = 0
        let secFluxSum = 0
        let thrPressSum = 0
        let thrFluxSum = 0
        let fouPressSum = 0
        let fouFluxSum = 0
        let fivPressSum = 0;
        let fivFluxSum = 0;
        if (this.data.pumpStatus?.filter(item => item.PUMP_GRP === 1).length > 0) {
            this.firSuji = JSON.parse(JSON.stringify(this.data.pumpStatus?.filter(item => item.PUMP_GRP === 1)));
            this.firPressTmp = this.data.PRI?.filter(item => item.PUMP_GRP === 1);
            this.firPressTmp.forEach(item => {
                firPressSum += Number(item.value)
            })
            this.firFluxTmp = this.data.FRI?.filter(item => item.PUMP_GRP === 1);
            this.firFluxTmp.forEach(item => {
                firFluxSum += Number(item.value)
            })
            this.firSpiTmp = this.data.SPI?.filter(item => item.PUMP_GRP === 1);
            this.firSuji?.forEach((element) => {
                if (element?.PUMP_TYP == 2) {
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
                if (element.value === "Off") {
                    element.opacity = '0.25'
                } else {
                    element.opacity = '1.0'
                }
            })
            this.firPump.title = this.firPressTmp[0]?.PUMP_GRP_NM
            this.firPump.sub[0].value = addCommaNumber(firPressSum)
            this.firPump.sub[1].value = addCommaNumber(firFluxSum)
        }
        if (this.$area == 'gosan') {
            this.firSuji = this.firSuji.reverse()
        }
        if (this.data.pumpStatus?.filter(item => item.PUMP_GRP === 2).length > 0) {
            this.secSuji = JSON.parse(JSON.stringify(this.data.pumpStatus?.filter(item => item.PUMP_GRP === 2)));
            this.secPressTmp = this.data.PRI?.filter(item => item.PUMP_GRP === 2);
            this.secPressTmp.forEach(item => {
                secPressSum += Number(item.value)
            })
            this.secFluxTmp = this.data.FRI?.filter(item => item.PUMP_GRP === 2);
            this.secFluxTmp.forEach(item => {
                secFluxSum += Number(item.value)
            })

            this.secSpiTmp = this.data.SPI?.filter(item => item.PUMP_GRP === 2);
            this.secSuji?.forEach((element) => {
                if (element.PUMP_TYP == 2) {
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
                if (element.value === "Off") {
                    element.opacity = '0.25'
                } else {
                    element.opacity = '1.0'
                }

            })
            this.secPump.title = this.secPressTmp[0]?.PUMP_GRP_NM
            this.secPump.sub[0].value = addCommaNumber(secPressSum)
            this.secPump.sub[1].value = addCommaNumber(secFluxSum)
        }
        if (this.data.pumpStatus?.filter(item => item.PUMP_GRP === 3).length > 0) {
            this.thrSuji = JSON.parse(JSON.stringify(this.data.pumpStatus?.filter(item => item.PUMP_GRP === 3)));
            this.thrPressTmp = this.data.PRI?.filter(item => item?.PUMP_GRP === 3);
            this.thrPressTmp.forEach(item => {
                thrPressSum += Number(item.value)
            })
            this.thrFluxTmp = this.data.FRI?.filter(item => item?.PUMP_GRP === 3);
            this.thrFluxTmp.forEach(item => {
                thrFluxSum += Number(item.value)
            })

            this.thrSpiTmp = this.data.SPI?.filter(item => item?.PUMP_GRP === 3);
            this.thrSuji?.forEach((element) => {
                if (element.PUMP_TYP == 2) {
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
                if (element.value === "Off") {
                    element.opacity = '0.25'
                } else {
                    element.opacity = '1.0'
                }

            })
            if (this.thrPressTmp.length > 0) {
                this.thrPump.title = this.thrPressTmp[0]?.PUMP_GRP_NM
            }
            this.thrPump.sub[0].value = addCommaNumber(thrPressSum)
            this.thrPump.sub[1].value = addCommaNumber(thrFluxSum)
        }
        if (this.data.pumpStatus?.filter(item => item.PUMP_GRP === 4).length > 0) {
            this.fouSuji = JSON.parse(JSON.stringify(this.data.pumpStatus?.filter(item => item.PUMP_GRP === 4)));
            this.fouPressTmp = this.data.PRI?.filter(item => item?.PUMP_GRP === 4);
            this.fouPressTmp.forEach(item => {
                fouPressSum += Number(item.value)
            })
            this.fouFluxTmp = this.data.FRI?.filter(item => item?.PUMP_GRP === 4);
            this.fouFluxTmp.forEach(item => {
                fouFluxSum += Number(item.value)
            })

            this.fouSpiTmp = this.data.SPI?.filter(item => item?.PUMP_GRP === 4);
            this.fouSuji?.forEach((element) => {
                if (element.PUMP_TYP == 2) {
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
                if (element.value === "Off") {
                    element.opacity = '0.25'
                } else {
                    element.opacity = '1.0'
                }

            })
            if (this.fouPressTmp.length > 0) {
                this.fouPump.title = this.fouPressTmp[0]?.PUMP_GRP_NM
            }
            this.fouPump.sub[0].value = addCommaNumber(fouPressSum)
            this.fouPump.sub[1].value = addCommaNumber(fouFluxSum)
        }
        if (this.data.pumpStatus?.filter(item => item.PUMP_GRP === 5).length > 0) {
            this.fivSuji = JSON.parse(JSON.stringify(this.data.pumpStatus?.filter(item => item.PUMP_GRP === 5)));
            this.fivPressTmp = this.data.PRI?.filter(item => item?.PUMP_GRP === 5);
            this.fivPressTmp.forEach(item => {
                fivPressSum += Number(item.value)
            })
            this.fivFluxTmp = this.data.FRI?.filter(item => item?.PUMP_GRP === 5);
            this.fivFluxTmp.forEach(item => {
                fivFluxSum += Number(item.value)
            })

            this.fivSpiTmp = this.data.SPI?.filter(item => item?.PUMP_GRP === 5);
            this.fivSuji?.forEach((element) => {
                if (element.PUMP_TYP == 2) {
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
                if (element.value === "Off") {
                    element.opacity = '0.25'
                } else {
                    element.opacity = '1.0'
                }

            })
            if (this.fivPressTmp.length > 0) {
                this.fivPump.title = this.fivPressTmp[0]?.PUMP_GRP_NM
            }
            this.fivPump.sub[0].value = addCommaNumber(fivPressSum)
            this.fivPump.sub[1].value = addCommaNumber(fivFluxSum)
        }

    },
    methods: {
        changePumpControlLeft(firStatus, secStatus, thrStatus, fouStatus, fivStatus) {
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
        }

    }
}
</script>

<style></style>
