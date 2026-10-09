<template>
  <report-grid ref="reportGrid"></report-grid>
</template>

<script>
import ReportGrid from '@/components/Grid/ReportGrid.vue';
export default {
  components: {
    ReportGrid,
  },
  data() {

    return {
    }
  },
  mounted() {
    this.setGridFiled();
    // this.initData();
  },
  updated() {
    // this.initData();
  },
  methods: {
    setGridFiled(value) {
      this.filed = [
        {
          headerName: '구분',
          field: 'code',
          cellEditor: 'agSelectCellEditor',
          cellEditorParams: { values: value },
          flex: 1,
          lockPosition: true,
          suppressMenu: true 
        },
        {
          headerName: '시간대 전력사용량(kWh)',
          children: [
            { headerName: '경부하', field: 'l_kwh', width: 90, filter: 'agTextColumnFilter' , suppressMenu: true  },
            { headerName: '중간부하', field: 'm_kwh', width: 90, filter: 'agNumberColumnFilter' , suppressMenu: true},
            { headerName: '최대부하', field: 'h_kwh', width: 90, suppressMenu: true },
          ]
        },
        {
          headerName: '시간대 전력사용량(%)',
          children: [
            { headerName: '경부하', field: 'l_kwh_p', width: 90, suppressMenu: true},
            { headerName: '중간부하', field: 'm_kwh_p', width: 90,suppressMenu: true },
            { headerName: '최대부하', field: 'h_kwh_p', width: 90, suppressMenu: true},
          ]
        },
        {
          headerName: '에너지 절감량(kWh)',
          field: 'savingKwh',
          suppressMenu: true
        },
        {
          headerName: '탄소절감량(tCO2)',
          field: 'savingCo2',
          suppressMenu: true
        },

      ]

      this.$refs.reportGrid.setField(this.filed)
    },
   
    initData(data) {
      
     

    
      const codeName = ['전일', '금일', '금월', '금년'];

      const rowData = data.data.map((item, index) => ({
        code: codeName[index] || 'No Data',
        l_kwh: this.addCommaNumber(item.l_kwh) || 'No Data',
        m_kwh: this.addCommaNumber(item.m_kwh) || 'No Data',
        h_kwh: this.addCommaNumber(item.h_kwh) || 'No Data',
        l_kwh_p: this.addCommaNumber(item.l_kwh_p) || 'No Data',
        m_kwh_p: this.addCommaNumber(item.m_kwh_p) || 'No Data',
        h_kwh_p: this.addCommaNumber(item.h_kwh_p) || 'No Data',
        savingKwh: this.addCommaNumber(item.savingKwh) || 'No Data',
        savingCo2: this.addCommaNumber(item.savingCo2) || 'No Data', 
      }));


   

      this.$refs.reportGrid.setData(rowData)
    },
    addCommaNumber(number) {

      // Check if the number is defined before calling toString()
      if (number !== undefined && number !== null) {
        // Convert the number to a string, add commas, and limit to two decimal places
        return parseFloat(number).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      } else {
        // Handle the case where the number is undefined or null
        return ""; // or any default value you want
      }
    }

 
  },
}

</script>