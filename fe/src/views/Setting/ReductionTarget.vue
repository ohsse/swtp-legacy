
<template>
  <!--절감목표 컴포넌트의 템플릿 부분 -->
  <div class="container-fluid">
    <!-- 템플릿 내용 -->
    <!-- 타이틀 시작 -->
    <BigTitle :title="'절감 목표'" />
    <!-- 타이틀 끝 -->
    <!-- 본문 컨텐츠 시작 -->
    <div class="contents-container">
      <div class="div-big2" style="height: 98%; width: 100%; margin-top: 1rem;">

        <!-- 필터 영역 -->
        <div
          style="display: inline-flex; height: 60px; width: 100%; padding: 0px 26px; justify-content: center; align-items: center; margin-top: 8px;">
          <div style="width: 90%; height: 31px;">
            <!-- selectbox -->
            <div style="float: left; height: 31px;">
              <div>
                <b-form-select size="sm" style="width: 130px;" v-model="selectedYear" @click="yearOption"
                  @change="handleOptionChange">
                  <b-form-select-option v-for="year in yearData" :key="year" :value="year">{{ year
                  }}</b-form-select-option>
                </b-form-select>
              </div>
            </div>
            <!-- input, selectbox, button -->
            <div
              style="float: right; display: inline-flex; justify-content: center; align-items: flex-end; height: 31px;">
              <input v-model="targetValue" class="top_textinput" @input="validateInput()" :maxlength="maxLength"
                style="width: 150px; height: 31px; display: flex; margin-left: 8px; text-align: right;">

              <b-form-select size="sm" style="width: 80px; display: flex; margin-left: 8px;" v-model="initUnit"
                @change="unitClick">
                <b-form-select-option v-for="items in unit" :key="items" :value="items">{{ items
                }}</b-form-select-option>
              </b-form-select>

              <button style="height: 32px; display: flex; margin-left: 8px;" class="search_btn_font search_btn"
                @click="allApply">일괄적용</button>

            </div>
          </div>

          <!-- save button  -->
          <div style="width: 10%;">
            <div class="searchBox" style="float: right;">
              <div class="searchTag1">
                <button style="height: 32px;" class="search_btn_font search_btn" @click="saveBtn">저장</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Table 영역 -->
        <div style="width: 100%; padding: 2rem;">
          <reductionTable ref="reductionTable" />
        </div>
      </div>
    </div>
    <!-- 본문 컨텐츠 끝 -->

  </div>
</template>

<script>
import reductionTable from "@/views/Setting/ReductionTarget/ReductionTarget_list.vue"
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"

export default {
  components: {
    reductionTable, BigTitle
  },
  data() {
    const now = new Date();
    return {
      now,
      currentYear: null,
      selectedYear: now.getFullYear(),
      // yearData: ['2021', '2022', '2023'],
      yearData: [],
      targetValue: 0,
      unit: ['kwh', '%'],
      initUnit: 'kwh',
      maxLength: 10,
    }
  },
  mounted() {
    const currentYear = new Date().getFullYear();

    for (let i = 0; i < 3; i++) {
      this.yearData.push((currentYear - i).toString());
    }

    this.$emit("onChangeBgClass", false);
    this.handleOptionChange();
    this.yearOption();
    this.unitClick();
  },
  methods: {
    validateInput() {
      this.targetValue = this.targetValue.replace(/[^0-9]/g, "");

    },
    yearOption() {
 
    },
    handleOptionChange() {

      this.$nextTick(() => {
        this.$refs.reductionTable.initData(this.selectedYear);
      });
    },
    allApply() {

      this.$refs.reductionTable.tagetValueData(this.targetValue);
    },
    saveBtn() {
      this.$refs.reductionTable.saveBtn();
    },
    unitClick() {
      this.$nextTick(() => {
        if (this.initUnit == "%") {
          this.maxLength = 2;
          this.targetValue = "";
        } else {
          this.maxLength = 10;
          this.targetValue = "";
        }
        this.$refs.reductionTable.unitClick(this.initUnit);
      });
    }

  },

}

</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.contents-container {
  height: 93%;
  width: 100%;
}

.div-new {
  background-image: url(/src/assets/img/div_new.png);
  background-size: 100% 100%;
  display: inline-block;
}

.top_textinput {
  height: 85%;
  width: 100%;
  display: inline-block;
  border: 1px solid #489cf2;
  background-color: #15284e;
  color: #fff;
  font-family: KHNPHDRegular;
  font-size: 14px;
  text-align: center;
  letter-spacing: 4px;
  border-radius: 5px;
}

.searchTag1 {
  height: 36%;
  margin-left: 12px;
}

.searchBox {
  display: flex;
  height: 100%;
  flex-direction: column;
  justify-content: center;
}

.search_btn_font {
  text-shadow: 0 0 9px #5cafff;
  font-size: 17px;
  letter-spacing: normal;
  color: #fff;
  font-family: KHNPHDRegular;
  text-align: center;
  line-height: 2;
}

.search_btn {
  width: 80px;
  align-self: center;
  border: solid 1px #b4dffa;
  background-color: rgba(139, 194, 240, 0.25);
  cursor: pointer;
  border-radius: 4px;
  align-items: center;
  justify-content: center;
  display: flex;
}
</style>
