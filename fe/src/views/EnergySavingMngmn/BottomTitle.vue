<template>
    <div class="bottom_title">{{ title }}</div>
</template>
<script>
export default {
    props: {
        title: {
            type: String,
            required: true
        }
    }
}
</script>

<style scoped>
.bottom_title {
    width: 100%;
    height: 26%;
    font-size: 174%;
    color: white;
    text-align: center;
    line-height: 150px;
    font-family: 'KHNPHDRegular';
}
</style>