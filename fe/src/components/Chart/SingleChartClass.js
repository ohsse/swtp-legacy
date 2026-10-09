import { addCommaNumber } from "@/util/addCommaNumber";
export default class ChartClass {
  constructor(dataX, dataY, labels, detline, nameX = null, nameY = null, index) {
    const chartColor = [

      "#0affff",
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
    this.xAxis = [{
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
    }];

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
        color: "#FFFFFF", // 원하는 텍스트 색상으로 변경
      },
      selectedMode: 'single',
      selected: (() => {
        const selectedObj = {};
        for (let i = 0; i < labels.length; i++) {
          selectedObj[labels[i]] = i < index ? false : true;
        }
        return selectedObj;
      })()
    };

    this.toolbox = {
      feature: {
        saveAsImage: {},
      },
    };

    this.grid = {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true,
    };
    this.yAxis = {
      name: nameY,
      type: "value",
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
    };

    this.series = [];

    dataY.forEach((element, i) => {
      const y = {
        name: labels[i],
        type: "line",
        stack: "Total",
        color: chartColor[i],
        opacity: i >= dataY.length - 1 ? 0.1 : 1,
        label: {
          show: false,
          position: "top",
        },
        areaStyle: {},
        emphasis: {
          focus: "series",
        },
        data: element,
      };



      if (detline) {
        y.markLine = {
          silent: true,
          symbol: "circle",
          lineStyle: {
            color: 'red',
            type: 'dashed',
            width: 2,
          },
          label: {
            // position: 'top',
            color: 'red',
            formatter: function () {
              return '목표 피크';
            }
          },
          data: [{ yAxis: detline }],
        };
      }

      this.series.push(y);
    });

  }

  lineChange() {
    this.series.forEach(y => {
      y.type = "line"
      y.color = undefined;
      y.opacity = undefined;
      y.areaStyle = undefined
    })
  }

  barChange() {
    this.series.forEach(y => {
      y.type = "bar"
    })
  }

  legendHide() {
    this.legend.show = false
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
  legendOption(type = 'plain', orient = 'vertical', show = true, left = 'auto', right = 'auto', top = 'auto', bottom = 'auto') {
    this.legend.type = type
    this.legend.orient = orient
    this.legend.show = show
    this.legend.left = left
    this.legend.right = right
    this.legend.top = top
    this.legend.bottom = bottom

  }

  setGridSize(left = '0%', right = '0%', top = '0%', bottom = '0%', containLabel = true) {
    this.grid.left = left  // 그리드 왼쪽 여백
    this.grid.right = right  // 그리드 오른쪽 여백
    this.grid.top = top    // 그리드 상단 여백
    this.grid.bottom = bottom  // 그리드 하단 여백
    this.containLabel = containLabel
  }
}
