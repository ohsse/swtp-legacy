<template>
    <MenuItem menuImg="icon/auto.png" menuKey="101" menuTitle="자율운영" @handleMenuClick="this.$router.push('/auto')" />

    <!-- <MenuItem menuImg="icon/dashboard.png" @handleMenuClick="this.$router.push('/auto')" menuTitle="대시보드" menuKey="1" />
    
    <MenuItem menuImg="icon/AUTO_MENU/chaksu.png" menuTitle="착수"  @handleMenuClick="this.$router.push('/receivingAlgorithm')" menuKey="1" />
    
    <MenuItem menuImg="icon/AUTO_MENU/yakpoom.png" menuTitle="약품"  @handleMenuClick="this.$router.push('/coagulantsAlgorithm')" menuKey="1" />

    <MenuItem menuImg="icon/AUTO_MENU/honhwa.png" menuTitle="혼화/응집"  @handleMenuClick="this.$router.push('/mixingAlgorithm')" menuKey="1" />
    
    <MenuItem menuImg="icon/AUTO_MENU/chemjeon.png" menuTitle="침전"  @handleMenuClick="this.$router.push('/sedimentationAlgorithm')" menuKey="1" />
    
    <MenuItem menuImg="icon/AUTO_MENU/yeogwa.png"
    v-if="gacMenu || !gacNot"
    menuTitle="여과"  @handleMenuClick="this.$router.push('/filterAlgorithm')" menuKey="1" />

    <MenuItem menuImg="icon/AUTO_MENU/gac.png"
    v-if="gacMenu"
    menuTitle="GAC여과"  @handleMenuClick="this.$router.push('/gacAlgorithm')" menuKey="1" />
    
    
    <MenuItem menuImg="icon/AUTO_MENU/sodoc.png" menuTitle="소독"  @handleMenuClick="this.$router.push('/disinfectionAlgorithm')" menuKey="1" />

    <MenuItem menuImg="icon/AUTO_MENU/ozone.png"
    v-if="gacMenu"
    menuTitle="오존"  @handleMenuClick="this.$router.push('/ozoneAlgorithm')" menuKey="1" /> -->

</template>

<script>
import MenuItem from '../MenuItem.vue';

export default {
    components: { MenuItem },
    data() {
        let gacMenu;
        let gacNot
        return {
            gacMenu,
            gacNot
        }
    },
    mounted() {
        if (this.$area == 'gumi' || this.$area == 'goryeong') {
            this.gacMenu = true
        }
        else if (this.$area == 'haepyeong' || this.$area == 'gunsan') {
            this.gacNot = true
        }
    },
}
</script>

<style></style>