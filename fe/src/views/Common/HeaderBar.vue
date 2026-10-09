<template>
    <header class="header containerBox">
        <div class="dateCss">
            <span class="text_timer text_timer-char">현재시간 </span>
            <span class="text_timer text_timer-num">{{ currentTime }}</span>
        </div>
        <div class="d-flex header_center" style="padding-top: 2px; padding-right: 225px;">
            <div class="header_environment" alt="환경부 로고"></div>
            <div class="header-title mb-0" @click="this.$router.push('/')">스마트 정수장 AI 플랫폼 </div>
            <div class="header_kwater" alt="k-water 로고"></div>
            <div class="header-bottom"></div>
        </div>
        <div>
            <div class="containerBox loginBox">
                <div v-show="limitTime" class="login__badge fL" @click="resetTimer">
                    <!-- <span class="login__badge--time">{{ displayMinutes }}:{{ displaySeconds }}</span> -->
                    <span class="login__badge--text">{{ user }}</span>
                </div>
                <img src="@/assets/img/user_img.png" alt="사람모양 이모티콘" class="userImg" @click="userClick()">
            </div>
        </div>
    </header>
</template>

<script>
import Swal from 'sweetalert2';
export default {
    data() {
        return {
            currentTime: '',
            minutes: 30,
            seconds: 0,
            user: 'KWATER', // Default value
            limitTime: false,
            usrNm: '김철수',
            role: '관리자' // 선택 사항
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
        console.log('--- localStorage의 모든 항목 ---');
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            const value = localStorage.getItem(key);
            console.log(`${key}: ${value}`);
        }
        console.log('------------------------------');

        const storedUser = localStorage.getItem('user');
        const storedUsrNm = localStorage.getItem('usrNm');
        const storedRole = localStorage.getItem('usrAuth');
        const storedUsrTi = localStorage.getItem('usrTi'); 

        console.log('localStorage에서 가져온 user 값:', storedUser);

        if (storedUser) {
            this.user = storedUser;
            this.usrNm = storedUsrNm;
            this.role = storedRole === '1' ? '운영자' : '관리자';
            if (storedUsrTi) {
                this.minutes = parseInt(storedUsrTi, 10);
            }
        }
        if (storedUsrTi !== '0') {
            this.startTimer();
            window.addEventListener('mousemove', this.resetTimerOnMouseMove);
            this.limitTime = true;
        } else {
            this.limitTime = false;
        }

        setInterval(this.updateTime, 1000);
        this.updateTime();
    },
    beforeUnmount() {
        window.removeEventListener('mousemove', this.resetTimerOnMouseMove);
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
                this.clickAuto();
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
            const storedUsrTi = localStorage.getItem('usrTi');
            if (storedUsrTi === '0') {
                return;
            }
            clearInterval(this.timerInterval);
            this.minutes = parseInt(storedUsrTi, 10) || 30;
            this.seconds = 0;
            this.startTimer();
        },
        resetTimerOnMouseMove() {
            const storedUsrTi = localStorage.getItem('usrTi');
            if (storedUsrTi !== '0') {
                this.resetTimer();
            }
        },
        userClick(){
            Swal.fire({
                title: '사용자 정보',
                html: `
                    <p style="text-align: left; margin-bottom: 5px;">
                    <strong>사용자 계정명:</strong> ${this.user}
                    </p>
                    <p style="text-align: left; margin-bottom: 15px;">
                    <strong>사용자 이름:</strong> ${this.usrNm}
                    ${this.role ? `<span style="font-size: 0.9em; color: #666; margin-left: 5px;">(${this.role})</span>` : ''}
                    </p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 15px 0;">
                    <p style="text-align: center; margin-top: 15px;">
                    로그아웃 및 정보수정을 위해<br>
                    자율운영 시스템으로 이동하시겠습니까?
                    </p>
                `,
                showCancelButton: true,
                confirmButtonText: '이동',
                cancelButtonText: '취소',
                animation: false,
                allowOutsideClick: false,
                allowEscapeKey: false,
                customClass: {
                    actions: 'my-swal-actions'
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    this.clickAuto();
                }
            });
        },
        clickAuto() {
            const token = localStorage.getItem('token')
            const noTokenAreas = ['gumi', 'hakya', 'haepyeong', 'unmun', 'jain', 'goryeong']
            if (noTokenAreas.includes(this.$area)) {
                this.$router.push(`/auto`);
            } else {
                this.$router.push(`/auto/${token}`);
            }
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

.login__badge {
    margin-right: 15px;
    padding-top: 5px;
    width: 100px;
    height: 30px;
    border-radius: 15px;
    border: 1px solid #7aa2bd;
    background-color: rgba(101, 183, 255, .35);
    cursor: pointer;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    text-shadow: 0 0 6px #5cafff;
    font-weight: 400;
}

.login__badge--time {
    padding-right: 3px;
    padding-bottom: 2.3px;
    font-size: 18px;
    line-height: 1.22;
    color: #b4dffa;
    font-family: 'Barlow';

}

.login__badge--text {
    color: #b4dffa;
    padding-bottom: 5.3px;
    font-size: 15px;
    line-height: 1.4;
    font-family: 'EliceDigitalBaeum_Regular';
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
    position: relative;
    z-index: 1;
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
    font-family: LABDigital;
    font-size: 25px;
    line-height: 1.2;
}

.swal2-actions {
    margin-bottom: 10px !important;
}
</style>