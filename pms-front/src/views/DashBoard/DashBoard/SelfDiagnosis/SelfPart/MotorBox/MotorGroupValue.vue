<template>
    <div class="val-icon"></div>
    <div class="val-line"></div>
    <div class="val-1">{{ this.item.rms }}rms </div>
    <div class="val-2">{{ this.item.c }}°C </div>
</template>
<script>
export default {
    props: ['item'],
}
</script>
<style lang="">
    
</style>