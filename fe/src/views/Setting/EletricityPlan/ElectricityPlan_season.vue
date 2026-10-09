<template>
  <b-col class="div_border" :style="{ height: '250px', width: '400px' }">
    <SmallTitle :title="'계절별'" />
    <b-list-group id="bigList" class="list-custom-group bigListFont bigListCont">
      <div :class="{ active: currentSeason === '봄철' }" class="seasonCss">봄</div>
      <div :class="{ active: currentSeason === '여름철' }" class="seasonCss">여름</div>
      <div :class="{ active: currentSeason === '가을철' }" class="seasonCss">가을</div>
      <div :class="{ active: currentSeason === '겨울철' }" class="seasonCss">겨울</div>
    </b-list-group>
  </b-col>
</template>

<script>
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
export default {
  components: { SmallTitle },
  props: ['initSSN'],
  data() {
    return {
      currentSeason: ''
    }
  },
  mounted() {
    this.updateSeason();
  },
  updated() {
    this.currentSeason = this.initSSN
  },
  methods: {
    sendSeasonEvent(season) {
      this.currentSeason = season; // 현재 선택된 계절을 업데이트
      const message = season + "철";
      this.$emit("getCostData", message);
    },
    updateSeason(season) {
      this.currentSeason = season;
    }
  },
}

</script>
<style>
.seasonCss {
  height: 50px !important;
  display: flex;
  justify-content: center;
  align-items: center;
}

.active {
  background-color: rgba(27, 87, 227, 0.2);
}
</style>