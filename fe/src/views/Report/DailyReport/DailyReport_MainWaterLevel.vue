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
    let selectZoneList = []
    return {
      selectZoneList
    }
  },
  updated() {
    this.initData();
  },
  methods: {
    setGridFiled(data) {

      data.data.sort((a, b) => a.TNK_GRP_IDX - b.TNK_GRP_IDX);

      const selectedTNK_GRP_IDX = new Set();
      const filteredData = [];

      for (const item of data.data) {
        if (selectedTNK_GRP_IDX.size >= 5 && !selectedTNK_GRP_IDX.has(item.TNK_GRP_IDX)) {
          break;
        }

        if (item.TNK_IDX === 1 || item.TNK_IDX === 2) {
          selectedTNK_GRP_IDX.add(item.TNK_GRP_IDX);
          filteredData.push(item);
        }
      }
      // console.log("filteredData = " , filteredData);

      this.field = [
        { headerName: "구분", field: "code", suppressMenu: true },
      ];
      const tnkGrpNmSet = new Set();
      // const codeName = ['최대','최소','평균'];
      for (let index = 0; index < filteredData.length; index++) {
        const item = filteredData[index];
        // console.log("item === " , item);


        if (!tnkGrpNmSet.has(item.TNK_GRP_NM)) { // 중복을 허용하지 않는 Set에 추가
          tnkGrpNmSet.add(item.TNK_GRP_NM);


          this.field.push({
            headerName: item.TNK_GRP_NM,
            children: [
              { headerName: '1지', field: 'one_ji' + '_' + index, width: 90, suppressMenu: true },
              { headerName: '2지', field: 'two_ji' + '_' + index, width: 90,  suppressMenu: true},
            ]
          },
          );

        }
        this.rowData = [
          {
            code: '최대', one_ji_0: filteredData[0].max_value.toFixed(2), two_ji_0: filteredData[1].max_value.toFixed(2),
            one_ji_2: filteredData[2].max_value.toFixed(2), two_ji_2: filteredData[3].max_value.toFixed(2),
            one_ji_4: filteredData[4].max_value.toFixed(2), two_ji_4: filteredData[5].max_value.toFixed(2),
            one_ji_6: filteredData[6].max_value.toFixed(2), two_ji_6: filteredData[7].max_value.toFixed(2),
            one_ji_8: filteredData[8].max_value.toFixed(2), two_ji_8: filteredData[9].max_value.toFixed(2)
          },
          {
            code: '최소', one_ji_0: filteredData[0].min_value.toFixed(2), two_ji_0: filteredData[1].min_value.toFixed(2),
            one_ji_2: filteredData[2].min_value.toFixed(2), two_ji_2: filteredData[3].min_value.toFixed(2),
            one_ji_4: filteredData[4].min_value.toFixed(2), two_ji_4: filteredData[5].min_value.toFixed(2),
            one_ji_6: filteredData[6].min_value.toFixed(2), two_ji_6: filteredData[7].min_value.toFixed(2),
            one_ji_8: filteredData[8].min_value.toFixed(2), two_ji_8: filteredData[9].min_value.toFixed(2)
          },
          {
            code: '평균', one_ji_0: filteredData[0].avg_value.toFixed(2), two_ji_0: filteredData[1].avg_value.toFixed(2),
            one_ji_2: filteredData[2].avg_value.toFixed(2), two_ji_2: filteredData[3].avg_value.toFixed(2),
            one_ji_4: filteredData[4].avg_value.toFixed(2), two_ji_4: filteredData[5].avg_value.toFixed(2),
            one_ji_6: filteredData[6].avg_value.toFixed(2), two_ji_6: filteredData[7].avg_value.toFixed(2),
            one_ji_8: filteredData[8].avg_value.toFixed(2), two_ji_8: filteredData[9].avg_value.toFixed(2)
          },
        ];

        this.$refs.reportGrid.setData(this.rowData)

        this.$refs.reportGrid.setField(this.field)
      }


      // const element = this.selectZoneList[index];
      // if (element.TNK_IDX == '1' || element.TNK_IDX == '2') {
      //   console.log("1지, 2지 표 되는거임 ", element);
      //   console.log("elemet1 max",element.max_value);


    }

  }



}
</script>