<template>
    <b-col id="month_icon" :style="{ backgroundColor: backgroundColor }" class="div_content_col h-100 mx-1">{{ data.STN_TM
    }}</b-col>
</template>
<script>
export default {
    props: {
        data: Object
    },
    data() {
        return {
            backgroundColor: '#0080008f'
        }
    },
    mounted() {
        const timezone = this.data.TIMEZONE;
        if (timezone == "L") {
            this.backgroundColor = '#0080008f';
        } else if (timezone == 'M') {
            this.backgroundColor = '#ffff008f';
        } else if (timezone == 'H') {
            this.backgroundColor = '#ff00008f';
        }
    }
}
</script>
<style scoped>
.div_content_col {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-family: 'KHNPHDRegular';
    font-size: 15px;
    text-align: center;
    /* background-color: #0080008f; */
    border: 2px solid #ffffff8f;
    border-radius: 5px;
    color: #fff;
}
</style>