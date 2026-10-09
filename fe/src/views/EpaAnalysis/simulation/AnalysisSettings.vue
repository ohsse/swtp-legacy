<template>
  <b-card class="bg-transparent border-0 p-0" body-class="bg-transparent p-0">
    <SmallTitle :title="'관망해석 설정'" />

    <b-row class="d-flex flex-column px-2 gap-2 mt-2">
      <b-col>
        <b-row class="d-flex align-items-center justify-content-between">
          <b-col md="4" class="d-flex align-items-center gap-2">
            <img src="@/assets/img/pressure.png" alt="아이콘" class="icon" />
            <span class="cal-title-font text-white">정수장 토출 유량 설정</span>
          </b-col>
          <b-col md="8" class="d-flex justify-content-end">
            <b-button variant="outline-light" size="sm" class="cust-btn" data-bs-toggle="modal"
                      data-bs-target="#multiInflowModal">
              배수지 수요량 설정
            </b-button>
          </b-col>
        </b-row>
      </b-col>
      <b-col>
        <b-row class="px-1">
          <b-col class="mt-0">
            <b-input-group class="cust-input">
              <b-form-input v-model="flowValue" type="number" placeholder="유량 입력" @input="handleFlowInput" />
              <b-input-group-append>
                <b-button variant="primary" class="btn-apply" @click="clickPumpFlow">
                  입력
                </b-button>
              </b-input-group-append>
            </b-input-group>
          </b-col>
        </b-row>
      </b-col>
      <b-col>
        <b-row class="px-1">
          <b-col class="d-flex justify-content-end">
            <div class="glow-value d-flex align-items-center gap-5">
              <span class="cal-title-font fs-3">정수장 토출 유량 </span>
              <div class="position-relative d-inline-block">
                <span class="glow-num lh-1">{{ totalFlowCalc(pumpFlow) }}</span>
                <span class="cal-title-font fs-5 ms-1">m³/h</span>
              </div>
            </div>
          </b-col>
        </b-row>
      </b-col>
    </b-row>

    <b-row class="d-flex flex-column px-2 gap-2 mt-3">
      <b-col>
        <b-row class="d-flex align-items-center">
          <b-col md="4" class="d-flex align-items-center gap-2">
            <img src="@/assets/img/pressure.png" alt="아이콘" class="icon" />
            <span class="cal-title-font text-white">펌프 선택</span>
          </b-col>
        </b-row>
      </b-col>

      <b-col class="flex-shrink-0 px-3">
        <div class="custom-tbl table-responsive mb-0 scrollable-table">
          <table class="table table-sm table-bordered align-middle mb-0">
            <thead>
            <tr>
              <th style="width:36px;"></th>
              <th style="width:100px;">순번</th>
              <template v-if="splitOldNew">
                <th>구펌프</th>
                <th>신펌프</th>
              </template>
              <th v-else>펌프</th>
              <th style="width:140px;">펌프주파수</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="(combo, index) in displayCombinations" :key="combo.id || `empty-${index}`">
              <template v-if="combo.id">
                <td>
                  <div class="form-check m-0">
                    <input
                        class="form-check-input cust-radio"
                        type="checkbox"
                        :id="'combo' + combo.id"
                        :checked="isComboChecked(combo)"
                        @change="toggleCombo(combo)"
                    >
                  </div>
                </td>
                <td>{{ combo.id }}</td>
                <template v-if="splitOldNew">
                  <td>
                    <div class="d-flex flex-wrap justify-content-center gap-2">
                      <span v-for="pump in combo.oldPumps" :key="pump" class="kw-chip">{{ pump }}</span>
                    </div>
                  </td>
                  <td>
                    <div class="d-flex flex-wrap justify-content-center gap-2">
                      <span v-for="pump in combo.newPumps" :key="pump" class="kw-chip">{{ pump }}</span>
                    </div>
                  </td>
                </template>
                <td v-else>
                  <div class="d-flex flex-wrap justify-content-center gap-2">
                    <span v-for="pump in combo.pumps" :key="pump" class="kw-chip">{{ pump }}</span>
                  </div>
                </td>
                <td>
                  <div class="d-flex align-items-center justify-content-center gap-1">
                    <b-form-input
                        :model-value="getPumpFrequency(combo)"
                        type="number"
                        number
                        :min="MIN_PUMP_HZ"
                        :max="MAX_PUMP_HZ"
                        step="0.1"
                        class="pump-frequency-input"
                        @update:model-value="setPumpFrequency(combo, $event)"
                        @click.stop
                    />
                    <span class="freq-unit">Hz</span>
                  </div>
                </td>
              </template>
              <template v-else>
                <td v-for="n in colCount" :key="n">&nbsp;</td>
              </template>
            </tr>
            </tbody>
          </table>
        </div>
      </b-col>

      <div class="text-end mt-2">
        <b-button variant="primary" class="btn-apply" @click="executeAnalysis">
          펌프 적용 및 실행
        </b-button>
      </div>
    </b-row>

  </b-card>
