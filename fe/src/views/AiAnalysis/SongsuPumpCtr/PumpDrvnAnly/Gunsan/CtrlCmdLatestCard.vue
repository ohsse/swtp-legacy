<template>
  <!-- 군산 5분 제어 판단 · 최근 판단 카드 (docs/gunsan-ctrl-workflow.html 9.1) -->
  <div v-if="cmd" class="ctrl-latest">
    <div class="ctrl-latest-head">
      <span>제어 판단 · {{ cmd.CTRL_TS.substring(11, 16) }}</span>
      <span class="ctrl-latest-mode">{{ modeLabel }}</span>
    </div>
    <div class="ctrl-latest-row">
      <div v-for="d in devices" :key="d.key" class="ctrl-latest-box">
        <div class="ctrl-latest-k">
          {{ d.name }}<span v-if="d.key === 'PUMP' && cmd.PUMP_COMB"> · 조합 {{ cmd.PUMP_COMB }}</span>
        </div>
        <template v-if="cmd[d.key + '_CMD_YN'] === 'Y'">
          <div class="ctrl-latest-v">{{ fmt(cmd[d.cur]) }} → {{ fmt(cmd[d.tgt], 0) }} {{ d.unit }}</div>
          <span :class="'st st-' + viewStatus(d.key).toLowerCase()">{{ statusLabel(viewStatus(d.key)) }}</span>
        </template>
        <div v-else class="ctrl-latest-v muted">명령 없음</div>
      </div>
    </div>
    <div class="ctrl-latest-reason">
      <span class="muted">사유</span> {{ reasonText }}
    </div>
  </div>
</template>

<script>
import { fetchFunc } from '@/util/fetchFunc'

const POLL_MS = 30 * 1000

const STATUS_LABELS = {
  WAITING: '승인·처리 대기',
  IN_PROGRESS: '송신 중',
  READY: '대기',
  APPLIED: '반영 완료',
  REJECTED: '거절',
  FAILED: '실패',
  EXPIRED: '만료',
}

export default {
  name: 'CtrlCmdLatestCard',
  data() {
    return {
      cmd: null,
      mode: null,
      consumerEnabled: false,
      timer: null,
      devices: [
        { key: 'PUMP', name: '송수펌프', cur: 'PUMP_CUR_HZ', tgt: 'PUMP_TGT_HZ', unit: 'Hz' },
        { key: 'NATIONAL', name: '국가산단 밸브', cur: 'NATIONAL_CUR_OPEN', tgt: 'NATIONAL_TGT_OPEN', unit: '%' },
        // 지방산단 밸브: 2026-09-30 벤더 드롭에서 나운 고수위 최종(fallback) 제어로 부활
        { key: 'LOCAL', name: '지방산단 밸브', cur: 'LOCAL_CUR_OPEN', tgt: 'LOCAL_TGT_OPEN', unit: '%' },
      ],
    }
  },
  computed: {
    modeLabel() {
      if (!this.consumerEnabled) return '연계 꺼짐'
      return ['AI 운전 · 자동 제어', 'AI 추천 · 승인 후 제어', 'AI 분석 · 미송신'][this.mode] || '-'
    },
    reasonText() {
      return (this.cmd?.REASONS || []).map(r => r.label).join(' · ') || '-'
    },
  },
  mounted() {
    this.load()
    this.timer = setInterval(this.load, POLL_MS)
  },
  beforeUnmount() {
    clearInterval(this.timer)
  },
  methods: {
    async load() {
      try {
        const res = await fetchFunc(`${this.$apiURL}/ai/ctrl/latest`)
        // fetchFunc 는 실패해도 던지지 않고 {error:true} 를 준다. 그때는 직전 표시를 유지한다
        if (!res || res.error || !res.data) return
        const data = res.data
        this.cmd = data.cmd || null
        this.mode = data.mode
        this.consumerEnabled = !!data.consumerEnabled
      } catch (e) {
        // 조회 실패 시 직전 표시를 유지한다
      }
    },
    viewStatus(device) {
      return this.cmd?.[device + '_VIEW_STATUS'] || this.cmd?.[device + '_CMD_STATUS'] || '-'
    },
    statusLabel(s) {
      return STATUS_LABELS[s] || s
    },
    fmt(v, digits = 1) {
      const n = Number(v)
      return Number.isFinite(n) ? n.toFixed(digits) : '-'
    },
  },
}
</script>

<style scoped>
.ctrl-latest {
  margin: 8px 0 12px;
  padding: 10px 14px;
  border: 1px solid #2f4a78;
  border-radius: 6px;
  background: rgba(21, 40, 78, 0.55);
  color: #e8edf5;
}

.ctrl-latest-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-weight: 700;
  margin-bottom: 8px;
}

.ctrl-latest-mode {
  font-size: 13px;
  font-weight: 600;
  color: #8cc2fa;
}

.ctrl-latest-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}

.ctrl-latest-box {
  padding: 8px 10px;
  border: 1px solid #2f4a78;
  border-radius: 4px;
}

.ctrl-latest-k {
  font-size: 12px;
  color: #a9b6cc;
}

.ctrl-latest-v {
  font-size: 18px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.ctrl-latest-reason {
  margin-top: 8px;
  font-size: 13px;
}

.muted {
  color: #7f8fab;
}

.st {
  display: inline-block;
  padding: 0 6px;
  border: 1px solid #56688f;
  border-radius: 3px;
  font-size: 12px;
}

.st-applied {
  border-color: #4caf7d;
  color: #7fdca8;
}

.st-in_progress,
.st-waiting,
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
