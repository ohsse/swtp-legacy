import { createApp } from 'vue'
import App from './App.vue'
import router from "./router";
import store from "./store";
import ECharts from 'vue-echarts'
import { use } from "echarts/core"
import Datepicker from "vue3-datepicker";
import 'vue3-datepicker/dist/vue3-datepicker.css';

import "./assets/css/custom.css";
import "./assets/css/global.css";
import "./assets/css/peakcontrol.css";
import "./assets/css/layout.css";
import "./assets/css/font.css";

import {
    CanvasRenderer
  } from 'echarts/renderers'
  import {
    BarChart,
    PieChart,
    LineChart,
    ScatterChart,
  } from 'echarts/charts'
  import {
    GridComponent,
    TooltipComponent,
    TitleComponent,
    LegendComponent,
    DataZoomComponent
  } from 'echarts/components'
  
  use([
    CanvasRenderer,
    BarChart,
    PieChart,
    LineChart,
    ScatterChart,
    GridComponent,
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    DataZoomComponent
  ])


import "@/styles/common.scss";
import BootstrapVue3 from "bootstrap-vue-3";
import "bootstrap-vue-3/dist/bootstrap-vue-3.css";



const app = createApp(App);
app.use(BootstrapVue3);
app.use(router);
app.use(store);
app.component('Vue3Datepicker', Datepicker);
app.component('v-chart', ECharts)
app.mount("#app");
