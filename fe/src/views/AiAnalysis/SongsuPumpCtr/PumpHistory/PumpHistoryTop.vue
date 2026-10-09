<template>
    <div :style="{ height: totalBox, overflow: 'auto' }">
        <b-row :cols="boxCols1" :style="boxStyle">
            <InfoBoxVue v-for="item in boxData1" :key="item.PUMP_GRP_DSC" :data="item" :perDatas="percentData"
                :boxLength="boxLength" />
        </b-row>
        <b-row v-show="boxRow2" :cols="boxCols2" :style="boxStyle">
            <InfoBoxVue v-for="item in boxData2" :key="item.PUMP_GRP_DSC" :data="item" :perDatas="percentData"
                :boxLength="boxLength" />
        </b-row>
        <b-row v-show="boxRow3" :cols="boxCols3" :style="boxStyle">
            <InfoBoxVue v-for="item in boxData3" :key="item.PUMP_GRP_DSC" :data="item" :perDatas="percentData"
                :boxLength="boxLength" />
        </b-row>
        <b-row v-show="boxRow4" :cols="boxCols4" :style="boxStyle">
            <InfoBoxVue v-for="item in boxData4" :key="item.PUMP_GRP_DSC" :data="item" :perDatas="percentData"
                :boxLength="boxLength" />
        </b-row>
    </div>
</template>

<script>
import InfoBoxVue from './InfoBox.vue'
export default {
    components: {
        InfoBoxVue
    },
    data() {
        return {
            boxData: null,
            percentData: {},
            boxStyle: {
                overflow: 'scroll',
                height: '200px',
                'overflow-x': 'hidden',
                'margin-left': '-10px',
                'margin-right': '10px'
            },
            boxCols1: 6,
            boxCols2: 4,
            boxCols3: 4,
            boxCols4: 3,
            boxRow2: false,
            boxRow3: false,
            boxRow4: false,
            boxData1: [],
            boxData2: [],
            boxData3: [],
            boxData4: [],
            boxLength: 0,
            totalBox: '200px'
        }
    },
    methods: {
        setData(boxData, perData) {
            this.boxData1 = boxData[0]
            this.boxCols1 = boxData[0].length % 2 === 1 ? boxData[0].length + 1 : boxData[0].length;
            //현재 파라미터값 2로 고정()
            this.boxLength = 2

            //테스트용 
            if (boxData.length > 1) {
                this.totalBox = '400px'
                if (boxData.length === 2) {
                    this.boxRow2 = true
                    this.boxStyle.height = '200px'
                    this.boxData2 = boxData[1]
                    this.boxCols2 = boxData[1].length % 2 === 1 ? boxData[1].length + 1 : boxData[1].length;
                }
                else if (boxData.length === 3) {
                    this.boxRow2 = true
                    this.boxRow3 = true
                    this.boxStyle.height = '200px'
                    this.boxData2 = boxData[1]
                    this.boxCols2 = boxData[1].length % 2 === 1 ? boxData[1].length + 1 : boxData[1].length;
                    this.boxData3 = boxData[2]
                    this.boxCols3 = boxData[2].length % 2 === 1 ? boxData[2].length + 1 : boxData[2].length;
                }
                else if (boxData.length == 4) {
                    this.boxRow2 = true
                    this.boxRow3 = true
                    this.boxRow4 = true
                    this.boxStyle.height = '200px'
                    this.boxData2 = boxData[1]
                    this.boxCols2 = boxData[1].length % 2 === 1 ? boxData[1].length + 1 : boxData[1].length;
                    this.boxData3 = boxData[2]
                    this.boxCols3 = boxData[2].length % 2 === 1 ? boxData[2].length + 1 : boxData[2].length;
                    this.boxData4 = boxData[3]
                }
            }
            this.percentData = {}
            this.percentData = perData

        }
    }
}
</script>