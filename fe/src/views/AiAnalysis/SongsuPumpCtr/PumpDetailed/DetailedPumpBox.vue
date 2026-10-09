<template>
    <div class="fL"
        :style="{ height: '95px', width: '100%', display: 'flex', alignItems: 'center', padding: '15px 20px 10px 20px' }">
        <div class="fL circle-dot"
            :style="{ width: '25%', height: '100%', fontSize: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }">
            {{ boxData.title }}</div>
        <div class="fL"
            style="width: 70%;height: 100%; display: flex;flex-direction: column;justify-content: center; line-height: 20px;">
            <DetailedPumpSub v-for="item in settings" :key="item" :setting="item" :values="boxData.sub" />
        </div>
    </div>
    <b-row :class="pumpClass" :style="pumpStyle">
        <DetailedPump v-for="item in boxData.pumpDatas" :key="item" :pump="item" :pumpHeight ="pumpHeight"/>
    </b-row>
</template>
<script>
import DetailedPump from './DetailedPump.vue';
import DetailedPumpSub from './DetailedPumpSub.vue';
export default {
    components:{
        DetailedPump,
        DetailedPumpSub
    },
    props: {
        pumpWidth:{
            type : Number
        },
        boxData : {
            type : Object
        },
        prdct: {
            type: Boolean
        },
        
    },
    data(){
        let heightKey =0
        if(this.pumpWidth == 1){
            heightKey = 1;
        }   
        return{
            settings :[
                {
                    title : '전력',
                    unit : 'kW',
                    key : '_PWR_PRDCT'
                },
                {
                    title : '관압',
                    unit : 'kg/cm2',
                    key : '_TUBE_PRSR_PRDCT'
                },
                {
                    title : '유량',
                    unit : 'm3',
                    key : '_PRDCT_MEAN'
                }
            ],
            pumpClass : 'row-cols-2',
            pumpStyle : { padding:'0 30px'},
            pumpHeight : heightKey
        }
    },
    mounted(){
        if(this.prdct){
            for(const item of this.settings){
                item.title = `예상 ${item.title}`
            }
        }
      
        if(this.pumpWidth == 1){
            this.pumpClass = 'row-cols-1'
            
        }
        else if(this.boxData.pumpDatas.length > 4){
            this.pumpClass = 'row-cols-3'
        }
    },
}
</script>
<style scoped>

.table-bg {
  background: url(@/assets/img/analysis/table_bg_03.png) no-repeat;
}

.r-circle {
  background: url(@/assets/img/r_circle.png) no-repeat;
  background-position: center;
}

.img_circle {
  background: url(@/assets/img/r_circle.png) no-repeat;
  background-position: center;
}

.circle-dot {
  max-height: 85%;
  border-style: dotted;
  border-color: #546b7d;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 2%;
  white-space: normal;
}

</style>