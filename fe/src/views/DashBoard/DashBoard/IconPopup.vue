<template>
    <!-- style에 top,left값 지정 필수 -->
    <div style="position: absolute;">
        <div class="aura"></div>
        <div class="cube">0%</div>
    </div>
</template>

<script>
export default {

}
</script>

<style>
.aura {
    width: 110px;
    height: 150px;
    background: url(@/assets/img/aura_bottom.png) 100% 100% no-repeat;
    display: block !important;
    box-sizing: inherit;
    pointer-events: none;
    top: 0px;
    left: 0px;
    animation: blink-v 3s infinite alternate;
    position: absolute;
}

.cube {
    z-index: 5;
    pointer-events: none;
    width: 80px;
    height: 80px;
    background: url(@/assets/img/cube__inner.png) 100% 100% no-repeat;
    display: flex;
    align-items: center;
    justify-content: center;
    top: 10px;
    left: 13px;
    animation: updown ease-in-out 2s infinite alternate;
    position: absolute;
    font-family: LABDigital !important;
    font-size: 20px;
    color: #c3eaff;
    letter-spacing: 1px;
    line-height: 111px;
}

@keyframes updown {
    from {
        transform: translateY(0px)
    }

    to {
        transform: translateY(20px)
    }
}

@keyframes blink-v {
    0% {
        opacity: 0.5;
    }

    100% {
        opacity: 1;
    }
}
</style>