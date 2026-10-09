import { fetchFunc } from '@/util/fetchFunc';
//하단 관압 데이터 설정
export function setPresData() {
  this.botMidCur = []
  this.botMidPre = []
  this.rate = []
  this.presTag.forEach((item, i) => {
  for (let key in this.botMidCurPresData) {
    if (Object.keys(this.botMidCurPresData).length != 0) {
        if (item == key && this.botMidCurPresData[key].length > 0) {
          this.botMidCur[i] = this.botMidCurPresData[key][this.botMidCurPresData[key].length - 1]?.toFixed(1);
        }
    }
  }
});
this.presTag.forEach((item, i) => {
  for (let key in this.botMidPrePresData) {
    if (Object.keys(this.botMidPrePresData).length != 0) {
        if (item == key && this.botMidPrePresData[key].length > 0) {
          this.botMidPre[i] = this.botMidPrePresData[key][this.botMidPrePresData[key].length - 1]?.toFixed(1);
        }
    }
  }
});

  this.botMidCur?.forEach((item, i) => {
    if (parseFloat(item) != 0) {
      this.rate[i] = ((parseFloat(this.botMidPre[i]) - parseFloat(item)) / parseFloat(item) * 100)?.toFixed(2)
    }
    else {
      this.rate[i] = ((parseFloat(this.botMidPre[i]) - parseFloat(item)) * 100)?.toFixed(2)
    }
  })
  this.presTag.forEach((item, i) => {
    const roundedCurData = this.botMidCurPresData[item]?.map(value => Math.round(value * 100) / 100);
    const roundedPreData = this.botMidPrePresData[item]?.map(value => Math.round(value * 100) / 100);
    if(this.$refs.PumpDrvnAnlyBotMid[i]){
    this.$refs.PumpDrvnAnlyBotMid[i].createChart(roundedCurData, this.curTs);
    this.$refs.PumpDrvnAnlyBotMid[i].createPreChart(roundedCurData,roundedPreData, this.preTs);
    }
  })
}

//하단 수요량 데이터 설정
export function setFlowData() {
  this.botMidCur = []
  this.botMidPre = []
  this.rate = []
  this.flowTag.forEach((item, i) => {
  for (let key in this.botMidCurFlowData) {
      if (item == key) {
        this.botMidCur[i] = this.botMidCurFlowData[key][this.botMidCurFlowData[key].length - 1]?.toFixed(1)
      }
  }
})

  this.flowTag.forEach((item, i) => {
    for (let key in this.botMidPreFlowData) {
      if (item == key) {
        this.botMidPre[i] = this.botMidPreFlowData[key][this.botMidPreFlowData[key].length - 1]?.toFixed(1)
      }
    }
  })
  this.botMidCur?.forEach((item, i) => {
    if (parseFloat(item) != 0) {
      this.rate[i] = ((parseFloat(this.botMidPre[i]) - parseFloat(item)) / parseFloat(item) * 100)?.toFixed(2)
    }
    else {
      this.rate[i] = ((parseFloat(this.botMidPre[i]) - parseFloat(item)) * 100)?.toFixed(2)
    }
    if (isNaN(this.rate[i])) {
      this.rate[i] = ''
    }
  })
  this.flowTag.forEach((item, i) => {
  for (let key in this.botMidCurFlowData) {
      if (item == key) {
        const value = this.botMidCurFlowData[key][this.botMidCurFlowData[key].length - 1];
        // if(i==0) this.pwrCurUnit = (parseFloat(this.curPwr)/value).toFixed(4)
        const formattedValue = Math.round(value).toLocaleString();
        this.botMidCur[i] = formattedValue;
      }
  }
})

  this.flowTag.forEach((item, i) => {
    for (let key in this.botMidPreFlowData) {
      if (item == key) {
        const value = this.botMidPreFlowData[key][this.botMidPreFlowData[key].length - 1];
        // if(i==0) this.pwrPreUnit = (parseFloat(this.prePwr)/value).toFixed(4)
        const formattedValue = Math.round(value).toLocaleString();
        this.botMidPre[i] = formattedValue;
      }
    }
  })
  this.flowTag.forEach((item, i) => {
    const roundedCurData = this.botMidCurFlowData[item]?.map(value => Math.floor(value));
    const roundedPreData = this.botMidPreFlowData[item]?.map(value => Math.floor(value));
    if(this.$refs.PumpDrvnAnlyBotMid[i] && roundedCurData?.length && roundedPreData?.length && this.curTs?.length && this.preTs?.length){
      this.$refs.PumpDrvnAnlyBotMid[i].createChart(roundedCurData, this.curTs)
      this.$refs.PumpDrvnAnlyBotMid[i].createPreChart(roundedCurData, roundedPreData, this.preTs);
    }
  })
}

