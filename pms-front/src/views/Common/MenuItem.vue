<template>
    <div v-if="menuKey == 0" class="mainMenuContainerMenuItem fontMenu" @click="$emit('handleMenuClick')">
        <div :class=menuClass></div>
        {{ menuTitle }}
    </div>


    <div v-if="menuKey == 1" class="subMenuContents fontServeMenu 1depth" style="color: rgb(255, 255, 255);"
        @click="$emit('handleMenuClick')">
        <img :src="require(`@/assets/img/${menuImg}`)"
            style="margin-left: 13px; margin-right: 12px; width: 20px; height: 18px; background-size: 100%; ">
        {{ menuTitle }}
    </div>

    <div v-if="menuKey == 2" class="subMenuContents">
        <li class="subMenuItemList" style="color: rgb(255, 255, 255);">{{ menuTitle }}</li>
    </div>

    <div class=" twoDepthMenu SeoundMenu" v-if="menuKey == 4" @click="$emit('handleMenuClick')">
        <div class="subMenuContents songsuLi">
            <li class="">{{ menuTitle }}</li>
        </div>
    </div>

    <div v-if="menuKey == 100" class="subMenuTitle">
        <img :src="require(`@/assets/img/${menuImg}`)"
            style="margin-left:13px; margin-right: 5px; width: 25px; height: 23px; background-size: 100%;">
        <span class="fontServeTitle">{{ menuTitle }}</span>
    </div>
    <div v-if="menuKey == 101" class="subMenuContents SeoundMenu" @click="$emit('handleMenuClick')">
        <li class="">{{ menuTitle }}</li>
    </div>
</template>

<script>
export default {
    props: ['menuImg', 'menuClick', 'menuTitle', 'menuKey', 'menuClass'],
    emits: ['handleMenuClick'],
    methods: {

    }
}
</script>

<style>
.SeoundMenu {
    padding-left: 30px;
}

.songsuLi {
    list-style-type: none;
    font-size: 12px;
    margin-left: 25px;
}
</style>