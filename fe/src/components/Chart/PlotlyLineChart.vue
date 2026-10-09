<template>
    <div style="width: 100%; height: 100%">
        <VuePlotly v-show="!noData" :key="chartKey" style="height: 100%" :config="config" :data="data" :layout="layout"
            :responsive="true" :display-mode-bar="false"></VuePlotly>
    </div>
</template>

<script>
import { VuePlotly } from "vue3-plotly";

export default {
    components: {
        VuePlotly,
    },
    data() {
        return {
            noData: false,
            chartColor: [
                "#6D5495",
                "#a866ad",
                "#846EFF",
                "#C2AFFF",
                "#EF5656",
                "#EA6464",
                "#4931D3",
                "#9C98B2",
                "#3B0A89",
                "#B64B8D",
                "#9922AF",
                "#490755",
            ],
            chartKey: 0,
            data: [
                {
                    ygap: 10,
                    type: "heatmap",
                    z: [],
                    x: [],
                    y: [],
                    showscale: false,
                    colorscale: [
                        [0, "transparent"],
                        [0.4, "#a866ad"],
                        [0.45, "#6D5495"],
                        [0.5, "#FEB5B4"],
                        [0.55, "#846EFF"],
                        [0.6, "#C2AFFF"],
                        [0.65, "#EF5656"],
                        [0.7, "#EA6464"],
                        [0.75, "#4931D3"],
                        [0.8, "#9C98B2"],
                        [0.85, "#3B0A89"],
                        [0.9, "#B64B8D"],
                        [0.95, "#9922AF"],
                        [1, "#490755"],
                    ],
                },
                {
                    // line 차트 데이터
                    x: [], // x 축 데이터
                    y: [], // y 축 데이터
                    mode: "lines", // 선 그래프 설정
                    line: {
                        color: "#3AA1DE", // 선 색상 설정
                        width: 3, // 선 두께 설정
                    },
                    name: "송수 유량(m³/hr)", // 그래프 이름 설정
                    yaxis: "y2",
                    xaxis: "x", // x 축에 연결하여 x축 분할선 비활성화
                },
                {
                    // line 차트 데이터
                    x: [], // x 축 데이터
                    y: [], // y 축 데이터
                    mode: "lines", // 선 그래프 설정
                    line: {
                        color: "#FFF", // 선 색상 설정
                        width: 3, // 선 두께 설정
                    },
                    name: "송수 압력(kgf/c㎡)", // 그래프 이름 설정
                    yaxis: "y3",
                    xaxis: "x", // x 축에 연결하여 x축 분할선 비활성화
                },
            ],
            layout: {
                legend: {
                    font: { color: "#FFF" },
                    orientation: "h", // 레전드의 방향을 수평으로 설정하여 차트 아래에 표시
                    x: 0,
                    y: 0.12,
                },
                showlegend: true,
                margin: { t: 10, l: 85, r: 50, b: 23 },
                hovermode: "x",
                plot_bgcolor: "transparent",
                paper_bgcolor: "transparent",
                xaxis: {
                    color: "#FFF",
                    showline: true,
                    showgrid: false,
                    tickformat: "%Y-%m-%d %H:%M",
                    nticks: 6,
                    autorange: false,
                },
                yaxis: {
                    color: "#FFF",
                    showline: true,
                    showgrid: false,
                    exponentformat: "none",
                    fixedrange: true,
                },
                font: { family: "KHNPHDRegular" },
                sizing: "stretch",
                yaxis2: {
                    color: "#3AA1DE",
                    showline: true,
                    showgrid: false,
                    overlaying: "y", // y 축과 겹치게 설정
                    side: "right", // 차트를 오른쪽에 표시
                    tickformat: ",d",
                    autorange: false,
                },
                yaxis3: {
                    color: "#FFF",
                    showline: true,
                    overlaying: "y", // y 축과 겹치게 설정
                    showgrid: false,
                    side: "right", // 차트를 오른쪽에 표시
                    position: 0,
                    tickformat: ".1f",
                    autorange: false,
                },
            },
            config: {
                displayModeBar: false,
            },
        };
    },
    mounted() { },
    methods: {
        /**
         *
         * @param {Array<Date>} x x축데이터(날짜 데이터 배열)
         * @param {Array<String>} y y축 데이터 (시설 배열<String>)
         * @param {Array<Array<int>>} z 1혹은 0의 배열데이터
         * @param {String} selectTime 캘린더박스 selected값 ex) 'h', 'm', 'd' 등등
         */
        makeChart(x, y, z, selectTime = "h", labels, flowData, presData, zData, xLegendPosition = 0.2, yLegendPosition = 0.08) {
            let yData = [];
            y.forEach((item) => {
                yData.push(item.replace("_", ""));
            });
            // this.colorSettig(z.length)
            this.setLegendPosition(xLegendPosition, yLegendPosition)
            this.layout.yaxis.title = labels;
            const chartData = [];
            let cnt = 0.95;
            z.forEach((element) => {
                const arrayData = [];
                element.forEach((item) => {
                    if (Number(item) > 0) {
                        let chartVal = cnt;
                        if (cnt == 0.5) {
                            chartVal = chartVal - 0.05;
                        }
                        arrayData.push(Number(chartVal));
                    } else {
                        arrayData.push(0);
                    }
                });
                chartData.push(arrayData);
                cnt = cnt - 0.05;
            });
            if (chartData.length == 0) {
                this.noData = true;
            } else {
                this.noData = false;
            }

            this.data[0].x = x;
            this.data[0].y = yData;
            this.data[0].z = chartData;
            this.data[0].name = labels;
            this.data[1].x = x; // x 축 데이터 설정
            this.data[1].y = flowData; // y 축 데이터 설정
            this.data[2].x = x; // x 축 데이터 설정
            this.data[2].y = presData; // y 축 데이터 설정
            if (selectTime == "m") {
                this.layout.xaxis.tickformat = "%d일 %H:%M";
            } else if (selectTime == "h") {
                this.layout.xaxis.tickformat = "%d일 %H";
            }
            this.layout.xaxis.range = [x[0], x[x.length - 1]]
            this.layout.xaxis.tickvals = [x[0], x[Math.floor(x.length / 4)], x[Math.floor(x.length / 2)], x[Math.floor(x.length * 3 / 4)], x[x.length - 1]]

            // flowData의 최소값과 최대값 구하기
            const minFlow = Math.min(...flowData);
            const maxFlow = Math.max(...flowData);

            // presData의 최소값과 최대값 구하기
            const minPres = Math.min(...presData);
            const maxPres = Math.max(...presData);

            // this.layout.yaxis2.range와 this.layout.yaxis3.range 설정
            this.layout.yaxis2.range = [minFlow * 0.9, maxFlow * 1.1];
            this.layout.yaxis3.range = [minPres * 0.8, maxPres * 1.2];

            // 노란색 데이터를 모아서 추가하는 방식으로 변경
            const yellowDataX = [];
            const yellowDataY = [];
            const yellowDataColor = [];
            zData.forEach(arr => {
                let lastElement = arr[arr.length - 1];  // 각 배열의 끝 인덱스 데이터
                while (arr.length < x.length) {
                    arr.push(lastElement);  // 끝 인덱스 데이터를 붙여넣음
                }
            });
            zData.forEach((rowData, rowIndex) => {
                let color = "rgba(204, 204, 51, 0.9)"
                if (rowIndex < 7) {
                    color = "rgba(204, 204, 51, 0.9)"
                }
                else {
                    color = "rgba(10, 250, 235, 0.9)"

                }
                const interval = Math.ceil(rowData.length / 50);
                rowData.forEach((value, columnIndex) => {
                    yellowDataX.push(x[columnIndex]);
                    yellowDataY.push(yData[rowIndex]);
                    // 만약 현재 처리 중인 열이 rowData의 마지막 열
                    if (columnIndex === rowData.length - 1) {
                        if (value != 0) {
                            yellowDataColor.push(color); // 노란색 설정
                        } else {
                            yellowDataColor.push("rgba(204, 204, 51, 0)"); // 투명색 설정
                        }
                    } else {
                        if (value != 0 && columnIndex % interval === 0) {
                            yellowDataColor.push(color); // 노란색 설정
                        } else {
                            yellowDataColor.push("rgba(204, 204, 51, 0)"); // 투명색 설정
                        }
                    }
                });
            });
            this.data[3] = {
                type: "scatter",
                mode: "markers",
                x: yellowDataX,
                y: yellowDataY,
                marker: {
                    color: yellowDataColor,
                    size: 4, // 점의 크기 설정
                },
                hoverinfo: "none", // 마우스 호버시 툴팁 비활성화
                showlegend: false, // 레전드 표시 비활성화
            };

            this.chartKey++;
        },
        colorSettig(length) {
            const colorscale = [[0, "transparent"]];
            const chartColor = [
                "#6D5495",
                "#a866ad",
                "#846EFF",
                "#C2AFFF",
                "#EF5656",
                "#EA6464",
                "#4931D3",
                "#9C98B2",
                "#3B0A89",
                "#B64B8D",
                "#9922AF",
                "#490755",
            ];

            const totalColors = length - 1;
            for (let i = 0; i < totalColors; i++) {
                const colorIndex = i % chartColor.length; // Get the index within chartColor array
                const index = 0.01 * (i + 1);
                colorscale.push([index, chartColor[colorIndex]]);
            }

            // To loop back and add the first color again
            colorscale.push([0.01 * (totalColors + 1), chartColor[0]]);
            // this.data[0].colorscale = colorscale
        },
        setLegendPosition(x, y) {
            this.layout.legend.x = x
            this.layout.legend.y = y
        }
    },
};
</script>

<style scoped>
/* Add your component styles here */
</style>
