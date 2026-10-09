export default class BarChartClass {
  constructor(datas, labels, nameX = null, nameY = null) {
    this.datas = datas;
    this.labels = labels;
    this.nameX = nameX;
    this.nameY = nameY
    this.xAxis = {
      name: nameX,
      type: "category",
      data: labels,
      axisLine: {
        show: true,
        lineStyle: {
          color: "#FFFFFF",
        },
      },
      axisLabel: {
        rotate: 90,
        color: "#fff",
        fontSize: 12,
      },

      //   inverse: true,
      animationDuration: 300,
      animationDurationUpdate: 300,
      // max: 2
    };
    this.yAxis = {
      name: nameY,
      //   max: 'dataMax',
      splitLine: {
        show: false, // 구분선을 표시하지 않도록 설정
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: "#FFFFFF",
        },
      },
      axisLabel: {
        color: "#fff",
        fontSize: 13,
      },
    };
    (this.tooltip = {
      show: true,
      trigger: "item",
      axisPointer: {},
    }),
      (this.series = []);
    this.legend = {
      show: false,
      textStyle: {
        color: "#fff",
      },
    };
    this.grid = {
      show: false,
    };
    this.setSeries(datas, labels);
  }
  setSeries(data, labels) {
    const nullArrayData = this.generateNullArray(data);
    const chartColor = ['#0affff', '#0887e2', '#85fbff', '#1f706d', '#25f4bc', '#A6FF96', '#ff9b05', '#FF6464', '#F7FD04', '#FFA3FD', '#7045f2', '#9922AF'];
    // const chartColor = [ '#13FFFF', '#13DFFF', '#13B3FF', '#137AFF', '#0F4EEE',  '#9962FE', '#CD81FF', '#E63EFF', '#F122B9', '#F21A68','#EC0820','#F97226'];
    // const chartColor = ['#6D5495', '#a866ad', '#846EFF', '#C2AFFF', '#EF5656',  '#EA6464', '#4931D3', '#9C98B2', '#3B0A89', '#B64B8D','#9922AF','#490755'];
    let seriesData = new Array();
    for (let i in nullArrayData) {
      seriesData.push({
        data: nullArrayData[i],
        type: "bar",
        name: labels[i],
        barGap: "-100%",
        barCategoryGap: "40%",
        color: chartColor[i],
        label: {
          show: false, // 데이터 레이블 표시 여부
          position: 'top', // 레이블 위치 (top, inside, ...)
          color: "#FFFFFF", // 레이블 텍스트 색상
          fontSize: 12 // 레이블 텍스트 크기
        }
      });
      this.series.push({
        data: nullArrayData[i],
        type: "bar",
        name: labels[i],
        barGap: "-100%",
        barCategoryGap: "40%",
        color: chartColor[i]
      });
    }

    this.series = seriesData;
  }
  generateNullArray(arr) {
    const result = [];
    const length = arr.length;

    for (let i = 0; i < length; i++) {
      const nullArray = Array(length).fill(null);
      nullArray[i] = arr[i];
      result.push(nullArray);
    }

    return result;
  }
  axisChange(axis) {
    let labelAxis = {
      type: "category",
      data: this.labels,
      animationDuration: 300,
      animationDurationUpdate: 300,
      axisLine: {
        show: true,
        lineStyle: {
          color: "#FFFFFF",
        },
      },
      axisLabel: {
        color: "#fff",
        fontSize: 13,
      },
    };
    let dataAxis = {
      splitLine: {
        show: false,
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: "#FFFFFF",
        },
      },
      axisLabel: {
        color: "#fff",
        fontSize: 13,
      },
    };
    if (axis == "x") {
      labelAxis.name = this.nameX
      dataAxis.name = this.nameY
      this.xAxis = labelAxis;
      this.yAxis = dataAxis;
    } else if (axis == "y") {
      labelAxis.name = this.nameY
      dataAxis.name = this.nameX
      this.xAxis = dataAxis;
      this.yAxis = labelAxis;
    }
  }
  changeLegendShow() {
    this.legend.show = false
  }
  setGridSize(left = '0%', right = '0%', top = '0%', bottom = '0%') {
    this.grid.left = left  // 그리드 왼쪽 여백
    this.grid.right = right  // 그리드 오른쪽 여백
    this.grid.top = top    // 그리드 상단 여백
    this.grid.bottom = bottom  // 그리드 하단 여백
  }
  changeAxisLabelRotation(degrees) {
    this.xAxis.axisLabel.rotate = degrees;
  }
  toggleDataLabels(position) {
    for (let i in this.series) {
      this.series[i].label.position = position
      this.series[i].label.show = true;
    }
  }
}
