import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import ECharts from "vue-echarts";
import VueLogger from "vuejs3-logger";
import Datepicker from "vue3-datepicker";
import "vue3-datepicker/dist/vue3-datepicker.css";

import "./assets/css/custom.css";
import "./assets/css/global.css";
import "./assets/css/peakcontrol.css";
import "./assets/css/layout.css";
import "./assets/css/font.css";
// quasar css 추가하면 몇몇 페이지가 깨짐... 이거 수정 !! 중요
// import "./assets/css/quasar.prod.css"

import BootstrapVue3 from "bootstrap-vue-3";
import "bootstrap-vue-3/dist/bootstrap-vue-3.css";

const isProduction = process.env.NODE_ENV === "production";

// Use plugin with optional defaults

const options = {
  isEnabled: true,
  logLevel: isProduction ? "error" : "debug",
  stringifyArguments: false,
  showLogLevel: true,
  showMethodName: true,
  separator: "|",
  showConsoleColors: true,
};

const app = createApp(App);
app.use(store);
app.use(BootstrapVue3);
// app.use(ECharts);
// app.use(Datepicker);
app.use(VueLogger, options);
app.component("Vue3Datepicker", Datepicker);
app.component(ECharts);
//
// 전체 영역 apiURL 변수화 처리
//
// 상대경로 접두사다. 절대 URL 을 쓰면 그 IP 가 번들에 인라인되어 현장마다 프런트를 다시
// 말아야 하고, 오리진이 갈려 CORS 도 따라온다. 프런트를 서빙하는 nginx(default.conf)가
// /ems-api/ 와 /epa/ 를 각각 ems-java-api, ems-py-api 컨테이너로 넘긴다.
//
// 접두사를 둘 다 /api 로 못 쓰는 이유: $pythonURL 쪽 호출 경로가 이미 /api/ 로 시작한다
// (`${pythonURL}/api/web/monitoring`). 같은 접두사를 쓰면 nginx 에서 구분이 안 된다.
//
// 아래 주석의 현장별 절대 URL 들은 이 방식 이전의 기록이다. 이제는 주소를 바꾸려고
// 이 줄을 건드릴 일이 없다 — nginx 가 서비스명으로 찾아간다.
app.config.globalProperties.$pythonURL = "/epa";
// app.config.globalProperties.$pythonURL = "http://localhost:23002";

app.config.globalProperties.$apiURL = "/ems-api";
// app.config.globalProperties.$apiURL = 'http://localhost:9000'; //dev
// app.config.globalProperties.$apiURL = 'http://localhost:9000'; // leegumi
// app.config.globalProperties.$apiURL = "http://localhost:10014"; //gosan
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //gumi
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //haepyeong
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //gunsan
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //buan
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //sanseong
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //goryeong
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //hakya
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //jain
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //unmun

// 포트 변경예정(금강)
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //gosan
// app.config.globalProperties.$apiURL = 'http://localhost:10114'; //gunsan
// app.config.globalProperties.$apiURL = 'http://localhost:10214'; //buan
// app.config.globalProperties.$apiURL = 'http://localhost:10314'; //sanseong
// 포트 변경예정(낙동강)
// app.config.globalProperties.$apiURL = 'http://localhost:10014'; //goryeong
// app.config.globalProperties.$apiURL = 'http://localhost:10114'; //gumi
// app.config.globalProperties.$apiURL = 'http://localhost:10214'; //hakya
// app.config.globalProperties.$apiURL = 'http://localhost:10314'; //haepyeong
// app.config.globalProperties.$apiURL = 'http://localhost:10414'; //jain
// app.config.globalProperties.$apiURL = 'http://localhost:10514'; //unmun

// app.config.globalProperties.$area = "gosan";
// app.config.globalProperties.$area = 'gumi';
// app.config.globalProperties.$area = 'haepyeong';
app.config.globalProperties.$area = 'gunsan';
// app.config.globalProperties.$area = 'buan';
// app.config.globalProperties.$area = 'sanseong';
// app.config.globalProperties.$area = 'goryeong';
// app.config.globalProperties.$area = 'hakya';
// app.config.globalProperties.$area = 'jain';
// app.config.globalProperties.$area = 'unmun';

// inpEditor 의 호스트 노출 포트. 컨테이너 내부는 항상 30090 이지만 호스트 매핑은 스택마다 다르다
// (로컬·운영 30090 / gunsan-dev 31090). EmsSubMenu 의 window.open 은 브라우저에서 실행되므로
// 도커 서비스명이 아니라 이 "호스트" 포트를 알아야 한다. 빌드 시 VUE_APP_INP_EDITOR_PORT 로 주입하고,
// 미주입이면 기존 동작(30090)을 유지한다. compose 의 inp-editor-fe ports: 와 반드시 같아야 한다.
app.config.globalProperties.$inpEditorPort = process.env.VUE_APP_INP_EDITOR_PORT || "30090";

app.use(router(app.config.globalProperties.$area));

app.mount("#app");
