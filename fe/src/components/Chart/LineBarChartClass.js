import { addCommaNumber } from "@/util/addCommaNumber";
export default class ChartClass {
  constructor(dataX, dataY, labels, nameX = null, nameY = null,limit,isPre) {
    // this.title = "목표 피크"
    const chartColor = [
      "rgba(10, 255, 255, 1)",
      "#0887e2",
      "#adfcff",
      "#35A29F",
      "#00DFA2",
      "#A6FF96",
      "#ff9b05",
      "#FF6464",
      "#F7FD04",
      "#FFA3FD",
      "#7045f2",
      "#9922AF",
    ]

    this.xAxis = [
      {
        name: nameX,
        type: "category",
        boundaryGap: false,
        data: dataX,
        axisLine: {
          show: true,
          lineStyle: {
            color: "#FFFFFF",
          },
        },
        axisLabel: {
          show: true, // x축의 tick 숨기기
      },
      },
    ];

    this.tooltip = {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        label: {
          backgroundColor: "#000000",
        },
      },
      formatter: function (params) {
        let tooltipText = params[0].name + "<br/>";
        params.forEach(function (item) {
          tooltipText += item.marker + item.seriesName + ": ";
          // 첫 번째와 두 번째 데이터만 소수점 세 자리까지 표현
          if (item.seriesIndex === 0 || item.seriesIndex === 1) {
            tooltipText += (item.value !== undefined && !isNaN(item.value)) ? item.value.toFixed(3) + "<br/>" : "No Data<br/>";
          } else {
            tooltipText += isNaN(item.value) ? "No Data<br/>" : Math.round(item.value) + "<br/>";
          }
        });
        return tooltipText;
      },
    };
    
    this.legend = {
      data: labels,
      textStyle: {
        color: "#FFFFFF",
      },
      left:110,
      top:0
    };

    this.grid = {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true,
    };
    let yAxisMax
    let yAxisMin
    let yAxisMaxForFirst
    let yAxisMinForFirst
    let yAxisMaxForSecond
    let yAxisMinForSecond
    if (Array.isArray(dataY[0])) {
      // dataY[0] 배열에서 null 값을 필터링하여 새로운 배열 생성
      const filteredDataY0 = dataY[0].filter(value => value !== null);
      
      // 최대값 및 최소값 계산
      yAxisMaxForFirst = Math.max(...filteredDataY0);
      yAxisMinForFirst = Math.min(...filteredDataY0) * 0.9;
  }
  
  if (Array.isArray(dataY[1])) {
      // dataY[1] 배열에서 null 값을 필터링하여 새로운 배열 생성
      const filteredDataY1 = dataY[1].filter(value => value !== null);
      
      // 최대값 및 최소값 계산
      yAxisMaxForSecond = Math.max(...filteredDataY1);
      yAxisMinForSecond = Math.min(...filteredDataY1) * 0.9;
  }
  
    if(
        dataY[2]
    ){
        yAxisMax = Math.max(...dataY[2]); 
        yAxisMin = Math.min(...dataY[2]);
          yAxisMax = yAxisMax +3
          yAxisMin = 0
    }
    this.yAxis = [{
      name: nameY,
      type: "value",
      position: 'left',
      splitLine: {
        show: false,
        lineStyle: {
          color: "#192B45",
        },
      },
      splitNumber: 6,
      axisLine: {
        show: true,
        lineStyle: {
          color: "#FFFFFF",
        },
      },
      axisLabel: {
        show: true,
        axisLabel: {
          color: "#FFFFFF",
          padding: 2,
          fontSize: 10,
        },
        formatter: function (value) {
          if (value === 0) {
            return value;
          }
          if(limit ===true){
            return value.toFixed(3)
          }
          return addCommaNumber(value);
        },
      },
      min: yAxisMinForFirst >= yAxisMinForSecond ? yAxisMinForSecond : yAxisMinForFirst,
      max: yAxisMaxForFirst <= yAxisMaxForSecond ? yAxisMaxForSecond : yAxisMaxForFirst, // Y 축 최대값 설정
    }
    ]
    this.yAxis.push({
        name: '',
        type: "value",
        show:false,
        position: 'right',
        splitLine: {
            show: true,
            lineStyle: {
                color: "#192B45",
            },
        },
        splitNumber: 6,
        axisLine: {
            show: true,
            lineStyle: {
                color: "#FFFFFF",
            },
        },
        axisLabel: {
            show: true,
            axisLabel: {
                color: "#FFFFFF",
                padding: 2,
                fontSize: 10,
            },
            formatter: function (value) {
                if (value === 0) {
                    return value;
                }
                return addCommaNumber(value);
            },
        },
        min: yAxisMinForFirst >= yAxisMinForSecond ? yAxisMinForSecond : yAxisMinForFirst,
        max: yAxisMaxForFirst <= yAxisMaxForSecond ? yAxisMaxForSecond : yAxisMaxForFirst, // Y 축 최대값 설정
        axisTick: {
            show: false,
        },
    });

    this.yAxis.push({
        name: '대',
        type: "value",
        position: 'right',
        splitLine: {
          show: true,
          lineStyle: {
            color: "#192B45",
          },
        },
        splitNumber: 6,
        axisLine: {
          show: true,
          lineStyle: {
            color: "#FFFFFF",
          },
        },
        axisLabel: {
          show: true,
          axisLabel: {
            color: "#FFFFFF",
            padding: 2,
            fontSize: 10,
          },
          formatter: function (value) {
            if (value === 0) {
              return value;
            }
            return addCommaNumber(value);
          },
        },
        min: yAxisMin,
        max: yAxisMax,
        axisTick: {
          show: false,
        },
      })

    this.series = [];

    dataY.forEach((element, i) => {
      let y = {
        name: labels[i],
        type: i===2 ? "bar":"line",
        color: chartColor[i],
        label: {
          show: false,
          position: "top",
        },
        emphasis: {
          focus: "series",
        },
        data: element,
      };

      if(i === 0){
        y.yAxisIndex = 1;
        y.color = "#00F5EE"
        y.areaStyle={
        opacity: 0.5,
        }
      }
      if (i === 1) {
        y.color = isPre===true ? "#F5F265": "#EAEAEA"
      }
      if(i===2){
        y.yAxisIndex = 2
        y.color = 'rgba(255, 255, 255,.6)'
        y.z =10
      }
      this.series.push(y);
    });
  }
  setGridSize(
    left = "0%",
    right = "0%",
    top = "0%",
    bottom = "0%",
    containLabel = true
  ) {
    this.grid.left = left; // 그리드 왼쪽 여백
    this.grid.right = right; // 그리드 오른쪽 여백
    this.grid.top = top; // 그리드 상단 여백
    this.grid.bottom = bottom; // 그리드 하단 여백
    this.containLabel = containLabel;
  }

}
