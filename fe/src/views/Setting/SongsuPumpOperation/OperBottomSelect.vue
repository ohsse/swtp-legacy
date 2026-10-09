<template>
    <b-row>
        <b-col xl="1" class="d-flex justify-content-center align-items-end">
            <img src="@/assets/img/image_01.png" :style="{ width: '17px', height: '157px', margin: '0 10px' }" />
        </b-col>
        <b-col xl="11">
            <div class="d-flex align-items-start flex-column box-bg-big" :style="{ height: '290px' }">
                <b-col class="d-flex align-items-center div_box_border w-100 px-3 mb-2">펌프</b-col>
                <b-col class="d-flex w-100 mb-2">
                    <div class="d-flex w-100">
                        <d-col class="d-flex align-items-center div_box_border px-3"
                            :style="{ width: '75%', marginRight: '10px' }">
                            <div class="">우선순위 분석</div>
                        </d-col>
                        <d-col class="d-flex align-items-center justify-content-center" :style="{ width: '25%' }">
                            <div class="custom-radio-category">
                                <input id="rank2" type="radio" name="type" v-model="anly" @click="$emit('selectPump', 'anly')" class="div_content2_left_category2" :checked="anly">
                            </div>
                        </d-col>
                    </div>
                </b-col>
                <b-col class="d-flex w-100 mb-2">
                    <div class="d-flex w-100">
                        <d-col class="d-flex align-items-center div_box_border px-3"
                            :style="{ width: '75%', marginRight: '10px' }">
                            <div class="">운영자 지정</div>
                        </d-col>
                        <d-col class="d-flex align-items-center justify-content-center" :style="{ width: '25%' }">
                            <div class="custom-radio-category">
                                <input id="rank1" type="radio" name="type" v-model="user" @click="$emit('selectPump', 'user')" class="div_content2_left_category2" :checked="user">
                            </div>
                        </d-col>
                    </div>
                </b-col>
                <b-col class="d-flex align-items-center div_box_border w-100 px-3 mb-2">현재 가동 가능한 펌프</b-col>
                <b-col class="d-flex align-items-center div_box_border w-100 px-3">결과 값</b-col>
            </div>
        </b-col>
    </b-row>
</template>
<script>
export default {
    data(){
        return{
            user : false,
            anly : false
        }
    },
    methods:{
        setCtrType(type){
            if(type == '1'){
                this.user = true
            }else{
                this.anly = true
            }
        }
    }
}
</script>
<style scoped>
.box-bg-big {
    padding: 10px;
    background: url(@/assets/img/box_bg_big.png) no-repeat;
    background-size: 100% 100%;
}

.div_content2_left_category2 {
    height: 50px;
    width: 50px;
    background: none;
    border: none;
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.custom-radio-category input[type='radio'] {
    background: none;
    border: none;
}

.custom-radio-category input[type='radio']:checked:after {
    -webkit-animation: scale-up-center 0.5s cubic-bezier(0.390, 0.575, 0.565, 1.000) both;
    animation: scale-up-center 0.5s cubic-bezier(0.390, 0.575, 0.565, 1.000) both;
    height: 50px;
    width: 50px;
    background: #489cf2;
    border: 10px #15284e;
    box-shadow: 0 0 10px #489cf2;
    border-style: solid;
    border-radius: 50%;
    content: '';
    display: inline-block;
}

.custom-radio-category input[type='radio']:after {
    height: 50px;
    width: 50px;
    background: #15284e;
    border: 10px #15284e;
    box-shadow: 0 0 10px #489cf2;
    border-style: solid;
    border-radius: 50%;
    content: '';
    display: inline-block;
}
.div_box_border {
    border: 1px solid #489cf2d1;
    box-shadow: 0 0 3px #489cf2;
    background-color: #0947ae66;
    border-radius: 5px;
}
</style>