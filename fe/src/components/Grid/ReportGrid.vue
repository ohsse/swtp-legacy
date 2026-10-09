<template>
  <ag-grid-vue class="ag-theme-alpine-dark" style="width: 100%; height: 100%" :columnDefs="columnDefs" :rowData="rowData"
    :defaultColDef="defaultColDef" rowSelection="multiple" animateRows="true" :stopEditingWhenCellsLoseFocus="true"
    @cell-clicked="cellWasClicked" @grid-ready="onGridReady" ref="agGrid">
  </ag-grid-vue>
</template>

<script>
import { AgGridVue } from "ag-grid-vue3"; // the AG Grid Vue Component
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
      editedData: [],
    };
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
      editable: false,
      // cellStyle: { 'white-space': 'normal', 'word-wrap': 'break-word'},
      // headerStyle :{ 'text-align': 'center' },
      cellClass: "centered-checkbox",
    });

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
      // console.log("setField" + filed);
      this.columnDefs = filed;
    },
    setData(rowData) {
      
      this.rowData = rowData;
    },
  },
};
</script>

<style>
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
  white-space: normal; /* 헤더 텍스트가 자동으로 다음 줄로 내려가도록 설정 */
  word-wrap: break-word; /* 긴 헤더 텍스트가 줄 바꿈되도록 설정 */
  line-height: 1.2; /* 필요에 따라 줄 간격 조절 */
  height: auto; /* 헤더 높이를 자동으로 조절 */
}

.centered-checkbox {
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>

