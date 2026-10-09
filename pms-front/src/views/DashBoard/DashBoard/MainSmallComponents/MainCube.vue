<template>
  <div class="cubeList">
    <div class="aura"></div>
    <!-- Text에 펌프모터, 가동반, 변압기 등 텍스트 기입 -> MapContents에서 컴포넌트 사용하고 따로 텍스트 값 넣어야함 -->
      <div class="onCube"> 
        <span class="main_per_unit">{{ formattedText }}</span>
      </div>
  </div>
</template>

<script>
import { useStore } from "vuex";
export default {
  props: [
    'nameText'
  ],
  computed: {
    formattedText() {
      // 데이터에 줄바꿈 문자를 추가하여 반환
      const store = useStore();
      const area = store.state.area;
      let text; 
      if (area == 'gosan') {
        text = this.nameText[0]?.grp_nm.substr(0,5) + "\n" + this.nameText[0]?.grp_nm.substr(-3)
      } else {
        text = this.nameText[0]?.grp_nm
      } 
      return text;
    }
},
}
</script>

<style>
.cube0 {
  z-index: 5;
  pointer-events: none;
  width: 90px;
  height: 90px;
  background: url(@/assets/img/cube__inner.png) 100% 100% no-repeat;
  background-size: 90px 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  top: 10px;
  left: -37px;
  animation: updown ease-in-out 2s infinite alternate;
  position: absolute;
}

.cube1 {
  z-index: 5;
  pointer-events: none;
  width: 90px;
  height: 90px;
  background: url(@/assets/img/cube__inner.png) 100% 100% no-repeat;
  background-size: 90px 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  top: 10px;
  left: 52px;
  animation: updown ease-in-out 2s infinite alternate;
  position: absolute;
}
.onCube{
  z-index: 5;
  pointer-events: none;
  width: 90px;
  height: 90px;
  background: url(@/assets/img/cube__inner.png) 100% 100% no-repeat;
  background-size: 90px 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  top: 10px;
  left: 7px;
  animation: updown ease-in-out 2s infinite alternate;
  position: absolute;
}

.aura {
  width: 110px;
  height: 150px;
  background: url(@/assets/img/aura_bottom.png) 100% 100% no-repeat;
  display: block !important;
  box-sizing: inherit;
  pointer-events: none;
  top: 0px;
  left: 0px;
  animation: blink-v 3s infinite alternate;
  position: absolute;
}

@keyframes updown {
  from {
    transform: translateY(0px)
  }

  to {
    transform: translateY(20px)
  }
}

@keyframes blink-v {
  0% {
    opacity: 0.5;
  }

  100% {
    opacity: 1;
  }
}

.main_per_unit {
  font-size: 13px;
  margin-top: 2px;
  padding: 12px;
  font-family: KHNPHUotfR, sans-serif !important;
  color: #c3eaff;
  letter-spacing: 1px;
  line-height: 22px;
  text-align: center;
}

.cubeList {
  position: absolute;
  top: 319px;
  left: 618px;
  width: 120px;
  height: 120px;
}
</style>