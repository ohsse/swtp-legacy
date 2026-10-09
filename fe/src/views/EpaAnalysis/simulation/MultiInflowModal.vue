<template>
  <div class="modal fade custom-modal" id="multiInflowModal" tabindex="-1" aria-labelledby="multiInflowModalLabel"
    aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content custom-modal__content">
        <div class="modal-header custom-modal__header">
          <h5 class="modal-title" id="multiInflowModalLabel">배수지 수요량 설정</h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>

        <div class="modal-body custom-modal__body">
          <div class="custom-tbl table-responsive mb-0">
            <table class="table table-sm table-bordered align-middle mb-0">
              <colgroup>
                <col style="width:14%">
                <col style="width:19%">
                <col style="width:14%">
                <col style="width:19%">
                <col style="width:14%">
                <col style="width:20%">
              </colgroup>
              <thead>
                <tr>
                  <th scope="col">배수지</th>
                  <th scope="col">수요량</th>
                  <th scope="col">배수지</th>
                  <th scope="col">수요량</th>
                  <th scope="col">배수지</th>
                  <th scope="col">수요량</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, rowIndex) in chunkedReservoirs" :key="rowIndex">
                  <template v-for="item in row" :key="item.NODE_ID">
                    <td>{{ item.TNK_NM }}</td>
                    <td>
                      <input type="number" class="form-control form-control-sm kw-input-number"
                        v-model="localTanks[item.TNK_NM]" @input="onNumberInput(item.TNK_NM)" />
                    </td>
                  </template>
                  <!-- 행의 남은 칸을 '-'로 채웁니다 -->
                  <template v-if="row.length < 3">
                    <td v-for="i in (3 - row.length)" :key="'empty-' + rowIndex + '-' + i" colspan="2">-</td>
                  </template>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="modal-footer custom-modal__footer">
          <b-button variant="outline-light" size="sm" class="cust-btn" @click="handleSave">저장</b-button>
          <b-button variant="outline-light" size="sm" class="cust-btn" data-bs-dismiss="modal"
            style="margin-right: 0;">취소</b-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as bootstrap from 'bootstrap';

export default {
  name: 'MultiInflowModal',
  props: {
    // 부모로부터 flows 데이터를 받습니다.
    tanks: {
      type: Array,
      required: true,
    }
  },
  emits: ['save'],
  data() {
    return {
      // 부모 데이터를 직접 수정하지 않기 위해 로컬 데이터로 복사해서 사용합니다.
      localTanks: {},
      // 테이블 구조를 정의하는 데이터
    };
  },
  computed: {
    // tanks 배열을 3개씩 묶어 2차원 배열로 만듭니다.
    chunkedReservoirs() {
      if (!this.tanks || this.tanks.length === 0) return [];
      const result = [];
      for (let i = 0; i < this.tanks.length; i += 3) {
        result.push(this.tanks.slice(i, i + 3));
      }
      return result;
    }
  },
  watch: {
    tanks: {
      handler(newTanks) {
        // flows 배열을 {TNK_NM: FLOW_RATE} 형태의 객체로 변환
        if (Array.isArray(newTanks)) {
          this.localTanks = {};
          newTanks.forEach(item => {
            if (item.TNK_NM) {
              const rawValue = item.FLOW_RATE?.toString() || '0';
              // 콤마가 없는 순수 숫자 문자열로 저장
              this.localTanks[item.TNK_NM] = Number(rawValue.replace(/,/g, '')).toString();
            }
          });
        } else {
          // 기존 객체 방식도 지원
          this.localTanks = { ...newTanks };
        }
        console.log("🚀 ~ handler ~ this.localTanks:", this.localTanks)
      },
      
      immediate: true,
      deep: true,
    }
  },
  methods: {
    // [수정됨] $nextTick을 사용하여 DOM 업데이트 타이밍 문제 해결
    onNumberInput(key) {
      // v-model이 값을 업데이트한 상태 (e.g., "123.")
      const value = this.localTanks[key] || '';

      // 1. (요청) 숫자 이외의 값 (소수점, 문자, 음수)을 모두 제거
      const sanitizedValue = value.toString().replace(/[^\d]/g, '');

      let finalValue;

      // 2. (요청) 값이 비어있으면 '0'
      if (sanitizedValue === '') {
        finalValue = '0';
      } else {
        // '05' -> '5'
        finalValue = Number(sanitizedValue).toString();
      }

      // 3. $nextTick으로 DOM 업데이트 (커서 점프 방지)
      this.$nextTick(() => {
        this.localTanks[key] = finalValue;
      });
    },

    // 콤마 포맷팅 (현재 입력 로직에서는 사용되지 않음)
    formatWithComma(numStr) {
      const strToFormat = numStr || '0';
      let parts = strToFormat.split('.');
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      return parts.join('.');
    },

    // 저장 버튼 클릭 시
    handleSave() {
      // localTanks의 값을 원본 tanks 배열 형식에 맞춰 새로운 배열로 생성
      const updatedTanks = this.tanks.map(tank => {
        const newFlowString = this.localTanks[tank.TNK_NM]; // (e.g., "1234")
        
        // 콤마 제거 로직이 더 이상 필요 없음
        const newFlowRate = parseFloat(newFlowString || '0');

        return {
          ...tank, // 기존 tank 데이터 복사
          FLOW_RATE: newFlowRate // FLOW_RATE만 업데이트
        };
      });

      // 이벤트를 통해 부모에게 업데이트된 tanks 배열 전달
      this.$emit('save', updatedTanks);
      
      // 모달 닫기
      const modalEl = document.getElementById('multiInflowModal');
      if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) {
          modal.hide();
        }
      }
    },
  },
};
</script>

