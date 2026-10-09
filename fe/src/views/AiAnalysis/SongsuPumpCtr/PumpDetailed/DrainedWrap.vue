<template>
    <template v-if="length == 1">
        <DrainedBox :data="data" :cnt="index" />
    </template>
    <template v-else>
        <div :class="wrapClass">
            <DrainedBox :data="data" :cnt="index" />
        </div>
    </template>
</template>
<script>
import DrainedBox from './DrainedBox.vue';
export default {
    components: {
        DrainedBox
    },
    props: {
        data: {
            type: Object
        },
        index: {
            type: Number
        },
        length: {
            type: Number
        }
    },
    data() {
        return {
            wrapClass: 'pipe_wrap_' + this.length
        }
    }
}
</script>
<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.pipe_wrap_2 {
  height: 50%;
}

.pipe_wrap_1 {
  display: flex;
  width: 100%;
  height: 100%;
}

.pipe_wrap_3 {
  height: calc(100% / 3);
}

</style>