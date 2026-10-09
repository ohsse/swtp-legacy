<template>
    <div class="row row-cols-5 row-cols-lg-5 g-1 gy-xxl-3 ps-xxl-4 justify-content-center"
        style="overflow-y: scroll; height: 470px; margin-top: 1px;">
        <WaterLevelCardVue v-for="item in cardData" :key="item" :data="item" />
    </div>
</template>
<script>
import WaterLevelCardVue from './WaterLevelCard.vue'
export default {
    components: {
        WaterLevelCardVue
    },
    data() {
        return {
            cardData: [

            ]
        }
    },
    methods: {
        setData(datas) {
            this.cardData = datas
        }
    }
}
</script>
<style></style>