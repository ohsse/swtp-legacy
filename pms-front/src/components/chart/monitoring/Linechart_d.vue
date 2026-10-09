<template>
    <div class="chart">
        <div class="titlebox" v-if="props.title">
            <img src="@/assets/subtitleicon.svg" alt="" />
            <span style="font-size: 18px;"> {{ props.title.split('-')[0] }}</span>&nbsp;
            <span>{{ props.title.split('-')[1] }}</span>
            <span v-if="changeTime" style="    float: right;
            border: 1px solid white;
            padding: 1px 11px;
            background-color: #454545">{{ props.changeTime }}</span>
        </div>
        <AreaChart class="linechart" :areaChartData="option" @modalClick="modalClick" @downloadCSV="downloadCSV"
            autoresize :isModalChartDia="props.isModal" @chartClick="chartClick" />
    </div>
</template>

<script>
import { useStore } from 'vuex';
import { ref, reactive, computed, watch } from 'vue';
import ChartClass from '@/components/chart/ChartClass.js'
import AreaChart from '@/components/chart/AreaChart.vue'

export default {
    components: { AreaChart },
    props: ['title', 'chartTitle', 'detailData', 'name1', 'yName', 'isTime', 'isModal',
        'nameGap', 'xLines', 'xName', 'changeTime', 'threshold', 'isPump', 'fixY', 'size'],
    setup(props, context) {
        let dataY = [];
        let dataX = [];
        let tempY = [];
        const chartClick = (dataAll) => {
            context.emit('chartClick', dataAll)
        }
        const modalClick = (dataAll) => {
            context.emit('showModal', dataAll)
        }
        const downloadCSV = () => {
            let _headers = [props.xName ? '주파수' : '날짜'];
            if (props.isModal == undefined) {
                _headers = [_headers, ...props.name1]
            } else {
                _headers.push(props.yName)
            }
            let csvData = new Array();

            csvData.push(_headers);
            let time = [];

            for (let index = 0; index < props.detailData[0].length; index++) {
                let inputDate = new Date(props.detailData[0][index][0])

                const year = inputDate.getFullYear();
                const month = inputDate.getMonth() + 1;
                const day = inputDate.getDate();
                const hours = inputDate.getHours();
                const minutes = inputDate.getMinutes();

                const outputDateString = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')} ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;

                if (props.isTime == undefined) {
                    time.push(outputDateString)
                } else {
                    time.push(props.detailData[0][index][0])
                }

                const csvRow = [time[index], ...props.detailData.map(data => data[index][1])];
                csvData.push(csvRow);
            }


            var lineArray = [];
            csvData.forEach(function (infoArray, index) {
                var line = infoArray.join(",");
                lineArray.push(index == 0 ? "\uFEFF" + line : line);
            });
            var csvContent = lineArray.join("\n");

            var blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
            var link = document.createElement("a");

            if (link.download !== undefined) { // feature detection
                // Browsers that support HTML5 download attribute
                link.setAttribute("href", window.URL.createObjectURL(blob));
                link.setAttribute("download", props.title == undefined ? props.chartTitle : props.title + '.csv');
                link.setAttribute("hidden", true);
            }
            else {
                console.log('error');
                link.setAttribute("href", "#");
            }
            link.click();
        }
        const store = useStore();
        const state = reactive({
            current: computed(() => props.detailData),
            name1: computed(() => props.name1),
        });
        let option = ref({})
        const isTime = props.isTime === undefined ? store.state.monitor1.flag : props.isTime
        const chartDataMake = () => {
            const nameGap = props.nameGap == undefined ? 25 : props.nameGap
            if (props.detailData.length > 0) {
                dataX = []
                dataY = []
                for (let i = 0; i < props.detailData.length; i++) {
                    props.detailData[i].forEach((item) => {
                        if (i == 0) {
                            if (isTime == true) {
                                if (item[0]) {
                                    // let inputDate = new Date(item[0])
                                    // const timeString = inputDate.toLocaleTimeString('en-US', {
                                    //         hour: '2-digit',
                                    //         minute: '2-digit',
                                    //         hour12: false
                                    //     });
                                    dataX.push(item[0])
                                    // dataX.push(timeString.substring(0, timeString.length-8))
                                }
                            } else {
                                if (item[0]) {
                                    dataX.push(item[0])
                                }
                            }
                        }
                        tempY.push(item[1])
                    })
                    if (tempY.length != 0) {
                        dataY.push(tempY)
                        tempY = []
                    }
                }
                if (props.threshold !== undefined) {
                    option.value = new ChartClass(dataX, dataY, state.name1, props.xLines, props.xName, props.yName, null, props.threshold, props.isPump, props.fixY, props.size)
                } else {
                    option.value = new ChartClass(dataX, dataY, state.name1, props.xLines, props.xName, props.yName, null, null, props.isPump, props.fixY, props.size)
                }
                option.value.yAxis[0].nameGap = nameGap

            }
        }
        chartDataMake()
        watch(() => props.xLines, function () {
            chartDataMake()
        })
        watch(() => props.detailData, function () {
            chartDataMake()
        });

        return { store, option, modalClick, downloadCSV, chartClick, props };
    },

};
</script>
