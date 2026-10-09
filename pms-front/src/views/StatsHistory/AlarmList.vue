<template>
    <b-row>
        <b-col md="12" class="position-relative">
            <div class="chart-box">
                <div class="chart-area w-100">
                    <div class="chart-con">
                        <div class="box-edge top-L blur" data-v-789da364=""></div>
                        <div class="box-edge top-R blur" data-v-789da364=""></div>
                        <div class="box-edge bottom-L blur" data-v-789da364=""></div>
                        <div class="box-edge bottom-R blur" data-v-789da364=""></div>
                        <div class="box-edge top-L" data-v-789da364=""></div>
                        <div class="box-edge top-R" data-v-789da364=""></div>
                        <div class="box-edge bottom-L" data-v-789da364=""></div>
                        <div class="box-edge bottom-R" data-v-789da364=""></div>
                        <div class="chart">
                            <!-- 서브 타이틀 시작 -->
                            <div class="title-box mb-3">
                                <img src="@/assets/img/circle.6d33197f.svg" alt="타이틀 블릿 이미지">
                                <p class="mb-0">알람 리스트</p>
                            </div>
                            <!-- 서브 타이틀 끝 -->
                            <!-- 날짜 조회 시작 -->
                            <div class="location">
                                <CalendarBox :alarmList="alarmList" @alarmListDate="alarmListDate" />
                            </div>
                            <button class="button2" @click="downloadCSV">CSV 다운로드</button>
                            <!-- 날짜 조회 끝 -->
                            <!-- 챠트 영역 시작 -->
                            <div style=" height: 500px;">
                                <ListGrid style="text-align: center;" ref="listGrid" />
                            </div>
                            <!-- 챠트 영역 끝 -->
                        </div>
                    </div>
                </div>
            </div>
        </b-col>
    </b-row>
</template>

<script>
import CalendarBox from '@/components/component/CalendarBox.vue'
import ListGrid from './ListGrid.vue'
import { useStore } from 'vuex'
import axios from 'axios'
export default {
    components: { CalendarBox, ListGrid },
    data() {
        const store = useStore();
        let alarmListData = [];
        return {
            store,
            alarmList: true,
            alarmListData
        }
    },
    methods: {
        async alarmListDate(from, to) {
            let startDate = new Date(from.getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ")
            let startDt = startDate.split(' ')[0]
            let endDate = new Date(to.getTime() + 9 * 60 * 60 * 1000).toISOString().replace("T", " ")
            let endDt = endDate.split(' ')[0]

            let params = {
                startDate: startDt,
                endDate: endDt
            };
            const res = await axios.get(`${this.store.state.globalIP}/api/v1/alarm/alarmList`, { params })
            const data = res.data.datas
            this.alarmListData = data
            if(data!=null){
                this.$refs.listGrid.setRowData(data);
            }
                
        },
        downloadCSV() {
            console.log("this.alarmListData", this.alarmListData);
            let _headers = ['일시', '설비명', '설비정보', '진단상태', '알람상태'];
            let csvData = [];

            csvData.push(_headers);

            for (let index = 0; index < this.alarmListData.length; index++) {
                let row = this.alarmListData[index];
                let csvRow = [
                    row.ALR_TIME,    // 일시
                    row.FAC_NAME,    // 설비명
                    row.FAC_INFO,    // 설비정보
                    row.DIAG_STUS,   // 진단상태
                    row.FLAG         // 알람상태
                ];
                csvData.push(csvRow);
            }

            let lineArray = [];
            csvData.forEach(function(infoArray, index) {
                let line = infoArray.join(",");
                lineArray.push(index === 0 ? "\uFEFF" + line : line); 
            });
            let csvContent = lineArray.join("\n");

            let blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
            let link = document.createElement("a");

            if (link.download !== undefined) {
                link.setAttribute("href", window.URL.createObjectURL(blob));
                link.setAttribute("download", 'alarm_list.csv');  // 파일 이름 설정
                link.setAttribute("hidden", true);
            } else {
                console.log('error');
                link.setAttribute("href", "#");
            }
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);  // 다운로드 후 링크 제거
        }

    },

}
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.title-box {
    font-size: 18px;
    display: flex;
    align-items: center;
    /* height: 15%; */
    color: #c8d7e9;
    text-shadow: 0px 0px 10px #24baff;
}

.title-box img {
    width: 16px;
    margin-right: 8px;
}

.chart-box {
    flex: 1;
    width: 100%;
    /* height: calc(100% / 2); */
    height: initial;
    display: flex;
    gap: 20px;
}

.chart-area {
    position: relative;
    width: 50%;
    height: 100%;
    background: rgba(0, 0, 0, 0.25);
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.chart-con {
    position: relative;
    float: left;
    width: 100%;
    height: 100%;
    border: 1px solid #2660ab;
    border-radius: 12px;
    padding: 15px;
}

.top-L {
    top: -1px;
    left: -1px;
    border-top: 2px solid #2C80FF;
    border-left: 2px solid #2C80FF;
    border-top-left-radius: 12px;
}

.top-R {
    top: -1px;
    right: -1px;
    border-top: 2px solid #2C80FF;
    border-right: 2px solid #2C80FF;
    border-top-right-radius: 12px;
}

.box-edge {
    width: 15px;
    height: 15px;
    position: absolute;
}

.bottom-L {
    bottom: -1px;
    left: -1px;
    border-bottom: 2px solid #2C80FF;
    border-left: 2px solid #2C80FF;
    border-bottom-left-radius: 12px;
}

.bottom-R {
    bottom: -1px;
    right: -1px;
    border-bottom: 2px solid #2C80FF;
    border-right: 2px solid #2C80FF;
    border-bottom-right-radius: 12px;
}

.location {
    position: absolute;
    top: 10px;
    right: 69px;
    height: 30px;
    display: flex;
    justify-content: end;
    gap: 10px;
    align-items: center;
    margin-bottom: 10px;
}

.location .search1 {
    display: flex;
    gap: 6px;
    align-items: center;
    position: relative;
}

.location .search1 input {
    border: none;
    outline: none;
    border-bottom: 2px solid #2660ab;
    background: rgba(255, 255, 255, 0.1);
    padding: 6px 10px;
    color: white;
    font-size: 18px;
    cursor: pointer;
    width: 130px;
}

.location .search1 span {
    color: white;
}

.location .search1 input {
    border: none;
    outline: none;
    border-bottom: 2px solid #2660ab;
    background: rgba(255, 255, 255, 0.1);
    padding: 6px 10px;
    color: white;
    font-size: 18px;
    cursor: pointer;
    width: 130px;
    height: 34px;
}

.location .button {
    outline: none;
    border: none;
    width: auto;
    height: 34px;
    padding: 10px 20px;
    background: linear-gradient(to right bottom, #0f77ff, #07418d);
    color: white;
    border-radius: 8px;
    font-size: 18px;
    line-height: 18px;
    cursor: pointer;
}

.button2 {
    position: absolute;
    right: 26px; /* 오른쪽 끝으로 이동 */
    top: 20px; /* 필요에 따라 상단 위치 조정 */
    outline: none;
    border: none;
    width: auto;
    height: 31px;
    padding: 10px 20px;
    background: linear-gradient(to right bottom, #3d91fe, #07418d);
    color: white;
    border-radius: 8px;
    font-size: 14px;
    line-height: 16px;
    cursor: pointer;
}
</style>