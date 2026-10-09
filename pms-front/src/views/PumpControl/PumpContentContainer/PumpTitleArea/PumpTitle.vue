<template>
    <div class="value-title" :style="gumiValueTitle">{{ title }}</div>
    <div :class="'value-val type' + index" :style="gumiValueVal">
        {{ item }}
        mm/s
    </div>
</template>
<script>
export default {
    props: ['title', 'item', 'index', 'area'],
    data() {
        return {
            gumiValueTitle: '',
            gumiValueVal: ''
        }
    },
    beforeUpdate() {
        if (this.area === 'gumi') {
            this.gumiValueTitle = 'font-size:18px; padding-top:11px'
            this.gumiValueVal = 'font-size:17px; height:23%; padding-top:11px'
        }
        else {
            this.gumiValueTitle = ''
            this.gumiValueVal = ''
        }
    },


}
</script>
<style lang="">
    
</style>