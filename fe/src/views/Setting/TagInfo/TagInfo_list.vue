<template>
  <div class="div-big2 mt-3 bottom-contents-box" >
    <div class="EitemsName" style="width: 98%; display:flex; justify-content: end; margin: 0 8px 0 8px;">
      <button @click="updateBtn()" style="height: 32px; float: right;" class="search_btn_font search_btn">저장</button>
    </div>
    <div style="margin: 0 20px 0 20px; overflow: scroll; height: 85%; width: 98%;">
      <TagInfoGrid ref="tagInfoGrid" @getUpdateData="tagUpdate" :style="{ height: '100%' }" />
    </div>
  </div>
</template>

<script>
import TagInfoGrid from '@/components/Grid/TagInfoGrid.vue'
import { fetchFunc } from '@/util/fetchFunc';

export default {
  components: {
    TagInfoGrid
  },
  data() {
    return {
      filed: new Array(),
      rowData: new Array(),

    }
  },
  methods: {
    setGridFiled(value) {
      this.filed = [
        {
          headerClass: 'header-center',
          headerName: '시설명',
          field: 'zone_code',
          cellEditor: 'agSelectCellEditor',
          cellEditorParams: { values: value },
          flex: 3,
          lockPosition: true,
        },
        {
          headerClass: 'header-center',
          headerName: '설비코드',
          field: 'FAC_CODE',
          editable: false,
          flex: 3,
          lockPosition: true,
        },
        {
          headerClass: 'header-center',
          headerName: '설비명',
          field: 'FAC_NAME',
          cellEditor: 'agTextCellEditor',
          cellEditorParams: {
            useFormatter: false,
            maxLength: 200
          },
          valueFormatter: function (params) {
            const replaceKeyword = /[!@#$%^&*+=[\]{};:'"|<.>?~`]/g;
            const value = params.value;
            let newValue
            if (value !== null && value !== "") {
              newValue = value.replace(replaceKeyword, "");
            } else {
              newValue = value;
            }
            return newValue;
          },
          flex: 7,
          lockPosition: true,
        },
        {
          headerClass: 'header-center',
          headerName: '태그',
          field: 'tagname',
          editable: false,
          flex: 6,
          wrapText: true, 
          autoHeight: true,
          cellRenderer: 'multilineCellRenderer',
          lockPosition: true,
        },
        {
          headerClass: 'header-center',
          headerName: '사용여부',
          field: 'USE_YN',
          editable: true,
          cellRenderer: 'agCheckboxCellRenderer',
          cellEditor: 'agCheckboxCellEditor',
          cellStyle: {              // 셀의 스타일을 설정하는 객체
            'text-align': 'center', // 텍스트를 중앙으로 정렬
          },
          flex: 2,
          lockPosition: true,
        },
      ]

      this.$refs.tagInfoGrid.setField(this.filed)
    },
    setGridRowData(data) {
      this.$refs.tagInfoGrid.setData(data)
    },
    updateBtn() {
      this.$refs.tagInfoGrid.onUpdateData();
    },
    async tagUpdate(data) {

      let updateData = data;
      for (let i in updateData) {
        updateData[i]['USE_YN'] = updateData[i]['USE_YN'] ? '1' : '0';
      }
      const apiURL = this.$apiURL;
      let res = (await fetchFunc(`${apiURL}/st/updateTagInfo`, updateData)).data

      if (res !== null && res !== undefined) {
    
        alert(`${res}건이 저장되었습니다.`)
        this.$emit('getNewList');
      }
    },

  }
}
</script>

<style scoped>
.bottom-contents-box {
  padding: 5px 10px;
  height: 85%;
  width: 99%;
}
.table-style {
  border-color: #489cf2;
  font-family: KHNPHDRegular;
  text-align: center;
}

.search_btn_font {
  text-shadow: 0 0 9px #5cafff;
  font-size: 17px;
  letter-spacing: normal;
  color: #fff;
  font-family: KHNPHDRegular;
  text-align: center;
  line-height: 2;
}

.search_btn {
  width: 80px;
  align-self: center;
  border: solid 1px #b4dffa;
  background-color: rgba(139, 194, 240, 0.25);
  cursor: pointer;
  border-radius: 4px;
  align-items: center;
  justify-content: center;
  display: flex;
}
</style>