</template>

<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";

// 고산 TB_PUMP_CAL 기준 신펌프 시작 번호.
// PUMP_IDX 1~7 = (구)송수펌프, 8~11 = (신)송수펌프.
// 출처: views/Setting/SongsuPumpOperationGosan.vue:163-179
const NEW_PUMP_FROM = 8;
const FIXED_PUMP_NUMBERS = [1, 2, 3, 4];

// 군산 송수펌프 호기 번호. 해석 엔진의 PUMPS 상수와 1:1이다
// (epa/epanet_gunsan/epanet_si_gs.py:77-82 — 군산(정)1~4).
// 엔진이 1~4 밖의 번호를 거부하므로 이 배열을 늘리려면 엔진 쪽이 먼저 바뀌어야 한다.
const GUNSAN_PUMP_NUMBERS = [1, 2, 3, 4];

// 인버터 주파수 허용 범위. 엔진 parse_pump_hz 의 검증과 같은 값이다
// (epanet_si_gs.py:583-584). 여기서 먼저 막아야 운영자가 500 대신 즉시 안내를 본다.
const MIN_PUMP_HZ = 1;
const MAX_PUMP_HZ = 60;

export default {
  name: 'AnalysisSettings',
  components: {
    SmallTitle,
  },
  props: {
    totalFlow: {
      type: String,
      default: '0'
    },
    tanks: {
      type: Array,
      default: () => []
    },
    pumpCal: {
      type: Array,
      default: () => []
    }
  },
  emits: ['execute'],
  data() {
    return {
      // 유량 설정 관련 데이터
      selectedReservoir: '', // watch에서 초기화되므로 빈 값으로 시작
      flowValue: '',
      // 펌프 조합 관련 데이터
      // 고산: 조합 1건만 고르는 단일 선택(selectedCombination)
      // 군산: 호기를 여러 개 체크하는 다중 선택(selectedPumpNos) — 엔진이 --pump-comb "1,3"
      //       처럼 조합을 그대로 받기 때문이다. 두 현장이 선택 모델 자체가 달라 state 를 나눴다.
      selectedCombination: 1,
      selectedPumpNos: [],
      pumpFrequencyByCombinationKey: {},
      // tanks 초기화 완료 플래그 (초기 한 번만 watcher 동작하도록)
      tanksInitDone: false,
      pumpFlow: 0
    };
  },
  computed: {
    // 고산만 구·신 펌프를 나눈다.
    // 군산은 단일 계통(TB_PUMP_CAL에 PUMP_GRP=1 하나)이라 구분 자체가 없다.
    // 부모 EpaAnalysisSimulation.vue:80 pumpGrp()와 같은 분기 축($area)을 쓴다.
    splitOldNew() {
      return this.$area === 'gosan';
    },
    // 군산은 펌프 다중선택 + 호기별 Hz 를 엔진에 그대로 넘긴다.
    // 고산은 조합 단일선택이고 Hz 개념 자체가 없다([RULES] 의 STATUS OPEN/CLOSED 뿐).
    isGunsan() {
      return this.$area === 'gunsan';
    },
    // 템플릿의 입력 범위(min/max)에 쓰려고 모듈 상수를 인스턴스에 노출한다.
    MIN_PUMP_HZ() {
      return MIN_PUMP_HZ;
    },
    MAX_PUMP_HZ() {
      return MAX_PUMP_HZ;
    },
    // 빈 행 패딩용 컬럼 수 (선택 + 순번 + 펌프컬럼 + 펌프주파수)
    colCount() {
      return this.splitOldNew ? 5 : 4;
    },
    // totalFlow 값에 따라 pumpCal 데이터를 필터링하고 가공
    filteredPumpCombinations() {
      // 군산은 TB_PUMP_CAL 과 유량 밴드를 쓰지 않는다 — 엔진이 --pump-comb 로 펌프를
      // 직접 지정받기 때문이다(epa_service_gunsan.py 의 docstring 참조).
      // 그래서 유량 입력 여부·DB 조회 결과와 무관하게 1~4호기를 항상 보여준다.
      // (기존에는 pumpCal 이 비거나 유량 범위가 안 맞으면 표 전체가 사라져 펌프를
      //  아예 고를 수 없었다.)
      if (this.isGunsan) {
        return GUNSAN_PUMP_NUMBERS.map(pumpNo => ({
          id: pumpNo,
          pumpNo,
          pumps: [pumpNo],
          oldPumps: [],
          newPumps: []
        }));
      }

      // 조합 필터의 기준값은 아래 pumpFlow(사용자가 [입력]으로 확정한 유량)다.
      // 배수지 수요량 합계인 totalFlow는 이 판단과 무관하므로 가드에서 뺀다 —
      // 군산은 TB_EPA_SIM_RESV_FLOW가 비어 tanks=[] → totalFlow=0 이라
      // 유량을 무엇으로 넣든 표 전체가 사라졌다. 유량 검증은 아래 isNaN(currentFlow)가 맡는다.
      if (!this.pumpCal || this.pumpCal.length === 0) {
        return [];
      }

      const currentFlow = parseFloat(String(this.pumpFlow).replace(/,/g, ''));
      if (isNaN(currentFlow)) return [];

      // 그룹 키: C_IDX + COUNT_IDX (같은 C_IDX 안의 여러 COUNT_IDX를 구분)
      const groups = this.pumpCal.reduce((acc, item) => {
        const key = `${item.C_IDX}_${item.COUNT_IDX}`;
        if (!acc[key]) acc[key] = { items: [], C_IDX: item.C_IDX, COUNT_IDX: item.COUNT_IDX };
        acc[key].items.push(item);
        return acc;
      }, {});

      // 각 그룹에서 현재 유량 범위에 맞는 기준 설정만 추출
      const candidates = Object.values(groups).map(group => {
        const items = group.items;
        const minConfig = items.find(i => Number(i.C_ORD) === 1);
        console.log("🚀 ~ minConfig:", minConfig)
        const maxConfig = items.find(i => Number(i.C_ORD) === 2);

        if (!minConfig || !maxConfig) return null;

        const minFlow = Number(minConfig.FC_VAL) || 0;
        const maxFlow = Number(maxConfig.FC_VAL) || 0;
        if (currentFlow < minFlow || currentFlow > maxFlow) return null;

        return {
          C_IDX: group.C_IDX,
          COUNT_IDX: group.COUNT_IDX,
          _minFlow: minFlow,
          _maxFlow: maxFlow,
          unit: minConfig.PWR_UNIT_COST,
          rawMinConfig: minConfig
        };
      }).filter(Boolean);

      // 최소유량 기준 오름차순 정렬
      candidates.sort((a, b) => a._minFlow - b._minFlow);
      const baseCandidate = candidates[0];

      if (!baseCandidate) {
        return [];
      }

      return FIXED_PUMP_NUMBERS.map((pumpNo, idx) => ({
        id: idx + 1,
        C_IDX: baseCandidate.C_IDX,
        COUNT_IDX: baseCandidate.COUNT_IDX,
        pumpNo,
        pumps: [pumpNo],
        oldPumps: pumpNo < NEW_PUMP_FROM ? [pumpNo] : [],
        newPumps: pumpNo >= NEW_PUMP_FROM ? [pumpNo] : [],
        total: '1대',
        unit: baseCandidate.unit,
        _minFlow: baseCandidate._minFlow,
        _maxFlow: baseCandidate._maxFlow,
        rawMinConfig: {
          ...baseCandidate.rawMinConfig,
          PUMP_COMB: String(pumpNo),
          PUMP_COUNT: 1
        }
      }));
    },

    // 기존 displayCombinations 로직 유지
    displayCombinations() {
      const minRows = FIXED_PUMP_NUMBERS.length;
      const currentRows = this.filteredPumpCombinations.length;

      if (currentRows >= minRows) {
        return this.filteredPumpCombinations;
      }

      const emptyRows = Array(minRows - currentRows).fill({});
      return [...this.filteredPumpCombinations, ...emptyRows];
    }
  },
  watch: {
    tanks: {
      handler(newVal) {
        // 이미 초기화가 끝났으면 더 이상 동작하지 않음
        if (this.tanksInitDone) return;

        if (newVal && newVal.length > 0) {
          this.selectedReservoir = newVal[0].TNK_NM;
          this.flowValue = newVal[0].FLOW_RATE || 0;
        } else {
          this.selectedReservoir = '';
          this.flowValue = 0;
        }

        // 최초 한 번만 실행되도록 플래그 설정
        this.tanksInitDone = true;
      },
      immediate: true
    },
    // filteredPumpCombinations가 변경될 때마다 선택된 조합을 첫 번째로 초기화
    filteredPumpCombinations: {
      handler(newVal) {
        // 군산은 목록이 1~4호기로 고정이라 "유량이 바뀌어 조합이 갈렸다"는 전제가 성립하지
        // 않는다. 여기서 되돌리면 운영자가 체크할 때마다 선택이 1호기로 리셋된다.
        if (this.isGunsan) return;

        if (newVal && newVal.length > 0) {
          this.selectedCombination = newVal[0].id;
        } else {
          this.selectedCombination = null;
        }
      },
      immediate: true
    }
  },
  methods: {
    // 해당 행이 체크된 상태인지. 고산은 단일 선택, 군산은 다중 선택이라 축이 다르다.
    isComboChecked(combo) {
      if (this.isGunsan) {
        return this.selectedPumpNos.includes(combo.pumpNo);
      }
      return this.selectedCombination === combo.id;
    },
    selectCombination(comboId) {
      this.selectedCombination = this.selectedCombination === comboId ? null : comboId;
    },
    // 군산 전용: 호기를 켜고 끈다. 배열을 새로 만들어 반응성을 확실히 잡는다.
    togglePumpNo(pumpNo) {
      this.selectedPumpNos = this.selectedPumpNos.includes(pumpNo)
          ? this.selectedPumpNos.filter(n => n !== pumpNo)
          : [...this.selectedPumpNos, pumpNo].sort((a, b) => a - b);
    },
    toggleCombo(combo) {
      if (this.isGunsan) {
        this.togglePumpNo(combo.pumpNo);
      } else {
        this.selectCombination(combo.id);
      }
    },
    comboKey(combo) {
      if (!combo) return '';
      // 군산 행에는 C_IDX/COUNT_IDX 가 없다(TB_PUMP_CAL 을 안 쓴다).
      // 호기 번호만으로 키가 유일하므로 그것만 쓴다.
      if (this.isGunsan) return `gunsan_${combo.pumpNo}`;
      return `${combo.C_IDX}_${combo.COUNT_IDX}_${combo.pumpNo || combo.id}`;
    },
    normalizePumpFrequencyInput(value) {
      const rawValue = value && value.target ? value.target.value : value;

      if (rawValue === '' || rawValue == null) {
        return '';
      }

      const numberValue = Number(rawValue);
      if (!Number.isFinite(numberValue)) return '';
      // 엔진과 같은 범위(1~60)로 막는다. 범위를 벗어난 값은 저장하지 않고 비운다 —
      // 통과시키면 해석이 500 으로 죽고 원인이 화면에 안 보인다.
      if (numberValue < MIN_PUMP_HZ || numberValue > MAX_PUMP_HZ) return '';
      return numberValue;
    },
    getPumpFrequency(combo) {
      const value = this.pumpFrequencyByCombinationKey[this.comboKey(combo)];
      return value ?? '';
    },
    setPumpFrequency(combo, value) {
      const key = this.comboKey(combo);
      if (!key) return;

      this.pumpFrequencyByCombinationKey = {
        ...this.pumpFrequencyByCombinationKey,
        [key]: this.normalizePumpFrequencyInput(value)
      };
    },
    /**
     * 군산 전용: 체크된 호기와 Hz 를 서버 형식으로 모은다.
     * 문제가 있으면 { error: '...' } 를 돌려준다.
     * 반환 형태는 [{ pumpNo, hz }] — 엔진 CLI 형식("1:55,3:52")은 서버 어댑터가 만든다.
     */
    collectGunsanPumps() {
      if (this.selectedPumpNos.length === 0) {
        return { error: '가동할 펌프를 최소 1대 선택하세요.' };
      }

      const pumps = [];
      const invalid = [];
      for (const pumpNo of this.selectedPumpNos) {
        const combo = this.filteredPumpCombinations.find(c => c.pumpNo === pumpNo);
        const hz = this.normalizePumpFrequencyInput(this.getPumpFrequency(combo));
        if (hz === '') {
          invalid.push(pumpNo);
          continue;
        }
        pumps.push({ pumpNo, hz });
      }

      if (invalid.length > 0) {
        return {
          error: `${invalid.join(', ')}호기의 펌프주파수를 ${MIN_PUMP_HZ}~${MAX_PUMP_HZ} Hz 범위로 입력하세요.`
        };
      }
      return { pumps };
    },
    // "조합 적용 및 실행" 버튼 클릭 시 호출될 메소드
    executeAnalysis() {
      // 군산은 여기서 끝난다. 아래 고산 경로(TB_PUMP_CAL 조합 + 유량 밴드)는 타지 않는다.
      // 서버는 settings.pumps 가 있으면 그걸 쓰고, 없으면 기존 selectedCombo 경로로
      // 떨어진다(epa/app/routes/epa_routes.py 의 _parse_selected_pumps).
      if (this.isGunsan) {
        const collected = this.collectGunsanPumps();
        if (collected.error) {
          alert(collected.error);
          return;
        }
        this.$emit('execute', {
          pumps: collected.pumps,
          selectedCombo: null,
          pumpFrequency: null,
          minFlow: null,
          maxFlow: null
        });
        return;
      }

      const selectedCombo = this.filteredPumpCombinations.find(
          combo => combo.id === this.selectedCombination
      );
      const pumpFrequency = selectedCombo
          ? this.normalizePumpFrequencyInput(this.getPumpFrequency(selectedCombo))
          : null;
      const selectedComboWithFrequency = selectedCombo
          ? {
            ...selectedCombo,
            pumpFrequency: pumpFrequency === '' ? null : pumpFrequency
          }
          : null;

      const settings = {
        selectedCombo: selectedComboWithFrequency,
        pumpFrequency: selectedComboWithFrequency ? selectedComboWithFrequency.pumpFrequency : null,
        // 최소/최대 유량도 함께 전달
        minFlow: selectedCombo ? Number(selectedCombo._minFlow) : null,
        maxFlow: selectedCombo ? Number(selectedCombo._maxFlow) : null
      };

      this.$emit('execute', settings);
    },
    handleFlowInput(value) {
      // 1. (요청 2, 3) 소수점, 문자, 음수 등 숫자 이외의 값을 모두 제거
      //    (value가 null일 수 있으므로 (value || '')로 방어)
      const sanitizedValue = (value || '').toString().replace(/[^\d]/g, '');

      let finalValue;

      // 2. (요청 1) 값이 비어있으면 '0'을,
      //    값이 있으면 (e.g., '05' -> 5) 숫자로 변환 후 문자로 되돌림
      if (sanitizedValue === '') {
        finalValue = '0';
      } else {
        finalValue = Number(sanitizedValue).toString();
      }

      // 3. $nextTick을 사용해 v-model(flowValue) 값을 업데이트 (커서 점프 방지)
      this.$nextTick(() => {
        this.flowValue = finalValue;
      });

      // 4. 부모 컴포넌트에는 '정리된' 값을 전달 (기존 value -> finalValue)
      // this.$emit('oneInputFlow', this.selectedReservoir, finalValue);
    },
    clickPumpFlow() {
      this.pumpFlow = this.flowValue;
    },
    totalFlowCalc(flow) {
      // maximumFractionDigits: 0 => toFixed(0)와 동일 (소수점 0자리, 반올림)
      return flow == null ? "-" : Number(flow).toLocaleString(undefined, { maximumFractionDigits: 0 });
    }
  },
};
</script>

