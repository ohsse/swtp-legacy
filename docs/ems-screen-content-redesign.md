# 스마트EMS 화면 컨텐츠 재구성 — 현황 진단과 설계안

> **성격**: 착수 전 설계 문서다. 현행 화면이 무엇을 보여주는지, 어디가 겹치고 어디가 뜻이 흐린지를
> 코드와 SQL 근거(`파일:라인`)로 적고, 그 위에 새 정보구조(IA)·지표 사전·대시보드 안을 제시한다.
> **코드 변경은 포함하지 않는다.** 숨김 화면도 지우지 않는다(흡수 후보로만 표기).
> **조사 기준**: `master` / `20c7513` 시점 소스. 경로는 `fe/src/`, `be/src/main/resources/sqlmapper/mysql/` 기준.
> **결정된 전제**: 1차 대상은 군산이되 다른 현장 분기가 깨지지 않는 공통 구조. 주 사용자는 현장 운영자.
> **관련 문서**: `docs/tenant-bundle-guide.md`(현장별 빌드, 하드코딩 주소 목록 §915-928),
> `docs/ai-mode-pump-control-flow.md`(AI 모드 0/1/2 의미).

---

## 1. 결론 요약

1. 메뉴에서 갈 수 있는 화면 **14개**, 라우트만 있고 메뉴가 주석 처리된 화면 **7개**, 어디서도 import 하지 않는 뷰 파일 10여 개가 있다.
2. 같은 데이터를 다른 그림으로 다시 보여주는 **화면 쌍이 5개**다. 송수펌프 쪽 3쌍, 전력피크 쪽 1쌍(차트 3벌), 대시보드 맵과 설비별 사용량 1쌍.
3. 화면이 서로 다른 숫자를 보여주는 근본 원인은 프런트가 아니라 **화면마다 따로 있는 SQL**이다. "전체 전력량"만 출처가 6종, 피크 정의 3종, 순시전력 2종, CO2 2종, 계절 2종이다.
4. 뜻이 흐린 지점은 세 부류다. ① kW/kWh 라벨 뒤바뀜 ② 물리적으로 의미 없는 집계(펌프 압력 합산, 수위 합 도넛) ③ 가짜·무언 대체 값(일일보고서 예상/발생전력 = 사용량 ×0.98/×1.02, 예측이 0이면 실측으로 바꿔 표시).
5. 제안: 화면을 **운영자의 질문 단위**로 다시 묶어 21개 → **12개(운영 9 + 설정 3)**. 그 전에 **지표 사전(한 지표 = 한 정의 = 한 출처)**을 세운다. 대시보드는 현장별 10벌 복붙을 설정 파일 기반 렌더러 1개로 바꾸되 맵만 현장 고유로 남긴다.
6. 실행은 4단계로 쪼개 각각 별도 착수한다. 이 문서는 그 순서와 리스크까지만 적는다.

---

## 2. 현행 화면 인벤토리

### 2.1 현장 결정과 메뉴 분기

- 현장은 빌드 시점 `main.js:88`의 `$area = 'gunsan'` 한 줄로 정해진다. 다른 현장은 주석(`:85-94`). `configurl.json`은 어디서도 쓰이지 않는다.
- 메뉴 분기 플래그 4종은 `views/Common/sub/EmsSubMenu.vue:125-151`에 있다.

| 플래그 | true 조건 | 영향 |
|---|---|---|
| `songsu` | gumi·haepyeong·hakya·jain 이 **아닐** 때 | 송수펌프 제어 메뉴, 설정 > 송수펌프 운영, 전력피크 3depth |
| `otherCompany` | gumi | 펌프 메뉴 전체를 외부 서버 `http://<internal-host>:11111/`로 보냄(`:157-159`) |
| `sanseong` | sanseong | 운전현황 분석·제어 이력 숨김 |
| `epa` | gosan·gunsan | 관망해석 메뉴 |

- `$area ==` 비교는 뷰 24개 파일에 50회 흩어져 있다.
- 1차 메뉴 "메인"과 "자율"은 둘 다 외부 자율운영 포털로 나간다(`views/Common/MainMenuContainerMenu.vue:4-5`). EMS 대시보드로 가려면 헤더 타이틀 또는 스마트EMS > 대시보드를 눌러야 한다.

### 2.2 메뉴 트리 (군산 기준)

| 1차 | 2차 | 3차 | 라우트 | 보여주는 것 | 주요 API |
|---|---|---|---|---|---|
| 대시보드 | | | `/` | §2.3 | §2.3 |
| AI 분석 | 송수펌프 제어 | 송수펌프 제어 분석 | `/EMSPumpControl` | 그룹별 관압·유량 원형 카드(운영현황/분석 결과), 펌프 ON/OFF·Hz, 주요인자(배수지 유입·개도·수위), 최소요구관압, AI 운전모드 변경 | `/ai/selectValve`, `selectPumpStatus`, `pumpSelect`, `selectPumpPrdctOnOffStatus`, `selectAiStatus` |
| | | 운전현황 분석 | `/PumpDrvnAnly` | 현장별 전용 7종(`router/drvnRoute.js:13-36`). 펌프 효율·성능곡선 | 현장별 |
| | | 성능곡선관리 | 외부 inpEditor | | |
| | | 송수펌프 제어 가동이력 | `/PumpHistory` | 펌프 카드(가동률, 정격), PWI 영역차트, SPI 선차트, PMB 히트맵, 엑셀 | `/es/selectPumpPerformList`, `/ai/selectPumpList` |
| | | 송수펌프 제어 이력 | `/PumpControlHistory` | AI 모드별 건수 막대·표, 제어 이력 표, 군산은 판단 이력 탭 | `/ai/selectPumpCtrHistoryList`, `getAiModeCount`, `/ai/ctrl/history` |
| | 관망해석 | 모니터링 | `/EpaAnalysisMonitoring` | 지도, 유량·압력 적합/적정/미흡 건수, 계측 vs 해석 표·차트 | `$pythonURL/api/web/monitoring` |
| | | 시뮬레이션 | `/EpaAnalysisSimulation` | 토출유량·배수지 수요·펌프 Hz 입력 → 해석 결과 표 | `$pythonURL/api/simulations/si` |
| | | 관망최적화 | 외부 inpEditor | | |
| | 전력피크 | 전력피크 분석 | `/PowerPeakAnalysis` | 피크치 설정, 총 순시·목표·요금적용 피크 카드, 주요인자 표, 그룹별 전력량 예측, 발생 vs 예상 전력 차트 | `/ai/selectPeakControl`, `selectPwrPrdctList`, `/st/selectPeakGoal`, `insertPeakGoal` |
| 에너지 사용 현황 | 시설별 사용량 | | `/ZoneUse` | 시설 카드(순시·전력량·최대), 합계 막대, 분포 도넛, 트렌드 | `/es/selectZoneUseList(_sum)`, `sisul_sunsi`, `sunsiChart` |
| | 설비별 사용량 | | `/FacUse` | 시설→설비 목록, 설비 트렌드, 설비별 평균 막대, 분포 도넛, 순시 | `/es/selectFac`, `selectFacUseList(_sum)`, `selectFacSunsi` |
| | 사용량 트렌드 | | `/UseTrand` | 전력 사용량 선차트, 최대 피크 막대(12개월), 금일/금월/금년 부하구분 표 | `/ai/selectUseTrandList`, `selectUseTrandRangeCostList` |
| 에너지 절감 관리 | 최적요금제 분석 | | `/CostAnaylsis` | 월 사용량·부하구분, 시간대별 단가, 전체·기본·부하별 요금 | `/ai/selectRtRate`, `/es/selectRateInfo` |
| | 절감목표 달성 현황 | | `/ReductionTargetStatus` | 월 카드 12개(목표/사용/%), 금월 게이지, CO2, 월별 막대 | `/st/getUsageData`, `getGoalData` |
| 설정 | 송수펌프 운영 | | `/SongsuPumpOperation` | 조합 목록·적용 결과·조합 설정 (전 현장 `SongsuPumpOperationGosan.vue`, `router/index.js:334-343`) | `/dr/*` |
| | 전력요금제 | | `/EletricityPlan` | 월별 계절, 요금 4종, 24시간 부하구분 | `/st/selectMonthSeason`, `setRateCost`, `setSeasonLoad` |
| | 절감목표 | | `/ReductionTarget` | 연도·월별 목표 입력 | `/st/selectGetSetting`, `updateGoal` |

