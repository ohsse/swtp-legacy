<template>
    <img src="@/assets/light.png" alt="" class="light-circle" />
    <img src="@/assets/light2.png" alt="" class="light-line" />
    <div class="content-header">
        <img src="@/assets/titleicon.svg" alt="" class="titleCon" />
        <p>{{ title }}</p>
    </div>
</template>
<script>
export default {
    props: ['title']
}
</script>
<style lang="">
    
</style>