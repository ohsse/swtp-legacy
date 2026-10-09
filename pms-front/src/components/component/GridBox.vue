<template>
  <ag-grid-vue class="ag-theme-alpine-dark" style="width: 100%; height: 100%;" :columnDefs="columnDefs" :rowData="rowData" />
</template>

<script>
import { AgGridVue } from "ag-grid-vue3";  // the AG Grid Vue Component

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
    }
  },
 
  methods: {
    setField(filed) {
      this.columnDefs = filed
    },
    setData(rowData) {
      this.rowData = rowData
    },
  },
}
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
}

</style>