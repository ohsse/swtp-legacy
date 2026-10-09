<template>
    <!--해더 컴포넌트의 템플릿 부분 -->

    <header class="header containerBox">
        <div class="dateCss">
            <span class="text_timer text_timer-char">현재시간 </span>
            <span class="text_timer text_timer-num">{{ currentTime }}</span>
        </div>
        <div class="d-flex header_center" style="padding-top: 2px; padding-right: 180px;">
            <div class="header_environment" alt="환경부 로고"></div>
            <div class="header-title mb-0" @click="this.$router.push('/')">스마트 정수장 AI 플랫폼 </div>
            <div class="header_kwater" alt="k-water 로고"></div>
            <div class="header-bottom"></div>
        </div>
        <div>
            <!-- 로그인 공간 -->
            <div class="containerBox loginBox">
                <!-- 15분 단위 타이머 미리 작업한거 주석 처리 -->
                <!-- <div class="timerCss">{{ displayMinutes }}:{{ displaySeconds }}</div> -->
                <div id="ctgry2" class="select_btn select_btn_font fL">{{ user }}</div>
                <!-- <div id="ctgry2" class="select_btn fL" @click="$emit('allPageAlarm')">00 : 00 로그인 연장</div> -->
                <img src="@/assets/img/user_img.png" alt="사람모양 이모티콘" class="userImg">
            </div>
        </div>
    </header>
</template>

<script>
export default {
    data() {
        return {
            currentTime: '',
            minutes: 15,
            seconds: 0,
            user: ''
        }
    },
    computed: {
        displayMinutes() {
            return this.minutes < 10 ? '0' + this.minutes : this.minutes;
        },
        displaySeconds() {
            return this.seconds < 10 ? '0' + this.seconds : this.seconds;
        }
    },
    mounted() {
        this.user = localStorage.getItem('user');
        this.startTimer();
        setInterval(this.updateTime, 1000);
        this.updateTime();
    },
    methods: {
        updateTime() {
            let DayFrom = new Date();
            const year = DayFrom.getFullYear();
            const month = String(DayFrom.getMonth() + 1).padStart(2, "0");
            const day = String(DayFrom.getDate()).padStart(2, "0");
            const hour = DayFrom.getHours();
            const min = DayFrom.getMinutes();
            const sec = DayFrom.getSeconds();
            const search = `${year}.${month}.${day} ${hour}:${min}:${sec}`;
            this.currentTime = search;
        },
        startTimer() {
            this.timerInterval = setInterval(this.updateTimer, 1000);
        },
        updateTimer() {
            if (this.minutes === 0 && this.seconds === 0) {
                clearInterval(this.timerInterval);
                // alert("로그인세션 끝났습니다. == ", this.minutes, this.seconds);
            } else {
                if (this.seconds === 0) {
                    this.minutes--;
                    this.seconds = 59;
                } else {
                    this.seconds--;
                }
            }
        },
        resetTimer() {
            clearInterval(this.timerInterval);
            this.minutes = 15;
            this.seconds = 0;
            this.startTimer();
        }
    },

}
</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
.dateCss {
    width: 330px;
    font-size: 25px;
    padding: 14px 0 0 20px;
}

.header_center {
    position: relative;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    justify-content: center;
    align-items: center;
}

.containerBox {
    display: flex;
    justify-content: space-between;
}

.select_btn {
    margin-right: 15px;
    padding-top: 5px;
    width: 172px;
    height: 30px;
    border-radius: 15px;
    border: 1px solid #7aa2bd;
    background-color: rgba(101, 183, 255, .35);
    cursor: pointer;
    text-shadow: 0 0 9px #5cafff;
    font-size: 16px;
    color: #fff;
    font-family: 'KHNPHDotfB';
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
}

.timerCss {
    color: aliceblue;
    width: 78px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.userImg {
    margin: 5px 22px 0px 10px;
    width: 15px;
    height: 20px;
}

.loginBox {
    padding-top: 10px;
}

.text_timer {
    color: #c3eaff;
    text-shadow: 0 0 5px rgba(101, 183, 255);
}

.text_timer-char {
    font-family: KHNPUotfR;
    font-size: 20px;
    line-height: 1.1;
}

.text_timer-num {
    font-family: LAB디지털;
    font-size: 25px;
    line-height: 1.2;
}
</style>
