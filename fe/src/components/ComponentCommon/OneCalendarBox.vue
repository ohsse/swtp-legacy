<template>
    <b-row class="d-flex justify-content-end">
        <div class="d-flex justify-content-end mb-3">
            <Vue3Datepicker
                :style="{ 'height': '30px', color: '#ffffff', backgroundColor: '#15284e', 'background-image': 'url(' + require('@/assets/img/select_cal.png') + ')', 'background-repeat': 'no-repeat', 'background-position': 'right', outline: 'none', 'border-width': '1px', 'borderColor': '#489cf2', borderRadius: '4px', 'padding-left': '10px', 'margin': '0 10px' }"
                input-class="input-class"
                :inputFormat="dateFormat.format" :locale="dateFormat.locale" v-model="selectedDate" />
                <span class="buttonArea" style="float:right"><span class="button"  @click="getCalValue()">조회</span></span>
        </div>
    </b-row>
</template>
<script>
import { ref } from 'vue';
import Vue3Datepicker from 'vue3-datepicker';
import { ko } from 'date-fns/locale';
import 'vue3-datepicker/dist/vue3-datepicker.css';
export default {

    components: {
        Vue3Datepicker
    },
    setup(props, { emit }) {
        const selectedDate = ref(new Date());
        const dateFormat = ref({
            locale: ko,
            format: 'yyyy-MM-dd',
        })
        const getCalValue = () => {
            setTimeout(() => {

                const getDate = selectedDate.value;
                const getYear = getDate.getFullYear()
                const getMonth = (getDate.getMonth() + 1) < 10 ? '0' + (getDate.getMonth() + 1) : (getDate.getMonth() + 1)
                const getDay = (getDate.getDate()) < 10 ? '0' + (getDate.getDate()) : (getDate.getDate())
                const returnDate = getYear+'-'+getMonth+'-'+getDay;
                emit("setDate", returnDate)

            }, 10)
        }

        return {
            selectedDate,
            getCalValue,
            dateFormat
        };
    },
    mounted(){
        this.getCalValue()
    }
}
</script>