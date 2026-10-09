<template>
  <b-col class="" :style="{ paddingLeft: '3rem',}">
    <SmallTitle :title="'시간별 부하설정'" />
    <b-row :style="{ height: 'calc(100% - 40px)', margin :'10px'}" v-if="this.isInit">
      <!-- 바깥쪽 v-for로 6개씩 묶기 -->
      <b-col  v-for="timeSession in 4" :key="timeSession" >
        <electricity_plan_time_option
        v-for="(item, index) in labels.slice((timeSession - 1) * 6, timeSession * 6)"
        :key="index"
        :label="item"
        :initData="{
          value: this.initData[index + (timeSession - 1) * 6],
          order: index + (timeSession - 1) * 6
        }"
        class="timeOption"
        :ref="'electricity_plan_time_option_' + index"
        @handleOptionsChange="handleOptionsChange"
        />
      </b-col>
    </b-row>
  </b-col>
</template>


<script>
import electricity_plan_time_option from "./ElectricityPlan_timeOption.vue"
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
export default {
  components: {
    electricity_plan_time_option,
    SmallTitle
  },
  data() {
    return {
      labels: [
        "00시~01시", "01시~02시", "02시~03시", "03시~04시", "04시~05시", "05시~06시",
        "06시~07시", "07시~08시", "08시~09시", "09시~10시", "10시~11시", "11시~12시",
        "12시~13시", "13시~14시", "14시~15시", "15시~16시", "16시~17시", "17시~18시",
        "18시~19시", "19시~20시", "20시~21시", "21시~22시", "22시~23시", "23시~24시",
      ],
      timezone: [],
      initData : [],
      isInit:false,
    };
  },
  updated() {
    this.getData();
    this.costSave();
  },
  mounted() {
    this.isInit = this.initData.length > 0 
  },
  methods: {
    paramMethod(){
      for (let i = 0; i < 1; i++) {
        this.$refs["electricity_plan_time_option_" + i][0].paramMethod();
      }
    },
    getData(selectSeasonLoad) {
      this.initData = selectSeasonLoad;
      this.isInit = this.initData.length > 0 
    },  
    handleOptionsChange(selectedOptions) {
      this.$emit('handleOptionsChange',selectedOptions )
    },
    
  },
};
</script>
<style scoped>
.timeOption{
  width: 100%;
  padding: 10px 0 0 0 ;
}
</style>
