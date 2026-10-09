import { addCommaNumber } from "@/util/addCommaNumber";
export default class ChartClass {
  constructor(dataX, dataY, labels, detline, nameX = null, nameY = null, name2Y = null,showLabel=true,thresMax=undefined,thresMin=undefined) {
    // this.title = "목표 피크"
    const chartColor = [
      nameX === '반투명' ? "rgba(10, 255, 255, 0.2)" : "rgba(10, 255, 255, 1)",
      nameX === '반투명' ? "#F5F265" : "#0887e2",
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
        nameGap: 5,
        nameTextStyle: {
          fontSize: 10, // 이름의 글꼴 크기 조정
        },
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
          show: showLabel, // x축의 tick 숨기기
          // fontSize: 12,
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
    };
    this.legend = {
      data: labels,
      textStyle: {
        color: "#FFFFFF", // 범례 텍스트 색상을 원하는 값으로 변경하세요.
      },
    };

    this.toolbox = {
      // feature: {
      //   saveAsImage: {},
      // },
    };

    this.grid = {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true,
    };

    let yAxisMax = Math.max(...dataY.flat()); 
    let yAxisMin = Math.min(...dataY.flat());

    //로직 수정 필요?
    yAxisMin = yAxisMin - (yAxisMin * 0.05);
    yAxisMin = Math.floor(yAxisMin / 10) * 10;
    if (Array.isArray(detline)) {
      detline.forEach(item => {
        if (parseInt(item.replace(/,/g, ''), 10) > yAxisMax) {
          yAxisMax = parseInt(item.replace(/,/g, ''), 10); 
        }else{
          // yAxisMax = (Math.ceil((yAxisMax)/100)) * 100
          yAxisMax = yAxisMax + (yAxisMax * 0.05);
          yAxisMax = Math.ceil(yAxisMax / 10) * 10;
        }
        if(parseInt(item.replace(/,/g, ''), 10) < Math.min(...dataY.flat())){
          // console.log("?");
          yAxisMin = parseInt(item.replace(/,/g, ''), 10)
        }
      })
    }
    else if(detline){
        if (detline > yAxisMax) {
          yAxisMax = detline; 
        }else{
          // yAxisMax = (Math.ceil((yAxisMax)/100)) * 100
          yAxisMax = yAxisMax + (yAxisMax * 0.05);
          yAxisMax = Math.ceil(yAxisMax / 10) * 10;
        }
        if(detline < Math.min(...dataY.flat())){
          // console.log("?");
          yAxisMin = detline
        }
    }
    else{
      yAxisMax = yAxisMax + (yAxisMax * 0.05);
      yAxisMax = yAxisMax < 5 ? 5 : Math.ceil(yAxisMax / 10) * 10;
    }
    if(!showLabel){
      if(thresMax &&thresMin){
      yAxisMax = Math.max(...dataY.flat()) <= thresMax ? (thresMax+0.1) : Math.max(...dataY.flat()); 
      yAxisMin = Math.min(...dataY.flat()) >= thresMin ? (thresMin-0.2) : Math.min(...dataY.flat());
      }else if(thresMax){
        yAxisMax = Math.max(...dataY.flat()) <= thresMax ? (thresMax+0.1) : Math.max(...dataY.flat());
        yAxisMin = Math.min(...dataY.flat()) >= thresMax ? (thresMax-0.2) : Math.min(...dataY.flat());
      }else{
        yAxisMax = Math.max(...dataY.flat()); 
        yAxisMin = Math.min(...dataY.flat());
      }
    }
    this.yAxis = [{
      name: nameY,
      type: "value",
      position: 'left',
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
        show: showLabel,
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
      max: yAxisMax, // Y 축 최대값 설정
    }
    ]
    if (name2Y != null) {
      this.yAxis.push({
        name: name2Y,
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
        axisTick: {
          show: false,
        },
      })
    }

    this.series = [];

    dataY.forEach((element, i) => {
      let y = {
        name: labels[i],
        type: "line",
        color: chartColor[i],
        opacity: i >= dataY.length - 1 ? 0.1 : 1,
        label: {
          show: false,
          position: "top",
        },
        areaStyle: {
        },
        emphasis: {
          focus: "series",
        },
        data: element,

      };
      if(nameX === '반투명'){
        if(i ==1){
          y.areaStyle.opacity =0
        }
      }
      if (name2Y != null) {
        if (i === 1) {
          y.yAxisIndex = 1;
        }
      }
      if (Array.isArray(detline)) {
        y.markLine = {
          silent: true,
          symbol: "circle",

          data: [
            {
              yAxis: parseInt(detline[0].replace(/,/g, ''), 10),
              label: {
                color: "red",
                fontSize: 18,
                formatter: () => "목표 피크",
                offset: [-35, 15],
              },
              lineStyle: {
                color: "red",
                type: "dashed",
                width: 2,
              },
            },
            {
              yAxis: parseInt(detline[1].replace(/,/g, ''), 10),
              label: {
                color: "orange",
                fontSize: 18,
                formatter: () => "요금적용\n전력피크",
                offset: [-35, -25],
              },
              lineStyle: {
                color: "orange",
                type: "dashed",
                width: 2,
              },
            },
          ],
        };
      }
      else if(detline){
          y.markLine = {
            silent: true,
            symbol: "circle",
            lineStyle: {
              color: "red",
              type: "dashed",
              width: 2,
            },
            label: {
              color: "red",
              fontSize: 18,
              formatter: () => "목표 피크",
              offset: [-35, 20],
            },
            data: [
              {
                yAxis: detline,
              },
            ],
          };
      }
      if(thresMax &&thresMin){
        y.markLine = {
          silent: true,
          symbol: "none",
          lineStyle: {
            color: '#F55900',
            type: 'dotted',
            width: 1,
          },
          label: {
            color: "red",
            fontSize: 18,
            formatter: () => "",
            offset: [-35, 20],
          },
          data: [
            {
              yAxis: thresMax,
            },
            {
              yAxis: thresMin,
            },
          ],
        };
      }else if(thresMax){
        y.markLine = {
          silent: true,
          symbol: "none",
          lineStyle: {
            color: '#F55900',
            type: 'dotted',
            width: 2,
          },
          label: {
            color: "red",
            fontSize: 18,
            formatter: () => "",
            offset: [-35, 20],
          },
          data: [
            {
              yAxis: thresMax,
            },

          ],
        };
      }

      this.series.push(y);
    });
  }

