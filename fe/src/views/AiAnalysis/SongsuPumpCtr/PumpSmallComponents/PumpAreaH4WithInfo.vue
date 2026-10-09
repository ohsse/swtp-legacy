<template>
    <b-col>
        <div class="pump_area_h4 pump_img fL"
            :style="{ opacity: this.items.opacity, height: pumpHeight + 'px', width: '50%', backgroundSize: pumpBackground + '% !important' }">
            #{{ items.PUMP_IDX }}
        </div>
        <span v-if="items.hz" style="float: left;"><span class="input_design"
                :style="{ height: '30px', float: 'center', marginRight: '3px' }">{{ items.hz
                }}</span>Hz</span>
        <on-off :style="{ marginTop: pumpHeight / 7 + '%', marginBottom: '10px', height: 25 + 'px', width: '25%' }"
            :pumpData="items.value" />
        <auto-part ref="AutoPart" :autoData="this.autoData" :style="{ height: pumpHeight / 6 + 'px', width: '50%' }" />
    </b-col>
</template>

<script>
import OnOff from '@/components/ComponentCommon/OnOff.vue';
import AutoPart from '@/components/ComponentCommon/AutoPart.vue';

export default {
    components: {
        OnOff,
        AutoPart
    },
    props: ['items', 'index', 'length', 'order'],
    data() {
        return {
            pumpHeight: 780 / this.length,
            pumpBackground: 90,
        }
    },
    mounted() {
        if (this.$area === 'buan') {
            this.pumpHeight = 120
        } else {
            this.pumpHeight = 780 / this.length
        }
    },
    methods: {
        changeAutoPart(status) {
            this.autoData = parseInt(status)
            if (this.$refs.AutoPart) {
                this.$refs.AutoPart.pumpOnOff(this.autoData)
            }
        }
    }
}
</script>

<style>
.pump_area_h4 {
    height: calc(100%/ 4);
    width: calc(100%);
}

.pump_img {
    background: url("@/assets/img/peakcontrol/pump_peakcontrol.png") no-repeat;
    background-size: 34%;
    background-position: center;
    text-align: left;
    text-indent: 5%;
    mix-blend-mode: color-dodge;
}
</style>