<style scoped>
.cust-btn {
  border-color: #83A3BB !important;
  color: #fff !important;
  background: rgba(131, 163, 187, .3) !important
}

.glow-value {
  display: flex;
  align-items: baseline;
  gap: 6px
}

.glow-num {
  font-size: 30px;
  font-family: LAB디지털 !important;
  line-height: 1;
  color: #fff;
  font-weight: 400;
  letter-spacing: .06em;
  text-shadow: 0 0 8px rgba(144, 195, 255, .9), 0 0 18px rgba(144, 195, 255, .45), 0 0 32px rgba(144, 195, 255, .25)
}

.cust-input .form-control {
  background: rgba(20, 40, 72, .6);
  border-color: #418EDE !important;
  color: #e7f3ff
}

.cust-input .form-control:focus {
  border-color: #5fb1ff;
  box-shadow: 0 0 0 .15rem rgba(95, 177, 255, .25)
}

.date_design {
  background-color: #15284e;
  border-color: #418EDE !important;
  color: #fff;
  font-size: 13px;
  font-family: KHNPHDRegular;
  border-radius: 5px;
  padding-right: 30px;
  /* 화살표 이미지와 텍스트가 겹치지 않도록 여백 추가 */

  /* [수정] 브라우저 기본 화살표 숨기기 */
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
}


