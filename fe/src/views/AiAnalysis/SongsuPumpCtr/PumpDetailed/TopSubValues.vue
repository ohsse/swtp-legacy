<template>
    <b-col xl="3" class="text-center">
        <b-row class="align-items-center">
            <b-col cols="6" class="detail_text">데이터 수집시간</b-col>
            <b-col style="font-size: 16px;">{{ topData.dataTime }}</b-col>
        </b-row>
    </b-col>
    <b-col xl="3" class="text-center">
        <b-row class="align-items-center">
            <b-col cols="8" class="detail_text">운영대수</b-col>
            <b-col>{{ topData.sequence }}</b-col>
        </b-row>
    </b-col>
    <b-col xl="3" class="text-center">
        <b-row class="align-items-center">
            <b-col cols="8" class="detail_text">운영모드</b-col>
            <b-col>{{ topData.optMode }}</b-col>
        </b-row>
    </b-col>
</template>
<script>
export default {
    props: {
        topData: {
            type: Object
        }
    },
    data() {
        return {
            dataTime: 0,
            sequence: 0,
            optMode: 'test'
        }
    }
}
</script>
