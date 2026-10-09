<template>
    <div class="value-area" :style="gumiValueArea">
        <div class="value-val hold" :style="gumiValueVal">펌프임계값<br />9.5mm/s</div>
        <div class="value-val hold yellow" :style="gumiValueVal">
            모터임계값<br />9.5mm/s
        </div>
    </div>
</template>
<script>
export default {
    props: ['pumpValue', 'motorValue', 'area'],
    data() {
        return {
            gumiValueArea: '',
            gumiValueVal: ''
        }
    },
    computed: {
        pumpAmpValue() {
            const pumpAmpThreshold = this.pumpValue.find(obj => obj.eq_type === 'pump' && obj.graph_type === 'de_rms_amp');
            return pumpAmpThreshold ? pumpAmpThreshold.th_value : '0';
        },
        motorAmpValue() {
            const motorAmpThreshold = this.motorValue.find(obj =>obj.eq_type === 'motor' && obj.graph_type === 'de_rms_amp');
            return motorAmpThreshold ? motorAmpThreshold.th_value : '0';
        }
    },
    beforeUpdate() {
        if (this.area === 'gumi') {
            this.gumiValueArea = 'width:140px; height:190px'
            this.gumiValueVal = 'height:90px; font-size:20px;line-height: 40px;'
        }
        else {
            this.gumiValueArea = ''
            this.gumiValueVal = ''
        }
    },
}
</script>
<style lang="">
    
</style>