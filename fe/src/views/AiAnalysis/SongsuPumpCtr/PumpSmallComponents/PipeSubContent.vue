<template>
    <div class="sub_content_middle_value fL sub_content_font">{{data.title}}</div>
    <div class="sub_content_middle_value fL">
        <div class="sub_input_box" id="분관">{{ data.value }}</div><span class="sub_content_font"> kg/cm2</span>
    </div>
</template>
<script>
export default {
    props:[
        'data'
    ]
}
</script>
<style scoped>
.sub_content_middle_value {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 50%;
    width: 100%;
}
.sub_input_box {
    width: 70px;
    border: 1px solid #489cf2;
    background-color: #15284e;
    color: #fff;
    font-family: LABDigital;
    text-align: center;
    margin-right: 2%;
    float: left;
}
.sub_content_font {
    text-shadow: 0 0 9px #5cafff;
    font-size: 14px;
    font-family: KHNPHDRegular;
    letter-spacing: normal;
    color: #c3eaff;
    align-self: center;
    padding: 0 2% 0 0;
    float: left;
}
</style>