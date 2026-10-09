<template>
  <b-col class="bottomContentsImg">
    <b-form-group
      label-cols="4"
      label-cols-lg="5"
      label-size="sm"
      :label="label"
      label-for="input-sm"
      class="comboFont text-center mx-auto mt-2"
    >
      <Multiselect  :placeholder="selectedValue" :options="options" @change="handleOptionsChange"/>
    </b-form-group>
  </b-col>
</template>

<script>
import Multiselect from "@vueform/multiselect";
export default {
  components: {
    Multiselect,
  },
  props: ['label', 'initData'],
  data() {
    return {
      result: [],
      selectedValue: '',
      options: [
        { label: "경부하", value: "L" },
        { label: "중부하", value: "M" },
        { label: "최대부하", value: "H" },
      ],
      rateIdx: 9,
      timeZone : '',
      allData: [],
    };
  },
  created() {
  },
  mounted() {
    this.getData222();
  },
  updated() {
    this.getData222();
  },

  methods: {  
    paramMethod(){

    },
    getData222() {
      this.timeZone = this.initData.value.TIMEZONE
      
      if(this.timeZone == 'L'){
        this.selectedValue = '경부하'
      } else if(this.timeZone == 'M'){
        this.selectedValue = '중부하'
      }else{
        this.selectedValue = '최대부하'
      }

    },
    handleOptionsChange(selectedOptions) {
      this.$emit('handleOptionsChange',{ options: selectedOptions, index: this.initData.order });
    },
    
  },
};
</script>

<style>
.multiselect-clear-icon {
  display: none !important;
}
</style>
