export default class ChartClass {
  /**
   * 
   * @param {*} dataX x축 데이터
   * @param {*} dataY y축 데이터
   * @param {*} labels 범례 
   * @param {*} xLines 정밀진단에서 사용되는 xLines
   * @param {*} nameX x축 이름
   * @param {*} nameY  y축 이름 1 
   * @param {*} name2Y y축 이름 2
   * @param {*} threshold 가로선 기준선 (송수펌프 목록에서만 사용)
   */
  constructor(dataX, dataY, labels, xLines, nameX = "날짜", nameY = null, name2Y = null, threshold, isPump, fixY, size) {
    const chartColor = [
      "#5470c6",
      "#91cc75",
      "#fac858",
      "#ee6666"
    ];
    const chartControlColor = [
      "#fac858",
      "#E68917",
      "#ee6666",
    ];
    this.xAxis = [
      {
        name: nameX,
        type: "category",
        boundaryGap: false,
        data: dataX,
        axisLine: {
          show: true,
          lineStyle: {
            color: '#5D96C4',
          },
        },
      }
    ];
    if (isPump) {
      this.xAxis[0].axisLabel = {
        interval: Math.ceil(dataX.length / 7),
        formatter: function (value) {
          return value.split(' ')[0].substring(5);
        }
      };
    }

    this.tooltip = {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderWidth: 1,
      borderColor: 'rgba(25,163,223, 0.5)',
      textStyle: {
        color: '#eee',
        fontSize: 12,
      },
      axisPointer: {
        type: "cross",
        label: {
          backgroundColor: "#000000",
        },
      },
      position: function (point, params, dom, rect, size) {
        // 툴팁을 마우스 아래에 표시하도록 조정
        return [point[0] - size.contentSize[0] - 10, point[1] - size.contentSize[1] / 2];
      },
    };

    this.legend = {
      type: 'scroll',
      // data: labels,
      data: labels,
      textStyle: {
        color: "#FFFFFF", // 범례 텍스트 색상을 원하는 값으로 변경하세요.
      },
      inactiveColor: '#444',
    };

    this.grid = {
      top: '10%',
      left: '5%',
      right: '10%',
      bottom: '0%',
      containLabel: true,
    };
    if (size) {
      this.grid.left = size + '%'
    }
    this.yAxis = [{
      name: nameY,
      type: "value",
      boundaryGap: false,
      position: 'left',
      splitLine: {
        show: true,
        lineStyle: {
          color: "#192B45",
        },
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: '#5D96C4',
        },
      },
      axisLabel: {
        show: true,
        fontStyle: {
          color: '#5D96C4',
        },
        formatter: function (value) {
          if (value === 0) {
            return value;
          }
          return value;
        },
      },
      axisTick: {
        show: false,
      },
    }]
    if (isPump) {
      this.yAxis[0].nameLocation = 'middle';
      this.yAxis[0].nameTextStyle = {
        color: '#5D96C4',
        // lineHeight: 15,
        align: 'center',
        fontSize: 10
      };
      // y축 최대값 숨긴거 
      // this.yAxis[0].axisLabel = {
      //   showMaxLabel: false  // y축 최대값 라벨 숨기기
      // };
    } else {
      this.yAxis[0].nameLocation = 'middle';
      this.yAxis[0].nameTextStyle = {
        lineHeight: 24,
      }
    }

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
            return value;
          },
        },
        axisTick: {
          show: false,
        },
      })
    }

    this.series = [];

    let isZero = false;
    let minChecker = 9999999;
    let maxChecker = -9999999;
    dataY.forEach((element, i) => {
      isZero = element.find(yItem => yItem > 0) == undefined
      element.forEach(yItem => minChecker = yItem < minChecker ? yItem : minChecker);
      element.forEach(yItem => maxChecker = yItem > maxChecker ? yItem : maxChecker);
      let x = {
        name: labels?.[i],
        type: "line",
        color: chartColor[i],
        label: {
          show: false,
          position: "top",
        },
        hoverAnimation: false,
        data: element,
      };
      if (xLines?.length > 0) {
        x.markLine = {
          data: []
        }
        xLines.forEach((item, i) => {
          x.markLine.data.push({
            label: {
              color: chartColor[i + 1 % 4],
              fontSize: 18,
              formatter: () => item.value + '\n\n' + item.type,
              offset: [0, 260],
            },
            silent: true,
            symbol: "circle",
            lineStyle: {
              color: chartColor[i + 1 % 4],
              type: 'dashed',
              width: 1,
            },
            xAxis: item.value * 2,
            name: item.type
          })
        })
      }
      if (threshold) {
        //   const th_value = threshold.find(thItem => thItem.koTitle == labels[i])?.th_value;
        //   if(th_value)
        //     x.markLine = {
        //   silent: true,
        //   symbol: "none",
        //   data: [{
        //     label: {
        //       color: "white",
        //       fontSize: 10,
        //       offset: [0, 10],
        //       formatter: () => "임계선",
        //     },
        //     lineStyle: {
        //       color: chartControlColor[i%4],
        //       type: 'dashed',
        //       width: 1,
        //     },
        //     yAxis: th_value
        //   }]
        // };

        threshold.forEach((item, i) => {
          if (!x.markLine) {
            x.markLine = {
              silent: true,
              symbol: "none",
              data: []
            };
          }
          x.markLine.data.push({
            label: {
              color: chartControlColor[i % 3],
              fontSize: 10,
              offset: [0, 10],
              formatter: () => item.koTitle,
            },
            lineStyle: {
              color: chartControlColor[i % 3],
              type: 'dashed',
              width: 1,
            },
            yAxis: item.value
          });
        })

      }
      this.series.push(x);
    });
    // 0 보다 큰게 없을경우 
    if (isZero == true) {
      this.yAxis.forEach(yA => {
        if (threshold) {
          if (fixY == 1) {
            yA.min = 0;
            yA.max = 10;
            yA.interval = 5;
            yA.data = [0, 3, 6, 10];
          } else if (fixY == 5) {
            yA.min = 0;
            yA.max = 10;
            yA.interval = 2.5;
          } else if (fixY == 3 || fixY == undefined) {
            this.yAxis.forEach(yA => {
              if (typeof maxChecker === 'number' && typeof minChecker === 'number') {
                let maxNumber = maxChecker + (maxChecker / 2)
                yA.max = maxNumber > threshold[0]?.value ? Math.ceil(maxNumber) : threshold[0]?.value + 10
                yA.min = Math.floor(minChecker)
                let interval = (maxNumber - minChecker) / 2;
                yA.interval = interval.toFixed(1);
              }
            })
          } else if (fixY == 99) {
            yA.min = 0;
            yA.max = 2.5;
            yA.interval = 1;
            // yA.data = [0, 0.5, 1, 1.5];
          }
          else {
            yA.min = 0;
            yA.max = 2.0;
            yA.interval = 0.5;
            yA.data = [0, 0.5, 1, 1.5];
          }
        } else {
          if (fixY == 1) {
            yA.min = 0;
            yA.max = 10;
            yA.interval = 5;
            yA.data = [0, 3, 6, 10];
          } else if (fixY == 2) {
            yA.min = 0;
            yA.max = 2.0;
            yA.interval = 0.5;
            yA.data = [0, 0.5, 1, 1.5];
          } else if (fixY == 3 || fixY == undefined) {
            this.yAxis.forEach(yA => {
              if (typeof maxChecker === 'number' && typeof minChecker === 'number') {
                let maxNumber = maxChecker + (maxChecker / 2)
                yA.max = Math.ceil(maxNumber)
                yA.min = Math.floor(minChecker)

                let interval = (maxNumber - minChecker) / 2;
                yA.interval = interval.toFixed(1);
              }
            })
          }
        }
      })
    } else {
      this.yAxis.forEach(yA => {
        if (threshold) {
          if (fixY == 1) {
            yA.min = 0;
            yA.max = 10;
            yA.interval = 5;
            yA.data = [0, 3, 6, 10];
          } else if (fixY == 5) {
            yA.min = 0;
            yA.max = 10;
            yA.interval = 2.5;
          } else if (fixY == undefined) {
            this.yAxis.forEach(yA => {
              if (typeof maxChecker === 'number' && typeof minChecker === 'number') {
                let maxNumber = maxChecker + (maxChecker / 2)
                yA.max = maxNumber > threshold[0]?.value ? Math.ceil(maxNumber) : threshold[0]?.value + 10
                yA.min = Math.floor(minChecker)

                let interval = (maxNumber - minChecker) / 2;
                yA.interval = interval.toFixed(1);
              }
            })
          } else if (fixY == 3) {
            this.yAxis.forEach(yA => {
              if (typeof maxChecker === 'number' && typeof minChecker === 'number') {
                let maxNumber = maxChecker + (maxChecker / 2)
                yA.max = maxNumber > threshold[2]?.value ? Math.ceil(maxNumber) : threshold[2]?.value + 10
                yA.min = Math.floor(minChecker)

                let interval = (maxNumber - minChecker) / 2;
                yA.interval = interval.toFixed(1);
                console.log("ya.max", labels[0], yA.max, yA.min)
              }
            })
          } else if (fixY == 99) {
            yA.min = 0;
            yA.max = 2.5;
            yA.interval = 1;
            // yA.data = [0, 0.5, 1, 1.5];
          }
          else {
            yA.min = 0;
            yA.max = 2.0;
            yA.interval = 0.5;
            yA.data = [0, 0.5, 1, 1.5];
          }
        } else {
          if (fixY == 1) {
            yA.min = 0;
            yA.max = 10;
            yA.interval = 5;
            yA.data = [0, 3, 6, 10];
          } else if (fixY == 2) {
            yA.min = 0;
            yA.max = 2.0;
            yA.interval = 0.5;
            yA.data = [0, 0.5, 1, 1.5];
          } else if (fixY == 3 || fixY == undefined) {
            this.yAxis.forEach(yA => {
              if (typeof maxChecker === 'number' && typeof minChecker === 'number') {
                let maxNumber = maxChecker + (maxChecker / 2)
                yA.max = Math.ceil(maxNumber)
                yA.min = Math.floor(minChecker)

                let interval = (maxNumber - minChecker) / 2;
                yA.interval = interval.toFixed(1);
              }
            })
          }
          else if (fixY == 5) {
            yA.min = 0;
            yA.max = 10;
            yA.interval = 2.5;
          }
        }
      })

    }
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
}
