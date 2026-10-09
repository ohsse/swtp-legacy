<template >
    <b-col>
        <div class="pump_area_h4 pump_img fL"
            :style="{ opacity: this.items.opacity, height: pumpHeight + 'px', width: '100%', backgroundSize: '80% !important' }">
            #{{ this.index + 1 }}</div>
    </b-col>
</template>
<script>
export default {
    props: ['items', 'index', 'length'],
    data() {
        return {
            pumpHeight: 780 / this.length,
        }
    },
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