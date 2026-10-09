<template>
    <q-table
        class="my-sticky-header-table"
        style="height: 858px"
        :rows="datas"
        :columns="columns"
        row-key="index"
        card-class="bg-transparent text-white table-card"
        table-class="text-white"
        table-header-class="text-white table-header"
        :pagination="initialPagination"
    />
</template>

<script>
const columns = [
    {
        name: 'index',
        label: '',
        align: 'center',
        field: 'index',
        style: 'width: 50px',
    },
    {
        name: 'date',
        align: 'center',
        label: '시간',
        field: 'date',
    },
    {
        name: 'name',
        align: 'center',
        label: '설비명',
        field: 'name',
    },
    {
        name: 'info',
        align: 'center',
        label: '설비정보',
        field: 'info',
    },
    {
        name: 'state',
        align: 'center',
        label: '상태',
        field: 'state',
    },
];

// const seed = [
//     {
//         date: '2021-06-15 15:00',
//         name: 'PAC 튜브펌프 #1',
//         info: '##',
//         state: '전압이상',
//     },
//     {
//         date: '2021-06-15 15:00',
//         name: 'PAC 튜브펌프 #1',
//         info: '##',
//         state: '전압이상',
//     },
//     {
//         date: '2021-06-15 15:00',
//         name: 'PAC 튜브펌프 #1',
//         info: '##',
//         state: '전압이상',
//     },
//     {
//         date: '2021-06-15 15:00',
//         name: 'PAC 튜브펌프 #1',
//         info: '##',
//         state: '전압이상',
//     },
//     {
//         date: '2021-06-15 15:00',
//         name: 'PAC 튜브펌프 #1',
//         info: '##',
//         state: '전압이상',
//     },
//     {
//         date: '2021-06-15 15:00',
//         name: 'PAC 튜브펌프 #1',
//         info: '##',
//         state: '전압이상',
//     },
//     {
//         date: '2021-06-15 15:00',
//         name: 'PAC 튜브펌프 #1',
//         info: '##',
//         state: '전압이상',
//     },
// ];
import { computed } from 'vue';

export default {
    setup(props) {
        const datas = computed(() => {
            let rows = [];
            // for (let i = 0; i < `${props.cnt}`; i++) {
            for (let i = 0; i < 30; i++) {
                let obj = {};
                obj.index = i + 1;
                obj.date = '2021-06-15 15:00';
                // obj.name = `${props.name}` + ' #' + obj.index;
                obj.name = '설비명' + ' #' + obj.index;
                obj.info = '-';
                obj.state = '전압이상';
                rows.push(obj);
            }
            return rows;
        });
        console.log(`${props.cnt}`);
        // rows = rows.concat(seed);
        // rows.forEach((row, index) => {
        //     row.index = index + 1;
        // });

        return {
            initialPagination: {
                sortBy: 'desc',
                descending: false,
                page: 1,
                rowsPerPage: 30,
                // rowsNumber: xx if getting data from a server
            },
            columns,
            datas,
        };
    },
    props: ['name', 'cnt'],
};
</script>
<style lang="scss">
.q-table th {
    border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important;
}
.table-row {
    background: rgba(255, 255, 255, 0) !important;
}
.table-row-2 {
    background: rgba(255, 255, 255, 0) !important;
}
.table-back {
    background: transparent !important;
    color: #fff !important;
}
.q-table th,
.q-table tr {
    background: transparent !important;
}
.q-table th {
    font-size: 14px;
    background: rgb(7, 25, 82) !important;
    color: #fff;
    border-top: 1px solid rgba(99, 134, 185, 0.575);
    font-weight: 400;
}

.q-table td,
.q-table th {
    padding: 15px 0 !important;
}

.q-table--enable-row-hover .q-table__body tr:hover > td {
    background-color: #212e3e !important;
}

tbody .cell {
    color: #fff;
}

.home {
    .q-table__card {
        border-radius: 0;
    }
    .q-field__native,
    .q-field__prefix,
    .q-field__suffix,
    .q-field__input {
        color: rgba(255, 255, 255, 1);
    }
    .q-field__marginal {
        color: rgba(255, 255, 255, 0.54);
    }
    .q-btn {
        color: #fff !important;
    }
    .q-table th {
        background: #26449c !important;
    }
}

.my-sticky-header-table {
    /* height or max-height is important */
    height: 310px;
    /* this is when the loading indicator appears */
}
.my-sticky-header-table .q-table__top {
    /* bg color is important for th; just specify one */
    background-color: #c1f4cd;
}
.my-sticky-header-table thead tr th {
    position: sticky;
    z-index: 1;
}
.my-sticky-header-table thead tr:first-child th {
    top: 0;
}
.my-sticky-header-table.q-table--loading thead tr:last-child th {
    /* height of all previous header rows */
    top: 48px;
}

.scroll::-webkit-scrollbar {
    width: 6px;
    // background: #fff;
    background: transparent;
    opacity: 0 !important;
}

.scroll::-webkit-scrollbar-thumb {
    // background: #fff;
    border-radius: 6px;
    background: RGBA(255, 255, 255, 0.15);
}

.scroll:hover::-webkit-scrollbar-thumb {
    // background: #bbb;
    background: RGBA(255, 255, 255, 0.3);
}

.scroll::-webkit-scrollbar-thumb:hover {
    background: RGBA(255, 255, 255, 0.3);
    // background: #aaa;
}
</style>
