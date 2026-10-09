<template>
  <MotorTop />

  <div class="monitoring">
    <div class="content">
      <!-- 펌프현황 -->
      <div class="section s-top">
        <div class="inSection s-left">

          <MotorChartComponent title="펌프-부하/반부하 총진동량" :name1="['부하 총진동량', '반부하 총진동량']" :detailData="[
            store.state.monitor1.detailData.pump_de_rms_amp,
            store.state.monitor1.detailData.pump_nde_rms_amp,
          ]" :selectedItem="item" :yName="'rms(mm/s)'" :isPump="true" :fixY="5" :threshold="threshold"
            @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.pump_rms_alarm" />

          <MotorChartComponent title="펌프-부하/반부하 베어링 결함" :name1="['부하 베어링', '반부하 베어링']" :detailData="[
            store.state.monitor1.detailData.pump_de_amp,
            store.state.monitor1.detailData.pump_nde_amp,
          ]" :selectedItem="item" :yName="'건전성 인자'" :isPump="true" :fixY="2" :threshold="thresholdOne"
            @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.pump_bearing_alarm"
            :subAlarmStatus="store.state.monitor1.alarmList?.pump_half_bearing_alarm" />

          <MotorChartComponent title="펌프-임펠러 결함" :name1="['펌프 임펠러']" :detailData="[
            store.state.monitor1.detailData.pump_impeller_amp
          ]" :selectedItem="item" :yName="'건전성 인자'" :isPump="true" :fixY="99" :threshold="thresholOther"
            @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.pump_impeller_alarm" />

          <MotorChartComponent title="펌프-케비테이션 발생" :name1="['펌프 케비테이션']" :detailData="[
            store.state.monitor1.detailData.pump_cavatation_amp
          ]" :selectedItem="item" :yName="'건전성 인자'" :isPump="true" :fixY="2" :threshold="thresholOther"
            @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.pump_cavitation_alarm" />

        </div>

        <MotorCenter ref="MotorCenter" :getSelectedItem="getSelectedItem"
          :alarmStatusImg="store.state.monitor1.alarmList" />

        <div class="inSection s-right">

          <MotorChartComponent title="모터-부하/반부하 총진동량" :name1="['부하 총진동량', '반부하 총진동량']" :detailData="[
            store.state.monitor1.detailData.motor_de_rms_amp,
            store.state.monitor1.detailData.motor_nde_rms_amp,
          ]" :selectedItem="item" :yName="'rms(mm/s)'" :isPump="true" :fixY="5" :threshold="threshold"
            @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.motor_rms_alarm" />

          <MotorChartComponent title="모터-부하/반부하 베어링 결함" :name1="['부하 베어링', '반부하 베어링']" :detailData="[
            store.state.monitor1.detailData.motor_de_amp,
            store.state.monitor1.detailData.motor_nde_amp,
          ]" :selectedItem="item" :yName="'건전성 인자'" :isPump="true" :fixY="2" :threshold="thresholdOne"
            @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.motor_bearing_alarm"
            :subAlarmStatus="store.state.monitor1.alarmList?.motor_half_bearing_alarm" />

          <MotorChartComponent title="모터-회전자 결함" :name1="['모터 회전자']" :detailData="[
            store.state.monitor1.detailData.motor_rotor_amp
          ]" :selectedItem="item" :yName="'건전성 인자'" :isPump="true" :fixY="2" :threshold="thresholOther"
            @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.motor_rotor_alarm" />

          <MotorChartComponent title="모터-권선온도" :name1="['R','S','T']" :detailData="[
            store.state.monitor1.detailData.winding_tempR,
            store.state.monitor1.detailData.winding_tempS,
            store.state.monitor1.detailData.winding_tempT,
          ]" :selectedItem="item" :yName="'℃'" :isPump="true" :fixY="3" :threshold="winding_temp_thres"
            @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.winding_temp_alarm" />

        </div>
      </div>

      <!-- 알람현황 -->
      <div class="section s-bottom" style="height:260px">

        <MotorChartComponent title="펌프모터-축정렬 불량" :name1="['펌프모터 축정렬']" :detailData="[
          store.state.monitor1.detailData.motor_misalignment_amp,
        ]" :selectedItem="item" :yName="'건전성 인자'" :isPump="true" :fixY="2" :threshold="thresholdOne"
          @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.pumpMotor_misalignment_alarm" />

        <MotorChartComponent title="펌프모터-질량 불평형" :name1="['펌프모터 질량 불평형']" :detailData="[
          store.state.monitor1.detailData.motor_unbalance_amp
        ]" :selectedItem="item" :yName="'건전성 인자'" :isPump="true" :fixY="2" :threshold="thresholdOne"
          @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.pumpMotor_unbalance_alarm" />

        <MotorChartComponent title="펌프모터-베어링온도" :name1="['펌프 부하', '펌프 반부하', '모터 부하', '모터 반부하']" :detailData="[
          store.state.monitor1.detailData.P_DE_bearing_temp,
          store.state.monitor1.detailData.P_NDE_bearing_temp,
          store.state.monitor1.detailData.M_DE_bearing_temp,
          store.state.monitor1.detailData.M_NDE_bearing_temp
        ]" :selectedItem="item" :yName="'℃'" :isPump="true" :fixY="3" :threshold="bearing_temp_thres"
          @openModal="openModal" :alarmStatus="store.state.monitor1.alarmList?.pumpMotor_bearing_temp_alarm" />

      </div>
    </div>
  </div>
  <ModalComp ref="ModalComp" v-show="isModalOpen" @closeModal="closeModal"></ModalComp>
