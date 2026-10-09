import * as echarts from "echarts";
export default class FrqncBarChartClass {
  constructor(dates, labels, datas) {
    this.dates = dates;
    this.labels = labels;
    this.datas = datas;
    this.xAxis = {
        name : '날짜',
        data: this.dates,
        type: "category",
        boundaryGap: false,
        axisLine: {
            show: true,
            lineStyle: {
            color: "#FFFFFF",
            },
        },
    };
    this.yAxis = {
        data: this.labels,
        axisLine: {
            show: true,
            lineStyle: {
            color: "#FFFFFF",
            },
        },
    };
    this.series = [
      {
        type: "custom",
        renderItem: function (params, api) {
            
            var categoryIndex = api.value(1);
            var start = api.coord([api.value(0), categoryIndex]);
            var end = api.coord([api.value(2), categoryIndex]);
            var height = api.size([0, 1])[1] * 0.6;
        
            if (api.value(3) === 0) {
              // If value is 0, don't draw the bar
              return null;
            }
        
            var rectShape = echarts.graphic.clipRectByRect(
              {
                x: start[0],
                y: start[1] - height / 2,
                width: end[0] - start[0],
                height: height,
              },
              {
                x: params.coordSys.x,
                y: params.coordSys.y,
                width: params.coordSys.width,
                height: params.coordSys.height,
              }
            );
            return (
              rectShape && {
                type: "rect",
                transition: ["shape"],
                shape: rectShape,
                style: api.style(),
              }
            );
        
        },
        itemStyle: {
          opacity: 0.8,
        },
        encode: {
          x: [0, 1],
          y: 0,
        },
        data: this.datas,
      },
    ];
  }
  renderItem(params, api) {
   
    var categoryIndex = api.value(1);
    var start = api.coord([api.value(0), categoryIndex]);
    var end = api.coord([api.value(2), categoryIndex]);
    var height = api.size([0, 1])[1] * 0.6;

    if (api.value(3) === 0) {
      // If value is 0, don't draw the bar
      return null;
    }

    var rectShape = echarts.graphic.clipRectByRect(
      {
        x: start[0],
        y: start[1] - height / 2,
        width: end[0] - start[0],
        height: height,
      },
      {
        x: params.coordSys.x,
        y: params.coordSys.y,
        width: params.coordSys.width,
        height: params.coordSys.height,
      }
    );
    return (
      rectShape && {
        type: "rect",
        transition: ["shape"],
        shape: rectShape,
        style: api.style(),
      }
    );
  }
}
