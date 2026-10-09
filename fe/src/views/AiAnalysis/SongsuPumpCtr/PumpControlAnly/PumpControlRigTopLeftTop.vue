<template>
    <div class="plate_areaForTop w-100">
        <div class="detail_textWrap">
            <div class="detail_text" :style="{
                fontSize: '18px', width: '40%'
            }">최소요구관압<br>기준 배수지</div>
            <span class="detail_value" :style="{ fontFamily: 'KHNPHDRegular', width: '60%', textAlign: 'center' }">{{
                this.name }}</span>
        </div>
        <div class="detail_textWrap">
            <div class="detail_text" :style="{
                fontSize: '19px'
            }">최소요구관압 (분기점)</div>
            <span class="detail_value">{{ this.point }}</span>
            <div class="detail_text" style="font-size:14px">kg/cm²</div>
        </div>
        <div class="detail_textWrap" v-if="pipe">
            <div class="detail_text">최소요구관압</div>
            <span class="detail_value">{{ this.pres }}</span>
            <div class="detail_text" style="font-size:14px">kg/cm²</div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['data4'],
    data() {
        return {
            name: '',
            point: '',
            pres: '',
            pipe: ''
        }
    },
    mounted() {
        if (this.$area == 'unmun') {
            this.pipe = false
        }
        else {
            this.pipe = true
        }
    },
    updated() {
    },
    methods: {
        settingValue(data) {
            this.name = data?.name
            this.point = data?.point
            this.pres = data?.pres
        }
    }
}
</script>

<style>
.detail_textWrap {
    width: calc(100% - 11px);
    display: flex;
    align-items: center;
    margin: 30px 15px;
    font-size: 18px;
    font-family: 'KHNPHDRegular';
    color: #fff;
}

.plate_areaForTop {
    background: url("@/assets/img/plate_img.png") no-repeat;
    background-size: 100% 20%;
    background-position-y: 163px;
    height: 200px
}
</style>