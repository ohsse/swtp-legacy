<template>
    <div class="content-panel">
        <PumpContentTitle :title="title" />
        <div class="content-container">
            <PumpValueData :label="'운영대수'" :item="data.running" :unit="'대'" />
            <PumpValueData :label="'유량'" :item="data.flow_rate_val" :unit="'㎥/min'" />
            <PumpValueData :label="'압력'" :item="data.pressure_val" :unit="'kgf/㎥'" />
            <PumpScatterArea :item="data" :scatterData="scatterData" />
        </div>
    </div>
</template>
<script>
import PumpContentTitle from "@/views/PumpControl/PumpManageStatus/PumpContentTitle.vue";
import PumpValueData from "@/views/PumpControl/PumpManageStatus//PumpValueData.vue";
import PumpScatterArea from "@/views/PumpControl/PumpManageStatus//PumpScatterArea.vue";
export default {
    components: {
        PumpContentTitle,
        PumpValueData,
        PumpScatterArea,
    },
    props: ['data', 'title', 'type', 'scatterData']
}
</script>
<style lang="">
    
</style>