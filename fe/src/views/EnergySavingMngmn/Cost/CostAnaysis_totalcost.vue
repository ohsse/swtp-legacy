<template>
    <b-col xl="12">
        <div class="position-relative border-small border_img" v-bind:style="{ height: '330px' }">
            <div class="layerGreen h-100">
                <div class="center_toptitle"></div>
                <div class="center_contents cost_aura cost_main"></div>
                <div class="center_contents cost_spring"></div>
                <div class="center_contents cost_plate cost_main"></div>
                <div class="center_contents cost_bottom"></div>
                <div class="center_contents main_text_box text-center">
                    <span id="main_cost" class="main_font" v-bind:style="{ lineHeight: '3' }" v-text="month + '월'"></span>
                    <span id="main_cost" class="main_font" v-bind:style="{ lineHeight: '3' }"> 전체요금</span><br>
                    <span class="main_font" id="TOT_FEE_MAIN"
                    v-if="costValue"   
                    v-bind:style="{ fontFamily: 'LAB디지털 !important', fontSize: '50px' }" v-text="cost" ></span>
                    <span class="main_font" id="TOT_FEE_MAIN"
                    v-if="!costValue"   
                    v-bind:style="{ fontFamily: 'LAB디지털 !important', fontSize: '50px' }" >0</span>
                    <span class="main_font"> 원</span>
                </div>
            </div>
        </div>
    </b-col>
</template>

<script>
export default {
    data() {
        return {
            cost: null,
            month: null,
            costValue : ''
        }
    },
    methods: {
        setMonth(month) {
            this.month = month
        },
        setTotal(cost) {
            if(cost == null){
                this.costValue = false
            }else{
                this.costValue = true
                this.cost = cost
            }

        }
    }

}
</script>
<style scoped>
.layerGreen {
    background-image: url(/src/assets/img/layerGreen.png);
    background-size: 100% 100%;
}

.center_toptitle {
    background-image: url(/src/assets/img/squreTitle.png);
    background-repeat: no-repeat;
    background-size: 100% 100%;
    width: 20%;
    height: 6%;
    position: absolute;
    top: 4%;
    left: 4%;
}

.cost_main {
    mix-blend-mode: overlay;
    position: absolute;
    background-repeat: no-repeat;
}

.cost_aura {
    background-image: url(/src/assets/img/cost_aura.png);
    background-size: 100% 100%;
    height: 85%;
    width: 50%;
}

.center_contents {
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.cost_spring {
    background-image: url(/src/assets/img/cost_spring.png);
    background-size: 100% 100%;
    height: 42%;
    width: 56%;
    position: absolute;
    background-repeat: no-repeat;
    mix-blend-mode: color-dodge;
}

.cost_main {
    mix-blend-mode: overlay;
    position: absolute;
    background-repeat: no-repeat;
}

.cost_plate {
    background-image: url(/src/assets/img/plate_aura.png);
    background-size: 100% 100%;
    height: 18%;
    width: 50%;
    margin-top: 10%;
}

.cost_bottom {
    background-image: url(/src/assets/img/bottom_aura.png);
    background-size: 100% 100%;
    height: 24%;
    width: 69%;
    margin-top: 14%;
    mix-blend-mode: color-dodge;
    position: absolute;
    background-repeat: no-repeat;
}

.main_text_box {
    position: absolute;
    mix-blend-mode: color-dodge;
}

.main_font {
    text-shadow: 0 0 9px #000000;
    font-size: 40px;
    font-family: KHNPHDRegular;
    letter-spacing: normal;
    color: #fbfbfb;
    align-self: center;
    font-weight: 700;
}
</style>