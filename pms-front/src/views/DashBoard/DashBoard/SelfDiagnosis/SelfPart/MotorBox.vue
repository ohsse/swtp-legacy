<template lang="">
  <div class="motor-box">
     <img v-if="!this.motorItem?.alarm" src="@/assets/motor.png" alt="" /> 
     <img v-else src="@/assets/motor-alert.png" alt="" class="alert-ani" /> 
    <div class="motor-value-area">
      <div class="group type1">
        <div class="val-icon"></div>
        <div class="val-line"></div>
        <div class="val-1">{{ this.motorItem?.pump_de_rms_amp }} rms</div>
        <div class="val-2">{{ this.motorItem?.brg_pump_de_temp }} °C</div>
      </div>
      <div class="group type2">
        <div class="val-icon"></div>
        <div class="val-line"></div>
        <div class="val-1">{{ this.motorItem?.pump_nde_rms_amp }} rms</div>
        <div class="val-2">{{ this.motorItem?.brg_pump_nde_temp }} °C</div>
      </div>
      <div class="group type3">
        <div class="val-icon"></div>
        <div class="val-line"></div>
        <div class="val-1">{{ this.motorItem?.motor_nde_rms_amp }} rms</div>
        <div class="val-2">{{ this.motorItem?.brg_motor_nde_temp }} °C</div>
      </div>
      <div class="group type4">
        <div class="val-icon"></div>
        <div class="val-line"></div>
        <div class="val-1">{{ this.motorItem?.motor_de_rms_amp }} rms</div>
        <div class="val-2">{{ this.motorItem?.brg_motor_de_temp }} °C</div>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  props: ["item"],
  components: {},
  data() {
    return {
      motorItem: [],
    };
  },
  mounted() {
    this.motorItem = this.item;
    console.log(this.motorItem)
  },
  methods: {
    changeMotorItem(data) {
      this.motorItem = data;
    },
  },
};
</script>
<style>
.dashboard-info-container .box2 .content3 .motor-box img.alert-ani {
  animation: alert-ani 1s infinite;
}

@keyframes alert-ani {
  from {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }

  to {
    opacity: 1;
  }
}
</style>
