<template >
    <div class="value-data">
        <div class="value-item">
            <div class="label">{{ label }}</div>
            <div class="value">
                {{ item }}
                {{ unit }}
            </div>
        </div>
    </div>
</template>
<script>
export default {
    props: ['label', 'item', 'unit']
}
</script>
<style lang="">
    
</style>