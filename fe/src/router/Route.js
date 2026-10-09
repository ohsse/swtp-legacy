import MainDashBoard_gosan from "@/views/DashBoard/MainDashBoard_gosan.vue";
import MainDashBoard_haepyeong from "@/views/DashBoard/MainDashBoard_haepyeong.vue";
import MainDashBoard_gunsan from "@/views/DashBoard/MainDashBoard_gunsan.vue";
import MainDashBoard_buan from "@/views/DashBoard/MainDashBoard_buan.vue";
import MainDashBoard_sanseong from "@/views/DashBoard/MainDashBoard_sanseong.vue";
import MainDashBoard_goryeong from "@/views/DashBoard/MainDashBoard_goryeong.vue";
import MainDashBoard_hakya from "@/views/DashBoard/MainDashBoard_hakya.vue";
import MainDashBoard_jain from "@/views/DashBoard/MainDashBoard_jain.vue";
import MainDashBoard_unmun from "@/views/DashBoard/MainDashBoard_unmun.vue";
import MainDashBoard_gumi from "@/views/DashBoard/MainDashBoard_gumi.vue";

export default class Route {
    constructor(area) {
        this.path = '/:token?';
        this.name = 'Dashboard';
        switch (area) {
            case 'gumi':
                this.component = MainDashBoard_gumi;
                break;
            case 'gosan':
                this.component = MainDashBoard_gosan;
                break;
            case 'haepyeong':
                this.component = MainDashBoard_haepyeong;
                break;
            case 'gunsan':
                this.component = MainDashBoard_gunsan;
                break;
            case 'buan':
                this.component = MainDashBoard_buan;
                break;
            case 'sanseong':
                this.component = MainDashBoard_sanseong;
                break;
            case 'goryeong':
                this.component = MainDashBoard_goryeong;
                break;
            case 'hakya':
                this.component = MainDashBoard_hakya;
                break;
            case 'jain':
                this.component = MainDashBoard_jain;
                break;
            case 'unmun':
                this.component = MainDashBoard_unmun;
                break;
            default:
                this.component = MainDashBoard_gosan;
        }

    }
}
