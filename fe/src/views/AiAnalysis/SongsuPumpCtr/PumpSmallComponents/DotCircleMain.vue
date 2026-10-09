<template>
    <div class="fL circle-dot"
        :style="{ width: style.mainWidth, height: style.mainHeight, fontSize: fontSize, display: 'flex', alignItems: 'center', justifyContent: 'center' }">
        {{ data.title }}</div>
    <div class="fL" v-if="data.sub"
        :style="{ width: style.sub, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }">
        <DotCicleRow v-for="item in data.sub" :key="item" :data="item" :width="style.row" />
    </div>
</template>
<script>
import DotCicleRow from './DotCircleRow.vue';
export default {
    props: [
        'data', 'style'
    ],
    data() {
        return {
            fontSize: '10px'
        }
    },
    components: {
        DotCicleRow
    },
    mounted() {
        // if (this.data.title.length > 6) {
        //     this.fontSize = '10px'
        // }
    }
}
</script>
<style scoped>
.r-circle {
    background: url(@/assets/img/r_circle.png) no-repeat;
    background-position: center;
}

.circle-dot {
    max-height: 85%;
    border-style: dotted;
    border-color: #546b7d;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 2%;
    white-space: normal;
}
</style>