<template>
  <LoadingSpinner class="loading-container" v-if="isLoading" />
  <div class="container-fluid">
    <!-- 템플릿 내용 -->
    <!-- 타이틀 -->
    <b-row>
      <b-col xl="4">
        <BigTitle :title="'관망해석 시뮬레이션'" />
      </b-col>
      <b-col xl="5" class="d-flex align-items-center"></b-col>
      <b-col xl="3" class="d-flex align-items-center justify-content-end">
        <MonitorMode :value="'simulation'" @change="onModeChange" />
      </b-col>
    </b-row>
    <!-- //타이틀 -->
    <!-- 본문 컨텐츠 -->
    <div class="contents-container" style="height: calc(100% - 100px);">
      <b-row class="h-100" style="margin-top: 15px">
        <b-col class="area" :xl="isMapFullscreen ? 12 : 5" style="position:relative; padding-right : 15px;">
          <!-- 지도 표출 -->
          <MapComponent :isFullscreen="isMapFullscreen" @toggle-fullscreen="toggleMapFullscreen"
            style="width: 100%; height: 100%; border: 1px solid #dcdcdc;" :isShowPin="false" :isSimulation="true"
            :nodes="nodes" :time-text="displayTime" />
        </b-col>
        <b-col v-if="!isMapFullscreen" xl="7" class="d-flex flex-column gap-4">
          <!-- 1) 관망해석 설정 -->
          <AnalysisSettings :tanks="tanks" :totalFlow="totalFlow" :pumpCal="pumpCal" @execute="handleExecuteAnalysis"
            @oneInputFlow="oneFlowSetting" />


          <!-- 2) 관망해석 결과 -->
          <AnalysisResults :results="results" class="flex-grow-1" style="min-height: 0;" />
        </b-col>
      </b-row>
    </div>
  </div>

  <!-- 다중설정 모달 -->
  <MultiInflowModal :tanks="tanks" @save="updateFlows" />
  <!-- //다중설정 모달 -->

