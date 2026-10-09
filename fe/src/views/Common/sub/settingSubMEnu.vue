<template>
    <MenuItem menuImg="icon/setting.png" menuKey="100" menuTitle="운영관리" />

    <MenuItem menuImg="icon/AUTO_MENU/alarm.png" menuTitle="알람 이력" @handleMenuClick="this.$router.push('/alarmHistory')"
        menuKey="1" />
    <MenuItem menuImg="icon/report01.png" menuTitle="제어 이력" @handleMenuClick="this.$router.push('/aiHistory')"
        menuKey="1" />
    <MenuItem menuImg="icon/ai.png" menuTitle="AI 운영 현황" @handleMenuClick="this.$router.push('/operationHistory')"
        menuKey="1" />
</template>

<script>
import MenuItem from '../MenuItem.vue'
export default {
    components: { MenuItem }

}
</script>

<style></style>