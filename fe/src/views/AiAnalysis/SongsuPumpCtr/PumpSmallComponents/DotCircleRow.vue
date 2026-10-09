<template>
    <div class="detail_textWrap" :style="{ margin: '0' }">
        <div class="detail_text" :style="{ width: width }">{{ data.title }}</div>
        <span class="detail_value" :style="{ textAlign: 'right' }">{{ data.value }}</span>
        <span class="detail_text" :style="{ marginLeft: '10px', width: 'initial', fontSize: '14px' }">{{ data.unit }}</span>
    </div>
</template>
<script>
export default {
    props: [
        'data', 'width'
    ],
}
</script>
<style>
.detail_textWrap {
    width: calc(100% - 11px);
    display: flex;
    align-items: center;
    margin: 10px 15px;
    font-size: 18px;
    font-family: 'KHNPHDRegular';
    color: #fff;
}

.detail_text {
    width: 70%;
    text-shadow: 0 0 9px #5cafff;
    color: #c3eaff;
}

.detail_value {
    width: 30%;
    font-family: LAB디지털;
    text-align: right;
}
</style>