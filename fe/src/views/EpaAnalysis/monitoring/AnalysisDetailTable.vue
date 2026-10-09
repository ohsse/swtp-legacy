<template>
  <b-card class="bg-transparent border-0 p-0 h-100" body-class="bg-transparent p-0 h-100">
    <div class="d-flex flex-column h-100">
      <SmallTitle :title="'관망해석 상세현황'" />

      <div class="custom-tbl mb-3" :class="{ 'scrollable-table': rows.length >= 5 }">
        <table class="table table-sm table-bordered align-middle mb-0">
          <thead>
            <tr>
              <th rowspan="2" scope="col">구분</th>
              <th colspan="4" scope="colgroup">유량(m³/h)</th>
              <th colspan="4" scope="colgroup">압력(kgf/cm²)</th>
            </tr>
            <tr>
              <th scope="col">상태</th>
              <th scope="col">계측값</th>
              <th scope="col">분석값</th>
              <th scope="col">오차율</th>
              <th scope="col">상태</th>
              <th scope="col">계측값</th>
              <th scope="col">분석값</th>
              <th scope="col">오차율</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.junction_id"
              :class="{ 'is-active': row.junction_id === internalActiveId }" @click="selRow(row)" tabindex="0"
              @keydown.enter="selRow(row)" style="cursor: pointer">
              <td>{{ row.name }}</td>
              <td>{{ row.flowStateText }}</td>
              <td>{{ nf(row.flowMeasured) }}</td>
              <td>{{ nf(row.flowAnalyzed) }}</td>
              <td>{{ pf(row.flowErrorRate) }}</td>
              <td>{{ row.pressureStateText }}</td>
              <td>{{ pnf(row.pressureMeasured) }}</td>
              <td>{{ pnf(row.pressureAnalyzed) }}</td>
              <td>{{ pf(row.pressureErrorRate) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- 하단 그래프 2열 (빈 영역) -->
      <div v-if="isChartLoading"
        class="border rounded-3 p-3 flex-fill d-flex align-items-center justify-content-center text-white-50"
        style="min-height: 200px; background: rgba(0,0,0,0.2);">

        <LoadingSpinner />
      </div>

      <b-row v-else class="g-3 flex-grow-1 min-h-0">

        <b-col v-if="isFlowChartVisible" :md="isPressureChartVisible ? 6 : 12" class="d-flex min-h-0">
          <div class="border rounded-3 p-3 flex-fill d-flex flex-column min-h-0">
            <div class="flex-grow-1 min-h-0">
              <AnalysisChart ref="flowChart" />
            </div>
          </div>
        </b-col>

        <b-col v-if="isPressureChartVisible" :md="isFlowChartVisible ? 6 : 12" class="d-flex min-h-0">
          <div class="border rounded-3 p-3 flex-fill d-flex flex-column min-h-0">
            <div class="flex-grow-1 min-h-0">
              <AnalysisChart ref="pressureChart" />
            </div>
          </div>
        </b-col>

        <b-col v-if="!isFlowChartVisible && !isPressureChartVisible" md="12">
          <div class="border rounded-3 p-3 flex-fill d-flex align-items-center justify-content-center text-white-50"
            style="min-height: 200px;">
            표시할 데이터가 없습니다.
          </div>
        </b-col>
      </b-row>
    </div>
  </b-card>
</template>

<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
import AnalysisChart from "@/views/EpaAnalysis/monitoring/AnalysisChart.vue";
import LoadingSpinner from '@/components/ComponentCommon/LoadingSpinner.vue';
import { fetchFunc } from '@/util/fetchFunc';
export default {
  name: "AnalysisDetailTable",
  components: { SmallTitle, AnalysisChart,LoadingSpinner },
  props: {
    rows: {
      type: Array,
      required: true,
    },
    activeId: {
      type: String,
      default: null,
    },
  },
  data() {
  return {
    initialChartLoaded: false, // 첫 차트가 로드되었는지 확인하는 플래그
    isFlowChartVisible: true,  // 유량 차트 표시 여부
    isPressureChartVisible: true, // 압력 차트 표시 여부
    isChartLoading: false,
    internalActiveId: null,
  };
  },
  watch: {
    rows(newRows) {
      // rows 데이터가 처음 들어오고, 아직 초기 차트를 로드하지 않았다면
      if (newRows && newRows.length > 0 && !this.initialChartLoaded) {
        // 첫 번째 행을 자동으로 선택하여 차트를 그립니다.
        this.selRow(newRows[0]);
        // 플래그를 true로 설정하여 다시 실행되지 않도록 합니다.
        this.initialChartLoaded = true;
      }
    }
  },
  methods: {
    // 부모에 있던 포매팅 함수를 가져옵니다.
    nf(n) {
      // totalFlowCalc와 동일
      return n == null ? "-" : Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });
    },
    pnf(n) {
      // minimum/maximumFractionDigits: 2 => toFixed(2)와 동일 (소수점 2자리)
      return n == null ? "-" : Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    pf(n) {
      // null 체크
      if (n == null) return "-";
      
      // 1(100%) 이상인 경우는 비정상 데이터로 간주
      if (Math.abs(n) == 1) return "-";
      
      const value = Number(n) * 100;
      
      // 값이 0이면 "0%"를 반환
      if (value === 0) return "0%";
      
      // 소수점 첫째 자리까지 계산
      const formatted = value.toFixed(1);
      
      // 소수점 이하가 0이면 정수부분만 표시
      return formatted.endsWith('.0') 
        ? Math.round(value) + "%" 
        : formatted + "%";
    },
    calculateArrayOrEmpty(calculationFn, ...arrays) {
      const allAreArrays = arrays.every(arr => Array.isArray(arr) && arr.length > 0);
      
      if (!allAreArrays) {
          return []; 
      }

      
      const firstLength = arrays[0].length;
      const allSameLength = arrays.every(arr => arr.length === firstLength);

      if (!allSameLength) {
          
          return []; 
      }

      
      return Array.from({ length: firstLength }, (value, i) => {
          
          const inputs = arrays.map(arr => arr[i]);
          return calculationFn(i, ...inputs);
      });
    },
    async selRow(row) {
      this.internalActiveId = row.junction_id
      // 1. 로딩 시작
      this.isChartLoading = true;

      // 2. 차트 보임/숨김 상태 먼저 결정
      this.isFlowChartVisible = row.flowStateText !== '-';
      this.isPressureChartVisible = row.pressureStateText !== '-';

      const junction_id = row.junction_id || null;
      if (!junction_id) {
        // ID가 없으면 로딩 즉시 종료
        this.isChartLoading = false;
        return;
      }
      
      // 3. API 호출 (이 시간 동안 로딩 스피너가 보임)
      const pythonURL = this.$pythonURL;
      const res = await fetchFunc(`${pythonURL}/api/web/monitoring/chart?junction_id=${junction_id}`);
      if (junction_id === "고산(정)유출") {
          // 통합 송수 계산
          const oldPump = await fetchFunc(`${pythonURL}/api/web/monitoring/chart?junction_id=335`);
          const newPump = await fetchFunc(`${pythonURL}/api/web/monitoring/chart?junction_id=11`);

          if (!oldPump || !newPump || !oldPump.data || !newPump.data) {
              // 데이터가 없어도 로딩 종료
              this.isChartLoading = false;
              return;
          }
          const pressureCal1 = 0.025268;
          const pressureCal2 = 0.968549;
          const pressureCalDefault = 0.064324;
          
          // 2. 데이터 추출
          const oldFlow = oldPump.data.flow;
          const newFlow = newPump.data.flow;
          const oldPressure = oldPump.data.pressure;
          const newPressure = newPump.data.pressure;
          

          // 3. 헬퍼 함수로 계산 (Vue 2.0 메서드로 호출)
          const combinedFlow = this.calculateArrayOrEmpty(
              (_, f1, f2) => f1 + f2, // 람다: 각 요소를 더함
              oldFlow,
              newFlow
          );

          const combinedPressure = this.calculateArrayOrEmpty(
              (_, p1, p2) => (p1 * pressureCal1) + (p2 * pressureCal2) + pressureCalDefault, // 람다: 공식 적용
              oldPressure,
              newPressure
          );

          
          res.data.flow = combinedFlow;
          res.data.pressure = combinedPressure;
          
      }
      if (!res || !res.data || !res.data.ts || res.data.ts.length === 0) {
        // 데이터가 없어도 로딩 종료
        this.isChartLoading = false;
        return;
      }

      const chartData = res.data;
      const xData = chartData.ts.map(timestamp => timestamp.substring(11, 16));

      // 4. [핵심] 로딩을 'false'로 설정
      //    (Vue가 v-else 블록(차트)을 그리도록 예약함)
      this.isChartLoading = false;

      // 5. [핵심] Vue가 차트를 DOM에 실제로 그릴 때까지 기다림
      await this.$nextTick(); 

      // 6. 이제 this.$refs.flowChart가 존재하므로 차트 초기화
      if (this.isFlowChartVisible && this.$refs.flowChart) {
        const yFlowData = [chartData.flow, chartData.epa_flow];
        this.$refs.flowChart.initChart(xData, yFlowData, "m³/h");
      }

      if (this.isPressureChartVisible && this.$refs.pressureChart) {
        const yPressureData = [chartData.pressure, chartData.epa_pressure];
        this.$refs.pressureChart.initChart(xData, yPressureData, "kgf/cm²");
      }
    },
  },
};
</script>

<style scoped>
/* 부모 컴포넌트에 있던 custom-tbl 관련 스타일을 그대로 가져옵니다. */
.custom-tbl th,
.custom-tbl td {
  border: 1px solid #405c8c;
  padding: 5px 8px;
  color: #fff;
  font-size: 16px;
  text-align: center;
  vertical-align: middle;
  background: rgba(0, 0, 0, 0.35);
}

.custom-tbl th {
  font-size: 18px;
  background: rgba(26, 44, 106, 1);
}

.custom-tbl tbody tr:hover,
.custom-tbl tbody tr.is-active {
  /* 활성 스타일 추가 */
  background: rgba(8, 80, 191, 1);
}

.custom-tbl tbody tr:hover td,
.custom-tbl tbody tr.is-active td {
  /* 활성 스타일 추가 */
  border: 1px solid #fff;
  border-top: 2px solid #fff;
}

/* 5줄 이상일 때 적용될 스크롤 스타일 */
.scrollable-table {
  max-height: 250px;
  overflow-y: auto;
}

/* a a a a모든 thead th에 공통으로 sticky 속성 적용 */
.scrollable-table thead th {
  position: sticky;
  z-index: 1;
  background: rgba(26, 44, 106, 1);
}

/* a a a a첫 번째 헤더 줄(tr)의 th들은 맨 위에 고정 */
.scrollable-table thead tr:first-child th {
  top: 0;
  /* z-index를 더 높게 주어 다른 헤더 셀 위에 위치하도록 보장 */
  z-index: 2;
}

/* a a a a두 번째 헤더 줄(tr)의 th들은 첫 번째 줄 높이만큼 아래에 고정 */
.scrollable-table thead tr:nth-child(2) th {
  /* 이 값은 첫 번째 헤더 줄의 실제 높이와 같아야 합니다. 
    개발자 도구(F12)로 높이를 확인하고 정확한 값으로 조절하세요.
  */
  top: 38px;
}

/* 테이블의 border 처리 방식을 변경하여 sticky 틈새 문제 해결 */
.scrollable-table table {
  border-collapse: separate;
  border-spacing: 0;
}

/* 1. 남아있는 요소가 이동할 때 애니메이션 (너비 변경)
  이것이 너비가 50% -> 100%로 부드럽게 변경되는 핵심입니다.
*/
.chart-shuffle-move {
  /* Bootstrap grid는 width, max-width, flex-basis를 사용합니다.
    이 속성들을 transition 대상으로 지정합니다.
  */
  transition: width 0.4s ease-in-out,
    max-width 0.4s ease-in-out,
    flex-basis 0.4s ease-in-out;
}

/* 2. 요소가 나타나거나 사라질 때 페이드 효과 (v-if) 
*/
.chart-shuffle-leave-active,
.chart-shuffle-enter-active {
  transition: opacity 0.3s ease;
}

.chart-shuffle-enter-from,
.chart-shuffle-leave-to {
  opacity: 0;
}

/* 사라지는 요소가 레이아웃을 망가뜨리지 않도록
  애니메이션 동안 absolute로 띄워줍니다. 
*/
.chart-shuffle-leave-active {
  position: absolute;
}
</style>