<template>
    <div class="modal-wrap">
        <div class="modal-contents">
            <div class="modal-container">
                <header id="" class="modal-header">
                    <h5 id="" class="modal-title">{{ this.title }}</h5>
                    <button type="button" aria-label="Close" @click="$emit('closeModal')"
                        class="close fs-3 text-white bg-transparent border-0">×</button>
                </header>
                <AreaChart ref="AreaChart" :style="{ height: '340px', width: '550px' }" />
            </div>
        </div>
    </div>
</template>

<script>
import AreaChart from '@/components/Chart/AreaChart.vue';
import ChartClass from '@/components/Chart/ChartClass.js';

export default {
    components: { AreaChart },
    data() {
        return {
            title: '',
        }
    },
    methods: {
        createChart(title, data) {
            this.title = title
            let dataX = [];
            let dataY = [];
            let labels = [title];

            data?.forEach((element) => {
                if (element.zone_name == title) {
                    dataX.push(element.x)
                    dataY.push(element.y)
                }
            });
            let chartClass = new ChartClass(dataX, [dataY], labels, false, '날짜', '전력량(kW)')
            chartClass.changeSingleChart()
            chartClass.setGridSize('5%', '10%', '10%', '0%')
            this.$refs.AreaChart.changeData(chartClass);
        },
    }
}
</script>

<style>
.modal-wrap {
    position: absolute;
    z-index: 1;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgba(0, 0, 0, 0.5);
}

.modal-contents {
    background-image: url(@/assets/img/img03.png);
    margin: 15% auto;
    padding: 20px;
    border: 1px solid #888;
    width: 80%;
    max-width: 600px;
    text-align: center;
}

#close-btn {
    color: #aaa;
    float: right;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
}

#close-btn:hover,
#close-btn:focus {
    color: black;
    text-decoration: none;
    cursor: pointer;
}

#close-btn:hover,
#close-btn:focus {
    color: black;
    text-decoration: none;
    cursor: pointer;
}
</style>
