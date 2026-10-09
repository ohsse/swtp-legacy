import axios from 'axios';
// import store from "@/components/store/index";
// import { setInterceptors } from "./common/interceptors";

// 엑시오스 초기화 함수
const instance = axios.create({
    // baseURL: ""
    baseURL: 'http://localhost:4040/',
    headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods':
            'GET, POST, PATCH, PUT, DELETE, OPTIONS',
    },
});
// 예약 정보 조회
const reservation = (id) => {
    // const list = instance.get("/static/login.json");
    const list = instance.get('/api/v1/genesis/' + id);
    return list;
};
export { reservation };
