<template>
  <ag-grid-vue class="ag-theme-alpine-dark" style="width: 100%; height: 100%;" :columnDefs="columnDefs" :rowData="rowData"
    :defaultColDef="defaultColDef" rowSelection="multiple" animateRows="true" :stopEditingWhenCellsLoseFocus="true"
    @cell-clicked="cellWasClicked" @grid-ready="onGridReady" @cell-value-changed="onCellValueChanged" ref="agGrid">
  </ag-grid-vue>
</template>
  
<script>
import { AgGridVue } from "ag-grid-vue3";  // the AG Grid Vue Component
import { ref, onBeforeMount } from "vue";

import "ag-grid-community/styles/ag-grid.css"; // Core grid CSS, always needed
import "ag-grid-community/styles/ag-theme-alpine.css"; // Optional theme CSS


export default {
  components: {
    AgGridVue,
  },
  data() {
    return {
      columnDefs: [],
      rowData: [],
      editedData: []
    }
  },
  setup() {
    const gridApi = ref(null); // Optional - for accessing Grid's API
    const gridColumnApi = ref();
    const rowHeight = ref(null);
    // Obtain API from grid's onGridReady event
    const onGridReady = (params) => {
      gridApi.value = params.api;
      gridColumnApi.value = params.columnApi;
    };
    onBeforeMount(() => {
      rowHeight.value = 120;
    });
    const defaultColDef = ref({
      sortable: true,
      filter: true,
      flex: 1,
      resizable: false,
      editable: true,
      // cellStyle: { 'white-space': 'normal', 'word-wrap': 'break-word'},
      // headerStyle :{ 'text-align': 'center' },
      cellClass: 'centered-checkbox',
    })


    return {
      gridApi,
      onGridReady,
      rowHeight,
      gridColumnApi,
      defaultColDef,
      
    };
  },
  methods: {
    setField(filed) {
      this.columnDefs = filed
    },
    setData(rowData) {
      this.rowData = rowData
    },
    /**
     * 셀 내용 편집시 작동하는 함수,
     * 설벼 명 변경시 설비코드 포함 여부 판단 및 저장될 배열에 저장
     * @param {*} params 
     */
    onCellValueChanged(params) {
      const { data, colDef, newValue, rowIndex } = params;
      if (colDef.field == "FAC_NAME") {
        const fac_cd = `(${data.FAC_CODE})`;
        if (!data.FAC_NAME || !data.FAC_NAME.includes(fac_cd)) {
          alert(`설비명에는 설비코드 '${fac_cd}'가 포함되어야 합니다.`);
          this.facNameEditCheck(rowIndex, `${data.FAC_NAME}${fac_cd}`);

        }
      }
      this.editedData.push({
        data: data,
        field: colDef.field,
        value: newValue
      });


    },
    /**
     * 저장 버튼 클릭시 update emit 발동
     */
    onUpdateData() {
      if (Array.isArray(this.editedData) && this.editedData.length === 0) {
        alert('수정된 데이터가 없습니다.')
        return false
      } else {
        const updatedData = [];
        this.editedData.forEach((item) => {
          updatedData.push(item.data);

        });

        this.editedData = []; // 기존 업데이트 배열 초기화

        this.$emit("getUpdateData", updatedData)
      }
    },
    /**
     * 설비명에 설비코드 미포함시 발동하는 함수 강제적으로 (설비코드) 삽입
     * @param {*} row 
     * @param {*} value 
     */
    facNameEditCheck(row, value) {
      // this.gridApi.setFocusedCell(0, "FAC_NAME", undefined);
      this.rowData[row]["FAC_NAME"] = value
      this.gridApi.applyTransaction({ update: [this.rowData[row]] })
      this.gridApi.startEditingCell({
        rowIndex: parseInt(row),
        colKey: "FAC_NAME",
        rowPinned: undefined,
        key: undefined
      });
    },
  }
};
</script>
  
<style scoped>
.ag-theme-alpine-dark {
  /* 헤더 텍스트 컬러*/
  --ag-foreground-color: #fff;
  /* 헤더 배경 컬러*/
  --ag-background-color: rgb(0, 0, 0, 0.1);
  /* 그리드 텍스트 컬러 */
  --ag-header-foreground-color: #fff;
  /* 그리드 배경 컬러 */
  --ag-header-background-color: rgb(0, 0, 0, 0.3);
  /* 그리드 스트라이프 패턴 색 */
  --ag-odd-row-background-color: rgb(0, 0, 0, 0.04);
  /* 헤더 수직 구분선 */
  --ag-header-column-resize-handle-color: #fff;
  --ag-font-color: #fff;
  --ag-borders: none;
  --ag-font-size: 17px;
  --ag-font-family: KHNPHDRegular;

}

.ag-theme-alpine-dark .ag-header-cell-label {
  display: flex;
  justify-content: center;
  align-items: center;
}

.centered-checkbox {
    display: flex;
    justify-content: center;
    align-items: center;
  }
</style>