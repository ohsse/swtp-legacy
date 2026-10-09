<template>
  <b-col class="div_border" :style="{ height: '570px', width: '400px' }">
    <SmallTitle :title="'월별'" />
    <b-list-group id="bigList" class="list-custom-group bigListFont bigListCont">
      <div v-for="(item, i) in 12" :key="i" class="container" :class="{ active: activeIndex === i }"
        @click="toggleActive(i, monthSeason[i + 1])">
        <p style="width:45px; margin: 0px 0px 0px 20px;">{{ `${i + 1}월` }}</p>
        <Multiselect :placeholder="monthSeason[i + 1]" :options="options"
          style="height: 36px;width: 150px; right:-30px;" @click="clickOption(i)" @change=changeSSN />
      </div>
    </b-list-group>
  </b-col>
</template>

<script>
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
import Multiselect from "@vueform/multiselect";
export default {
  components: { SmallTitle, Multiselect },
  props: ["result"],
  data() {
    return {
      activeIndex: new Date().getMonth(),
      options: [
        { label: "봄철", value: "봄철" },
        { label: "여름철", value: "여름철" },
        { label: "가을철", value: "가을철" },
        { label: "겨울철", value: "겨울철" },
      ],
      monthSeason: {},
      clickMonth: 0,
    }
  },
  mounted() {
  },
  updated() {
    this.toggleActive(this.activeIndex, this.result[this.activeIndex].SSN)
    this.seasonData();
  },
  methods: {
    seasonData() {
      for (let index = 0; index < this.result.length; index++) {
        let month = this.result[index].MNTH;
        month = month < 10 ? parseInt(month) : month
        const season = this.result[index].SSN;
        this.monthSeason[month] = season;
      }
    },
    toggleActive(index, ssn) {
      if (this.activeIndex !== index) {
        this.activeIndex = index; // 다른 항목 클릭 시만 활성화
      }
      this.$emit("getCostData", ssn)
    },
    changeSSN(options) {
      this.$emit("postMonthSSN", { month: this.clickMonth, options: options })
    },
    clickOption(options) {
      this.clickMonth = options
    },
  },
};
</script>
<style>
.container {
  display: inline-flex;
  margin-top: 7px;
}

.active {
  /* 여기에 활성화될 때의 스타일을 추가하세요 */
  background-color: rgba(27, 87, 227, 0.2);
}
</style>