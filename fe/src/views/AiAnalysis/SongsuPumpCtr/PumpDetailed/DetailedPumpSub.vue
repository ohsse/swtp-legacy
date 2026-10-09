<template>
    <div class="detail_textWrap" style="margin: 0;">
        <div class="detail_text" style="width: 50%;">{{ setting.title }}</div>
        <span class="detail_value" style="text-align: right; margin: 0px 0px 5px;">{{ value }}</span><span class="detail_text"
            style="margin-left: 10px;width: initial;font-size:14px">{{ setting.unit }}</span>
    </div>
</template>
<script>
import { addCommaNumber } from '@/util/addCommaNumber'
export default {
    props: {
        setting: {
            type: Object
        },
        values: {
            type: Object
        }
    },
    data(){
        return{
            value : 0
        }
    },
    mounted(){

        this.value = addCommaNumber(this.values.value[`${this.values.grp_idx}${this.setting.key}`])
            
    }
}
</script>
<style scoped>
.detail_text {
  /* width: 70%; */
  text-shadow: 0 0 9px #5cafff;
  color: #c3eaff;
}
</style>