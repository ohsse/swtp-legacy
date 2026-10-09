<template>
  <b-col xl="5">
    <small-title :title="title" />
    <table class="table table-borderless juyoinja plate_area mb-0" style="height: 100%;">
      <colgroup>
        <col width="70%" />
        <col width="20%" />
        <col width="10%" />
      </colgroup>
      <tbody>
        <tr>
          <td class="detail_text">총 순시 전력</td>
          <td class="detail_value">{{ sunsiPower }}</td>
          <td class="text_val_unit">kw</td>
        </tr>
        <tr>
          <td class="detail_text">송수 펌프 순시 전력</td>
          <td class="detail_value">{{ targetPower }}</td>
          <td class="text_val_unit">kw</td>
        </tr>
        <tr>
          <td class="detail_text">요금 적용 전력 피크</td>
          <td class="detail_value">{{ costPower }}</td>
          <td class="text_val_unit">kw</td>
        </tr>
      </tbody>
    </table>
  </b-col>
</template>

<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";
export default {
  components: { SmallTitle },
  props: ['sunsiPower', 'targetPower', 'costPower'],
  data() {
    return {
      title: "주요인자",
      // 총순시전력: 0,
      // 펌프순시전력: 0,
      // 요금적용전력: 0,
    };
  },
  mounted() {
    // this.fetchData();
  },
  methods: {
    // fetchData() {
    //   const apiURL = this.$apiURL;
    //   let _this = this;
    //   fetch(`${apiURL}/ai/selectPeakControl`)
    //     .then((response) => {
    //       if (!response.ok) {
    //         throw new Error("Failed to fetch");
    //       }
    //       return response.json();
    //     })
    //     .then((data) => {
    //       if (data !== null) {
    //         _this.총순시전력 = data.data[0].allPwi;
    //         _this.총순시전력 = Math.ceil(_this.총순시전력);
    //         _this.총순시전력 = _this.총순시전력.toLocaleString();

    //         _this.펌프순시전력 = data.data[0].pumpPwi;
    //         _this.펌프순시전력 = Math.ceil(_this.펌프순시전력);
    //         _this.펌프순시전력 = _this.펌프순시전력.toLocaleString();

    //         _this.요금적용전력 = data.data[0].costPwr;
    //         _this.요금적용전력 = Math.ceil(_this.요금적용전력);
    //         _this.요금적용전력 = _this.요금적용전력.toLocaleString();
    //       } else {
    //         console.log("no data");
    //       }
    //     })
    //     .catch((error) => {
    //       console.error("Error:", error);
    //     });
    // },
  },
};
</script>
<style>
.plate_area {
  background: url("@/assets/img/plate_img.png") no-repeat;
  background-size: 100% 20%;
  background-position-y: 280px;
  height: 230px;
}
</style>
