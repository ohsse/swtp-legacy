# swtp-legacy — 정수장 에너지·설비 관리 시스템 (1세대)

여러 지자체 정수장에 배포·운영한 **EMS(에너지 관리)·PMS(펌프 설비 관리)** 시스템과, 그 위에서 동작하는 AI·수리해석 모듈의 원본입니다.
이 시스템을 운영하며 쌓은 경험으로 다시 설계한 것이 [swtp-monol](https://github.com/ohsse/swtp-monol)과 [swtp-platform](https://github.com/ohsse/swtp-platform)입니다.

## 구성

| 디렉토리 | 내용 | 기술 |
|---|---|---|
| `be` | EMS 백엔드: 전력·요금·펌프 운전 데이터, Kafka 기반 SCADA 수집, 펌프 제어 명령 | Spring Boot 2.7, Java 11 |
| `fe` | EMS 프론트엔드: 대시보드, 지도(OpenLayers), 차트 | Vue 3, Vuex, ECharts, OpenLayers |
| `pms-back` · `pms-front` | PMS: 펌프·모터 진동 진단 화면과 API | Spring Boot 2.5 / Vue 3, ECharts |
| `al` | AI 모듈: 전력 수요 예측, 펌프 조합 최적화(GA + EPANET 수리해석), 요금 계산 | Python, TensorFlow/Keras, scikit-learn, WNTR |
| `ems_gu_predict` | 시계열 수요 예측 모델 학습·추론 파이프라인 | Python, PyTorch |
| `epa` | EPANET 수리해석 API 서버 | Python, Flask, WNTR |
| `inpEditor` | 관망 모델(INP) 웹 편집기: 편집 API, 지도 기반 편집 UI, 조도계수 GA 최적화 | Spring Boot 4.1 · Java 21 / React 19 · Vite · OpenLayers / Python |
| `docs` | 분석·작업 문서 | — |

## 지자체별 멀티 테넌트 운영

하나의 코드베이스를 `application-{지자체코드}.properties` 프로파일로 나눠 10여 개 정수장에 배포했습니다(`be/src/main/resources/`).
이때 겪은 **"설정만으로는 흡수되지 않는 현장별 차이"**가 다음 세대 설계(`resources-env` 분리, compose 프로파일 기반 선택 배포)의 출발점입니다.

## 공개 버전에서 바뀐 점

현장 운영 시스템이라 다음을 제거하거나 치환했습니다.

| 항목 | 처리 |
|---|---|
| DB 접속정보(정수장별 호스트·계정·비밀번호), JWT 키 | `CHANGE_ME`, `localhost`, 환경변수로 치환 |
| 실제 정수장 관망 모델(`.inp`)과 그것에서 파생된 샘플 | 삭제 (WNTR 라이브러리의 공개 테스트 관망만 유지) |
| 현장 SCADA 태그 목록, 학습된 모델 가중치·스케일러(`.pkl`, `.pt` 등), 예측 결과물 | 삭제 (학습·추론 **코드는 유지**) |
| 사업 문서, 지도 타일, 상용 DB 설치본, 설치 파일, 로그 | 삭제 |

그래서 이 저장소는 **그대로 실행되지 않습니다.** 코드 구조와 구현 방식을 보여주기 위한 공개본입니다.
