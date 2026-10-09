<template>
    <b-col  class="pipe_right_line1">{{ data[0].drainedTitle }}</b-col>
    <div :class="bgClass">
      <DrainedWrap v-for="(item, index) in data" :key="item" :data="item" :index="index" :length="data.length"/>
    </div>
</template>
<script>
import DrainedWrap from './DrainedWrap.vue';

export default {
    components:{
      DrainedWrap
    },
    props:{
      data : {
        type : Array
      }
    },
    data() {
        return {
            bgClass : 'pipe_background_'+this.data.length,
            title : null
        }
    },
    mounted(){
      

    }
}
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.pipe_right_line1{    
    color: #fff;
    font-family: 'KHNPHDRegular';

    text-shadow: 0 0 9px #5cafff;
    color: #c3eaff;
}
.pipe_background_1 {
  height: calc(100% / 10);
  background: url(@/assets/img/ai_song/one_pump.png) no-repeat;
  background-size: 100% 100%;
  padding: 1% 0;
}

.pipe_background_2 {
  height: calc(100% / 10 + 100% / 10);
  background: url(@/assets/img/ai_song/two_pump.png) no-repeat;
  background-size: 100% 100%;
}

.pipe_background_3 {
  height: calc(100% / 10 + 100% / 10 + 100% / 10);
  background: url(@/assets/img/ai_song/two_pump.png) no-repeat;
  background-size: 100% 100%;
}
</style>
