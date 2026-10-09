<template>
  <div  class="q-dialog fullscreen no-pointer-events q-dialog--modal">
    <div class="q-dialog__backdrop fixed-full" aria-hidden="true"></div>
    <div
      class="q-dialog__inner flex no-pointer-events q-dialog__inner--minimized q-dialog__inner--standard fixed-full flex-center"
      tabindex="-1"
    >
      <div class="q-card bg-default">
        <div class="q-card__section q-card__section--vert">
          <div class="text-h6">펌프모터 축정렬 불량</div>
        </div>
        <div class="q-card__section q-card__section--vert q-pt-none">
          <!-- 송수펌프모터 #{{ store.state.monitor1.sampleData.idx }} 모터 <span
            class="large"
            >평택계통 송수펌프모터 #2</span
          >-->
          <span class="large">{{
            store.state.monitor1.modelList[0][store.state.monitor1.sampleData.idx]
              .title
          }}</span>
          축정렬불량 여부로 인한 고장이 예상됩니다. <br />
          해당 장비에 대한 조치를 취하시겠습니까?
        </div>
        <div class="q-card__actions justify-end q-card__actions--horiz row">
          <!-- <q-btn flat label="OK" color="primary" v-close-popup /> --><button @click="$emit('modalClick')"
            class="q-btn q-btn-item non-selectable no-outline q-btn--flat q-btn--rectangle q-btn--actionable q-focusable q-hoverable confirm-btn"
            tabindex="0"
            type="button"
            role="button"
          >
            <span class="q-focus-helper"></span
            ><span
              class="q-btn__content text-center col items-center q-anchor--skip justify-center row"
              ><span class="block" >확인</span></span
            >
          </button>
        </div>
      </div>
    </div>
  </div>
  
</template>

<script>
import { useStore } from "vuex";
import { computed, reactive } from "vue";
// import axios from "axios";

export default {
  data() {
    let modalChange;
    const store = useStore();
    const state = reactive({
      model: store.state.monitor1.selectModel,
      options: computed(() => {
        let list = [];
        for (let i = 0; i < store.state.monitor1.modelList.length; i++) {
          list.push(store.state.monitor1.modelList[i].title);
        }
        return list;
      }),
      datePop: false,
      date: {
        from: "",
        to: "",
      },
      startStr: "",
      endStr: "",
      // alert: false,
    });
    return {
      store,
      state,
      modalChange
    }
  },
}
</script>

<style></style>