</template>
<script>
  import BigTitle from '@/components/ComponentCommon/BigTitle.vue';
  import LoadingSpinner from '@/components/ComponentCommon/LoadingSpinner.vue';

  import MapComponent from '@/components/Map/MapComponent.vue';
  import MonitorMode from '@/views/Common/MonitorMode.vue';
  import { fetchFunc } from '@/util/fetchFunc';
  import AnalysisSettings from '@/views/EpaAnalysis/simulation/AnalysisSettings.vue';
  import AnalysisResults from '@/views/EpaAnalysis/simulation/AnalysisResults.vue';
  import MultiInflowModal from '@/views/EpaAnalysis/simulation/MultiInflowModal.vue';
  export default {
    name: 'EpaAnalysisSimulation',
    components: {
        BigTitle,
        MapComponent,
        MonitorMode,
        AnalysisSettings,
        AnalysisResults,
        MultiInflowModal,
        LoadingSpinner
    },
    data(){
      return{
        isMapFullscreen: false,
        // [배열이어야 한다] {} 로 두면 settingData 가 채우기 전에 this.nodes.map() 이 불려
        // "map is not a function" 으로 죽는다. 그 자리에서 죽으면 isLoading 을 끄는 줄에
        // 도달하지 못해 스피너가 영구히 남는다. MapComponent 의 nodes prop 도 type: Array 라
        // {} 를 넘기면 prop 경고와 함께 filter/length 가 전부 어긋난다.
        nodes: [],
        mapNodes: [],
        tanks:[],
        results:[],
        pumpCal:[],
        isLoading: false,
        displayTime: '시뮬레이션 시각 : 2025-10-21 18:31:00'
      }
    },
    computed: {
      // 전체 펌프 조합 조회에 쓸 펌프그룹 번호.
      // 고산 TB_PUMP_CAL은 0(통합)·1·2를 갖고 0이 전체를 대표하지만,
      // 군산은 PUMP_GRP=1만 존재한다. 0으로 조회하면 결과가 비므로 사업소별로 가른다.
      pumpGrp() {
        return this.$area === 'gosan' ? 0 : 1;
      },
      // tanks 배열이 변경될 때마다 totalFlow를 자동으로 다시 계산합니다.
      totalFlow() {
        if (!this.tanks || this.tanks.length === 0) {
          return 0;
        }
        // 각 tank의 FLOW_RATE를 모두 더합니다. 문자열(콤마 포함) 방지 위해 숫자로 변환
        return this.tanks.reduce((sum, tank) => {
          const val = Number(String(tank.FLOW_RATE || 0).replace(/,/g, ''));
          return sum + (isNaN(val) ? 0 : val);
        }, 0);
      }
    },
    created() {
      this.init();
    },
    methods: {
      // fetchFunc 는 실패해도 throw 하지 않고 { error: true, message } 를 돌려준다
      // (util/fetchFunc.js 의 catch). 그대로 .data 를 꺼내면 undefined 가 되어,
      // 원인 지점이 아니라 한참 뒤 .map()/.raw 자리에서 엉뚱한 TypeError 로 터진다.
      // 실패를 여기서 한 번에 끊어 메시지를 살린다 — epa 의 api_error 가 주는
      // "관망해석 엔진이 사용 중입니다" 같은 안내가 운영자에게 그대로 보여야 한다.
      unwrap(res, what) {
        if (!res || res.error) {
          throw new Error(`${what}을(를) 불러오지 못했습니다: ${(res && res.message) || '응답 없음'}`);
        }
        return res.data;
      },

      // 최초 진입. nodes 를 채운 뒤에 해석 결과를 입혀야 하므로 순서를 강제한다.
      // 예전에는 created 가 settingData 를, mounted 가 getSimulationResults 를 각각 띄워
      // 둘이 경쟁했다. mounted 시점에는 settingData 의 첫 await 가 끝나지 않아 nodes 가
      // 비어 있었고, 해석 결과가 빈 배열로 덮이거나 그대로 TypeError 가 났다.
      async init() {
        this.isLoading = true;
        try {
          await this.settingData();
          await this.loadSimulationResults();
        } catch (error) {
          console.error('관망해석 시뮬레이션 초기화 실패:', error);
          alert(`데이터를 불러오지 못했습니다: ${error.message}`);
        } finally {
          // [중요] finally 가 없으면 위에서 던진 순간 스피너가 영구히 남는다.
          this.isLoading = false;
        }
      },

      toggleMapFullscreen() {
        this.isMapFullscreen = !this.isMapFullscreen;
      },
      // MultiInflowModal에서 'save' 이벤트 발생 시 호출될 메서드
      updateFlows(updatedTanks) {
        // 자식에게 받은 새로운 배열로 교체하면, computed 속성인 totalFlow가 자동으로 갱신됩니다.
        this.tanks = updatedTanks;
      },
      // 스피너는 부르는 쪽(init)이 책임진다 — 여기서 켜고 끄면 뒤따르는
      // loadSimulationResults 와 서로 상태를 덮어쓴다.
      async settingData(){
        const pythonURL = this.$pythonURL;
        const setNodes = this.unwrap(await fetchFunc(`${pythonURL}/api/web/nodes`), '표시지점');
        this.nodes = setNodes.map(element => {
    
            if (element.JUNCTION_ID === "10") {
                
                return {
                    ...element,       
                    PIPE_ID: "p_10" 
                };
            }
            
            
            return element; 
        });
        // 배수지 수요량
        this.tanks = this.unwrap(await fetchFunc(`${pythonURL}/api/web/tanks`), '배수지 수요량');

        // 전체 펌프 조합
        this.pumpCal = this.unwrap(
          await fetchFunc(`${pythonURL}/api/web/simulration/pumpComb?pump_grp=${this.pumpGrp}`), '펌프 조합');
      },
      // 해석 실행 후 갱신·재조회에서 부르는 진입점. 스피너를 스스로 책임진다.
      async getSimulationResults(){
        this.isLoading = true;
        try {
          await this.loadSimulationResults();
        } catch (error) {
          console.error('관망해석 결과 조회 실패:', error);
          alert(`해석 결과를 불러오지 못했습니다: ${error.message}`);
        } finally {
          // [중요] finally 가 없으면 위에서 던진 순간 스피너가 영구히 남는다.
          // 예전에는 isLoading = false 가 메서드 마지막 줄에만 있어, 중간에서
          // TypeError 가 나면 화면이 로딩 상태로 굳었다.
          this.isLoading = false;
        }
      },

      // 순수 조회·가공. 스피너를 건드리지 않으므로 init 에서도 그대로 재사용한다.
      async loadSimulationResults(){
        const pythonURL = this.$pythonURL;
        const simulationResults = this.unwrap(await fetchFunc(`${pythonURL}/api/web/simulration`), '해석 결과');

        this.tanks = this.unwrap(await fetchFunc(`${pythonURL}/api/web/tanks`), '배수지 수요량');
        // raw 가 없으면 아래 조회가 전부 undefined 가 된다. 0 으로 표시될지언정 죽지는 않게 한다.
        const raw = simulationResults.raw || {};
        this.displayTime = `시뮬레이션 시각 : ${simulationResults.ts}`;
        // 1. nodes 배열에 시뮬레이션 결과(flowAnalyzed, pressureAnalyzed)를 추가합니다.
        const updatedNodes = this.nodes
        // .filter(node => node.IS_DISPLAY == 1)
        .map(node => {
          const originalFlowAnalyzed = raw[node.PIPE_ID];
          const originalPressureAnalyzed = raw[node.JUNCTION_ID];
          const displayFlowAnalyzed = originalFlowAnalyzed === null ? 0 : originalFlowAnalyzed;
          const displayPressureAnalyzed = originalPressureAnalyzed === null ? 0 : originalPressureAnalyzed;
          return {
            ...node,
            flowAnalyzed: displayFlowAnalyzed,
            pressureAnalyzed: displayPressureAnalyzed
          };
        })
        this.nodes = updatedNodes;
        
        
        //관망해석결과
        const displayableNodes = this.nodes.filter(node => node.IS_DISPLAY == 1);

        const formattedResults = [];

        // 2. 필터링된 배열을 2씩 증가시키며 순회합니다.
        for (let i = 0; i < displayableNodes.length; i += 2) {
          
          // 이제 node1은 항상 IS_DISPLAY가 1입니다.
          const node1 = displayableNodes[i];
          
          // node2는 필터링된 배열의 다음 요소이거나, 없으면 undefined가 됩니다.
          const node2 = displayableNodes[i + 1]; 

          const row = {
            div1: node1.LOCATION_NM,
            flow1: node1.flowAnalyzed,
            pressure1: node1.pressureAnalyzed,

            // node2가 존재하는지(undefined가 아닌지) 확인합니다.
            div2: node2 ? node2.LOCATION_NM : '-',
            flow2: node2 ? node2.flowAnalyzed : '-',
            pressure2: node2 ? node2.pressureAnalyzed : '-'
          };
          
          formattedResults.push(row);
        }
        
        this.results = formattedResults;
      },
      // AnalysisSettings에서 'execute' 이벤트 발생 시 호출될 메서드
      async handleExecuteAnalysis(settings) {
        console.log(settings); // 이제 selectedCombo만 들어있음
        const pythonURL = this.$pythonURL;
        try {
          // [수정] 부모가 직접 관리하는 this.tanks 데이터를 API 형식에 맞게 가공합니다.

          const tanksForApi = this.tanks.map(tank => ({
            node_id: tank.NODE_ID,
            flow_rate: tank.FLOW_RATE
          }));


          // 1. 가공된 유량 값(tanks)을 DB에 업데이트합니다.
          const updateResponse = await fetchFunc(`${pythonURL}/api/web/updateRate`, {
            method: 'POST',
            body: JSON.stringify(tanksForApi) // settings.tanksForApi 대신 직접 만든 데이터를 사용
          });

          if (updateResponse.code !== 200) {
            throw new Error('유량 업데이트에 실패했습니다.');
          }

          console.log('유량 업데이트 성공:', updateResponse);
          alert('유량 정보가 성공적으로 저장되었습니다.');

          // 2. 유량 업데이트 성공 시, 시뮬레이션을 실행합니다.
          const simulationResponse = await fetchFunc(`${pythonURL}/api/simulations/si`, {
            method: 'POST',
            body: JSON.stringify({ settings }) // 자식에게 받은 펌프 정보 사용
          });
            
          if (simulationResponse.code !== 200) {
            // 서버 메시지를 버리지 않는다. 해석 엔진의 검증 문구
            // ("군산 송수펌프는 1~4호기만 지정할 수 있습니다", "1호기 Hz는 1~60 범위여야 합니다")가
            // 운영자에게 그대로 보여야 무엇을 고쳐야 할지 알 수 있다.
            throw new Error(simulationResponse.message || '시뮬레이션 실행에 실패했습니다.');
          }

          console.log('시뮬레이션 실행 성공:', simulationResponse);
          alert('시뮬레이션을 성공적으로 실행했습니다. 결과를 갱신합니다.');

          // 3. 시뮬레이션 성공 시, 결과값을 다시 불러와 화면을 갱신합니다.
          await this.getSimulationResults();

        } catch (error) {
          console.error('관망해석 실행 중 오류 발생:', error);
          alert(`오류가 발생했습니다: ${error.message}`);
        }
      },
      oneFlowSetting(tank, value){
        
        // 입력값을 숫자로 정리 (콤마 제거, 빈값 -> 0)
        const newFlow = Number(String(value).replace(/,/g, '')) || 0;
        const updatedTanks = this.tanks.map(t => {
          if(t.TNK_NM === tank){
            return {
              ...t,
              FLOW_RATE: newFlow
            }
          }
          return t;
        });
        this.tanks = updatedTanks;
      }
      
    }
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

.cust-btn {
  border-color: #83A3BB !important;
  color: #fff !important;
  background: rgba(131, 163, 187, 0.3) !important;
}

.glow-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.glow-num {
  font-size: 30px;
  font-family: LAB디지털 !important;
  line-height: 1;
  color: #fff;
  font-weight: 400;
  letter-spacing: .06em;
  /* 디지털 계열 느낌: 여러 겹의 네온 블러 */
  text-shadow:
    0 0 8px rgba(144, 195, 255, .9),
    0 0 18px rgba(144, 195, 255, .45),
    0 0 32px rgba(144, 195, 255, .25);
}

.glow-pct {
  font-size: 24px;
  font-family: LAB디지털 !important;
  color: #9fc7ff;
  font-weight: 400;
  text-shadow:
    0 0 6px rgba(144, 195, 255, .85),
    0 0 14px rgba(144, 195, 255, .35);
}

/* 커스텀 테이블(표) */
.custom-tbl th {
  font-size: 18px;
}

.custom-tbl th,
.custom-tbl td {
  border: 1px solid #405C8C;
  padding: 5px 8px;
  color: #fff;
  font-size: 16px;
  text-align: center;
  vertical-align: middle;
  background: rgba(0, 0, 0, 0.35);
}

.custom-tbl th {
  background: rgba(26, 44, 106, 1);
}

.custom-tbl tbody tr:hover {
  background: rgba(8, 80, 191, 1) !important;
}

.custom-tbl tbody tr:hover td {
  border: 1px solid #fff;
  border-top: 2px solid #fff;
}


/* ===== 컨트롤 ===== */
.cust-input .form-control {
  background: rgba(20, 40, 72, .6);
  border-color: #418EDE !important;
  color: #e7f3ff;
}

.cust-input .form-control:focus {
  border-color: #5fb1ff;
  box-shadow: 0 0 0 .15rem rgba(95, 177, 255, .25);
}

.cust-btn {
  border-color: rgba(160, 210, 255, .35) !important;
  color: #d9f1ff !important;
  background: rgba(255, 255, 255, .03);
}

.cust-btn:hover {
  background: rgba(255, 255, 255, .06);
}

/* 둥근칩(펌프 번호) */
.kw-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 26px;
  border-radius: 999px;
  background: #174D9e;
  color: #fff;
  font-weight: 700;
}

