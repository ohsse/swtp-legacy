<template>
    <div style="width: 100%; height: 100%;">
        <VuePlotly v-show="!noData" :key="chartKey" style="height: 100%;" :config="config" :data="data" :layout="layout"
            :responsive="true" :display-mode-bar="true"></VuePlotly>
    </div>
</template>
  
<script>
import { VuePlotly } from 'vue3-plotly'

export default {
    components: {
        VuePlotly
    },
    data() {

        return {
            noData: false,
            chartColor: ['#6D5495', '#a866ad', '#846EFF', '#C2AFFF', '#EF5656', '#EA6464', '#4931D3', '#9C98B2', '#3B0A89', '#B64B8D', '#9922AF', '#490755'],
            chartKey: 0,
            data: [
                {
                    ygap: 10,
                    type: 'heatmap',
                    z: [],
                    x: [],
                    y: [],
                    showscale: false,
                    colorscale: [
                        [0, 'transparent'],
                        [0.4, '#a866ad'],
                        [0.45, '#6D5495'],
                        [0.5, 'transparent'],
                        [0.55, '#846EFF'],
                        [0.6, '#C2AFFF'],
                        [0.65, '#EF5656'],
                        [0.7, '#EA6464'],
                        [0.75, '#4931D3'],
                        [0.8, '#9C98B2'],
                        [0.85, '#3B0A89'],
                        [0.9, '#B64B8D'],
                        [0.95, '#9922AF'],
                        [1, '#490755'],
                    ],
                    xAxisCount : 6
                }
            ],
            layout: {
                legend: {
                    font: { color: '#FFF' },
                },
                showlegend: true,
                margin: { t: 20, l: 100, r: 80, b: 30 },
                modebar: { activecolor: 'blue' },
                hovermode: 'x',
                plot_bgcolor: 'transparent',
                paper_bgcolor: 'transparent',
                xaxis: { color: "#FFF", showline: true, showgrid: false, tickformat: "%Y-%m-%d %H:%M", nticks: 2 },
                yaxis: { color: "#FFF", showline: true, showgrid: false, exponentformat: 'none', fixedrange: true, },
                font: { family: 'KHNPHDRegular' },
                sizing: 'stretch'
            }
        }
    },
    mounted() {
    },
    methods: {
        /**
         * 
         * @param {Array<Date>} x x축데이터(날짜 데이터 배열)
         * @param {Array<String>} y y축 데이터 (시설 배열<String>)
         * @param {Array<Array<int>>} z 1혹은 0의 배열데이터
         * @param {String} selectTime 캘린더박스 selected값 ex) 'h', 'm', 'd' 등등
         */
        makeChart(x, y, z, selectTime = 'h', xAxisCount = 6) {
            
            this.layout.xaxis.nticks = xAxisCount;
            // this.colorSettig(z.length)
            this.layout.yaxis.title = '';
            const chartData = []
            let cnt = 0.95;
            z.forEach(element => {
                const arrayData = []
                element.forEach(item => {

                    if (Number(item) > 0) {
                        let chartVal = cnt;
                        if(cnt == 0.5){
                            chartVal = chartVal - 0.05;
                        }
                        arrayData.push(Number(chartVal))
                    } else{
                        arrayData.push(0)
                    }

                })
                chartData.push(arrayData)
                cnt = cnt - 0.05;
            })
            
            if (chartData.length == 0) {
                this.noData = true
            }
            else {
                this.noData = false
            }
            this.data[0].x = x;
            this.data[0].y = y;
            this.data[0].z = chartData;
            this.data[0].name = '';
            if (selectTime == 'h') {
                this.layout.xaxis.tickformat = "%Y-%m-%d %H:%M"
            } else if (selectTime == 'd') {
                this.layout.xaxis.tickformat = "%Y-%m-%d"
            } else if (selectTime == 'm') {
                this.layout.xaxis.tickformat = "%Y-%m"
            } else {
                this.layout.xaxis.tickformat = "%Y"
            }
            // let allZeroFlag = true;
            // let allZeroZdata = []
            // this.data[0].z.forEach(item => {
            //     const anyNonZero = item.some(value => value !== 0);
            //     anyNonZero == true ? allZeroFlag = true : allZeroFlag = false
            // })
            // if (allZeroFlag == false) {
            //     this.data[0].x.forEach(() => {
            //         allZeroZdata.push(1);
            //     });
            //     this.data[0].z.push(allZeroZdata)
            //     this.data[0].y.push('펌프 가동여부')
            // }
            
            this.chartKey++;
        },
        colorSettig(length) {
            const colorscale = [[0, 'transparent']];
            const chartColor = ['#6D5495', '#a866ad', '#846EFF', '#C2AFFF', '#EF5656', '#EA6464', '#4931D3', '#9C98B2', '#3B0A89', '#B64B8D', '#9922AF', '#490755'];

            const totalColors = length - 1;
            for (let i = 0; i < totalColors; i++) {
                const colorIndex = i % chartColor.length; // Get the index within chartColor array
                const index = 0.01 * (i + 1)
                colorscale.push([index, chartColor[colorIndex]]);
            }

            // To loop back and add the first color again
            colorscale.push([0.01 * (totalColors + 1), chartColor[0]]);
            // this.data[0].colorscale = colorscale
        }
    }
}
</script>
  
<style scoped>
/* Add your component styles here */
</style>
  