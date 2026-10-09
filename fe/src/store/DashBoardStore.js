import { reactive } from "vue";

// state는 Vuex의 상태를 나타냅니다.
const state = reactive({
  nowElec: [],
});

// actions는 Vuex의 액션을 나타냅니다.
const actions = {
  // fetchNowElec 함수는 http://localhost:8080/selectNowElec에 요청을 보냅니다.
  async fetchNowElec({ commit }) {
    try {
      // response는 http://localhost:8080/selectNowElec에 대한 응답입니다.
      const response = await fetch("http://localhost:8080/selectNowElec");
      // data는 http://localhost:8080/selectNowElec에 대한 응답의 JSON 데이터입니다.
      const data = await response.json();
      // setNowElec mutation은 nowElec의 값을 수정합니다.
      commit("setNowElec", data);
    } catch (error) {
      // 오류가 발생하면 에러를 콘솔에 출력합니다.
    }
  },
};

// mutations는 Vuex의 mutation을 나타냅니다.
const mutations = {
  // setNowElec mutation은 nowElec의 값을 수정합니다.
  setNowElec(state, nowElec) {
    // state.nowElec에 nowElec의 값을 설정합니다.
    state.nowElec = nowElec;
  },
};

// getters는 Vuex의 getter를 나타냅니다.
const getters = {
  // getNowElec getter는 nowElec의 값을 가져옵니다.
  getNowElec: (state) => state.nowElec,
};

// export default는 state, actions, mutations, getters를 정의합니다.
export default {
  namespaced: true,
  state: state,
  actions: actions,
  mutations: mutations,
  getters: getters,
};
