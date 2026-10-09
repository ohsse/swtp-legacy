<template>
  <GridBox ref="gridBox"/> 
 </template>
 
 <script>
 import GridBox from '@/components/component/GridBox.vue';
 
 export default {
     name: 'App',
     data() {
         return {
             columnDefs: null,
             rowData: null
         }
     },
     components: {
         GridBox
     },
     mounted() {
       this.setGridFiled();
       // this.setRowData();
     },
     methods: {
       setGridFiled() {
         this.filed = [
           {
             headerName: '일시',
             field: 'ALR_TIME',
             flex: 3,
             lockPosition: true,
             sortable: true, 
             sort: 'desc',
           },
           {
             headerName: '설비명',
             field: 'FAC_NAME',
             flex: 3,
             lockPosition: true,
             sortable: true, 
           },
           {
             headerName: '설비정보',
             field: 'FAC_INFO',
             flex: 3,
             lockPosition: true,
             sortable: true, 
           },
           {
             headerName: '진단상태',
             field: 'DIAG_STUS',
             flex: 3,
             lockPosition: true,
             sortable: true, 
           },
           {
             headerName: '알람상태',
             field: 'FLAG',
             flex: 3,
             lockPosition: true,
             sortable: true, 
           },
         ]
         this.$refs.gridBox.setField(this.filed)
       },
       setRowData(data){
         const rowData = [];
         for (let index = 0; index < data.length; index++) {
           const item = data[index];
           rowData.push({
             ALR_TIME: item?.ALR_TIME,
             FAC_NAME: item?.FAC_NAME,
             FAC_INFO: item?.FAC_INFO,
             DIAG_STUS: item?.DIAG_STUS,
             FLAG: item?.FLAG
           });
         }
         this.$refs.gridBox.setData(rowData)
       }
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