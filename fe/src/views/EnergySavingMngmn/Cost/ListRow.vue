<template>
    <div class="d-flax align-items-center seasonFont" style='width:100%; margin : 10px 0 15px 0; display: flex; justify-content: center;'>
        <div style='width: 10%;'><span v-text="row.STN_TM"></span>시</div>
        <div style='width: 12%;' :style="textColor" v-text="load"></div>
        <div style='width: 28%;'><span> 기본요금 : </span><span class='text_number' style='font-family: LAB디지털;  font-size: 22px;' v-text="row.BASE_RATE"></span><span style='margin-left: 5px;'>(원/kW)</span></div>
        <div style='width: 40%;'><span> 전기사용요금 : </span><span class='text_number'  style='font-family: LAB디지털;  font-size: 22px;' v-text="row.ELCTR_RATE"></span><span style='margin-left: 5px;'>(원/kWh)</span></div>
    </div>
</template>
<script>
export default {
    props:{
        row:{
            type: Object,
            required: true
        }
    },
    data(){
        return{
            textColor:{
                color : '#00ff0096'
            },
            load : "경부하"
        }
    },
    mounted(){
        switch(this.row.TIMEZONE){
            case "L":
                this.load = "경부하";
                this.textColor.color = '#00ff0096';
                break;
            case "M":
                this.load = "중간부하";
                this.textColor.color = '#ffff0096';
                break;
            case "H":
                this.load = "최대부하";
                this.textColor.color = '#ff3333d9';
                break;
        }
    }
}
</script>
<style scoped>
.seasonFont {
    /* text-shadow: 0 0 9px #5cafff; */
    font-size: 18px;
    /* color: #fff; */
    color: #d7d7d7cf;
    font-family: 'KHNPHDRegular';
    text-align: left;
}
</style>