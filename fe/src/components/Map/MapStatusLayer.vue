<template>
  <!-- 부모 컨테이너는 position:relative 여야 합니다 -->
  <div class="map-status-layer">
    <div v-show="visible" class="popup-card plc-top" :style="{
      left: x + '%',
      top: y + '%',
      transform: 'translate(-50%, 0)'
    }" role="dialog" :aria-label="`${title} 상세정보`">
      <div class="popup-head">{{ title }}</div>

      <table class="popup-table" aria-describedby="측정/분석/오차/상태">
        <thead>
          <tr>
            <th class="cal-title-font">구분</th>
            <th class="cal-title-font">유량</th>
            <th class="cal-title-font">압력</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!isSimulation">
            <td class="cal-title-font">계측값</td>
            <td class="glow-num">{{ fmt(flow.measured) }}</td>
            <td class="glow-num">{{ fmt(pressure.measured) }}</td>
          </tr>
          <tr>
            <td class="cal-title-font">분석값</td>
            <td class="glow-num">{{ fmt(flow.analyzed) }}</td>
            <td class="glow-num">{{ fmt(pressure.analyzed) }}</td>
          </tr>
          <tr v-if="!isSimulation">
            <td class="cal-title-font">오차</td>
            <td class="glow-num">{{ fmt(flow.error, true) }}</td>
            <td class="glow-num">{{ fmt(pressure.error, true) }}</td>
          </tr>
          <tr v-if="!isSimulation">
            <td class="cal-title-font">상태</td>
            <td class="cal-title-font text-white">
              {{ stateLabel(flow.state) }}
            </td>
            <td class="cal-title-font text-white">
              {{ stateLabel(pressure.state) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>

export default {
  name: "MapStatusLayer",
  props: {
    /** 팝업 표시 여부 */
    visible: { type: Boolean, default: false },
    /** 팝업 좌표(부모의 % 기준) */
    x: { type: Number, default: 50 },
    y: { type: Number, default: 50 },
    /** 배지 아래로 내리는 오프셋(px) */
    offset: { type: Number, default: 14 },
    /** 팝업 타이틀 (예: 고산분기) */
    title: { type: String, default: "지점명" },
    /** 유량 데이터 */
    flow: {
      type: Object,
      default: () => ({
        measured: null, analyzed: null, error: null, state: "good",
      }),
    },
    /** 압력 데이터 */
    pressure: {
      type: Object,
      default: () => ({
        measured: null, analyzed: null, error: null, state: "good",
      }),
    },
    isSimulation: {
      type: Boolean,
      default: false,
    }
  },
  methods: {
    // MapStatusLayer.vue의 methods 안 fmt 함수 수정
    fmt(v, isRate = false) {
      if (v === null || v === undefined || v === "") return "-";

      // isRate가 true일 경우, 소수점을 유지한 채로 계산해야 합니다.
      if (isRate) {
        const num = Number(v);
        if (!Number.isFinite(num)) return "-"; // 유효하지 않은 숫자는 '-' 처리
        const percentage = num * 100;
        
        // 소수점 첫째 자리까지 계산
        const formatted = percentage.toFixed(1);
        if (Math.abs(v) == 1) return "-";
        // 소수점 이하가 0이면 정수부분만 표시
        return formatted.endsWith('.0') 
          ? Math.round(percentage) + "%" 
          : formatted + "%";
      }

      // isRate가 false인 경우 (기존 로직)
      const n = Number(v);
      if (!Number.isFinite(n)) return String(v);
      return Math.round(n).toLocaleString();
    },
    stateLabel(s) {
      if (s === "good") return "적합";
      if (s === "normal") return "적정";
      if (s === "bad") return "미흡";
      if (s === "none") return "-";
      return "상태";
    },
  },
};
</script>

<style scoped>
.map-status-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.popup-card {
  position: absolute;
  pointer-events: auto;
  width: 260px;
  color: #e9f1ff;
  background: #0D1930;
  box-shadow: 0 0 20px 0 #0D67F2 inset;
  backdrop-filter: blur(2px);
  z-index: 10;
  font-variant-numeric: tabular-nums;
}

.popup-head {
  background: #1A2C6A;
  font-size: 18px;
  text-align: center;
  padding: 8px 10px;
  margin-bottom: 10px;
  font-weight: 600;
  color: #fff;
  letter-spacing: .5px;
}

.popup-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.popup-table thead th {
  font-weight: 500;
  padding: 4px 0 6px;
  text-align: center;
}

.popup-table td {
  padding: 10px 2px;
  text-align: center;
}

.state-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  background: #2f6fff;
}

.state-dot[data-status="bad"] {
  background: #ff4d4f;
}

.state-dot[data-status="normal"] {
  background: #22bb66;
}

.glow-num {
  font-size: 18px;
  font-family: LAB디지털 !important;
  line-height: 1;
  color: #fff;
  font-weight: 400;
  letter-spacing: .06em;
  text-shadow: 0 0 8px rgba(144, 195, 255, .9), 0 0 18px rgba(144, 195, 255, .45), 0 0 32px rgba(144, 195, 255, .25);
}
</style>
