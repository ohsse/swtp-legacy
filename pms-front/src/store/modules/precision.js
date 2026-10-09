const precision = {
  namespaced: true,
  state: {
    titles: [],
    changeTime: '',
    settingPump: -1,
    choiceMoter: "",
    choiceChannel: "",
    startDt: "",
    endDt: "",
    mainChart: [],
    pumps: [],
    chartDatas: [
      {
        isChange: true,
        title: " Overall Trend (150 20816_3 Alarm Limits)",
        yName: "속도[mm/s]",
        data: [],
        name: "",
      },
      {
        isChange: true,
        title: " TimeWave",
        yName: "속도[mm/s]",
        data: [],
        name: "",
      },
      {
        isChange: true,
        title: " Spectrum",
        yName: "속도[mm/s]",
        data: [],
        name: "",
      },
    ],
    async getData(rootState, data, reqTxt) {
      data.motor_id = rootState.precision.choiceMoter;
      data.channel_nm = rootState.precision.choiceChannel;
      const myHeaders = new Headers();
      myHeaders.append("Content-Type", "application/json");
      let res = await fetch(
        `${rootState.globalIP}/api/v1/diagnosis/${reqTxt}`,
        {
          method: "POST",
          headers: myHeaders,
          body: JSON.stringify(data),
        }
      );
      return await res.json();
    },
  },
  actions: {
    async spectrumFreq({ rootState, commit }, data) {
      const res = await rootState.precision.getData(rootState, data, "spectrumFreq");
      commit("spectrumFreq", res.datas);
    },
    async choiceMoter({ commit }, data) {
      commit("choiceMoter", data)
    },
    async getMainChart({ rootState, commit }, data) {
      const res = await rootState.precision.getData(rootState, data, "rms");
      commit("getMainChart", res.datas);
    },
    async getTimeWaveChart({ rootState, commit }, data) {
      const res = await rootState.precision.getData(
        rootState,
        data,
        "timewave"
      );
      commit("getTimeWaveChart", res.datas);
    },
    async getSpectrumChart({ rootState, commit }, data) {
      const res = await rootState.precision.getData(
        rootState,
        data,
        "spectrum"
      );
      commit("getSpectrumChart", res.datas);
      this.dispatch("precision/spectrumFreq", { acq_date: data.acq_date })
    },
    async getPumps({ rootState, commit }) {
      let res = await fetch(`${rootState.globalIP}/api/v1/diagnosis/pumpList`, {
        method: "GET",
      });
      res = await res.json();
      commit("getPumps", res.datas);
    },
  },
  mutations: {
    setDate(state, datas) {
      state.startDt = datas.startDate
      state.endDt = datas.endDate
    },
    getMainChart(state, datas) {
      const temp = [];
      datas.forEach((item) => {
        temp.push([item.ACQ_DATE, item.RMS]);
      });
      state.chartDatas[0].data.length = 0;
      state.chartDatas[0].data = []
      state.chartDatas[0].data.push(temp);
      state.chartDatas[0].isChange = !state.chartDatas[0].isChange
    },
    getTimeWaveChart(state, datas) {
      state.chartDatas[1].data = []
      state.chartDatas[1].data.length = 0
      const temp = []
      datas?.at(0)?.DATA_ARRAY.forEach(item => {
        temp.push([(item.x / 12800).toFixed(2), item.y])
      })
      state.chartDatas[1].data.push(temp)
      // state.chartDatas[1].data = datas;
    },
    spectrumFreq(state, datas) {
      state.chartDatas[2].xLines = 0
      state.chartDatas[2].xLines = []
      datas.forEach(item => {
        state.chartDatas[2].xLines.push({ value: item.FREQ_VALUE, type: item.FREQ_TYPE + 'x' })
      })
    },
    getSpectrumChart(state, datas) {
      state.chartDatas[2].data = []
      state.chartDatas[2].data.length = 0
      const temp = []
      datas?.at(0)?.DATA_ARRAY.forEach(item => {
        temp.push([item.x, item.y])
      })
      state.chartDatas[2].data.push(temp)
    },
    getPumps(state, datas) {
      state.choiceMoter = datas[0][0].MOTOR_ID;
      state.choiceChannel = datas[0][0].CHANNEL_NM.split(",")[0];
      state.pumps = datas;
    },
    settingPump(state, data) {
      state.settingPump = data;
    },
    choiceMoter(state, data) {
      state.choiceMoter = data.motor;
      state.choiceChannel = data.channel;
    },
    titles(state, data) {
      state.titles = data;
    },
    changeTime(state, data) {
      state.changeTime = data;
    }
  },
};
export default precision;
