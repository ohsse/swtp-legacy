<template>
    <MenuItem menuImg="icon/ems.png" menuKey="100" menuTitle="스마트EMS" />

    <MenuItem menuImg="icon/dashboard.png" @handleMenuClick="this.$router.push('/ems')" menuTitle="대시보드" menuKey="1" />

    <MenuItem menuImg="icon/ai.png" menuTitle="AI 분석" @handleMenuClick="ai = !ai" menuKey="1" />
    <div class="twoDepthMenu" v-if="ai && !this.otherCompany">
        <!-- 송수펌프 제어 다음 메뉴 컴포넌트함 시험삼아 해봄 컨포넌트화 처리함 -->
        <MenuItem v-if="ai" menuKey="101" @handleMenuClick="songsumenu = !songsumenu" menuTitle="송수펌프 제어" />
        <MenuItem menuClick="location.href='PumpControl';" menuTitle="송수펌프 제어 분석" menuKey="4" v-if="songsumenu"
            @handleMenuClick="this.$router.push('/EMSPumpControl')" />
        <!-- <MenuItem  menuClick="location.href='PumpControlDetailed';" menuTitle="송수펌프 제어 세부 현황" menuKey="4" v-if="songsumenu" @handleMenuClick="this.$router.push('/PumpControlDetailed')"/> -->
        <!-- <MenuItem  menuClick="location.href='PumpControlTrand';" menuTitle="송수펌프 제어 트렌드" menuKey="4" v-if="songsumenu" @handleMenuClick="this.$router.push('/PumpControlTrand')"/> -->
        <MenuItem menuClick="location.href='PumpDrvnAnly';" menuTitle="운전현황 분석" menuKey="4" v-if="songsumenu"
            @handleMenuClick="this.$router.push('/PumpDrvnAnly')" />
        <MenuItem menuClick="location.href='PumpHistory';" menuTitle="송수펌프 제어 가동이력" menuKey="4" v-if="songsumenu"
            @handleMenuClick="this.$router.push('/PumpHistory')" />
        <MenuItem menuClick="location.href='PumpControlHistory';" menuTitle="송수펌프 제어 이력" menuKey="4" v-if="songsumenu"
            @handleMenuClick="this.$router.push('/PumpControlHistory')" />
        <!-- <MenuItem  menuClick="location.href='MajorDrainage';" menuTitle="주요 배수지 수위 현황" menuKey="4" v-if="songsumenu" @handleMenuClick="this.$router.push('/MajorDrainage')" /> -->

        <MenuItem v-if="ai" menuKey="101" @handleMenuClick="peak = !peak" menuTitle="전력피크" />
        <MenuItem menuClick="location.href='PowerPeakAnalysis';" menuTitle="전력피크 분석" menuKey="4" v-if="peak"
            @handleMenuClick="this.$router.push('/PowerPeakAnalysis')" />
        <!-- <MenuItem  menuClick="location.href='PowerPeakDetail'" menuTitle="전력피크 세부현황" menuKey="4" v-if="peak"   @handleMenuClick="this.$router.push('/PowerPeakDetail')"/> -->

        <!-- <MenuItem v-if="ai" menuKey="101" @handleMenuClick="dr=!dr" menuTitle="DR 참여"/>
        <MenuItem  menuClick="location.href='#';" menuTitle="DR 참여 분석" menuKey="4" v-if="dr" />
        <MenuItem  menuClick="location.href='#';" menuTitle="DR 참여 세부현황" menuKey="4" v-if="dr" /> -->
    </div>
    <div class="twoDepthMenu" v-if="this.otherCompany">
        <!-- 송수펌프 제어 다음 메뉴 컴포넌트함 시험삼아 해봄 컨포넌트화 처리함 -->
        <MenuItem v-if="ai" menuKey="101" @handleMenuClick="songsumenu = !songsumenu" menuTitle="송수펌프 제어" />
        <MenuItem menuTitle="송수펌프 제어 분석" menuKey="4" v-if="songsumenu" @handleMenuClick="goPump('PumpControl')" />
        <!-- <MenuItem  menuClick="location.href='PumpControlDetailed';" menuTitle="송수펌프 제어 세부 현황" menuKey="4" v-if="songsumenu" @handleMenuClick="this.$router.push('/PumpControlDetailed')"/> -->
        <!-- <MenuItem  menuClick="location.href='PumpControlTrand';" menuTitle="송수펌프 제어 트렌드" menuKey="4" v-if="songsumenu" @handleMenuClick="this.$router.push('/PumpControlTrand')"/> -->
        <MenuItem menuTitle="송수펌프 제어 세부 현황" menuKey="4" v-if="songsumenu"
            @handleMenuClick="goPump('PumpControlDetailed')" />
        <MenuItem menuTitle="송수펌프 제어 트렌드" menuKey="4" v-if="songsumenu" @handleMenuClick="goPump('PumpControlTrand')" />
        <MenuItem menuTitle="송수펌프 가동 이력" menuKey="4" v-if="songsumenu" @handleMenuClick="goPump('PumpHistory')" />
        <MenuItem menuTitle="주요 배수지 수위 현황" menuKey="4" v-if="songsumenu" @handleMenuClick="goPump('MajorDrainage')" />
        <MenuItem v-if="ai" menuKey="101" @handleMenuClick="peak = !peak" menuTitle="전력피크" />
        <MenuItem menuClick="location.href='PowerPeakAnalysis';" menuTitle="전력피크 분석" menuKey="4" v-if="peak"
            @handleMenuClick="this.$router.push('/PowerPeakAnalysis')" />
        <MenuItem v-if="ai" menuTitle="제어 이력" menuKey="101" @handleMenuClick="goPump('LogHistory')" />
    </div>


    <MenuItem @handleMenuClick="isEnergyUse = !isEnergyUse" menuTitle="에너지 사용 현황" menuKey="1"
        menuImg="icon/spend.png" />
    <div class="twoDepthMenu" v-if="isEnergyUse">
        <MenuItem menuKey="101" menuTitle="시설별 사용량" @handleMenuClick="this.$router.push('/ZoneUse')" />
        <MenuItem menuKey="101" menuTitle="설비별 사용량" @handleMenuClick="this.$router.push('/FacUse')" />
        <MenuItem menuKey="101" menuTitle="사용량 트렌드" @handleMenuClick="this.$router.push('/UseTrand')" />
    </div>

    <MenuItem @handleMenuClick="isEnergyOptimize = !isEnergyOptimize" menuTitle="에너지 절감 관리" menuKey="1"
        menuImg="icon/reduce.png" />
    <div class="twoDepthMenu" v-if="isEnergyOptimize">
        <MenuItem menuKey="101" menuTitle="최적요금제 분석" @handleMenuClick="this.$router.push('/CostAnaylsis')" />
        <MenuItem menuKey="101" menuTitle="절감목표 달성 현황" @handleMenuClick="this.$router.push('/ReductionTargetStatus')" />
    </div>

    <MenuItem v-if="hasToken" @handleMenuClick="isSetting = !isSetting" menuTitle="설정" menuKey="1"
        menuImg="icon/setting.png" />
    <div id="settingMenu" class="twoDepthMenu" v-if="isSetting && !this.otherCompany">
        <!-- <MenuItem  menuTitle="태그 정보" menuKey="101" @handleMenuClick="this.$router.push('/TagInfo')"/> -->
        <MenuItem menuTitle="송수펌프 운영" menuKey="101" @handleMenuClick="this.$router.push('/SongsuPumpOperation')"
            v-if="songsu" />
        <MenuItem menuTitle="전력요금제" menuKey="101" @handleMenuClick="this.$router.push('/EletricityPlan')" />
        <MenuItem menuTitle="절감목표" menuKey="101" @handleMenuClick="this.$router.push('/ReductionTarget')" />
        <!-- <MenuItem  menuTitle="목표 전력피크" menuKey="101" @handleMenuClick="this.$router.push('/TargetStategyPeak')"/> -->
    </div>
    <div id="settingMenu" class="twoDepthMenu" v-if="isSetting && this.otherCompany">
        <!-- <MenuItem  menuTitle="태그 정보" menuKey="101" @handleMenuClick="this.$router.push('/TagInfo')"/> -->
        <MenuItem menuTitle="송수펌프 운영" menuKey="101" @handleMenuClick="this.$router.push('/SongsuPumpOperation')"
            v-if="songsu" />
        <MenuItem menuTitle="전력요금제" menuKey="101" @handleMenuClick="this.$router.push('/EletricityPlan')" />
        <MenuItem menuTitle="절감목표" menuKey="101" @handleMenuClick="this.$router.push('/ReductionTarget')" />
        <MenuItem menuTitle="태그 관리" menuKey="101" @handleMenuClick="goPump('TagInfo')" />
        <MenuItem menuTitle="배수지 관리" menuKey="101" @handleMenuClick="goPump('WaterTankMst')" />
        <MenuItem menuTitle="Q-Table 관리" menuKey="101" @handleMenuClick="goPump('QTableMst')" />

        <!-- <MenuItem  menuTitle="목표 전력피크" menuKey="101" @handleMenuClick="this.$router.push('/TargetStategyPeak')"/> -->
    </div>
    <!-- <MenuItem @handleMenuClick="isReport = !isReport" menuTitle="보고서" menuKey="1" menuImg="icon/report01.png" />
    <div id="settingMenu" class="twoDepthMenu" v-if="isReport">
        <MenuItem menuTitle="일일 보고서" menuKey="101" @handleMenuClick="this.$router.push('/DailyReport')" />
    </div> -->
</template>
<script>
import MenuItem from '../MenuItem.vue'
import { useStore } from "vuex";
export default {
    components: { MenuItem }
    , data() {
        return {
            ai: false, songsumenu: false, peak: false,
            dr: false, isEnergyUse: false, isEnergyOptimize: false,
            isSetting: false, isReport: false, otherCompany: false, hasToken: true
        }
    },
    mounted() {
        const store = useStore();
        const area = store.state.area;
        if (area == 'gumi' || area == 'hakya') {
            this.songsu = false
        }
        else {
            this.songsu = true
        }
        if (area == 'gumi') {
            this.otherCompany = true
        }
        else {
            this.otherCompany = false
        }
        if (localStorage.getItem('auth') == true) {
            this.hasToken = false
        } else {
            this.hasToken = true
        }
    },
    methods: {
        goToDashboard() {
        },
        goPump(url) {
            window.location.href = 'http://localhost:11111/' + url
        }
    }
}
</script>