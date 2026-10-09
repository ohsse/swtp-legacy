<template>
    <div class="value-area2" :style="gumiValueArea2">
        <PumpTitle :item="item.pump_de_amp_val" title="펌프 부하" index="1" :area="area" />
        <PumpTitle :item="item.pump_nde_amp_val" title="펌프 반부하" index="2" :area="area" />
        <PumpTitle :item="item.motor_de_amp_val" title="모터 부하" index="3" :area="area" />
        <PumpTitle :item="item.motor_nde_amp_val" title="모터 반부하" index="4" :area="area" />
    </div>
</template>
<script>
import PumpTitle from '@/views/PumpControl/PumpContentContainer/PumpTitleArea/PumpTitle.vue';
export default {
    components: {
        PumpTitle
    },
    props: ['item', 'area'],
    data() {
        return {
            gumiValueArea2: '',
        }
    },
    beforeUpdate() {
        if (this.area === 'gumi') {
            this.gumiValueArea2 = 'width:230px; height:190px;'
        }
        else {
            this.gumiValueArea2 = ''
        }
    },
}
</script>
<style lang="">
    
</style>