<style scoped>
/* 원본 소스에서 모달 관련 모든 스타일을 여기에 복사했습니다. */
.custom-modal .custom-modal__content {
  position: relative;
  border: 0;
  overflow: hidden;
  background: #0f1c2a;
  color: #dbe7ff;
  border-radius: 0;
  box-shadow: 0 12px 40px rgba(0, 0, 0, .5);
  overflow: hidden
}

.custom-modal__content::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  z-index: 1;
  box-shadow: inset 0 0 20px 0 #0D67F2;
  background: transparent
}

.custom-modal__header {
  font-size: 1.5rem;
  font-weight: 700;
  background: #1A2C6A;
  color: #fff;
  border-bottom: 0 !important;
  padding: 10px 16px;
  border-top-left-radius: 0 !important;
  border-top-right-radius: 0 !important
}

.custom-modal__header .modal-title {
  font-size: 1.45rem;
  font-weight: 800;
  letter-spacing: .02em
}

.custom-modal__header .btn-close {
  width: .5rem;
  height: .5rem;
  margin-right: 7px
}

.custom-modal__body {
  background: #0f1c2a;
  padding: 18px 18px 0
}

.custom-modal__footer {
  border-top: 0;
  background: #0f1c2a;
  padding: 14px 18px 18px;
  justify-content: flex-end;
  border-bottom-left-radius: 0 !important;
  border-bottom-right-radius: 0 !important
}

.custom-modal__footer .btn {
  font-weight: 700;
  border-radius: 0
}

/* 테이블 스타일 */
.custom-tbl th {
  font-size: 18px
}

.custom-tbl td,
.custom-tbl th {
  border: 1px solid #405C8C;
  padding: 5px 8px;
  color: #fff;
  font-size: 16px;
  text-align: center;
  vertical-align: middle;
  background: rgba(0, 0, 0, .35)
}

.custom-tbl th {
  background: rgba(26, 44, 106, 1)
}

.custom-tbl tbody tr:hover {
  background: rgba(8, 80, 191, 1) !important
}

.custom-tbl tbody tr:hover td {
  border: 1px solid #fff;
  border-top: 2px solid #fff
}

/* 인풋 박스 스타일 */
.kw-input-number,
.cust-input .form-control {
  background: rgba(20, 40, 72, .6);
  border-color: #418EDE !important;
  color: #e7f3ff;
}

.cust-btn {
  border-color: #83A3BB !important;
  color: #fff !important;
  background: rgba(131, 163, 187, .3) !important;
}
</style>