<template>
    <div :class="className" :style="displayStyle">
        <div class="dash_border_img2 div_small">
            <div class="bottom_fac_title">
                <span class="bottom_fac_lsit_cont2 fL"><span>{{ hoverVal.title }} 주요 설비</span> TOP 3</span>
                <span class="bottom_fac_lsit_cont2 fR"><span class="elec_use_unit_font" style=" font-size: 15px;">전력 :
                    </span>
                    <span style="font-family: LABDigital; font-size: 19px; ">{{ mainValue }}</span><span
                        class="elec_use_unit_font"> kW</span>
                </span>
            </div>
            <div class="chart_div" v-if="this.values[0]">
                <HoverGraph :title="item.title" :graphVal="item.value" :graphSize="item.size"
                    v-for="item in this.values" :key="item" />
            </div>
            <div class="chart_div" v-if="!this.values[0]">
                <span style="font-size: 19px; padding-top: 70px;">No Data</span>
            </div>
        </div>
    </div>
</template>

<script>
import { addCommaNumber } from '@/util/addCommaNumber'
import HoverGraph from './MainSmallComponents/HoverGraph.vue'
export default {
    props: [
        'hoverVal'
    ],
    components: { HoverGraph },
    data() {
        // const values =[];
        // this.hoverVal.values.forEach(item => {
        //     const size = (item.value/this.hoverVal.mainValue)*100
        //     values.push({value:item.value, title:item.title, size:size})
        // });
        return {
            values: [],
            displayStyle: {
                display: 'none'
            },
            className: 'hoverInfo',
            mainValue: 0
        }
    },
    methods: {
        setData(values) {
            this.values = []
            values.forEach(item => {
                let size = (item.value / this.hoverVal.mainValue) * 100
                size = isNaN(size) ? 0 : size
                this.values.push({ value: addCommaNumber(item.value), title: item.title, size: size })
            })
            this.mainValue = addCommaNumber(this.hoverVal.total)
        },
        show() {
            this.displayStyle.display = 'block';
            this.className = 'hoverInfo'
        },
        hide() {
            this.className = 'hoverInfo hoverInfoNone'
            // this.displayStyle.display = 'none';
        }
    }
}
</script>

<style>
.bottom_fac_lsit_cont2 {
    font-size: 16px;
    font-family: 'KHNPHDRegular';
    color: #24ABE2;
    line-height: 43px;
    font-weight: bold;
}

.bottom_fac_title {
    width: 89%;
    height: 16%;
    margin-top: 16px;
    display: flex;
    align-content: flex-start;
    justify-content: space-around;
    align-items: center;
}

.main_info_up {
    -webkit-animation: up 0.5s linear;
    -moz-animation: up 0.5s linear;
    animation: up 0.5s linear;
}

.main_info_down {
    -webkit-animation: down 0.5s forwards;
    -moz-animation: down 0.5s forwards;
    animation: down 0.5s forwards;
}

.div_small {
    height: 100%;
    display: flex;
    align-items: center;
    text-align: center;
    flex-direction: column;
}

.dash_border_img2 {
    background: url(@/assets/img/01_table_bg.png) no-repeat;
    background-position: center;
    background-size: 100% 100%;
}

@keyframes move-up-building {
    from {
        transform: translateY(380px);
    }

    to {
        transform: translateY(0px);
    }
}

@keyframes move-down-popup {
    from {
        transform: translateY(0px);
    }

    to {
        transform: translateY(380px);
        opacity: 0;
        /* 투명하게 만들어 사라지게 함 */
    }
}
</style>