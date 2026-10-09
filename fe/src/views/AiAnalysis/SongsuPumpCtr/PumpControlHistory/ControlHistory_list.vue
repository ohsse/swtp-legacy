<template>
  <div>
    <div class="table-scroll">
      <b-table class="table-style table-posi" :fields="fields" :items="paginatedItems"></b-table>
    </div>
    <b-pagination class="pagination-custom" v-model="currentPage" v-if="items && items.length"
      :total-rows="items.length" :per-page="perPage" align="center" />
  </div>
</template>
<script>
export default {
  data() {
    return {
      thisYearData: [],
      lastYearData: null,
      fields: [
        { key: 'ORDER_TIME', label: '제어시간', sortable: true, thStyle: { width: '200px' } },
        { key: 'PUMP_NM', label: '송수펌프', sortable: true, thStyle: { width: '200px' } },
        { key: 'TAG', label: '태그명', sortable: false, thStyle: { width: '200px' } },
        { key: 'ANLY_CD', label: '구분', sortable: false, thStyle: { width: '200px' } },
        { key: 'FLAG', label: '결과', sortable: false, thStyle: { width: '200px' } },
        { key: 'UPDT_TIME', label: '갱신시간', sortable: false, thStyle: { width: '200px' } },
        { key: 'AI_STATUS', label: '운전모드', sortable: false, thStyle: { width: '200px' } }
      ],
      items: [],
      currentPage: 1,
      perPage: 15,
    }
  },
  computed: {
    paginatedItems() {
      const start = (this.currentPage - 1) * this.perPage
      const end = start + this.perPage
      return this.items?.slice(start, end)
    }
  },
  mounted() {
    this.setData()
  },

  methods: {
    setData(items) {
      this.currentPage = 1
      this.items = items
    },
  },
}
</script>

<style>
.table-style {
  border-color: #489cf2;
  font-family: KHNPHDRegular;
  text-align: center;
}
.table-scroll {
  max-height: 250px; /* 필요에 따라 높이 조정 */
  overflow-y: auto;
}
.table-posi {
  margin-top: 0px;
}

input[type="text"] {
  /* 원하는 색상으로 배경색을 변경합니다. */
  background-color: #15284e;
  /* 테두리의 색상을 변경합니다. */
  border-color: blue;
  /* 테두리 두께를 변경합니다. */
  border-width: .125rem;
  /* 테두리를 둥글게 처리합니다. */
  border-radius: .3125rem;
  /* 입력된 텍스트의 색상을 변경합니다. */
  color: #ffffff;

}

.right-aligned-input {
  text-align: right;
}
.pagination-custom {
  margin-top : 10px;
}
.pagination-custom .page-link {
  background-color: transparent;
  border-color: transparent;
  color: #ffffff;
}

.pagination-custom .page-item.active .page-link {
  background-color: #489cf2;
  border-color: transparent;
}

.pagination-custom .page-item.disabled .page-link {
  background-color: transparent;
  border-color: transparent;
  color: #15284e;
}
</style>