<template>
  <b-card class="card bg-transparent border-0 p-0 h-100" body-class="bg-transparent p-0">
    <SmallTitle :title="'관망해석 결과'" />
    <b-row class="d-flex justify-content-between align-items-end">
      <b-col md="10">
        <!-- 좌측 타이틀 -->
      </b-col>
      <b-col md="4">
        <!-- 우측 버튼 -->
      </b-col>
      <b-col md="8" class="d-flex justify-content-end">

        <b-button variant="outline-light" size="sm" class="cust-btn me-2 mt-2" @click="downloadCSV">CSV 다운로드</b-button>
      </b-col>
    </b-row>

    <b-row class="mt-2">
      <b-col class="px-3 mt-0">
        <div class="mt-2 flex-shrink-0">
          <div class="custom-tbl table-responsive mb-0" :style="{ maxHeight: '300px', overflowY: 'auto' }">
            <table class="table table-sm table-bordered align-middle mb-0">
              <thead>
                <tr>
                  <th>구분</th>
                  <th>유량(m<sup>3</sup>/h)</th>
                  <th>압력(kgf/cm<sup>2</sup>)</th>
                  <th>구분</th>
                  <th>유량(m<sup>3</sup>/h)</th>
                  <th>압력(kgf/cm<sup>2</sup>)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in results" :key="index">
                  <td>{{ row.div1 }}</td>
                  <td>{{ formatValue(row.flow1, "flow") }}</td>
                  <td>{{ formatValue(row.pressure1, "press") }}</td>
                  <td>{{ row.div2 }}</td>
                  <td>{{ formatValue(row.flow2, "flow") }}</td>
                  <td>{{ formatValue(row.pressure2, "press") }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </b-col>
    </b-row>
  </b-card>
</template>

<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";

export default {
  name: 'AnalysisResults',
  components: { SmallTitle },
  props: {
    results: {
      type: Array,
      default: () => [
        { div1: '고산분기', flow1: 963, pressure1: '00', div2: '군봉분기', flow2: 963, pressure2: '00' },
        { div1: '익산분기', flow1: 510, pressure1: '00', div2: '나운분기', flow2: 510, pressure2: '00' },
        { div1: '장항분기', flow1: 270, pressure1: '00', div2: '대야분기', flow2: 270, pressure2: '00' },
        { div1: '김제분기', flow1: 641, pressure1: '00', div2: '전주분기', flow2: 641, pressure2: '00' },
        { div1: '삼례분기', flow1: 199, pressure1: '00', div2: '대성분기', flow2: 199, pressure2: '00' },
        { div1: '옥석분기', flow1: 345, pressure1: '00', div2: '금구분기', flow2: 345, pressure2: '00' },
        { div1: '농수산분기', flow1: 725, pressure1: '00', div2: '반월분기', flow2: 725, pressure2: '00' },
        { div1: '춘포분기', flow1: 652, pressure1: '00', div2: '신지분기', flow2: 652, pressure2: '00' },
        { div1: '춘포분기', flow1: 652, pressure1: '00', div2: '-', flow2: '-', pressure2: '-' },
      ]
    }
  },
  methods: {
    downloadCSV() {
      if (!this.results || this.results.length === 0) {
        alert('다운로드할 데이터가 없습니다.');
        return;
      }

      // CSV 헤더 (테이블과 동일하게)
      const headers = [
        '구분', '유량(m3/h)', '압력(kgf/cm2)',
        '구분', '유량(m3/h)', '압력(kgf/cm2)'
      ];

      // CSV 데이터 행 생성 (toFixed 직접 적용)
      const rows = this.results.map(row => {
        // 값이 null이나 undefined가 아닐 때만 toFixed 적용
        // Number()로 감싸서 숫자 타입으로 변환 후 toFixed 호출
        const flow1 = row.flow1 != null ? Number(row.flow1).toFixed(0) : '';
        const pressure1 = row.pressure1 != null ? Number(row.pressure1).toFixed(2) : '';
        const flow2 = row.flow2 != null ? Number(row.flow2).toFixed(0) : '';
        const pressure2 = row.pressure2 != null ? Number(row.pressure2).toFixed(2) : '';

        return [
          row.div1,
          flow1,
          pressure1,
          row.div2,
          flow2,
          pressure2
        ];
      });

      // CSV 문자열 생성
      let csvContent = '\uFEFF'; // UTF-8 BOM (한글 깨짐 방지)
      csvContent += headers.join(',') + '\r\n';
      rows.forEach(rowArray => {
        csvContent += rowArray.join(',') + '\r\n';
      });

      // Blob 객체 생성
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });

      // 다운로드 링크 생성 및 클릭
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', '관망해석_결과.csv');
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },
    /**
     * 테이블에 표시될 값을 포맷팅하는 함수
     * @param {*} value - 포맷팅할 값
     * @returns {string|number} - 포맷팅된 결과
     */
    formatValue(value, type) {
      // 값이 null이거나 undefined이거나 이미 '-' 문자일 경우 '-' 반환
      if (value === null || value === undefined || value === '-') {
        return '-';
      }
      
      // 숫자형으로 변환
      const numValue = Number(value);

      // 변환된 값이 숫자가 아니거나 0 이하일 경우 0 반환
      if (isNaN(numValue) || numValue <= 0) {
        return 0;
      }
      
      // 그 외의 경우는 소수점 두 자리로 포맷팅하여 반환
      if(type === "flow"){
        return numValue.toLocaleString(undefined, { maximumFractionDigits: 0 });
      }else{  
        return numValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); 
      }
    }
  }
}
</script>

<style scoped>
/* 기존 CSS에서 결과 테이블 관련 스타일을 여기에 붙여넣습니다. */
.cust-btn {
  border-color: #83A3BB !important;
  color: #fff !important;
  background: rgba(131, 163, 187, .3) !important
}

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

/* [추가된 코드] 
  3번째 열(압력)의 오른쪽 테두리를 굵게 만듭니다. 
*/
.custom-tbl th:nth-child(3),
.custom-tbl td:nth-child(3) {
  border-right-width: 3px;
  /* 굵기를 3px로 설정 (조절 가능) */
  border-right-color: #405C8C;
  /* 기존 테두리 색상 */
}

/* [추가된 코드] 
  마우스 호버 시에도 3번째 열의 굵은 테두리를 흰색으로 유지합니다. 
*/
.custom-tbl tbody tr:hover td:nth-child(3) {
  border-right-width: 3px;
  border-right-color: #fff;
  /* 호버 시 흰색 테두리 유지 */
}
</style>