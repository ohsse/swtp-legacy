<template>
    <!-- 메뉴 첫번째 대분류 시작 -->
    <div class="mainMenuContainerMenu">
        <MenuItem menuClass="dashboard_btn_on" menuTitle="메인" @handleMenuClick="clickAuto()" menuKey="0" />
        <MenuItem menuClass="auto_btn_on" menuTitle="자율" @handleMenuClick="clickAuto()" menuKey="0" />
        <MenuItem menuClass="ems_btn_on" menuTitle="스마트EMS" @handleMenuClick="subMenuShow(); emsSub = true;"
            menuKey="0" />
        <MenuItem v-if="pmsArea" menuClass="pms_btn_on" menuTitle="스마트PMS" @handleMenuClick="clickPMS()" menuKey="0" />
        <MenuItem menuClass="setting_btn_on" menuTitle="운영 관리" @handleMenuClick="clickSetting()" menuKey="0" />
    </div>
    <!-- 메뉴 첫번째 대분류 끝-->
    <div class="subMenu" id="setting" style="left: 100px;" v-if="isSubShow" @mouseleave="subMenuLeave">
        <AutoSubMenu v-if="autoSub" />
        <!--자율 메뉴 끝-->
        <!-- 스마트 PMS 메뉴 시작-->
        <PmsSubMenu v-if="pmsSub" />
        <!-- 스마트 PMS 메뉴 끝-->
        <!--운영관리 메뉴 시작 -->
        <SettingSubMEnu v-if="settingSub" />
        <!--   스마트 EMS 메뉴 시작 -->
        <EmsSubMenu v-if="emsSub" />
    </div>
    <!--자율 메뉴 시작-->

</template>

<script>
import EmsSubMenu from './sub/EmsSubMenu.vue'
import MenuItem from './MenuItem.vue'
import SettingSubMEnu from './sub/settingSubMEnu.vue'
import PmsSubMenu from './sub/pmsSubMenu.vue'
import AutoSubMenu from './sub/autoSubMenu.vue'


export default {

    components: {
        AutoSubMenu, PmsSubMenu, SettingSubMEnu, MenuItem, EmsSubMenu
    },
    data() {
        return {
            emsSub: false, autoSub: false, pmsSub: false, settingSub: false,
            isSubShow: false,
            pmsArea: true
        }
    },
    mounted() {
        if (this.$area == 'gosan' || this.$area == 'gumi' || this.$area == 'hakya') {
            this.pmsArea = true
        }
        else {
            this.pmsArea = false
        }
    },
    methods: {
        goToSystem(path) {
            const token = localStorage.getItem('token');
            const noTokenAreas = ['gumi', 'hakya', 'haepyeong', 'unmun', 'jain', 'goryeong'];
            
            if (noTokenAreas.includes(this.$area)) {
                this.$router.push(`/${path}`);
            } else {
                this.$router.push(`/${path}/${token}`);
            }
        },

        // 기존 click 메서드들을 간결하게 수정
        clickAuto() {
            this.goToSystem('auto');
        },
        clickPMS() {
            this.goToSystem('pms');
        },
        clickSetting() {
            this.goToSystem('alarmHistory');
        },
        subMenuShow() {
            this.isSubShow = true;
            this.autoSub = false;
            this.emsSub = false;
            this.pmsSub = false;
            this.settingSub = false;
        },
        subMenuLeave() {
            this.subMenu = false;
            this.autoSub = false;
            this.pmsSub = false;
            this.settingSub = false;
            this.isSubShow = false;
        }

    }
}
</script>

<style>
.submenu {
    margin-top: -800px;
    margin-left: 100px;
}
</style>