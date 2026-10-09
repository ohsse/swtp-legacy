<template>
    <div class="pieChart-box">
        <div class="charts">
            <div class="title-box">
                <img src="@/assets/img/circle.6d33197f.svg" alt="타이틀 블릿 이미지">
                <p class="mb-0">설비현황 통계</p>
            </div>
            <div class="box-edge top-L blur"></div>
            <div class="box-edge top-R blur"></div>
            <div class="box-edge bottom-L blur"></div>
            <div class="box-edge bottom-R blur"></div>
            <div class="box-edge top-L"></div>
            <div class="box-edge top-R"></div>
            <div class="box-edge bottom-L"></div>
            <div class="box-edge bottom-R"></div>
            <!-- 파이챠트 영역 -->


            <v-chart class="piechart" :option="option" />
            <!-- <p class="text">정상</p> -->

            <!-- //파이챠트 영역 -->
        </div>
    </div>
</template>

<script>
import * as echarts from 'echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { PieChart } from 'echarts/charts';
import 'echarts-liquidfill';
import {
    TitleComponent,
    TooltipComponent,
    LegendComponent,
} from 'echarts/components';
import VChart, { THEME_KEY } from 'vue-echarts';
import { defineComponent, watch, ref } from 'vue';
import { useStore } from 'vuex';
use([
    CanvasRenderer,
    PieChart,
    TitleComponent,
    TooltipComponent,
    LegendComponent,
]);

export default defineComponent({
    components: {
        VChart,
    },
    provide: {
        [THEME_KEY]: 'dark',
    },
    mounted() {
        this.drawChart()
    },
    setup() {
        const store = useStore();

        const fetchData = () => {
            store.dispatch('getAllFacStats', null, { root: true })
        };

        fetchData();
        const option = ref({});

        watch(() => store.state.process[0].normal, function () {
            drawChart()
        });
        const drawChart = () => {
            const normalValue = store.state.process
                .map((item) => item.normal)
                .reduce((a, b) => a + b, 0);
            const errValue = store.state.process
                .map((item) => item.err)
                .reduce((a, b) => a + b, 0);

            const trafficWay = [
                {
                    name: '정상',
                    value: normalValue,
                },
                {
                    name: '이상',
                    value: errValue,
                },
            ];

            const normal = trafficWay.filter((data) => data.name === '정상')[0]
                .value;
            const error = trafficWay.filter((data) => data.name === '이상')[0]
                .value;

            const normalPercentage = ((normal / (normal + error)) * 100).toFixed(0);

            const data = [];
            const borderColor = ['#1464EF', '#ED1874'];
            const color = [
                new echarts.graphic.LinearGradient(0, 1, 0, 0, [
                    {
                        offset: 0,
                        color: '#08286d96',
                    },
                    {
                        offset: 1,
                        color: '#1a95fa67',
                    },
                ]),
                new echarts.graphic.LinearGradient(0, 1, 0, 0, [
                    {
                        offset: 0,
                        color: '#52062381',
                    },
                    {
                        offset: 1,
                        color: '#f30e667c',
                    },
                ]),
            ];
            const shadowColor = ['#1464EF', '#ED1874'];

            for (var i = 0; i < trafficWay.length; i++) {
                data.push({
                    value: trafficWay[i].value,
                    name: trafficWay[i].name,
                    itemStyle: {
                        borderWidth: 2,
                        shadowBlur: 5,
                        borderColor: borderColor[i],
                        color: color[i],
                        shadowColor: shadowColor[i],
                    },
                });
            }

            option.value = {
                backgroundColor: 'rgba(0,0,0,0)',
                title: {
                    text: '',
                    textStyle: {
                        fontWeight: 'normal',
                        fontSize: 25,
                        color: 'rgb(97, 142, 205)',
                    },
                },
                legend: {
                    show: true,
                    right: 0,
                    top: 0,
                    orient: 'vertical',
                    itemHeight: 6,
                    textStyle: {
                        color: '#fff',
                        fontSize: 14,
                    },
                },
                series: [
                    {
                        type: 'liquidFill',
                        radius: '60%',
                        center: ['48%', '50%'],
                        data: [
                            normalPercentage * 0.01,
                            normalPercentage * 0.01 - 0.1,
                            normalPercentage * 0.01 - 0.25,
                        ],
                        backgroundStyle: {
                            borderWidth: 1,
                            color: '#191E36',
                        },
                        label: {
                            formatter: '{a|정상}\n{b|' + normalPercentage + '%}', // 텍스트 설정
                            rich: {
                                a: {
                                    fontSize: 15, // "정상" 텍스트의 크기를 조절합니다
                                    color: '#fff', // "정상" 텍스트의 색상
                                    padding: [0, 0, 30, 0],
                                },
                                b: {
                                    fontSize: 45,
                                    color: 'rgb(255, 255, 255)',
                                },
                            },
                            textStyle: {
                                fontSize: 45,
                                lineHeight: 30,
                                textShadowColor: 'rgba(0,0,0,0.2)',
                                textShadowBlur: 8,
                                textShadowOffsetX: 2,
                                textShadowOffsetY: 2,
                            },
                        },
                        outline: {
                            show: false,
                        },
                    },
                    {
                        type: 'pie',
                        center: ['48%', '50%'],
                        radius: ['65%', '80%'],
                        emphasis: {
                            scale: false, // 원하는 값으로 설정하실 수 있습니다.
                            // 다른 강조 효과 설정
                        },
                        data: data,
                        itemStyle: {
                            normal: {
                                label: {
                                    show: true,
                                    position: 'outside',
                                    color: '#fff',
                                    fontSize: 16,
                                    lineHeight: 20,
                                    align: 'center',

                                    formatter: (params) => {
                                        var percent = 0;
                                        var total = 0;
                                        for (
                                            var i = 0;
                                            i < trafficWay.length;
                                            i++
                                        ) {
                                            total += trafficWay[i].value;
                                        }
                                        percent = (
                                            (params.value / total) *
                                            100
                                        ).toFixed(0);
                                        if (params.name !== '') {
                                            return (
                                                params.name +
                                                '\n' +
                                                percent +
                                                '%' +
                                                '\n' +
                                                params.value +
                                                '건'
                                            );
                                        } else {
                                            return '';
                                        }
                                    },
                                },
                                labelLine: {
                                    length: -10,
                                    length2: 30,
                                    show: true,
                                    lineStyle: {
                                        width: 3,
                                    },
                                },
                            },
                        },
                    },
                ],
            };
        }

        return { option, store, fetchData, drawChart };
    },
});

</script>

<style></style>