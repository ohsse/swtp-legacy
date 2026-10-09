import PumpDrvnAnlyForGosan from "@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/Gosan/PumpDrvnAnlyForGosan.vue";
import PumpDrvnAnlyForGoryeong from "@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/Goryeong/PumpDrvnAnlyForGoryeong.vue";
import PumpDrvnAnlyForGunsan from "@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/Gunsan/PumpDrvnAnlyForGunsan.vue";
import PumpDrvnAnlyForBuan from "@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/Buan/PumpDrvnAnlyForBuan.vue";
import PumpDrvnAnlyForSanseong from  "@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/Sanseong/PumpDrvnAnlyForSanseong.vue";
import PumpDrvnAnlyForUnmun from  "@/views/AiAnalysis/SongsuPumpCtr/PumpDrvnAnly/Unmun/PumpDrvnAnlyForUnmun.vue";
import MainDashBoard_jain from "@/views/DashBoard/MainDashBoard_jain.vue";

export default class drvnRoute {
    constructor(area) {
        this.path = '/PumpDrvnAnly';
        this.name = 'PumpDrvnAnly';
        switch (area) {
            case 'gosan':
                this.component = PumpDrvnAnlyForGosan;
                break;
            case 'gunsan':
                this.component = PumpDrvnAnlyForGunsan;
                break;
            case 'buan':
                this.component = PumpDrvnAnlyForBuan;
                break;
            case 'sanseong':
                this.component = PumpDrvnAnlyForSanseong;
                break;
            case 'goryeong':
                this.component = PumpDrvnAnlyForGoryeong;
                break;
            case 'jain':
                this.component = MainDashBoard_jain;
                break;
            case 'unmun':
                this.component = PumpDrvnAnlyForUnmun;
                break;
            default:
        }

    }
}
