<template>
    <div class="d-flex justify-content-center align-items-center p-3" >
        <span v-show="!noData">No Data</span>
    </div>
</template>

<script>
import * as echarts from "echarts";
import { shallowRef } from 'vue';

export default {
    data() {
        return {
            myChart: shallowRef(null),
            noData : true,
        };
    },
    methods: {
        changeData(dataAll) {

              // 기존에 추가된 내용이 있다면 제거
            const existingAdditionalContent = this.$el.querySelector('.additional-content');
            if (existingAdditionalContent) {
                existingAdditionalContent.remove();
            }

            if (this.myChart != null && this.myChart != "" && this.myChart != undefined) {
                this.myChart.dispose(); //차트돔이 먼저 생성된 경우 기존 돔을 삭제해준다
            }
            if(dataAll){
                this.noData = true;
                this.myChart = echarts.init(this.$el);
                this.myChart.setOption(dataAll);
                window.onresize = () => {
                    this.myChart.resize();
                };
            }else{
                // this.noData = false
                const additionalContent = document.createElement('div');
                additionalContent.className = 'additional-content';
                additionalContent.innerHTML = '<p>No Data.</p>';
                this.$el.appendChild(additionalContent);
            }
        },
        resizeChart() {
            this.myChart.resize()
        }   
    },
};
</script>

<style></style>
