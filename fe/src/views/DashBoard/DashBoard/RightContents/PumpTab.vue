<template>
    <div v-for="(item, index) in this.suji" :key="item" :items="item" class="col">
        <div :class="{ 'dash_pump_tab pump_number': true, 'selected_tab': activeTab === index + 1 }" @click="click(index)"
            :style="{ 'background-color': item.value === 'Off' ? 'rgb(139 194 240 / 57%)' : 'rgb(139 194 240 / 0%)' }">
            {{ index + 1 }}
        </div>
    </div>
</template>
<script>
export default {
    props: ['suji', 'tabIndex', 'name', 'length'],
    data() {
        return {
            activeTab: this.tabIndex,
        }
    },
    updated() {
    },
    mounted() {
    },
    methods: {
        changeActiveTab(index) {
            this.activeTab = index
        },
        click(index) {
            this.$emit('clickTab', this.length + index);
        }
    },
    emits: ['clickTab']
}

</script>
<style>
.right_pump_title {
    color: #c2cad1;
    font-family: 'KHNPHDRegular';
    font-size: 12px;
    text-shadow: 0 0 10px #000;
    /* text-indent: 3%; */
    text-align: center;
    padding: 0 7px;
    /* width: 47px; */
    line-height: 31px;
}

.pump_number {
    font-family: 'LABDigital !important';
    font-size: 16px;
    color: #fff;
    text-align: center;
    line-height: 23px;
}

.dash_pump_tab {
    padding: 2px;
    border: solid 1px #b4dffa;
    background-color: rgb(139 194 240 / 57%);
    cursor: pointer;
}

.selected_tab {
    color: #F8C314 !important;
    border: solid 1px #F8C314 !important;
    font-weight: bold;
}
</style>