//하단 수위 데이터 설정
export function setLevelData() {
  this.botMidCur = []
  this.botMidPre = []
  this.rate = []
  this.levelTag.forEach((item, i) => {
  for (let key in this.botMidCurLevelData) {
    if (Object.keys(this.botMidCurLevelData).length != 0) {
        if (item == key && this.botMidCurLevelData[key].length > 0) {
          this.botMidCur[i] = this.botMidCurLevelData[key][this.botMidCurLevelData[key].length - 1].toFixed(2);
        }
    }
  }
});
if(this.$area ==='unmun'){
  this.levelTag.forEach((item, i) => {
    for (let key in this.botMidCurLevelData) {
      if (Object.keys(this.botMidPreLevelData).length != 0) {
          if (item == key && this.botMidPreLevelData[key]?.length > 0) {
            this.botMidPre[i] = this.botMidPreLevelData[key][this.botMidPreLevelData[key].length - 1].toFixed(2);
          }
          else if(item == key){
            this.botMidPreLevelData[key] = this.botMidCurLevelData[key]
            this.botMidPre[i] = this.botMidPreLevelData[key][this.botMidPreLevelData[key].length - 1].toFixed(2);
          }
      }
    }
  });
}
else{
  this.levelTag.forEach((item, i) => {
    for (let key in this.botMidCurLevelData) {
      if (Object.keys(this.botMidCurLevelData).length != 0) {
          if (item == key && this.botMidCurLevelData[key].length > 0) {
            this.botMidPre[i] = this.botMidCurLevelData[key][this.botMidCurLevelData[key].length - 1].toFixed(2);
          }
      }
    }
  });
}

  this.botMidCur?.forEach((item, i) => {
    if (parseFloat(item) != 0) {
      this.rate[i] = ((parseFloat(this.botMidPre[i]) - parseFloat(item)) / parseFloat(item) * 100).toFixed(2)
    }
    else {
      this.rate[i] = ((parseFloat(this.botMidPre[i]) - parseFloat(item)) * 100).toFixed(2)
    }
  })

  this.levelTag.forEach((item, i) => {
    let roundedPreData
    const roundedCurData = this.botMidCurLevelData[item]?.map(value => Math.round(value * 100) / 100);
    if(this.$area ==='unmun'){
      roundedPreData = this.botMidPreLevelData[item]?.map(value => Math.round(value * 100) / 100);
    }
    else{
      roundedPreData = this.botMidCurLevelData[item]?.map(value => Math.round(value * 100) / 100);

    }
    if(this.$refs.PumpDrvnAnlyBotMid[i]){
    this.$refs.PumpDrvnAnlyBotMid[i].createChart(roundedCurData, this.curTs);
    this.$refs.PumpDrvnAnlyBotMid[i].createPreChart(roundedCurData,roundedPreData, this.preTs);
    }
  })
}


export async function ExcelDown(type) {
  let grpNumber = this.tabIndex + 1
  if(this.$area === 'buan') grpNumber = 1
  else if(this.$area === 'goryeong'){
    if(this.tabIndex === 0 || this.tabIndex === 2) grpNumber = 1
    else grpNumber =2
  }

  this.time = await this.getDateParams()
  let loadingState;
  if (type === 'pre') {
    loadingState = 'preExcelLoading';
  } else if (type === 'anly') {
    loadingState = 'anlyExcelLoading';
  } else {

    return;
  }

  this[loadingState] = true;

  try {
    let response
    if(this.tabIndex === -1){
      response = await fetch(`${this.$apiURL}/dr/download?startDate=${this.time}&range=${this.range}&findIdx=${type === 'pre' ? 1 : 2}&cycle=${this.cycle}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
    }
    else{
      response = await fetch(`${this.$apiURL}/dr/download?startDate=${this.time}&range=${this.range}&findIdx=${type === 'pre' ? 1 : 2}&cycle=${this.cycle}&pump_grp=${grpNumber}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(new Blob([blob]));
    const a = document.createElement('a');
    a.href = url;
    a.download = `${type === 'pre' ? '예측 결과.xlsx' : '분석 이력.xlsx'}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  } catch (error) {
   
    alert('엑셀 다운로드 실패');
  }

  this[loadingState] = false;
}
export async function createPlotly() {
  this.time = await this.getDateParams()
  const ploty_xDate = []
  const ploty_flowData = []
  const ploty_presData = []
  this.historyData = (await fetchFunc(`${this.$apiURL}/dr/getPumpUse?startDate=${this.time}&cycle=${this.cycle}&range=${this.range}&pump_grp=${this.tabIndex + 1}`)).data
  this.preHistoryData = (await fetchFunc(`${this.$apiURL}/dr/predictionPumpCombination?startDate=${this.time}&cycle=${this.cycle}&range=${this.range}&pump_grp=${this.tabIndex + 1}`)).data
  if (this.tabIndex === 0) {
    this.oldPreData?.data.forEach(element => {
      ploty_xDate.push(element.date)
      ploty_flowData.push((element.flow).toFixed(0))
      ploty_presData.push((element.pressure).toFixed(2))
    })
  } else if (this.tabIndex === 1) {
    this.newPreData?.data.forEach(element => {
      ploty_xDate.push(element.date)
      ploty_flowData.push((element.flow).toFixed(0))
      ploty_presData.push((element.pressure).toFixed(2))
    })
  }
  this.$refs.PlotlyLineChart.makeChart(ploty_xDate, Object.keys(this.historyData), Object.values(this.historyData), this.selectedCycle, '', ploty_flowData, ploty_presData, Object.values(this.preHistoryData), 0, 0.08)
}
