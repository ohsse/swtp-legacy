<template>
  <b-col xl="5">


    <small-title :title="smallTitle" />

    <div class="table-bg-02 p-5" v-bind:style="{ height: '530px' }">
      <LoadingSpinner v-if="isLoading"></LoadingSpinner>
      <div v-if="isLoading == false" :style="{ height: '100%' }">
        <div class="scan_line scanning"></div>
        <table class="table table-borderless me-auto mx-auto mb-0" v-bind:style="{ width: '90%', height: '100%' }">
          <colgroup>
            <col width="70%">
            <col width="30%">
          </colgroup>
          <thead v-if="!isTrand">
            <tr>
              <td class="spend_tagname spend_co1">설비명</td>
              <td class="spend_text spend_co1" colspan="2">소비 전력</td>
            </tr>
          </thead>

          <!-- //TODO:임시로 값 지정  -->
          <tbody v-if="!isTrand">
            <tr v-for="(item, i) in title" :key="i">
              <td class="spend_co1">{{ item }}</td>
              <td class="spend_value">{{ this["FAC" + (i + 1)] }}</td>
              <td class="spend_unit">kw</td>
            </tr>
          </tbody>

          <tbody v-if="isTrand">
            <tr v-for="(item, i) in sunsiListTitle" :key="i">
              <td class="spend_co1">{{ item.TAG_DCS }}</td>
              <td class="spend_value">{{ sunsi[i] }}</td>
              <td class="spend_unit">{{ item.TAG_UNIT }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </b-col>
</template>

<script>
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
import LoadingSpinner from '@/components/ComponentCommon/LoadingSpinner.vue';
import { twoDigits } from '../Func/PowerPeakFunc';

export default {
  props: ['isTrand', 'topTitle', 'sunsi', 'sunsiTitle', 'info'],
  components: { SmallTitle, LoadingSpinner },
  data() {
    let smallTitle
    return {
      title: [],
      FAC1: 0,
      FAC2: 0,
      FAC3: 0,
      FAC4: 0,
      FAC5: 0,
      FAC6: 0,
      currentHour: '',
      smallTitle,
      isLoading: false,
      sunsiListTitle: []
    }
  },

  mounted() {
    if (this.topTitle) {
      this.smallTitle = this.topTitle
      this.sunsiData = this.sunsi
      // this.sunsiListTitle = this.sunsiTitle
      this.trandListTitleUnit();
    } else if (this.topTitle === undefined) {
      this.smallTitle = `${twoDigits(new Date().getHours())}시 주요 전력 소비 설비`;
    }
    if (!this.isTrand) {
      this.peakData();
    }
  },
  updated() {
    if (this.topTitle) {
      this.smallTitle = this.topTitle
      this.sunsiData = this.sunsi
      // this.sunsiListTitle = this.sunsiTitle
      this.trandListTitleUnit();
    } else if (this.topTitle === undefined) {
      this.smallTitle = `${twoDigits(new Date().getHours())}시 주요 전력 소비 설비`;
    }

  },
  methods: {
    trandListTitleUnit() {
      this.sunsiListTitle = []
      for (let index = 0; index < this.sunsiTitle.length; index++) {
        // console.log("this.sunsiTitle", this.sunsiTitle);
        // console.log("this.info",this.info);
        const found = this.info.find((element) => element.TAG_NAME == this.sunsiTitle[index]);
        this.sunsiListTitle.push(found ? found : {})
      }
      // console.log("제목들", this.sunsiListTitle);
    },
    peakData() {
      const apiURL = this.$apiURL;
      this.isLoading = true;
      fetch(`${apiURL}/es/peakFac`)
        .then(response => {
          this.isLoading = false
          if (!response.ok) {
            throw new Error('Failed to fetch');
          }
          return response.json();
        })
        .then(data => {
          if (data !== null) {
            for (let i = 0; i < data.data.length; i++) {
              this.title.push(data.data[i]["FAC_NAME"]);
            }
            this.FAC1 = data.data[0].kWVALUE;
            this.FAC2 = data.data[1].kWVALUE;
            this.FAC3 = data.data[2].kWVALUE;
            this.FAC4 = data.data[3].kWVALUE;
            this.FAC5 = data.data[4].kWVALUE;
            this.FAC6 = data.data[4].kWVALUE;
          }
        })
    },

  }

}

</script>
<style scoped>
/* 추가적인 스타일링이 필요하다면 여기에 작성할 수 있습니다. */
.refresh_img {
  display: inline-block;
  background: url(/src/assets/img/refresh.png) no-repeat;
  background-size: 100% 100%;
  background-position: center;
  width: 55px;
  height: 55px;
  margin-left: 52%;
}

.font_timer {
  font-family: LABDigital !important;
  font-size: 25px;
  color: #c3eaff;
  letter-spacing: 1px;
  /* line-height: 111px; */
}

.spend_co1 {
  text-shadow: 0 0 9px #5cafff;
  font-size: 18px;
  font-family: KHNPHDRegular;
  letter-spacing: normal;
  color: #c3eaff;
  align-self: center;
}

.spend_value {
  width: 15%;
  font-family: 'LAB디지털';
  font-size: 20px;
  text-align: right;
}

.spend_unit {
  width: 10%;
  margin-left: 10px;
  padding-right: 20px;
  text-align: left;
  text-shadow: 0 0 9px #5cafff;
  color: #c3eaff;
}</style>