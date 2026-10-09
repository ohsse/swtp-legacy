import ChartClass from './ChartClass';

export default class ChartLineClass extends ChartClass {

  // overiding
  constructor(dataX, dataY, labels, detline, nameX, nameY) {
    super(dataX, dataY, labels, detline, nameX, nameY);
    this.lineChange();
  }

  newFunction(dataY) {
    console.log("dataYY", dataY);
    let flatDataY = dataY.flat();

    //let sumOfFlatDataY = flatDataY.reduce((acc, value) => acc + value, 0);
    //let averageY =  Math.ceil(sumOfFlatDataY / flatDataY.length);

    // 십의 자리보고 100 단위로 반올림 
    //let newMinValue = (Math.floor(((averageY / 1.2)) / 100)) * 100;

    let minValue = Math.min(...flatDataY);
    // console.log("dataYY - minValue", minValue);
    let minValueTenPercent = minValue - (minValue * 0.05);
    let roundedValue = Math.floor(minValueTenPercent / 10) * 10;

    let maxValue = Math.max(...flatDataY);
    // console.log("dataYY - maxValue", maxValue);
    let maxValueTenPercent = maxValue + (maxValue * 0.05);
    let roundedMaxValue = Math.ceil(maxValueTenPercent / 10) * 10;

    this.yAxis[0].min = roundedValue;
    this.yAxis[0].max = roundedMaxValue;


  }

}


