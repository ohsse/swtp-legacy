<template>
  <LoadingSpinner class="loading-container" v-if="isLoading"></LoadingSpinner>
  <div>
    <b-container fluid class="main-content px-5">
      <!-- 타이틀 시작 -->
      <BigTitle :title="'시설별 사용량'" />
      <!-- 타이틀 끝 -->
      <div class="contents-container">
        <b-row>
          <b-col class="d-flex justify-content-end mb-4">
            <CalendarBox @chartData="chartData" :noMount="true" />
          </b-col>
        </b-row>
        <b-row class="gx-4 mb-4">
          <b-row class="contents position-relative" :style="{ height: '376px' }">
            <ZoneUse_DataFlowComponentVue v-for="item in items" :key="item" :items="item" :total="this.dbTotal"
              :sunsiTotal="this.sunsiTotal" :data="this.data1" :length="this.items.length"
              @showChartModal="showChartModal" />
            <!-- 애니메이션 시작 -->
            <div data-v-6e5b1fe1 class="position-absolute centered-div" style="height: 20%">
              <div class="water-h-flow-img one fadein" style="pointer-events: none">
                <div class="buble delay1"></div>
              </div>
              <div class="water-h-flow-img two fadein" style="pointer-events: none">
                <div class="buble delay1"></div>
              </div>
              <div class="water-h-flow-img three fadein" style="pointer-events: none">
                <div class="buble delay1"></div>
              </div>
              <div class="water-h-flow-img four fadein" style="pointer-events: none">
                <div class="buble delay1"></div>
              </div>
              <div class="water-h-flow-img five fadein" style="pointer-events: none">
                <div class="buble delay1"></div>
              </div>
              <div class="water-h-flow-img six fadein" style="pointer-events: none">
                <div class="buble delay1"></div>
              </div>
            </div>
            <!-- 애니메이션 끝 -->
          </b-row>
        </b-row>
        <b-row class="mt-4">
          <BottomLeft ref="BottomLeft" :items="items" />
          <BottomMid ref="BottomMid" />
          <BottomRig ref="BottomRig" :items="items" />
        </b-row>
      </div>
    </b-container>

    <ZoneUseModal ref="ZoneUseModal" v-if="isModalOpen" @closeModal="closeModal" />
    <!-- 본문 컨텐츠 끝 -->

  </div>
</template>

