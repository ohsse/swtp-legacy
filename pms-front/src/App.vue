<template>
  <div :class="{ page_bg: !changeClass, 'sub_page_bg': changeClass }">
    <HeaderBar @allPageAlarm="allPageAlarm" />
    <!-- <MenuBar /> -->
    <MenuBar />
    .
    <allAlarm v-if="this.store.state.alarmEvent" :abnormalAlarm="abnormalAlarm" @modalEvent="modalEvent" />

    <router-view />
  </div>
</template>

<script>
import HeaderBar from "@/views/Common/HeaderBar.vue";
import MenuBar from "@/views/Common/MenuBar.vue";
import allAlarm from "@/components/component/AllAlarm.vue"
import { useStore } from "vuex";
import { fetchFunc } from "./util/fetchFunc";
export default {
  components: { HeaderBar, MenuBar, allAlarm },
  data() {
    const store = useStore();
    return {
      changeClass: false,
      alarmEvent: false,
      abnormalAlarm: [],
      store
    };
  },
  created() {
    this.setGlobalIP();
  },
  mounted() {
    this.store.state.alarmEvent = false
    // this.allPageAlarm()
    setInterval(() => {
      this.allPageAlarm();
      this.store.dispatch('dashboard/motorAlarm');
    }, (3 * 60 * 1000));
    this.getToken();
    setInterval(() => {
      this.refreshToken();
    }, 1 * (1000 * 60));
  },
  methods: {
    async getToken() {
      let res;
      if (!localStorage.getItem('token') || localStorage.getItem('token') == 'undefined') {
        //url에서 긁어오기
        res = await fetchFunc(`${this.store.state.globalIP}login/checkTkn?tkn=${window.location.pathname.split('/').filter(Boolean).pop()}`);
        localStorage.removeItem('token');
        localStorage.setItem('token', res?.accessToken);

        if (this.decodeJWT(res.accessToken).user_auth[0].role == "0") {
          localStorage.setItem('auth', false);
          localStorage.setItem('user', this.decodeJWT(res.accessToken).sub);
        } else {
          localStorage.setItem('user', this.decodeJWT(res.accessToken).sub);
          localStorage.setItem('auth', true);
        }
      }
      else {
        this.refreshToken();
      }

    },
    async refreshToken() {
      let res;
      if (!localStorage.getItem('token') || localStorage.getItem('token') == 'undefined') {
        this.getToken();
      }
      else {
        res = await fetchFunc(`${this.store.state.globalIP}login/refreshTkn?tkn=${localStorage.getItem('token')}`);
        localStorage.removeItem('token');
        localStorage.setItem('token', res?.accessToken);
        if (this.decodeJWT(res.accessToken).user_auth[0].role == "0") {
          localStorage.setItem('auth', false);
          localStorage.setItem('user', this.decodeJWT(res.accessToken).sub);
        }
        else {
          localStorage.setItem('auth', true);
          localStorage.setItem('user', this.decodeJWT(res.accessToken).sub);
        }
      }
    },
    setGlobalIP() {
      this.$store.dispatch('setGlobalIP');
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
    async allPageAlarm() {
      let res = await fetch(
        `${this.store.state.globalIP}/api/v1/main/motorAlarm`
      );
      let data = await res.json();
      this.abnormalAlarm = []
      console.log('data?.datas', data?.datas);
      if (Array.isArray(data?.datas) && data?.datas?.length > 0)
        data?.datas?.forEach((element) => {
          for (let i = 0; i < element.length; i++) {
            let obj = element[i];
            if (obj.Alarm) {
              this.store.state.alarmEvent = true,
                this.abnormalAlarm.push(obj);
            }
          }
        })

    },
    modalEvent() {
      this.store.state.alarmEvent = false
    }
  },
};
</script>

<style>
html {
  width: 100%;
  height: 100%;
}
</style>
