<template>
  <b-row class="mb-3">
    <b-col xl="3">
      <div :class="colorClass" v-if="dataType.title">
        <span>{{ dataType.title }}</span>
        <span>{{ dataType.title2 }}</span>
      </div>
    </b-col>
    <b-col xl="9">
      <div class="blue_round box-bg" :style="{ width: '280px' }">
        <div class="w-100 d-flex flex_center_between" :style="{ height: '30px' }">
          <div class="content__text-box">{{ dataType.subTitle }}</div>
          <div class="content__value-box" :style="{ width: '200px' }" v-if="dataType.subValue">
            <span :style="{ fontSize: '22px' }">{{ dataType.subValue }}</span>
            <span class="unit">{{ dataType.subUnit }}</span>
          </div>
        </div>
        <div class="w-100 d-flex flex_center_between" :style="{ height: '70px' }">
          <div :class="animationTitle">
            <RotationItem :data="itemData" v-for="(itemData, index) in dataType.innerData" :key="index" />
          </div>
        </div>
      </div>
    </b-col>
  </b-row>
</template>

<script>
import RotationItem from './RotationItem.vue';
export default {
  components: { RotationItem },
  props: [
    'dataType'
  ],
  data() {
    return {
      colorClass: this.dataType.color + " m-auto",
      animationTitle: this.dataType.isSub ? 'animationTItle-two' : 'animationTItle'
    }
  }
};
</script>
<style>
.flex_center_between {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.box-bg {
  background: url(@/assets/img/dash_top.png) no-repeat !important;
  background-size: 100% 100% !important;
  width: 270px;
  height: 100px;
  padding: 0px 25px;
  justify-content: unset;
}

.unit {
  font-size: 16px;
  color: #a4ceed;
  font-family: "KHNPHDRegular";
  margin-left: 5px;
}

.blue_round {
  width: 105px;
  height: 100px;
  color: #fff;
  text-shadow: 0 0 9px #5cafff;
  font-family: "KHNPHDRegular";
  background: url(@/assets/img/00_top_roundline_b.png) no-repeat;
  background-size: 100%;
  background-position: center;
  display: flex;
  font-size: 16px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.green_round {
  width: 105px;
  height: 100%;
  color: #fff;
  text-shadow: 0 0 9px #5cafff;
  font-family: "KHNPHDRegular";
  background: url(@/assets/img/00_top_roundline_g.png) no-repeat;
  background-size: 100%;
  background-position: center;
  display: flex;
  font-size: 16px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.content__value-box {
  width: 140px;
  text-shadow: rgba(209, 250, 255, 0.5) 0px 0px 5px;
  font-size: 18px;
  text-align: right;
  color: rgb(242, 251, 255);
  font-family: LAB디지털 !important;
  background-position: center center;
}

.content__text-box {
  width: 75px;
  background-size: 100% 20px;
  background-position-y: bottom;
  text-shadow: 0 0 9px #5cafff;
  font-family: KHNPHUotfR;
  font-size: 16px;
  line-height: 1.5;
  text-align: left;
  color: #fff;
}

.animationTItle-two {
  width: 100%;
  display: flex;
  overflow: hidden;
  flex-direction: row-reverse;
  height: 48px;
}

.animationTItle {
  width: 100%;
  display: flex;
  overflow: hidden;
  flex-direction: column-reverse;
  height: 24px;
}
</style>