<script>
import CalendarBox from "@/components/ComponentCommon/CalendarBox.vue";
import BottomLeft from "@/views/EnergyUseStts/ZoneUse/ZoneUse_bottomLeft.vue";
import BottomMid from "@/views/EnergyUseStts/ZoneUse/ZoneUse_bottomMid.vue";
import BottomRig from "@/views/EnergyUseStts/ZoneUse/ZoneUse_bottomRig.vue";
import ZoneUse_DataFlowComponentVue from "@/views/EnergyUseStts/ZoneUse/ZoneUse_DataFlowComponent.vue";
import ZoneUseModal from "@/views/EnergyUseStts/ZoneUse/ZoneUseModal.vue";
import LoadingSpinner from '@/components/ComponentCommon/LoadingSpinner.vue';
import BigTitle from "@/components/ComponentCommon/BigTitle.vue"
import Swal from 'sweetalert2'
export default {
  layout: "default",
  name: "ZoneUse",
  components: {
    CalendarBox,
    BottomLeft,
    BottomMid,
    BottomRig,
    ZoneUse_DataFlowComponentVue,
    ZoneUseModal,
    LoadingSpinner,
    BigTitle
  },
  data() {
    return {
      total: 0,
      dbTotal: 0,
      sunsiTotal: 0,
      sunsiHap: 0,
      items: [
        // [{ title: "관리동" }, { title: "급속여과지동" }],
        // [{ title: "활성탄흡착지동" }, { title: "송수펌프동" }],
        // [{ title: "약품동" }, { title: "염소투입동" }],
        // [{ title: "오존설비동" }, { title: "탈수기동내부" }],
      ],
      sumData: [],
      apiURL: this.$apiURL,
      isShow: false,
      isModalOpen: false,
      isLoading: false,
    };
  },
  mounted() {
    this.$emit("onChangeBgClass", false);
  },
  updated() {
    if (this.isModalOpen) {
      this.$refs.ZoneUseModal.createChart(this.title, this.data3);
    }
  },
  created() {
    const now = new Date();
    const DayFrom = new Date(now.setDate(now.getDate()));
    const DayTo = new Date(now.setDate(now.getDate() + 1));
    let dateFrom = this.formattedDate(DayFrom);
    let dateTo = this.formattedDate(DayTo);
    this.getData(dateFrom, dateTo, "h");
    setInterval(() => {
      this.getSunsiData();
    }, 1000 * 60);
  },

  methods: {
    async getData(dateFrom, dateTo, selected) {
      this.isLoading = true;

      const requests = [
        fetch(`${this.apiURL}/es/selectZoneUseList?start_date=${dateFrom}&end_date=${dateTo}&time_type=${selected}`),
        fetch(`${this.apiURL}/es/selectZoneUseList_sum?start_date=${dateFrom}&end_date=${dateTo}&time_type=${selected}`),
        fetch(`${this.apiURL}/es/sunsiChart`),
        fetch(`${this.apiURL}/st/selectZone`)
      ];

      try {
        const responses = await Promise.allSettled(requests);

        this.data1 = responses[0].status === 'fulfilled' ? await responses[0].value.json() : null;
        this.data2 = responses[1].status === 'fulfilled' ? await responses[1].value.json() : null;
        this.data3 = responses[2].status === 'fulfilled' ? await responses[2].value.json() : null;
        this.data4 = responses[3].status === 'fulfilled' ? await responses[3].value.json() : null;

        this.data1 = this.data1.data;
        this.data2 = this.data2.data;
        this.data3 = this.data3.data;
        this.data4 = this.data4.data;
      } catch (error) {
        Swal.fire({
          animation: false,
          text: "No Data",
        });
      }

      this.initData(this.data1, this.data2, this.data4);
      this.getSunsiData();
      
      await this.$refs.BottomMid.createChart(this.data2);
      await this.$refs.BottomLeft.createChart(this.data2, this.sumData);
      await this.$refs.BottomRig.createChart(this.data1, this.sumData);
      
      this.isLoading = false;
    },
    async getSunsiData() {
      let response = await fetch(`${this.apiURL}/es/sisul_sunsi`);
      this.sunsiHap = 0
      let data = await response.json();
      data = data.data;
      this.sunSi = data;

      this.sunSi?.forEach((element) => {
        this.items?.forEach((titles) => {
          titles.forEach((item) => {
            if (element.zone_name == item.title) {
              item.sunsi = element.y;
              if (item.title != "태양광") {
                this.sunsiHap += element.y
              }
            }
          });
        });
      });
      const totalElec = this.data2?.filter(item => item.zone_code == '총전력량')
      const totalSunsi = this.data2?.filter(item => item.zone_code == '총전력')
      if (totalElec?.length > 0) {
        this.items?.forEach(item => {
          let data = item.filter(item => item.title == "기타설비")
          if (data?.length > 0) {
            data[0].sunsi = totalSunsi[0].y - this.sunsiHap
            data[0].sunsi = data[0].sunsi.toFixed(2)
          }
        })
      }
    },
    formattedDate(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    },
    chartData(dateFrom, dateTo, selected) {
      this.getData(dateFrom, dateTo, selected);
    },
    initData(data1, data2, data4) {
      this.items = []
      this.total = 0
      for (var i = 0; i < data4?.length; i++) {

        let title = [{ title: data4[i].zone_code }];
        if (i + 1 < data4.length) {
          title.push({ title: data4[++i].zone_code });
        } else {
          title.push({ title: 'NO DATA' });
        }
        this.items.push(title);
      }
      this.sumData = [];
      this.items.forEach((item, i) => {
        item.forEach((element, j) => {
          item[j].isFirst = i <= 0 ? true : false;
          item[j].isLast = i >= this.items.length - 1 ? true : false;
          element.isData = false;
          element.max = 0;
          element.sum = 0;
          element.sunsi = 0;
          element.total = 0;
          element.maxDate = "";
        });
        this.sumData.push(item[0].title);
        this.sumData.push(item[1].title);
      });
      if (data1 != null) {
        data1?.forEach((element) => {
          this.items?.forEach((titles) => {
            titles.forEach((item) => {
              if (element.zone_code == item.title) {
                item.isData = true;
                if (item.max < element.y) {
                  item.max = element.y;
                  item.maxDate = element.x;
                }
              }
            });
          });
        });
        data2?.forEach((element) => {
          this.items?.forEach((titles) => {
            titles.forEach((item) => {
              if (element.zone_code == item.title) {
                if (item.title != "태양광") {
                  item.sum = element.y;
                  this.total += element.y;
                }
                else {
                  item.sum = element.y;
                  this.total -= element.y;
                }
              }
            });
          });
        });
        const totalElec = data2?.filter(item => item.zone_code == '총전력량')
        const totalSunsi = data2?.filter(item => item.zone_code == '총전력')
        if (totalElec?.length > 0) {
          this.dbTotal = totalElec[0].y
          this.items?.forEach(item => {
            let data = item.filter(item => item.title == "기타설비")
            if (data?.length > 0) {
              data[0].isData = true;
              data[0].sum = totalElec[0].y.toFixed(2) - this.total
              data[0].sum = data[0].sum.toFixed(2)
              // data[0].sunsi = totalSunsi[0].y - this.sunsiHap
            }
          })
        }
        if (totalSunsi?.length > 0) {
          this.sunsiTotal = totalSunsi[0].y
        }

      }

    },
    showChartModal(title) {
      this.title = title;
      this.isModalOpen = true;
    },
    closeModal() {
      this.isModalOpen = false;
    },
  },
  emits: ['onChangeBgClass']
};
</script>

