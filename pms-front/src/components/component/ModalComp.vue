<template>
    <div class="modal-wrap">
        <div class="modal-contents">
            <div class="modal-container">
                <header class="modal-header">
                    <h5 class="modal-title">{{ this.title }}</h5>
                    <button type="button" aria-label="Close" @click="$emit('closeModal')"
                        class="close fs-3 text-white bg-transparent border-0">×</button>
                </header>
                <AreaChart ref="AreaChart" :style="{ height: '600px', width: '1500px' }" :isModalChart="true" />
            </div>
        </div>
    </div>
</template>

<script>
import AreaChart from '@/components/chart/AreaChart.vue';

export default {
    components: { AreaChart },
    data() {
        return {
            title: '',
        }
    },
    methods: {
        createChart(chartClass, title) {
            this.title = title
            this.$refs.AreaChart.changeData(chartClass)
        },
    }
}
</script>

<style>
.modal-wrap {
    position: absolute;
    z-index: 101;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgba(0, 0, 0, 0.5);
}

.modal-contents {
    background-image: url(@/assets/img/img03.png);
    margin: 10% auto;
    padding: 20px;
    border: 1px solid #888;
    width: 80%;
    max-width: 1800px;
    text-align: center;
}

#close-btn {
    color: #aaa;
    float: right;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
}

#close-btn:hover,
#close-btn:focus {
    color: black;
    text-decoration: none;
    cursor: pointer;
}

#close-btn:hover,
#close-btn:focus {
    color: black;
    text-decoration: none;
    cursor: pointer;
}
</style>
