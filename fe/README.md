# smartEMS

![환경부](src/assets/evironment.png)![k-water](src/assets/kwater.png)

***

사업장의 최적 에너지 관리로써 전력비 절감, 용수공급 안정이 최우선 목표 <br>
최적 펌프 제어 및 전력 피크 관리를 위한 데이터 분석 및 학습 알고리즘 적용

***

## Project setup

```shell
npm install
npm install @vueform/multiselect
```

### Compiles and hot-reloads for development

```shell
npm run serve
```

### Compiles and minifies for production

```shell
npm run build
```

### Lints and fixes files

```shell
npm run lint
```

### Version
```
node -v : 18.12.1
npm -v : 9.6.7
@vue/cli 5.0.8
추가 버전 확인이 필요한경우 package.json 에서 dependencies 정보 확인하기
```

### 정수장별로 전환 하는 방법 
```
main.js
라인 49 부터 58번줄 까지 고산부터 운문 까지 소스 구현 
해당되는 지역만 주석 해제하고 나머지는 주석걸어놓으면 해당되는 정수장 메인화면 나옴 
```

### 대표적으로 사용중인 라이브러리 
1. ag-grid-vue3
2. echarts
3. vue3-datepicker
4. vue-router
5. vuex
package.json 파일에 버전 적혀있으므로 참고바랍니다. 