<template>
    <div v-if="!isPopup" class="select_btn_font_title"
        style="font-size: 18px; margin-left:16px; margin-right:20px; font-family:none; white-space: nowrap;"> AI
        운전모드
    </div>
    <div v-if="!isPopup" class="btn-round-wrap" style="margin-left: 20px;">
        <div v-for="(item, index) in aiMode" :key="index" @click="changeTab(index)"
            :class="{ 'select_btn select_btn_font fL btn-round': true, 'active-tab': selectedIndex === index }">{{ item
            }}</div>
    </div>
    <div v-if="isPopup" class="btn-round-wrap" style="margin-left: 10px;">
        <div v-for="(item, index) in aiMode" :key="index"
            :class="{ 'select_btn select_btn_font fL btn-round': true, 'active-tab': selectedIndex === index }">{{ item
            }}</div>
    </div>
</template>
<script>
import { fetchFunc } from '@/util/fetchFunc';
import { useStore } from 'vuex';
import Swal from 'sweetalert2'
// import { watch } from "vue";
export default {
    props: ['autoData', 'index', 'isPopup'],
    data() {
        return {
            aiMode: ['AI', 'AI 추천', 'AI 분석'],
            selectedIndex: -1,
            data: {},
            emerData: 0,
            store: useStore(),
            message: "AI 모드를 수정하시겠습니까?",
        }
    },
    mounted() {
        if (this.isPopup == true) {
            this.selectedIndex = 1
        }
        // this.$store.state.aiFlag = true
        // watch(() => this.$store.state.aiFlag, () => {
        //     // this.message = "AI 분석모드로 전환됩니다."
        //     this.changeTabForPopUp(2, this.$store.state.aiPumpGrp)
        // });
    },
    beforeUpdate() {
        // console.log(this.selectedIndex)
    },
    methods: {
        /**
         * 군산 5분 제어 판단: 모드 전환이 진행 중·승인 대기 명령에 미치는 영향을 확인창에 덧붙인다.
         * (docs/gunsan-ctrl-workflow.html 5.1)
         */
        async ctrlCmdNotice(nextMode) {
            if (this.$area !== 'gunsan') return ''
            try {
                const data = (await fetchFunc(`${this.$apiURL}/ai/ctrl/pending`)).data || {}
                if (!data.consumerEnabled) return ''
                const notes = []
                if (data.queueActiveCount > 0) {
                    notes.push(`진행 중인 제어 명령 ${data.queueActiveCount}건이 폐기됩니다.`)
                }
                const waiting = (data.items || []).filter(i => !i.BLOCK_REASON).length
                if (waiting > 0 && nextMode === 0) {
                    notes.push(`승인 대기 중인 추천 ${waiting}건이 자동 송신됩니다.`)
                } else if (waiting > 0 && nextMode === 2) {
                    notes.push(`승인 대기 중인 추천 ${waiting}건은 송신되지 않습니다.`)
                }
                return notes.length ? ' ' + notes.join(' ') : ''
            } catch (e) {
                return ''
            }
        },
        async changeTab(index) {
            const confirmed = await Swal.fire({
                animation: false,
                text: `${this.message}${await this.ctrlCmdNotice(index)}`,
                showCancelButton: true,
                confirmButtonText: '적용',
                cancelButtonText: '취소',
                confirmButtonColor: 'rgba(239, 194, 240, 0.25)',
                cancelButtonColor: 'rgba(239, 194, 240, 0.25)'
            });
            if (confirmed.isConfirmed) {
                this.data.PUMP_GRP = this.index.toString()
                this.data.STATUS = index
                // if (this.emerData != 0) {
                fetchFunc(`${this.$apiURL}/ai/updateAiStatus`, this.data)
                    .then(() => {
                        Swal.fire({
                            animation: false,
                            text: '정상적으로 수정되었습니다.'
                        });
                        this.selectedIndex = index
                        this.$emit('changeAutoPart', this.selectedIndex, this.emerData, true)
                        this.$emit('changePumpControl', this.selectedIndex)
                        location.reload()
                        // this.$emit('getAiStatus')
                    }
                    );
                // }
                // else {
                //     Swal.fire({
                //         animation: false,
                //         text: '비상정지 모드를 해제해주세요.'
                //     });
                // }
                this.message = "AI 모드를 수정하시겠습니까?"
            }
            // this.$emit('changeData', index);
        },
        async changeTabForPopUp(index, pumpGrp) {
            this.message = "AI추천 모드로 운전중입니다.<br>확인을 누르시는 경우 AI분석 모드로 변경됩니다."
            const emerData = (await fetchFunc(`${this.$apiURL}/ai/selectAiStatus`)).data[pumpGrp - 1]?.emergencyStatus
            const confirmed = await Swal.fire({
                animation: false,
                html: this.message,
                showCancelButton: true,
                confirmButtonText: '적용',
                cancelButtonText: '취소',
                confirmButtonColor: 'rgba(239, 194, 240, 0.25)',
                cancelButtonColor: 'rgba(239, 194, 240, 0.25)'
            });

            if (confirmed.isConfirmed) {
                this.data.PUMP_GRP = pumpGrp.toString()
                this.data.STATUS = index
                // if (emerData != 0) {
                fetchFunc(`${this.$apiURL}/ai/updateAiStatus`, this.data)
                    .then(() => {
                        Swal.fire({
                            animation: false,
                            text: '정상적으로 수정되었습니다.'
                        });
                        this.selectedIndex = index
                        this.$emit('changeAutoPart', this.selectedIndex, emerData, true)
                        this.$emit('changePumpControl', this.selectedIndex)
                        // this.$emit('getAiStatus')
                        window.location.href = "PumpDrvnAnly"
                    }
                    );
                // }
                // else {
                //     Swal.fire({
                //         animation: false,
                //         text: '비상정지 모드를 해제해주세요.'
                //     });
                // }
            }
            // this.$emit('changeData', index);
        },
        changeAuto(index, emerData) {
            this.emerData = emerData
            this.selectedIndex = index
        }
    }
}
</script>
<style>
/* [송수펌프 제어 분석] 페이지용 AI운전보드 선택 버튼 */
.select_btn_font_title {
    text-shadow: 0 0 9px #5cafff;
    font-size: 13px;
    color: #a8d0f5;
    font-family: 'KHNPHDBold';
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
}

