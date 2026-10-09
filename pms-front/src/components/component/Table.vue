<template>
     <div class="table">
      <div class="thead">
        <div class="num"></div>
        <div class="status">상태</div>
        <div class="list">설비명</div>
      </div>
      <div class="tbody">
        <tr v-for="(tr, index) in rows" :key="index">
          <td class="num">{{tr.name}}</td>
          <td class="status">
            <div class="circle" :class="{err:!tr.status}"></div>
          </td>
          <td class="list">{{tr.list}}</td>
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

    return {
      rows,
      name,
    }
  }
}
</script>