  noDetLineName() {
    this.series.forEach((y) => {
      if (y.markLine) {
        y.markLine.label.formatter = () => "";
      }
    });
  }
  lineChange() {
    this.series.forEach((y) => {
      y.type = "line";
      y.color = undefined;
      y.opacity = undefined;
      y.areaStyle = undefined;
    });
  }

  barChange() {
    this.series.forEach((y) => {
      y.type = "bar";
    });
  }

  changeSingleChart() {
    this.legend.selectedMode = "single";
  }

  legendHide() {
    this.legend.show = false;
  }

  nameSetting(xName, yName) {
    this.xAxis.name = xName;
    this.yAxis.name = yName;
  }

  /**
   *
   * @param {String} type
   * @param {String} orient
   * @param {Boolean} show
   * @param {*} left 위치
   * @param {*} right 위치
   * @param {*} top 위치
   * @param {*} bottom 위치
   */
  legendOption(
    type = "plain",
    orient = "vertical",
    show = true,
    left = "auto",
    right = "auto",
    top = "auto",
    bottom = "auto"
  ) {
    this.legend.type = type;
    this.legend.orient = orient;
    this.legend.show = show;
    this.legend.left = left;
    this.legend.right = right;
    this.legend.top = top;
    this.legend.bottom = bottom;
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
  setNameGap() {
    this.yAxis[0].nameLocation = 'middle'
    this.yAxis[0].nameGap = 25
  }
}
