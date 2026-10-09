<template>
  <div>
    <b-table class="table-style table-posi" :items="items">
      <template v-slot:cell(적용할목표치)="data">
        <input type="text" v-model="data.value" @input="eventInput($event, data.index)" class="right-aligned-input" />
      </template>
    </b-table>
  </div>
</template>

<script>
import { fetchFunc } from '@/util/fetchFunc';
import Swal from 'sweetalert2'
export default {
  data() {
    return {
      thisYearData: [],
      lastYearData: null,
      items: [
        { 월: '1월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '2월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '3월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '4월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '5월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '6월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '7월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '8월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '9월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '10월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '11월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
        { 월: '12월', 전년도목표치: '', 기준년도사용량: '', 적용중인목표치: '', 적용할목표치: 0 },
      ],
      targetValue: null,
      unit: null,
      allData: [],
      anotherValue: null,
      data: {
        value: '' // 초기값 설정
      },
      inputData: [],
    }
  },
  mounted() {
    // this.initData();

  },

  methods: {
    eventInput(event, slots) {
      // this.items.at(slots).적용할목표치 = event.target.value
      this.items[slots].적용할목표치 = event.target.value;
    },
    unitClick(unit) {
      this.unit = unit;
    },
    async initData(selectedYear) {


      let getData = [];
      const apiURL = this.$apiURL;
      let data = await fetchFunc(`${apiURL}/st/selectGetSetting`)
      getData = data.data;
      this.lastYearData = selectedYear - 1;

      for (let index = 0; index < getData.length; index++) {
        if (selectedYear == getData[index]["year"]) {
          for (let i = 1; i < 13; i++) {
            this.items[i - 1]["적용중인목표치"] = Number(getData[index][i + "m"]).toLocaleString();
          }
        } else if (getData[index]["year"] == 'base') {
          for (let i = 1; i < 13; i++) {
            let numberGetData = getData[index][i + "m"]
     
            if (getData[index][i + "m"]) {
              this.items[i - 1]["기준년도사용량"] = Number(numberGetData).toLocaleString();
            } else if (Number(numberGetData) == 0 || Number(numberGetData) == "0" || Number(numberGetData).toLocaleString() == "0") {
              this.items[i - 1]["기준년도사용량"] = '';
            }
          }
        } else if (this.lastYearData == getData[index]["year"])
          for (let i = 1; i < 13; i++) {
            this.items[i - 1]["전년도목표치"] = Number(getData[index][i + "m"]).toLocaleString();
          }
      }


      // 초기 선택값을 현재 년도로 설정
    },
    // 일괄적용
    tagetValueData(targetValue) {
      this.targetValue = targetValue;

      // unit이 '%'일 때만 퍼센트 계산 로직을 수행
      if (this.unit === '%') {
        // 퍼센트 값을 소수점 형태로 변환 (예: 99 -> 0.99)
        const multiplier = this.targetValue * 0.01;

        for (let i = 1; i < 13; i++) {
          const appliedGoalValue = parseFloat(this.items[i - 1]["기준년도사용량"].replace(/,/g, ''));

          if (!isNaN(appliedGoalValue)) {
            // 올바른 퍼센트를 곱하고 소수점 2자리까지 반올림
            const calculatedValue = (appliedGoalValue * multiplier).toFixed(2);
            
            // 문자열로 된 결과를 다시 숫자로 변환하여 할당
            this.items[i - 1]["적용할목표치"] = parseFloat(calculatedValue);
          } 
        }
      } else {
        // '%'가 아닐 경우, targetValue를 그대로 적용
        for (let index = 0; index < 12; index++) {
          this.items[index]["적용할목표치"] = this.targetValue;
        }
      }
    },

    async saveBtn() {
      const confirmed = await Swal.fire({
        text: '저장하시겠습니까?',
        animation : false,
        showCancelButton: true,
        confirmButtonText: '저장',
        cancelButtonText: '취소'
      });

      let params = {};
      if (confirmed.isConfirmed) { 
        // params.month1 = parseInt(this.items[0].적용할목표치) == 0 ? '' : parseInt(this.items[0].적용할목표치)
        // params.month2 = parseInt(this.items[1].적용할목표치)
        // params.month3 = parseInt(this.items[2].적용할목표치)
        // params.month4 = parseInt(this.items[3].적용할목표치)
        // params.month5 = parseInt(this.items[4].적용할목표치)
        // params.month6 = parseInt(this.items[5].적용할목표치)
        // params.month7 = parseInt(this.items[6].적용할목표치)
        // params.month8 = parseInt(this.items[7].적용할목표치)
        // params.month9 = parseInt(this.items[8].적용할목표치)
        // params.month10 = parseInt(this.items[9].적용할목표치)
        // params.month11 =parseInt(this.items[10].적용할목표치)
        // params.month12 = parseInt(this.items[11].적용할목표치)

        for (var i = 0; i < 12; i++) {
          params["month" + (i + 1)] = Number(this.items[i].적용할목표치) == 0 ? '' : Number(this.items[i].적용할목표치);
        }

        var myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        const apiURL = this.$apiURL;
        var requestOptions = {
          method: 'POST',
          headers: myHeaders,
          body: JSON.stringify(params),
        };


        await fetch(`${apiURL}/st/updateGoal/`, requestOptions)
          .then(response => response.text());
        await Swal.fire({
          animation: false,
          text: '저장되었습니다.',
          confirmButtonText: '확인'
        }).then(() => {
          location.reload(); 
        });
      } else {
        Swal.fire({
          animation : false,
          text: '저장이 취소되었습니다.',
        });
      }

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

.table-posi {
  margin-top: 2.5rem;
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
</style>