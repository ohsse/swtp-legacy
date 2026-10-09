import { createStore } from 'vuex';
import DashBoardStore from './DashBoardStore';

export default createStore({
modules: {
dashboard: DashBoardStore,
},
});