
<template>
  <!--태그정보 컴포넌트의 템플릿 부분 -->
  <div class="container-fluid">
    <!-- 템플릿 내용 -->
      <!-- 타이틀 시작 -->
      <BigTitle :title="'태그 정보'" />
      <!-- 타이틀 끝 -->


      <!-- 본문 컨텐츠 시작 -->
      <div class="contents-container">
        <div class="div-tag" style="height:93px; display:inline-flex; width: 99%;">

          <div class="searchBox">
            <div class="searchTag1 searchLabel">시설명</div>
            <div class="searchTag1">
              <b-form-select id="zone" v-model="tagSearch.zone" :options="zoneOption" size="sm" class="mb-3" />
            </div>
          </div>
          <div class="searchBox">
            <div class="searchTag1 searchLabel">설비명</div>
            <div class="searchTag1">
              <input id="fac" @input="handleInput($event)" v-model="tagSearch.fac" class="top_textinput">
            </div>
          </div>
          <div class="searchBox">
            <div class="searchTag1 searchLabel">태그명</div>
            <div class="searchTag1">
              <input id="tagname" @input="handleInput($event)" v-model="tagSearch.tagname" class="top_textinput">
            </div>
          </div>
          <div class="searchBox">
            <div class="searchTag1 searchLabel"></div>
            <div class="searchTag1">
              <button class="search_btn_font search_btn" style="height: 85%;" @click="findTagInfo()">조회</button>
            </div>
          </div>

        </div>
        <tagInfo ref="grid" @getNewList="getTagInfoList()"></tagInfo>
      </div>











  </div>
</template>

<script>
import tagInfo from "@/views/Setting/TagInfo/TagInfo_list.vue";
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"
import { fetchFunc } from "@/util/fetchFunc";
import { replace } from "@/util/replace";

export default {
  components: {
    tagInfo,
    BigTitle
  },
  data() {
    return {
      zoneOption: [
        { value: null, text: '전체' }
      ],
      tagSearch: {
        zone: null,
        fac: null,
        tagname: null
      },
      zoneArray: new Array()
    }
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
    this.getZoneData()
    this.getTagInfoList()
  },
  methods: {
    async getZoneData() {
      const apiURL = this.$apiURL;
      let zoneInfo = (await fetchFunc(`${apiURL}/st/selectZone?use_yn=1`)).data
      let zoneArray = new Array();
      zoneInfo.forEach((item) => {
        zoneArray.push(item.zone_name)
        let option = {
          value: item.zone_name,
          text: item.zone_name
        }
        this.zoneOption.push(option)
      });

      this.$refs.grid.setGridFiled(zoneArray)
    },
    async getTagInfoList() {
      const apiURL = this.$apiURL;

      let tagList = (await fetchFunc(`${apiURL}/st/selectTagList?zone_code=${this.tagSearch.zone}&fac_name=${this.tagSearch.fac}&tagname=${this.tagSearch.tagname}`)).data;
      for (let i in tagList) {
        tagList[i]['USE_YN'] = tagList[i]['USE_YN'] === '1';
      }
      this.$refs.grid.setGridRowData(tagList)
    },
    async findTagInfo() {
      await this.getTagInfoList();
    },
    handleInput(event) {
      const inputElement = event.target;
      // 외부 함수 호출 (인자로 입력 요소의 값을 전달)
      replace(inputElement);
    },
  }
};


</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.contents-container {
  height: 93%;
  width: 100%;
}

.searchBox {
  display: flex;
  width: 15%;
  height: 100%;
  flex-direction: column;
  justify-content: center;
  margin-left: 50px;
}

.searchTag1 {
  height: 36%;
  width: 100%;
}

.searchLabel {
  font-family: KHNPHDRegular;
  font-size: 14px;
  letter-spacing: 4px;
  color: white;
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

.div_border {
  background-image: url(@/assets/img/box_bg_small.png);
  background-size: 100% 100%;
}

.div-tag {
  width: 100%;
  height: 100%;
  background-image: url("@/assets/img/box_bg_taginfo.png");
  background-size: 100% 100%;
  /* mix-blend-mode: color-dodge; */
}
</style>
