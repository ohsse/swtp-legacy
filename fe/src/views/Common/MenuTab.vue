<template>
    <button v-for="(item, index) in pumpList" :key="index" @click="changeTab(index)"
        :class="{ 'custom-button': true, 'active-tab': selectedIndex === index }">
        {{ onlyName ? item.PUMP_GRP_NM.replace(/[^가-힣]/g, "") : item.PUMP_GRP_NM }}
    </button>
</template>

<script>
import { fetchFunc } from '@/util/fetchFunc';

export default {
    props: ['onlyName'],
    data() {
        return {
            pumpList: [],
            selectedIndex: 0, // 초기 선택 인덱스를 0으로 설정
        };
    },
    mounted() {
        this.getData();
    },
    methods: {
        async getData() {
            if (this.onlyName) this.pumpList = (await fetchFunc(`${this.$apiURL}/ai/selectDrvnPumpMaster`)).data;
            else this.pumpList = (await fetchFunc(`${this.$apiURL}/ai/selectPumpMaster`)).data;
        },
        changeTab(index) {
            this.selectedIndex = index;
            this.$emit('changeData', index);
        },
        changeIndex(index) {
            this.selectedIndex = index;
        }
    },
};
</script>

<style scoped>
.custom-button {
    width: 120px;
    height: 40px;
    align-self: center;
    border: solid 1px #b4dffa;
    background-color: rgb(47, 65, 97, .5);
    border: 1px solid rgb(168, 210, 236, .5);
    color: white;
    cursor: pointer;
    border-radius: 4px;
    margin-left: 20px;
    text-shadow: 0 0 9px #5cafff;
    font-family: 'KHNPHDBold';
    font-weight: normal;
}

.active-tab {
    background-color: rgb(67, 91, 121);
    border: 1px solid rgb(168, 210, 236, 1);
    /* 원하는 색상으로 변경하세요 */
}
</style>
