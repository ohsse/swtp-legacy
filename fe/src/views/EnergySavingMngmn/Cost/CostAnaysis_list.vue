<template>
    <b-col xl="12">
        <div class="center_bottom_box" v-bind:style="{ height: '260px' }">
            <div class="cost-box">
                <div id="seasonTitleArea" class="bottom_box_row">
                    <div class="center_bottom_circle float-start"></div>
                    <div id="seasonBtn0" style="display: block;" class="cal_season_btn cal_season_btn_font float-end"
                        v-text="season">
                    </div>
                </div>

                <div id="infoA" style="overflow: auto; " class="bottom-box-row bottom-box-border seasonFont scrollbar ">
                    <row v-for="(item, index) in row" :key="index" :row="item"></row>
                </div>
            </div>
        </div>
    </b-col>
</template>
<script>
import row from "@/views/EnergySavingMngmn/Cost/ListRow.vue"
export default {
    components: {
        row,
    },
    data() {
        return {
            season: null,
            row: []
        }
    },
    methods: {
        setSeason(season) {
            this.season = season
        },
        setRow(data) {
            this.row = []
            this.row = data
        }
    }
}
</script>
<style scoped>
.cal_season_btn{
    cursor: default;
}
.center_bottom_box {
    background-image: url(/src/assets/img/box_bg_middle.png);
    background-repeat: no-repeat;
    background-size: 100% 100%;
}

.bottom_box_row {
    align-items: center;
    height: 27%;
    padding: 1%;
}

.center_bottom_circle {
    background-image: url(/src/assets/img/cost_circle.png);
    background-repeat: no-repeat;
    background-size: contain;
    width: 24%;
    height: 100%;
    margin-left: 1%;
}

.bottom-box-border {
    /* background: #526d84; */
    background: #00070c61;
    /* opacity: 0.9; */
    border-radius: 5px;
    /* position: absolute; */
    width: 96%;
    height: 65%;
    margin: 0 2%;
}
</style>