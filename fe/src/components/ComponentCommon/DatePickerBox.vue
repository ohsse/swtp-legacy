<template>
  
  
      <Datepicker
        v-model="dp2From"
        :ref="inputs.dp2From"
        class="datepicker"
        :locale="locale"
        :weekStartsOn="0"
        :inputFormat="inputFormat"
        @focus="setOldValue($event.target.value)"
        @update:modelValue="validateFromTo('from', 'dp2From', 'dp2To')"
      />


      <Datepicker
        v-model="dp2To"
        :ref="inputs.dp2To"
        class="datepicker"
        :locale="locale"
        :weekStartsOn="0"
        :inputFormat="inputFormat"
        @focus="setOldValue($event.target.value)"
        @update:modelValue="validateFromTo('to', 'dp2From', 'dp2To')"
      />
        

 

</template>

<script>
import { ref, reactive, defineComponent } from 'vue';
// vue3-datepicker
import Datepicker from 'vue3-datepicker';
import { ko } from 'date-fns/locale';


export default defineComponent({
  name: 'App',
  components: {
    Datepicker,
  },
  setup() {
    // :weekStartsOn="0" 'Sunday' is first
    const picked = ref(new Date());
    const locale = reactive(ko);
    const inputFormat = ref('yyyy-MM-dd');

    // dp2
    const now = new Date();
    const dp2 = ref(new Date());
    const dp2From = ref(new Date(now.setDate(now.getDate() - 7)));
    const dp2To = ref(new Date(now.setDate(now.getDate() + 14)));
    // [from, to]'s value before changing value
    let oldVal = '';

    // dp3
    const dp3 = ref(new Date());

    // refs
    // const datepicker1 = ref(null);
    // dynamic refs
    const inputs = [];

    const clickCalIcon = (refId) => {
      const dp = inputs[refId].value;
      // console.log(dp);
      dp.inputRef.focus();
    };
    const getCalValue = (refId) => {
      // console.log(refId);
      // console.log(datepicker1.value.input);
      // ref="datepicker1"

      const dp = inputs[refId].value;
      // console.log(dp);
      alert(dp.input);
    };
    const setOldValue = (val) => {
      // console.log(val);
      oldVal = val;
    };
    const validateFromTo = (target, refFrom, refTo) => {
      setTimeout(() => {
        const dpFrom = inputs[refFrom].value;
        const dpTo = inputs[refTo].value;
        // alert(dpFrom.input + ' ~ ' + dpTo.input);

        if (dpFrom.input > dpTo.input) {
          alert('Validation Error!!');

          let date = null;
          if (oldVal) {
            const arrOldVal = oldVal.split('-');
            date = new Date(
              Number(arrOldVal[0]),
              Number(arrOldVal[1]) - 1,
              Number(arrOldVal[2]),
            );
          }
          // console.log(date);

          if (target === 'from') {
            dp2From.value = date;
          } else if (target === 'to') {
            dp2To.value = date;
          }
          return;
        }
      }, 10);
    };
    const isTodayOver = (date) => {
      return date > new Date();
    };

    return {
      picked,
      locale,
      inputFormat,
      // datepicker1,
      inputs,
      clickCalIcon,
      getCalValue,
      dp2From,
      dp2To,
      dp2,
      setOldValue,
      validateFromTo,
      dp3,
      isTodayOver,
    };
  },
});
</script>

<style scoped>
div {
  text-align: center;
}
div.date {
  display: inline-flex;
}
</style>