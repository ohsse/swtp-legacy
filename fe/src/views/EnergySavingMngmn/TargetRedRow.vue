<template>
    <tr>
        <td class="bottom_col1 align-middle">{{ item.text }}</td>
        <td id="goalPower" class="bottom_middle_val align-middle">{{ item.val }}</td>
        <td class="table_unit align-middle">{{ item.unit }}</td>
    </tr>
</template>
<script>
export default {
    props: {
        item: Object
    }
}
</script>

<style scoped>
.table_unit {
    font-size: 16px;
    color: #a4ceed;
    font-family: 'KHNPHDRegular';
    padding-left: 14px !important;
}

td {
    padding: 7px 0;
}

.bottom_col1 {
    text-shadow: 0 0 9px #5cafff;
    font-size: 19px;
    font-weight: normal;
    font-stretch: normal;
    font-style: normal;
    letter-spacing: normal;
    color: #c3eaff;
    text-align: left;
    font-family: 'KHNPHUotfR';
    display: flex;
    align-items: flex-end;
}

.bottom_middle_val {
    text-shadow: 0 0 9px #5cafff;
    font-size: 19px;
    font-weight: normal;
    font-stretch: normal;
    font-style: normal;
    letter-spacing: normal;
    color: #fff;
    font-family: 'LAB디지털';
    text-align: right;
}
</style>