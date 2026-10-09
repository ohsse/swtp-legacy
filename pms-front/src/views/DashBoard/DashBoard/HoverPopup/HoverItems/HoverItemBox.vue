<template>
    <div class="item-box" v-for="(item, i) in index" :key="i">
        <div :class="alarmHoverGrpList[i]?.Alarm ? 'error' : 'item'"></div>
        <div v-if="index[i].grp_nm == '신평생활'" class="item-title" >{{ index[i].pump_idx +'번' }}</div>
        <div v-if="index[i].grp_nm == '임하가압장'" class="item-title" >{{ index[i].pump_idx +'번' }}</div>
        <div v-if="index[i].grp_nm.substr(-5) == '송수펌프동'" class="item-title">{{ getPumpNumberFromGroup(index[i].pump_nm) }}</div>
    </div>
</template>
<script>
export default {
    props: ['index','alarmHoverGrpList'],
    data() {
        return {
        }
    },
    methods: {
        getPumpNumberFromGroup(groupName) {
            // 그룹명에서 숫자만 추출하여 반환합니다.
            const name = groupName.split(" ")
            return name[1];
        }
    },
}
</script>
<style >
</style>
