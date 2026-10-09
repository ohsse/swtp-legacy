import * as echarts from "echarts";
import ecStat from "echarts-stat";

export default class ScatterChartClass {
  constructor(data, order, isA1 = true, isA4 = true, isA7 = true) {
    order?.forEach((item, i) => {
      order[i] = (parseInt(item) - 5).toString();
    });
    let cnt = 0;
    let rectX, rectY;
    this.data = data?.data;
    let commaArray = [];

    this.data?.forEach((element, i) => {
      let commaObj1 = {
        symbol: "circle",
        symbolSize: [7, 7],
        xAxis: element.flow,
        yAxis: element.pressure,
        itemStyle: {
          color: "#F7FD04",
        },
        label: {
          formatter: "",
          position: "top",
        },
      };
      let commaObj2 = {
        symbol: "circle",
        symbolSize: [7, 7],
        xAxis: element.flow,
        yAxis: element.A4,
        itemStyle: {
          color: "#ff9b05",
        },
        label: {
          formatter: "",
          position: "top",
        },
      };
      let commaObj3 = {
        symbol: "circle",
        symbolSize: [7, 7],
        xAxis: element.flow,
        yAxis: element.A1,
        itemStyle: {
          color: "#ff9b05",
        },
        label: {
          formatter: "",
          position: "top",
        },
      };
      let commaObj4 = {
        symbol: "circle",
        symbolSize: [7, 7],
        xAxis: element.flow,
        yAxis: element.A7,
        itemStyle: {
          color: "#ff9b05",
        },
        label: {
          formatter: "",
          position: "top",
        },
      };
      if (!isA1) {
        commaObj3.symbol = "none";
      }
      if (!isA4) {
        commaObj2.symbol = "none";
      }
      if (!isA7) {
        commaObj4.symbol = "none";
      }
      if (i == this.data.length - 1) {
        commaObj1.itemStyle.color = "#00DFA2";
        commaObj2.itemStyle.color = "#7045f2";
        commaObj3.itemStyle.color = "#7045f2";
        commaObj3.itemStyle.color = "#7045f2";
        commaObj1.symbolSize = [15, 15];
        commaObj2.symbolSize = [15, 15];
        commaObj3.symbolSize = [15, 15];
        commaObj4.symbolSize = [15, 15];
        commaObj1.label.formatter = "성능";
        commaObj2.label.formatter= "저항";
        commaObj3.label.formatter = "저항";
        commaObj4.label.formatter = "저항";
        if (order == undefined) {
          rectX = element.flow;
          rectY = element.pressure;
        }
      } else {
        commaObj1.itemStyle.color = "#F7FD04";
        commaObj2.itemStyle.color = "#ff9b05";
        commaObj3.itemStyle.color = "#ff9b05";
        commaObj4.itemStyle.color = "#ff9b05";
        commaObj1.symbolSize = [7, 7];
        commaObj2.symbolSize = [7, 7];
        commaObj3.symbolSize = [7, 7];
        commaObj4.symbolSize = [7, 7];
        commaObj1.label.formatter = "";
        commaObj2.label.formatter = "";
        commaObj3.label.formatter = "";
        commaObj4.label.formatter = "";
      }
      if (i > this.data.length - 7 && i < this.data.length - 1) {
        cnt++;
        commaObj1.label.formatter = cnt.toString();
        commaObj2.label.formatter = cnt.toString();
        commaObj3.label.formatter = cnt.toString();
        commaObj4.label.formatter = cnt.toString();
      }
      commaArray.push(commaObj1);
      commaArray.push(commaObj2);
      commaArray.push(commaObj3);
      commaArray.push(commaObj4);
    });

    if (this.data?.length > 0) {
      this.pressure = data?.data[this.data?.length - 1]?.pressure;
      this.flow = data?.data[this.data?.length - 1]?.flow;
      this.A4_data = data?.data[this.data?.length - 1]?.A4;
      this.A1_data = data?.data[this.data?.length - 1]?.A1;
      this.A7_data = data?.data[this.data?.length - 1]?.A7;
    }
    echarts.registerTransform(ecStat.transform.clustering);
    let minY = 9999;
    // const comma = [[this.flow, this.pressure]]
    const data1 = [];
    const data2 = [];
    const data3 = [];
    const data4 = [];
    const data5 = [];
    const data6 = [];
    const data7 = [];
    let colorNum = -1;
    let chkFlag = 99999 
     for (let Q_GS_predict = 13000; Q_GS_predict <= 20000; Q_GS_predict++) {
      for (let P_GS_predict = 3.4; P_GS_predict <= 5.4; P_GS_predict += 0.19) {
        let fir;
        if (
          Q_GS_predict >= 18800 &&
          Q_GS_predict <= 19200 &&
          P_GS_predict >=
            58.6613373258886 -
              0.00527586346649821 * Q_GS_predict +
              1.29578746828551e-7 * Q_GS_predict ** 2
        ) {
          fir =
            58.6613373258886 -
            0.00527586346649821 * Q_GS_predict +
            1.29578746828551e-7 * Q_GS_predict ** 2;
          if (order == undefined) {
            if (
              this.flow <= Q_GS_predict * 1.1 &&
              this.flow >= Q_GS_predict * 0.9 &&
              this.pressure <= fir * 1.1 &&
              this.pressure >= fir * 0.9
            ) {
                let flowFlag = this.flow >= Q_GS_predict ? this.flow - Q_GS_predict : Q_GS_predict - this.flow
                let presFlag = this.pressure >= fir ? this.pressure - fir : fir - this.pressure
                let distance = Math.sqrt(flowFlag * flowFlag + presFlag * presFlag);
                if(chkFlag>distance){
                    chkFlag = distance
                    colorNum = 1
                }
            }
          } else {
            if (
              (order[0] == "4" && order[1] == "5",
              order[2] == "6" && order[3] == "7")
            ) {
              colorNum = 1;
            }
          }
          data1.push([Q_GS_predict, fir]);
        } else if (
          Q_GS_predict >= 16500 &&
          Q_GS_predict <= 19000 &&
          P_GS_predict >=
            -3.43193582761012 +
              0.00120472303735243 * Q_GS_predict -
              4.08245928068585e-8 * Q_GS_predict ** 2
        ) {
          fir =
            -3.43193582761012 +
            0.00120472303735243 * Q_GS_predict -
            4.08245928068585e-8 * Q_GS_predict ** 2;
          if (order == undefined) {
            if (
              this.flow <= Q_GS_predict * 1.1 &&
              this.flow >= Q_GS_predict * 0.9 &&
              this.pressure <= fir * 1.1 &&
              this.pressure >= fir * 0.9
            ) {
                let flowFlag = this.flow >= Q_GS_predict ? this.flow - Q_GS_predict : Q_GS_predict - this.flow
                let presFlag = this.pressure >= fir ? this.pressure - fir : fir - this.pressure
                let distance = Math.sqrt(flowFlag * flowFlag + presFlag * presFlag);
                if(chkFlag>distance){
                    chkFlag = distance
                    colorNum = 2
                }
            }
          } else {
            if (
              (order[0] == "2" && order[1] == "4",
              order[2] == "6" && order[3] == "7")
            ) {
              colorNum = 2;
            }
          }
          data2.push([Q_GS_predict, fir]);
        } else if (
          Q_GS_predict >= 16500 &&
          Q_GS_predict <= 18500 &&
          P_GS_predict >=
            2.95 + 0.000497 * Q_GS_predict - 0.0000000229 * Q_GS_predict ** 2
        ) {
          fir =
            2.95 + 0.000497 * Q_GS_predict - 0.0000000229 * Q_GS_predict ** 2;
          if (order == undefined) {
            if (
              this.flow <= Q_GS_predict * 1.1 &&
              this.flow >= Q_GS_predict * 0.9 &&
              this.pressure <= fir * 1.1 &&
              this.pressure >= fir * 0.9
            ) {
                let flowFlag = this.flow >= Q_GS_predict ? this.flow - Q_GS_predict : Q_GS_predict - this.flow
                let presFlag = this.pressure >= fir ? this.pressure - fir : fir - this.pressure
                let distance = Math.sqrt(flowFlag * flowFlag + presFlag * presFlag);
                if(chkFlag>distance){
                    chkFlag = distance
                    colorNum = 3
                }
            }
          } else {
            if (
              (order[0] == "2" && order[1] == "4",
              order[2] == "5" && order[3] == "7")
            ) {
              colorNum = 3;
            }
          }
          data3.push([Q_GS_predict, fir]);
        } else if (
          Q_GS_predict >= 14500 &&
          Q_GS_predict <= 18000 &&
          P_GS_predict >=
            0.120821964429389 +
              0.000853219487279097 * Q_GS_predict -
              3.52433865423429e-8 * Q_GS_predict ** 2
        ) {
          fir =
            0.120821964429389 +
            0.000853219487279097 * Q_GS_predict -
            3.52433865423429e-8 * Q_GS_predict ** 2;
          if (order == undefined) {
            if (
              this.flow <= Q_GS_predict * 1.1 &&
              this.flow >= Q_GS_predict * 0.9 &&
              this.pressure <= fir * 1.1 &&
              this.pressure >= fir * 0.9
            ) {
                let flowFlag = this.flow >= Q_GS_predict ? this.flow - Q_GS_predict : Q_GS_predict - this.flow
                let presFlag = this.pressure >= fir ? this.pressure - fir : fir - this.pressure
                let distance = Math.sqrt(flowFlag * flowFlag + presFlag * presFlag);
                if(chkFlag>distance){
                    chkFlag = distance
                    colorNum = 4
                }
            }
          } else {
            if ((order[0] == "4" && order[1] == "5", order[2] == "6")) {
              colorNum = 4;
            }
          }
          data4.push([Q_GS_predict, fir]);
        } else if (
          Q_GS_predict >= 14500 &&
          Q_GS_predict <= 16500 &&
          P_GS_predict >=
            0.46770987097162 +
              0.000872862970476709 * Q_GS_predict -
              3.89262100721736e-8 * Q_GS_predict ** 2
        ) {
          fir =
            0.46770987097162 +
            0.000872862970476709 * Q_GS_predict -
            3.89262100721736e-8 * Q_GS_predict ** 2;
          if (order == undefined) {
            if (
              this.flow <= Q_GS_predict * 1.1 &&
              this.flow >= Q_GS_predict * 0.9 &&
              this.pressure <= fir * 1.1 &&
              this.pressure >= fir * 0.9
            ) {
                let flowFlag = this.flow >= Q_GS_predict ? this.flow - Q_GS_predict : Q_GS_predict - this.flow
                let presFlag = this.pressure >= fir ? this.pressure - fir : fir - this.pressure
                let distance = Math.sqrt(flowFlag * flowFlag + presFlag * presFlag);
                if(chkFlag>distance){
                    chkFlag = distance
                    colorNum = 5
                }
            }
          } else {
            if ((order[0] == "4" && order[1] == "5", order[2] == "7")) {
              colorNum = 5;
            }
          }
          data5.push([Q_GS_predict, fir]);
        } else if (
          Q_GS_predict >= 15000 &&
          Q_GS_predict <= 16000 &&
          P_GS_predict >=
            -0.759451815235986 +
              0.0010218039074961 * Q_GS_predict -
              4.43777727901476e-8 * Q_GS_predict ** 2
        ) {
          fir =
            -0.759451815235986 +
            0.0010218039074961 * Q_GS_predict -
            4.43777727901476e-8 * Q_GS_predict ** 2;
          if (order == undefined) {
            if (
              this.flow <= Q_GS_predict * 1.1 &&
              this.flow >= Q_GS_predict * 0.9 &&
              this.pressure <= fir * 1.1 &&
              this.pressure >= fir * 0.9
            ) {
                let flowFlag = this.flow >= Q_GS_predict ? this.flow - Q_GS_predict : Q_GS_predict - this.flow
                let presFlag = this.pressure >= fir ? this.pressure - fir : fir - this.pressure
                let distance = Math.sqrt(flowFlag * flowFlag + presFlag * presFlag);
                if(chkFlag>distance){
                    chkFlag = distance
                    colorNum = 6
                }
            }
          } else {
            if ((order[0] == "2" && order[1] == "4", order[2] == "6")) {
              colorNum = 6;
            }
          }
          data6.push([Q_GS_predict, fir]);
        } else if (
          Q_GS_predict >= 13700 &&
          Q_GS_predict <= 14800 &&
          P_GS_predict <
            -13.5501934770404 +
              0.00300980057376775 * Q_GS_predict -
              1.23001244874999e-7 * Q_GS_predict ** 2
        ) {
          fir =
            -13.5501934770404 +
            0.00300980057376775 * Q_GS_predict -
            1.23001244874999e-7 * Q_GS_predict ** 2;
          if (order == undefined) {
            if (
              this.flow <= Q_GS_predict * 1.1 &&
              this.flow >= Q_GS_predict * 0.9 &&
              this.pressure <= fir * 1.1 &&
              this.pressure >= fir * 0.9
            ) {
                let flowFlag = this.flow >= Q_GS_predict ? this.flow - Q_GS_predict : Q_GS_predict - this.flow
                let presFlag = this.pressure >= fir ? this.pressure - fir : fir - this.pressure
                let distance = Math.sqrt(flowFlag * flowFlag + presFlag * presFlag);
                if(chkFlag>distance){
                    chkFlag = distance
                    colorNum = 7
                }
            }
          } else {
            if (order[0] == "5" && order[1] == "7") {
              colorNum = 7;
            }
          }
          data7.push([Q_GS_predict, fir]);
        }
        minY = minY > fir ? fir : minY;
      }
    }

    var CLUSTER_COUNT = 8;
    var DIENSIION_CLUSTER_INDEX = 2;
    var COLOR_ALL = [
      "#0affff",
      "#0affff",
      "#0affff",
      "#0affff",
      "#0affff",
      "#0affff",
      "#0affff",
      "#35A29F",
    ];
    var pieces = [];
    for (var i = 0; i < CLUSTER_COUNT; i++) {
      pieces.push({
        value: i,
        color: COLOR_ALL[i],
      });
    }
    const option = {
      dataset: [
        {
          transform: {
            type: "ecStat:clustering",
            // print: true,
            config: {
              clusterCount: CLUSTER_COUNT,
              outputType: "single",
              outputClusterIndexDimension: DIENSIION_CLUSTER_INDEX,
            },
          },
        },
      ],
      tooltip: {
        position: "top",
      },
      visualMap: {
        type: "piecewise",
        top: "middle",
        min: 0,
        max: CLUSTER_COUNT,
        splitNumber: CLUSTER_COUNT,
        dimension: DIENSIION_CLUSTER_INDEX,
        pieces: pieces,
        textStyle: {
          color: "#ffffff", // 전체 텍스트 색상을 원하는 색상으로 변경합니다.
        },
        show: false,
      },
      grid: {
        borderColor: 'transparent',
        show :false,
        top: 30,
        left: 50,
        right: 30,
        bottom:80,
      },
      xAxis: {
        type: 'value',
        name: 'Water Supply Rate (m³/hr)',
        nameLocation: 'middle',
        nameGap: 30,
        splitLine: {
          lineStyle: {
            color: '#455182' // x축 분할선의 색상을 흰색(#ffffff)으로 변경
        }
        },
        nameTextStyle: {
        color: '#ffffff' 
      },
        min: 13000,
        axisLabel: {
          color: "#ffffff", 
        },
      },
      yAxis: {
        type: 'value',
        name: 'Pressure (kgf/cm²)', 
        nameLocation: 'middle',
        nameGap: 30,  
        splitLine: {
          lineStyle: {
            color: '#455182'
           } // x축 분할선의 색상을 흰색(#ffffff)으로 변경
        },
        nameTextStyle: {
        color: '#ffffff', 
        align: 'center' 
    },
        min: (minY - 0.2).toFixed(2),
        max: 5.7, // y 축의 최소값
        axisLabel: {
          color: "#ffffff", // y축 레이블 텍스트 색상 조정
        },
      },
      series: [
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 1 ? "#FF0000" : "#0affff",
          },
          data: data1.map((point, index) => {
            return {
                value: point,
                label: index === 0 ? { show: true, formatter: '#4567' } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 2 ? "#FF0000" : "#0affff", // 원하는 다른 색상으로 변경하세요
          },
          data: data2.map((point, index) => {
            return {
                value: point,
                label: index === 0 ? { show: true, formatter: '#2467' } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 3 ? "#FF0000" : "#0affff",
          },
          data: data3.map((point, index) => {
            return {
                value: point,
                label: index === 0 ? { show: true, formatter: '#2457' } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 4 ? "#FF0000" : "#0affff",
          },
          data: data4.map((point, index) => {
            return {
                value: point,
                label: index === 0 ? { show: true, formatter: '#456' } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 5 ? "#FF0000" : "#0affff",
          },
          data: data5.map((point, index) => {
            return {
                value: point,
                label: index === 0 ? { show: true, formatter: '#457' } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 6 ? "#FF0000" : "#0affff",
          },
          data: data6.map((point, index) => {
            return {
                value: point,
                label: index === 0 ? { show: true, formatter: '#246' } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 7 ? "#FF0000" : "#0affff",
          },
          data: data7.map((point, index) => {
            return {
                value: point,
                label: index === 0 ? { show: true, formatter: '#57' } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          data: [],
          markPoint: {
            data: commaArray,
            tooltip: {
              formatter: function (params) {
                return (
                  "x: " + params.data.xAxis + "<br>y: " + params.data.yAxis
                );
              },
            },
          },
        },
        {
          type: "line",
          data: [],
          markPoint: {
            data: [
              {
                symbol: "rect",
                symbolSize: [35, 35],
                xAxis: rectX,
                yAxis: rectY,
                itemStyle: {
                  color: "transparent",
                  borderColor: "#FF0000", // 테두리 색을 지정합니다.
                  borderWidth: 2,
                },
                label: {
                  formatter: name,
                  position: "top",
                },
              },
            ],
          },
        },
      ],
    };
    this.option = option;
  }
}
