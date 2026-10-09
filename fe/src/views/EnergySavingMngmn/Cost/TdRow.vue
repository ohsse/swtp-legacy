<template>
    <tr>
        <td class="cal-title-font align-middle" :style="{ fontSize: fontSize }" v-html="setting.text"></td>
        <td class="contents_value_font align-middle">{{ value[setting?.key] }}</td>
        <td class="contents_value_unit align-middle" v-bind:style="'text-align:letf'">{{ setting.unit }}</td>
    </tr>
</template>
<script>
export default {
    data() {
        return {
            fontSize: '1.1em'
        }
    },
    props: {
        setting: {
            type: Object,
            required: true
        },
        value: {
            type: Object,
            required: true
        },
        usage: {
            type: Boolean,
        },
    },
    mounted() {
        if (this.usage == true) {
            this.fontSize = '0.9em'
        }
    }
}
</script>
<style scoped></style>