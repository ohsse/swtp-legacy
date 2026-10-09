<template>
   <div class="" style="display: flex; justify-content: center; position: absolute;">
      <div class="datacube">
         <div style="display: flex; align-items: center;">
            <span class="cubevalue">{{ cubeVal }}</span><span class="percentage">%</span>
         </div>
      </div>
      <div class="aura"></div>
   </div>
</template>

<script>
export default {
   props: [
      'cubeVal'
   ]
}
</script>

<style>

.datacube {
   /* z-index: 5;
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
   line-height: 111px; */

   z-index: 5;
   pointer-events: none;
   width: 80px;
   height: 80px;
   background: url(@/assets/img/cube__inner.png) 100% 100% no-repeat;
   background-size: 80px 80px;
   display: flex;
   top: 0px;
   align-items: center;
   justify-content: center;
   animation: updown ease-in-out 2s infinite alternate;
   position: absolute;
}

.building-visible {
   display: block !important;
}

/* .cube__inner {
   width: 80px;
   height: 80px;
   display: flex;
   align-items: center;
   justify-content: center;
   background-image: url(@/assets/img/cube__inner.png);
}

.cube__noimg {
   width: 80px;
   height: 80px;
   -webkit-transform-style: preserve-3d;
   -webkit-transform: rotateX(0) rotateY(0) rotateZ(0);
   transform-style: preserve-3d;
   transform: rotateX(0) rotateY(0) rotateZ(0);
}

.cube__front_logo {
   width: 80px;
   height: 80px;
   background-image: url(/img/cube_ai_icon.721ecad2.png);
   background-position: center;
   background-size: cover;
   position: absolute;
   -webkit-backface-visibility: hidden;
   backface-visibility: hidden;
   display: flex;
   align-items: center;
   justify-content: center;
} */


.cubevalue {
   font-family: LABDigital !important;
   font-size: 20px;
   color: #c3eaff;
   letter-spacing: 1px;
   line-height: 111px;
}

.percentage {
   font-family: LABDigital !important;
   font-size: 22px;
   color: #c3eaff;
   letter-spacing: 1px;
   line-height: 106px;
}

.aura {
  width: 110px;
  height: 150px;
  background: url(@/assets/img/aura_bottom.png) 100% 100% no-repeat;
  /* display: block !important; */
  box-sizing: inherit;
  pointer-events: none;
  /* top: 0px;
  left: 0px; */
  animation: blink-v 3s infinite alternate;
  position: absolute;
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