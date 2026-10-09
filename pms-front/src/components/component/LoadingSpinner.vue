<template>  
<section>
  <div class="loader">
  </div>
  <p class="loading-text">Loading...</p>
</section>
  
</template>

<script>
export default {};
</script>

<style scoped>
*{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
section{
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
}
.loader {
  font-size: 10px;
  margin: 50px auto;
  text-indent: -9999em;
  width: 7em;
  height: 7em;
  border-radius: 50%;
  background: rgb(34, 103, 213);
  background: -moz-linear-gradient(left, rgb(34, 103, 213) 10%, rgba(255, 255, 255, 0) 42%);
  background: -webkit-linear-gradient(left, rgb(34, 103, 213) 10%, rgba(255, 255, 255, 0) 42%);
  background: -o-linear-gradient(left, rgb(34, 103, 213) 10%, rgba(255, 255, 255, 0) 42%);
  background: -ms-linear-gradient(left, rgb(34, 103, 213) 10%, rgba(255, 255, 255, 0) 42%);
  background: linear-gradient(to right, rgb(34, 103, 213) 10%, rgba(255, 255, 255, 0) 42%);
  position: absolute;
  -webkit-animation: load3 1.4s infinite linear;
  animation: load3 1.4s infinite linear;
  -webkit-transform: translateZ(0);
  -ms-transform: translateZ(0);
  transform: translateZ(0);
}
.loader:before {
  width: 50%;
  height: 50%;
  background: rgb(34, 103, 213);
  border-radius: 100% 0 0 0;
  position: absolute;
  top: 0;
  left: 0;
  content: '';
}
.loader:after {
  background: rgb(22, 30, 55);
  width: 75%;
  height: 75%;
  border-radius: 50%;
  content: '';
  margin: auto;
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
}
@-webkit-keyframes load3 {
  0% {
    -webkit-transform: rotate(0deg);
    transform: rotate(0deg);
  }
  100% {
    -webkit-transform: rotate(360deg);
    transform: rotate(360deg);
  }
}
@keyframes load3 {
  0% {
    -webkit-transform: rotate(0deg);
    transform: rotate(0deg);
  }
  100% {
    -webkit-transform: rotate(360deg);
    transform: rotate(360deg);
  }
}
 .loading-text {
  position: relative;
  left: 100px;
  color: #fff; /* 텍스트 색상 설정 */
  font-size: 20px;
}
</style>
