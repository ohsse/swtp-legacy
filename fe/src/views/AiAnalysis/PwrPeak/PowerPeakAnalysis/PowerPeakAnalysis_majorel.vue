<template>
  <b-col xl="4">
    <b-row class="h-100 left_bg justify-content-md-center">
      <b-col md="9" class="mt-3" v-bind:style="{ height: '105px' }">
        <div class="d-flex flex-column align-items-center text_title_base">
          <div class="d-flex w-100 justify-content-center" v-bind:style="{ height: '40px', lineHeight: '40px' }">
            <span class="text_title_font">총 순시 전력</span>
          </div>
          <div class="d-flex justify-content-center" v-bind:style="{ height: '65px', lineHeight: '65px' }">
            <span id="allPWI" class="text_val_font">{{ sunsiPower }}</span>
            <span class="text_val_unit">kW</span>
          </div>
        </div>
      </b-col>
      <b-col md="9" class="mt-3">
        <b-row class="position-relative left_div_center">
          <!--b-col class="position-absolute top-50 start-0 translate-middle-y blinkingY_down p-0" id="blinkingY_down"></b-col-->
          <!--b-col class="position-absolute top-50 end-0 translate-middle-y blinkingY_up p-0" id="blinkingY_up"></b-col-->
          <div class="cal-title-font d-flex flex-column text-center" id="rolling">
            <span>전력 피크 예상 시간</span>
            <span v-bind:style="{ fontSize: '26px' }">{{ peakTime }}</span>
          </div>
        </b-row>
      </b-col>
      <b-col md="9" class="mb-3" v-bind:style="{ marginTop: '-20px' }">
        <div class="middle_title text-center my-1">
          <span class="text_title_font">목표 피크 전력</span>
        </div>
        <div class="middle_val input_box">
          <span id="목표피크전력" class="text_val_font">{{ targetPower }}</span><span class="text_val_unit">kW</span>
        </div>
      </b-col>
      <b-col md="9" class="mb-3" v-bind:style="{ height: '105px' }">
        <div class="d-flex flex-column align-items-center text_title_base">
          <div class="d-flex w-100 justify-content-center" v-bind:style="{ height: '40px', lineHeight: '40px' }">
            <span class="text_title_font">요금 적용 전력 피크</span>
          </div>
          <div class="d-flex justify-content-center" v-bind:style="{ height: '65px', lineHeight: '65px' }">
            <span id="allPWI" class="text_val_font">{{ costPower }}</span>
            <span class="text_val_unit">kW</span>
          </div>
        </div>
      </b-col>
    </b-row>
  </b-col>
</template>

<script>
export default {
  props: ['sunsiPower', 'targetPower', 'costPower'],
  data() {
    return {
      peakTime: "없음",
      baseUrl: process.env.VUE_APP_BASE_URL,
    };
  },
  // mounted() {
  //   console.log("this.sunsiPower", this.sunsiPower);
  // },
  // updated() {
  //   console.log("update", this.sunsiPower);
  // },
  methods: {
    peakTimeFunction(peakTime) {
      this.peakTime = peakTime;
    },

  },
};
</script>
