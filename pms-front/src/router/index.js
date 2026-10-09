import { createRouter, createWebHistory } from "vue-router";
import store from '@/store';


const autoURL = "http://localhost";
const emsURL = "http://localhost:3000";
// const pmsURL = "http://localhost:4000";
const routes = [

  // 
  // 자율운영 메뉴바 
  // 
  {
    path: '/auto/:token',
    name: 'AutoMainDashBoard',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/${localStorage.getItem('token')}`;
    },
  },
  {
    path: '/receivingAlgorithm',
    name: 'receivingAlgorithm',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/receivingAlgorithm`;
    },
  },

  {
    path: '/coagulantsAlgorithm',
    name: 'coagulantsAlgorithm',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/coagulantsAlgorithm`;
    },
  },
  {
    path: '/mixingAlgorithm',
    name: 'mixingAlgorithm',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/mixingAlgorithm`;
    },
  },
  {
    path: '/sedimentationAlgorithm',
    name: 'sedimentationAlgorithm',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/sedimentationAlgorithm`;
    },
  },
  {
    path: '/filterAlgorithm',
    name: 'filterAlgorithm',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/filterAlgorithm`;
    },
  },
  {
    path: '/gacAlgorithm',
    name: 'gacAlgorithm',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/gacAlgorithm`;
    },
  },
  {
    path: '/disinfectionAlgorithm',
    name: 'disinfectionAlgorithm',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/disinfectionAlgorithm`;
    },
  },
  {
    path: '/ozoneAlgorithm',
    name: 'ozoneAlgorithm',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/ozoneAlgorithm`;
    },
  },
  {
    path: '/alarmHistory',
    name: 'alarmHistory',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/alarmHistory`;
    },
  },
  {
    path: '/aiHistory',
    name: 'aiHistory',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/aiHistory`;
    },
  },
  {
    path: '/operationHistory',
    name: 'operationHistory',
    beforeEnter: () => {
      const serverPort = getServerPort(store.state.area);
      window.location.href = `${autoURL}:${serverPort}/operationHistory`;
    },
  },

  {
    path: '/',
    name: 'Dashboard',
    component: () => import("@/views/DashBoard/MainDashBoard.vue"),
    beforeEnter: (to, from, next) => {
      // 여기서 store.area를 고산이면 'Dashboard'로, 학야면 'AnotherComponent'로 설정
      if (store.state.area === 'gosan') {
        next({ name: 'Dashboard_G' });
      } else if (store.state.area === 'hakya') {
        next({ name: 'Dashboard_H' });
      } else if (store.state.area === 'gumi') {
        // 다른 경우에는 특정 페이지로 리디렉션 또는 기본값으로 설정할 수 있음
        next({ name: 'Dashboard_Gu' });
      }
    },
  },
  {
    path: '/:token?',
    name: 'Dashboard_G',
    component: () => import("@/views/DashBoard/MainDashBoard.vue"),
  },
  {
    path: "/PumpControl",
    name: "PumpControl",
    component: () => import("@/views/PumpControl.vue"),
  },
  {
    path: '/StatsHistory',
    name: 'StatsHistory',
    component: () => import("@/views/StatsHistory.vue"),
  },

  {
    path: "/PumpMonitoring",
    name: "PumpMonitoring",
    props: route => ({ alarmData: route.query.alarmData }),
    component: () => import("@/views/PumpMonitoring.vue"),
  },
  {
    path: "/PrecisionDiagnosis",
    name: "PrecisionDiagnosis",
    component: () => import("@/views/PrecisionDiagnosis.vue"),
  },
  {
    path: '/:token?',
    name: 'Dashboard_H',
    component: () => import("@/views/DashBoard/MainDashBoardHakya.vue"),
  }
  ,
  {
    path: '/:token?',
    name: 'Dashboard_Gu',
    component: () => import("@/views/DashBoard/MainDashBoardGumi.vue"),
  }
  ,

  //
  // EMS 페이지로 넘어가도록 route에서 지정  
  // 
  {
    path: '/ems',
    name: 'MainDashBoard',
    beforeEnter: () => {
      window.location.href = `${emsURL}/`;
    }
  },
  {
    path: '/EMSPumpControl',
    name: 'EMSPumpControl',
    beforeEnter: () => {
      window.location.href = `${emsURL}/EMSPumpControl`;
    }
  },
  {
    path: '/PumpControlDetailed',
    name: 'PumpControlDetailed',
    beforeEnter: () => {
      window.location.href = `${emsURL}/PumpControlDetailed`;
    }
  },
  {
    path: '/PumpControlTrand',
    name: 'PumpControlTrand',
    beforeEnter: () => {
      window.location.href = `${emsURL}/PumpControlTrand`;
    }
  },
  {
    path: '/PumpDrvnAnly',
    name: 'PumpDrvnAnly',
    beforeEnter: () => {
      window.location.href = `${emsURL}/PumpDrvnAnly`;
    }
  },
  {
    path: '/PumpHistory',
    name: 'PumpHistory',
    beforeEnter: () => {
      window.location.href = `${emsURL}/PumpHistory`;
    }
  },
  {
    path: '/MajorDrainage',
    name: 'MajorDrainage',
    beforeEnter: () => {
      window.location.href = `${emsURL}/MajorDrainage`;
    }
  },
  {
    path: '/PowerPeakAnalysis',
    name: 'PowerPeakAnalysis',
    beforeEnter: () => {
      window.location.href = `${emsURL}/PowerPeakAnalysis`;
    }
  },
  {
    path: '/PowerPeakDetail',
    name: 'PowerPeakDetail',
    beforeEnter: () => {
      window.location.href = `${emsURL}/PowerPeakDetail`;
    }
  },
  {
    path: '/FacUse',
    name: 'FacUse',
    beforeEnter: () => {
      window.location.href = `${emsURL}/FacUse`;
    }
  },
  {
    path: '/UseTrand',
    name: 'UseTrand',
    beforeEnter: () => {
      window.location.href = `${emsURL}/UseTrand`;
    }
  },
  {
    path: '/CostAnaylsis',
    name: 'CostAnaylsis',
    beforeEnter: () => {
      window.location.href = `${emsURL}/CostAnaylsis`;
    }
  },
  {
    path: '/ReductionTargetStatus',
    name: 'ReductionTargetStatus',
    beforeEnter: () => {
      window.location.href = `${emsURL}/ReductionTargetStatus`;
    }
  },
  {
    path: '/TagInfo',
    name: 'TagInfo',
    beforeEnter: () => {
      window.location.href = `${emsURL}/TagInfo`;
    }
  },
  {
    path: '/SongsuPumpOperation',
    name: 'SongsuPumpOperation',
    beforeEnter: () => {
      window.location.href = `${emsURL}/SongsuPumpOperation`;
    }
  },
  {
    path: '/EletricityPlan',
    name: 'EletricityPlan',
    beforeEnter: () => {
      window.location.href = `${emsURL}/EletricityPlan`;
    }
  },
  {
    path: '/ReductionTarget',
    name: 'ReductionTarget',
    beforeEnter: () => {
      window.location.href = `${emsURL}/ReductionTarget`;
    }
  },
  {
    path: '/TargetStategyPeak',
    name: 'TargetStategyPeak',
    beforeEnter: () => {
      window.location.href = `${emsURL}/TargetStategyPeak`;
    }
  },
  {
    path: '/DailyReport',
    name: 'DailyReport',
    beforeEnter: () => {
      window.location.href = `${emsURL}/DailyReport`;
    }
  },
  {
    path: "/PumpControlHistory",
    name: "PumpControlHistory",
    beforeEnter: () => {
      window.location.href = `${emsURL}/PumpControlHistory`;
    }
  },




];

function getServerPort(area) {
  const validAreas = ['gosan', 'gunsan', 'sanseong', 'buan', 'gumi', 'haepyeong', 'hakya', 'goryeong', 'jain', 'unmun'];
  const portMapping = {
    gosan: 10011,
    gunsan: 10021,
    sanseong: 10031,
    buan: 10041,
    gumi: 10111,
    haepyeong: 10121,
    hakya: 10131,
    goryeong: 10141,
    jain: 10151,
    unmun: 10161,
  };

  return validAreas.includes(area) ? portMapping[area] : 10013;
}

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});
if (window.location.pathname.split('/').filter(Boolean).pop() === undefined && (!localStorage.getItem('token') || localStorage.getItem('token') === 'undefined')) {
  const serverPort = getServerPort(store.state.area);
  window.location.href = `${autoURL}:${serverPort}/login`;
}
export default router;