/* 숫자 입력 필드 스피너 제거 */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0
}

input[type=number] {
  -moz-appearance: textfield
}

/* 펌프 조합 테이블 스타일 */
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

.kw-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 26px;
  border-radius: 999px;
  background: #174D9e;
  color: #fff;
  font-weight: 700
}

.cust-radio {
  width: 1.1rem;
  height: 1.1rem;
  background-color: transparent;
  border: 1px solid #76A4F1;
  float: unset !important;
  cursor: pointer
}

.cust-radio:checked {
  border-color: #51b2ff;
  box-shadow: unset !important
}

.cust-radio:active,
.cust-radio:focus {
  box-shadow: unset !important
}

.pump-frequency-input {
  width: 82px;
  height: 30px;
  padding: 2px 8px;
  text-align: right;
  background: rgba(20, 40, 72, .6);
  border: 1px solid #418EDE;
  color: #fff;
  font-size: 14px
}

.pump-frequency-input:focus {
  background: rgba(20, 40, 72, .75);
  border-color: #5fb1ff;
  color: #fff;
  box-shadow: 0 0 0 .15rem rgba(95, 177, 255, .25)
}

.freq-unit {
  color: #d8e7ff;
  font-size: 13px
}

.btn-apply {
  color: #fff;
  background: #0B63B0;
  padding: .6rem 1.2rem;
  font-weight: 600;
  height: 42px;
  border: 0
}

/* 스크롤 및 높이 제어 */
.scrollable-table {
  max-height: 147px;
  overflow-y: auto;
}

.scrollable-table::-webkit-scrollbar {
  width: 8px;
}

.scrollable-table::-webkit-scrollbar-thumb {
  background-color: #418EDE;
  border-radius: 4px;
}

.scrollable-table::-webkit-scrollbar-track {
  background-color: rgba(0, 0, 0, 0.35);
}
</style>
