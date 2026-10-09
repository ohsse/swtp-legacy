<template>
    <div class="chart">
        <v-chart class="scatterchart" :option="option" />
    </div>
</template>

<script>
import { reactive, computed, watch } from 'vue';
import VChart from 'vue-echarts';
export default {
    components: { VChart },
    props: ['data', 'flow_rate', 'pressure', 'color', 'scatterData'],
    setup(props) {
        let bgData = reactive(props.scatterData)
        const dataLevel = [];
        const dataPTK = {};
        const qKey = [], pKey = [], xKey = [], yKey = [];
        Object.keys(bgData)?.filter(item => {
            if (item.startsWith('Q_')) {
                qKey.push(item)
            }
            if (item.startsWith('P_')) {
                pKey.push(item)
            }
            if (item.startsWith('x_')) {
                xKey.push(item);
            }
            if (item.startsWith('y_')) {
                yKey.push(item);
            }
        })
        qKey.forEach((element, j) => {
            const arrayLevel = [];

            bgData[element]?.forEach((item, i) => {
                if (i % 20 === 0) {
                    let x = item;
                    let y = bgData[pKey[j]][i];
                    arrayLevel.push([x, y]);
                }
            });
            dataLevel.push(arrayLevel);
        });
        xKey.forEach(keyItem => {
            const keyChecker = keyItem.split('x_');
            for (let i = 0; i < bgData[keyItem].length; i++) {
                if (dataPTK[keyChecker[1]]) {
                    dataPTK[keyChecker[1]].push([bgData[keyItem][i], bgData['y_' + keyChecker[1]][i]]);
                } else {
                    dataPTK[keyChecker[1]] = [[bgData[keyItem][i], bgData['y_' + keyChecker[1]][i]]];
                }
            }
        })
        const colorSetting = (val) => {
            if (val === 1) return '#ff9100';
            if (val === 2) return '#47ff51';
            if (val === 3) return '#0048ff';
        };

        const state = reactive({
            data: computed(() => props.data),
            flow_rate: computed(() => props.flow_rate),
            pressure: computed(() => props.pressure),
            color: computed(() => props.color),
        });

        watch(state, () => {
            // console.log('state.color :: ' + state.color);
            // state.flow_rate = [];
            // state.pressure = [];
            // state.data = [];
            option.series[option.series.length - 2].data = state.data;
            option.series[option.series.length - 1].data =
                state.data.length === 0
                    ? []
                    : [state.data[state.data.length - 1]];
            option.series[option.series.length - 1].itemStyle.color = colorSetting(state.color);
        });
        const scatterColors = ['#911F2722', '#05505222', '#19349822'];  // Colors for scatter plots
        const lineColors = ['#911F27', '#055052', '#193498'];  // Colors for line plots
        const option = reactive({
            backgroundColor: 'rgba(0,0,0,0)',
            title: {
                textStyle: {
                    color: '#fff',
                },
                left: 'center',
            },
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(0,0,0,0.8)',
                borderWidth: 1,
                borderColor: 'rgba(25,163,223, 0.5)',
                textStyle: {
                    color: '#eee',
                    fontSize: 12,
                },
                axisPointer: {
                    lineStyle: {
                        color: {
                            type: 'linear',
                            x: 0,
                            y: 0,
                            x2: 0,
                            y2: 1,
                            colorStops: [
                                {
                                    offset: 0,
                                    color: 'rgba(126,199,255,0)',
                                },
                                {
                                    offset: 0.5,
                                    color: 'rgba(126,199,255,1)',
                                },
                                {
                                    offset: 1,
                                    color: 'rgba(126,199,255,0)',
                                },
                            ],
                            global: false,
                        },
                    },
                },
                formatter: '{a} : {c}',
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100,
                },
            ],
            legend: {
                right: '0',
                top: 26,
                data: ['Normal', 'Warning', 'Critical', 'Fault'],
                textStyle: {
                    color: '#fff',
                },
            },
            xAxis: {
                name: '유량(㎥/min)',
                nameLocation: 'middle',
                nameGap: 30,
                nameTextStyle: {
                    color: '#5D96C4',
                },
                axisLabel: {
                    color: '#5D96C4',
                    fontStyle: {
                        fontSize: 10,
                    },
                },
                splitLine: {
                    lineStyle: {
                        type: 'dashed',
                        color: '#192B45',
                    },
                },
                axisLine: {
                    lineStyle: {
                        color: '#192B45',
                    },
                },
                min: 0,
            },
            yAxis: {
                name: '압력(kgf/㎥)',
                nameLocation: 'middle',
                nameGap: 30,
                nameTextStyle: {
                    color: '#5D96C4',
                },
                axisLabel: {
                    color: '#5D96C4',
                    fontStyle: {
                        fontSize: 10,
                    },
                },
                splitLine: {
                    lineStyle: {
                        type: 'dashed',
                        color: '#192B45',
                    },
                },
                axisLine: {
                    lineStyle: {
                        color: '#192B45',
                    },
                },
                scale: true,
            },
            grid: {
                left: '10%',
                right: '5%',
                top: '5%',
                bottom: '10%',
                containLabel: true,
            },
            series: [
                ...dataLevel.map((data, index) => ({
                    name: `dataLevel_${index}`,
                    data,
                    type: 'scatter',
                    symbolSize: 5,
                    large: true,
                    itemStyle: {
                        color: scatterColors[index % dataLevel.length]
                    },
                    tooltip: {
                        show: false,
                    },
                    animation: false,
                })),
                ...Object.keys(dataPTK).map((key, index) => {
                    let areaStyle = null;
                    let lineStyle = null;
                    if (index < dataLevel.length) {
                        areaStyle = {
                            color: scatterColors[index],
                            opacity: 1,
                        };
                    }
                    lineStyle = {
                        width: 1,
                        color: lineColors[(key[key.length - 1] % (lineColors.length + 1)) - 1]
                    }
                    return {
                        name: `dataPTK_${index}`,
                        data: dataPTK[key],
                        showSymbol: false,
                        type: 'line',
                        smooth: true,
                        areaStyle: areaStyle,
                        lineStyle: lineStyle,
                        tooltip: {
                            show: false,
                        },
                        animation: false,
                    };
                }),
                {
                    name: 'value',
                    data: state.data,
                    type: 'scatter',
                    symbolSize: 1,
                    itemStyle: {
                        color: '#04E0F3',
                    },
                    large: true,
                    tooltip: {
                        formatter() {
                            return '';
                        },
                    },
                    animation: false,
                },
                {
                    name: 'value2',
                    data: state.data.length !== 0 ? [state.data[state.data.length - 1]] : [],
                    type: 'scatter',
                    symbolSize: 10,
                    itemStyle: {
                        color: colorSetting(state.color),
                        opacity: 1,
                    },
                    large: true,
                    tooltip: {
                        formatter() {
                            return '';
                        },
                    },
                    animation: false,
                }
            ]
        });

        return { option };
    },

};

</script>
