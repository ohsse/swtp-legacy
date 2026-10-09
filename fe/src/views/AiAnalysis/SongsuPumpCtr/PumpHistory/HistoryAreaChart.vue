<template>
    <b-row style="height: 95%; width: 100%;" class="d-flex justify-content-center align-items-center">
        <AreaChart ref="AreaChart" />
    </b-row>
</template>
<script>
import AreaChart from '@/components/Chart/AreaChart.vue';
import ChartClass from '@/components/Chart/ChartClass';
import ChartLineClass from '@/components/Chart/ChartLineClass';
export default {
    components: {
        AreaChart
    },
    data() {
        return {
        }
    },
    methods: {
        async initChart(x, y, fac_name, type, unit) {
            let chartLineClass
            if (type == 'line') {
                chartLineClass = new ChartLineClass(x, y, fac_name, null, "날짜", unit)
            } else {
                chartLineClass = new ChartClass(x, y, fac_name, null, "날짜", unit)
            }
            chartLineClass.legendOption('scroll', 'vertical', true, 'right', 0, 50, 'auto')
            chartLineClass.setGridSize('5%', '20%', '15%', '10%', true)
            await this.$refs.AreaChart.changeData(
                chartLineClass
            );
            this.$refs.AreaChart.resizeChart()

        }
    }
}
</script>
