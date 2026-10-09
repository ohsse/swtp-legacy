<template>
  <LoadingSpinner class="loading-container" v-if="isLoading" />
  <div class="container-fluid">
    <!-- 템플릿 내용 -->
    <!-- 타이틀 -->
    <b-row>
      <b-col xl="4">
        <BigTitle :title="'관망해석 모니터링'" />
      </b-col>
      <b-col xl="5" class="d-flex align-items-center"></b-col>
      <b-col xl="3" class="d-flex align-items-center justify-content-end">
        <MonitorMode :value="'monitor'" @change="onModeChange" />
      </b-col>
    </b-row>
    <!-- //타이틀 -->
    <!-- 본문 컨텐츠 -->
    <div class="contents-container" style="height: calc(100% - 100px);">
      <b-row class="h-100" style="margin-top: 15px">
        <b-col class="area" :xl="isMapFullscreen ? 12 : 5" style="position:relative; padding-right : 15px;">
          <MapComponent :isFullscreen="isMapFullscreen" @toggle-fullscreen="toggleMapFullscreen"
            style="width: 100%; height: 100%; border: 1px solid #dcdcdc;" :isShowPin="true" :nodes="nodes"
            :time-text="displayTime" />
        </b-col>
        <keep-alive>
          <b-col v-if="!isMapFullscreen" xl="7" class="d-flex flex-column gap-4">
            <AnalysisStatus :flow-data="status.flow" :pressure-data="status.pressure" />
            <AnalysisDetailTable :rows="mapRows" :active-id="activePointId" @row-click="onRowClick" />
          </b-col>
        </keep-alive>
      </b-row>
    </div>
    <optionVue />
  </div>
</template>
<script>
    import BigTitle from '@/components/ComponentCommon/BigTitle.vue';
    import MapComponent from '@/components/Map/MapComponent.vue';
    import MonitorMode from '@/views/Common/MonitorMode.vue';
    import LoadingSpinner from '@/components/ComponentCommon/LoadingSpinner.vue';
    import { fetchFunc } from '@/util/fetchFunc';

    
    import AnalysisStatus from '@/views/EpaAnalysis/monitoring/AnalysisStatus.vue';
    import AnalysisDetailTable from '@/views/EpaAnalysis/monitoring/AnalysisDetailTable.vue';
export default {
    name: "EpaAnalysisMonitoring",
    components: {
        BigTitle,
        MapComponent,
        MonitorMode,
        AnalysisStatus,
        AnalysisDetailTable,
        LoadingSpinner
    },
    data(){
      return{
        activePointId: null,  // 현재 열린 지도 팝업 id
              // 전체 화면 상태를 관리하는 데이터 추가
        isMapFullscreen: false,
        // 지도 좌표/상태(아이디는 테이블과 동일)
        status: {
            flow: {
                good: { count: 39, percent: 94 },
                normal: { count: 6, percent: 4 },
                bad: { count: 3, percent: 2 },
            },
            pressure: {
                good: { count: 42, percent: 96 },
                normal: { count: 1, percent: 2 },
                bad: { count: 1, percent: 2 },
            },
        },
        nodes:{},
        mapNodes:{},
        // 테이블 데이터(지도와 id/name 매칭)
        detailRows: [
        ],
        mapRows: [
        ],
        displayTime: '모니터링 시각 : 2025-10-21 18:31:00',
        rawDataInterval: null,
      };
    },
    created() {
      this.settingData();
    },
    mounted(){
      this.getRawData();

      const fiveMinutesInMs = 5 * 60 * 1000;
      this.rawDataInterval = setInterval(this.getRawData, fiveMinutesInMs);

    },
    beforeUnmount() {

      // 4. 컴포넌트가 사라지기 전에 인터벌 정리 (메모리 누수 방지)
      if (this.rawDataInterval) {
        clearInterval(this.rawDataInterval);
      }
    },
    methods:{
      onRowClick(row) {
        this.activePointId = row.id;
      },
      nf(n) {
        // totalFlowCalc와 동일
        return n == null ? "-" : Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });
      },
      pnf(n) {
        // minimum/maximumFractionDigits: 2 => toFixed(2)와 동일 (소수점 2자리)
        return n == null ? "-" : Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      },
      pf(n) {
        // 100을 곱한 값에 콤마 + 소수점 0자리 + "%"
        return n == null ? "-" : Number(Number(n) * 100).toLocaleString(undefined, { maximumFractionDigits: 0 }) + "%";
      },
      toggleMapFullscreen() {
        this.isMapFullscreen = !this.isMapFullscreen;
      },
      async settingData(){
        
        const pythonURL = this.$pythonURL;
        const setNodes = (await fetchFunc(`${pythonURL}/api/web/nodes`)).data
        
        
        this.nodes = setNodes.map(element => {
    
            if (element.JUNCTION_ID === "10") {
                
                return {
                    ...element,       
                    PIPE_ID: "p_10" 
                };
            }
            
            
            return element; 
        });
      },
      // EpaAnalysisMonitoring.vue의 methods 안에 getRawData 함수를 교체

