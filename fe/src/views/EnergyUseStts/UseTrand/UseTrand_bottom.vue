<template>
    <b-col xl="4">
        <SmallTitle :title="`${this.time} 누적 전기 사용량`" />
        <div class="bottom-contents-box">
            <!-- -----------------------Date Use Table------------------------ -->
                <UseGridHeader :cost="this.totalCost" :use="this.totalUse" />
                <UseGridRow v-for="item in items" :key="item" :items="item" />
            <!-- -----------------------Date Use Table------------------------ -->
        </div>
    </b-col>
</template>

<script>
import UseGridHeader from '@/components/ComponentCommon/UseGridHeader.vue';
import UseGridRow from '@/components/ComponentCommon/UseGridRow.vue';
import { addCommaNumber } from '@/util/addCommaNumber';
import SmallTitle from '@/components/ComponentCommon/SmallTitle.vue';
export default {
    components: {
        UseGridHeader,
        UseGridRow,
        SmallTitle
    },
    props: ['time'],
    data() {
        return {
            items: [
                { type: "경부하", usePer: 0, costPer: 0, useVal: 0, costVal: 0 },
                { type: "중부하", usePer: 0, costPer: 0, useVal: 0, costVal: 0 },
                { type: "최대부하", usePer: 0, costPer: 0, useVal: 0, costVal: 0 },
            ],
            totalCost: 0,
            totalUse: 0
        }
    },
    mounted() {
        // this.settingData()
    },
    updated() {
    },
    methods: {
        settingData(data, time) {
            const cost = []
            const use = []
            const filteredData = data?.filter(item => item.range === time);
            const Ldata = filteredData?.filter(item => item.timezone === 'L')
            const Mdata = filteredData?.filter(item => item.timezone === 'M')
            const Hdata = filteredData?.filter(item => item.timezone === 'H')
            const Tdata = filteredData?.filter(item => item.timezone === 'T')

            cost.push(Ldata[0]?.cost)
            use.push(Ldata[0]?.value)
            cost.push(Mdata[0]?.cost)
            use.push(Mdata[0]?.value)
            cost.push(Hdata[0]?.cost)
            use.push(Hdata[0]?.value)
            this.totalCost = Tdata[0]?.cost.toFixed(0)
            this.totalUse = Tdata[0]?.value.toFixed(0)

            this.items.forEach((element, i) => {
                const calculatedUsePer = (use[i] / this.totalUse * 100);
                const calculatedCostPer = (cost[i] / this.totalCost * 100);
                element.usePer = !isNaN(calculatedUsePer) ? calculatedUsePer?.toFixed(1) : 0;
                element.costPer = !isNaN(calculatedCostPer) ? calculatedCostPer?.toFixed(1) : 0;
                element.useVal = addCommaNumber(use[i]?.toFixed(0))
                element.costVal = addCommaNumber(cost[i]?.toFixed(0))
            })

            this.totalCost = addCommaNumber(this.totalCost)
            this.totalUse = addCommaNumber(this.totalUse)
        }
    },


}
</script>

<style>
.bottom-contents-box {
    align-content: flex-start;
    padding: 5px 10px;
    text-align: center;
    height: 90%;
}

.table_image {
    height: 25%;
    background-image: url(/src/assets/img/div_new.png);
    background-size: 100% 100%;
    text-align: center;
    margin-bottom: 4px;
    align-items: center;
}

.graph-bar {
    display: flex;
    background-image: url(/src/assets/img/percent_bar.png);
    background-size: 100% 100%;
    align-content: flex-start;
    height: 10px;
    mix-blend-mode: color-dodge;
}

.text-align-right {
    text-align: right;
}
</style>