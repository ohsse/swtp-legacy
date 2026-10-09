<template>
  <report-grid ref="reportGrid"></report-grid>
  </template>

<script>
import ReportGrid from '@/components/Grid/ReportGrid.vue';
export default{
  components : {
    ReportGrid,
  },
  data() {   
  
    return {
    }
  },
  mounted() {

    this.setGridFiled();
    // this.setGridRow();
  },
  methods: {
    export(){
      this.$refs.reportGrid.exportToCsv();
    },
    // selectClick(DayFrom){
    //  console.log("DayFrom"  + DayFrom);
    //   console.log("selectClick = " + this.search+this.search2,this.search3,this.search4,this.search5,this.search6, this.search7);
    // },
    setGridRow(data){
      const rowData = [];

      for (let index = 0; index < data.data.length; index++) {
        const item = data.data[index];
        rowData.push({
          code: item.ts,
          PRDCT_PWR: item.PRDCT_PWR,
          GNRTD_PWR: item.GNRTD_PWR,
          USE_PWR: item.USE_PWR,
        });
      }
      this.$refs.reportGrid.setData(rowData)
    },
    setGridFiled() {
      this.filed = [
        {
          headerName: '구분',
          field: 'code',
          suppressMenu: true 
        },
      {
          headerName: '예상전력',
          field: 'PRDCT_PWR',
          suppressMenu: true 
        },
        {
          headerName: '발생전력',
          field: 'GNRTD_PWR',
          suppressMenu: true 
        },
        {
          headerName: '사용량',
          field: 'USE_PWR',
          suppressMenu: true 
        },
       
      ]

      this.$refs.reportGrid.setField(this.filed)
    },
  },
}

</script>