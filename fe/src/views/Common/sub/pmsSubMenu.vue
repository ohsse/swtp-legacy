<template>
    <MenuItem menuImg="icon/pms.png" menuKey="100" menuTitle="스마트PMS" />

    <!-- 스마트정수정 pms 1탭스 메뉴만 정리함 -->
    <MenuItem menuImg="icon/pms_dash.svg" @handleMenuClick="this.$router.push('/pms')" menuTitle="대시보드" menuKey="1"
        :noSub="true" />

    <MenuItem menuImg="icon/AUTO_MENU/auto_songsu.svg" @handleMenuClick="isAutoSongsu = !isAutoSongsu" menuTitle="송수"
        menuKey="1" />
    <div class="twoDepthMenu" v-if="isAutoSongsu">
        <MenuItem @handleMenuClick="this.$router.push('/PMSPumpControl')" menuTitle="송수펌프모터" menuKey="101"
            :noSub="true" />
    </div>

    <MenuItem menuImg="icon/PMS_MENU/tonggae.png" @handleMenuClick="this.$router.push('/StatsHistory')"
        menuTitle=" 통계/이력" menuKey="1" :noSub="true" />

    <MenuItem menuImg="icon/PMS_MENU/tonggae.png" @handleMenuClick="this.$router.push('/PrecisionDiagnosis')" menuTitle="정밀진단"
    menuKey="1" :noSub="true"/>

</template>

<script>
import MenuItem from '../MenuItem.vue'
export default {
    components: { MenuItem },
    data() {
        return {
            isChaksu: false, isYakpoom: false, isHonhwa: false, isChemjeon: false, isYeogwa: false, isGac: false, isOzone: false, isSodoc: false, isAutoSongsu: false
        }
    }

}
</script>

<style>
/* twodepth 배경색 */
.subMenu>.subMenuContents.fontServeMenu.one-depth {
    background: #1d3f69;
}

/* twodepth 화살표 */
.subMenu>.subMenuContents.fontServeMenu.one-depth::after,
.subMenu>.twoDepthMenu>.subMenuContents.SeoundMenu.two-depth::after {
    content: "";
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #fff;
    position: absolute;
    right: 10px;
}
</style>