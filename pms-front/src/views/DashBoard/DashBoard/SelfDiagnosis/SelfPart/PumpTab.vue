<template>
    <div class="itemList list1">
        <div class="list-title">
            <span>{{ item.name }}</span>
            <img src="@/assets/img/small_list_title_bg.png" alt="리스트 배경 이미지" />
        </div>
        <div class="item-box">
            <div v-for="(element, index) in data" :key="index" :class="{
                 'item': true, 'selected': selectedItem === index, 'alarm': element?.alarm 
               // 'item': true, 'selected': selectedItem === index, 
            }" @click="selectItem(index)" @mouseenter="killTimer()" @mouseleave="timeRotation()">
                {{ Number(element.scada_id.slice(-2)) }}
            </div>
        </div>
    </div>
</template>

<script>
import { useStore } from 'vuex';
export default {
    props: ['item', 'count', 'id', 'data'],
    data() {
        return {
            pumpId: null,
            rotationId: 0,
            rotationIndex: 0,
            selectedItem: null,
            timer: null,
            store: useStore(),
        };
    },
    mounted() {
        this.pumpId = this.id
        this.timeRotation()
    },
    methods: {
        changeSelectedItem(index) {
            this.selectedItem = index
        },
        selectItem(index = 0) {
            if (this.pumpId === 0) {
                this.$emit('clickFirSuji', index)
            }
            else if (this.pumpId === 1) {
                this.$emit('clickSecSuji', index)
            }
        },
        killTimer() {
            clearTimeout(this.timer);
        },
        timeRotation() {
            const area = this.$store.state.area
            if (this.id === 0) {
                this.killTimer()
                if (this.rotationId === 0) {
                    this.timer = setTimeout(() => {
                        this.rotationIndex++;
                        this.$emit('clickFirSuji', this.rotationIndex)
                        if (area == 'gosan') {
                            if (this.rotationIndex === 6) { // 탭 개수 - 1
                                this.rotationIndex = -1;
                                this.rotationId = 1;
                            }
                        } else if (area == 'gumi') {
                            if (this.rotationIndex === 3) { // 탭 개수 - 1
                                this.rotationIndex = -1;
                                this.rotationId = 0;
                            }
                        } else if (area == 'hakya') {
                            if (this.rotationIndex === 5) { // 탭 개수 - 1
                                this.rotationIndex = -1;
                                this.rotationId = 0;
                            }
                        }
                        this.timeRotation();
                    }, 5000);
                }
                else if (this.rotationId === 1) {
                    this.timer = setTimeout(() => {
                        this.rotationIndex++;
                        this.$emit('clickSecSuji', this.rotationIndex)
                        if (this.rotationIndex === 3) { // 탭 개수 - 1
                            this.rotationIndex = -1;
                            this.rotationId = 0;
                        }
                        this.timeRotation();
                    }, 5000);
                }
            }
        },

    },
    emits: ['clickFirSuji', 'clickSecSuji']
};
</script>
<style>
.alarm {
    background: #ff5c5c66;
    border: solid 1px #ff5c5c;
}
</style>  