**라우트는 있으나 메뉴가 주석 처리된 화면 7개** (`EmsSubMenu.vue:12-15, 24-25, 63-64, 86, 93, 96, 105, 107-110`)

| 라우트 | 파일 | 내용 요약 |
|---|---|---|
| `/PumpControlDetailed` | `views/AiAnalysis/SongsuPumpCtr/PumpControlDetailed.vue` | 그룹별 예상 전력·관압·유량 vs 실측, 동작하지 않는 AI 토글(`PumpDetailed/AiOperation.vue:9-31`) |
| `/PumpControlTrand` | `…/PumpControlTrand.vue` | 배수지 태그 영역차트, 펌프 토출압력, PMB 히트맵, 순시값 표 |
| `/MajorDrainage` | `…/MajorDrainage.vue` | 배수지 수위 추이, 수위 합 도넛, 수위 카드 |
| `/PowerPeakDetail` | `components/ComponentCommon/PowerPeakDetail.vue` | 발생 vs 예상 전력 큰 차트 + 시각별 주요 소비 설비 표, 15분마다 `location.reload()` |
| `/TargetStategyPeak` | 위와 같은 컴포넌트 | 제목과 피크치 입력칸만 다름(`:78-88`) |
| `/TagInfo` | `views/Setting/TagInfo.vue` | 태그 조회·사용여부 저장 |
| `/DailyReport` | `views/Report/DailyReport.vue` | 전력 사용량·시설별·펌프 가동·배수지 수위·시간대별 표 7종, 엑셀 |

### 2.3 대시보드 (현장별 10벌)

| 유형 | 현장 | 구성 |
|---|---|---|
| A. 우측 펌프 패널형 | gosan, gunsan, buan, goryeong, unmun | 좌상단 롤링 카드 3종 + 중앙 3D 맵 + 우측 펌프 목록·피크 차트 |
| B. 하단 피크형 | gumi, haepyeong, hakya, jain, sanseong | 롤링 카드 3종 + 맵 + 하단 피크 차트 |

- `router/Route.js:13-47`의 switch 로 현장별 `MainDashBoard_*.vue`를 고른다. default 는 고산.
- 10벌의 차이는 레이아웃 좌표·배경·import 경로뿐이고, 하위 `RotationContents.vue`는 현장 간 0~4줄 차이. 진짜 다른 것은 `*/MapContents.vue`(3D 맵)뿐이다.
- 모든 대시보드가 같은 API 를 부른다: `/es/selectNowElec`, `selectNowPeak`, `selectYMD`, `baseElec`, `rstSavingTargetSum`, `/ai/selectPwrPrdctList`, `selectPumpStatus`, `selectAiStatus`, `/st/selectPeakGoal`.

군산(A형) 위젯:

| 위젯 | 파일 | 내용 | 갱신 |
|---|---|---|---|
| 소비 현황 | `views/DashBoard/gunsan/RotationContents.vue:18, 91-103` | 큰 값 = 순시 `nowPwi`(kW). 롤링 = 금일/금월/금년/전일 사용량(kWh)과 "목표대비 %" | 1분 |
| 절감 현황 | `:19, 106-111` | 금일/금월/금년/전일 절감량 kWh. 큰 값은 0으로 고정돼 `v-if` 로 숨겨짐. 단위 선언은 'kW' | 1분 |
| 탄소절감 | `:20-25, 115-120` | 같은 4종 CO2 kg | 1분 |
| 3D 맵 | `views/DashBoard/gunsan/MapContents.vue` | 건물별 전력 비중 % 큐브. 클릭 → `/FacUse?selected=` 전체 리로드 | 1회 |
| 펌프 목록 | `views/DashBoard/DashBoard/RightContents/RightContents.vue` | 그룹별 AI 모드 토글(AI/AI 추천/AI 분석), 펌프 ON/OFF·자동/반자동 | ON/OFF 1회, AI 상태 1분 |
| 피크 관리 | `…/RightContents/BottomPeak.vue` | 당일 "발생 전력" vs "예상 전력" 영역차트 + 목표 피크선 | 1회 |

### 2.4 쓰이지 않는 파일 (삭제가 아니라 기록 목적)

