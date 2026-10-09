<template>
  
  <calendar-box   @chartData="chartData" @getTankList="getTankList" ref="calendarBox" :tankListData="tankListData"/>

</template>

<script>
import CalendarBox from '@/components/ComponentCommon/CalendarBox.vue'
export default {
  components: { CalendarBox },
  data() {
    return {
      tankListData : undefined,
    }
  },
  methods: {
    chartData(dateFrom, dateTo, selected, tankNum) {
      this.$emit("selectDate",dateFrom , dateTo, selected, tankNum )
    },
    tankList(data){
      const tankList = new Object();
      for (let index = 0; index < data[0].length; index++) {
        tankList[data[0][index].TNK_GRP_NM] = data[0][index].TNK_GRP_IDX
      }
      this.tankListData = tankList
      // console.log("tankListData", this.tankListData);
    },
    getTankList(value){

      this.$emit("tnkGrpIdx", value);
    }
  },

}
</script>

<style>

</style>