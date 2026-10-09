<template lang="">
    <div class="icon-area" v-on:click="clickParam(item, index+1)" :class="{
        error: this.error,
        none: this.none,
    }" :style="gumiIconArea">
        <div class="title-box">
            <img src="@/assets/circle.svg" alt="" />
            <div>{{ formattedText }}</div>
        </div>
        <img class="icon" src="@/assets/motor.png" :style="gumiIcon"/>
    </div>
</template>
<script>
import { useStore } from "vuex";
import { useRouter } from "vue-router";
export default {
    props: ['item', 'error', 'none', 'index','number'],
    computed: {
    formattedText() {
      // 데이터에 줄바꿈 문자를 추가하여 반환
      const store = useStore();
      const area = store.state.area;
      let text; 
      if (area == 'gosan') {
        text = this.item.substr(0, 3) + this.item.substr(8, 9) + Number(this.number)
      } else {
        text = this.item
      } 
      return text;
    }
},
    setup() {
        const store = useStore();
        const router = useRouter();
        const area = store.state.area
        let gumiIconArea, gumiIcon
        if (area === 'gumi') {
            gumiIconArea = 'width:300px; height:192px'
            gumiIcon = 'width:80%; height:80%'
        }
        else {
            gumiIconArea = ''
        }
        const clickParam = (value, idx) => {
            store.state.monitor1.selectModel = value
            if (area === "gosan") {
                if (idx > 7) {
                    store.state.monitor1.id = "motor_n_" + (idx - 7);
                }
                else {
                    store.state.monitor1.id = "motor_o_" + idx;
                }
                if (idx < 10) {
                    store.state.monitor1.scada_id = "pump_scada_0" + idx;
                } else {
                    store.state.monitor1.scada_id = "pump_scada_" + idx;
                }
            }
            else {
                store.state.monitor1.id = "motor_0" + idx;
                store.state.monitor1.scada_id = "pump_scada_0" + idx;
            }
            if (area == 'hakya') {
                store.state.monitor1.modelList[0].map((x) => (x.select = false));
                store.state.monitor1.modelList[0].filter((x) => {
                    if (x.id === store.state.monitor1.id) {
                        x.select = true;
                        return;
                    }
                });
            } else {
                if (idx <= 4) {
                    store.state.monitor1.modelList[0].map((x) => (x.select = false));
                    store.state.monitor1.modelList[0].filter((x) => {
                        if (x.id === store.state.monitor1.id) {
                            x.select = true;
                            return;
                        }
                    });
                }
                else {
                    store.state.monitor1.modelList[1].map((x) => (x.select = false));
                    store.state.monitor1.modelList[1].filter((x) => {
                        if (x.id === store.state.monitor1.id) {
                            x.select = true;
                            return;
                        }
                    });
                }
            }

            let alarmData = store.state.monitor1.id
            router.push({ name: "PumpMonitoring", query: { alarmData } });
        };
        return {
            clickParam,
            store,
            gumiIconArea,
            gumiIcon
        };
    }
}
</script>
<style lang="">
    
</style>