</template>

<script>
import { useStore } from "vuex";
import { computed, reactive, ref, onMounted, watch } from "vue";
// import { useRouter } from 'vue-router';
import MotorChartComponent from './PumpMonitoring/MotorChartComponent.vue';
import MotorCenter from './PumpMonitoring/MotorCenter.vue';
import MotorTop from './PumpMonitoring/MotorTop.vue';
import ModalComp from "@/components/component/ModalComp.vue";
export default {
  name: "PumpMonitoring",
  components: {
    MotorChartComponent,
    MotorCenter,
    MotorTop,
    ModalComp
  },
  props: {
    alarmData: String // 또는 다른 타입으로 설정하세요.
  },
  setup(props) {
    const threshold = [
      { "koTitle": '주의', "value": 4.2 },
      { "koTitle": '경고', "value": 6.1 },
      { "koTitle": '결함', "value": 9.5 },
    ]

    const thresholdOne = [
      {"koTitle": '', "value": '' },
      { "koTitle": '경고', "value": 0.8 },
      { "koTitle": '결함', "value": 1 },
    ]

    const thresholOther = [
      {"koTitle": '', "value": '' },
      { "koTitle": '', "value": '' },
      { "koTitle": '결함', "value": 1 },
    ]

    const winding_temp_thres = [{ "koTitle": '', "value": '' },{ "koTitle": '', "value": '' },{ "koTitle": '임계선 130', "value": 130 }]
    const bearing_temp_thres = [{ "koTitle": '', "value": '' },{ "koTitle": '', "value": '' },{ "koTitle": '임계선 80', "value": 80 }]

    const pumpAmp = computed(() => {
      const modelList = store.state.monitor1.modelList;
      if (modelList.length > 0 && modelList[0].length > 0) {
        const filteredData = modelList[0][0].threshold.filter((item) => {
          // return (item.eq_type === 'pump' && (item.graph_type === 'de_rms_amp' || item.graph_type === 'nde_rms_amp'));
          if (item.eq_type === 'pump') {
            if (item.graph_type === 'de_rms_amp') {
              item.koTitle = '부하 베어링'
            }
            if (item.graph_type === 'nde_rms_amp') {
              item.koTitle = '반부하 베어링'
            }
            return item.koTitle !== undefined
          }

        });
        return filteredData;
      }
      return [];
    });

    const motorAmp = computed(() => {
      const modelList = store.state.monitor1.modelList;
      if (modelList.length > 0 && modelList[0].length > 0) {
        const filteredData = modelList[0][0].threshold.filter((item) => {
          // return (item.eq_type === 'pump' && (item.graph_type === 'de_rms_amp' || item.graph_type === 'nde_rms_amp'));
          if (item.eq_type == 'motor') {
            if (item.graph_type == 'de_rms_amp') {
              item.koTitle = '부하 베어링'
            }
            if (item.graph_type == 'nde_rms_amp') {
              item.koTitle = '반부하 베어링'
            }
            return item.koTitle !== undefined
          }

        });
        return filteredData;
      }
      return [];
    });


    const MotorCenter = ref(null);
    let item = ref('')
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
      flag: true,
    });
    onMounted(() => {
      todayDate();
      state.flag = true
      store.state.monitor1.id = props.alarmData
      store.dispatch("monitor1/getPumpList", props.alarmData)
        .then(() => {
          changeSelect();
        })
      // store.dispatch('monitor1/alarm', { parameterName: props.alarmData})
      store.dispatch('monitor1/alarm', { parameterName: props.alarmData, motorParams: { id: store.state.monitor1.id, endDate: new Date(new Date(store.state.monitor1.pickDate.to).getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ").split(' ')[0], startDate: new Date(new Date(store.state.monitor1.pickDate.from).getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ").split(' ')[0] } });
    });
    watch(() => store.state.monitor1.modelList, function () {
      store.dispatch('monitor1/bearingTempInfo');
      if (state.flag) {
        item.value = props.alarmData;
      }
      // store.dispatch('monitor1/alarm', { parameterName: props.alarmData})
      store.dispatch('monitor1/alarm', { parameterName: props.alarmData, motorParams: { id: store.state.monitor1.id, endDate: new Date(new Date(store.state.monitor1.pickDate.to).getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ").split(' ')[0], startDate: new Date(new Date(store.state.monitor1.pickDate.from).getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ").split(' ')[0] } });
    });
    watch(() => store.state.monitor1.alarmFlag, function () {
      store.state.monitor1.alarmData?.forEach(alarmElement => {
        alarmElement.forEach(alarmItem => {
          store.state.monitor1.modelList.forEach(element => {
            element.forEach(item => {
              if (item.id === alarmItem.motor_id)
                item.alarm = alarmItem.Alarm
              if (item.select == true) {
                store.state.monitor1.id = item.id
              }
            })
          });
        })
      });
      changeSelect()
    })
    const getSelectedItem = (alarm) => {
      console.log("getSelectedItem", alarm)
      item.value = alarm
      // store.dispatch('monitor1/alarm', { parameterName: props.alarmData})
      store.dispatch('monitor1/alarm', { parameterName: alarm, motorParams: { id: store.state.monitor1.id, endDate: new Date(new Date(store.state.monitor1.pickDate.to).getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ").split(' ')[0], startDate: new Date(new Date(store.state.monitor1.pickDate.from).getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ").split(' ')[0] } });
    };
    const todayDate = () => {
      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
      store.state.monitor1.pickDate.from = oneWeekAgo.toISOString().split("T")[0]
      store.state.monitor1.pickDate.to = new Date().toISOString().split("T")[0]
    };
    const changeSelect = () => {
      let selectedId = props.alarmData
      if (props.alarmData != undefined && state.flag) {
        state.flag = false
        store.state.monitor1.modelList.forEach(element => {
          element.map((x) => (x.select = false));
        });
        console.log("changeSelect", selectedId)
        console.log(store.state.monitor1.modelList)
        store.state.monitor1.modelList.forEach(element => {
          element.forEach(item => {
            console.log("item",item)
            if (item.id == selectedId) {
              item.select = true
              MotorCenter.value.setPumpImg(selectedId)
              MotorCenter.value.setEqOn(item.eq_on)
            }
          })
        });
      }
    }

    return {
      store,
      state,
      getSelectedItem,
      item,
      MotorCenter,
      pumpAmp, motorAmp, threshold, thresholdOne,thresholOther,
      winding_temp_thres, bearing_temp_thres
    };
  },
  data() {
    return {
      isModalOpen: false
    }
  },
  mounted() {
    setInterval(() => {
      location.reload(); // 페이지를 새로고침
    }, 60 * 60 * 1000);
  },
  methods: {
    openModal(dataAll, title) {
      console.log(title)
      this.isModalOpen = true;
      this.$refs.ModalComp.createChart(dataAll, title)
    },
    closeModal() {
      this.isModalOpen = false;
    },
  }
};
</script>

<style></style>