.btn-round-wrap {
    height: 30px;
    border-radius: 20px;
    padding: 2px;
    background: #334b70;
}

.btn-round-wrap .select_btn {
    color: #313131;
    background-color: #4b668d;
}

.btn-round {
    border-radius: 20px;
}

.active-tab {
    color: #000 !important;
    background-color: #b4dffa !important;
    -webkit-box-shadow: 0px 0px 5px 1px rgba(180, 223, 250, 0.6);
    -moz-box-shadow: 0px 0px 5px 1px rgba(180, 223, 250, 0.6);
    box-shadow: 0px 0px 5px 1px rgba(180, 223, 250, 0.6);
}

/* //[송수펌프 제어 분석] 페이지용 AI운전보드 선택 버튼 */

/* [대시보드] 페이지 */
.select_btn_font {
    /*text-shadow: 0 0 9px #5cafff;*/
    font-size: 13px;
    color: #000;
    font-family: 'KHNPHDBold';
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
}

.select_btn {
    width: fit-content;
    height: 26px;
    padding: 5px 10px;
    align-self: center;
    color: #939cb0;
    font-weight: 400 !important;
    background-color: #2f4161;
    cursor: pointer;
    border: 1px solid #b4dffa;
    margin-left: 5px;
}

.select_btn.active {
    color: white;
    background-color: #587da8;
    -webkit-box-shadow: 0px 0px 5px 1px rgba(180, 223, 250, 0.6);
    -moz-box-shadow: 0px 0px 5px 1px rgba(180, 223, 250, 0.6);
    box-shadow: 0px 0px 5px 1px rgba(180, 223, 250, 0.6);
}

.select_btn:first-child {
    margin-left: 0;
}

.swal2-container {
    z-index: 20000 !important;
}
</style>