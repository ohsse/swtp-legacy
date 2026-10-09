<template>
    <div class="chart_bar_div fL">
        <div style="width: 86%;height: 50%;display: flex;align-items: center;">
            <div class="bottom_all1 fL">{{ title }}</div>
            <div class="bottom_all1 fR" style="width: 30%; text-align: right;"><span class="bottom_fac_font_num">{{
                graphVal
            }}</span><span class="bottom_fac_font_unit">kW</span></div>
        </div>

        <div class="bottom_all4 fL">
            <div class="bottom_all3_1" style="position: relative;">
                <div class="chart_bar_base"></div>
                <div class="chart_bar" :style="'background-size: ' + graphSize + '% 100%;'"></div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: [
        'title', 'graphVal', 'graphSize'
    ]
}
</script>

<style>
.chart_bar {
    position: absolute;
    background: url(@/assets/img/percent_bar.png);
    background-size: 21% 100%;
    width: 100%;
    height: 100%;
    z-index: 5;
    background-repeat: no-repeat;
    transition: all linear .3s;
}

.chart_bar_base {
    position: absolute;
    background: url(@/assets/img/percent_bar_bg.png);
    background-size: 100% 100%;
    width: 100%;
    height: 100%;
    z-index: 4;
}

.bottom_all3_1 {
    height: 43%;
    text-align: left;
    margin: 10px 5px;
}

.bottom_all4 {
    width: 87%;
    height: 49%;
    font-size: 15px;
    font-family: 'KHNPHDRegular';
    letter-spacing: normal;
    color: #c3eaff;
}

.chart_bar_div {
    width: 100%;
    height: calc(85%/3);
    margin-left: 21px;
}

.chart_div {
    width: 89%;
    height: 75%;
    display: flex;
    flex-direction: column;
    margin-top: 8px;
}

.bottom_all1 {
    width: 70%;
    color: #fff;
    /*font-family: 'KHNPHDRegular';*/
    font-size: 14px;
    text-align: left;
    margin-left: 6px;
}
</style>