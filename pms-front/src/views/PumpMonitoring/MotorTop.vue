<!-- 부모 컴포넌트 -->
<template>
  <div class="topContent">
    <div class="back-btn" @click="back">
      <span> ← Back</span>
    </div>
    <div class="right-content location">
      <CalendarBox ref="calendarBox" />
      <button class="button" @click="downloadExcel">저장</button>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useStore } from "vuex";
import CalendarBox from '@/components/component/CalendarBox.vue';
import axios from 'axios';

export default {
  components: { CalendarBox },

  setup() {
    const router = useRouter();
    const store = useStore();
    const calendarBox = ref(null); // CalendarBox에 대한 ref 추가

    const formatToYYYYMMDD = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const downloadExcel = async () => {
        const from = calendarBox.value.from;
        const to = calendarBox.value.to;
        const formattedFrom = formatToYYYYMMDD(from);
        const formattedTo = formatToYYYYMMDD(to);
        
        const baseUrl = store.state.globalIP + "/api/v1/reportControl/motorReport";
        const response = await axios.get(`${baseUrl}/${formattedFrom}/${formattedTo}`, {
            responseType: 'blob'
        });

        const blob = new Blob([response.data], {
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.setAttribute('download', `motor_report_${formattedFrom}_${formattedTo}.xlsx`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    };

    const back = () => {
        router.push("/PumpControl");
        store.state.monitor1.searchDate = false;
    };

    return {
        calendarBox,
        downloadExcel,
        back
    };
  }
}
</script>
