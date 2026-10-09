export async function getPowerPeakData(apiURL) {
  let now = new Date();
  var year2 = now.getFullYear();
  var month2 = twoDigits(now.getMonth() + 1);
  var date = twoDigits(now.getDate());

  let todayTime = year2 + "-" + month2 + "-" + date;

  // const apiURL = this.$apiURL;
  let res = await fetch(`${apiURL}/ai/selectPwrPrdctList?date=${todayTime}`);
  // let res = await fetch(`${apiURL}/ai/peakSelect?date=${todayTime}`);
  let data = await res.json();
  if (data !== null) {
    let dataX = [];
    let dataY = [[], []];
    for (let i = 0; i < data.data.length; i++) {
      dataX.push(data.data[i]["DATE"]);
      let pwr = data.data[i]["PWR"];

      let prdctPwr = data.data[i]["PRDCT_PWR"];

      if (isNaN(prdctPwr)) {
        // 숫자 변환이 실패한 경우
        dataY[1].push(0);
      } else {
        dataY[1].push(prdctPwr);
      }

      if (isNaN(pwr)) {
        // dataY[0].push[0];
      } else {
        dataY[0].push(pwr);
      }
    }
    dataY[0].slice(0, new Date().getHours() + 1)
    let detline;

    let res2 = await fetch(`${apiURL}/st/selectPeakGoal`);
    let data2 = await res2.json();
    if (data2 !== null) {
      detline = data2.data[0]["value"];
    }
    // return new ChartClass(
    //   dataX,
    //   dataY,
    //   ["전력 피크 예상 시간", "전력 피크 발생 시간"],
    //   detline,
    //   "날짜",
    //   "kWh"
    // )

    return { dataX, dataY, detline };
  }
}

export function twoDigits(num) {
  return num.toString().padStart(2, "0");
}
