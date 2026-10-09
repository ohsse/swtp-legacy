<template>
  <div class="chart-box" :class="{
    error: alarmStatus || subAlarmStatus,
  }">
    <Frame />
    <Linechart :title="title" :name1="name1" :detailData="detailData" :yName="yName" :isPump="isPump" :threshold="threshold" :fixY="fixY"
     @showModal="showModal"/>
  </div>
</template>

<script>
import Frame from "@/components/component/BoxFrame.vue";
import Linechart from "@/components/chart/monitoring/Linechart_d.vue";
import { useStore } from "vuex";
import { reactive, ref, watchEffect } from "vue";
export default {
  props: ["title", "detailData", "name1", 'selectedItem', 'yName','alarmStatus','subAlarmStatus', 'isPump', 'threshold', 'fixY'],
  components: {
    Frame,
    Linechart,
  },
  setup(props) {
    let findItem = ref()
    const store = useStore();
    let TITLE = reactive({
      name: "",
    });
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
    watchEffect(() => {
      for (const motorGroup of store.state.monitor1.modelList) {
        const foundMotor = motorGroup.find((motor) => motor.id === props.selectedItem);
        if (foundMotor) {
          findItem.value = foundMotor.alarm;
        }
      }
    });

    return {
      store,
      state,
      TITLE,
      findItem,
    };
  },
  methods: {
    showModal(dataAll) {
      this.$emit('openModal', dataAll, this.title)
    },
  }
};

</script>

<style></style>