// EpaAnalysisMonitoring.vue의 methods 안에 getRawData 함수를 교체

      async getRawData() {
        
        
        this.isLoading = true;
        const pythonURL = this.$pythonURL;
        const res = await fetchFunc(`${pythonURL}/api/web/monitoring`);
        
        if (!res || !res.data) return;
        
        const rawData = res.data.raw;
        
        // 고산 통합 유량 및 압력 계산
        const pressureCal1 = 0.025268;
        const pressureCal2 = 0.968549;
        const pressureCalDefault = 0.064324;
        const flow1 = rawData['701-367-FRI-4001'];
        const flow2 = rawData['701-367-FRI-4004'];
        const pressure1 = rawData['701-367-PRI-4010'];
        const pressure2 = rawData['701-367-PRI-4019'];

        // flow1과 flow2가 둘 다 null이 아니면(true) 합계를, 아니면(false) 0을 할당
        rawData['gosan_all_fri'] = (flow1 != null && flow2 != null) 
            ? (flow1 + flow2) 
            : 0;

        // pressure1과 pressure2가 둘 다 null이 아니면(true) 공식을, 아니면(false) 0을 할당
        rawData['gosan_all_pri'] = (pressure1 != null && pressure2 != null) 
            ? ((pressure1 * pressureCal1) + (pressure2 * pressureCal2) + pressureCalDefault) 
            : 0;



        this.displayTime = `모니터링 시각 : ${res.data.ts}`;
        const updatedNodes = this.nodes
        .filter(node => node.IS_DISPLAY == 1)
        .map(node => {
          // 1. rawData에서 원본 값을 가져옴
          const originalFlowMeasured = rawData[node.FRI_TAG];
          const originalFlowAnalyzed = rawData[node.PIPE_ID];
          const originalPressureMeasured = rawData[node.PRI_TAG];
          const originalPressureAnalyzed = rawData[node.JUNCTION_ID];

          // 2. 원본 값을 사용해 상태를 먼저 계산
          //    calculateStatus 함수는 null을 'bad'로, undefined를 'none'
          const { error: flowError, status: flowStatus } = this.calculateStatus(originalFlowMeasured, originalFlowAnalyzed);
          const { error: pressureError, status: pressureStatus } = this.calculateStatus(originalPressureMeasured, originalPressureAnalyzed);

          // 3. null이면 0
          const displayFlowMeasured = originalFlowMeasured === null ? 0 : originalFlowMeasured;
          const displayFlowAnalyzed = originalFlowAnalyzed === null ? 0 : originalFlowAnalyzed;
          const displayPressureMeasured = originalPressureMeasured === null ? 0 : originalPressureMeasured;
          const displayPressureAnalyzed = originalPressureAnalyzed === null ? 0 : originalPressureAnalyzed;
          
          
          let overallStatus;
          if (flowStatus === 'bad' || pressureStatus === 'bad') {
            overallStatus = 'bad';
          } else if (flowStatus === 'normal' || pressureStatus === 'normal') {
            overallStatus = 'normal';
          } else {
            overallStatus = 'good';
          }
          

          return {
            ...node,
            flowMeasured: displayFlowMeasured,
            flowAnalyzed: displayFlowAnalyzed,
            flowError,
            flowStatus,
            pressureMeasured: displayPressureMeasured,
            pressureAnalyzed: displayPressureAnalyzed,
            pressureError,
            pressureStatus,
            status: overallStatus,
          };
        });

       
        this.nodes = updatedNodes;
        
        
        // 현황 및 상세현황
        this.detailRows = updatedNodes
        .filter(node => node.IS_DISPLAY == 1)
        .map(node => ({
          junction_id: node.JUNCTION_ID,
          pipe_id: node.PIPE_ID,
          name: node.LOCATION_NM,
          flowStateText: this.getStatusText(node.flowStatus),
          flowMeasured: node.flowMeasured,
          flowAnalyzed: node.flowAnalyzed,
          flowErrorRate: node.flowError,
          pressureStateText: this.getStatusText(node.pressureStatus),
          pressureMeasured: node.pressureMeasured,
          pressureAnalyzed: node.pressureAnalyzed,
          pressureErrorRate: node.pressureError,
        }));
        console.log("🚀 ~ this.detailRows:", this.detailRows)
        this.mapRows = updatedNodes
        .map(node => ({
          junction_id: node.JUNCTION_ID,
          pipe_id: node.PIPE_ID,
          name: node.LOCATION_NM,
          flowStateText: this.getStatusText(node.flowStatus),
          flowMeasured: node.flowMeasured,
          flowAnalyzed: node.flowAnalyzed,
          flowErrorRate: node.flowError,
          pressureStateText: this.getStatusText(node.pressureStatus),
          pressureMeasured: node.pressureMeasured,
          pressureAnalyzed: node.pressureAnalyzed,
          pressureErrorRate: node.pressureError,
        }));
        
        // 상태
        this.status = {
          flow: this.calculateStatusSummary(updatedNodes, 'flowStatus'),
          pressure: this.calculateStatusSummary(updatedNodes, 'pressureStatus'),
        };
        this.isLoading = false;
      },
      /**
       * 계측값과 분석값으로 상태를 계산하는 최종 함수
       * @param {number | null | undefined} measured - 계측값
       * @param {number | null | undefined} analyzed - 분석값
       * @returns {{error: number|null, status: 'good'|'normal'|'bad'|'none'}}
       */
      calculateStatus(measured, analyzed) {
        const isMeasuredInvalid = measured === undefined || measured === null || isNaN(Number(measured));
        const isAnalyzedInvalid = analyzed === undefined || analyzed === null || isNaN(Number(analyzed));

        // 1. [핵심 수정] 두 값 모두 유효하지 않을 때만 'none'
        //    (예: FRI_TAG와 PIPE_ID가 모두 없어서 measured와 analyzed가 둘 다 undefined인 경우)
        if (isMeasuredInvalid && isAnalyzedInvalid) {
          return { error: null, status: 'none' };
        }

        // 2. [핵심 수정] 둘 중 하나라도 유효하지 않으면 'bad' (미흡)
        if (isMeasuredInvalid || isAnalyzedInvalid) {
          return { error: null, status: 'bad' };
        }
        
        // --- 이하 로직은 두 값이 모두 유효한 숫자일 때만 실행됩니다 ---

        // 3. 계측값이 0이면 오차율 계산이 불가하므로 별도 처리
        if (Number(measured) === 0) {
          // 분석값도 0이면 오차 없음('적합'), 아니면 '미흡'
          const status = Number(analyzed) === 0 ? 'good' : 'bad';
          return { error: Number(analyzed) === 0 ? 0 : null, status: status };
        }

        // 4. 두 값 모두 유효한 숫자이면 오차율 계산
        const errorRate = Math.abs(measured - analyzed) / measured;
        let status;
        if (errorRate <= 0.05) {
          status = 'good';
        } else if (errorRate <= 0.10) {
          status = 'normal';
        } else {
          status = 'bad';
        }
        return { error: errorRate, status };
      },
      getStatusText(status) {
        switch (status) {
          case 'good': return '적합';
          case 'normal': return '적정';
          case 'bad': return '미흡';
          case 'none': return '-';
          default: return '알 수 없음';
        }
      },
  /**
   * 노드 배열을 바탕으로 상태별 개수와 비율을 계산하는 함수
   * @param {Array} nodes - 계산된 updatedNodes 배열
   * @param {'flowStatus' | 'pressureStatus'} statusKey - 계산할 상태 키
   * @returns {object} - { good: {count, percent}, ... } 형태의 객체
   */
  calculateStatusSummary(nodes, statusKey) {
    const total = nodes.length;
    if (total === 0) {
      return {
        good: { count: 0, percent: 0 },
        normal: { count: 0, percent: 0 },
        bad: { count: 0, percent: 0 },
      };
    }

    // 상태별 개수를 세기 위한 초기 객체
    const counts = { good: 0, normal: 0, bad: 0 };
    
    // 배열을 순회하며 statusKey에 해당하는 상태의 개수를 증가시킴
    nodes.forEach(node => {
      const status = node[statusKey];
      if (Object.hasOwn(counts, status)) { // ✅ 안전하고 권장되는 방식
        counts[status]++;
      }
    });

    // 계산된 개수와 백분율로 최종 객체를 만들어 반환
    return {
      good: {
        count: counts.good,
        percent: Math.round((counts.good / total) * 100),
      },
      normal: {
        count: counts.normal,
        percent: Math.round((counts.normal / total) * 100),
      },
      bad: {
        count: counts.bad,
        percent: Math.round((counts.bad / total) * 100),
      },
    };
  },
    },
  }
</script>
<style scoped>
.contents-container {
  height: 93%;
  width: 100%;
}

.div_title {
  background-size: 42% 100%;
  background-repeat: no-repeat;
}

.card-header .icon {
  width: 28px;
  height: 28px;
  margin-right: 10px;
}

.status-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 6px;
  font-size: 1rem;
  font-weight: 500;
}

.status-label {
  color: #888;
}

.status-value {
  font-weight: 700;
  color: #222;
}

.suitable {
  background: #e6f7e6;
  border: 1px solid #b2e6b2;
}

.proper {
  background: #f7f3e6;
  border: 1px solid #e6dcb2;
}

.insufficient {
  background: #fbeaea;
  border: 1px solid #e6b2b2;
}


.loading-container {
  position: fixed;
  /* 절대 위치 설정 */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  /* 반투명한 배경 */
  z-index: 9999;
  /* 다른 요소 위에 표시하기 위한 z-index 설정 */
  display: flex;
  justify-content: center;
  /* 수평 가운데 정렬 */
  align-items: center;
}
</style>