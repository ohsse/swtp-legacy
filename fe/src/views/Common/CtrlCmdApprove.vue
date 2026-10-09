<template>
  <!-- 군산 5분 제어 판단 · AI 추천 모드 승인 팝업 (docs/gunsan-ctrl-workflow.html 9.2) -->
  <div v-if="visible" class="ctrl-approve-mask">
    <div class="ctrl-approve-card" role="dialog" aria-labelledby="ctrl-approve-title">
      <div class="ctrl-approve-head">
        <span id="ctrl-approve-title">AI 추천 · 제어 승인 대기</span>
        <!-- 판단은 다음 판단 20초 전에 마감된다. 응답이 없으면 REJECTED(승인 응답 없음)로 종결 -->
        <span class="ctrl-approve-remain" title="마감까지 응답이 없으면 거절로 처리되고, 다음 판단이 새로 올라옵니다">응답 마감까지 {{ remainText }}</span>
      </div>

      <div class="ctrl-approve-body">
        <div v-for="item in items" :key="item.CTRL_ID + ':' + item.DEVICE" class="ctrl-approve-item">
          <div class="ctrl-approve-device">
            {{ item.DEVICE_NM }}<span v-if="item.DEVICE === 'PUMP' && item.PUMP_COMB"> · 조합 {{ item.PUMP_COMB }}</span>
          </div>
          <div class="ctrl-approve-value">
            {{ fmt(item.CUR) }} → {{ fmt(item.TGT, 0) }} {{ unit(item.DEVICE) }}
            <span class="ctrl-approve-delta">({{ delta(item) }})</span>
          </div>
          <div class="ctrl-approve-ts">판단 {{ item.CTRL_TS }}</div>
          <div v-if="item.BLOCK_REASON" class="ctrl-approve-block">
            승인 불가 · {{ item.BLOCK_REASON_LABEL }}
          </div>
          <div v-else class="ctrl-approve-btns">
            <button type="button" class="ctrl-btn ctrl-btn-ok" :disabled="busy || itemRemain(item) <= 0" @click="approve(item)">승인</button>
            <button type="button" class="ctrl-btn ctrl-btn-no" :disabled="busy" @click="reject(item)">거절</button>
          </div>
        </div>

        <div class="ctrl-approve-reason">
          <span class="ctrl-approve-label">사유</span>
          {{ reasonText }}
        </div>
      </div>

      <div class="ctrl-approve-foot">
        <button type="button" class="ctrl-btn" :disabled="busy || !approvable.length" @click="rejectAll">모두 거절</button>
        <button type="button" class="ctrl-btn" @click="dismiss">닫기(나중에)</button>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchFunc } from '@/util/fetchFunc'
import Swal from 'sweetalert2'

// 승인 대기 조회 주기. 서버 판정(:40)과 반영 판정(30초)에 맞춘다
const POLL_MS = 30 * 1000

