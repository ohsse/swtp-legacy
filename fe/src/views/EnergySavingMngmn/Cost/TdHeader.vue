<template>
    <tr>
        <td class="cal-title-font">{{ setting.text }}</td>
        <td class="text-right contents_value_font" colspan="2"
            v-bind:style="{ fontFamily: 'KHNPHDRegular !important', fontSize: '23px' }">{{ value[setting.key] }}</td>
    </tr>
</template>
<script>
export default {
    props: {
        setting: {
            type: Object,
            required: true
        },
        value: {
            type: Object,
            required: true
        }
    },
}
</script>
<style scoped></style>