<template>
  <!-- 군산 5분 제어 판단 이력 (docs/gunsan-ctrl-workflow.html 10장) -->
  <div>
    <div class="table-scroll">
      <b-table class="table-style table-posi" :fields="fields" :items="paginatedItems" show-empty
        empty-text="해당 기간의 제어 판단이 없습니다.">
        <template #cell(PUMP)="row">
          <span v-if="row.item.PUMP_CMD_YN === 'Y'">
            {{ fmt(row.item.PUMP_CUR_HZ) }} → {{ fmt(row.item.PUMP_TGT_HZ, 0) }} Hz
            <span :class="'st st-' + statusClass(row.item.PUMP_CMD_STATUS)">{{ statusLabel(row.item.PUMP_CMD_STATUS) }}</span>
          </span>
          <span v-else class="muted">-</span>
        </template>
        <template #cell(NATIONAL)="row">
          <span v-if="row.item.NATIONAL_CMD_YN === 'Y'">
            {{ fmt(row.item.NATIONAL_CUR_OPEN) }} → {{ fmt(row.item.NATIONAL_TGT_OPEN, 0) }} %
            <span :class="'st st-' + statusClass(row.item.NATIONAL_CMD_STATUS)">{{ statusLabel(row.item.NATIONAL_CMD_STATUS) }}</span>
          </span>
          <span v-else class="muted">-</span>
        </template>
        <template #cell(LOCAL)="row">
          <span v-if="row.item.LOCAL_CMD_YN === 'Y'">
            {{ fmt(row.item.LOCAL_CUR_OPEN) }} → {{ fmt(row.item.LOCAL_TGT_OPEN, 0) }} %
            <span :class="'st st-' + statusClass(row.item.LOCAL_CMD_STATUS)">{{ statusLabel(row.item.LOCAL_CMD_STATUS) }}</span>
          </span>
          <span v-else class="muted">-</span>
        </template>
        <template #cell(REASONS)="row">
          {{ (row.item.REASONS || []).map(r => r.label).join(' · ') || '-' }}
        </template>
        <template #cell(TRACE)="row">
          <div v-for="t in (row.item.TRACE || [])" :key="t.TRACE_ID" class="trace">
            {{ t.TS.substring(11) }} {{ deviceLabel(t.DEVICE) }} {{ actionLabel(t.ACTION) }}<span
              v-if="t.REASON_LABEL"> · {{ t.REASON_LABEL }}</span><span v-if="t.USER_ID"> · {{ t.USER_ID }}</span>
          </div>
          <span v-if="!(row.item.TRACE || []).length" class="muted">-</span>
        </template>
      </b-table>
    </div>
    <b-pagination class="pagination-custom" v-model="currentPage" v-if="items && items.length"
      :total-rows="items.length" :per-page="perPage" align="center" />
  </div>
</template>

<script>
const STATUS_LABELS = {
  READY: '대기',
  APPLIED: '반영',
  REJECTED: '거절',
  FAILED: '실패',
  EXPIRED: '만료',
  NO_COMMAND: '-',
}

const ACTION_LABELS = {
  ENQUEUE: '적재',
  APPROVE: '승인',
  REJECT: '거절',
  EXPIRE: '만료',
  APPLY: '반영',
  FAIL: '실패',
}

export default {
  name: 'CtrlCmdHistoryList',
  data() {
    return {
      fields: [
        { key: 'CTRL_TS', label: '판단시각', sortable: true, thStyle: { width: '170px' } },
        { key: 'PUMP', label: '송수펌프(Hz)', thStyle: { width: '190px' } },
        { key: 'NATIONAL', label: '국가산단 밸브(%)', thStyle: { width: '190px' } },
        { key: 'LOCAL', label: '지방산단 밸브(%)', thStyle: { width: '190px' } },
        { key: 'REASONS', label: '판단 사유' },
        { key: 'TRACE', label: '처리', thStyle: { width: '280px' } },
      ],
      items: [],
      currentPage: 1,
      perPage: 15,
    }
  },
  computed: {
    paginatedItems() {
      const start = (this.currentPage - 1) * this.perPage
      return (this.items || []).slice(start, start + this.perPage)
    },
  },
  methods: {
    setData(items) {
      this.currentPage = 1
      this.items = items || []
    },
    fmt(v, digits = 1) {
      const n = Number(v)
      return Number.isFinite(n) ? n.toFixed(digits) : '-'
    },
    statusLabel(s) {
      return STATUS_LABELS[s] || s || '-'
    },
    statusClass(s) {
      return (s || 'none').toLowerCase()
    },
    actionLabel(a) {
      return ACTION_LABELS[a] || a
    },
    deviceLabel(d) {
      if (d === 'PUMP') return '펌프'
      return d === 'LOCAL' ? '지방산단 밸브' : '국가산단 밸브'
    },
  },
}
</script>

<style scoped>
.muted {
  color: #6f7f9c;
}

.trace {
  font-size: 12px;
  line-height: 1.5;
  text-align: left;
  white-space: nowrap;
}

.st {
  display: inline-block;
  margin-left: 4px;
  padding: 0 6px;
  border: 1px solid #56688f;
  border-radius: 3px;
  font-size: 12px;
}

.st-applied {
  border-color: #4caf7d;
  color: #7fdca8;
}

.st-ready {
  border-color: #489cf2;
  color: #8cc2fa;
}

.st-failed {
  border-color: #e0685e;
  color: #ef8a80;
}

.st-expired {
  border-color: #d9a441;
  color: #f2c14e;
}

.st-rejected {
  color: #a9b6cc;
}
</style>
