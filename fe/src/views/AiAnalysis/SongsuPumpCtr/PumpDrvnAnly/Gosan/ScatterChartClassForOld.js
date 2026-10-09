import * as echarts from "echarts";
import ecStat from "echarts-stat";

export default class ScatterChartClassForOld {
  constructor(data, order, combCal,isA1 = true, isA4 = true, isA7 = true) {
    let curOrder = []
    order?.forEach((item, i) => {
      curOrder[i] = (parseInt(item)).toString();
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
          color: "#CCCC33",
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
          color: "#9966FF",
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
          color: "#33FFFF",
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
          color: "#FF33CC",
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
        commaObj1.itemStyle.color = "#FFFF00";
        commaObj2.itemStyle.color = "#6633CC";
        commaObj3.itemStyle.color = "#00CCCC";
        commaObj4.itemStyle.color = "#CC0099";
        commaObj1.symbolSize = [15, 15];
        commaObj2.symbolSize = [15, 15];
        commaObj3.symbolSize = [15, 15];
        commaObj4.symbolSize = [15, 15];
        commaObj1.label.formatter = "성능";
        commaObj1.label.textStyle = { fontSize: 16, fontWeight:'bold' };
        commaObj2.label.formatter = "저항";
        commaObj2.label.textStyle = { fontSize: 16, fontWeight:'bold' };
        commaObj3.label.formatter = "저항";
        commaObj3.label.textStyle = { fontSize: 16, fontWeight:'bold' };
        commaObj4.label.formatter = "저항";
        commaObj4.label.textStyle = { fontSize: 16, fontWeight:'bold' };
        if (order == undefined) {
          rectX = element.flow;
          rectY = element.pressure;
        }
      } else {
        commaObj1.itemStyle.color = "rgba(204, 204, 51, 0.5)";
        commaObj2.itemStyle.color = "rgba(153, 102, 255, 0.5)";
        commaObj3.itemStyle.color = "rgba(51, 255, 255, 0.5)";
        commaObj4.itemStyle.color = "rgba(255, 51, 204, 0.5)";
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
    const data8 = [];
    const data9 = [];
    const data10= [];
    let colorNum = -1;
     for (let Q_GS_predict = 11000; Q_GS_predict <= 19400; Q_GS_predict+=10) {
      let fir;
        if (
          Q_GS_predict >= 18800 &&
          Q_GS_predict <= 19400
        ) {
          fir =
            58.6613373258886 -
            0.00527586346649821 * Q_GS_predict +
            0.00000013 * Q_GS_predict ** 2;
            if (
              (curOrder[0] == "4" && curOrder[1] == "5"&&
              curOrder[2] == "6" && curOrder[3] == "7")
            ) {
              colorNum = 1;
            }
          data1.push([Q_GS_predict, fir]);
        } if (
          Q_GS_predict >= 16800 &&
          Q_GS_predict <= 19300 
        ) {
          fir =
            -3.43193582761012 +
            0.00120472303735243 * Q_GS_predict -
            0.000000041 * Q_GS_predict ** 2;
            if (
              (curOrder[0] == "2" && curOrder[1] == "4"&&
              curOrder[2] == "6" && curOrder[3] == "7")
            ) {
              colorNum = 2;
            }
          data2.push([Q_GS_predict, fir]);
        } if (
          Q_GS_predict >= 16000 &&
          Q_GS_predict <= 19200
        ) {
          fir =
          3.46795572136709 + 0.000426388235108014 * Q_GS_predict - 0.0000000195 * Q_GS_predict ** 2;
            if (
              (curOrder[0] == "2" && curOrder[1] == "4"&&
              curOrder[2] == "5" && curOrder[3] == "7")
            ) {
              colorNum = 3;
            }
          data3.push([Q_GS_predict, fir]);
        } if (
          Q_GS_predict >= combCal[6].FC_VAL &&
          Q_GS_predict <= combCal[7].FC_VAL
        ) {
          fir = combCal[6].P_SQRT_MUL_VAL + combCal[6].P_MUL_VAL * Q_GS_predict + combCal[6].P_ADD_VAL * Q_GS_predict**2
            if ((curOrder[0] == "4" && curOrder[1] == "5"&& curOrder[2] == "6")) {
              colorNum = 4;
            }
          data4.push([Q_GS_predict, fir]);
        } 
        if (
        Q_GS_predict >= combCal[4].FC_VAL &&
        Q_GS_predict <= combCal[5].FC_VAL
      ) {
        fir = combCal[4].P_SQRT_MUL_VAL + combCal[4].P_MUL_VAL * Q_GS_predict + combCal[4].P_ADD_VAL * Q_GS_predict**2
            if ((curOrder[0] == "2" && curOrder[1] == "4"&& curOrder[2] == "6")) {
              colorNum = 5;
            }
          data5.push([Q_GS_predict, fir]);
        } if (
          Q_GS_predict >= 13000 &&
          Q_GS_predict <= 15400
        ) {
          fir =
            -13.5501934770404 +
            0.00300980057376775 * Q_GS_predict -
            0.000000123 * Q_GS_predict ** 2;
            if (curOrder[0] == "2" && curOrder[1] == "5"&& curOrder[2] == "7") {
              colorNum = 6;
            }
          data6.push([Q_GS_predict, fir]);
        }
      if (
        Q_GS_predict >= combCal[2].FC_VAL &&
        Q_GS_predict <= combCal[3].FC_VAL
      ) {
        fir = combCal[2].P_SQRT_MUL_VAL + combCal[2].P_MUL_VAL * Q_GS_predict + combCal[2].P_ADD_VAL * Q_GS_predict**2
          if (
            (curOrder[0] == "4" && curOrder[1] == "6")
          ) {
            colorNum = 7;
          }
        data7.push([Q_GS_predict, fir]);
      } 
      if (
        Q_GS_predict >= 15000 &&
        Q_GS_predict <= 18000
      ) {
        fir = -0.00000004 * Q_GS_predict**2 +0.0010218 * Q_GS_predict -0.75945182
          if (
            (curOrder[0] == "4" && curOrder[1] == "6" && curOrder[2] == "7")
          ) {
            colorNum = 8;
          }
        data8.push([Q_GS_predict, fir]);
      } 
      // if (
      //   Q_GS_predict >= combCal[0].FC_VAL &&
      //   Q_GS_predict <= combCal[1].FC_VAL
      // ) {
      //   fir = combCal[1].P_SQRT_MUL_VAL + combCal[1].P_MUL_VAL * Q_GS_predict + combCal[1].P_ADD_VAL * Q_GS_predict**2
      //     if (
      //       (curOrder[0] == "2" && curOrder[1] == "6")
      //     ) {
      //       colorNum = 10;
      //     }
      //   data10.push([Q_GS_predict, fir]);
      // } 
      minY = minY > fir ? fir : minY;

    }
    curOrder = []
    var CLUSTER_COUNT = 8;
    var DIENSIION_CLUSTER_INDEX = 2;
    var COLOR_ALL = [
      "#31F565",
      "#31F565",
      "#31F565",
      "#31F565",
      "#31F565",
      "#31F565",
      "#31F565",
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
          formatter: function (params) {
              // yAxis가 정의되어 있을 때 소수점 둘째 자리까지 표시, 아닐 경우 빈 문자열 반환
              if(params?.value[1]){
              return (
                  "x: " + (params?.value[0]).toFixed(0) + "<br>y: " + (params?.value[1]).toFixed(2)
              );
            }
          },
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
        name: '송수 유량 (m³/hr)',
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
        min: 11000,
        axisLabel: {
          color: "#ffffff", 
        },
      },
      yAxis: {
        type: 'value',
        name: '송수 압력 (kgf/cm²)', 
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
        min: (minY - 1).toFixed(2),
        max: 5.7, // y 축의 최소값
        axisLabel: {
          color: "#ffffff", // y축 레이블 텍스트 색상 조정
          formatter: function (value) {
            return value.toFixed(1); // 소수점 1번째 자리까지 표현
        }
        },
      },
      dataZoom: [
        {
            type: 'inside', // 마우스 드래그로 확대/축소
            xAxisIndex: [0], // x축 인덱스
            start: 0, // 시작 위치
            end: 100, // 종료 위치
        },
        {
            type: 'slider', // 슬라이더 형태의 확대/축소
            xAxisIndex: [0], // x축 인덱스
            start: 0, // 시작 위치
            end: 100, // 종료 위치
            bottom: 15,
            height: 20, 
        }
    ],
      series: [
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 3,
          itemStyle: {
            borderColor: colorNum == 1 ? "#F5323A" : "rgba(49, 245, 101, 0.1)",
          },
          data: data1.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#4567"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#4567', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 3,
          itemStyle: {
            borderColor: colorNum == 2 ? "#F5323A" : "rgba(49, 245, 101, 0.1)", // 원하는 다른 색상으로 변경하세요
          },
          data: data2.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#2467"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#2467', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 3,
          itemStyle: {
            borderColor: colorNum == 3 ? "#F5323A" : "rgba(49, 245, 101, 0.1)",
          },
          data: data3.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#2457"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#2457', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 4 ? "#F5323A" : "#31F565",
          },
          data: data4.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#456"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#456', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 5 ? "#F5323A" : "#31F565",
          },
          data: data5.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#246"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#246', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 3,
          itemStyle: {
            borderColor: colorNum == 6 ? "#F5323A" : "rgba(49, 245, 101, 0.1)",
          },
          data: data6.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#257"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#257', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 7 ? "#F5323A" : "#31F565",
          },
          data: data7.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#46"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#46', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 3,
          itemStyle: {
            borderColor: colorNum == 8 ? "#F5323A" : "rgba(49, 245, 101, 0.1)",
          },
          data: data8.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#467"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#467', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 3,
          itemStyle: {
            borderColor: colorNum == 9 ? "#F5323A" : "rgba(49, 245, 101, 0.1)",
          },
          data: data9.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#246"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#246', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 10 ? "#F5323A" : "#31F565",
          },
          data: data10.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#26"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#26', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
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
                  // yAxis가 정의되어 있을 때 소수점 둘째 자리까지 표시, 아닐 경우 빈 문자열 반환
                  if(params.data.yAxis){
                  return (
                      "x: " + params.data.xAxis.toFixed(0) + "<br>y: " + params.data.yAxis.toFixed(2)
                  );
                }
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
                symbolSize: [35,35],
                xAxis: rectX,
                yAxis: rectY,
                itemStyle: {
                  color: "transparent",
                  borderColor: "#F5323A", // 테두리 색을 지정합니다.
                  borderWidth: 2,
                },
                label: {
                  formatter: name,
                  position: "top",
                },
              },
            ],
            tooltip: {
              formatter: function (params) {
                if(params.data.yAxis){
                  return (
                      "x: " + params.data.xAxis.toFixed(0) + "<br>y: " + params.data.yAxis.toFixed(2)
                  );
                }
              },
          },
          },
        },
      ],
    };
    this.option = option;
  }
}
