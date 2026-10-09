import * as echarts from "echarts";
import ecStat from "echarts-stat";

export default class ScatterChartClassForNew {
  constructor(data, order, isA1 = true, isA4 = true, isA7 = true,Hz) {
 
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
    let colorNum = -1;
     for (let Q_GS_predict = 310; Q_GS_predict <= 810; Q_GS_predict+=0.2) {
      let fir;
      if (
        Q_GS_predict >= 610 &&
        Q_GS_predict <= 660
      ) {
        fir = -0.000024932 * Q_GS_predict**2 +0.03150935 * Q_GS_predict +(-2.457650589)
          if (
            (curOrder[0] == "7" && Hz[0]=="60Hz")
          ) {
            colorNum = 1;
          }
        data1.push([Q_GS_predict, fir]);
      } 
      if (
        Q_GS_predict >= 770 &&
        Q_GS_predict <= 810
      ) {
        fir = -0.000246882 * Q_GS_predict**2 +0.375932822 * Q_GS_predict +(-135.608828117)
          if (
            (curOrder[0] == "7" && Hz[0]=="55Hz")
          ) {
            colorNum = 2;
          }
        data2.push([Q_GS_predict, fir]);
      } 
      if (
        Q_GS_predict >= 730 &&
        Q_GS_predict <= 770
      ) {
        fir = -0.00008505 * Q_GS_predict**2 +0.11676313 * Q_GS_predict +(-32.51196023)
          if (
            (curOrder[0] == "7" && Hz[0]=="54Hz")
          ) {
            colorNum = 3;
          }
        data3.push([Q_GS_predict, fir]);
      } 

      if (
        Q_GS_predict >= 650 &&
        Q_GS_predict <= 730
      ) {
        fir = -0.00012322 * Q_GS_predict**2 +0.163695495 * Q_GS_predict +(-46.833364686)
          if (
            (curOrder[0] == "7" && Hz[0]=="53Hz")
          ) {
            colorNum = 4;
          }
        data4.push([Q_GS_predict, fir]);
      } 

      if (
        Q_GS_predict >= 570 &&
        Q_GS_predict <= 610
      ) {
        fir = -0.000239034 * Q_GS_predict**2 +0.268815845 * Q_GS_predict +(-68.049137452)
          if (
            (curOrder[0] == "7" && Hz[0]=="51Hz")
          ) {
            colorNum = 5;
          }
        data5.push([Q_GS_predict, fir]);
      } 

      if (
        Q_GS_predict >= 510 &&
        Q_GS_predict <= 570
      ) {
        fir = -0.000090201 * Q_GS_predict**2 +0.087742852 * Q_GS_predict +(-13.834163959)
          if (
            (curOrder[0] == "7" && Hz[0]=="50Hz")
          ) {
            colorNum = 6;
          }
        data6.push([Q_GS_predict, fir]);
      } 

      if (
        Q_GS_predict >= 425 &&
        Q_GS_predict <= 510
      ) {
        fir = -0.00002895324 * Q_GS_predict**2 +0.02167906033 * Q_GS_predict +(3.26278947268)
          if (
            (curOrder[0] == "7" && Hz[0]=="49Hz")
          ) {
            colorNum = 7;
          }
        data7.push([Q_GS_predict, fir]);
      } 

      if (
        Q_GS_predict >= 380 &&
        Q_GS_predict <= 425
      ) {
        fir = -0.000294772 * Q_GS_predict**2 +0.229302092 * Q_GS_predict +(-37.412639448)
          if (
            (curOrder[0] == "7" && Hz[0]=="48Hz")
          ) {
            colorNum = 8;
          }
        data8.push([Q_GS_predict, fir]);
      } 

      if (
        Q_GS_predict >= 310 &&
        Q_GS_predict <= 380
      ) {
        fir = -0.00003058271 * Q_GS_predict**2 +0.01487758068 * Q_GS_predict +(5.55706055476)
          if (
            (curOrder[0] == "7" && Hz[0]=="47Hz")
          ) {
            colorNum = 9;
          }
        data9.push([Q_GS_predict, fir]);
      } 

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
        min: 250,
        max:850,
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
        min: (minY - 0.1).toFixed(2),
        max: 10.5, // y 축의 최소값
        axisLabel: {
          color: "#ffffff", // y축 레이블 텍스트 색상 조정
          formatter: function (value) {
            return value.toFixed(1); // 소수점 1번째 자리까지 표현
        }
        },
      },
      series: [
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor:  colorNum == 1 ? "#F5323A" : "#31F565",
          },
          data: data1.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#7/60Hz"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#7/60Hz', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor:  colorNum == 2 ? "#F5323A" : "#31F565", // 원하는 다른 색상으로 변경하세요
          },
          data: data2.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#7/55Hz"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#7/55Hz', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor:  colorNum == 3 ? "#F5323A" : "#31F565",
          },
          data: data3.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#7/54Hz"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#7/54Hz', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor:  colorNum == 4 ? "#F5323A" : "#31F565",
          },
          data: data4.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#7/53Hz"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#7/53Hz', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor:  colorNum == 5 ? "#F5323A" : "#31F565",
          },
          data: data5.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#7/51Hz"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#7/51Hz', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor:  colorNum == 6 ? "#F5323A" : "#31F565",
          },
          data: data6.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#7/50Hz"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#7/50Hz', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
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
                tooltip: { formatter: "#7/49Hz"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#7/49Hz', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 8 ? "#F5323A" : "#31F565",
          },
          data: data8.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#7/48Hz"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#7/48Hz', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
            };
        }),
        },
        {
          type: "scatter",
          encode: { tooltip: [0, 1] },
          symbolSize: 5,
          itemStyle: {
            borderColor: colorNum == 9 ? "#F5323A" : "#31F565",
          },
          data: data9.map((point, index) => {
            return {
                value: point,
                tooltip: { formatter: "#7/47Hz"+ "<br>x: " + (point[0]).toFixed(0) + "<br>y: " + (point[1]).toFixed(2),backgroundColor: 'rgba(255, 255, 255, 0.7)'  },
                label: index === 0 ? { show: true, formatter: '#7/47Hz', textStyle: { fontSize: 16, fontWeight:'bold' } } : { show: false }
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
