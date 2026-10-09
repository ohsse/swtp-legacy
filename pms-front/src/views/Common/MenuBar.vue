<template>
  <!--메뉴바 컴포넌트의 템플릿 부분 -->
  <div class="menu_cont">
    <!-- 템플릿 내용 -->
    <div class="menu">
      <div class="mainMenu">
        <div class="mainMenuContainer">
          <div class="mainMenuContainerLogo"></div>
          <MainMenuContainerMenu />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import MainMenuContainerMenu from './MainMenuContainerMenu.vue';

export default {
props:['subShow'],
components :{
  MainMenuContainerMenu
},
methods:{
  menuClick(text){
    this.subShow(text);
    this.menu = text;
  },
  data() {
    return {
      menu:'main',  
    }
  },
}
};

</script>

<style scoped>
/* 컴포넌트에만 적용되는 스타일 정의 */
a {
text-decoration: none;
color: black;
}

.menu-bar {
display: none;
}

/* 마우스 호버 시 메뉴바 보여줌 */
.menu:hover .menu-bar {
display: block;
background: rgb(30, 133, 157);
z-index: 9;
}

/* 메뉴바 스타일 설정 */
.menu-bar {
background-color: #f1f1f1;

flex: left;
top: 100%;
left: 0;
width: 200px;

}

#nomalems{
display: none;
}

.ems{
display: block;
width: 100%;
color: #f1f1f1;
}


</style>