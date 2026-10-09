<template>
    <div>
        <div class="water-icon2" :class="{
            none: !this.none,
        }"></div>
        <div class="water-icon2 delay2" :class="{
            none: !this.none,
        }"></div>
    </div>
</template>
<script>
export default {
    props: ['none'],
    mounted() {
    }
}
</script>
<style lang="">
    
</style>