- 라우트 없음: `views/DashBoard/MainDashBoard.vue`, `MainDashBoard_vertical.vue`
- import 없음: `DashBoard/NowElec.vue`, `PumpState.vue`, `CostLeft.vue`, `TopPump*.vue`, `MiddleMajor.vue`; `SongsuPumpCtr/PumpDetailed/DetailedCenter.vue`('평택'·'송산' 하드코딩), `PumpControlAnly/PumpControlRigBot.vue`, `PumpSmallComponents/PumpAreaH35.vue`·`PumpAreaH4.vue`·`DotCircleForPipe.vue`, `PumpDrvnAnly/Gosan/PumpDrvnAnlyForGosan_OLD.vue`, `PumpDrvnAnly/Gunsan/CtrlCmdLatestCard.vue`, `components/Map/MapTest.vue`, `components/PwrPeak/PowerPeakAnalysus_rightGrid.vue`(0바이트), `components/Chart/ScatterChartClass.js`, `store/DashBoardStore.js`(`<internal-host>` 하드코딩, dispatch 하는 곳이 미사용 뷰 하나)
- 라우트 버그: `router/drvnRoute.js:29-30` jain 의 운전현황 분석이 `MainDashBoard_jain`으로 연결됨. gumi·haepyeong·hakya 는 default 가 비어 component 가 없음.

---

## 3. 문제 진단

### 3.1 화면 간 중복

**(1) 송수펌프 6화면 × 지표**

| 지표 | 제어 분석 | 세부현황(숨김) | 제어 트렌드(숨김) | 가동이력 | 제어 이력 | 주요 배수지(숨김) |
|---|---|---|---|---|---|---|
| 시점 | 현재 | 현재 | 기간 | 기간 | 기간 | 하루 |
| 펌프 ON/OFF | ○ 실측+예측 혼재 | ○ | 히트맵 | 히트맵 | | |
| 관압 | 합산 kg/cm²(실측·예측) | 실측 합·예측 합 | PRI 추이 "m" | | | |
| 유량 | 합 m³/h | "m³" | 배수지 태그 "m" | | | |
| 전력 | | 실측·예측 kW | | PWI "kWh" | | |
| Hz | ○ | ○ | | SPI | 판단 Hz(군산) | |
| 배수지 수위·유입·개도 | 주요인자 | 오른쪽 열 | 영역차트·순시표 | | | 추이·도넛·카드 |
| 최소요구관압·분기점 | ○ | ○ | | | | |
| AI 모드·제어 | 모드 변경 | 미동작 토글 | | | 이력·건수 | |
| 핵심 API | selectPumpStatus, pumpSelect | selectSongsuTagValueList, pumpSelect | selectPumpPerformList | selectPumpPerformList | selectPumpCtrHistoryList | selectTankDataHourList |

- 제어 분석 ≈ 세부현황: 둘 다 현재 그룹별 관압·유량을 예측/실측으로 나란히 둔다. 차이는 세부현황에 전력이 있고 AI 토글이 동작하지 않는 것뿐.
- 제어 트렌드 ≈ 가동이력: 같은 API(`/es/selectPumpPerformList`, `enerSpend_mssql.xml:197`)와 같은 PMB 히트맵.
- 주요 배수지 ⊂ 제어 트렌드.
- 제어 이력만 성격이 다르다(제어 명령 이력).

**(2) 전력피크 차트 3벌**

| 요소 | 전력피크 분석 | 피크 세부현황(숨김) | 대시보드 피크 관리 |
|---|---|---|---|
| 발생 vs 예상 전력 차트 | ○ 기준선 2(목표, 요금적용) | ○ 기준선 1 | ○ 기준선 1 |
| 데이터 함수 | `components/Func/PowerPeakFunc.js` | 같음 | `BottomPeak.vue`(같은 로직 복제) |
| 현재 순시 출처 | `/ai/selectPeakControl` | | `/es/selectNowElec` |
| 고유 컨텐츠 | 피크 예상 시각, 그룹별 전력량 예측 | 시각별 주요 소비 설비 표 | 없음 |

- 전력피크 분석 안에서도 "총 순시 전력"과 "요금 적용 전력 피크"가 왼쪽 카드와 "주요인자" 표에 두 번 나온다(`PowerPeakAnalysis/PowerPeakAnalysis_totalUsage.vue:12-24`).

**(3) 전력량·부하구분이 나오는 곳**

| 지표 | 시설별 | 설비별 | 사용량 트렌드 | 최적요금제 | 절감목표 | 일일보고서(숨김) | 대시보드 |
|---|---|---|---|---|---|---|---|
| 전체 전력량 kWh | `총전력량` 행 | | `selectPwrSumList`(오늘/월/년 고정) | `TB_RT_RATE_RST`(AI 결과) | `getUsageData` | `selectReport_kwh` | `selectYMD` |
| 시설별 전력량 | 카드·막대·도넛 3중 | | | | | 시설별 열 | 맵 % |
| 경/중/최대부하 | | | ○ | ○ | | ○ | |
| 순시전력 kW | 카드·총 순시·모달·트렌드 | 순시 전력 | "전력 사용량" 차트 | | | type=6 | 큰 값 |

- 시설별 사용량 한 화면 안에서도 같은 합계(data2)를 카드·합계 막대·분포 도넛 세 번 보여준다. 설비별 사용량도 같은 평균값을 막대·도넛 두 번.
- 대시보드 맵의 % 큐브는 클릭하면 설비별 사용량으로 가므로 그 화면의 축약본이다.

### 3.2 지표 정의 불일치

| 지표 | 정의 1 | 정의 2 | 정의 3 |
|---|---|---|---|
| 전체 전력량 | `enerSpend_mssql.xml:386 selectYMD`(대시보드) | `ai_mssql.xml:1972 selectPwrSumList`(트렌드) | `setting_mssql.xml:555 selectReport_kwh`(보고서), `getUsageData`(절감목표), `TB_RT_RATE_RST`(요금제), `selectZoneUseList_sum`(시설별) |
| 부하구분 사용량 | 트렌드: **이번 달 단가 하나로 연간을 분류**(`ai_mssql.xml:1997`, `rri.RATE_IDX='1' and rri.MNTH = month(CURDATE())`) | 보고서: 각 월 단가로 분류(`setting_mssql.xml:583`) | 요금제: AI 결과 테이블 |
| 피크 | 시설별: 시설 순시 합의 시간당 최대 | 트렌드: 최근 12개월 월별 최대 순시(`ai_mssql.xml:1940-1969`) | 보고서: PWQ(kWh) 최대를 "전력 피크값(kW)"으로 표기(`setting_mssql.xml:829-836`) |
| 순시전력 | 대시보드 `selectNowElec`(`enerSpend_mssql.xml:365`) | 전력피크 `selectPeakControl`(`ai_mssql.xml:2162`) | 시설별 `sisul_sunsi` |
| CO2 절감 | 절감목표: (목표 − 사용) × 0.4663, kg, 프런트 계산(`ReductionTarget.vue:109-110`) | 보고서·대시보드: `TB_RST_SAVINGS_TARGET`, tCO2/kg | |
| 계절 | 최적요금제: 월로 하드코딩(`CostAnaylsis.vue:77-85`) | 설정: DB `selectMonthSeason`(`setting_mssql.xml:857`) | |
| 부하 용어 | '중부하'(트렌드, 요금제 시간대 설정) | '중간부하'(최적요금제, 보고서, 요금 입력) | |

