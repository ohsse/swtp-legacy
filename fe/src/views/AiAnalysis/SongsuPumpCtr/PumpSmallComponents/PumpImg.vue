<template>
    <div :class="className" :style="data.style">{{ num }}</div>
    <div v-if="data.input" class="fL" style="background-size: 80%; height: 25px; width: 100%; display: flex; align-items: center; justify-content: center; font-size: 18px;">
        <span class="input_design" style="margin-right: 10px; height:100%;">{{ data.input.value }}</span>Hz
    </div>
</template>
<script>
export default{
    props:[
        'data', 'className', 'num'
    ]
}
</script>
<style>
.pump_img {
    background: url(@/assets/img/peakcontrol/pump_peakcontrol.png) no-repeat;
    background-size: 28%;
    background-position: center;
    text-align: left;
    text-indent: 20%;
    mix-blend-mode: color-dodge;
}
.pump_area_h4 {
    height: calc(100%/ 4 );
    width: calc(100% );
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
}
</style>