<template lang="">
  <div class="box" v-if="isUpper">
    <template v-if="!this.isData">
      <div class="box-contents-title img-position-top">{{ items.title!="NO DATA" ? items.title : ''  }}</div>
      <div class="box-value-contents" :style="{ marginTop: '33px' }"></div>
      <div class="box-value-contents">
        <div class="box-value-contents_nodata"></div>
      </div>
      <div class="box-value-contents"></div>
      <div class="box-value-contents"></div>
    </template>
<template v-if="this.isData">
      <div class="box-contents-title img-position-top">{{ items.title }}</div>
      <div class="box-value-contents" :style="{ marginTop: '33px' }">
        <div class="box-value-contents__value" :style="{ color: 'yellow' }">
          {{ commaItems.sunsi }}
        </div>
        <div class="box-value-contents__unit">kW</div>
        <div class="chartIcon" @click="showModal(items.title)"></div>
      </div>
      <div class="box-value-contents">
        <div class="box-value-contents__value">{{ commaItems.sum }}</div>
        <div class="box-value-contents__unit">kWh</div>
      </div>
      <template v-if="items.title !='기타설비'">
      <div class="box-value-contents">
        <div class="box-value-contents__value">{{ commaItems.max }}</div>
        <div class="box-value-contents__unit">kW</div>
      </div>
      </template>
<div class="box-value-contents">
  <div class="box-value-contents__value date_text" :style="{ width: '100%', textAlign: 'center' }">
    {{ items.maxDate }}
  </div>
</div>
</template>
</div>
<div class="box box_bottom" v-if="!isUpper">
  <template v-if="!this.isData">
      <div class="box-value-contents" :style="{ marginTop: '46px' }"></div>
      <div class="box-value-contents">
        <div class="box-value-contents_nodata"></div>
      </div>
      <div class="box-value-contents"></div>
      <div class="box-value-contents"></div>
      <div
        class="box-contents-title img-position-bottom"
        :style="{ margin: '20px 0 0 0' }"
      >
        {{ items.title!="NO DATA" ? items.title : '' }}
      </div>
    </template>
  <template v-if="this.isData">
      <div class="box-value-contents" :style="{ marginTop: '46px' }">
        <div class="box-value-contents__value" :style="{ color: 'yellow' }">
          {{ commaItems.sunsi }}
        </div>
        <div class="box-value-contents__unit">kW</div>
        <div class="chartIcon" @click="showModal(items.title)"></div>
      </div>
      <div class="box-value-contents">
        <div class="box-value-contents__value">{{ commaItems.sum }}</div>
        <div class="box-value-contents__unit">kWh</div>
      </div>
      <template v-if="items.title !='기타설비'">
      <div class="box-value-contents">
        <div class="box-value-contents__value">{{ commaItems.max }}</div>
        <div class="box-value-contents__unit">kW</div>
      </div>
      </template>
  <div class="box-value-contents">
    <div class="box-value-contents__value date_text" :style="{ width: '100%', textAlign: 'center' }">
      {{ items.maxDate }}
    </div>
  </div>
  <div class="box-contents-title img-position-bottom" :style="{ margin: '20px 0 0 0' }">
    {{ items.title }}
  </div>
  </template>
</div>
</template>
<script>
import { addCommaNumber } from '@/util/addCommaNumber';
export default {
  components: {},
  props: ["isUpper", "items", "data"],
  data() {
    return {
      isData: false,
      commaItems: this.items
    };
  },
  updated() {
    if (this.items.isData == true) {
      this.isData = true;
    }

  },
  mounted() {
    this.setComma()
    if (this.items.isData == true) {
      this.isData = true;
    }
  },
  methods: {
    setComma() {
      this.commaItems.sum = addCommaNumber(this.commaItems.sum)
      this.commaItems.max = addCommaNumber(this.commaItems.max)
      this.commaItems.sunsi = addCommaNumber(this.commaItems.sunsi)
    },
    showModal(title) {
      this.$emit("emitModal", title);
    },
  },
  emits: ['emitModal'],
};
</script>
<style>
.contents-container .box .box-value-contents {
  display: flex;
  width: 100%;
  height: 27px;
}

.contents-container .box .box-value-contents__value {
  width: 50%;
  text-shadow: 0 0 9px #5cafff;
  font-size: 19px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.56;
  letter-spacing: normal;
  text-align: right;
  color: #fff;
  font-family: "LAB디지털" !important;
}

.box-value-contents_nodata {
  width: 100%;
  text-shadow: 0 0 9px #5cafff;
  font-size: 40px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1;
  letter-spacing: normal;
  text-align: center;
  color: #fff;
  font-family: "LAB디지털" !important;
}

.contents-container .box .box-value-contents__unit {
  width: 25%;
  margin-left: 15.5px;
  font-size: 18px;
  font-weight: normal;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.79;
  letter-spacing: normal;
  text-align: left;
  color: #a4ceed;
}

.box-contents-title {
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
</style>