### 3.3 뜻이 흐리거나 틀린 값

**단위**
- 순시전력(PWI, kW)을 'kWh'로 표기: `UseTrand/UseTrand_topLeft.vue:23`, `ZoneUse/ZoneUse_bottomRig.vue:71`, `UseTrand_topRig.vue:35`('kwh'), `PumpHistory.vue:214`, 피크 차트 전부.
- 반대로 kWh 최대를 'kW'로: 일일보고서 전력 피크값.
- 대시보드 "전력절감" 단위 선언 'kW', 내용은 kWh(`RotationContents.vue:19`).
- 관압 단위 3종: kg/cm²(제어 분석), "m"(제어 트렌드 `:156`), kgf/cm²(관망해석). 유량 m³/h 와 m³ 혼용(`PumpDetailed/DetailedPumpBox.vue:55`).
- 단위가 아예 없는 곳: 세부현황 열 머리(유입유량/개도율/수위/유출유량), 정격양정, 운영대수, 시뮬레이션 수요량 모달, 지도 팝업(`components/Map/MapStatusLayer.vue`, 압력을 정수로 반올림 `:104-106`).
- 수위 트렌드 Y축이 'kWh'(`Report/DailyReport_WaterLevelTrend.vue:50`).

**물리적으로 의미 없는 집계**
- 펌프별 압력을 **합산**해 그룹 관압으로 표시(`PumpControlAnly/PumpControlLeft.vue:127-159`, `PumpControlDetailed.vue:249`).
- 배수지 수위 합을 도넛 비율로(`MajorDrainage.vue:147-159`).
- 설비별 사용량 `_sum` API 는 실제로 AVG(`enerSpend_mssql.xml:162-170`). 평균으로 그린 "분포" 도넛의 비중은 뜻이 없다.
- "개도율 %"에 밸브 열림 신호(0/1)를 넣음(`PumpControl.vue:360`).

**가짜·무언 대체**
- 일일보고서 "예상전력"·"발생전력" = 사용량 × 0.98 / × 1.02(`setting_mssql.xml:803-804`). 측정값이 아니다.
- 제어 분석 "분석 결과"는 예측 합이 0이면 실측으로 바꿔 표시하고 라벨이 같다(`PumpControlAnly/PumpControlRig.vue:187-214`). "운영현황"과 생김새도 같아 실측/예측 구분이 안 된다.
- 세부현황 "예상"은 `PRDCT_TIME_DIFF==1440` 행만 합산(`PumpControlDetailed.vue:188`)인데 기준 시각이 화면에 없다. 제어 분석은 구분 없이 모든 행을 더해 둘의 계산이 다르다.
- 관망해석 모니터링 초기 더미 건수와 고정 시각 "2025-10-21 18:31:00"(`EpaAnalysisMonitoring.vue:61-80`), 시뮬레이션 결과 표 기본 더미(`simulation/AnalysisResults.vue:59-70`).
- 동작하지 않는 AI 운영 토글(`PumpDetailed/AiOperation.vue:31`, "HMI 화면 작화 이후 작업 예정").

**기준 없는 비교**
- 대시보드 "목표대비 %"의 목표는 `selectNowPeak`의 월별 값을 일수로 나눈 것(`RotationContents.vue:57-63`). 이름은 peak 인데 사용량 목표로 쓴다.
- 절감목표 현황: 진행 중인 달 누계를 월 전체 목표와 비교(`ReductionTarget.vue:105-110`). 월초엔 늘 '달성'. % 가 높을수록 좋은지 나쁜지 기준선·색이 없다. 연도 선택 불가(`:65`).
- 세부현황 게이지 최대값 80 하드코딩(`PumpDetailed/DetailedPipe.vue:99`).
- "최소요구관압 기준 배수지"는 요구치 최대 배수지가 아니라 `TNK_GRP_IDX` 첫 번째(`PumpControl.vue:280-282`).
- 제어 이력 "AI 운영 현황 건수"가 무엇을 센 건지 정의 없음(`PumpControlHistory.vue:39-52`).
- 최적요금제 분석은 요금제를 비교하지 않는다. 선택 버튼이 주석 처리돼 항상 '선택I'(`Cost/CostAnaysis_right.vue:73-80`), "추천 요금제"는 정의만 있고 표시 안 됨(`CostAnaylsis.vue:30-33`).

**필터가 일부에만 먹음**
- 사용량 트렌드의 기간 필터는 좌상단 차트에만 적용. 피크 차트(12개월 고정)·하단 표(오늘/월/년 고정)는 그대로(`UseTrand.vue:107-125`). `/ai/peakMax` 는 백엔드에 없고 결과도 안 씀.

**저장 로직**
- 절감목표 설정은 고른 연도와 상관없이 올해로 저장(`setting_mssql.xml:369, 409` `date_format(NOW(),'%Y')`).
- 일일보고서 "가동 트렌드" URL 에 `}` 와 줄바꿈이 섞여 항상 빈 화면(`DailyReport.vue:173-175`).

---

## 4. 설계 원칙

| # | 원칙 | 적용 규칙 |
|---|---|---|
| P1 | **한 지표 = 한 정의 = 한 출처** | §5 지표 사전에 등록된 API/SQL 하나만 쓴다. 프런트에서 ×0.98 같은 가공 금지. 같은 지표가 두 화면에 나오면 같은 숫자여야 한다. |
| P2 | **실측 / 예측 / 해석 / 목표를 눈으로 구분** | 실선 = 실측(PWI/PWQ), 점선 = 예측, 음영 = 관망해석 결과, 수평선 = 목표. 예측이 없으면 "예측 없음"으로 비우고 실측으로 대체하지 않는다. 예측값 옆에 생성 시각을 쓴다. |
| P3 | **화면 하나 = 운영자 질문 하나** | 화면 제목이 질문의 답이 되게 한다. 두 질문이 섞이면 탭으로 나누거나 화면을 합친다. |
| P4 | **비교에는 항상 기준선과 판정** | % 만 띄우지 않는다. 목표 대비는 "경과 일수 비례 목표"와 비교하고 초과/여유를 색과 문구로 판정한다. |
| P5 | **현장 차이는 코드 분기가 아니라 설정** | `$area ==` 대신 `siteConfig.features.*`, `siteConfig.pumpGroups` 같은 데이터로 분기. 맵처럼 진짜 현장 고유인 것만 컴포넌트를 바꿔 끼운다. |