/* 라디오 커스텀(파란 네온 링) */
.cust-radio {
  width: 1.1rem;
  height: 1.1rem;
  background-color: transparent;
  border: 1px solid #76A4F1;
  float: unset !important;
  cursor: pointer;
}

.cust-radio:checked {
  border-color: #51b2ff;
  box-shadow: unset !important;
}

.cust-radio:active,
.cust-radio:focus {
  box-shadow: unset !important;
}

/* 버튼 */
.btn-apply {
  color: #fff;
  background: #0B63B0;
  padding: .6rem 1.2rem;
  font-weight: 600;
  height: 42px;
  border: 0;
}

/* 컴포넌트에만 적용되는 스타일 정의 */
.date_design {
  background-color: #15284e;
  border-color: #418EDE !important;
  color: #fff;
  font-size: 13px;
  margin-left: 10px;
  font-family: KHNPHDRegular;
  border-radius: 5px;
}

/* ## 다중설정 모달 ## */
/* 모달 전체 톤 */
.custom-modal .custom-modal__content {
  position: relative;
  border: 0;
  overflow: hidden;
  background: #0f1c2a;
  /* 기존 배경 */
  color: #dbe7ff;
  border-radius: 0;
  box-shadow: 0 12px 40px rgba(0, 0, 0, .5);
  /* 외곽 그림자는 그대로 */
  overflow: hidden;
}

