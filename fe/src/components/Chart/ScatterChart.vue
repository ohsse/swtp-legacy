<template>
    <div ref="chart" :style="{ height: '100%', width: '100%' }">
    </div>
</template>
<script>
import * as echarts from 'echarts';
export default {
    components: {
    },
    data() {
        return {
            isLoading: false,
            noData: false
        }
    },
    mounted() {
    },
    methods: {
        changeData(data) {
            if (data.option.dataset.length > 0) {
                this.noData = true
            }
            if (this.chart) {
                this.chart.dispose();
            }
            this.chart = echarts.init(this.$refs.chart);

            // Scatter Chart 옵션 설정
            this.chart.setOption(data.option);
        }
    }
};
</script>

<style>
/* 스타일을 필요에 따라 추가하세요 */
</style>