---

## 5. 지표 사전 (용어·단위 통일표)

| 지표명(표기) | 정의 | 단위 | 단일 출처(API → SQL) | 현재 어긋난 곳 |
|---|---|---|---|---|
| 전력량 | 선택 기간·선택 노드(전체/시설/설비)의 PWQ 적산 합 | kWh | **신설** `/es/selectEnergyUse(nodeType, nodeId, from, to, unit)`. 기준 SQL 은 `enerSpend_mssql.xml:5 selectZoneUseList` 계열 | §3.2 출처 6종 |
| 순시전력 | 최신 1건 PWI. 전체 = 같은 시각 시설 PWI 합 | kW | `/ai/selectPeakControl`(`ai_mssql.xml:2162`) | 대시보드 `selectNowElec`, 시설별 `sisul_sunsi`, kW→kWh 라벨 |
| 피크 | 15분 평균 PWI 의 기간 최대(요금 산정 기준과 동일) | kW | `/ai/peakSelect`(`ai_mssql.xml:1171`) 로 통일. 15분 평균 SQL 존재 여부는 **미확정** | 피크 정의 3종 |
| 목표 피크 | 운영자가 설정한 피크 상한 | kW | `/st/selectPeakGoal`(`setting_mssql.xml:848`) | `PowerPeakFunc.js` 기준선을 kWh 로 주석 |
| 부하구분 사용량 | 경/중/최대부하 시간대별 PWQ 합. 시간대·계절은 설정 화면 DB 값 | kWh(단가 미적용) | `selectEnergyUse(groupBy=load)` + `/st/selectRateSeason`, `selectMonthSeason` | 단가 적용 방식 3종, 계절 하드코딩, '중부하/중간부하' 혼용 |
| 전력요금 | 기본요금 + Σ(부하구분 kWh × 계절·요금제 단가) | 원 | `/ai/selectRtRate`(`ai_mssql.xml:1313`, 선택 I/II/III 전부) | 선택 I 고정, 트렌드 별도 계산 |
| 목표 대비 진척 | 누계 kWh ÷ (월 목표 × 경과일 / 월 일수) | % | `/st/getGoalData`(`setting_mssql.xml:157`) + `selectEnergyUse` | 월 전체 목표와 비교, 판정 없음 |
| 절감량 | 기준선 전력량 − 실측 전력량, `TB_RST_SAVINGS_TARGET` 값 그대로 | kWh, 원 | `/es/baseElec`(`enerSpend_mssql.xml:437`), `rstSavingTargetSum`(`:450`) | 프런트 재합산(`RotationContents.vue:73-81`)과 SQL 합계 혼재 |
| CO2 절감량 | 절감 kWh × 배출계수(설정값 1개) | tCO2, 소수 2자리 | `baseElec.savingCo2` 단일. 계수 저장 위치는 **미확정** | 정의·단위 2종(kg/t), 프런트 상수 0.4663 |
| 원단위 | 기간 전력량 ÷ 기간 송수량 | kWh/m³ | `selectEnergyUse` ÷ FRI 적산. 송수량 출처는 **미확정** | 일일보고서·송수펌프 운영에만 있고 정의 다름 |
| 관압 | 그룹 **대표 토출 압력 센서 1개**의 PRI 현재값 | 현장 태그 단위 그대로(라벨 명시) | `/ai/selectValve`(`ai_mssql.xml:2115`) 대표 태그만. 대표 센서 선정 기준 **미확정** | 펌프별 압력 합산 |
| 유량 | 그룹 토출 유량계 FRI 현재값 / 기간 적산 | m³/h, m³ | `/ai/selectValve`, `selectPumpPerformList`(`enerSpend_mssql.xml:197`) | m³/h·m³·"m" 혼용 |
| 수위 | 배수지별 수위, 하한/상한 설정값과 함께 | m | `/ai/selectTankDataHourList`(`ai_mssql.xml:1789`) | 합산·도넛 표시 |
| 예측 기준시각 | 예측 생성 시각과 예측 대상 구간 | 시각 | `selectPwrPrdctList`(`AiController.java:497`), `selectPumpPrdct`(`:127`) 응답에 생성 시각 노출 | 예측 0→실측 대체, 기준시각 미표기 |
| AI 모드 | 0 AI 제어 / 1 AI 추천 / 2 AI 분석 | 코드 → 라벨 고정 | `/ai/selectAiStatus`(`ai_mssql.xml:2734`) | "자동/반자동" 별도 라벨(`AutoPart.vue:3-4`), "건수" 정의 없음 → "추천 발생 건수"로 |

---

## 6. 새 정보구조(IA) 안

화면 수 **운영 9 + 설정 3 = 12개** (현재 14 + 숨김 7 = 21). 외부 링크(성능곡선관리, 관망최적화, 구미 외부 서버)는 메뉴 항목이 아니라 해당 화면 안의 버튼으로 내린다. 기존 라우트는 한 릴리스 동안 신규 라우트로 `redirect` 를 유지한다.

