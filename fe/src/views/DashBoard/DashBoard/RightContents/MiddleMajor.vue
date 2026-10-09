<template>
  <b-row class="px-3">
    <div class="bg" :style="{ height: '256px' }">
      <b-col class="title_wrap mx-3" :style="{ display: 'inline-block' }">
        <h5 class="dash_title w-100 clearfix">주요배수지 현황</h5>
        <ul class="nav default-tabs w-100">
          <li v-for="(suji, index) in sujiList" :key="index" class="nav-item">
            <a style="padding-left: 8px; padding-right: 8px;"
              :class="{ 'nav-link': true, 'active': this.activeTab === index }" @click="setActiveTab(index)"
              :href="'#menu' + (index + 1)">
              {{ suji }}
            </a>
          </li>
        </ul>
      </b-col>
      <b-col class="mx-3">
        <div class="tab-content">
          <div v-for="(element, index) in major" :key="element"
            :class="{ 'tab-pane fade': true, 'active show': this.activeTab === index }">
            <div class="pump_div"
              :style="{ height: '200px', color: '#fff', fontFamily: 'KHNPHDRegular', fontSize: '13px', marginTop: '10px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }">
              <inflow-status :inflowVal="item" v-for="item in element" :key="item" />
            </div>
          </div>

        </div>
      </b-col>
    </div>
  </b-row>
</template>

<script>
import InflowStatus from '@/views/DashBoard/DashBoard/MainSmallComponents/InflowStatus.vue'

export default {
  components: { InflowStatus },
  data() {
    return {
      sujiList: [],
      activeTab: 0,
      major: [],
      majorData: [],
    }
  },
  created() {
  },
  methods: {
    setActiveTab(index) {
      // 클릭된 탭을 활성화
      this.activeTab = index;
    },
    initData(data) {
      data.sort((a, b) => a.TNK_GRP_IDX - b.TNK_GRP_IDX);

      const selectedTNK_GRP_IDX = new Set();
      const filteredData = [];

      for (const item of data) {
        if (selectedTNK_GRP_IDX.size >= 5 && !selectedTNK_GRP_IDX.has(item.TNK_GRP_IDX)) {
          break;
        }

        selectedTNK_GRP_IDX.add(item.TNK_GRP_IDX);
        filteredData.push(item);
      }

      const groupedData = [];

      const groupMap = new Map();

      filteredData.forEach(item => {
        const TNK_GRP_IDX = item.TNK_GRP_IDX;

        if (!groupMap.has(TNK_GRP_IDX)) {
          groupMap.set(TNK_GRP_IDX, []);
        }

        groupMap.get(TNK_GRP_IDX).push(item);
      });
      // console.log(groupMap)
      groupMap.forEach(group => {
        groupedData.push(group);
      });

      this.sujiList = Array.from(new Set(filteredData.map(item => item.TNK_GRP_NM.slice(0, 2))));
      // console.log(groupedData)
      groupedData.forEach((element, index) => {
        if (element.length <= 2) {
          this.majorData.push(
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[0].유입유량).toFixed(2),
              valueRate: parseFloat(element[0].IN_FO || 0).toFixed(2),
              valueRate2: parseFloat(element[1].IN_FO || 0).toFixed(2),
              waterLevel: parseFloat(element[0].수위).toFixed(2),
              waterLavel2: parseFloat(element[1].수위).toFixed(2),
              outflowVal: parseFloat(element[1].유출유량).toFixed(2),
            }
          )
        }
        else {
          this.majorData.push(
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[0].유입유량).toFixed(2),
              valueRate: parseFloat(element[0].IN_FO || 0).toFixed(2),
              valueRate2: parseFloat(element[1].IN_FO || 0).toFixed(2),
              waterLevel: parseFloat(element[0].수위).toFixed(2),
              waterLavel2: parseFloat(element[1].수위).toFixed(2),
              outflowVal: parseFloat(element[1].유출유량).toFixed(2),
            },
            {
              title: this.sujiList[index],
              inflowVal: parseFloat(element[2].유입유량).toFixed(2),
              valueRate: parseFloat(element[2].IN_FO || 0).toFixed(2),
              valueRate2: parseFloat(element[3].IN_FO || 0).toFixed(2),
              waterLevel: parseFloat(element[2].수위).toFixed(2),
              waterLavel2: parseFloat(element[3].수위).toFixed(2),
              outflowVal: parseFloat(element[3].유출유량).toFixed(2),
            }
          )
        }
        this.major.push(this.majorData)
        this.majorData = [];
      });
    }
  }
}
</script>

<style>
.waterwall_back_gosan {
  position: absolute;
  top: 143px;
  left: 0;
  width: 1590px;
  height: 690px;
  background: url(@/assets/img/local_geumgang/gosan/waterwall_gosan.png) no-repeat;
  background-size: 67% 97%;
  background-position: 56% 83%;
}

.offPump {
  background-color: #5b49491f !important;
}

.off_pump_img {
  width: 250px;
  height: 60px;
  background: #1A406F;
  opacity: 0.8;
  align-self: center;
  color: #F8C314;
  font-size: 21px;
  font-weight: bold;
  font-family: KHNPHDRegular;
  border: 2px solid #00C0FF;
  text-align: center;
  line-height: 57px;
  letter-spacing: 5px;
}

.pump_name {
  color: rgb(255, 255, 255);
  font-size: 21px;
  line-height: 57px;
  letter-spacing: 5px;
  position: absolute;
  bottom: 0;
  right: 56px;
  font-family: LAB디지털 !important;
}

.pump_name_unit {
  font-family: KHNPHDRegular;
  font-size: 17px;
  color: #c3eaff;
  margin-left: 2px;
  line-height: 57px;
  letter-spacing: 5px;
  position: absolute;
  bottom: 0;
  right: 15px;
}

.carousel_vertical .carousel__track {
  height: 150px;
}

.carousel__viewport {
  height: 100%;
}

.carousel_vertical .carousel__item {
  /* min-height: 200px; */
  width: 100%;
  height: 150px;
  background-color: var(--vc-clr-primary);
  color: var(--vc-clr-white);
  font-size: 20px;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.carousel__item img {
  width: 100%;
  height: 100%;
}

.carousel__prev,
.carousel__next {
  color: #007aff;
}

.slide-img-btn div {
  display: inline;
}

ul.slide-img-btn li:nth-child(3n) {
  margin-right: 0;
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
  width: px;
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
  flex-direction: column-reverse;
  height: 48px;
}

.animationTItle {
  width: 100%;
  display: flex;
  overflow: hidden;
  flex-direction: column-reverse;
  height: 24px;
}


.right_box1 {
  width: 83%;
  height: 30%;
  align-self: center;
  display: flex;
}

.right_box2 {
  width: 83%;
  height: 33%;
  align-self: center;
}

.right_box3 {
  width: 83%;
  height: 30%;
  align-self: center;
}

.dash_right {
  height: 100%;
  width: 25%;
  float: left;
}

.div_right {
  width: 100%;
  height: 99%;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
}

.right_title_div {
  height: 18%;
  width: 100%;
}
</style>