<template>
  <div v-if="isAppReady" :class="{ page_bg: !changeClass, sub_page_bg: changeClass }">
    <HeaderBar @allPageAlarm="allPageAlarm" @testPopup="testPopup" />
    <!-- <MenuBar /> -->

    <MenuBar />
    <!-- <div class="drawer-handler">
        <div class="tri"></div>
      </div> -->

    <div class="container_layout">
      <router-view @onChangeBgClass="onChangeBgClass" />
    </div>
  </div>
  <OnOffAlarm v-if="OnOffEvent" ref="OnOffAlarm" :message1="this.message1" :message2="this.message2"
    :message3="this.message3" :message4="this.message4" :message5="this.message5" @closeBtn="closeBtn"
    @cancelBtn="cancelBtn" @testPopup="testPopup" :test="test" />
  <OnOffAlready v-if="AlreadyEvent" @closeAlready="closeAlready" />
  <!-- 군산 5분 제어 판단: AI 추천 모드 승인 팝업 (스스로 30초마다 조회) -->
  <CtrlCmdApprove v-if="isAppReady && $area === 'gunsan'" />
  <all-alarm v-if="alarmEvent" :abnormalAlarm="abnormalAlarm" @allPageAlarm="allPageAlarm"
    @allAlarmClose="allAlarmClose" @onlyColse="onlyColse" />

</template>