| 1차 | 2차 (라우트) | 답하는 질문 | 위젯 (지표 · 차트 · 단위 · 기간 · 기준선) | 재사용 API / 컴포넌트 | 흡수 후보 기존 화면 |
|---|---|---|---|---|---|
| 대시보드 | 대시보드 `/` | 지금 내가 손대야 할 게 있나? | §7 | §7 | `MainDashBoard_*` 10개 → 1개 |
| 펌프 운전 | 송수펌프 운전 `/pump/operation` | 지금 펌프를 어떻게 돌리고 있고, AI 는 무엇을 권하나? | ① 그룹별 펌프 카드: 가동(PMB)·Hz(SPI)·전력 kW, AI 모드 배지, 추천 대기 건수 ② 그룹 관압(대표 센서 1개)·유량 m³/h 게이지 ③ 배수지 수위 m + 하한/상한선 ④ 금일 24h 실측(실선) vs 예측(점선) kW, 현재 시각 수직선, 예측 생성 시각 표기 ⑤ 현재 조합 vs 추천 조합 비교 표 | `/ai/selectPumpStatus`, `selectValve`, `selectAiStatus`, `pumpSelect`/`pumpSelect_new`, `selectPumpPrdct`, `selectPumpPrdctOnOffStatus`, `/ai/ctrl/pending`, `selectTankList`, `selectTankDataHourList` / `Chart/AreaChart`, `ComponentCommon/AutoPart`, `OnOff`, `views/Common/MenuTab`, `AiMode` | 송수펌프 제어 분석, 제어 세부현황(숨김), 주요 배수지(숨김) |
| 펌프 운전 | 송수펌프 이력 `/pump/history` | 지난 기간 펌프를 어떻게 돌렸고, AI 추천을 얼마나 따랐나? | 탭A 가동이력: PMB 히트맵(펌프×시간), 가동시간 h, 기동횟수, 가동 중 평균 kW·m³/h, 기간(시/일/월). 탭B 제어·추천 이력: 추천 발생→승인/거부/자동실행 타임라인, 추천 이행률 %(분모 명시), 모드별 시간 비율. 엑셀 | `/es/selectPumpPerformList`, `/ai/selectPumpList`, `selectPumpCtrHistoryList`, `getAiModeCount`, `/ai/ctrl/history`, `/dr/pumpCombinationExcel` / `Chart/PlotlyHeatmapChart`, `ComponentCommon/CalendarBox`, `PumpControlHistory/ControlHistory_list`, `CtrlCmdHistory_list` | 가동이력, 제어 이력, 제어 트렌드(숨김) |
| 펌프 운전 | 운전효율 분석 `/PumpDrvnAnly` | 각 펌프 효율은 성능곡선 대비 어떤가? | 현장별 전용 화면 유지. 상단에 "성능곡선 편집" 외부 버튼(`openInpEditor`) | 기존 `drvnRoute.js` 분기 유지. jain 오매핑(`:29-30`)만 수정 | 메뉴 "성능곡선관리" 항목 → 버튼 |
| 펌프 운전 | 관망해석 `/epa` (gosan·gunsan) | 해석 모델이 계측과 맞는가? 이렇게 바꾸면 수압·수위가 어떻게 되나? | 탭A 모니터링: 지도 + 노드별 계측 vs 해석(실선/음영), 오차율 상위 N 표, 임계선. 결측은 "미흡"이 아니라 "계측 없음"으로. 탭B 시뮬레이션: 조건 입력 → 수압·수위·전력, 현재 운전 대비 차이. "관망최적화" 외부 버튼 | `$pythonURL/api/web/monitoring`, `monitoring/chart`, `nodes`, `tanks`, `simulration*`, `/api/simulations/si` / `components/Map/MapComponent`, 기존 `EpaAnalysis/monitoring/*`, `simulation/*` | 관망해석 모니터링, 시뮬레이션 (두 라우트 → 한 화면 두 탭) |
| 전력 | 피크 관리 `/power/peak` | 오늘 목표 피크를 넘길 위험이 있나? 넘긴 적이 있나? | ① 현재 순시 kW · 목표 피크 kW · 여유 kW/% (단일 출처) ② 금일 15분 kW 실측(실선)+예측(점선)+목표(수평선) ③ 월별 최대 kW 막대 12개월 + 목표선 ④ 초과 발생 일시·지속시간·당시 가동 펌프 표 ⑤ 시각별 주요 소비 설비 표 | `/ai/selectPeakControl`, `selectPwrPrdctList`, `peakSelect`, `/st/selectPeakGoal`, `/es/peakFac` / `Func/PowerPeakFunc.js`, `Chart/ChartLineClass`, `BarChartClass`, `ComponentCommon/InstantaneousData` | 전력피크 분석, 피크 세부현황(숨김), 목표 전력피크(숨김). 대시보드 피크 차트는 이 화면 위젯을 임베드 |
| 전력 | 사용량 분석 `/power/usage` | 어디서(시설→설비), 언제(시간대·부하구분), 얼마나(kWh) 쓰나? 전년·전월 대비는? | ① 좌측 트리: 정수장 → 시설 → 설비, 선택 시 우측 갱신 ② 선택 노드 기간 kWh + 전년동기/전월 대비 %(기준선) ③ 시계열 kWh 막대(시/일/월/년) ④ 부하구분 도넛(단가 미적용) ⑤ 자식 노드 Top-N 막대 ⑥ 현재 순시 kW(보조, 라벨 분리) | `/st/selectZone`, `/es/selectFac` + **신설** `selectEnergyUse` / `BarChartClass`, `DoughnutChart`, `CalendarBox`, `ZoneUse/ZoneUse_DataFlowComponent`, `FacUse/FacUse_topList` | 시설별 사용량, 설비별 사용량, 사용량 트렌드, 대시보드 맵 클릭 목적지 |
| 전력 | 요금제 비교 `/power/tariff` | 어느 요금제(선택 I/II/III)가 우리 패턴에 가장 유리한가? | ① 월 선택 → 3개 요금제 나란히: 기본·전력량·합계 원, 현재 요금제 표시 ② 최저 요금제 대비 차액 원/% ③ 부하구분 kWh × 단가 표(계절은 DB) ④ 연간 누적 비교 라인. 금액 천 단위 구분 | `/ai/selectRtRate`(3안 모두), `/es/selectRateInfo`, `/st/selectMonthSeason` / `Cost/CostAnaysis_list`, `TdRow` | 최적요금제 분석 (선택 I 고정 → 3안 비교로 의미 복원) |
| 전력 | 절감목표 달성 `/power/target` | 이번 달·올해 목표 대비 어디까지 왔고, AI 로 얼마나 아꼈나? | ① 금일/금월/금년 kWh vs 일수 비례 목표, 판정 색 ② 월별 사용 vs 목표 막대 12개월, 연도 선택 ③ 절감량 kWh·원·tCO2(단일 정의) 추이 ④ 일일 요약표(날짜·사용·목표·절감·피크 kW·가동 펌프) + 엑셀 | `/st/getGoalData`, `selectGetSetting`, `/es/selectYMD`, `baseElec`, `rstSavingTargetSum`, `/st/selectReport`, `/cm/download` / `ReductionTarget/MonthCard`, `Grid/ReportGrid` | 절감목표 달성 현황, 일일보고서(숨김; 가짜 예상/발생전력 제거 후 요약표로) |
| 설정 | 송수펌프 운영 `/SongsuPumpOperation` | (기존) | 기존 유지 | 기존 | — |
| 설정 | 전력요금제 `/EletricityPlan` | (기존) | 기존 유지. 계절·부하시간대의 **유일한 출처** | 기존 | — |
| 설정 | 목표 관리 `/ReductionTarget` | 월별 사용 목표와 피크 목표를 한 곳에서 | 연도별 월 kWh 목표 표(저장 연도 버그 수정) + 목표 피크 kW 입력 | `/st/updateGoal`, `insertPeakGoal`, `selectPeakGoal` | 절감목표 + 전력피크 분석의 피크치 입력(`PowerPeakAnalysis.vue:10-14`). 태그 정보(숨김)는 흡수처 없음(구미는 외부 서버에 별도) |

