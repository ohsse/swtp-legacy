<template>
    <b-row class="px-3 mb-4">
        <b-col class="position-relative rounded-bottom rounded-lg"
          :style="{ marginTop: '35px', paddingTop: '12px', background: '#0c0e18', border: '1px solid #263750', borderTopRightRadius: '5px' }">
          <div class="title-round position-absolute" :style="{ top: '-32px', left: '-1px' }">
            <div class="sub-title mx-2 float-start" :style="{ marginTop: '3px' }">{{props?.plantVal[0].GRP_NM}}</div>
            <div class="float-end">
              <button class="btn btn-sm bg-primary" :style="{ height: '28px' }" @click="pumpSetting(props?.plantVal[0].GRP_IDX)">
                <i class="bi bi-gear-fill"></i>
              </button>
            </div>
          </div>
          <btn-list v-for="(item, index) in props?.plantVal" :key="index" :btns="item"/>
        </b-col>
      </b-row>
</template>
<script>
import { watch } from 'vue'
import BtnList from './BtnList.vue';
import { useStore } from 'vuex';
export default {
    components:{
        BtnList
    },
    props:['plantVal'],
    setup(props) {
      const store = useStore()
      watch(()=>props, ()=>{
      })
      const pumpSetting = (pumpIdx)=>{
        store.commit("precision/settingPump", pumpIdx)
      }
      return {props, pumpSetting}
    }
}
</script>
<style>
    
</style>