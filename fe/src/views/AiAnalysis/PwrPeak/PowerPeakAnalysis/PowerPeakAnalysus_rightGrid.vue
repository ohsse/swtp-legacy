<template>
  <b-col xl="6">
    <small-title :title="title"></small-title>
    <div class="p-3" v-bind:style="{ height: '400px' }">
      <b-tabs class="custom-tabs"> </b-tabs>
      <span v-for="item in zone" :key="item.pump_grp">
        <input :class="['input', (selectedTabIndex === item.pump_grp) ? 'selected-input' : '']" :value="item.zone"
          type="button" @click="handleButtonClick(item.pump_grp)" />
      </span>
      <AreaChart ref="AreaChart" />
    </div>
  </b-col>
</template>

<script>
import AreaChart from "@/components/Chart/AreaChart.vue";
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
import ChartLineClass from "@/components/Chart/ChartLineClass";

export default {
  components: { SmallTitle, AreaChart },

  data() {
    return {
      title: "용수수요예측 펌프사용 전력량 예측",
      param: "pyung_tap",
      loaded: false,
      zone: [],
      zoneNumber: 0,
      selectedTabIndex: 0,
    };
  },

  // name:'',
  mounted() {
    this.$nextTick(async () => {
      await this.zoneTabSelect();
      this.tapData();
    });
  },

  methods: {
    handleButtonClick(index) {


      // 버튼을 클릭했을 때 호출되는 함수로, 여기서 index 값을 사용할 수 있습니다.
      this.selectedTabIndex = index; // 선택된 탭의 인덱스 저장
      this.zoneNumber = index; // 예시로 index에 1을 더한 값으로 변경하도록 함

      this.tapData();
    },
    /**
     * this.zoneNumber가 고정값이 아니게 되어 기본값 0만 아니면 로직 실행
     */
    async tapData() {
      // let _this = this;
      const apiURL = this.$apiURL;
      let res;
      let dataX = [];
      let dataY = [];

      if (this.zoneNumber != 0) {
        res = await fetch(`${apiURL}/ai/pumpGrpSelect?pump_grp=${this.zoneNumber}`);

        this.data = await res.json();
        this.data.data.data.forEach((data1) => {
          dataX.push(data1["PRDCT_TIME"]);
          dataY.push(data1["PWR_PRDCT"]);
        });
      }
      let chartClass = new ChartLineClass(
        dataX,
        [dataY],
        ["전력량 예측값"],
        null,
        "날짜",
        "kWh"
      )
      chartClass.newFunction([dataY]);
      chartClass.setGridSize('5%', '10%', '15%', '10%')
      this.$refs.AreaChart.changeData(
        chartClass
      );
    },

    /**
     * API selectCTR_PRF_PUMPMST_INF => pumpUsageList 로 변경
     * 예측데이터가 있는 펌프 그룹 및 그룹 DCS를 가져옴
     * 탭 만드는 리스트를 단일 String 배열(그룹명)이 아닌 Object로 변경(그룹명, 그룹 id)
     */
    async zoneTabSelect() {
      // let _this = this;
      const apiURL = this.$apiURL;
      // let res = await fetch(`${apiURL}/st/selectCTR_PRF_PUMPMST_INF`);
      let res = await fetch(`${apiURL}/ai/pumpUsageList`);
      let data = await res.json();
      if (data !== null) {
        const uniqueItems = new Set();
        for (let i = 0; i < data.data.length; i++) {
          // const item = data.data[i]["PUMP_NM"].substring(0, 6);
          // const item = data.data[i]["PUMP_GRP_DSC"]
          // api 최초 호출 및 탭 index를 위한 할당
          if (i == 0) {
            this.zoneNumber = data.data[i]["PUMP_GRP"];
            this.selectedTabIndex = data.data[i]["PUMP_GRP"];
          }
          const item = {};
          item['zone'] = data.data[i]["PUMP_GRP_DSC"];
          item['pump_grp'] = data.data[i]["PUMP_GRP"];
          uniqueItems.add(item);
        }
        this.zone = Array.from(uniqueItems);
      }
    },
  },
};
</script>
<style>
.input {
  background: url(@/assets/img/pump/disable_false.png);
  background-size: 100% 100%;
  border: 2px #135096;
  border-radius: 2px 15px 0 0;
  color: #000000;
  width: 80px;
  height: 25px;
  margin-right: 1px;
  mix-blend-mode: color-dodge;
  font-size: 12px;
}

.selected-input {
  color: #fff;
}
</style>
