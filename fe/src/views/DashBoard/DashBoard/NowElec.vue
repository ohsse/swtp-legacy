<!--http://localhost:8080/selectNowElec-->
<!-- NowElec.vue -->
<!--
<template>
  <div>
    <h1>에너지 절감 현황</h1>
    <p>현재 전기 사용량: {{ nowElec }}</p>
    <p>절약된 전기 비용:</p>
    <ul>
      <li v-for="data in nowElec.data4" :key="data.ts">
        <div class="saving-cost-item">
          <span class="saving-cost-item-date">{{ data.ts }}</span>
          <span class="saving-cost-item-kwh">{{ data.savingKwh }} kWh</span>
          <span class="saving-cost-item-won">{{ data.savingCost }} 원</span>
        </div>
      </li>
    </ul>
  </div>
</template>-->

<template>
  <div>
  </div>
</template>
<script>
import { mapGetters } from "vuex";

export default {
  computed: {
    ...mapGetters(["dashboard/getNowElec"]),
    nowElec() {
      return this["dashboard/getNowElec"];
    },
    data4() {
      return this["dashboard/getData4"];
    },
  },
  mounted() {
    this.$store.dispatch("dashboard/fetchNowElec");
  },
};
</script>

<style>
.saving-cost-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.saving-cost-item-date {
  font-size: 14px;
  font-weight: bold;
}

.saving-cost-item-kwh {
  font-size: 12px;
}

.saving-cost-item-won {
  font-size: 16px;
  font-weight: bold;
  color: red;
}
</style>