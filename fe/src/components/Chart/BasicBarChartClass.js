export default class BasicBarChartClass {
  constructor(datas, labels, legend, nameX = null, nameY = "kWh") {
    this.datas = datas;
    this.labels = labels;
    this.xAxis = {
      name: nameX,
      type: "category",
      data: labels,
      axisLabel: {
        color: "#fff",
        fontSize: 12,
      },
      
      animationDuration: 300,
      animationDurationUpdate: 300,
    };
    this.yAxis = {
      name: nameY,
      //   max: 'dataMax',
      splitLine: {
        show: false, // 구분선을 표시하지 않도록 설정
      },
      
      axisLabel: {
        color: "#fff", // 텍스트 색상을 빨간색으로 변경
        fontSize: 13,
      },
      
      axisLine: {
        show: true,
        lineStyle: {
          color: "#FFFFFF",
        },
      },
      nameAxisLabel:{
        overflow:'breakAll'

      }
    };
    this.tooltip = {
      show: true,
      trigger: "item",
      axisPointer: {},
    },
      (this.series = []);
    this.legend = {
      show: true,
      textStyle: {
        color: "#fff",
      },
    };
    this.grid = {
      show: false,
    };
    this.setSeries(datas, legend);
  }
  setSeries(data, legend) {
    let series = new Array()
    const chartColor = ['#6D5495', '#a866ad', '#846EFF', '#C2AFFF', '#EF5656',  '#EA6464', '#4931D3', '#9C98B2', '#3B0A89', '#B64B8D','#9922AF','#490755'];

    data.forEach((item, index) => {
      let seriesObj = {
        data : item,
        type : 'bar',
        name : legend[index],
        color : chartColor[index]
      }
      series.push(seriesObj)
    });


    this.series = series;
  }
  changeLegendShow(){
    this.legend.show = false
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
