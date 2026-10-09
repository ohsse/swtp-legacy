<template>
  <b-col xl="3" class="d-flex align-items-stretch">
    <!-- 각 ElectricityPan_timeBox 컴포넌트에 개별적인 timeZone을 전달 -->
    <ElectricityPan_timeBox 
      :label="label"
      :initData="this.initData"
      @handleOptionsChange="handleOptionsChange"
      ref="ElectricityPan_timeBox"
    />
  </b-col>
</template>

<script>
import ElectricityPan_timeBox from "./ElectricityPan_timeBox.vue";
export default {
  components: {
    ElectricityPan_timeBox
  },
  props: ['initData','label'],
  data() {
    return {
      timeZone: null, // 각 컴포넌트에 전달할 timeZone 변수
      index: 0,
    };
  },
  created() {
  },
  mounted() {
    // console.log("this.initData_timeOption", this.initData);
  },
  methods: {
    paramMethod(){
    
      this.$refs.ElectricityPan_timeBox.paramMethod();
    },
    // upData(data){
    //   this.$emit("upData", data);
    // },
    handleOptionsChange(selectedOptions) {
      this.$emit('handleOptionsChange',selectedOptions )
    },
  },
};
</script>

<style>

</style>
