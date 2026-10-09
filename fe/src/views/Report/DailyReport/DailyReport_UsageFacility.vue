<template>
  <report-grid ref="reportGrid"></report-grid>
</template>

<script>
import ReportGrid from "@/components/Grid/ReportGrid.vue";
export default {
  components: {
    ReportGrid,
  },
  data() {
    return {
      code: [],

    };
  },
  mounted() { },
  methods: {
    export() {
      this.$refs.reportGrid.onExcelExport();
    },
    // selectClick(DayFrom){
    //  console.log("DayFrom"  + DayFrom);
    //   console.log("selectClick = " + this.search+this.search2,this.search3,this.search4,this.search5,this.search6, this.search7);
    // },
    addCommaNumber(number) {
      // 숫자를 문자열로 변환한 후, 3자리마다 콤마(,)를 추가합니다.
      return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },

    setGridRow(data) {
  const codeName = ["전일", "금일", "금월", "금년"];
  const rowData = [];

  for (let index = 0; index < data.data.length; index++) {
    const row = {};
    
    for (let j = 0; j < this.field.length; j++) {
      if (this.field[j].field == 'totalPower') {
        const totalPower = data.data[index].kwh_sum ? data.data[index].kwh_sum.toFixed(2) : "";
        row[this.field[j].field] = this.addCommaNumber(totalPower); // totalPower 값을 포맷팅하여 콤마 추가
      } else if (this.field[j].field == 'code') {
        row[this.field[j].field] = codeName[index];
      } else {
        const totalNumber = data.data[index][this.field[j].field] ? data.data[index][this.field[j].field] : '';
        row[this.field[j].field] = this.addCommaNumber(totalNumber)
      }
    }

    rowData.push(row);
  }

  this.$refs.reportGrid.setData(rowData);
},


    setGridFiled(data) {
      // console.log("자식 한테 받음");
      // console.log("setGridFiled = ", data);
      this.field = [
        { headerName: "구분", field: "code" , suppressMenu: true},
        { headerName: "총전력량", field: "totalPower" ,  suppressMenu: true},
      ];

      for (let index = 0; index < data.data.length; index++) {
        const item = data.data[index];
        this.field.push({
          headerName: item.zone_name,
          field: item.zone_code,
          suppressMenu: true
        });
      }
      // console.log("this.field UsageFacility", this.field);

      this.$refs.reportGrid.setField(this.field);
    },
  },
};
</script>
