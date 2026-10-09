<template>
    <b-row class="px-3">
        <div class="divid_line" :style="{ height: bgHeight + 'px' }">
            <b-col class="pt-0">
                <h5 class="dash_title" :style="{ height: '50px'/*lineHeight: '25px', marginBottom: dashMargin*/ }">{{
                    this.title ? this.title.replace(/[^가-힣]/g, "")
                        : 'NoData' }}
                </h5>
            </b-col>
            <b-col class="d-flex justify-content-start">
                <AiMode ref="AiMode" :autoData="this.autoData" :emerData="this.emerData" :index="this.index"
                    @changeAutoPart="changeAutoPart" :style="{ marginBottom: aiMargin }" />
            </b-col>
            <b-col class="mx-3 pt-1">
                <div v-for="(item) in data" :key="item"
                    style="display: flex; flex-direction: row; flex-wrap: wrap; align-items: center; color: #d4eaf6; text-shadow: 0 0 8px #5cafff; font-size: 18px;"
                    :style="{ marginBottom: marginBottom + 'px' }">
                    <div style="flex: 0.8;">
                        {{ '펌프 #' + item.PUMP_IDX }}
                    </div>
                    <div>
                        <OnOff :pumpData="item.value"></OnOff>
                    </div>
                    <div>
                        <AutoPart ref="AutoPart" :autoData="this.autoData" :emerData="this.emerData"></AutoPart>
                    </div>
                </div>

            </b-col>
        </div>
    </b-row>
</template>

<script>
import AiMode from '@/views/Common/AiMode.vue';
import OnOff from '@/components/ComponentCommon/OnOff.vue';
import AutoPart from '@/components/ComponentCommon/AutoPart.vue';
export default {
    components: {
        AiMode,
        OnOff,
        AutoPart
    },
    props: ['bgHeight', 'title', 'data', 'index'],
    data() {
        return {
            marginBottom: 5,
            dashMargin: '20px',
            aiMargin: '20px',
            autoData: '',
            emerData: ''
        }
    },
    updated() {
    },
    mounted() {
        if (this.$area === 'buan') {
            this.marginBottom = 1
            this.dashMargin = '10px'
            this.aiMargin = '20px'
        }
        else {
            this.marginBottom = 5
            this.dashMargin = '20px'
            this.aiMargin = '20px'
        }
    },
    methods: {
        changeAutoPart(status, emerStatus, update = false) {
            this.autoData = parseInt(status)
            this.emerData = parseInt(emerStatus)
            this.$refs.AiMode.changeAuto(this.autoData, this.emerData);
            if (this.$refs.AutoPart) {
                this.data.forEach((item, index) => {
                    this.$refs.AutoPart[index].pumpOnOff(this.autoData)
                })
            }
            if (update == true) {
                this.$emit('initAiData')
            }
        }
    }
}
</script>

<style>
.waterwall_back_gosan {
    position: absolute;
    top: 143px;
    left: 0;
    width: 1590px;
    height: 690px;
    background: url(@/assets/img/local_geumgang/gosan/waterwall_gosan.png) no-repeat;
    background-size: 67% 97%;
    background-position: 56% 83%;
}

.offPump {
    background-color: #5b49491f !important;
}

.off_pump_img {
    width: 250px;
    height: 60px;
    background: #1A406F;
    opacity: 0.8;
    align-self: center;
    color: #F8C314;
    font-size: 21px;
    font-weight: bold;
    font-family: KHNPHDRegular;
    border: 2px solid #00C0FF;
    text-align: center;
    line-height: 57px;
    letter-spacing: 5px;
}

.pump_name {
    color: rgb(255, 255, 255);
    font-size: 21px;
    line-height: 57px;
    letter-spacing: 5px;
    position: absolute;
    bottom: 0;
    right: 56px;
    font-family: LAB디지털 !important;
}

.pump_name_unit {
    font-family: KHNPHDRegular;
    font-size: 17px;
    color: #c3eaff;
    margin-left: 2px;
    line-height: 57px;
    letter-spacing: 5px;
    position: absolute;
    bottom: 0;
    right: 15px;
}

.carousel_vertical .carousel__track {
    height: 150px;
}

.carousel__viewport {
    height: 100%;
}

.carousel_vertical .carousel__item {
    /* min-height: 200px; */
    width: 100%;
    height: 150px;
    background-color: var(--vc-clr-primary);
    color: var(--vc-clr-white);
    font-size: 20px;
    border-radius: 8px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.carousel__item img {
    width: 100%;
    height: 100%;
}

.carousel__prev,
.carousel__next {
    color: #007aff;
}

.slide-img-btn div {
    display: inline;
}

ul.slide-img-btn li:nth-child(3n) {
    margin-right: 0;
}




.green_round {
    width: 105px;
    height: 100%;
    color: #fff;
    text-shadow: 0 0 9px #5cafff;
    font-family: "KHNPHDRegular";
    background: url(@/assets/img/00_top_roundline_g.png) no-repeat;
    background-size: 100%;
    background-position: center;
    display: flex;
    font-size: 16px;
    align-items: center;
    justify-content: center;
    flex-direction: column;
}

.box-bg {
    background: url(@/assets/img/dash_top.png) no-repeat !important;
    background-size: 100% 100% !important;
    width: 270px;
    height: 100px;
    padding: 0px 25px;
    justify-content: unset;
}

.unit {
    font-size: 16px;
    color: #a4ceed;
    font-family: "KHNPHDRegular";
    margin-left: 5px;
}

.content__value-box {
    width: 140px;
    text-shadow: rgba(209, 250, 255, 0.5) 0px 0px 5px;
    font-size: 18px;
    text-align: right;
    color: rgb(242, 251, 255);
    font-family: LAB디지털 !important;
    background-position: center center;
}

.content__text-box {
    width: px;
    background-size: 100% 20px;
    background-position-y: bottom;
    text-shadow: 0 0 9px #5cafff;
    font-family: KHNPHUotfR;
    font-size: 16px;
    line-height: 1.5;
    text-align: left;
    color: #fff;
}

.animationTItle-two {
    width: 100%;
    display: flex;
    overflow: hidden;
    flex-direction: column-reverse;
    height: 48px;
}

.animationTItle {
    width: 100%;
    display: flex;
    overflow: hidden;
    flex-direction: column-reverse;
    height: 24px;
}


.right_box1 {
    width: 83%;
    height: 30%;
    align-self: center;
    display: flex;
}

.right_box2 {
    width: 83%;
    height: 33%;
    align-self: center;
}

.right_box3 {
    width: 83%;
    height: 30%;
    align-self: center;
}

.dash_right {
    height: 100%;
    width: 25%;
    float: left;
}

.div_right {
    width: 100%;
    height: 99%;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
}

.right_title_div {
    height: 18%;
    width: 100%;
}
</style>