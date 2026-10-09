<template>
  <div :class="className" :style="displayStyle">
    <div class="popup-top-edge"></div>
    <div class="popup-bottom-edge"></div>
    <div class="popup-contents">
      <HoverItems :grpList="hoverVal" :alarmHoverGrpList="alarmHoverGrpList"/>
    </div>
  </div>
</template>

<script>
import HoverItems from '@/views/DashBoard/DashBoard/HoverPopup/HoverItems.vue'
import { useStore } from 'vuex';
export default {
  components: {
    HoverItems,
  },
  props: [
    'hoverVal', 'alarmHoverGrpList'
  ],
  data() {
    const store = useStore();
    return {
      values: [],
      displayStyle: {
        display: 'block'
      },
      className: 'hoverInfo',
      mainValue: 0,
      grpList: [],
      alarmGrpList : [],
      store
    }
  },
  mounted() {
    this.getData();
  },
  updated() {
  },
  methods: {
    show() {
      this.displayStyle.display = 'block';
      this.className = 'hoverInfo'
    },
    hide() {
      this.className = 'hoverInfo hoverInfoNone'
    },
    initHide() {
      this.displayStyle.display = 'none';
    },
    async getData() {
      
      let res = await fetch(
        `${this.store.state.globalIP}/api/v1/main/motorDataAll`
        );
      let res2 = await fetch(
        `${this.store.state.globalIP}/api/v1/main/motorAlarm`
        );
        let data = await res.json();
        let data2 = await res2.json();
        if (data !== null) {
          for (let index = 0; index < data.datas.length; index++) {
            // console.log("check", data.datas[index]);
            this.grpList.push(data.datas[index]);
            this.alarmGrpList.push(data2.datas[index])
          }
        }
        console.log("popup alarm ----", this.alarmGrpList);
        
        this.$emit('songsuList', this.grpList, this.alarmGrpList)
      }
  }
}
</script>

<style>
.main_info_up {
  -webkit-animation: up 0.5s linear;
  -moz-animation: up 0.5s linear;
  animation: up 0.5s linear;
}

.main_info_down {
  -webkit-animation: down 0.5s forwards;
  -moz-animation: down 0.5s forwards;
  animation: down 0.5s forwards;
}

.div_small {
  height: 100%;
  display: flex;
  align-items: center;
  text-align: center;
  flex-direction: column;
}

.dash_border_img {
  background: url(@/assets/img/00_table_bg_long.png) no-repeat;
  background-position: center;
  background-size: 100% 100%;
}


.hoverInfo .popup-top-edge {
  position: absolute;
  top: 1px;
  margin: 4px;
  width: 98%;
  height: 11px;
  background: url(@/assets/img/popup_title_top_edge.png) no-repeat;
  background-size: 100%;
  background-position: center;
}

.hoverInfo .popup-bottom-edge {
  position: absolute;
  bottom: 1px;
  margin: 4px;
  width: 98%;
  height: 11px;
  background: url(@/assets/img/popup_title_bottom_edge.png) no-repeat;
  background-size: 100%;
  background-position: center;
}

.hoverInfo .popup-contents {
  width: 100%;
  height: 100%;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.hoverInfo .popup-contents .items .title2 {
  color: white;
  text-shadow: 0 0 9px #5cafff;
  margin-bottom: 10px;
  font-size: 18px;
}

.hoverInfo .popup-contents .items .item-list {
  width: 100%;
  display: flex;
  gap: 15px;
}

.hoverInfo .popup-contents .items {
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  gap: 10px;
}

.hoverInfo .popup-contents .items::after {
  content: "";
  width: 100%;
  position: absolute;
  bottom: -15px;
  left: 50%;
  transform: translateX(-50%);
  height: 1px;
  background: linear-gradient(to right, #70a8dbb9, #2d6599, #13283ba1);
}

.hoverInfo .popup-contents .items:last-child::after {
  height: 0;
}

.hoverInfo .popup-contents .items .item-list .item-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  width: 60px;
}

.hoverInfo .popup-contents .items .item-list .item-box .item {
  width: 12px;
  height: 12px;
  background: #b4dffa;
  box-shadow: 0 0 6px 0 #5cafff;
  border-radius: 15px;
}
.hoverInfo .popup-contents .items .item-list .item-box .error {
  width: 12px;
  height: 12px;
  background: hsla(0, 93%, 61%, 0.745);
  box-shadow: 0 0 6px 0 hsla(0, 93%, 61%, 0.745);
  border-radius: 15px;
}

.hoverInfo .popup-contents .items .item-list .item-box .item-title {
  color: #c3eaff;
  font-size: 14px;
  text-align: center;
}

@keyframes move-up-building {
  from {
    transform: translateY(380px);
  }

  to {
    transform: translateY(0px);
  }
}

@keyframes move-down-popup {
  from {
    transform: translateY(0px);
  }

  to {
    transform: translateY(380px);
    opacity: 0;
    /* 투명하게 만들어 사라지게 함 */
  }
}

.zindex10 {
  z-index: 10;
}

.zindex10 {
  opacity: 0 !important;
}

.opacity50 {
  opacity: 0.5 !important;
}

.opacity100 {
  opacity: 100 !important;
}
</style>