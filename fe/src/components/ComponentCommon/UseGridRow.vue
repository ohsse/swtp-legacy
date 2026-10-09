<template>
    <b-row class="table_image">
        <b-col xl="2">{{ items.type }}</b-col>
        <b-col xl="6" class="bottom_all2">
            <b-row class="align-itemss-center">
                <b-col xl="2" class="use-cost" style="padding-right: 4px;">사용량</b-col>
                <div class="perImgDiv">
                    <b-col xl="10" ref="usePerImg" class="graph-bar" :style="{ width: items.usePer + '%' }"></b-col>
                </div>
            </b-row>
            <b-row>
                <b-col xl="2" class="use-cost" style="padding-right: 4px;">비용</b-col>
                <div class="perImgDiv">
                    <b-col xl="10" ref="costPerImg" class="graph-bar" :style="{ width: items.costPer + '%' }"></b-col>
                </div>
            </b-row>
        </b-col>

        <b-col xl="1" class="bottom_all3">
            <b-row class="bottom_all2 text-align-right">{{ items.usePer }}%</b-row>
            <b-row class="bottom_all2 text-align-right">{{ items.costPer }}%</b-row>
        </b-col>

        <b-col xl="3" class="bottom_all5">
            <b-row class="bottom_all2 text-align-right align-end">{{ items.useVal }} kWh</b-row>
            <b-row class="bottom_all2 text-align-right align-end">{{ items.costVal }} 원</b-row>
        </b-col>
    </b-row>
</template>

<script>

export default {
    props: ["items", "useUnit", "costUnit"],
    data() {
        return {
        }
    },
    mountd() {

    },
    methods: {
    },

}
</script>

<style>
.perImgDiv {
    width: 82%;
    padding: 0;
    height: 22.5px;
    display: flex;
    align-items: center;
}

.table_image {
    height: 62px;
    background-image: url(/src/assets/img/div_new.png);
    background-size: 100% 100%;
    text-align: center;
    margin-bottom: 4px;
    align-items: center;
}

.graph-bar {
    display: flex;
    background-image: url(/src/assets/img/percent_bar.png);
    background-size: 100% 100%;
    align-content: flex-start;
    height: 10px;
    padding-left: 1px;
    padding-right: 1px;
    mix-blend-mode: color-dodge;
}

.bottom_all2 {
    font-size: 15px;
    font-family: 'KHNPHDRegular';
    letter-spacing: normal;
    color: #c3eaff;
    font-weight: normal;
}

.text-align-right {
    text-align: right;
}

.use-cost {
    text-align: right;
    padding-left: 0;
}

.bottom_all3 {
    margin-left: 4px;
    padding-right: 0;
}

.bottom_all5 {
    margin-left: -4px;
}

.align-end {
    display: flex;
    justify-content: flex-end;
    padding-right: 12px;
}
</style>