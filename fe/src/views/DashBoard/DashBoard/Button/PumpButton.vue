<template>
    <b-col>
        <div :class="className">{{pumpValue}}</div>
    </b-col>
</template>

<script>
export default {
    props:[
        'isSelect', 'pumpValue'
    ],
    data(){
        return{
            className:'dash_pump_tab pump_number '+(this.isSelect?'selected_tab':'')
        }
    }
}
</script>

<style>
.pump_number {
    font-family: 'LABDigital !important';
    font-size: 16px;
    color: #fff;
    text-align: center;
    line-height: 23px;
    }
.offPump {
    background-color: #5b49491f;
}
.dash_pump_tab {
    padding:2px;
    border: solid 1px #b4dffa;
    background-color: rgb(139 194 240 / 57%);
    cursor: pointer;
}
.selected_tab {
    color: #F8C314!important;
    border: solid 1px #F8C314!important;
    font-weight: bold;
}
</style>