/* 내부 파란 glow를 위 레이어로 얹기 */
.custom-modal__content::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  /* 입력/클릭 방해 X */
  z-index: 1;
  /* 헤더/바디/푸터 위로 */
  box-shadow: inset 0 0 20px 0 #0D67F2;
  /* 배경은 투명 (그림자만) */
  background: transparent;
}

/* 헤더 상단 고정 + 그라데이션 */
.custom-modal__header {
  font-size: 1.5rem;
  font-weight: 700;
  background: #1A2C6A;
  color: #fff;
  border-bottom: 0 !important;
  padding: 10px 16px;
  border-top-left-radius: 0 !important;
  border-top-right-radius: 0 !important;
}

.custom-modal__header .modal-title {
  font-size: 1.45rem;
  font-weight: 800;
  letter-spacing: .02em;
}

.custom-modal__header .btn-close {
  width: 0.5rem;
  height: 0.5rem;
  margin-right: 7px
}


/* 바디 */
.custom-modal__body {
  background: #0f1c2a;
  padding: 18px 18px 0;
}

/* 푸터 */
.custom-modal__footer {
  border-top: 0;
  background: #0f1c2a;
  padding: 14px 18px 18px;
  justify-content: flex-end;
  border-bottom-left-radius: 0 !important;
  border-bottom-right-radius: 0 !important;
}

.custom-modal__footer .btn {
  font-weight: 700;
  border-radius: 0;
}

.custom-modal__footer .btn-secondary {
  background: #23354e;
  border: 0;
}

.custom-modal__footer .btn-primary {
  background: #2f64ff;
  border: 0;
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