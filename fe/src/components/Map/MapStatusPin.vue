<template>
  <div class="map-status-pin" :style="{ left: x + '%', top: y + '%' }">
    <div class="pin" :class="statusClass">
      <span class="label">{{ label }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: "MapStatusPin",
  props: {
    x: { type: Number, default: 50 },
    y: { type: Number, default: 50 },
    status: { type: String, default: "good" } // good | normal | bad
  },
  computed: {
    label() {
      if (this.status === "good") return "적합";
      if (this.status === "normal") return "적정";
      if (this.status === "bad") return "미흡";
      return "상태";
    },
    statusClass() {
      return {
        good: this.status === "good",
        normal: this.status === "normal",
        bad: this.status === "bad",
      };
    }
  }
};
</script>

<style scoped>
.map-status-pin {
  position: absolute;
  transform: translate(-50%, -100%); /* 핀 꼬리 기준 */
  z-index: 10;
  pointer-events: none; /* UI 전용 */
}

.pin {
  position: relative;
  width: 70px;  /* PNG 실제 크기에 맞게 조정 */
  height: 80px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pin.good {
  background-image: url("@/assets/img/pins/pin_good.png");
}
.pin.normal {
  background-image: url("@/assets/img/pins/pin_normal.png");
}
.pin.bad {
  background-image: url("@/assets/img/pins/pin_bad.png");
}

.label {
  position: absolute;
  top: 19px;
  font-size: 16px;
  font-weight: 700;
  color: #000;
  user-select: none;
}
</style>
