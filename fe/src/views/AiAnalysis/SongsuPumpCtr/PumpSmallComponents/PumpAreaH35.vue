<template >
    <b-col>
        <div class="pump_area_h35 pump_img fL"
            :style="{ backgroundSize: '65%', opacity: this.items.opacity, width: '125%', height: '80px' }">#{{ this.index +
                1 }}
        </div>
        <div v-if="typeof this.items.hz !== 'undefined'" class="fL w-100"
            :style="{ backgroundSize: '80%', height: '30px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '5px' }">
            <span class="input_design" :style="{ marginRight: '10px', height: 'calc(100% - 2px)' }">{{ this.items.hz
            }}</span>Hz
        </div>
    </b-col>
</template>
<script>
export default {
    props: ['items', 'index'],
    mounted() {
    }
}
</script>
<style>
.pump_area_h35 {
    height: 39%;
    width: 100%;
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