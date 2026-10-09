export default class DoughnutChartClass {
  constructor(data, radius = ["40%", "70%"], center = ['50%', '50%']) {
    var chartColor = ['#0086B3', '#0095FF', '#0271bb', '#15A88A', '#0b7f3d', '#49A92F', '#D68101', '#FF3838', '#A09818', '#E65EDC', '#865DFF', '#9922AF'];
    this.tooltip = {
      trigger: "item",
      formatter: "{b}: {d}%",
    };
    this.legend = {
      top: "5%",
      left: "right",
      orient: "vertical",
      textStyle: {
        color: '#ffffff',
        fontSize: 10
      },
    };
    this.series = [
      {
        name: "Access From",
        type: "pie",
        radius: radius,
        center: center,
        avoidLabelOverlap: false,
        label: {
          show: true,
          position: "inner",
          formatter: "{d}%",
          color: 'white',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 40,
            fontWeight: "bold",
          },
        },
        labelLine: {
          show: false,
        },
        data: data,
        itemStyle: {
          // 차트 아이템(원)의 색상 설정
          color: function (params) {
            const colors = chartColor; // 색상 배열 예시

            return colors[params.dataIndex % colors.length];
          }
        },
      },
    ];
    this.grid = {
      left: "0",
      right: "0",
      bottom: "0",
      top: "0",
      containLabel: true,
    };
  }
  changeLegendShow() {
    this.legend.show = false
  }
  changeLegendFontSize(fontSize) {
    this.legend.textStyle.fontSize = fontSize
  }
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
