<template>
    <div class="pipe_big_background">
        <div class="pipe_big_gauge " :style="guageHeight"> <!-- 여기 퍼센트 바꾸기 -->
            <div style="color: white; margin-top: -35px; text-align: center;font-family: 'LABDigital';" id="waterPercent"></div>
        </div>
    </div>
</template>
<script>
export default {
    data(){
        return{
            guageHeight:{
                'background-size': '100% 55%',
                bottom : '5.5%'
            }
        }
    },
    methods:{
        calculateHeight(value){
            const baseHeight = 0; // 최소 높이 값 (0%일 때)
            const maxHeight = 90; // 최대 높이 값 (100%일 때)
            
            // 입력된 백분율 값을 기반으로 높이를 계산
            const calculatedHeight = baseHeight + (maxHeight - baseHeight) * (value / 100);

            let bottomPer;
            if(calculatedHeight<70){
                bottomPer = '5.5%'
            }else{
                bottomPer = '5%';
            }

            this.guageHeight['background-size'] = `100% ${calculatedHeight}%`;
            this.guageHeight.bottom = bottomPer;
        }
    }
}
</script>
<style>
.pipe_big_gauge {
    background: url(@/assets/img/ai_song/pipe_big.png) no-repeat;
    width: 100%;
    height: 100%;
    background-size: 100% 55%; /** 90%가 꽉참 70% 이상일때는 bottom 값을 5%로 변경 */
    background-position: bottom center;
    float: left;
    position: absolute; /* 절대 위치로 설정 */
    bottom: 5.5%;
}
.pipe_big_background {
    background: url(@/assets/img/ai_song/pipe_big.png) no-repeat;
    width: 20%;
    height: 100%;
    background-size: 100% 90%;
    background-position: center;
    float: right;
    display: flex;
    align-items: flex-end;
    position: relative;
}
</style>