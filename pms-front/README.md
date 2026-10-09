# smartPMS

![환경부](src/assets/evironment.png)![k-water](src/assets/kwater.png)

---

사람이 분석 판단하여 운영하는 정수장을 빅데이터 기반의 인공지능 기술을 활용, 자율운영, 에너지관리, 설비관리 및 지능형 안정이 융합된 미래형 정수장 구축
고장감지 및 고장원인에 대한 취득, 분석을 통해 분석
데이터를 분석 운영하는 예지보전 시스템을 구축한다.

---

## Project setup

```
npm install
```

### Compiles and hot-reloads for development

```
npm run serve
```

### Compiles and minifies for production

```
npm run build
```

### Lints and fixes files

```
npm run lint
```

### Customize configuration

See [Configuration Reference](https://cli.vuejs.org/config/).

### Version

```
node -v : 18.12.1
npm -v : 9.6.7
@vue/cli 5.0.8
추가 버전 확인이 필요한경우 package.json 에서 dependencies 정보 확인하기
```

### 정수장별로 전환 하는 방법

```
index.js src/store 파일
state 안에 area 만 일치하는 정수장에 맞게 변경한다
( 현재 고산, 구미, 학야 중에 일치하는것만 주석풀어놓음 만약 학야 정수장이면 학야 주석 풀고 나머지 주석하기)

index.js src/api 파일 axios baseURL도 정수장에 맞게 변경해준다.
```

### 자주 발생하는 문제 또는 해결방안

1. EChart 라이브러리로 차트를 생성할때 DOM 생성문제때문에 'ParentNode'를 찾을수 없다는 오류 나오 발생한다면
   vue 에서 차트를 생성할때 라이브사이클을 확인하면서 순차적으로 차트를 그릴수있도록 수정해야합니다.
2. 데이터가 없는 경우에는 백엔드 담당 직원과 데이터 유무 확인하고 추후 어떻게 대처할지 논의할 사항

### 대표적으로 사용중인 라이브러리

1. ag-grid-vue3
2. echarts
3. vue3-datepicker
4. vue-router
5. vuex
   package.json 파일에 버전 적혀있으므로 참고바랍니다.