**현장 분기 보존 규칙 (현재 플래그 ↔ 설정)**

| 현재 플래그 (`EmsSubMenu.vue:125-151`) | 설정 키 | 동작 |
|---|---|---|
| `songsu=false` (gumi·haepyeong·hakya·jain) | `features.pumpControl=false` | "펌프 운전" 1차 메뉴 전체 숨김. 전력 4개 화면만 노출 |
| `epa=true` (gosan·gunsan) | `features.epa=true` | 관망해석 노출 |
| `sanseong=true` | `features.drvnAnalysis=false` | 운전효율 분석·제어 이력 탭 숨김 |
| `otherCompany=true` (gumi) | `features.externalPumpPortal=url` | 펌프 운전 메뉴를 외부 링크로 대체(현재 `goPump`) |

---

## 7. 대시보드 재구성 안

### 7.1 운영자 시선 우선순위

| 순위 | 질문 | 위젯 | 데이터 | 판정 기준선 |
|---|---|---|---|---|
| 1 | 지금 피크 위험한가? | 상단 좌: 현재 kW / 목표 kW / 여유 % 게이지 + 금일 15분 실측·예측·목표선 라인(피크 관리 화면 위젯 재사용) | `selectPeakControl`(현재·목표 둘 다), `selectPwrPrdctList` | 여유 10% 미만 경고. 예측선이 목표를 넘는 시각 표시 |
| 2 | 펌프는 AI 가 돌리고 있나, 내가 승인할 추천이 있나? | 상단 우: 그룹별 AI 모드 배지 + 긴급 플래그 + **추천 대기 N건** 버튼(→ 기존 `CtrlCmdApprove` 모달) + 펌프 ON/OFF 요약 | `selectAiStatus`, `/ai/ctrl/pending`, `selectPumpStatus` | 대기 1건 이상 강조. 모드 변경은 펌프 운전 화면에서만(대시보드 토글·`location.reload()` 제거) |
| 3 | 오늘·이달 사용이 목표 안인가? | 중단: 금일/금월/금년 3타일(kWh, 일수 비례 목표 대비 %, 전일/전월 동기 대비). 롤링 제거, 고정 노출. 절감 kWh·tCO2 는 보조 줄 | `selectYMD`, `getGoalData`, `baseElec` | 비례 목표 100% 초과 시 적색 |
| 4 | 배수지·관망에 이상이 있나? | 하단 좌: 배수지 수위 막대(하한/상한선). EPA 현장은 최근 해석 오차율 상위 3 | `selectTankDataHourList`, `$pythonURL/api/web/monitoring` | 수위 하한 근접, 오차율 임계 초과 |
| 5 | 어디서 전력을 많이 쓰나? | 하단 우: 현장 맵(건물별 kW 비율, 범례·분모 표기) — 현장 고유 컴포넌트. 클릭 → `/power/usage?zone=` (라우터 이동, 리로드 아님) | `selectWppPwrPercentList`, `getTop3` | — |

### 7.2 설정 기반 레이아웃 (10벌 → 1개)

- `fe/src/config/sites/<area>.js` + `index.js`(`$area` 로 선택). 내용:
  - `features`: pumpControl / epa / drvnAnalysis / externalPumpPortal
  - `pumpGroups`: 그룹 수·이름·표시 높이 (현재 `RightContents.vue` initData 의 현장별 if 문을 데이터로)
  - `dashboard.widgets`: 순서·표시 여부 (buan 의 피크 위젯 분리, B형 현장의 펌프 패널 없음 등)
  - `map.component`: 동적 import. 현장 고유 `MapContents` 만 유지
- `views/DashBoard/MainDashBoard.vue` 하나가 `siteConfig.dashboard.widgets` 를 돌며 `<component :is>` 로 렌더. `router/Route.js` 는 switch 없이 이 컴포넌트 하나.
- 공통 하위(`RotationContents`, `RightContents`, `BottomPeak`/`PeakBottomRig`)는 현장 디렉터리에서 `views/DashBoard/widgets/` 로 승격.
- 위젯마다 따로 거는 `setInterval`(1분·10분·1회 혼재)을 대시보드 단일 폴링으로 통일. 펌프 ON/OFF 와 AI 모드가 다른 시각의 값인 문제 해소.

---

## 8. 단계별 실행 순서 (이 문서에서는 착수하지 않음)

각 단계는 별도 착수 단위다. **1단계에서도 파일은 지우지 않는다**(숨김 화면 유지 결정).

### 1단계 — 메뉴·플래그 데이터화, 구 라우트 redirect 설계
- `views/Common/sub/EmsSubMenu.vue:125-151` 플래그 계산을 `siteConfig.features` 로 교체. 주석 처리된 메뉴 항목은 그대로 둔다.
- `router/index.js` 에 신규 라우트 추가 + 구 라우트 → 신규 `redirect` 매핑표. 숨김 라우트 7개는 유지.
- 버그 수정: `router/drvnRoute.js:29-30` jain 오매핑, gumi·haepyeong·hakya 의 빈 default.
- 리스크: 10개 현장 각각 `$area` 를 바꿔 빌드가 통과하는지 확인(동적 import 경로). `Dockerfile.gunsan:20-21` 의 sed 치환이 큰따옴표만 찾아 실제로는 치환되지 않는 점 함께 점검.

### 2단계 — 지표 사전 적용 (숫자의 단일화)
- 백엔드: `enerSpend_mssql.xml` 에 `selectEnergyUse` 신설(노드 타입·기간·단위·부하구분 파라미터). `ai_mssql.xml:1940-1969` 월별 피크를 15분 평균 PWI 최대로 정정하거나 `peakSelect` 로 대체. `selectRtRate` 가 3개 요금제를 모두 반환하는지 확인. `setting_mssql.xml:369, 409` 저장 연도 파라미터화. `:803-804` 가짜 예상/발생전력 제거.
- 프런트: `fe/src/util/metrics.js`(라벨·단위·포맷 상수) 신설 후 하드코딩 라벨 치환. `components/Func/PowerPeakFunc.js` 를 피크 데이터 단일 진입점으로. `CostAnaylsis.vue:77-85` 계절 → `selectMonthSeason`.
- 리스크: SQL 단일화로 숫자가 바뀌면 운영자가 "값이 달라졌다"고 느낀다. **변경 전후 비교표를 현장별로 한 달치 뽑아 공유**한다. 현장별 DB 차이(파일명은 `_mssql` 인데 `mysql` 폴더)를 각 현장 DB 에서 쿼리 검증.

