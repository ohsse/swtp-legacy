<template>
    <b-row>
        <b-col class="div-new p-4" v-bind:style="{ height: '472px' }">
            <b-row>
                <b-col xl="2" class="mb-3">
                    <div class="title_show" v-bind:style="{ height: '20px' }"></div>
                </b-col>
            </b-row>
            <b-row cols="6" class="gy-3">

                <MonthCard v-for="item in list" :key="item.month" :data="item" />


            </b-row>
        </b-col>
    </b-row>
</template>

<script>
import MonthCard from "@/views/EnergySavingMngmn/MonthCard.vue";

export default {
    components: {
        MonthCard
    },
    data() {
        return {
            list: new Array()
        }
    },
    methods: {
        getTopData(data) {
            this.list = data
        }
    }
}
</script>

<style scoped>
.div-new {
    background-image: url(/src/assets/img/div_new.png);
    background-size: 100% 100%;
    display: inline-block;
}

.title_show {
    background-image: url(/src/assets/img/dot_road.png);
    background-size: 100% 35%;
    background-repeat: no-repeat;
    background-position: center;
}
</style>