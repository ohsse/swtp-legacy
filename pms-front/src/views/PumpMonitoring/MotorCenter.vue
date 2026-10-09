<template>
  <div class="inSection s-center">
    <!-- <div class="action-btn reset" v-on:click="selectReset()">reset</div> -->
    <div class="chart-box">
      <div class="titlebox">
        <img src="@/assets/monitor-centerTitle.svg" alt="" />
        <p v-if="findTitle">
          {{ findTitle }}
        </p>
        <p v-if="!findTitle && songsuTitle">
          송수펌프모터
          <!-- {{ setTitle(store.state.monitor1.selectModel) }} -->
        </p>
        <p v-if="!findTitle && !songsuTitle">
          가압펌프
          <!-- {{ setTitle(store.state.monitor1.selectModel) }} -->
        </p>
      </div>



        <!-- 동작중 아직 미완성 -->
        <!-- <div class="state-area" :style="gumiStateArea">
          <div class="alarm-icon" :class="{
              error: state.eq_on_type
          }" :style="gumiAlarmIcon">
              <img class="icon" src="@/assets/alarm.svg" />
          </div>
          <p>
              {{
                state.eq_on_type ? "동작중" : ""
              }}
          </p>
        </div> -->



      <img src="@/assets/light2.png" alt="" class="light" />
      <BoxFrame />

      <div class="motors">
        <div class="main-motor">
          <!-- <img v-if="alarmStatusImg?.doubleAlarm" src="@/assets/motor-alert.png" alt="" /> -->
          <img v-if="alarmStatusImg?.Alarm" src="@/assets/motor_alert.png" alt="" style="
          position: absolute;
      " />
          <img v-if="alarmStatusImg?.pump_impeller_alarm" src="@/assets/pumpImg/Pump_ImpellerDefect.png" alt="" style="
          position: absolute;
      " />
          <img v-if="alarmStatusImg?.pump_cavitation_alarm" src="@/assets/pumpImg/Pump_CavitationDefect.png" alt=""
            style="
          position: absolute;
      " />
          <img v-if="alarmStatusImg?.pumpMotor_misalignment_alarm" src="@/assets/motor-alert.png" alt="" style="
          position: absolute;
      " />
          <img v-if="alarmStatusImg?.pumpMotor_unbalance_alarm" src="@/assets/pumpImg/Motor_UnbalanceDefect.png" alt=""
            style="
            position: absolute;
        " />
          <img v-if="alarmStatusImg?.motor_rotor_alarm" src="@/assets/pumpImg/Motor_RotorDefect.png" alt="" style="
          position: absolute;
      " />
          <img v-if="alarmStatusImg?.motor_bearing_alarm" src="@/assets/pumpImg/Motor_LoadBearingDefect.png" alt=""
            style="
          position: absolute;
      " />
          <img v-if="alarmStatusImg?.motor_half_bearing_alarm" src="@/assets/pumpImg/Motor_Half-LoadBearingDefect.png"
            alt="" style="
            position: absolute;
        " />
          <img v-if="alarmStatusImg?.pump_bearing_alarm" src="@/assets/pumpImg/Pump_LoadBearingDefect.png" alt="" style="
          position: absolute;
      " />
          <img v-if="alarmStatusImg?.pump_half_bearing_alarm" src="@/assets/pumpImg/Pump_Half-LoadBearingDefect.png"
            alt="" style="
            position: absolute;
        " />
          <img v-if="!alarmStatusImg?.Alarm" src="@/assets/motor.png" alt="정상" />
        </div>

        <!-- <div v-if="findId" class="alert-motor">
          <img src="@/assets/alert4.png" alt="" />
        </div> -->

        <div class="select-motor" :style="areaStyle">
          <motor-component :modelList="item" :style="{ marginRight: '20px' }"
            v-for="(item, index) in store.state.monitor1.modelList" :key="item" :index="index" :setPumpImg="setPumpImg"
            :emitSelectedItem="emitSelectedItem" />

        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useStore } from "vuex";
import { reactive, ref } from "vue";
import BoxFrame from "@/components/component/BoxFrame.vue";
import MotorComponent from './MotorComponent.vue';
import axios from "axios";
export default {
  props: {
    getSelectedItem: {
      type: Function,
      required: true
    },
    alarmStatusImg: {
      type: Object,
    }
  },
  components: {
    BoxFrame,
    MotorComponent
  },
  data() {
    let songsuTitle = false;
    return {
      songsuTitle,
    }
  },
  mounted() {
    const store = useStore();
    this.area = store.state.area;
    if (this.area === 'gumi') {
      this.areaStyle = 'justify-content: space-evenly;'
      this.songsuTitle = true
    } else if (this.area === 'hakya') {
      this.areaStyle = 'justify-content: space-evenly;'
      this.songsuTitle = false
    } else {
      this.areaStyle = ''
      this.songsuTitle = true
    }
  },
  setup(props) {
    let findId = ref();
    let findTitle = ref(0);
    const store = useStore();
    const state = reactive({
      model: store.state.monitor1.selectModel,
      datePop: false,
      date: {
        from: "",
        to: "",
      },
      startStr: "",
      endStr: "",
      alert: false,
      eq_on_type: false 
    });
    const setPumpImg = (id) => {
      for (const motorGroup of store.state.monitor1.modelList) {
        const foundMotor = motorGroup.find(motor => motor.id === id);
        console.log(motorGroup)
        console.log(foundMotor)
        if (foundMotor) {
          findId.value = foundMotor.alarm;
          console.log(foundMotor)
          let arr = foundMotor.title.split(" ");
          findTitle.value = arr[0] + " " + arr[2];
          if (findTitle.value == '(신)송수펌프동 #1') {
            findTitle.value = '(신)송수펌프동 #8'
          } else if (findTitle.value == '(신)송수펌프동 #2') {
            findTitle.value = '(신)송수펌프동 #9'
          } else if (findTitle.value == '(신)송수펌프동 #3') {
            findTitle.value = '(신)송수펌프동 #10'
          } else if (findTitle.value == '(신)송수펌프동 #4') {
            findTitle.value = '(신)송수펌프동 #11'
          }
        }
      }
    }
    const setEqOn = (eq_type) => {
      state.eq_on_type = eq_type;
      console.log("eq_type", eq_type)
    }
    const setTitle = (val) => {
      // if (val) {
      //   let arr = val.split(" ");
      //   return arr[0] + " " + arr[2];
      // }
      return val
    };
    const selectReset = () => {
      store.state.monitor1.mode = false;
      axios.get(`http://${store.state.globalIp}/reset`);
      window.location.reload(true);
    };
    const emitSelectedItem = (num) => {
      props.getSelectedItem(num)
    };

    return {
      selectReset,
      store,
      state,
      setTitle,
      setPumpImg,
      findId,
      findTitle,
      emitSelectedItem,
      setEqOn
    }
  },
  methods: {
  }
}
</script>

<style>
.state-area {
  width: 75px;
  height: 123px;
  float: left;
  color: #fff;
  text-align: center;
  font-size: 12px;
  padding-top: 25px;
  margin-left: 900px;
  margin-right: 30px;
}
  .alarm-icon {
      width: 50px;
      height: 50px;
      border-radius: 50px;
      margin-left: 12px;
      background: linear-gradient(
          to right bottom,
          #0091f2,
          #001b87
      );
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 8px;
      box-shadow: 0 0 8px #4b8dff;

     
  }
  .icon {
    width: 40%;
}
  .alarm-icon.error {
      background: linear-gradient(
          to right bottom,
          #f20000,
          #870000
      );
      box-shadow: 0 0 8px #ff1616;
  }


</style>