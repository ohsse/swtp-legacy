const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true
})





// 스프링부트와 연결하기 위해 
const path = require('path')

module.exports = {


  // outputDir :"../SMARTEMSBACKEND/src/main/resources/static",

  configureWebpack: {
    resolve: {
      alias: {
        '@env': path.resolve(__dirname, `src/.env.development`),
      },
    },
  },


  transpileDependencies: ['quasar'],


  devServer: {
    client: {
      overlay: false
    },

    // $apiURL/$pythonURL 이 '/ems-api', '/epa' 상대경로라서 컨테이너 배포에서는 프런트를
    // 서빙하는 nginx(default.conf)가 프록시한다. npm run serve 에는 그 nginx 가 없으므로
    // 개발 서버가 같은 역할을 대신한다. 두 곳의 경로 접두사와 대상 포트는 반드시 일치해야 한다.
    //
    // 대상이 localhost 인 이유: npm run serve 는 도커 밖에서 도니까 서비스명 DNS 가 없다.
    // compose 의 ports: 왼쪽(호스트 포트)을 봐야 한다 — legacy 스택 9000/23002,
    // 군산 로컬 스택(docker-compose.gunsan-dev.yml)은 9001/23003 으로 시프트돼 있다.
    proxy: {
      '/ems-api': {
        target: 'http://localhost:9000',
        changeOrigin: true,
        pathRewrite: { '^/ems-api': '' }
      },
      '/epa': {
        target: 'http://localhost:23002',
        changeOrigin: true,
        pathRewrite: { '^/epa': '' }
      }
    }
  }
};

