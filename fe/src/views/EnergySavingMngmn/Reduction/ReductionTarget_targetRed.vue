<template>
  <b-col class="table_s">
    <subTitle :title="title"></subTitle>
    <table class="table table-borderless bottom_row1 mx-auto mb-0 table_bg" v-bind:style="{ width: '78%' }">
      <colgroup>
        <col width="55%">
        <col width="45%">
      </colgroup>
      <tbody>
        <row :item="targetPwr"></row>
        <row :item="usePwr"></row>
        <row :item="useCo2"></row>
        <row :item="useTargetCo2"></row>
      </tbody>
    </table>
    <div class="bottom_line_val">
      <div
        v-bind:style="{ color: 'white', textAlign: 'center', fontSize: '20px', fontWeight: 'bolder', fontFamily: 'KHNPHUotfR' }">
        CO2발생량&nbsp;
        <span id="useCo2_r">{{ this.useCo2.val }} kg</span>
        &nbsp;CO2절감량&nbsp;&nbsp;
        <span id="goalVSco2_r">{{ this.useTargetCo2.val }} kg</span>
      </div>
    </div>
  </b-col>
</template>

<script>
import row from "@/views/EnergySavingMngmn/TargetRedRow.vue"
import subTitle from "@/views/EnergySavingMngmn/BottomTitle.vue"
export default {
  components: {
    row,
    subTitle
  },
  props: {
    title: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      targetPwr: {
        text: "목표 전력 사용량",
        unit: "kWh",
        val: 0
      },
      usePwr: {
        text: "전력 사용량",
        unit: "kWh",
        val: 0
      },
      useCo2: {
        text: "CO2절감량",
        unit: "kg",
        val: 0
      },
      useTargetCo2: {
        text: "목표대비 CO2 절감량",
        unit: "kg",
        val: 0
      },
    }
  },
  methods: {
    makeTargetRed(useVal, targetVal, useCo2, useTargetCo2) {
      this.targetPwr.val = targetVal;
      this.usePwr.val = useVal;
      this.useCo2.val = useCo2;
      this.useTargetCo2.val = useTargetCo2;
    }
  }
}
</script>

<style scoped>
.table_bg {
  --bs-table-bg: none;
}

.bottom_line_val {
  width: 96%;
  position: absolute;
  bottom: 40px;
}

.table_s {
  background-image: url(@/assets/img/table_s.png);
  background-size: 100% 100%;
  height: 340px;
  width: 30.5%;
  margin: 5px 5px 0 0;
  padding: 0 10px 10px 10px;
  position: relative;
}

.table_s:last-child {
  margin-right: 0;
}

.bottom_title {
  width: 100%;
  height: 30%;
  font-size: 174%;
  color: white;
  text-align: center;
  line-height: 150px;
  font-family: 'KHNPHDRegular';
}
</style>