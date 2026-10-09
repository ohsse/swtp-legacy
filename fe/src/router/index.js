import { createRouter, createWebHistory } from "vue-router";
import Route from "./Route";
import drvnRoute from "./drvnRoute";

// const autoURL = "http://localhost";
// 자율운영 포털은 이 스택 밖의 별도 앱이고 포트도 다르다(getServerPort). 같은 오리진이
// 아니라서 nginx 로 프록시할 대상이 없으므로 상대경로로는 못 간다. 대신 접속한 호스트를
// 그대로 따라가게 해서 IP 하드코딩만 걷어낸다 — 포털은 늘 프런트와 같은 서버에 있다.
// (예전에는 고산 운영망 localhost 고정이라 현장마다 프런트를 다시 말아야 했다)
const autoURL = `http://${window.location.hostname}`;
// const pmsURL = "http://localhost:4000";
const pmsURL = "http://localhost:10015"; //gosan
// const pmsURL = 'http://localhost:10015'; //gumi
// const pmsURL = 'http://localhost:10015'; //hakya

export default function router(area) {
  //
  // 자율운영 페이지 route에서 지정, port 변경
  //
  const autoOperationRoutes = [
    new Route(area),
    {
      path: "/auto/:token?",
      name: "AutoMainDashBoard",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        const token = localStorage.getItem("token");
        const url = token
          ? `${autoURL}:${serverPort}/${token}`
          : `${autoURL}:${serverPort}`;
        window.location.href = url;
      },
      props: true,
    },
    {
      path: "/receivingAlgorithm",
      name: "receivingAlgorithm",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/receivingAlgorithm`;
      },
    },
    {
      path: "/coagulantsAlgorithm",
      name: "coagulantsAlgorithm",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/coagulantsAlgorithm`;
      },
    },
    {
      path: "/mixingAlgorithm",
      name: "mixingAlgorithm",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/mixingAlgorithm`;
      },
    },
    {
      path: "/sedimentationAlgorithm",
      name: "sedimentationAlgorithm",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/sedimentationAlgorithm`;
      },
    },
    {
      path: "/filterAlgorithm",
      name: "filterAlgorithm",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/filterAlgorithm`;
      },
    },
    {
      path: "/gacAlgorithm",
      name: "gacAlgorithm",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/gacAlgorithm`;
      },
    },
    {
      path: "/disinfectionAlgorithm",
      name: "disinfectionAlgorithm",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/disinfectionAlgorithm`;
      },
    },
    {
      path: "/ozoneAlgorithm",
      name: "ozoneAlgorithm",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/ozoneAlgorithm`;
      },
    },
    {
      path: "/alarmHistory/:token?",
      name: "alarmHistory",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        const token = localStorage.getItem("token");
        const url = token
          ? `${autoURL}:${serverPort}/${token}`
          : `${autoURL}:${serverPort}`;
        window.location.href = url;
      },
      props: true,
    },
    {
      path: "/aiHistory",
      name: "aiHistory",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/aiHistory`;
      },
    },
    {
      path: "/operationHistory",
      name: "operationHistory",
      beforeEnter: () => {
        const serverPort = getServerPort(area);
        window.location.href = `${autoURL}:${serverPort}/operationHistory`;
      },
    },
  ];

  const routes = [
    new Route(area),
    new drvnRoute(area),
    {
      path: "/EpaAnalysisMonitoring",
      name: "EpaAnalysisMonitoring",
      component: () => import("@/views/EpaAnalysis/EpaAnalysisMonitoring.vue"),
    },
    {
      path: "/EpaAnalysisSimulation",
      name: "EpaAnalysisSimulation",
      component: () => import("@/views/EpaAnalysis/EpaAnalysisSimulation.vue"),
    },
    {
      path: "/EMSPumpControl",
      name: "EMSPumpControl",
      component: () =>
        import("@/views/AiAnalysis/SongsuPumpCtr/PumpControl.vue"),
    },
    {
      path: "/PumpControlDetailed",
      name: "PumpControlDetailed",
      component: () =>
        import("@/views/AiAnalysis/SongsuPumpCtr/PumpControlDetailed.vue"),
    },
    {
      path: "/PumpControlTrand",
      name: "PumpControlTrand",
      component: () =>
        import("@/views/AiAnalysis/SongsuPumpCtr/PumpControlTrand.vue"),
    },
    {
      path: "/PumpHistory",
      name: "PumpHistory",
      component: () =>
        import("@/views/AiAnalysis/SongsuPumpCtr/PumpHistory.vue"),
    },
    {
      path: "/PumpControlHistory",
      name: "PumpControlHistory",
      component: () =>
        import("@/views/AiAnalysis/SongsuPumpCtr/PumpControlHistory.vue"),
    },
    {
      path: "/MajorDrainage",
      name: "MajorDrainage",
      component: () =>
        import("@/views/AiAnalysis/SongsuPumpCtr/MajorDrainage.vue"),
    },
    {
      path: "/PowerPeakAnalysis",
      name: "PowerPeakAnalysis",
      component: () =>
        import("@/views/AiAnalysis/PwrPeak/PowerPeakAnalysis.vue"),
    },
    {
      path: "/PowerPeakDetail",
      name: "PowerPeakDetail",
      component: () =>
        import("@/components/ComponentCommon/PowerPeakDetail.vue"),
    },
    {
      path: "/ZoneUse",
      name: "ZoneUse",
      component: () => import("@/views/EnergyUseStts/ZoneUse.vue"),
    },
    {
      path: "/FacUse",
      name: "FacUse",
      component: () => import("@/views/EnergyUseStts/FacUse.vue"),
    },
    {
      path: "/UseTrand",
      name: "UseTrand",
      component: () => import("@/views/EnergyUseStts/UseTrand.vue"),
    },
    {
      path: "/CostAnaylsis",
      name: "CostAnaylsis",
      component: () => import("@/views/EnergySavingMngmn/CostAnaylsis.vue"),
    },
    {
      path: "/ReductionTargetStatus",
      name: "ReductionTargetStatus",
      component: () => import("@/views/EnergySavingMngmn/ReductionTarget.vue"),
    },
    {
      path: "/TagInfo",
      name: "TagInfo",
      component: () => import("@/views/Setting/TagInfo.vue"),
    },
    {
      path: "/SongsuPumpOperation",
      name: "SongsuPumpOperation",
      component: () => {
        const songsuPumpUrl = getSounsuPumpUrl(area);
        return import(`@/views/Setting/${songsuPumpUrl}`);
      },
    },
    {
      path: "/EletricityPlan",
      name: "EletricityPlan",
      component: () => import("@/views/Setting/EletricityPlan.vue"),
    },
    {
      path: "/ReductionTarget",
      name: "ReductionTarget",
      component: () => import("@/views/Setting/ReductionTarget.vue"),
    },
    {
      path: "/TargetStategyPeak",
      name: "TargetStategyPeak",
      component: () =>
        import("@/components/ComponentCommon/PowerPeakDetail.vue"),
    },
    {
      path: "/DailyReport",
      name: "DailyReport",
      component: () => import("@/views/Report/DailyReport.vue"),
    },

    //
    // PMS 페이지로 넘어가도록 route에서 지정
    //

    {
      path: "/pms/:token?",
      name: "PMSMainDashBoard",
      beforeEnter: () => {
        const token = localStorage.getItem("token");
        const url = token ? `${pmsURL}/${token}` : `${pmsURL}`;
        window.location.href = url;
      },
      props: true,
    },
    {
      path: "/PMSPumpControl",
      name: "PMSPumpControl",
      beforeEnter: () => {
        window.location.href = `${pmsURL}/PumpControl`;
      },
    },
    {
      path: "/StatsHistory",
      name: "StatsHistory",
      beforeEnter: () => {
        window.location.href = `${pmsURL}/StatsHistory`;
      },
    },
    {
      path: "/PrecisionDiagnosis",
      name: "PrecisionDiagnosis",
      beforeEnter: () => {
        window.location.href = `${pmsURL}/PrecisionDiagnosis`;
      },
    },
    {
      path: "/PumpMonitoring",
      name: "PumpMonitoring",
      props: (route) => ({ alarmData: route.query.alarmData }),
      beforeEnter: () => {
        window.location.href = `${pmsURL}/PumpMonitoring`;
      },
    },
    {
      path: "/hakya",
      name: "Dashboard_H",
      beforeEnter: () => {
        window.location.href = `${pmsURL}/hakya`;
      },
    },

    ...autoOperationRoutes,
  ];

  // 위에서 정의한 getServerPort 함수 추가
  function getServerPort(area) {
    const validAreas = [
      "gosan",
      "gunsan",
      "sanseong",
      "buan",
      "gumi",
      "haepyeong",
      "hakya",
      "goryeong",
      "jain",
      "unmun",
    ];
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
  function getSounsuPumpUrl(area) {
    let returnUrl;
    if (area === "gosan") {
      returnUrl = "SongsuPumpOperationGosan.vue";
    } else {
      returnUrl = "SongsuPumpOperationGosan.vue";
    }

    return returnUrl;
  }

  const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes,
  });
  if (area === "gosan" || area === "gunsan" || area === "buan") {
    if (
      window.location.pathname.split("/").filter(Boolean).pop() === undefined &&
      (!localStorage.getItem("token") ||
        localStorage.getItem("token") === "undefined")
    ) {
      const serverPort = getServerPort(area);
      window.location.href = `${autoURL}:${serverPort}/login`;
    }
  }
  return router;
}
