<template>
    <div class="w-100 position-relative p-3 pumpMid"
        :style="{ height: 'calc(83% - 40px)', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '15px' }">
        <img class="d-flex justify-content-start" :src="require(`@/assets/img/toptitle.png`)"
            :style="{ position: 'absolute', top: '15px', left: '0', width: '150px', height: '25px' }" />
        <template v-if="(this.$area != 'gunsan' && this.$area != 'gosan' && this.tabIndex != 2 && this.tabIndex != 1
            && this.$area != 'unmun') || this.$area == 'goryeong'">
            <div :style="{ height: 'calc(100%/4)', height: '100%', width: '100%', marginBottom: '15px' }">
                <div class="pump_div" v-for="(element) in major" :key="element"
                    :style="{ height: '100px', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '13px', marginTop: '30px' }">
                    <BigInflowStatus :inflowVal="item" v-for="item in element" v-bind:key="item" :style="{
                        marginBottom: 40 / major.length + 'px'
                    }" />
                </div>
            </div>
        </template>

        <BigInflowStatusForGunsan v-if="this.$area === 'gunsan'" ref="ForGunsan" />
        <BigInflowStatusForGosan v-if="this.$area === 'gosan'" ref="ForGosan" />
        <BigInflowStatusForBuan v-if="this.$area === 'buan' && this.tabIndex === 2" ref="ForBuan" />
        <BigInflowStatusForBuanForThree v-if="this.$area === 'buan' && this.tabIndex === 1" ref="ForBuanForThree" />
        <BigInflowStatusForUnmun v-if="this.$area === 'unmun'" ref="ForUnmun" />

        <img class="d-flex justify-content-end" :src="require(`@/assets/img/image (14).png`)"
            :style="{ width: '150px', height: '25px', position: 'absolute', right: '0', bottom: '0' /*marginTop: '3%', float: 'right'*/ }">

    </div>
</template>

<script>
import BigInflowStatus from '@/views/DashBoard/DashBoard/MainSmallComponents/BigInflowStatus.vue'
import BigInflowStatusForBuanForThree from '@/views/DashBoard/DashBoard/MainSmallComponents/BigInflowStatusForBuanForThree.vue'
import BigInflowStatusForGunsan from '@/views/DashBoard/DashBoard/MainSmallComponents/BigInflowStatusForGunsan.vue'
import BigInflowStatusForBuan from '@/views/DashBoard/DashBoard/MainSmallComponents/BigInflowStatusForBuan.vue'
import BigInflowStatusForGosan from '@/views/DashBoard/DashBoard/MainSmallComponents/BigInflowStatusForGosan.vue'
import BigInflowStatusForUnmun from '@/views/DashBoard/DashBoard/MainSmallComponents/BigInflowStatusForUnmun.vue'
export default {
    components: {
        BigInflowStatus,
        BigInflowStatusForGunsan,
        BigInflowStatusForGosan,
        BigInflowStatusForBuan,
        BigInflowStatusForBuanForThree,
        BigInflowStatusForUnmun
    },
    data() {
        return {
            data: [],
            tabIndex: -1
        }
    },
    props: ['major'],
    mounted() {
    },
    updated() {
        if (this.$refs.ForBuan) {
            this.$refs.ForBuan.settingData(this.data)
        }
        else if (this.$refs.ForBuanForThree) {
            this.$refs.ForBuanForThree.settingData(this.data)
        }
    },
    methods: {
        sendingData(major, tabIndex) {
            this.data = major
            this.tabIndex = tabIndex
            if (this.$refs.ForGunsan) {
                this.$refs.ForGunsan.settingData(major)
            }
            else if (this.$refs.ForGosan) {
                this.$refs.ForGosan.settingData(major)
            } else if (this.$refs.ForUnmun) {
                this.$refs.ForUnmun.settingData(major)
            }

        }
    }
}
</script>

<style>
.pumpMid {
    transform: scale(1, 1.2);
    transform-origin: top;
}

.pipeline-un-y {
    text-align: center;
    height: 100%;
    background: url(@/assets/img/analysis/pipeline_un_y.png) no-repeat;
    background-size: 35% 75%;
    background-position: 0% 50%
}

.pipeline-un-y-right {
    text-align: center;
    height: 100%;
    background: url(@/assets/img/analysis/pipeline_un_y.png) no-repeat;
    background-size: 35% 75%;
    background-position: 100% 50%
}
</style>