export default {
  name: 'CtrlCmdApprove',
  data() {
    return {
      items: [],
      mode: null,
      busy: false,
      // 닫은 항목과 알람을 낸 항목 (CTRL_ID:DEVICE). 목록이 줄기만 해서는 다시 뜨거나 울리지 않는다
      dismissedKeys: [],
      alarmedKeys: [],
      pollTimer: null,
      tickTimer: null,
      now: Date.now(),
      fetchedAt: Date.now(),
    }
  },
  computed: {
    itemKeys() {
      return this.items.map(i => i.CTRL_ID + ':' + i.DEVICE)
    },
    // 닫지 않은 항목이 하나라도 있으면 뜬다. 새 판단이 올라오면 다시 뜬다
    visible() {
      return this.mode === 1 && this.itemKeys.some(k => !this.dismissedKeys.includes(k))
    },
    approvable() {
      return this.items.filter(i => !i.BLOCK_REASON)
    },
    remainText() {
      if (!this.items.length) return '--:--'
      const sec = Math.min(...this.items.map(this.itemRemain))
      return String(Math.floor(sec / 60)).padStart(2, '0') + ':' + String(sec % 60).padStart(2, '0')
    },
    reasonText() {
      const labels = []
      this.items.forEach(i => (i.REASONS || []).forEach(r => {
        if (!labels.includes(r.label)) labels.push(r.label)
      }))
      return labels.join(' · ') || '-'
    },
  },
  mounted() {
    this.poll()
    this.pollTimer = setInterval(this.poll, POLL_MS)
    this.tickTimer = setInterval(() => { this.now = Date.now() }, 1000)
  },
  beforeUnmount() {
    clearInterval(this.pollTimer)
    clearInterval(this.tickTimer)
  },
  methods: {
    async poll() {
      try {
        const res = await fetchFunc(`${this.$apiURL}/ai/ctrl/pending`)
        // fetchFunc 는 실패해도 던지지 않고 {error:true} 를 준다. 그때는 직전 상태를 유지한다
        if (!res || res.error || !res.data) return
        const data = res.data
        this.mode = data.mode
        this.items = data.items || []
        this.fetchedAt = Date.now()
        this.now = this.fetchedAt
        // 알람음은 새 판단이 나타날 때 한 번만 낸다
        const fresh = this.itemKeys.filter(k => !this.alarmedKeys.includes(k))
        if (this.visible && fresh.length) {
          this.alarmedKeys = this.alarmedKeys.concat(fresh).slice(-50)
          try {
            new Audio(require('@/assets/pump_alarm_sound.mp3')).play()
          } catch (e) {
            // 브라우저 자동재생 차단은 무시한다
          }
        }
      } catch (e) {
        // 조회 실패 시 팝업 상태를 유지하고 다음 주기에 다시 조회한다
      }
    },
    async approve(item) {
      await this.send('approve', item)
    },
    async reject(item) {
      await this.send('reject', item)
    },
    async rejectAll() {
      const confirmed = await Swal.fire({
        animation: false,
        text: '승인 대기 중인 제어를 모두 거절하시겠습니까?',
        showCancelButton: true,
        confirmButtonText: '모두 거절',
        cancelButtonText: '취소',
      })
      if (!confirmed.isConfirmed) return
      for (const item of this.approvable) {
        await this.send('reject', item, true)
      }
      await this.poll()
    },
    async send(action, item, silent = false) {
      this.busy = true
      try {
        const res = await fetchFunc(`${this.$apiURL}/ai/ctrl/${action}`, {
          ctrlId: item.CTRL_ID,
          device: item.DEVICE,
          userId: localStorage.getItem('user'),
        })
        if (!silent) {
          Swal.fire({ animation: false, text: res?.message || '처리되었습니다.' })
        }
      } catch (e) {
        if (!silent) {
          Swal.fire({ animation: false, text: '요청 처리 중 오류가 발생했습니다.' })
        }
      } finally {
        this.busy = false
        if (!silent) await this.poll()
      }
    },
    // 응답 마감까지 남은 초. 서버 값에서 마지막 조회 이후 흐른 시간을 뺀다
    itemRemain(item) {
      const elapsed = Math.floor((this.now - this.fetchedAt) / 1000)
      return Math.max(0, (Number(item.REMAIN_SEC) || 0) - elapsed)
    },
    // 상태를 바꾸지 않고 숨긴다. 새 판단이 올라오면 다시 뜬다
    dismiss() {
      this.dismissedKeys = this.dismissedKeys.concat(this.itemKeys).slice(-50)
    },
    fmt(v, digits = 1) {
      const n = Number(v)
      return Number.isFinite(n) ? n.toFixed(digits) : '-'
    },
    unit(device) {
      return device === 'PUMP' ? 'Hz' : '%'
    },
    delta(item) {
      const d = Math.round(Number(item.TGT)) - Number(item.CUR)
      if (!Number.isFinite(d)) return '-'
      return (d > 0 ? '+' : '') + d.toFixed(1) + (item.DEVICE === 'PUMP' ? ' Hz' : ' %p')
    },
  },
}
</script>

<style scoped>
.ctrl-approve-mask {
  position: fixed;
  inset: 0;
  z-index: 6100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
}

.ctrl-approve-card {
  width: min(560px, calc(100vw - 32px));
  max-height: calc(100vh - 48px);
  overflow: auto;
  background: #1f2a44;
  color: #e8edf5;
  border: 1px solid #3a4a6b;
  border-radius: 6px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.ctrl-approve-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  font-size: 17px;
  font-weight: 700;
  border-bottom: 1px solid #3a4a6b;
}

.ctrl-approve-remain {
  font-size: 14px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  color: #f2c14e;
}

.ctrl-approve-body {
  display: grid;
  gap: 10px;
  padding: 14px 18px;
}

.ctrl-approve-item {
  padding: 10px 12px;
  border: 1px solid #3a4a6b;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.03);
}

.ctrl-approve-device {
  font-size: 13px;
  color: #a9b6cc;
}

.ctrl-approve-value {
  margin-top: 2px;
  font-size: 20px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.ctrl-approve-delta {
  font-size: 13px;
  font-weight: 500;
  color: #a9b6cc;
}

.ctrl-approve-ts {
  font-size: 12px;
  color: #8190a8;
}

.ctrl-approve-block {
  margin-top: 6px;
  font-size: 13px;
  color: #ef8a80;
}

.ctrl-approve-btns,
.ctrl-approve-foot {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ctrl-approve-btns {
  margin-top: 8px;
}

.ctrl-approve-reason {
  font-size: 13px;
  line-height: 1.5;
}

.ctrl-approve-label {
  display: inline-block;
  margin-right: 6px;
  color: #8190a8;
}

.ctrl-approve-foot {
  justify-content: flex-end;
  padding: 12px 18px 16px;
  border-top: 1px solid #3a4a6b;
}

.ctrl-btn {
  min-width: 84px;
  padding: 6px 14px;
  border: 1px solid #56688f;
  border-radius: 4px;
  background: transparent;
  color: #e8edf5;
  font-weight: 600;
  cursor: pointer;
}

.ctrl-btn:focus-visible {
  outline: 2px solid #f2c14e;
  outline-offset: 2px;
}

.ctrl-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.ctrl-btn-ok {
  border-color: #4caf7d;
  color: #7fdca8;
}

.ctrl-btn-no {
  border-color: #e0685e;
  color: #ef8a80;
}
</style>
