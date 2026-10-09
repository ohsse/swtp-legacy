<template>
    <b-col>
        <div class="month mb-3">{{ data.month }}월</div>
        <div class="showwant">
            <div class="month_left">
                <div class="row1">
                    <div class="posif">목표량</div>
                    <div id="1월목표량" class=" bottom_middle_val">{{ data.targetVal }}</div>
                </div>
                <div class="row1">
                    <div class="posif">사용량</div>
                    <div id="1월" class="bottom_middle_val">{{ data.useVal }}</div>
                </div>
            </div>
            <div class="month_right">
                <div id="1per" class="persent">{{ data.persent }}%</div>
            </div>
        </div>
    </b-col>
</template>
<script>
export default {
    props: {
        data: {
            type: Object,
            required: true
        }
    },
    mounted() {
     
    }
}
</script>

<style scoped>
.month {
    color: white;
    height: 20px;
    display: inline-block;
    font-weight: bolder;
    font-size: 18px;
}

.showwant {
    background-image: url(/src/assets/img/soure_pump.png);
    height: 140px;
    background-repeat: no-repeat;
    background-size: 100% 100%;
}

.month_left {
    float: left;
    width: 67%;
    height: 50%;
}

.month_right {
    float: left;
    width: 28%;
    height: 85%;
    display: flex;
    justify-content: center;
    align-items: center;
}

.row1 {
    height: 100%;
    display: flex;
    align-items: center;
}

.posif {
    width: 29%;
    color: skyblue;
    display: inline-block;
    margin: 0px 0px 0px 10px;
    font-weight: bolder;
}

.persent {
    color: white;
    font-size: 20px;
    font-weight: bolder;
}

.bottom_middle_val {
    text-shadow: 0 0 9px #5cafff;
    font-size: 19px;
    font-weight: normal;
    font-stretch: normal;
    font-style: normal;
    letter-spacing: normal;
    color: #fff;
    font-family: 'LAB디지털';
    text-align: right;
}
</style>