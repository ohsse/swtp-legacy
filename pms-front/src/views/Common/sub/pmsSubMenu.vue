<template>
    <MenuItem menuImg="icon/pms.png" menuKey="100" menuTitle="스마트PMS" />

    <!-- 스마트정수정 pms 1탭스 메뉴만 정리함 -->
    <MenuItem menuImg="icon/pms_dash.svg" @handleMenuClick="this.$router.push('/')" menuTitle="대시보드" menuKey="1" />

    <MenuItem menuImg="icon/AUTO_MENU/auto_songsu.svg" @handleMenuClick="isAutoSongsu = !isAutoSongsu" menuTitle="송수"
        menuKey="1" />
    <div class="twoDepthMenu" v-if="isAutoSongsu">
        <MenuItem @handleMenuClick="this.$router.push('/PumpControl')" menuTitle="송수펌프모터" menuKey="101" />
    </div>

    <MenuItem menuImg="icon/PMS_MENU/tonggae.png" @handleMenuClick="this.$router.push('/StatsHistory')" menuTitle=" 통계/이력"
        menuKey="1" />
        
    <MenuItem menuImg="icon/PMS_MENU/tonggae.png" @handleMenuClick="this.$router.push('/PrecisionDiagnosis')" menuTitle="정밀진단"
    menuKey="1" />
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

<style></style>