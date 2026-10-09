<template>
  <b-card class="bg-transparent border-0 p-0" body-class="bg-transparent p-0">
    <SmallTitle :title="'관망해석 현황'" />

    <b-row class="g-3 mt-2">
      <b-col md="6" class="px-3 mt-0">
        <div class="d-flex flex-column gap-2">
          <div class="d-flex align-items-center gap-2">
            <img src="@/assets/img/pressure.png" alt="유량 아이콘" class="icon" />
            <span class="cal-title-font">유량</span>
          </div>
          <b-row class="row g-3">
            <b-col class="d-flex">
              <div class="glow-tile d-flex flex-column g-2 flex-fill">
                <div class="cal-title-font text-start text-white align-self-baseline">적합</div>
                <div class="glow-value d-flex justify-content-end">
                  <span class="glow-num">{{ flowData.good.count }}</span>
                  <span class="glow-pct">({{ flowData.good.percent }}%)</span>
                </div>
              </div>
            </b-col>
            <b-col class="d-flex">
              <div class="glow-tile d-flex flex-column g-2 flex-fill">
                <div class="cal-title-font text-start text-white align-self-baseline">적정</div>
                <div class="glow-value d-flex justify-content-end">
                  <span class="glow-num">{{ flowData.normal.count }}</span>
                  <span class="glow-pct">({{ flowData.normal.percent }}%)</span>
                </div>
              </div>
            </b-col>
            <b-col class="d-flex">
              <div class="glow-tile d-flex flex-column g-2 flex-fill">
                <div class="cal-title-font text-start text-white align-self-baseline">미흡</div>
                <div class="glow-value d-flex justify-content-end">
                  <span class="glow-num">{{ flowData.bad.count }}</span>
                  <span class="glow-pct">({{ flowData.bad.percent }}%)</span>
                </div>
              </div>
            </b-col>
          </b-row>
        </div>
      </b-col>

      <b-col md="6" class="px-3 mt-0">
        <div class="d-flex flex-column gap-2">
          <div class="d-flex align-items-center gap-2">
            <img src="@/assets/img/pressure.png" alt="압력 아이콘" class="icon" />
            <span class="cal-title-font">압력</span>
          </div>
          <div class="row g-3">
            <b-col class="d-flex">
              <div class="glow-tile d-flex flex-column g-2 flex-fill">
                <div class="cal-title-font text-start text-white align-self-baseline">적합</div>
                <div class="glow-value d-flex justify-content-end">
                  <span class="glow-num">{{ pressureData.good.count }}</span>
                  <span class="glow-pct">({{ pressureData.good.percent }}%)</span>
                </div>
              </div>
            </b-col>
            <b-col class="d-flex">
              <div class="glow-tile d-flex flex-column g-2 flex-fill">
                <div class="cal-title-font text-start text-white align-self-baseline">적정</div>
                <div class="glow-value d-flex justify-content-end">
                  <span class="glow-num">{{ pressureData.normal.count }}</span>
                  <span class="glow-pct">({{ pressureData.normal.percent }}%)</span>
                </div>
              </div>
            </b-col>
            <b-col class="d-flex">
              <div class="glow-tile d-flex flex-column g-2 flex-fill">
                <div class="cal-title-font text-start text-white align-self-baseline">미흡</div>
                <div class="glow-value d-flex justify-content-end">
                  <span class="glow-num">{{ pressureData.bad.count }}</span>
                  <span class="glow-pct">({{ pressureData.bad.percent }}%)</span>
                </div>
              </div>
            </b-col>
          </div>
        </div>
      </b-col>
    </b-row>
  </b-card>
</template>

<script>
import SmallTitle from "@/components/ComponentCommon/SmallTitle.vue";

export default {
  name: "AnalysisStatus",
  components: { SmallTitle },
  props: {
    flowData: {
      type: Object,
      required: true,
    },
    pressureData: {
      type: Object,
      required: true,
    },
  },
  methods: {
    nf(n) {
      // totalFlowCalc와 동일
      return n == null ? "-" : Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });
    },
    pnf(n) {
      // minimum/maximumFractionDigits: 2 => toFixed(2)와 동일 (소수점 2자리)
      return n == null ? "-" : Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    pf(n) {
      // 100을 곱한 값에 콤마 + 소수점 0자리 + "%"
      return n == null ? "-" : Number(Number(n) * 100).toLocaleString(undefined, { maximumFractionDigits: 0 }) + "%";
    },
  },
};
</script>

<style scoped>
/* 부모 컴포넌트에 있던 glow-tile 관련 스타일을 그대로 가져옵니다. */
.glow-tile {
  position: relative;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 4px;
  padding: 10px;
  border: 1px solid #76a4f1;
}

.glow-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.glow-num {
  font-size: 30px;
  font-family: LAB디지털 !important;
  line-height: 1;
  color: #fff;
  font-weight: 400;
  letter-spacing: 0.06em;
  text-shadow: 0 0 8px rgba(144, 195, 255, 0.9),
    0 0 18px rgba(144, 195, 255, 0.45), 0 0 32px rgba(144, 195, 255, 0.25);
}

.glow-pct {
  font-size: 24px;
  font-family: LAB디지털 !important;
  color: #9fc7ff;
  font-weight: 400;
  text-shadow: 0 0 6px rgba(144, 195, 255, 0.85),
    0 0 14px rgba(144, 195, 255, 0.35);
}

/* 아이콘 스타일 등 필요한 다른 스타일도 가져오세요. */
.icon {
  width: 20px;
  /* 예시 크기 */
  height: 20px;
}

.cal-title-font {
  /* 예시 스타일 */
  color: white;
  font-size: 16px;
}
</style>