### 3단계 — 화면 통합

| 신규 화면 | 기반으로 삼을 파일 | 흡수할 부품 |
|---|---|---|
| `/pump/operation` | `SongsuPumpCtr/PumpControl.vue` + `PumpControlAnly/*` | `PumpDetailed/DetailedPumpBox.vue`(예측/실측 비교 박스), `MajorDrainageComponents/WaterLevelCard.vue` |
| `/pump/history` | `PumpHistory.vue` + `PumpHistory/*` | `PumpControlHistory/ControlHistory_list.vue`·`CtrlCmdHistory_list.vue` 를 탭B 로, `PumpControlTrand/SelectBox.vue` |
| `/epa` | `EpaAnalysis/EpaAnalysisMonitoring.vue` | `EpaAnalysisSimulation.vue` 를 탭으로. 초기 더미값·고정 시각 제거, 표 행 클릭↔지도 연동 |
| `/power/peak` | `PwrPeak/PowerPeakAnalysis.vue` | `ComponentCommon/PowerPeakDetail.vue` 의 주요 소비 설비 표. 피크 입력(`:10-14`)은 설정으로 이동 |
| `/power/usage` | `EnergyUseStts/UseTrand.vue`(기간 UI) | `ZoneUse/ZoneUse_DataFlowComponent.vue`(계층), `FacUse/FacUse_topList.vue`(설비 목록) |
| `/power/tariff` | `EnergySavingMngmn/CostAnaylsis.vue` | `Cost/CostAnaysis_list.vue` 를 3열로, `CostAnaysis_right.vue:73-80` 선택 버튼 복원 |
| `/power/target` | `EnergySavingMngmn/ReductionTarget.vue` | `Report/DailyReport/DailyReport_PowerConsumption.vue`·`DailyReport_PumpOperationHistory.vue` 를 요약표로, `Grid/ReportGrid.vue` |

- 리스크: `PumpControl.vue:198-216` 현장별 API 조합(`pumpSelect` vs `pumpSelect_new`)이 다르다 → `siteConfig.pumpApiVariant` 로 데이터화하되 1차는 그대로 옮긴다. sanseong 은 제어 이력 탭 숨김. 고산은 펌프 순서 반전(`PumpControlLeft.vue:161`) 같은 현장 특례를 설정으로.
- 통합 후 구 화면 파일은 한 릴리스 동안 남겨 두고(redirect 로 도달 불가), 다음 릴리스에서 삭제 여부를 따로 결정한다.

### 4단계 — 대시보드
- `fe/src/config/sites/*.js` 10개 작성. `views/DashBoard/MainDashBoard.vue` 를 위젯 렌더러로 재작성, `router/Route.js` 단순화. `MainDashBoard_*.vue` 10개와 현장별 `RotationContents.vue` 는 3단계와 같은 방식으로 한 릴리스 보류 후 정리. `*/MapContents.vue` 는 `views/DashBoard/maps/<area>Map.vue` 로 이름만 바꿔 유지.
- `RightContents.vue` 의 현장별 그룹 수/높이 if 문 → `siteConfig.pumpGroups`.
- 리스크: gumi 대시보드만 400줄 차이 → gumi 는 별도 위젯 세트로 config 에 기술(코드 분기 아님). `App.vue` 의 전역 팝업(`AllAlarm` 1분, `OnOffAlarm` 10분, `CtrlCmdApprove` 30초)과 폴링 주기 정합 확인.

---

## 9. 대안과 채택하지 않은 이유

**대안: 화면 구조는 그대로 두고 라벨·단위·숨김 라우트만 정리(2단계만 수행)**

비용이 가장 적고 현장 분기 리스크도 없다. 그러나 "전체 전력량" 출처 6종·피크 정의 3종은 화면이 분리돼 있는 한 각 화면이 자기 SQL 을 계속 부르므로 숫자 불일치가 재발하고, 운영자는 여전히 "어느 화면의 숫자가 맞나"를 물어야 한다. 요금제 비교 부재, 목표 비례 비교 부재 같은 의미 문제도 화면 안의 위젯을 바꿔야 풀린다. 즉 P1 을 절반만, P3·P4 는 달성하지 못하므로 채택하지 않는다. 다만 2단계는 어느 안이든 선행돼야 하므로 먼저 착수하는 것은 같다.

---

## 10. 미확정 사항

| 항목 | 왜 필요한가 | 확인 방법 |
|---|---|---|
| 관압 대표 센서 선정 기준 | 펌프별 압력 합산을 대체할 "그룹 관압" 1개가 필요 | 현장별 `TB_PUMP_*`/태그 마스터에서 토출 헤더 압력 태그 유무 확인 |
| 15분 평균 피크 SQL 존재 여부 | 피크 정의 통일의 전제 | `ai_mssql.xml:1171 peakSelect` 본문과 `TB_RAWDATA_15MIN` 류 테이블 확인 |
| 원단위용 송수량 출처 | 원단위 지표 신설 여부 | FRI 적산 테이블 또는 EPA `tanks` 응답 |
| CO2 배출계수 저장 위치 | 프런트 상수 0.4663 과 DB 값 중 어느 것이 기준인지 | `TB_RST_SAVINGS_TARGET` 생성 로직(ems_al 파이썬) 확인 |
| `selectRtRate` 가 선택 I/II/III 를 모두 반환하는지 | 요금제 비교 화면의 전제 | `ai_mssql.xml:1313` 본문과 `TB_RT_RATE_RST` 데이터 |
| 구미 외부 포털과의 경계 | 구미는 펌프 화면이 외부 서버 | 구미 측 서버가 이 리포 코드인지, 라우트 경로 의존이 있는지 |
| `FacUse` 막대·도넛 라벨 `FAC_CODE` 대소문자 | 실제 화면에서 라벨이 비는지 | 개발서버에서 설비별 사용량 화면 확인 |
| `PumpHistory` 가동률 키 불일치 | 카드가 "undefined%" 로 보이는지 | 개발서버 가동이력 화면 확인 |
