<template>
    <b-row class="table_image">
        <b-col xl="2">전체</b-col>
        <b-col xl="6" class="bottom_all2">사용량 <span class="bottom_all2_value"></span>{{ use }} kWh</b-col>
        <b-col xl="4" class="bottom_all2 text-align-right">비용 <span class="bottom_all2_value"></span>{{ cost }} 원</b-col>
    </b-row>
</template>

<script>

export default {
    props: ["cost", "use", "useUnit", "costUnit"],
}
</script>

<style>
.table_image {
    height: 62px;
    background-image: url(/src/assets/img/div_new.png);
    background-size: 100% 100%;
    text-align: center;
    margin-bottom: 4px;
    align-items: center;
}
</style>