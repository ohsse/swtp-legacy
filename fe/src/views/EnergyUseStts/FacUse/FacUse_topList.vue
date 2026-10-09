<template>
  <b-col xl="2 px-5" class="ai-arrow-right">
    <small-title :title="smallTitleZone" />
    <b-list-group class="list-custom-group left_bg fontContent d-flex align-items-center"
      v-bind:style="{ height: '360px', overflowY: 'scroll', width: '100%' }">

      <b-list-group-item v-for="(item, index) in items" :key="index" :class="{ active: activeIndex === index }"
        @click="toggleActive(index, item), subListData(item), getGroup(item)" v-bind:style="{ width: '93%' }">{{ item
        }}</b-list-group-item>

    </b-list-group>

  </b-col>
  <img class="blinking" :src="require(`@/assets/img/ai_arrow_right.png`)"
    style="width: 70px;height: 360px;background: url('src\assets\img\ai_arrow_right.png');background-size: 100% 100%;float:left; mix-blend-mode:color-dodge;" />


  <b-col xl="4 px-5" class="ai-arrow-right">
    <small-title :title="smallTitleFac" />
    <b-list-group class="list-custom-group left_bg p-4 fontContent d-flex align-items-center text-ellipsis"
      v-bind:style="{ width: '600px', height: '380px', overflowY: 'scroll', }" v-if="dong == 0">
      <!-- 기본페이지에 비었음  -->
      <b-list-group-item v-bind:style="{ width: '100%', marginBottom:'10px'}" class="" v-for="(item, index) in subList" :key="index"
        :class="{ active: subActiveIndex === index }" @click="subListActive(index, item), getSubGroup(item.fac_code)">
        <div class="px-1 BoxSize">
          {{ item.DCS }}
          <!-- {{ item.DCS.substring(0, item.DCS.lastIndexOf(`(${item.fac_code})`)) }} -->
          <!-- <b-col style="width: 100%; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">
          </b-col>
          <b-col style="width: 100%; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">
          </b-col> -->

          <!-- ({{ item.fac_code }}) -->
        </div>
      </b-list-group-item>
    </b-list-group>

  </b-col>

  <img class="blinking" :src="require(`@/assets/img/ai_arrow_right.png`)"
    style="width: 70px;height: 360px;background: url('src\assets\img\ai_arrow_right.png');background-size: 100% 100%;float:left; mix-blend-mode:color-dodge;" />
</template>

<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";



export default {
  components: { SmallTitle },
  emits: ['getGroupId', 'getSubGroupId'],
  data() {
    let smallTitleZone = '시설 현황'
    let smallTitleFac = '설비 목록'
    return {
      group: undefined,
      subGroup: undefined,
      dong: 0,
      borderStyle: {},
      items: [],
      subList: [],
      activeIndex: -1,
      subActiveIndex: 0,
      smallTitleZone,
      smallTitleFac
    }
  },
  mounted() {
  },
  methods: {
    // 목록 클릭시 활성 이벤트 함수
    toggleActive(index, item) {
      if (this.activeIndex !== index) {
        this.activeIndex = index; // 다른 항목 클릭 시만 활성화
        this.subListData(item);
      }
    },
    subListActive(index) {
      if (this.subActiveIndex !== index) {
        this.subActiveIndex = index;
      }
    },


    // 설비목록 리스트 함수
    zoneData(items, index = 0) {
      this.items = items;
      if (!this.group) {
        this.toggleActive(index, items[index])
        this.getGroup(items[index])
      }
    },

    // 클릭 이벤트 핸들러에서 호출하는 함수
    async subListData(item) {
      // 클릭된 item을 파라미터로 사용하여 다른 fetch 요청을 보낼 수 있습니다.
      const apiURL = this.$apiURL;
      // 데이터 초기화
      this.subList = [];

      let response = await fetch(
        `${apiURL}/es/selectFac?zone_code=${item}`
      );
      let data = await response.json();

      // data.data.forEach((item) => {
      //   this.subList.push(item)
      // })
      this.subList = data.data;
      this.subListActive(0, this.subList[0].fac_code)
        this.getSubGroup(this.subList[0].fac_code)
      // console.log("subActiveIndex", this.subActiveIndex);
      // if(this.subActiveIndex === undefined ){
      //   this.subListActive(0, this.subList[0].fac_code)
      //   this.getSubGroup(this.subList[0].fac_code)
      // }else{
      //   console.log("2");
      //   console.log("subActiveIndex", this.subActiveIndex);
      //   this.subListActive(this.subActiveIndex, this.subList[0].fac_code)
      //   this.getSubGroup(this.subList[this.subActiveIndex].fac_code)
      // }
    },
    getGroup(item) {
      this.group = item;
      this.$emit("getGroupId", item)
    },
    getSubGroup(item) {
      this.subGroup = item;
      this.$emit("getSubGroupId", item)
    },
    groupToss() {
      if (this.group)
        this.$emit("getGroupId", this.group);
      if (this.subGroup)
        this.$emit("getSubGroupId", this.subGroup);
    }
  },
}
</script>

<style>
/* 이미지 깜빡이기 */
.blinking {
  -webkit-animation: blink 3s linear infinite;
  -moz-animation: blink 3s linear infinite;
  animation: blink 3s linear infinite;

}

.text-ellipsis {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>