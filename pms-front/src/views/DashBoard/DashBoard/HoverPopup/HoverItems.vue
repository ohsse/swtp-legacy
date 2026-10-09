<template >
    <div class="items" >
        <div class="title2">{{ this.grpList[0]?.grp_nm + title.name }}</div>
        <div class="item-list">
            <HoverItemBox  :index="grpList" :alarmHoverGrpList="alarmHoverGrpList" />
        </div>
    </div>
</template>
<script>
import HoverItemBox from '@/views/DashBoard/DashBoard/HoverPopup/HoverItems/HoverItemBox.vue'
import { useStore } from 'vuex';
export default {
    components: {
        HoverItemBox,
    },
    props: ['grpList','alarmHoverGrpList'],
    data() {
        return {
            title: { name: '' },
        }
    },
    mounted() {
        this.titleChange();
    },
    methods: {
        titleChange() {
            const store = useStore();
            const area = store.state.area;
            // console.log("area", area);
            if (area == 'gosan') {
                this.title.name = ' 송수펌프모터'
            } else if (area == 'gumi') {
                this.title.name = ' 송수펌프모터'
            } else if (area == 'hakya') {
                this.title.name = ' 가압펌프'
            }
        }
    },

}
</script>
<style lang="">
    
</style>