<style scoped>
.contents-container .box {
  display: flex;
  flex-flow: column;
  align-items: center;
  width: 100%;
  height: 50%;
  margin: -26px 0 55px 0;
}

.contents-container .box {
  height: 32px;
  background: url(@/assets/img/title_bar.png) no-repeat;
  background-size: 100% 100%;
  mix-blend-mode: luminosity;
  color: #ffffff;
  font-family: "KHNPHDBold";
  font-size: 18px;
  text-shadow: 0 0 10px #000;
  line-height: 2;
  text-indent: 3%;
  width: 100%;
  text-align: center;
}

.contents-container .box .box-top-title {
  text-shadow: 0 0 9px #5cafff;
  font-size: 20px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.56;
  letter-spacing: normal;
  text-align: right;
  width: 85%;
  color: #fff;
}

.contents-container .box .box-bottom {
  display: flex;
  width: 100%;
  height: 43px;
  margin-top: 10px;
  -o-object-fit: contain;
  object-fit: contain;
  border: solid 1px rgb(72 156 242);
  border-radius: 5px;
}

.contents-container .box .box-bottom__value {
  width: 100%;
  text-shadow: 0 0 5px rgb(209 250 255/ 50%);
  font-family: "LAB디지털" !important;
  font-size: 24px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.6;
  letter-spacing: normal;
  text-align: right;
  color: #ffffff;
}

.contents-container .box .box-bottom__unit {
  margin: 0 5px 0 10px;
  font-size: 16px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 2.7;
  letter-spacing: normal;
  text-align: left;
  color: #417db9;
}

.one {
  position: absolute;
  width: 120px;
  height: 8px;
  left: 100px;
  animation: 4s fadein;
}

.two {
  position: absolute;
  width: 120px;
  height: 8px;
  left: 400px;
}

.three {
  position: absolute;
  width: 120px;
  height: 8px;
  left: 700px;
}

.four {
  position: absolute;
  width: 120px;
  height: 8px;
  left: 1000px;
}

.five {
  position: absolute;
  width: 120px;
  height: 8px;
  left: 1300px;
}

.six {
  position: absolute;
  width: 120px;
  height: 8px;
  right: 160px;
}

.buble {
  background-image: url("@/assets/img/pipe_elec.png");
  background-size: 100% 100%;
  width: 20px;
  height: 20px;
  position: absolute;
  left: 120px;
  top: -7px;
  transform: rotate(45deg);
}

.delay1 {
  animation: 3s slide-right;
  animation-delay: 0s;
  animation-iteration-count: infinite;
}

.fadein {
  animation: 3s fadein;
  animation-delay: 0s;
  animation-iteration-count: infinite;
}

.centered-div {
  position: absolute;
  top: 40%;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.loading-container {
  position: fixed;
  /* 절대 위치 설정 */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  /* 반투명한 배경 */
  z-index: 9999;
  /* 다른 요소 위에 표시하기 위한 z-index 설정 */
  display: flex;
  justify-content: center;
  /* 수평 가운데 정렬 */
  align-items: center;
}

@keyframes slide-right {
  from {
    margin-left: -200px;
  }

  to {
    margin-left: 0%;
  }
}

@keyframes fadein {
  0% {
    opacity: 0;
  }

  50% {
    opacity: 1;
  }

  100% {
    opacity: 0;
  }
}
</style>
