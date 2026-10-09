<template>
    <b-col class="left_bg"
        style="height: 900px; margin-top: 10px; padding:10px 10px 10px 20px; overflow-y: scroll; height: 800px;">
        <b-list-group class="fontContent list-custom-group list-group">
            <b-list-group-item :class="{ active: activeIndex === index }" @click="toggleActive(item, index)"
                v-for="(item, index) in listData" :key="index">{{ item }}</b-list-group-item>
        </b-list-group>
    </b-col>
</template>
<script>
export default {
    data() {
        return {
            activeIndex: -1,
            listData: [

            ]
        }
    },
    mounted() {


    },
    methods: {
        setList(datas) {
            this.listData = []
            let listData = []
            datas.forEach((item) => {
                if (!listData.includes(item.TNK_GRP_NM)) {
                    listData.push(item.TNK_GRP_NM)
                }
            })
            this.listData = listData
            this.toggleActive(this.listData[0], 0)
        },
        toggleActive(item, index) {
            if (this.activeIndex !== index) {
                this.activeIndex = index; // 다른 항목 클릭 시만 활성화
                this.getItem(item)

            }
        },
        getItem(item) {

            this.$emit('selectItem', item)
        }
    }
}
</script>
<style scoped></style>