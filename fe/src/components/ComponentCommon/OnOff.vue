<template>
  <div class="myButton" :class="fontCss">{{ pumpStatus }}</div>
</template>

<script>
export default {
  props: ['pumpData'],
  data() {
    let pumpStatus = '';
    let num = 0;
    return {
      pumpStatus,
      num,
      fontCss: 'onCss'
    }
  },
  mounted() {
    this.pumpOnOff();
  },
  methods: {
    pumpOnOff() {
      // props 에서 pumpData 받은 거 사용, this.num -> this.pumpData 로 변경하기 
      if (this.pumpData === 'Off') {
        this.fontCss = 'offCss'
        this.pumpStatus = 'OFF'
      } else {
        this.fontCss = 'onCss'
        this.pumpStatus = 'ON'
      }
    }
  },
}
</script>

<style>
.myButton {
  width: 40px;
  height: 20px;
  border-radius: 30px;
  /*box-shadow: 0px 4px 6px -1px #000000;*/
  /*background: linear-gradient(to bottom, #808080 5%, #757575 100%);*/
  background-color: #3b506a;
  /*border: 1px solid #555555;*/
  justify-content: center;
  align-items: center;
  display: flex;
  cursor: pointer;
  font-family: 'KHNPHDBold';
  font-size: 12px;
  font-weight: bold;
  padding: 6px 24px;
  /*border: 1px solid #000000;*/
   cursor: default;
   
}
.myButton:hover {
  cursor: default; /* 마우스를 올렸을 때도 커서를 화살표로 유지 */
}
/* .myButton:hover {
  background: linear-gradient(to bottom, #757575 5%, #808080 100%);
  background-color: #757575;
  box-shadow: 0px 6px 8px -3px #000000;

} */

.onCss {
  color: black;
  background-color: #b3e5fc;
  text-shadow: 0 0 0px #5cafff;
  -webkit-box-shadow: 0px 0px 5px 1px rgba(180, 223, 250, 0.6);
  -moz-box-shadow: 0px 0px 5px 1px rgba(180, 223, 250, 0.6);
  box-shadow: 0px 0px 5px 1px rgba(180, 223, 250, 0.6);
}

.offCss {
  color: black;
  text-shadow: 0 0 0px #1f1f1f;
}
</style>
