<template>
    <b-tabs class="custom-tabs"></b-tabs>
    <div v-if="this.zone[0]">
        <span v-for="(item, i) in zone" :key="i" :class="{ 'selected-tab': selectedTabIndex === i }">
            <input :class="['input', (selectedTabIndex === i) ? 'selected-input' : '']" :value="item" type="button"
                @click="handleButtonClick(i)" />
        </span>
    </div>
    <div class="fL w-100" :style="{ height: '400px' }">
        <AreaChart ref="AreaChart" />
    </div>
</template>
<script>
import AreaChart from '@/components/Chart/AreaChart.vue';
import ChartClass from '@/components/Chart/ChartClass';
export default {
    components: {
        AreaChart,
    },
    data() {
        return {
            data1: [],
            data2: [],
            zone: [],
            selectedTabIndex: 0,
        };
    },
    mounted() {
    },
    methods: {
        createChart(data1, data2) {
            this.data1 = data1
            this.data2 = data2
            if (data1?.data[0]?.PUMP_GRP_NM) {
                this.zone.push(data1?.data[0]?.PUMP_GRP_NM)
            }
            if (data2?.data[0]?.PUMP_GRP_NM) {
                this.zone.push(data2?.data[0]?.PUMP_GRP_NM)
            }
            let dataY = [];
            const pwrPrdct = this.data1?.data?.filter(item => item.PUMP_IDX === 1).map(item => item.PWR_PRDCT);
            const prdctMean = this.data1?.data?.filter(item => item.PUMP_IDX === 1).map(item => item.PRDCT_MEAN);
            const tubePrsrPrdct = this.data1?.data?.filter(item => item.PUMP_IDX === 1).map(item => item.TUBE_PRSR_PRDCT);

            const dataX = this.data1?.data?.filter(item => item.PUMP_IDX === 1).map(item => item.PRDCT_TIME);


            if (this.$area == 'sanseong') {
                let sanseongPwr = []
                let sanseongMean = []
                let sanseongTube = []
                pwrPrdct.forEach((item, index) => {
                    sanseongPwr[index] = 0
                    sanseongMean[index] = 0
                    sanseongTube[index] = 0
                });
                dataY.push(sanseongMean) //예상유량
                dataY.push(sanseongTube) //예상관압
                dataY.push(sanseongPwr) //예상전력
            }
            else {
                dataY.push(prdctMean) //예상유량
                dataY.push(tubePrsrPrdct) //예상관압
                dataY.push(pwrPrdct) //예상전력
            }

            let chartClass = new ChartClass(dataX, dataY, ["예상유량", "예상관압", "예상전력"], false, "날짜", "m3", 'kg/cm2')
            chartClass.setGridSize('5%', '8%', '15%', '10%')
            this.$refs.AreaChart.changeData(chartClass);
      
        },
        handleButtonClick(index) {
            this.selectedTabIndex = index; // 선택된 탭의 인덱스 저장
            this.zoneNumber = index + 1;
            this.tapData(index);
        },
        async tapData(index) {
            let data = [];

            if (index == 0) {
                data = this.data1?.data
            } else if (index == 1) {
                data = this.data2?.data
            }

            let pumpIndex = data[0].PUMP_IDX;
            let dataY = [];

            const pwrPrdct = data?.filter(item => item.PUMP_IDX === pumpIndex).map(item => item.PWR_PRDCT);
            // const prdctMean = data?.filter(item => item.PUMP_IDX === pumpIndex).map(item => item.PRDCT_MEAN);
            // const tubePrsrPrdct = data?.filter(item => item.PUMP_IDX === pumpIndex).map(item => item.TUBE_PRSR_PRDCT);
            const dataX = data?.filter(item => item.PUMP_IDX === pumpIndex).map(item => item.PRDCT_TIME);
            let sanseongPwr = []
            let sanseongMean = []
            let sanseongTube = []
            // dataY.push(prdctMean) //예상유량
            // dataY.push(tubePrsrPrdct) //예상관압
            // dataY.push(pwrPrdct) //예상전력
            pwrPrdct.forEach((item, index) => {
                sanseongPwr[index] = 0
                sanseongMean[index] = 0
                sanseongTube[index] = 0
            });
            dataY.push(sanseongMean) //예상유량
            dataY.push(sanseongTube) //예상관압
            dataY.push(sanseongPwr) //예상전력
            let chartClass = new ChartClass(dataX, dataY, ["예상유량", "예상관압", "예상전력"], false, "날짜", "m3", 'kg/cm2')
            chartClass.setGridSize('5%', '8%', '15%', '10%')
            this.$refs.AreaChart.changeData(chartClass);
         
        },
    }
}
</script>
<style>
.input {
    background: url(@/assets/img/pump/disable_false.png);
    background-size: 100% 100%;
    border: 2px #135096;
    border-radius: 2px 15px 0 0;
    color: #000000;
    width: 80px;
    height: 25px;
    margin-right: 1px;
    mix-blend-mode: color-dodge;
    font-size: 12px;
}

.selected-input {
    color: #fff;
}
</style>