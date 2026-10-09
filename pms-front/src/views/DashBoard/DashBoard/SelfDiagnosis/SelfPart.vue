<template>
  <div class="dashboard-info-container">
    <div class="content-box box2">
      <div class="titleBox">
        <div class="title2">자율진단</div>
        <img src="@/assets/img/small_light.png" alt="전등 이미지">
      </div>
      <div class="content3">
        <div class="list-box">
          <PumpTab ref="FirSuji" :data="store.state.dashboard.motorInfo[0]" :item="firSuji" @clickFirSuji="clickFirSuji"
            @clickSecSuji="clickSecSuji" :id="0" />
          <PumpTab v-if="store.state.dashboard.motorInfo[1]" ref="SecSuji" :data="store.state.dashboard.motorInfo[1]"
            :item="secSuji" @clickSecSuji="clickSecSuji" :id="1" />
        </div>
        <MotorBox ref="MotorBox" :item="store.state.dashboard.motorInfo" />
      </div>
    </div>
  </div>
</template>

<script>
import MotorBox from '@/views/DashBoard/DashBoard/SelfDiagnosis/SelfPart/MotorBox.vue'
import PumpTab from '@/views/DashBoard/DashBoard/SelfDiagnosis/SelfPart/PumpTab.vue'
import { useStore } from 'vuex';
import { onMounted, watch } from "vue";
export default {
  components: {
    MotorBox,
    PumpTab,
  },

  setup() {
    const store = useStore();
    onMounted(() => {
      store.state.dashboard.motorInfoSelect = false
      store.dispatch('dashboard/getPumpList');
    });
    watch(() => store.state.dashboard.motorInfoSelect, function () {
      store.dispatch('dashboard/motorAlarm');
      store.dispatch('dashboard/motorDataAll');
      store.dispatch('dashboard/pumpBearingAll');
    });
    return { store };
  },
  data() {
    return {
      firSuji: { name: '' },
      secSuji: { name: '(신)송수펌프동' },
    }
  },
  mounted() {
    this.namechange();
    this.$refs.FirSuji.changeSelectedItem(0)
    this.setMotorItem(0, 0)
  },
  updated() {
    this.setMotorItem(0, 0)
  },
  methods: {
    namechange() {
      const store = useStore();
      const area = store.state.area;
      if (area == 'gosan') {
        this.firSuji.name = '(구)송수펌프동'
      } else if (area == 'gumi') {
        this.firSuji.name = '신평(생활)계통'
      } else if (area == 'hakya') {
        this.firSuji.name = '임하가압장'
      }
    },
    clickFirSuji(index = 0) {
      if (this.$refs.FirSuji) {
        this.$refs.FirSuji.changeSelectedItem(index)
        this.setMotorItem(index, 0)
      }
      if (this.$refs.SecSuji) {
        this.$refs.SecSuji.changeSelectedItem(null)
      }

    },
    clickSecSuji(index = 0) {
      if (this.$refs.SecSuji) {
        this.$refs.SecSuji.changeSelectedItem(index)
        this.setMotorItem(index, 1)
      }
      if (this.$refs.FirSuji) {
        this.$refs.FirSuji.changeSelectedItem(null)
      }
    },
    setMotorItem(index, id) {
      if (this.store.state.dashboard.motorInfo.length > 0) {
        this.$refs.MotorBox.changeMotorItem(this.store.state.dashboard.motorInfo[id][index])
      }
    },

  }
}
</script>

<style></style>