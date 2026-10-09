<template>
  <span class="div_title">
    <span class="text_label">
      {{ title }}
    </span>
    <div v-if="date" class="dateCss text-center">
      <span class="text_timer text_timer-num">{{ date }}</span>
    </div>
  </span>

</template>

<script>
export default {
  props: ['title', 'date'],

}
</script>

<style>
.text_label {
  position: absolute;
}
</style>