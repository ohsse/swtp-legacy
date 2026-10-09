<template>
     <div class="table">
      <div class="thead">
          <div class="num"></div>
          <div class="time">시간</div>
          <div class="list">설비명</div>
          <div class="info">설비정보</div>
          <div class="status">상태</div>
      </div>
      <div class="tbody">
        <tr v-for="(tr, index) in rows" :key="index">
          <td class="num">{{tr.num}}</td>
          <td class="time">{{tr.time}}</td>
          <td class="list">{{tr.list}}</td>
          <td class="info">{{tr.info}}</td>
          <td class="status">{{tr.status}}</td>
        </tr>
      </div>
    </div>
 

</template>

<script>
import { ref } from 'vue'

export default {
   components: {
    },
    props:['title', 'tableRow'],
  setup (props) {

    const name = ref(props.title)
    
    const rows = ref(props.tableRow)

    console.log(props.thead);
    return {
      rows,
      name,
    }
  }
}
</script>