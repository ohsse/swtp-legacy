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
            chartColor: [],
            chartKey: 0,
            data: [
                {
                    ygap: 5,
                    type: "heatmap",
                    z: [],
                    x: [],
                    y: [],
                    showscale: false,
                    colorscale: [
                    ],
                    zmin: 0,
                    zmax: 100,
                    hoverinfo: 'text',
                    text: [],
                },
                {
                    x: [],
                    y: [],
                    mode: "lines",
                    line: {
                        color: "#3AA1DE",
                        width: 3,
                    },
                    name: "<span style='color: white; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;'>송수 유량(m³/hr)</span>",
                    yaxis: "y2",
                    xaxis: "x",
                },
                {
                    x: [],
                    y: [],
                    mode: "lines",
                    line: {
                        color: "#EAEAEA",
                        width: 3,
                    },
                    name: "<span style='color: white; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;'>송수 압력(kgf/c㎡)</span>",
                    yaxis: "y3",
                    xaxis: "x",
                }
            ],
            layout: {
                legend: {
                    font: { color: "#FFF" },
                    orientation: "h",
                    x: 0,
                    y: 0.12,
                    xanchor: "center"
                },
                showlegend: true,
                margin: { t: 30, l: 100, r: 50, b: 23 },
                hovermode: "z",
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
                    overlaying: "y",
                    side: "right",
                    tickformat: ",d",
                    autorange: false,
                },
                yaxis3: {
                    color: "#EAEAEA",
                    showline: true,
                    overlaying: "y",
                    showgrid: false,
                    side: "right",
                    position: 0,
                    tickformat: ".1f",
                    autorange: false,
                },
                shapes: [],
                annotations: []
            },
            config: {
                displayModeBar: false,
            },
        };
    },
    mounted() {

    },
    methods: {
        makeChart(x, y, z, selectTime = "h", labels, flowData, presData, zData, xLegendPosition = 0.5, yLegendPosition = 0.08) {
            const result = z.reduce((acc, curr, index) => {
                if (index !== 0) {
                    acc.push(zData[index - 1]);
                }
                acc.push(curr);
                return acc;
            }, []);
            result.push(zData[zData.length - 1]);
            const newData = y.flatMap(item => [item, `(예측)${item}`]);
            this.setLegendPosition(xLegendPosition, yLegendPosition);
            this.layout.yaxis.title = labels;
            const curDataTypes = new Set([0, ...z.flat().filter(value => !Number.isNaN(value))]);
            // const curDataTypes = new Set(z.flat().filter(value => !Number.isNaN(value)));
            const preDataTypes = new Set(zData.flat().filter(value => !Number.isNaN(value)));
            this.curDataColor = Array.from(curDataTypes).sort((a, b) => a - b).map((value, index, array) => {
                if (value === 0) {
                    return [value / 100, "transparent"];
                } else if (value === 0.9999) {
                    return [value / 100, `rgba(0,245,238,1.0)`];
                    // return [(value + 0.0001) / 100, `#00C6F4`];
                }
                else {
                    const opacity = 0.15 + (0.75 / (array.length > 1 ? array.length : 2 - 1)) * index;
                    return [value / 100, `#00F5EE${Math.round(opacity * 255).toString(16).padStart(2, '0')}`];
                }
            });

            this.preDataColor = Array.from(preDataTypes)
                .sort((a, b) => a - b)
                .filter(value => value !== 0)
                .map((value, index, array) => {
                    if (value === 0.9998) {
                        return [value / 100, `rgba(255,255,0,1.0)`];
                        // return [(value + 0.0002) / 100, `#F5D900`];
                    }
                    const opacity = 0.15 + (0.75 / (array.length > 1 ? array.length : 2 - 1)) * index;
                    return [value / 100, `#FFFF00${Math.round(opacity * 255).toString(16).padStart(2, '0')}`];
                });
            let colorscale = this.curDataColor.concat(this.preDataColor);
            colorscale[colorscale.length] = [1, "transparent"];
            colorscale.sort((a, b) => a[0] - b[0]);
            const chartData = result;
            if (chartData.length == 0) {
                this.noData = true;
            } else {
                this.noData = false;
            }
            this.data[0].text = chartData?.map((row) =>
                row?.map((value, colIndex) => {
                    if (value === 0) {
                        return `${x[colIndex]}<br>미가동`;
                    } else if (value === 0.9998 || value === 0.9999) {
                        return `${x[colIndex]}<br>가동`;
                    } else if (!isNaN(value)) {
                        return `${x[colIndex]}<br>주파수: ${value.toFixed(0)}Hz`;
                    }
                })
            );


            this.data[0].x = x;
            this.data[0].y = newData;
            this.data[0].z = chartData;
            this.data[0].colorscale = colorscale;
            this.data[1].x = x; // x 축 데이터 설정
            this.data[1].y = flowData; // y 축 데이터 설정
            this.data[2].x = x; // x 축 데이터 설정
            this.data[2].y = presData; // y 축 데이터 설정
            if (selectTime == "m") {
                this.layout.xaxis.tickformat = "%d일 %H:%M";
            } else if (selectTime == "h") {
                this.layout.xaxis.tickformat = "%d일 %H";
            }

            this.layout.xaxis.range = [x[0], x[x.length - 1]];
            this.layout.xaxis.tickvals = [x[0], x[Math.floor(x.length / 4)], x[Math.floor(x.length / 2)], x[Math.floor(x.length * 3 / 4)], x[x.length - 1]];

            const minFlow = Math.min(...flowData);
            const maxFlow = Math.max(...flowData);

            const minPres = Math.min(...presData);
            const maxPres = Math.max(...presData);

            this.layout.yaxis2.range = [minFlow * 0.9, maxFlow * 1.1];
            this.layout.yaxis3.range = [minPres * 0.8, maxPres * 1.2];

            // Add custom legend items for the colorscale
            this.layout.shapes = [];
            this.layout.annotations = [];
            this.addCustomLegend(this.data[0].colorscale);

            this.chartKey++;
        },

        setLegendPosition(x, y) {
            this.layout.legend.x = x;
            this.layout.legend.y = y;
        },

        addCustomLegend(colorscale) {
            const legendHeight = 0.05;
            let legendWidth = 0.09;
            const totalColors = colorscale.length;
            let curLegendX
            let preLegendX
            let legendSpacing
            legendWidth = 0.09;
            curLegendX = -0.1;
            preLegendX = this.curDataColor.length / (colorscale.length - 1);
            legendSpacing = (1 - curLegendX - legendWidth * totalColors) / (totalColors - 1); // 총 길이에 맞게 간격 조정
            if (colorscale.length > 14) {
                legendWidth = 0.05;
                curLegendX = -0.25;
                legendSpacing = (1 - curLegendX - legendWidth * totalColors) / (totalColors - 1);
                preLegendX = (legendWidth + legendSpacing) * (this.curDataColor.length - 2)
            }
            const legendY = 1.13;
            let fontSize = colorscale.length > 14 ? 10 : 12;
            this.curDataColor.forEach(([value, color], index) => {
                if (index === 0) return; // Skip the first value (0, transparent)
                this.layout.shapes.push({
                    type: 'rect',
                    xref: 'paper',
                    yref: 'paper',
                    x0: curLegendX + index * (legendWidth + legendSpacing),
                    y0: legendY - legendHeight,
                    x1: curLegendX + index * (legendWidth + legendSpacing) + legendWidth,
                    y1: legendY,
                    fillcolor: color,
                    line: {
                        width: 0
                    }
                });
                this.layout.annotations.push({
                    xref: 'paper',
                    yref: 'paper',
                    x: curLegendX + index * (legendWidth + legendSpacing) + legendWidth / 2,
                    y: legendY - legendHeight - 0.02,
                    // text: `${(value * 100).toFixed(0)}Hz`,
                    text: value <= 0.01 ? `가동` : `${(value * 100).toFixed(0)}Hz`,
                    showarrow: false,
                    font: {
                        color: '#FFF',
                        size: fontSize
                    },
                    xanchor: 'center',
                });
            });
            this.preDataColor.forEach(([value, color], index) => {
                this.layout.shapes.push({
                    type: 'rect',
                    xref: 'paper',
                    yref: 'paper',
                    x0: preLegendX + index * (legendWidth + legendSpacing),
                    y0: legendY - legendHeight,
                    x1: preLegendX + index * (legendWidth + legendSpacing) + legendWidth,
                    y1: legendY,
                    fillcolor: color,
                    line: {
                        width: 0
                    }
                });
                this.layout.annotations.push({
                    xref: 'paper',
                    yref: 'paper',
                    x: preLegendX + index * (legendWidth + legendSpacing) + legendWidth / 2,
                    y: legendY - legendHeight - 0.02,
                    // text: `${(value * 100).toFixed(0)}Hz`,
                    text: value <= 0.01 ? `가동` : `${(value * 100).toFixed(0)}Hz`,
                    showarrow: false,
                    font: {
                        color: '#FFF',
                        size: fontSize
                    },
                    xanchor: 'center',
                });
            });
        },

    }
};
</script>
