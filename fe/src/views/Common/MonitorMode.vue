<template>
  <div class="monitor-mode">
    <button
      class="mode-btn"
      :class="{ active: value === 'monitor' }" @click="setMode('monitor')"
    >
      모니터링
    </button>

    <button
      class="mode-btn"
      :class="{ active: value === 'simulation' }" @click="setMode('simulation')"
    >
      시뮬레이션
    </button>
  </div>
</template>

<script>
export default {
  name: "MonitorMode",
  props: {
    value: {
      type: String,
      default: ""
    }
  },
  // data, created, watch 모두 제거
  methods: {
    setMode(mode) {
      // 내부 상태를 변경할 필요 없이 바로 이벤트를 발생시킴
      this.$emit("input", mode);
      this.$emit("change", mode);

      if (mode === 'monitor') {
        this.$router.push('/EpaAnalysisMonitoring');
      } else if (mode === 'simulation') {
        this.$router.push('/EpaAnalysisSimulation');
      }
    }
  }
};
</script>

<style scoped>
.monitor-mode {
  display: flex;
  padding: 5px;
  align-items: center;
  gap: 6px;
  height: auto;
  border-radius: 20px;
  background: #334b70;
}

.mode-btn {
  background: #4B668D;
  color: #000;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: background 0.3s ease, color 0.3s ease;
}

.mode-btn:hover {
  background: #B4DFFA;
}

.mode-btn.active {
  background: #B4DFFA;
  color: #000;
}
</style>
