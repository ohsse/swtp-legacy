<template>
    <b-row>
        <b-col xl="11" class="p-0">
            <SmallTitle :title="'적용 결과'" />
        </b-col>
        <b-col xl="1" class="p-0">
            <b-button @click="save" id="btnSave" variant="secondary"
                class="season_btn season_btn_font fs-6 px-3 float-end"
                :style="{ height: '40px' }"><span>적용</span></b-button>
        </b-col>
    </b-row>
    <b-row style="margin-bottom: 10px; padding: 0 10px;">
        <div class="text_title_base2" :style="{ width: '100%', position:'relative'}">
            <b-row class="w-100 d-flex flex_center_between" :style="{ height: '200px' }">
                <b-col class="animationTItle-two" :style="{ height: '70px', color: '#5cebfe', 'font-size': '50px' }">
                    {{ applyPump }}
                </b-col>
            </b-row>
        </div>
    </b-row>
    <b-row class="mt-5 d-flex justify-content-center flex_center fontContent text-center" style="text-align: center; font-size: 2.5em;">
        <b-col xl="3" style="color: #3789b4 ">
            기준 대수
        </b-col>
        <b-col xl="1">
            {{ selectCount }}
        </b-col>
        <b-col xl="3"  style="color: #ffff99">
              현재 대수
        </b-col>
        <b-col xl="1">
            {{ nowCount }}
        </b-col>
    </b-row>
</template>
<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";

export default {
    components :{
        SmallTitle
    },
    props: {
        applyPump: {
            type: String,
            required: true
        },
        nowCount: {
            type: Number,
            required: true
        },
        selectCount: {
            type: Number,
            required: true
        },
    },
    methods:{
        save(){
            this.$emit('save')
        }
    }
}
</script>
<style scoped>
.season_btn {
    height: 33px;
    padding-top: 3px;
    padding-bottom: 3px;
    border: solid 1px #b4dffa;
    background-color: rgba(139, 194, 240, 0.25);
}

.box-bg-big {
    padding: 10px;
    background: url(@/assets/img/box_bg_big.png) no-repeat;
    background-size: 100% 100%;
}



.div_box_title_border {
    background: #067be6cc;
    border: 3px solid #0cc7f7b0;
    box-shadow: 0 0 5px #0cc7f7b0;
    justify-content: center;
    text-indent: 0;
    border-radius: 5px;
}

.div_box_border {
    border: 1px solid #489cf2d1;
    box-shadow: 0 0 3px #489cf2;
    background-color: #0947ae66;
    border-radius: 5px;
}
.contents-container {
  height: 93%;
  width: 100%;
}
.custom-button {
    width: 120px;
    height: 40px;
    align-self: center;
    border: solid 1px #b4dffa;
    background-color: rgb(67, 91, 121);
    border: 1px solid rgb(168, 210, 236, 1);
    color: white;
    cursor: pointer;
    border-radius: 4px;
    margin-left: 20px;
    text-shadow: 0 0 9px #5cafff;
    font-family: 'KHNPHDBold';
    font-weight: normal;
}


.search_btn_font {
  text-shadow: 0 0 9px #5cafff;
  font-size: 17px;
  letter-spacing: normal;
  color: #fff;
  font-family: KHNPHDRegular;
  text-align: center;
  line-height: 2;
}

.search_btn {
  width: 80px;
  align-self: center;
  border: solid 1px #b4dffa;
  background-color: rgba(139, 194, 240, 0.25);
  cursor: pointer;
  border-radius: 4px;
  align-items: center;
  justify-content: center;
  display: flex;
}
.text_title_base2 {
    background: linear-gradient(to right, rgba(139, 194, 240, 0) 20%, rgba(139, 194, 240, 0.25) 50%, rgba(139, 194, 240, 0) 80%);
    background-color: rgba(139, 194, 240, 0); /* fallback color for browsers that don’t support gradients */
    background-size: 100% 100%;
    text-align: center;
}

.content__text-box {
  width: 100%;
  background-size: 100% 20px;
  background-position-y: bottom;
  text-shadow: 0 0 9px #5cafff;
  font-family: KHNPHUotfR;
  font-size: 26px;
  line-height: 1.5;
  text-align: left;
  color: #fff;
}

.season_btn {
    height: 33px;
    padding-top: 3px;
    padding-bottom: 3px;
    border: solid 1px #b4dffa;
    background-color: rgba(139, 194, 240, 0.25);
}
</style>