<template>
    <div class="w-100" :style="{ marginBottom: '10px' }">
        <p class="mb-4 mt-4"> {{ title }}</p>
        <div class="plate_area W-100"
            :style="{ height: plateHeight, backgroundSize: '100% 40%', backgroundPositionY: backPosiY }">
            <div v-for="(element, index) in item" :key="element" class="detail_textWrap"
                :style="{ width: '80%', justifyContent: 'center', margin: margin }">
                <div class="detail_text" :style="{ width: '80%', fontSize: fontSize }">{{ element.name }}</div>
                <span class="detail_value" :style="{ width: '10%', textAlign: 'right' }"></span>{{ value[index] }}<span
                    class="detail_text" :style="{ marginLeft: '10px', width: 'initial', fontSize: '14px' }">{{
                        element.unit
                    }}</span>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['title', 'item', 'data', 'data4', 'presValue'],
    data() {
        return {
            firSuji: [],
            secSuji: [],
            thrSuji: [],
            fouSuji: [],
            fivSuji: [],
            value: [],
            plateHeight: '160px',
            backPosiY: '55px',
            margin: '10px',
            fontSize: '16px'
        }
    },
    mounted() {
        if (this.$area === 'buan') {
            this.margin = '5px'
            this.fontSize = '14px'
            this.plateHeight = '200px'
        }
    },
    updated() {
        if (this.item?.length >= 4) {
            this.backPosiY = '100px'
        }
        if (this.title.slice(-2) === '대수') {
            this.setCntValue()
        } else if (this.title.slice(-2) === '관압') {
            this.setPresValue()
        }
    },
    methods: {
        setCntValue() {
            if (this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 1).length > 0) {
                this.firSuji = this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 1);
                let firCnt = 0
                this.firSuji.forEach((element) => {
                    if (element.value == 'On') {
                        firCnt++
                    }
                })
                this.value.push(firCnt)
            }
            if (this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 2).length > 0) {
                this.secSuji = this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 2);
                let secCnt = 0
                this.secSuji.forEach((element) => {
                    if (element.value == 'On') {
                        secCnt++
                    }
                })
                this.value.push(secCnt)
            }
            if (this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 3).length > 0) {
                this.thrSuji = this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 3);
                let thrCnt = 0
                this.thrSuji.forEach((element) => {
                    if (element.value == 'On') {
                        thrCnt++
                    }
                })
                this.value.push(thrCnt)
            }
            if (this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 4).length > 0) {
                this.fouSuji = this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 4);
                let fouCnt = 0
                this.fouSuji.forEach((element) => {
                    if (element.value == 'On') {
                        fouCnt++
                    }
                })
                this.value.push(fouCnt)
            }
            if (this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 5).length > 0) {
                this.fivSuji = this.data?.pumpStatus?.filter(item => item.PUMP_GRP === 5);
                let fivCnt = 0
                this.fivSuji.forEach((element) => {
                    if (element.value == 'On') {
                        fivCnt++
                    }
                })
                this.value.push(fivCnt)
            }
          
        },
        setPresValue() {
            this.presValue?.forEach(element => {
                if (element) {
                    this.value.push(parseFloat(element).toFixed(2))
                }
            })
        }
    }
}
</script>

<style>
.plate_area {
    background: url("@/assets/img/plate_img.png") no-repeat;
    background-size: 100% 20%;
    background-position-y: 160px;
    height: 230px;
}

.detail_text {
    width: 70%;
    text-shadow: 0 0 9px #5cafff;
    color: #c3eaff;
}

.detail_value {
    width: 30%;
    font-family: LAB디지털;
    text-align: right;
}
</style>