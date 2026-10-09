<template>
    <ul class="btn-list d-flex justify-content-between align-items-center rounded">
        <li><button class="btn btn-default"
            :style="{ cursor: 'none', color: '#fff', background: '#5e808f' }">#{{props.btns.PUMP_IDX}}</button></li>
        <li v-for="(item, index) in channel_nm" :key="index"><button @click="clickBtn(item)" 
            :class='btnClass+
            (store.state.precision.choiceMoter == props.btns.MOTOR_ID
            &&channel_nm.findIndex((item)=>item==store.state.precision.choiceChannel)==index?" active":"")'
            >{{item}}</button></li>
    </ul>
</template>
<script>
import { watch } from 'vue';
import { useStore } from 'vuex';
export default {
    props:["btns"],
    setup(props) {
        const store = useStore()
        const channel_nm = props.btns.CHANNEL_NM.split(',');
        const channel_id = props.btns.CHANNEL_ID.split(',');
        let btnClass="btn btn-default"
        watch(()=>[store.state.precision.choiceChannel, store.state.precision.choiceMoter], ()=>{
            btnClass = (store.state.precision.choiceMoter == props.btns.MOTOR_ID &&
            store.state.precision.choiceChannel == channel_nm.find((item)=>item==store.state.precision.choiceChannel))?"btn btn-default active":"btn btn-default"
        })
        const clickBtn = (id)=>{
            store.dispatch("precision/choiceMoter", {motor:props.btns.MOTOR_ID, channel:id})
        }
        return {props, channel_id, channel_nm, clickBtn, store, btnClass}
    }
}
</script>
<style>
    
</style>