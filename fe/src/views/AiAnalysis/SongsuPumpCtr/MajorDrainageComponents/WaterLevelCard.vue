<template>
    <div class="col">
        <b-row class="div-small text-center p-3 align-items-center">
            <b-col class="bottom_all1">{{ data.TNK_GRP_NM }}</b-col>
            <b-col class="measure_font align-items-end">{{ data.LEI != null ? data.LEI : 0 }}<spna class="bottom_all2 px-1">
                    m
                </spna>
            </b-col>
        </b-row>
    </div>
</template>
<script>
export default {
    props: [
        'data'
    ],
    mounted() {
    }

}
</script>