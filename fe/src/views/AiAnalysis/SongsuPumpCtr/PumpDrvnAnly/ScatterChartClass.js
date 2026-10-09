import * as echarts from "echarts";
import ecStat from "echarts-stat";

export default class ScatterChartClass {
  constructor(data, order, combCal, isA1 = true, isA4 = true, isA7 = true, interval = 1) {
    let allData = [];
    // let curOrder = []
    // order?.forEach((item, i) => {
    //   curOrder[i] = (parseInt(item)).toString();
    // });
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
        yAxis: element.A4 || element.A2 || element.A3,
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
        yAxis: element.A1 || element.A3 || element.A5,
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
        yAxis: element.A7 || element.A6 || element.A,
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
        commaObj1.label.textStyle = { fontSize: 16, fontWeight: "bold" };
        commaObj2.label.formatter = "저항";
        commaObj2.label.textStyle = { fontSize: 16, fontWeight: "bold" };
        commaObj3.label.formatter = "저항";
        commaObj3.label.textStyle = { fontSize: 16, fontWeight: "bold" };
        commaObj4.label.formatter = "저항";
        commaObj4.label.textStyle = { fontSize: 16, fontWeight: "bold" };
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
    let minY = Infinity; // 최소값 초기화
    let maxY = -Infinity; // 최대값 초기화
    let colorNum = -1;
    let allLabels = [];
    let minData;
    let maxData;
    // 데이터 배열을 반복하여 작업 수행
    for (let i = 0; i < combCal.length; i += 2) {
      const lowerBound = combCal[i].FC_VAL;
      const upperBound = combCal[i + 1].FC_VAL;
      let data = [];
      // 매핑에 따라 데이터 추가
      minData = Math.min(lowerBound, ...combCal.map((cal) => cal.FC_VAL));
      maxData = Math.max(upperBound, ...combCal.map((cal) => cal.FC_VAL));
      for (
        let Q_GS_predict = Math.min(
          lowerBound,
          ...combCal.map((cal) => cal.FC_VAL)
        );
        Q_GS_predict <=
        Math.max(upperBound, ...combCal.map((cal) => cal.FC_VAL));
        Q_GS_predict += interval
      ) {
        let fir;

        if (Q_GS_predict >= lowerBound && Q_GS_predict <= upperBound) {
          fir =
            combCal[i].P_SQRT_MUL_VAL +
            combCal[i].P_MUL_VAL * Q_GS_predict +
            combCal[i].P_ADD_VAL * Q_GS_predict ** 2;

          data.push([Q_GS_predict, fir]);
          // 최소,최대값 갱신
          minY = Math.min(minY, fir);
          maxY = Math.max(maxY, fir);
        }
      }

      // 데이터 배열에 추가
      if (data.length > 0) {
        this[`data${i / 2 + 1}`] = data;
      }
      allLabels.push([combCal[i].PUMP_COMB, combCal[i + 1].PUMP_COMB]);
      allData.push(data);
    }
    var CLUSTER_COUNT = 8;
    var DIENSIION_CLUSTER_INDEX = 2;
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
          if (params?.value[1]) {
            return (
              "x: " +
              (params?.value[0]).toFixed(0) +
              "<br>y: " +
              (params?.value[1]).toFixed(2)
            );
          }
        },
      },

      grid: {
        borderColor: "transparent",
        show: true,
        top: 30,
        left: 50,
        right: 30,
        bottom: 80,
      },
      xAxis: {
        type: "value",
        name: "송수 유량 (m³/hr)",
        nameLocation: "middle",
        nameGap: 30,
        splitLine: {
          lineStyle: {
            color: "#455182",
          },
        },
        nameTextStyle: {
          color: "#ffffff",
        },
        min: parseFloat((minData * 0.9).toFixed(0)),
        max: parseFloat((maxData * 1.1).toFixed(0)),
        axisLabel: {
          color: "#ffffff",
        },
      },
      yAxis: {
        type: "value",
        name: "송수 압력 (kgf/cm²)",
        nameLocation: "middle",
        nameGap: 30,
        splitLine: {
          lineStyle: {
            color: "#455182",
          },
        },
        nameTextStyle: {
          color: "#ffffff",
          align: "center",
        },
        min: parseFloat(minY * 0.95).toFixed(2),
        max: parseFloat(maxY * 1.05).toFixed(2), // y 축의 최소값
        axisLabel: {
          color: "#ffffff", // y축 레이블 텍스트 색상 조정
          formatter: function (value) {
            return value.toFixed(1);
          },
        },
      },
      dataZoom: [
        {
          type: "inside", // 마우스 드래그로 확대/축소
          xAxisIndex: [0], // x축 인덱스
          start: 0, // 시작 위치
          end: 100, // 종료 위치
        },
        {
          type: "slider", // 슬라이더 형태의 확대/축소
          xAxisIndex: [0], // x축 인덱스
          start: 0, // 시작 위치
          end: 100, // 종료 위치
          bottom: 15,
          height: 20,
        },
      ],
      series: [
        {
          type: "scatter",
          data: [],
          markPoint: {
            data: commaArray,
            tooltip: {
              formatter: function (params) {
                // yAxis가 정의되어 있을 때 소수점 둘째 자리까지 표시, 아닐 경우 빈 문자열 반환
                if (params?.data.yAxis) {
                  return (
                    "x: " +
                    params?.data.xAxis.toFixed(0) +
                    "<br>y: " +
                    params?.data.yAxis.toFixed(2)
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
                symbolSize: [35, 35],
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
                if (params?.data.yAxis) {
                  return (
                    "x: " +
                    params?.data.xAxis.toFixed(0) +
                    "<br>y: " +
                    params?.data.yAxis.toFixed(2)
                  );
                }
              },
            },
          },
        },
      ],
    };
    const label = processData(allLabels);
    // order 는 "P#1(44Hz), P#2(44Hz)" 같은 펌프조합+주파수 문자열(실측은 수요예측 응답, 예측은 제어 테이블).
    // 라벨은 "#1(44Hz),#2(44Hz)" 꼴이므로 P 를 떼고 토큰 단위로 정렬해 비교한다.
    // 펌프 나열 순서·공백 차이로 하이라이트가 빠지는 일을 막는다. order 가 없으면 하이라이트 없음.
    const orderKey = normalizeCombKey(order);
    if (orderKey) {
      label.forEach((item, i) => {
        if (normalizeCombKey(item) === orderKey) {
          colorNum = i + 1;
        }
      });
    }
    for (let i = 0; i < allData.length; i++) {
      option.series.push({
        type: "scatter",
        encode: { tooltip: [0, 1] },
        symbolSize: 5,
        itemStyle: {
          color: colorNum == i + 1 ? "#F5323A" : "#31F565",
          borderColor: colorNum == i + 1 ? "#F5323A" : "#31F565",
        },
        data: allData[i].map((point, index) => {
          return {
            value: point,
            tooltip: {
              formatter:
                label[i] +
                "<br>x: " +
                point[0].toFixed(0) +
                "<br>y: " +
                point[1].toFixed(2),
              backgroundColor: "rgba(255, 255, 255, 0.7)",
            },
            label:
              index === 0
                ? {
                  show: true,
                  formatter: label[i],
                  textStyle: { fontSize: 14, color: "#FFFFFF" },
                  position: "top",
                  offset: [0, 5],
                }
                : { show: false },
          };
        }),
      });
    }
    this.option = option;
  }
}
// "P#1(44Hz), P#2(44Hz)" / "#2(44Hz),#1(44Hz)" 를 모두 "#1(44Hz),#2(44Hz)" 로 맞춘다.
// 문자열이 아니거나 비어 있으면 빈 문자열을 돌려 호출부에서 하이라이트를 건너뛰게 한다.
function normalizeCombKey(value) {
  if (typeof value !== "string") return "";
  return value
    .replace(/P/g, "")
    .replace(/\s+/g, "")
    .split(",")
    .filter((token) => token !== "")
    .sort()
    .join(",");
}

function processData(data) {
  let result = [];
  data.forEach((item) => {
    let indices = item[0].split(",");
    let values = item[1].split(",");
    let pairs = [];
    for (let i = 0; i < indices.length; i++) {
      if (values[i] !== undefined && values[i] !== "" && values[i] !== '0')
        pairs.push(`#${indices[i]}(${values[i]}Hz)`);
      else pairs.push(`#${indices[i]}`);
    }
    result.push(pairs.join(","));
  });
  return result;
}
