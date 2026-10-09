<template>
  <report-grid ref="reportGrid"></report-grid>
</template>

<script>
import ReportGrid from "@/components/Grid/ReportGrid.vue";
export default {
  components: {
    ReportGrid,
  },
  methods: {
    addCommaNumber(number) {
      // 숫자를 문자열로 변환한 후, 3자리마다 콤마(,)를 추가합니다.
      return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },
    setGridRow(data) {
      const codeName = [
        "일누계(전력사용량)",
        "일누계(비율)",
        "월누계(전력사용량)",
        "월누계(비율)",
        "연누계(전력사용량)",
        "연누계(비율)",
      ];
      const rowData = [];

      for (let index = 0; index < data.data.length; index++) {
        const row = {};
        let keysCount = Object.keys(data.data[0]).length;
        for (let j = 0; j < keysCount; j++) {
          const keysArray = Object.keys(data.data[0]);
          const firstKey = keysArray[j];  
          if (firstKey == 'pwr_sum') {
            const totalPower = data.data[index][firstKey] ? data.data[index][firstKey] : "";
            row[keysArray[j]] = this.addCommaNumber(totalPower); // totalPower 값을 포맷팅하여 콤마 추가
          } else if(firstKey == 'frq_value'){
            const frqValue = data.data[index][firstKey] ? data.data[index][firstKey] : "";
            row[keysArray[j]] = this.addCommaNumber(frqValue); // totalPower 값을 포맷팅하여 콤마 추가
          } else if(firstKey == 'basic_unit'){
            const basicUnit = data.data[index][firstKey] ? data.data[index][firstKey] : "";
            row[keysArray[j]] = this.addCommaNumber(basicUnit); // totalPower 값을 포맷팅하여 콤마 추가
           } else if(firstKey == 'type'){
              if(data.data[index][firstKey] == 'pwr_kwh_day'){
                row['code'] = codeName[0]
              } else if(data.data[index][firstKey] == 'ctr_rate_day'){
                row['code'] = codeName[1]
              } else if(data.data[index][firstKey] == 'pwr_kwh_month'){
                row['code'] = codeName[2]
              } else if(data.data[index][firstKey] == 'ctr_rate_month'){
                row['code'] = codeName[3]
              } else if(data.data[index][firstKey] == 'pwr_kwh_year'){
                row['code'] = codeName[4]
              } else if(data.data[index][firstKey] == 'ctr_kwh_year'){
                row['code'] = codeName[5]
              }
           } 
           else {
            const totalNumber =  data.data[index][firstKey] ?  data.data[index][firstKey] : '';
            row[keysArray[j]] = this.addCommaNumber(totalNumber)
          }
        }
        rowData.push(row);
      }


      this.$refs.reportGrid.setData(rowData);
    },
    setGridFiled(data) {
      const uniquePumpGrpNames = new Set();
      const pumpGrpIdxMapping = new Map();

      for (const item of data.data) {
        const pumpGrpName = item.PUMP_GRP_NM;

        if (!uniquePumpGrpNames.has(pumpGrpName)) {
          uniquePumpGrpNames.add(pumpGrpName);
          const pumpGrpIdx = item.PUMP_GRP;
          pumpGrpIdxMapping.set(pumpGrpName, pumpGrpIdx);
        }
      }

      const newData = {};

      for (const item of data.data) {
        const pumpGrpName = item.PUMP_GRP_NM;
        const tnkGrpIdxKey =
          item.TNK_GRP_IDX === 1 ? "TNK_GRP_IDX_1" : "TNK_GRP_IDX_2";

        if (!newData[pumpGrpName]) {
          newData[pumpGrpName] = {};
        }

        if (!newData[pumpGrpName][tnkGrpIdxKey]) {
          newData[pumpGrpName][tnkGrpIdxKey] = [];
        }

        newData[pumpGrpName][tnkGrpIdxKey].push(item);
      }

      // PUMP_IDX로 정렬된 데이터로 newData 업데이트
      for (const pumpGrpName in newData) {
        for (const tnkGrpIdxKey in newData[pumpGrpName]) {
          newData[pumpGrpName][tnkGrpIdxKey].sort(
            (a, b) => a.PUMP_IDX - b.PUMP_IDX
          );
        }
      }

      this.filed = [
        {
          headerName: "구분",
          field: "code",
          suppressMenu: true
        },
      ];

      for (const pumpGrpName in newData) {
        const children = [];

        for (const tnkGrpIdxKey in newData[pumpGrpName]) {
          const tnkGrpIdx = newData[pumpGrpName][tnkGrpIdxKey];

          for (let i = 0; i < tnkGrpIdx.length; i++) {
            const item = tnkGrpIdx[i];
            const pumpIdx = item.PUMP_IDX;
            children.push({
              headerName: `${pumpIdx}지`,
              field: `pump_${pumpIdx}`,
              width: 90,
              suppressMenu: true
            });
          }
        }
        this.filed.push({
          headerName: pumpGrpName + " 송수펌프 전력사용량(kWh)",
          children: children,
        });
      }

      this.filed.push(
        {
          headerName: "유효합계(kwh)",
          field: "pwr_sum",
          suppressMenu: true
        },
        {
          headerName: "용수공급량(m3)",
          field: "frq_value",
          suppressMenu: true
        },
        {
          headerName: "원단위(kwh/m3)",
          field: "basic_unit",
          suppressMenu: true
        }
      );
      this.$refs.reportGrid.setField(this.filed);
    },
  },
};
</script>