<script>
import HeaderBar from "@/views/Common/HeaderBar.vue";
import MenuBar from "@/views/Common/MenuBar.vue";
import AllAlarm from "./views/Common/AllAlarm.vue";
import OnOffAlarm from "@/views/Common/OnOffAlarm.vue";
import OnOffAlready from "@/views/Common/OnOffAlready.vue";
import CtrlCmdApprove from "@/views/Common/CtrlCmdApprove.vue";
import { fetchFunc } from "@/util/fetchFunc";
import { useStore } from "vuex";
export default {
  components: { HeaderBar, MenuBar, AllAlarm, OnOffAlarm, OnOffAlready, CtrlCmdApprove },
  data() {
    return {
      alarmEvent: false,
      changeClass: false,
      OnOffEvent: false,
      AlreadyEvent: false,
      abnormalAlarm: [],
      link: "",
      msg: "",
      ALR_ID: "",
      ALR_TYP: "",
      prevDatas: [],
      message1: '',
      message2: '',
      message3: '',
      message4: '',
      message5: '',
      store: useStore(),
      test: false,
      sunnamAllOff: false,
      grGongPri: '',
      isAppReady: false,
    };
  },
  mounted() {
    this.initApp();
    this.startInterval();

    // 기존 1분마다 실행되는 로직
    this.tokenInterval = setInterval(() => {
      this.allPageAlarm();
      // auth가 false일 때만 1분마다 refreshToken 실행
      if (localStorage.getItem('auth') === "true" && (this.$area === 'gosan' || this.$area === 'gunsan' || this.$area === 'buan' || this.$area === 'sanseong')) {
        this.refreshToken();
      }
    }, 1 * (1000 * 60));

    if (this.$area === 'gosan' || this.$area === 'gunsan' || this.$area === 'buan' || this.$area === 'sanseong') {
      this.getToken();
    }

    // auth가 true일 때 마우스 움직임 감지하여 1분에 한 번만 refreshToken 실행
    this.lastRefresh = 0;
    this.mouseMoveHandler = () => {
      if (localStorage.getItem('auth') === "false" && (this.$area === 'gosan' || this.$area === 'gunsan' || this.$area === 'buan'  || this.$area === 'sanseong')) {
        const now = Date.now();
        if (now - this.lastRefresh > 60 * 1000) {
          this.refreshToken();
          this.lastRefresh = now;
        }
      }
    };
    window.addEventListener('mousemove', this.mouseMoveHandler);
  },
  beforeUnmount() {
    clearInterval(this.tokenInterval);
    window.removeEventListener('mousemove', this.mouseMoveHandler);
  },
  methods: {
    async initApp() {
      await this.getToken(); // getToken이 완료될 때까지 기다립니다.
      this.isAppReady = true; // 로딩 완료
    },
    setDefaultUserInfo() {
      localStorage.removeItem('token');
      localStorage.setItem('user', 'defaultUser');
      localStorage.setItem('usrNm', 'KWATER');
      localStorage.setItem('usrPn', '');
      localStorage.setItem('usrTi', 0);
      localStorage.setItem('auth', false);
      localStorage.setItem('usrAuth', 0);
    },
    async getToken() {
      let res;
      const urlToken = window.location.pathname.split('/').filter(Boolean).pop();
      const storedToken = localStorage.getItem('token');
      const hasUrlToken = urlToken && urlToken !== 'undefined' && urlToken.split('.').length === 3;

      // URL에 토큰이 존재하면, localStorage에 기존 토큰이 있더라도 덮어씁니다.
      if (hasUrlToken) {
        try {
          res = await fetchFunc(`${this.$apiURL}/login/checkTkn?tkn=${urlToken}`);

          if (res?.accessToken) {
            localStorage.removeItem('token');
            localStorage.setItem('token', res.accessToken);

            const decodedToken = this.decodeJWT(res.accessToken);

            if (decodedToken) {
              localStorage.setItem('user', decodedToken.sub);
              localStorage.setItem('usrNm', decodedToken.usrNm);
              localStorage.setItem('usrPn', decodedToken.usrPn);
              localStorage.setItem('usrTi', decodedToken.usrTi);

              if (decodedToken.user_auth && decodedToken.user_auth[0].role == "0") {
                localStorage.setItem('auth', false);
                localStorage.setItem('usrAuth', 0);
              } else {
                localStorage.setItem('auth', true);
                localStorage.setItem('usrAuth', 1);
              }
            }
          }
        } catch (error) {
          console.error("Error fetching token from URL, setting default user info:", error);
          // 오류 발생 시 기본값 설정
          this.setDefaultUserInfo();
        }
        if (res?.error) {
          this.setDefaultUserInfo();
        }
      } else if (storedToken && storedToken !== 'undefined') {
        // URL에 토큰이 없고, localStorage에만 토큰이 있을 경우 갱신을 시도
        this.refreshToken();
      } else {
        // URL과 localStorage 모두에 토큰이 없는 경우 (최초 진입 등)
        console.warn("No token found. Setting default user info.");
        this.setDefaultUserInfo();
      }
    },
    async refreshToken() {
        let res;
        if (!localStorage.getItem('token') || localStorage.getItem('token') == 'undefined') {
          this.getToken();
        }
        else {
          res = await fetchFunc(`${this.$apiURL}/login/refreshTkn?tkn=${localStorage.getItem('token')}`);
          
          const decodedToken = this.decodeJWT(res?.accessToken); // 새로 추가된 정보를 디코딩

          if (decodedToken) { // 토큰이 유효할 경우
            localStorage.removeItem('token');
            localStorage.setItem('token', res?.accessToken);

            // 추가된 정보를 localStorage에 저장합니다.
            localStorage.setItem('user', decodedToken.sub); 
            localStorage.setItem('usrNm', decodedToken.usrNm); 
            localStorage.setItem('usrPn', decodedToken.usrPn); 
            localStorage.setItem('usrTi', decodedToken.usrTi); 

            // 권한 처리 로직은 그대로 유지
            if (decodedToken.user_auth[0].role == "0") {
              localStorage.setItem('auth', false);
            } else {
              localStorage.setItem('auth', true);
            }
          }
        }
    },
    onChangeBgClass(isChange) {
      this.changeClass = isChange;
    },
    decodeJWT(token) {
      // JWT는 헤더, 페이로드, 서명이 '.'으로 구분됨
      const base64Url = token.split('.')[1]; // 페이로드 부분 가져오기
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/'); // Base64 URL 디코딩
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(c =>
        '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      ).join(''));

      return JSON.parse(jsonPayload); // JSON 형식으로 변환하여 반환
    },
    // 알람 api
    async allPageAlarm(isModal) {
      const apiURL = this.$apiURL;
      if (!isModal) {
        let res = await fetch(`${apiURL}/alarm/getAlarmList`);
        let data = await res.json();
        if (data.data.length > 0) {
          this.alarmEvent = true;
          this.abnormalAlarm = data.data;
          // 덤프 데이터 없어서 임시로 넣음 테스트용
          // this.abnormalAlarm = [{MSG : '초과했다.', LINK : 'http://localhost:3000/PowerPeakAnalysis'}]
          this.ALR_ID = this.abnormalAlarm[0]?.ALR_ID;
          this.ALR_TYP = this.abnormalAlarm[0]?.ALR_TYP;
          this.msg = this.abnormalAlarm[0]?.MSG;
          this.link = this.abnormalAlarm[0]?.LINK;

          if (this.ALR_TYP == 'PUMP') {
            let audio
            if (this.$area === 'goryeong') {
              audio = new Audio(require('@/assets/trilla_02-89358.mp3'));
            }
            else {
              audio = new Audio(require('@/assets/pump_alarm_sound.mp3'));
            }
            audio.play();
          }

        } else {
          this.alarmEvent = false;
        }
      } else {
        // 확인 버튼 클릭하고 api 다시 호출 
        var myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");

        let params;
        if (this.ALR_TYP == 'PUMP') {
          params = { ALR_ID: this.ALR_ID }
        } else {
          params = { MSG: this.msg }
        }

        var requestOptions = {
          method: "POST",
          headers: myHeaders,
          body: JSON.stringify(params),
        };


        fetch(`${apiURL}/alarm/checkAlarm`, requestOptions)
          .then((response) => response.text());


        if (this.ALR_TYP == 'PEAK') {
          location.href = this.link;
          this.alarmEvent = false;
        } else {
          this.alarmEvent = false;
          // setInterval(() => {
          // }, 1 * (1000));
          this.allPageAlarm();
        }
        // setInterval(() => {
        //   this.allPageAlarm();
        // }, 1 * (1000 * 30));


      }
    },
    async changePumpOnOff() {
      let nowUseData = []//실측과 예측의 모터값이 달라지는 경우 체크하는 배열
      let nowHzData = []//실측과 예측의 주파수값이 달라지는 경우 체크하는 배열
      let nowPriData = []//실측과 예측의 압력값이 달라지는 경우 체크하는 배열
      let pumpStatusDatas = []//현재 펌프 상태를 저장하는 배열
      let sunnamData = []
      const funces = []

      funces.push(
        fetchFunc(`${this.$apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=1`),
        fetchFunc(`${this.$apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=2`),
        // fetchFunc(`${this.$apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=3`),
        // fetchFunc(`${this.$apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=4`),
        // fetchFunc(`${this.$apiURL}/ai/selectPumpPrdctOnOffStatus?pump_grp=5`),
      );
      let retData = await Promise.all(funces)
      const aiData = await fetchFunc(`${this.$apiURL}/ai/selectAiStatus`);
      const pumpList = await fetchFunc(`${this.$apiURL}/ai/selectPumpMaster`);
      this.grGoalPri = await fetchFunc(`${this.$apiURL}/dr/getGrLifePre`);

      retData.forEach((item) => {
        pumpStatusDatas = pumpStatusDatas.concat(item.data)
        sunnamData = sunnamData.concat(item.data?.filter(dataItem => dataItem.PUMP_GRP_NM === '선남가압장'))
        nowUseData = nowUseData.concat(item.data?.filter(dataItem => dataItem?.value !== dataItem?.nowUse))
        nowHzData = nowHzData.concat(item.data?.filter(dataItem => dataItem?.FREQ.toFixed(0) !== dataItem?.nowFreq.toFixed(0)))
        nowPriData = nowPriData.concat(item.data?.filter(dataItem => dataItem?.TUBE_PRSR_PRDCT.toFixed(1) !== dataItem?.nowPri.toFixed(1)))
      })
      sunnamData?.forEach(item => {
        if (item?.nowUse === "Off") this.sunnamAllOff = true
        else {
          this.sunnamAllOff = false
          return true
        }
      })

      this.errChecker(nowUseData, pumpList, nowHzData, nowPriData)



      this.$store.state.mode0 = aiData.data[0]?.AI_STATUS;
      this.$store.state.mode1 = aiData.data[1]?.AI_STATUS;
      this.$store.state.mode2 = aiData.data[2]?.AI_STATUS;
      this.$store.state.mode3 = aiData.data[3]?.AI_STATUS;
      this.$store.state.mode4 = aiData.data[4]?.AI_STATUS;
      this.prevDatas = pumpStatusDatas
    },
    async errChecker(nowUseData, pumpList, nowHzData, nowPriData) {
      // 군산: 5분 제어 판단이 펌프 제어를 넘겨받았으면 기존 조합 변경 팝업은 띄우지 않는다.
      // 서버가 기존 조합 생성을 쉬는 조건(PumpScheduler)과 같은 값을 본다.
      if (this.$area === 'gunsan') {
        try {
          const ctrl = (await fetchFunc(`${this.$apiURL}/ai/ctrl/pending`)).data;
          if (ctrl?.pumpControlActive) {
            this.OnOffEvent = false;
            return;
          }
        } catch (e) {
          // 조회 실패 시 기존 동작을 유지한다
        }
      }
      const res = (await fetchFunc(`${this.$apiURL}/ai/pumpCommandStatus`)).data;
      if (nowUseData.length > 0 || nowHzData.length > 0 || nowPriData.length > 0) {
        if (res?.isRunning == false && res?.data?.length > 0) {
          // console.log('pumpCommandStatus', res.data)
          const audio = new Audio(require('@/assets/pump_alarm_sound.mp3'));
          audio.play();
          this.test = false
          this.OnOffEvent = true;
          let msg = {};
          pumpList?.data?.forEach(element => {
            const errDatas = nowUseData.filter(useData => {
              if (useData.PUMP_GRP == element.PUMP_GRP) {
                if (!(useData.PUMP_GRP_NM == '선남가압장' && this.sunnamAllOff == true)) {
                  if (msg[element.PUMP_GRP] == undefined) msg[element.PUMP_GRP] = ``
                  msg[element.PUMP_GRP] += `${useData.PUMP_GRP_NM}${useData.PUMP_GRP_IDX}: ${"(" + useData.nowUse + ")"} -> ${useData.value}<br>`;
                  return true  
                }
              }
            });
            const errHzDatas = nowHzData.filter(hzData => {
              if (!(this.$area === 'goryeong' && (hzData.PUMP_IDX === 4 || hzData.PUMP_IDX === 7))) {
                if (hzData.nowUse === "On" && hzData.value === "On") {
                  if (hzData.PUMP_GRP == element.PUMP_GRP) {
                    if (msg[element.PUMP_GRP] == undefined) msg[element.PUMP_GRP] = ``
                    msg[element.PUMP_GRP] += `${hzData.PUMP_GRP_NM}${hzData.PUMP_GRP_IDX}: ${"(" + hzData.nowFreq.toFixed(0) + "Hz)"} -> ${hzData.FREQ.toFixed(0)}Hz<br>`;
                    return true
                  }
                }
              }
            });
            const errPriDatas = nowPriData.filter(priData => {
              if (this.$area === 'goryeong' && priData.PUMP_IDX === 4) {
                if (priData.nowUse === "On" && priData.value === "On" && Math.abs(priData.nowPri - priData.TUBE_PRSR_PRDCT) > 0.2) {
                  if (priData.PUMP_GRP == element.PUMP_GRP) {
                    if (msg[element.PUMP_GRP] == undefined) msg[element.PUMP_GRP] = ``
                    msg[element.PUMP_GRP] += `${priData.PUMP_GRP_NM}${priData.PUMP_GRP_IDX}: ${"(목표 설정값)"} -> ${this.grGoalPri?.data['780-344-PRC-4004']}kgf/c㎡<br>`;
                    // msg[element.PUMP_GRP] += `${priData.PUMP_GRP_NM}${priData.PUMP_GRP_IDX}: ${"(" + priData.nowPri.toFixed(1) + "kgf/c㎡)"} -> ${priData.TUBE_PRSR_PRDCT.toFixed(1)}kgf/c㎡<br>`;
                    return true
                  }
                }
              }
              else if (this.$area === 'goryeong' && priData.PUMP_IDX === 7) {
                if (priData.nowUse === "On" && priData.value === "On" && Math.abs(priData.nowPri - priData.TUBE_PRSR_PRDCT) > 0.2) {
                  if (priData.PUMP_GRP == element.PUMP_GRP) {
                    if (msg[element.PUMP_GRP] == undefined) msg[element.PUMP_GRP] = ``
                    msg[element.PUMP_GRP] += `${priData.PUMP_GRP_NM}${priData.PUMP_GRP_IDX}: ${"(" + priData.nowPri.toFixed(1) + "kgf/c㎡)"} -> ${priData.TUBE_PRSR_PRDCT.toFixed(1)}kgf/c㎡<br>`;
                    msg[element.PUMP_GRP] += `${priData.PUMP_GRP_NM}${priData.PUMP_GRP_IDX}: ${"(목표 설정값)"} -> ${this.grGoalPri?.data['780-344-PRC-6004']}kgf/c㎡<br>`;
                    return true
                  }
                }
              }
            });
            this['message' + element.PUMP_GRP] = [];
            // console.log('errDatas : ', errDatas)
            // console.log('errHzDatas : ', errHzDatas)
            // console.log('errPriDatas :', errPriDatas)
            if (errDatas.length > 0 || errHzDatas.length > 0 || errPriDatas.length > 0) {
              this['message' + element.PUMP_GRP].push(`${element.PUMP_GRP_NM.replace('정수지', '송수펌프')}`)
            }
            this['message' + element.PUMP_GRP].push(msg[element.PUMP_GRP])
          })
          this.AlreadyEvent = false
        }
        else if (res.isRunning === true || res.data?.length === 0) {

          this.OnOffEvent = false;
          this.AlreadyEvent = false;
        }
      }
    },
    //확인
    async closeBtn(pump_grp) {
     
      this.OnOffEvent = false

      alert('펌프 상태 변경 요청이 전송되었습니다.');
      if (this.$store.state.mode0 == 1 || this.$store.state.mode1 == 1 || this.$store.state.mode2 == 1 || this.$store.state.mode3 == 1 || this.$store.state.mode4 == 1) {
        const res = (await fetchFunc(`${this.$apiURL}/ai/pumpCommandStatus`)).data;
        if (res?.isRunning == false && res?.data?.length > 0) {
          try {
            const response = await fetchFunc(`${this.$apiURL}/ai/pumpCommand?pump_grp=${pump_grp}`);
            
            alert(response.data);
            // window.location.href = "/PumpDrvnAnly";
          } catch (error) {
            
            alert('API 호출 중 오류가 발생했습니다.');
          }
        }
        else {
          this.AlreadyEvent = true;
        }
      }
      else {
        this.OnOffEvent = false
      }
      // window.location.href = "/PumpDrvnAnly"
    },
    allAlarmClose() {
      const apiURL = this.$apiURL;
      var myHeaders = new Headers();
      myHeaders.append("Content-Type", "application/json");

      let params;
      if (this.ALR_TYP == 'PUMP') {
        params = { ALR_ID: this.ALR_ID }
      } else {
        params = { MSG: this.msg }
      }

      var requestOptions = {
        method: "POST",
        headers: myHeaders,
        body: JSON.stringify(params),
      };
     

      fetch(`${apiURL}/alarm/checkAlarm`, requestOptions)
        .then((response) => response.text());

      this.alarmEvent = false;

      setInterval(() => {
        this.allPageAlarm();
      }, 60 * (1000));
    },
    onlyColse() {
      this.alarmEvent = false;
    },
    //취소
    cancelBtn() {
      this.OnOffEvent = false
      // if (this.$store.state.mode0 == 1 || this.$store.state.mode1 == 1 || this.$store.state.mode2 == 1 || this.$store.state.mode3 == 1) {
      //   this.$refs.OnOffAlarm.changeMode()
      // }
      // else {
      // window.location.href = "/PumpDrvnAnly"
      // }
    },
    closeAlready() {
      this.AlreadyEvent = false
    },
    testPopup(state) {
      this.test = true
      this.OnOffEvent = state
    },
    async checkIsRunning() {
      const res = (await fetchFunc(`${this.$apiURL}/ai/pumpCommandStatus`)).data;
     
      return res.isRunning
    },
    startInterval() {
      let closetime = 5
      const now = new Date();
      const minutes = now.getMinutes();
      const seconds = now.getSeconds();
      const milliseconds = now.getMilliseconds();
      const nextRunInMinutes = 10 - (minutes % 10);
      const nextRunInMillis = (nextRunInMinutes * 60 * 1000) - (seconds * 1000) - milliseconds + 10000;

      setTimeout(async () => {
        await this.changePumpOnOff();

        setTimeout(async () => {
          if (await this.checkIsRunning() === false) {
            this.OnOffEvent = false;
          }
          if (
            (this.$store.state.mode0 === undefined || this.$store.state.mode0 == 2) &&
            (this.$store.state.mode1 === undefined || this.$store.state.mode1 == 2) &&
            (this.$store.state.mode2 === undefined || this.$store.state.mode2 == 2) &&
            (this.$store.state.mode3 === undefined || this.$store.state.mode3 == 2) &&
            (this.$store.state.mode4 === undefined || this.$store.state.mode4 == 2)
          ) {
            closetime = 1;
          }
          else {
            closetime = 5
          }
        }, closetime * 60 * 1000);

        setInterval(async () => {
          await this.changePumpOnOff();

          setTimeout(async () => {
            if (await this.checkIsRunning() === false) {
              this.OnOffEvent = false;
            }
            if (
              (this.$store.state.mode0 === undefined || this.$store.state.mode0 == 2) &&
              (this.$store.state.mode1 === undefined || this.$store.state.mode1 == 2) &&
              (this.$store.state.mode2 === undefined || this.$store.state.mode2 == 2) &&
              (this.$store.state.mode3 === undefined || this.$store.state.mode3 == 2) &&
              (this.$store.state.mode4 === undefined || this.$store.state.mode4 == 2)
            ) {
              closetime = 1;
            }
            else {
              closetime = 5
            }
          }, closetime * 60 * 1000);

        }, 10 * 60 * 1000); // 10분 10초 마다 changePumpOnOff 호출

      }, nextRunInMillis);
    }
  },
};
</script>

<style>
html {
  width: 100%;
  height: 100%;
}

.container_layout {
  width: 99%;
  height: 89%;
  margin: 10px;
}

/* .drawer-handler{
  display: flex;
    align-items: center;
    justify-content: center;
    position: absolute;
    top: 65px;
    right: -13px;
    width: 13px;
    height: 31px;
    background-size: 100%;
    background-repeat: no-repeat;
    background-color: #08214a;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    z-index: 100;
}
.drawer-handler .tri{
    width: 0;
    height: 0;
    border-top: 5px solid transparent;
    border-left: 5px solid #fff;
    border-bottom: 5px solid transparent;
} */
</style>
