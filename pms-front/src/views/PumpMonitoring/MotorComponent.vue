<template>
  <div class="motor-box" v-for="motor in modelList" :key="motor.id" @click="selectedMotor(motor.id)"
    :style="motor.id === 'motor_04' ? { marginRight: 3 + 'px' } : {}">
    <div class="motor-img" :class="{
      selected: motor.select,
      error: motor.alarm,
    }">
      <!-- <div class="action-btn" v-on:click="select(motor.idx + 1)"
        :style="motor.visible ? { visibility: 'visible' } : {}">
        {{ motor.idx + 1 }}
      </div> -->
      <img src="@/assets/motor.png" alt="" />
    </div>
    <div class="motor-name" :class="{ selectName: motor.select }">
      {{ setTitle(motor.title, motor.scada_id) }}
    </div>
  </div>

  <MotorModal v-if="state.alert" @modalClick="modalClick" />
</template>


<script>
import { useStore } from "vuex";
import { reactive, onMounted } from "vue";
import MotorModal from './MotorModal.vue';

export default {
  components: { MotorModal },
  props: {
    modelList: {
      type: Array,
      required: true
    },
    index: {
      type: Number,
      required: true
    },
    setPumpImg: {
      type: Function,
      required: true
    },
    emitSelectedItem: {
      type: Function,
      required: true
    },
  },
  setup(props) {
    const store = useStore();
    let modalChange = false;
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
    });
    onMounted(() => {
    })
    // console.log(store.state.monitor1.modelList)
    const modalClick = () => {
      state.alert = false
    }

    const setTitle = (val, val2) => {
      let area = store.state.area;
      if(area == 'gosan'){
        let arr = val.substr(0,3);
        let arr2 = val.substr(8,9);
        let text = Number(val2.slice(-2));
        return arr + arr2 + text;
      } else {
        return val
      }
     
    };
    //테스트 소스
    const select = (idx) => {
      store.state.monitor1.mode = true;
      let val = idx <= 7 ? idx - 1 : idx - 8;
      store.state.monitor1.sampleData.idx = val;
      store.state.monitor1.modelList[props.index][val].alarm = true;
      store.dispatch("monitor1/alarm");
      if (store.state.monitor1.mode) {
        setTimeout(() => {
          state.alert = true;
        }, 3000);
      }

      props.setPumpImg(store.state.monitor1.modelList[props.index][val].id)
    };
    //테스트 소스 끝
    const selectedMotor = (num) => {
      let select
      store.state.monitor1.modelList.forEach(item => {
        item.forEach(element => {
          if (element.id == num) {
            select = element
          }
        })
      })
      store.state.monitor1.selectModel = select.title;
      const scada_id = num.replace("motor", "pump_scada");
      store.state.monitor1.scada_id = scada_id
      store.state.monitor1.id = num
      store.state.monitor1.modelList.forEach(element => {
        element.map((x) => (x.select = false));
      });
      store.state.monitor1.modelList[props.index].filter((x) => {
        if (x.id === num) {
          x.select = true;
          return;
        }
      });
      let temp = JSON.parse(JSON.stringify(store.state.monitor1.modelList))
      store.state.monitor1.modelList = temp
      props.setPumpImg(num)
      props.emitSelectedItem(num)
    };
    const selectModel = (value) => {
      let select = store.state.monitor1.modelList.filter(
        (v) => v.title === value
      );
      store.state.monitor1.selectedMotor = select[0].title;
      store.state.monitor1.id = select[0].id;
      store.state.monitor1.scada_id = select[0].id;
    };
    return {
      store,
      selectedMotor,
      state,
      setTitle,
      select,
      selectModel,
      alert,
      modalChange,
      modalClick
    };
  },
};
</script>

<style></style>
