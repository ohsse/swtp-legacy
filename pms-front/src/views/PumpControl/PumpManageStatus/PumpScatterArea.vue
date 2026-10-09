<template>
    <div class="value-chart">
        <div class="label">▸ 분포도</div>
        <div class="value">
            <Scatter :scatterData="scatterData" :data="item.data" :color="item.running" />
        </div>
    </div>
</template>
<script>
import Scatter from '@/components/chart/monitoring/Scatter_PTK.vue';

export default {
    components: {
        Scatter,
    },
    props: ['scatterData', 'item'],
    mounted() {
    }
}
</script>
<style lang="">
    
</style>