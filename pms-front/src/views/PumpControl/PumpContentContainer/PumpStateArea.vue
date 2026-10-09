<template>
    <div class="state-area" :style="gumiStateArea">
        <div class="alarm-icon" :class="{
            error: this.error,
        }" :style="gumiAlarmIcon">
            <img class="icon" src="@/assets/alarm.svg" />
        </div>
        <p>
            {{
                this.error ? "동작중" : ""
            }}
        </p>
    </div>
</template>
<script>
export default {
    props: ['error', 'area'],
    data() {
        return {
            gumiAlarmIcon: '',
            gumiStateArea: ''
        }
    },
    beforeUpdate() {
        if (this.area === "gumi") {
            this.gumiAlarmIcon = ''
            this.gumiStateArea = 'padding-top:50px'
        }
        else {
            this.gumiAlarmIcon = ''
            this.gumiStateArea = ''
        }
    }
}
</script>
<style lang="">
    
</style>