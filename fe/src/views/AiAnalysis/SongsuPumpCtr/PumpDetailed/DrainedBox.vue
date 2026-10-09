<template>
    
    <b-row class="mx-0" style="width: 98%; height: 100%;">
        <b-col class="mx-2 py-1" style="height: 95%;">
            <b-row v-if="data.유입유량1" :class="valueClass+' mb-1'" :style="valueStyle">
                {{ value['유입유량1'] }}
            </b-row>
            <b-row v-else class="mb-1" style="height: 45%;"/>
            <b-row v-if="data.유입유량2" :class="valueClass" :style="valueStyle">
                {{ value['유입유량2'] }}
            </b-row>
        </b-col>
        <b-col class="mx-2 py-1" style="height: 95%; width: 100%;">
            <b-row v-if="data['유입밸브 열림1']" style="height: 45%;" class="valve_on mb-1 mx-0"></b-row>
            <b-row v-else-if="data['유입밸브 닫힘1']" style="height: 45%;" class="valve_off mb-1 mx-0"></b-row>
            <b-row v-else class="mb-1" style="height: 45%;"/>
            <b-row v-if="data['유입밸브 열림2']" style="height: 45%;" class="valve_on mx-0"></b-row>
            <b-row v-else-if="data['유입밸브 닫힘2']" style="height: 45%;" class="valve_off mx-0"></b-row>
            <b-row v-else class="mb-1" style="height: 45%;"/>
        </b-col>
        <b-col class="mx-2 py-1" style="height: 95%;">
            <b-row v-if="data['유입밸브 개도율1']" :class="valueClass+' mb-1'" :style="valueStyle">
                {{ value['유입밸브 개도율1']+'%' }}
            </b-row>
            <b-row v-else class="mb-1" style="height: 45%;"/>
            <b-row v-if="data['유입밸브 개도율2']" :class="valueClass" :style="valueStyle">
                {{ value['유입밸브 개도율2']+'%' }}
            </b-row>
        </b-col>
        <b-col class="pipe_center"/>
        <b-col class="mx-2 py-1" style="height: 75%;">
            <b-row v-if="data.수위1" :class="valueClass+' mb-1'" :style="valueStyle">
                {{ value.수위1 }}
            </b-row>
            <b-row v-else class="mb-1" style="height: 45%;"/>
            <b-row v-if="data.수위2" :class="valueClass" :style="valueStyle">
                {{ value.수위2 }}
            </b-row>
        </b-col>
        <b-col class="mx-2 py-1" style="height: 75%;">
            <b-row v-if="data['유출유량1']" :class="valueClass+' mb-1'" :style="valueStyle">
                {{ value['유출유량1'] }}
            </b-row>
            <b-row v-else class="mb-1" style="height: 45%;"/>
            <b-row  v-if="data['유출유량2']" :class="valueClass" :style="valueStyle">
                {{ value['유출유량2'] }}
            </b-row>
            
        </b-col>
    </b-row>
</template>
<script>
import { addCommaNumber } from '@/util/addCommaNumber';

export default {
    props:{
        data : {
            type : Object
        },
        cnt : {
            type : Number
        }
    },
    data(){
        return{
            value : {},
            valueClass : 'd-flex justify-content-center align-items-center',
            valueStyle : {
                'height' : '45%',
                'border': '1px solid #489cf2',
                'background-color': '#15284e',
                'color': '#fff',
                'text-align': 'center',
                'font-family': 'LABDigital',
                'font-size' :'0.95em'
            },
            titleStyle:{
                'font-family': 'KHNPHDRegular',
                'font-size' :'0.8em',
                'text-shadow': '0 0 9px #5cafff',
                color: '#c3eaff'
            }
        }
    },
    mounted(){
        const keys = Object.keys(this.data)
        for(const key of keys){
            if(this.data[key]){
                this.value[key] = addCommaNumber(Number(this.data[key]))
            }
        }
    }
}
</script>
<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.pipe_center{
    display: flex;
    justify-content: center; /* 수평 중앙 정렬 */
    align-items: center; /* 수직 중앙 정렬 */
    background: url(@/assets/img/ai_song/tank.png) no-repeat;
	width: 100%;
    background-size: 100% 100%;
    height: 90%;
}


/* 벨브 색상 */
.valve_off{
	
    background: url(@/assets/img/ai_song/valve.png) no-repeat;
    opacity: 0.4;
    display: flex;
    justify-content: center; /* 수평 중앙 정렬 */
    align-items: center; /* 수직 중앙 정렬 */
    width: 100%;
    background-size: 100% 100%;
    height: 90%;
}
.valve_on{
    background: url(@/assets/img/ai_song/valve.png) no-repeat;
    display: flex;
    justify-content: center; /* 수평 중앙 정렬 */
    align-items: center; /* 수직 중앙 정렬 */
    width: 100%;
    background-size: 100% 100%;
    height: 90%;
}
</style>