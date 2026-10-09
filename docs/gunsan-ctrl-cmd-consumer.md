# 군산 5분 제어 판단 → 제어명령 연계

- 일자: 2026-09-23
- 상태: 🔧 진행 (코드 완료, 서비스 드라이 테스트 11건 통과, 로컬 Kafka 시나리오 통과(2026-09-28), 현장 반영 대기)
- 리뷰: 정확성 리뷰(fresh) ✅ · 명세·검증 진실성 리뷰(fresh) ✅ — 반영 내역은 함정 기록·알려진 한계
- 관련: [gunsan-ctrl-workflow.html](gunsan-ctrl-workflow.html) (워크플로우·게이트·상태 전이·현장 절차), [ai-mode-pump-control-flow.md](ai-mode-pump-control-flow.md), [gunsan-pump-control-kafka.md](gunsan-pump-control-kafka.md), [sql/gunsan_ctrl_cmd.sql](sql/gunsan_ctrl_cmd.sql)

---

## 발단

벤더 5분 판단 스크립트 `epa/epanet_gunsan/main_5min.py` 가 `TB_CTRL_CMD_RST` 에 펌프 주파수·밸브 개도 제어값을 쓴다. 이 값으로 기존 제어명령 대기열(`TB_HMI_CTR_TAG` → Kafka `ems_result`)과 이력을 그대로 쓰고, 화면의 AI 운전모드(0 운전 / 1 추천 / 2 분석)에 따라 동작하게 한다.

2026-09-23 11:05 벤더가 계약을 확정했다.

> `TB_CTRL_CMD_RST` 의 `PUMP_CMD_YN` / `NATIONAL_CMD_YN` 이 `Y` 이면 제어를 실행하고, 제어값은 `PUMP_TGT_HZ` / `NATIONAL_TGT_OPEN` 을 보낸다.

같은 시각 벤더 최종본이 들어왔다. 지방산단 밸브가 빠졌고, "제어했나"를 상태가 아니라 `CMD_YN` 으로 판단하는 시퀀스(제어 → 5분 HOLD → 방향 확인 후 제어, 위험수위 즉시)로 바뀌었다. 대조 결과는 워크플로우 문서 14장에 있다.

제어 태그 번호는 현장에서 확인해 반영한다.

같은 날 13:28 벤더가 다시 교체했다(526+/295−). **"제어했다"를 `APPLIED` 로만 판단**하게 바뀌었다. 직전 행이 `CMD_YN='Y' AND STATUS='APPLIED'` 일 때만 다음 5분을 HOLD 하고, 반응 확인 기준도 마지막 `APPLIED` 명령이다(`get_last_applied_device_command`, `row_has_applied_command`). 코드 주석에 "실제 적용 성공 후 Java 제어부가 APPLIED로 변경해야 한다"고 적혀 있다. 사용자가 확인한 쟁점은 다음과 같다.

- 대상 행: `*_CMD_YN='Y'` 이고 `*_CMD_STATUS='READY'`. 지방산단은 제어 대상에서 제외, 주 제어는 운전 펌프 주파수와 국가산단 밸브 개도.
- AI 운전: 송신 후 `APPLIED`. AI 추천: 승인하면 송신 후 `APPLIED`, 거절하면 `REJECTED`. AI 분석: `REJECTED`.
- 기존 화면 요청부터 응답까지의 흐름(팝업 → 확인 → 대기열 → Kafka → FLAG → 이력)은 유지한다.
- 국가산단 밸브 제어 세부는 현장 조사 뒤 확정한다.

## 결정 (2026-09-23)

### 1. 트리거는 `*_CMD_YN = 'Y'`, 처리 결과는 벤더 테이블 상태 컬럼에 되돌려 쓴다

소비자는 `*_CMD_YN='Y'` 이고 `*_CMD_STATUS='READY'` 인 장치를 처리한다. 결과는 `PUMP_CMD_STATUS` / `NATIONAL_CMD_STATUS` 에 `APPLIED / REJECTED / FAILED / EXPIRED` 로 쓴다. 비교 후 교체(`WHERE ... STATUS='READY'`)라 중복 전이가 없다.

- 되돌려 쓰는 이유 (13:28 판): Python 은 `APPLIED` 만 "실제 제어"로 본다. 쓰지 않으면 HOLD 가 걸리지 않아 5분마다 명령이 나간다. 11:05 판에서는 반응 확인 오판(`*_NO_RESPONSE`) 방지가 이유였으나, 이제는 벤더 순서 제어의 필수 입력이다.
- `REJECTED`·`FAILED`·`EXPIRED` 는 Python 에게 모두 "제어 없음"이다. 처리 이유를 사람이 구분하려고 유지한다(2026-09-23 사용자 결정).
- 기각: 벤더 테이블을 읽기 전용으로 두고 우리 테이블에만 기록. 13:28 판에서는 벤더 시퀀스가 동작하지 않는다.
- 벤더 UPDATE 허용(P2): 13:28 판 코드가 Java 의 `APPLIED` 기록을 전제하므로 확인된 것으로 본다.

### 2. `APPLIED` 는 송신 완료 시점 (2026-09-23 정정)

같은 판단·장치의 대기열 행이 전부 `FLAG=2` 이면 `APPLIED` 다. 펌프와 밸브가 같다.

- 처음에는 밸브에 개도 계측(`POI-8601`) 되읽기 ±1%p 를 추가로 요구했다. 13:28 판에서 뺐다. `APPLIED` 가 **다음 5분 판단보다 늦으면** Python 은 제어가 없었던 것으로 보고 HOLD 없이 새 명령을 내 이중 제어가 된다. 되읽기는 밸브 이동 시간만큼 `APPLIED` 를 늦춘다. 개도 계측은 TRACE `DETAIL` 에 기록만 한다. 효과 확인은 Python `response_ok_for_national_valve` 가 유량·수위 추세로 한다. `CONFIRM_TIMEOUT`, `ctrl.cmd.valve.confirm-*` 는 없앴다.
- 사용자 요구("송신 후 APPLIED")와도 같다.
- 기각: 승인 즉시 `APPLIED`. 실패 지점마다 `FAILED` 로 덮어써야 하고 하나라도 빠지면 이력이 거짓이 된다.

### 2-1. 시간 제약: `APPLIED` 는 다음 판단 전에 (2026-09-23)

`한 판단의 대기열 행 수 × 송신 주기 + 판정 지연 < 5분`. 송신기(`pumpTask`)는 전 현장 공통 1분 주기에 한 번에 한 행이다. 펌프 4대면 약 :04:15 로 들어오지만, 밸브 두 행(VOP·VPL)이 붙으면 약 :06:15 로 넘친다.

- 결정: 송신 주기는 **1분 유지**. 밸브 행 수·순서가 현장 조사 뒤 정해지면 이 식으로 다시 본다. `PumpScheduler.java:62` 의 주석 처리된 30초 cron 은 근거 기록이 없어(초기 커밋부터 주석) 채택하지 않았다.
- 대신 적재를 매 5분 :40 → **매분 :40** 으로 바꿨다(`ctrl.cmd.consumer.cron`). Python 계산이 40초를 넘거나 대기열이 붐벼도 다음 기회가 5분 뒤가 아니라 1분 뒤다. 행 잠금으로 중복 처리는 없다. 반복되는 `PENDING`·`SKIPPED`·`BUSY` 로그는 debug 로 내렸다.
- 추천 모드는 결정 2-3 으로 다음 판단 전에 마감한다.

### 2-3. 판단은 그 주기 안에서만 유효 — 추천 무응답은 다음 판단 전에 `REJECTED` (2026-09-23)

사용자 제안: 추천 모드에서 응답이 없으면 Python 이 다음 행을 만들기 전에 `REJECTED` 로 돌린다.

- 마감 = `CTRL_TS + cycle-min(5분) − decision-close-sec(20초)`. :00 판단은 :04:40 에 마감하고, 반영 판정(:04:45)이 Python :05 실행 전에 종결한다.
  - 추천 무응답 → `REJECTED` `APPROVE_TIMEOUT`(처리자 없음, 추적 ACTION `EXPIRE`)
  - 운전 모드에서 끝내 적재 못 함 → `EXPIRED` `STALE`
  - 사람이 한 거절(`USER_REJECT`, 처리자 있음)과는 사유 코드로 구분한다.
- **이전 방식의 빈틈을 막는다.** 이전에는 TTL 10분이나, 같은 장치에 `CMD_YN='Y'` 인 새 행이 나올 때(`SUPERSEDED`)만 만료했다. 그래서 다음 판단이 "제어 불필요"(`N`)이면 5분 전 판단을 최대 10분까지 승인해 보낼 수 있었다.
- Python 판단은 바뀌지 않는다. `READY`·`REJECTED`·`EXPIRED` 는 Python 에게 모두 "제어 없음"이다.
- `ctrl.cmd.approve-ttl-min` 을 없애고 `ctrl.cmd.decision-close-sec=20` 을 추가했다. 조회 범위는 `cycle-min × 2` 로 정한다.
- 팝업은 "응답 마감까지" 남은 시간을 보여 주고, 0이면 승인 버튼을 끈다. 마감 후 승인 API 는 422 로 "승인 응답 없음"을 돌려준다.
- 시계: DB 와 Python 은 같은 Linux 서버의 컨테이너라 호스트 시계를 같이 쓴다(사용자 확인). 개발 DB 는 `@@system_time_zone = Asia/Seoul`. 새 Python 컨테이너도 `TZ=Asia/Seoul`(P8).
- 남는 경계: :04 이후 승인은 송신이 :05:00 `pumpTask` 에서 나가 `APPLIED` 가 Python :05 판단보다 늦다. Python 은 그 판단을 "제어 없음"으로 보고 새 추천을 낼 수 있지만, 추천 모드라 사람이 다시 승인해야 나간다(벤더 공유).

### 2-2. 거절·분석 모드의 기록은 기존 방식과 같다

`TB_HMI_CTR_TAG`(대기열)·`TB_HMI_CTR_LOG`(송신 로그)는 **실제로 대기열에 들어간 명령**만 남는다. 기존 코드도 같다. 조합 생성기(`pumpAiControlTask`)는 운전 모드에서만 적재하고, 기존 추천 팝업의 "취소"(`App.vue cancelBtn`)는 서버를 부르지 않으며, 분석 모드는 적재하지 않는다. LOG 에는 이 밖에 모드 전환(`ANLY_CD='INIT'`, `AiService.java:1377-1489`)이 남는다.

- 추천 거절·분석 모드·게이트 탈락·만료는 두 테이블에 남지 않는다. 벤더 상태 컬럼과 `TB_CTRL_CMD_TRACE`(처리자·사유·시각)에 남고, 제어이력 화면의 "제어 판단 이력"에서 본다.
- 승인·운전 모드 송신은 기존과 똑같이 TAG(FLAG 0→1→2) + LOG 에 남고 "송신 이력"에 보인다.
- 화면 흐름은 (가) 형태 유지로 결정했다(2026-09-23). 팝업 → 경보음 → 장치별 승인·거절 → 대기열 → Kafka → FLAG → 이력. 기존 `OnOffAlarm` 팝업에는 거절 버튼이 없어 새 팝업(`CtrlCmdApprove.vue`)을 쓴다.

### 3. 제어 태그는 DB 에 둔다

- 펌프 주파수 쓰기 태그: 기존 `TB_CTR_PRF_PUMPMST_INF.CTR_AUTO_FREQ_TAG` (개발 덤프에 `891-365-PMC-4000~4003` 존재). 2026-09-23 이 컬럼에 펌프별 제어태그가 정의되어 있다고 확인 전달받았다(P3).
- 밸브 태그: `TB_WPP_TAG_CODE` `FUNC_TYP='CtrlCmdTag'` 의 `NATIONAL_OPEN`(개도 설정 `891-365-POC-8603`) / `NATIONAL_PULSE`(OPENC, 상향 `891-365-VVK-8606`) / `NATIONAL_CLOSE_PULSE`(CLOSEC, 하향 `891-365-VVK-8607`) 행 `TAG` 컬럼. 2026-09-30 확정.
- 기각: `application-gu.properties`. 현장에서 태그를 바꿀 때마다 재빌드·재배포가 필요하다.

### 3-1. 운전·추천·분석은 AI 운전모드(`PumpStatus`) 하나로 정한다 (2026-09-23 정정)

모드 원천은 `TB_WPP_TAG_CODE` `FUNC_TYP='PumpStatus'` 의 `DEFAULT_VALUE`(0 AI / 1 추천 / 2 분석)뿐이다. 화면의 AI 운전모드 토글(`AiMode.vue` → `/ai/updateAiStatus`)이 이 값을 바꾸고, 소비자는 `PumpService.getAiControlStatus()` 로 읽는다.

- 처음에는 장치별 활성 스위치 `PUMP_ENABLED` / `NATIONAL_ENABLED`(`CtrlCmdTag`, 기본 `'0'`)를 따로 두었다. 사용자 지시로 걷어냈다. 스위치가 있으면 화면에서 AI 로 바꿔도 송신되지 않아 화면과 실제 동작이 어긋난다. 게이트 `DEVICE_DISABLED` 도 함께 없앴다.
- 대가: 별도 안전장치가 없다. 펌프 쓰기 태그가 이미 있으므로 **AI 운전(0)인 채로 배포하면 다음 :40 에 바로 송신된다.** 배포 전에 모드를 분석(2) 또는 추천(1)으로 둔다. 밸브는 태그를 넣기 전까지 `TAG_NOT_CONFIGURED` 로 막힌다.
- 기존 `TestMode` / `CtrTestMode` 게이트는 남겼다. 모드 스위치가 아니라 전 현장 공통 송신 차단이고, 꺼져 있으면 `pumpTask` 도 발행하지 않아 적재해도 `QUEUE_TIMEOUT` 이 될 뿐이다.

### 4. 기존 조합 생성기와의 배타는 `ctrl.cmd.consumer.enabled` 로 묶는다

`PumpScheduler.pumpAiControlTask` 는 군산에서 `ctrl.cmd.consumer.enabled=true` 이면 모드와 무관하게 쉰다. 화면의 기존 10분 예측비교 팝업도 같은 조건(`pumpControlActive`)에서 숨는다. 두 생성원이 같은 대기열에 쓰지 않게 하는 배포 설정이지 운전 모드가 아니다. 켜면 기동·정지는 사람이 SCADA 에서 한다(워크플로우 P9).

### 5. 밸브 펄스는 새 구분 코드 `VPL` 과 새 송신 메서드

기존 `sendCtrTagVVKItem` 은 군산 경로에서 대기열 행을 `FLAG=1` 에 남긴다. 되돌리는 `VVKStatusTask` 가 부안(`ba`) 전용이라 `pumpTask` 가 영구히 멈춘다. `sendCtrPulseTagItem` 을 새로 두어 1 → 펄스 폭 → 0 후 `FLAG=2` 로 되돌린다. 개도 설정 `VOP` 는 기존 `sendCtrFreqTagItem` 을 재사용한다.

### 5-1. 상향은 OPENC, 하향은 CLOSEC (2026-09-30 변경)

현장 확인으로 밸브 방식이 확정됐다. 목표 개도를 판단 행의 `NATIONAL_CUR_OPEN` 과 비교해 펄스 태그를 고른다.

- 상향(목표 > 현재): `VOP` 목표 개도 → `VPL` OPENC 1 → 3초 → 0
- 하향(목표 < 현재): `VOP` 목표 개도 → `VPC` CLOSEC 1 → 3초 → 0
- 현재 개도가 없으면 `REJECTED CUR_OPEN_UNKNOWN`, 목표와 같으면 `REJECTED NO_CHANGE`. 방향에 필요한 펄스 태그가 비어 있으면 `TAG_NOT_CONFIGURED`.

현재 개도로 판단 행 값을 쓰는 이유: Python 이 목표를 `CUR ± VALVE_STEP` 으로 만들므로 방향이 Python 사유(`NATIONAL_OPEN`/`NATIONAL_CLOSE`)와 항상 같다. 적재 시점 계측을 새로 읽으면 그 사이 개도가 움직여 방향이 뒤집힐 수 있다.

전송 순서 설정 `ctrl.cmd.valve.order` 는 없앴다. 순서는 개도값 → 펄스로 고정이다. 펄스 폭은 `ctrl.cmd.valve.pulse-width-sec`(기본 3초)다.

### 6. 이력 화면은 펌프 쿼리를 건드리지 않고 밸브 행을 `UNION ALL`

제어이력 화면은 로그가 아니라 대기열 `TB_HMI_CTR_TAG` 를 펌프 마스터와 조인해 읽는다. 조인을 LEFT JOIN 으로 바꾸는 계획 대신, 펌프 쿼리를 글자 그대로 두고 `VOP`·`VPL` 행만 덧붙였다. 전 현장 공통 쿼리라 회귀 위험을 줄이기 위해서다.

### 7. 승인은 장치별, 대기열 혼잡은 판정이 아니라 재시도

한 판단 행에 펌프와 밸브가 동시에 `Y` 일 수 있다. 같은 판단 행의 대기열 행은 서로를 막지 않는다(`countForeignActiveQueue`). 다른 명령이 진행 중이면 `READY` 로 두고 다음 주기에 재시도하며, 판단 마감(다음 판단 20초 전, 결정 2-3)이 먼저 오면 `EXPIRED` 다(추천 모드 무응답은 `REJECTED`).

### 8. 계획과 달라진 배치

- 매퍼는 `pump_mssql.xml` 이 아니라 새 `ctrl_cmd_mssql.xml` 로, API 는 `AiController` 가 아니라 새 `CtrlCmdController`(`/ai/ctrl/*`)로 뺐다. 벤더 계약에 묶인 코드를 한곳에 모아 드롭 대조를 쉽게 하려는 것이다.
- `selectCtrTagList` 화이트리스트에 `VOP` 를 넣지 않았다. `pumpTask` 는 `ANLY_CD` 없이 조회하므로 필요가 없다.
- 추천 모드에서도 매분 :40 에 게이트 전체를 돌려 탈락은 즉시 확정한다. 보낼 수 없는 추천을 팝업에 올리지 않기 위해서다.

### 9. 지방산단 밸브가 제어 대상으로 돌아왔다 (2026-09-30)

벤더 `main_5min.py` 2026-09-30 드롭이 지방산단 분기밸브(`891-365-POI-8600`)를 **나운 고수위 최종(fallback) 제어**로
되살렸다(대조 기록 `docs/gunsan-ctrl-5min-drop-review.md`). 판단 행에 `LOCAL_CMD_YN/STATUS/CUR_OPEN/TGT_OPEN/OBSERVE_UNTIL`
이 다시 실린다. 사용자가 같은 날 "지방산단 밸브도 제어 명령이 들어가야 한다"고 정했고 태그를 확정했다.

| 용도 | `TAG_DSC` | 태그 |
|---|---|---|
| 목표 개도 설정 | `LOCAL_OPEN` | `891-365-POC-8602` |
| OPENC 펄스(상향) | `LOCAL_PULSE` | `891-365-VVK-8601` |
| CLOSEC 펄스(하향) | `LOCAL_CLOSE_PULSE` | `891-365-VVK-8602` |
| 개도 되읽기(기록용) | `ctrl.cmd.valve.local.readback-tag` | `891-365-POI-8600` |

- 송신 방식은 국가산단(결정 5-1)과 같다: `VOP` 목표 개도 → 방향별 펄스 1 → 3초 → 0. 방향은 판단 행의 `LOCAL_CUR_OPEN` 과 비교한다.
- 구현은 장치 이름을 컬럼·태그 키·대기열 `OPT_IDX` 접두로 그대로 쓰는 구조라, `DEVICES` 에 `LOCAL` 을 넣고 `evaluateNational` 을 `evaluateValve(device)` 로 일반화했다. 매퍼는 `cmdColumns`·`selectReadyCmdList`·`countNewerDeviceCmd`·`updateDeviceStatus` 네 곳에 `LOCAL` 분기가 늘었다.
- **왜 BE 가 꼭 처리해야 하나**: Python 은 지방산단 원복(OPEN)과 조건부 CLOSE 의 근거로 `APPLIED` 행만 본다(`get_last_applied_device_command`). BE 가 `LOCAL_CMD_STATUS` 를 `APPLIED` 로 되돌려 쓰지 않으면 원복은 영영 발동하지 않고, 조건이 유지되는 동안 5분마다 `READY` 행만 쌓인다.
- 제어이력 화면(`ai_mssql.xml` 의 `VOP/VPL/VPC` UNION)은 `CTR_NM` 만 "지방산단밸브"로 달라지므로 쿼리 변경이 없다. 승인 팝업(`CtrlCmdApprove.vue`)은 `DEVICE_NM`·단위를 서버 값·PUMP 여부로만 판단해 변경이 없다.
- P14(지방산단 컬럼의 향후)는 이것으로 닫는다.

## 변경 내역

| 대상 | 변경 |
|---|---|
| `be/.../pump/CtrlCmdService.java` | 신규. 게이트·적재·승인·거절·반영 판정·화면 조회·사유 한글 사전 |
| `be/.../pump/CtrlCmdScheduler.java` | 신규. `@Profile("gu")`. consume `40 * * * * *`(매분, 결정 2-1), judge `15,45 * * * * *` |
| `be/.../pump/CtrlCmdController.java` | 신규. `GET /ai/ctrl/latest·pending·history`, `POST /ai/ctrl/approve·reject` |
| `be/.../pump/CtrlCmdMapper.java`, `sqlmapper/mysql/ctrl_cmd_mssql.xml` | 신규 |
| `be/.../pump/PumpService.java` | `VOP`·`VPL` 분기, `sendCtrPulseTagItem`, 로그 라벨 2개, `ctrl.cmd.valve.pulse-width-sec` |
| `be/.../pump/PumpScheduler.java` | 군산에서 `isPumpControlActive()` 면 `pumpAiControlTask` 건너뜀 |
| `be/.../sqlmapper/mysql/ai_mssql.xml` | `selectPumpCtrHistoryList`·`selectPumpCtrHistoryCount` 에 밸브 행 `UNION ALL`/합산 |
| `be/src/main/resources/application-gu.properties` | `ctrl.cmd.*` 11키 (주석은 기존 관례대로 `\u` 이스케이프). 13:28 대응으로 `confirm-*` 2키 삭제, `cycle-min` 추가. 결정 2-3 으로 `approve-ttl-min` 삭제, `decision-close-sec` 추가 |
| `fe/src/views/Common/CtrlCmdApprove.vue` | 신규. 추천 모드 승인 팝업 (30초 조회, 장치별 승인/거절) |
| `fe/src/views/AiAnalysis/.../Gunsan/CtrlCmdLatestCard.vue` | 신규. 최근 판단 카드. 2026-09-28 사용자 요청으로 운전현황 분석 화면에서 뺐다(파일은 남김, 현재 어디서도 쓰지 않음) |
| `fe/src/views/AiAnalysis/.../PumpControlHistory/CtrlCmdHistory_list.vue` | 신규. 판단 이력 표 |
| `fe/src/App.vue` | 승인 팝업 장착, 군산 `pumpControlActive` 면 기존 팝업 생략 |
| `fe/src/views/Common/AiMode.vue` | 군산 모드 전환 확인창에 진행 중·승인 대기 건수 |
| `fe/.../PumpControlHistory.vue` | 판단 이력 전환 버튼 |
| `fe/.../PumpDrvnAnlyForGunsan.vue` | 최근 판단 카드를 붙였다가 2026-09-28 되돌림(커밋 `f5523b4` 이전과 동일). 운전현황 분석 화면에는 기존 콘텐츠만 보이고, 승인은 전역 팝업(`CtrlCmdApprove`)으로만 한다 |
| `docs/sql/gunsan_ctrl_cmd.sql` | 신규. 추적 테이블 DDL, 설정 행(멱등), 현장 UPDATE, 확인 쿼리 |
| `docs/gunsan-ctrl-workflow.html` | 최종본 기준으로 재작성, 구현 반영 |
| `epa/epanet_gunsan/main_5min.py` | 변경 없음 (벤더 소유. 워킹트리 차이는 13:28 벤더 드롭) |
| `deploy/gunsan/*` | 변경 없음. `ems-ctrl-5min` 컨테이너 추가는 별도 작업(P8) |
| 벤더 테이블 DDL | 변경 없음 |

### 변경 내역 — 지방산단 밸브 제어 대상 복귀 (2026-09-30, 결정 9)

| 대상 | 변경 |
|---|---|
| `be/.../pump/CtrlCmdService.java` | `LOCAL` 상수, `DEVICES = PUMP·NATIONAL·LOCAL`(public), `evaluateNational` → `evaluateValve(device)`, `tgt/cur/deviceLabel` 3장치, 되읽기 태그 장치별(`readbackTag`), 대기열 `CTR_NM` "지방산단밸브", `REASON_LABELS` 에 `LOCAL_*` 12종·`OSIK_BALANCE_*`·`OSIK_OUTFLOW_MISSING` |
| `be/.../pump/CtrlCmdScheduler.java` | 장치 배열 대신 `CtrlCmdService.DEVICES` 순회 |
| `sqlmapper/mysql/ctrl_cmd_mssql.xml` | `cmdColumns` LOCAL 4컬럼, `selectReadyCmdList` OR 1줄, `countNewerDeviceCmd`·`updateDeviceStatus` `LOCAL` 분기 |
| `application-gu.properties` | `ctrl.cmd.valve.local.readback-tag=891-365-POI-8600` |
| `CtrlCmdServiceIT.java` | `insertLocalValveTags`, `insertCmd(…, local)` 오버로드(98 → 93 %), LOCAL 4케이스(태그 없음/하향 CLOSEC/상향 OPENC/현재개도 없음/추천 목록) |
| `docs/sql/gunsan_ctrl_cmd.sql` | 2절 `LOCAL_OPEN/PULSE/CLOSE_PULSE` 행 3개(멱등), 3절 확정 태그 UPDATE 3줄, 드롭 선행조건 확인 SQL, 4-(d) LOCAL 컬럼 |
| `fe/.../CtrlCmdHistory_list.vue` | `LOCAL` 열 + 셀 템플릿, `deviceLabel` 3장치 |
| `fe/.../Gunsan/CtrlCmdLatestCard.vue` | devices 배열에 지방산단 |
| `docs/gunsan-ctrl-workflow.html` | 장치 둘 → 셋, 4.5 결과 행, P14 반영, 14장 대조표 1·7행 |

## 함정 기록

- **트랜잭션 테스트에서 MyBatis 1차 캐시가 JDBC 변경을 가린다.** 테스트 전체가 한 트랜잭션이라 SqlSession 하나를 쓰고(`localCacheScope` 기본 SESSION), 같은 조회를 다시 하면 캐시된 결과가 온다. JdbcTemplate 으로 FLAG·CTRL_TS 를 바꾼 뒤 두 번째 `judgeAll()` 이 옛 값을 봐 3건이 실패했다. 테스트의 쓰기 도우미에서 `SqlSessionTemplate.clearCache()` 를 부르게 했다. 운영 경로는 해당 없다. `judgeAll`·스케줄러는 호출마다 새 세션이고, `processDevice` 는 한 트랜잭션에서 같은 조회를 한 번씩만 한다.
- **Git Bash 에서 한글 출력이 깨져 보인다.** 테스트 보고서의 한글 메서드 이름, 파이썬으로 출력한 한글 모두 깨져 보였다. 클래스 파일 안의 한글은 기본 컴파일로도 UTF-8 로 정상이었다(바이트 검색으로 확인). 터미널 표시 문제다.

- **`sendCtrTagVVKItem` 이 군산에서 대기열을 막는다.** 송신 후 `ANLY_CD` 를 `INIT` 으로 바꾸고 로그만 남겨 `updateCtrTag`(TAG+ANLY_CD+OPT_IDX) 가 원래 행을 못 찾는다. 결정 5.
- **`TB_WPP_TAG_CODE` 에 기본키가 없다.** `INSERT IGNORE` 로는 중복을 못 막아 `NOT EXISTS` 로 멱등하게 했다. 두 번 실행해 4행인 것을 확인했다(당시 스위치 2행 포함. 결정 3-1 이후 밸브 태그 2행만 남는다).
- **로컬 JDK 21 에서 `compileJava` 가 Lombok 1.18.24 오류로 실패한다.** (`JCTree$JCImport does not have member field 'qualid'`) JDK 11 로 빌드한다.
- **`fe` 잠금 파일이 `package.json` 과 어긋나 `npm ci` 가 실패한다.** (echarts-stat, ol, proj4 누락) 작업 전부터 있던 상태다. 추적 파일을 바꾸지 않도록 `npm install --no-package-lock` 로 설치했다.
- **properties 한글 주석은 bash heredoc 으로 넘기면 깨진다.** 스크래치 스크립트로 `\u` 이스케이프를 생성해 붙였다.
- **이력 화면의 원천은 `TB_HMI_CTR_LOG` 가 아니라 `TB_HMI_CTR_TAG` 다.** 워크플로우 문서 10장 초안을 정정했다.

리뷰에서 나와 고친 것 (2026-09-23):

- **반영 판정과 승인 사이의 경합.** `judgeAll` 은 같은 빈 안에서 돌아 `@Transactional` 이 걸리지 않는다. 승인이 행을 잠그고 적재하는 사이 판정이 "대기열 없음 + 낡음"을 보면, 커밋 뒤 READY 를 `EXPIRED` 로 바꿔 송신되는 명령이 만료로 기록됐다. 만료 경로를 `TransactionTemplate` 으로 감싸고, 행을 잠근 뒤 READY·대기열 없음을 다시 확인하게 했다(`expireIfIdle`). 두 리뷰어가 함께 지적했다.
- **펄스 도중 예외 시 OPENC 가 1 로 남음.** 1 송신 뒤의 로그·대기·갱신을 `try/finally` 로 감싸 0 송신과 `FLAG=2` 를 보장했다.
- **밸브 되읽기가 송신 전 계측값으로 판정.** 대기열 행의 마지막 `UPDT_TIME` 이후 계측(`TS`)만 쓰게 했다. 스텝이 허용오차 이하이면 움직이지 않아도 `APPLIED` 가 되던 문제다. (이후 결정 2 정정으로 되읽기 판정 자체를 없앴다.)
- **게이트 순서가 문서와 달랐다.** 코드를 문서 순서(모드 → 테스트모드 → 신선도 → 값 범위 → 태그 → 운전 펌프. 당시 있던 장치 스위치는 결정 3-1 로 제거)로 맞췄다. 태그 누락 알람이 조합 변경 사유에 묻히지 않는다.
- **화면 폴링이 원시테이블을 과하게 읽음.** `pending` 사전검사는 운전 펌프 확인(PMB 원시값 4건)을 건너뛰고, 판단 시점 조합의 쓰기 태그만 본다. 승인 순간에는 전체 게이트를 다시 돈다.
- **`fetchFunc` 는 실패해도 예외를 던지지 않고 `{error:true}` 를 준다.** 팝업·카드가 일시 조회 실패에 사라지던 것을 직전 상태 유지로 고쳤다.
- **"닫기" 가 목록이 줄기만 해도 다시 뜸.** 닫은 항목과 알람 낸 항목을 `CTRL_ID:DEVICE` 단위로 기억하게 했다.
- **`ctrlId` 누락 시 500.** 본문 code 409 로 응답하게 했다.
- **판단 이력 조회가 `23:59:59` 판단을 뺌.** `CTRL_TS <= TO` 로 바꿨다.

## 알려진 한계

- ➖ 검증불가: 운영 브로커(`<internal-host>`)로의 송신, SCADA 반영. 운영망에서만 확인된다. 워크플로우 15장 현장 절차로 대체한다. 송신 코드 경로 자체는 로컬 브로커로 확인했다(2026-09-28 시나리오).
- 게이트 분기·상태 전이·승인·거절·마감과 MyBatis 매퍼 XML 로딩은 드라이 테스트 `CtrlCmdServiceIT` 로 확인했다(11건 통과, 실측 결과 참고). 컨트롤러 HTTP 계층(`/ai/ctrl/pending·latest·approve·reject`), 스케줄러 cron 연결, `pumpTask` 의 FREQ·VOP·VPL 송신 분기, `selectLatestCmd` 는 2026-09-28 로컬 시나리오에서 확인했다. **미실시**: `/ai/ctrl/history`(`selectCmdHistory`·`selectTraceByCtrlIds`), 운전 모드(0) 자동 적재, 422 응답(마감 뒤 승인·게이트 탈락).
- `TB_HMI_CTR_LOG.DCS` 는 항상 NULL 이다. `PumpService.insertHmiTagLog` 가 `DCS` 라벨(밸브 개도 설정·밸브 펄스 포함)을 채우지만 매퍼 `insertHmiTagLog`(`pump_mssql.xml:264-268`)의 컬럼 목록에 `DCS` 가 없다. 변경 전부터 RUN/STOP 도 같다. 이력 화면은 `ANLY_CD` 로 라벨을 만들어 영향이 없다.
- 대기열 경유 송신의 Kafka `time` 은 `"2026-09-28 13:13:43.0"` 처럼 `.0` 이 붙는다. 대기열 `TIME`(datetime)을 MyBatis 가 `Timestamp` 로 읽어 `toString()` 하기 때문이다. 기존 FREQ 송신도 같은 경로다. 펄스의 0 송신만 `nowStringDate()` 라 `.0` 이 없다. `time` 은 송신 시각이 아니라 **적재 시각 − 2분**이다. 게이트웨이가 두 형식을 모두 받는지는 현장에서 확인한다([gunsan-pump-control-kafka.md](gunsan-pump-control-kafka.md) 3.4 의 예시는 `.0` 없음).
- 목표값을 정수로 반올림해 보낸다. 기존 FREQ 제어와 같은 방식이다. Python 목표가 소수(예: 평균 44.3 → 45.3)면 실제 변화량과 벤더 테이블의 `TGT` 가 어긋난다. 추적의 `DETAIL` 에 실제 송신값이 남는다. 태그가 소수를 받는지 현장에서 확인한 뒤 바꿀지 정한다.
- 기존 제어이력 개수 쿼리는 펌프 쪽에서 RUN/STOP 만 센다(FREQ 제외, 변경 전부터). 목록과 개수의 기준이 원래 달랐고, 밸브 합산도 그 위에 얹었다.
- 주파수·밸브 모두 되읽기 검증 없이 `FLAG=2` 로 `APPLIED` 처리한다(결정 2). 게이트웨이 쓰기 허용(P6)이 없으면 `APPLIED` 가 찍혀도 실제로는 안 움직이고, Python 은 그 뒤 `*_NO_RESPONSE` 로 보류한다.
- 추천 모드 승인 가능 시간은 약 4분 40초다. 무응답은 `REJECTED APPROVE_TIMEOUT`(결정 2-3). :04 이후 승인은 `APPLIED` 가 다음 판단보다 늦는다.
- 펌프 4대 + 밸브가 한 판단에 함께 나오면 `APPLIED` 가 다음 판단보다 늦는다(결정 2-1). 밸브 확정 뒤 송신 주기를 다시 본다.
- 알람 시간당 1회 제한은 인스턴스 메모리라 재기동하면 초기화된다.
- `USER_ID` 는 화면이 보내는 `localStorage.user` 를 그대로 기록한다. 서버 쪽 인증과 대조하지 않는다.
- 판단 이력 조회 상한 2000행.

## 검증

```
# 백엔드 컴파일 (JDK 11)
JAVA_HOME="C:/Program Files/Java/jdk11.0.21_9" ./gradlew compileJava -q

# 신규·변경 SQL: 개발 덤프 DB(<internal-host> / ems_db) 한 트랜잭션 + ROLLBACK
#   추적 테이블은 docs/sql DDL 을 TEMPORARY 로 실행
# 이력 쿼리 회귀: 변경 전(HEAD) 과 후를 펌프 이력이 가장 많은 날(2024-10-20)로 비교

# 벤더 최종본 결과 행 컬럼
python epanet_gunsan/main_5min.py --conn epanet_gunsan/connections.json --ts "2026-09-21 13:30:00" --dry-run

# 프론트 빌드·린트
npx vue-cli-service build --dest <scratch>
npx vue-cli-service lint --no-fix <변경 파일 6개>
```

### 실측 결과 (2026-09-23)

백엔드 컴파일:

```
JDK 21: > java.lang.NoSuchFieldError: Class com.sun.tools.javac.tree.JCTree$JCImport does not have member field 'com.sun.tools.javac.tree.JCTree qualid'
JDK 11: EXIT=0 (출력 없음)
```

SQL (트랜잭션 + ROLLBACK, 발췌):

```
--- 1 selectCtrlCmdTagConfig (시드 2회 실행 후)          (4 rows)
--- 2 selectReadyCmdList(LOOKBACK 20)                      (2 rows)
--- 4 countNewerDeviceCmd PUMP (기대: PUMP 1, NATIONAL 0)   {'n': '1'}
--- 4 countNewerDeviceCmd NATIONAL                         {'n': '0'}
--- 7 countForeignActiveQueue (자기 행 제외)               {'n': '0'}
--- 7b countForeignActiveQueue (다른 판단 행 기준, +4)     {'n': '4'}
--- 8 updateDeviceStatus PUMP READY→APPLIED                rowcount = 1
--- 8b 같은 전이 반복 (기대 0)                             rowcount = 0
--- 8c NATIONAL 이 N 인 행 (기대 0)                        rowcount = 0
--- 9 discardQueueRows NATIONAL (기대 2)                   rowcount = 2
--- 10 selectPumpMaster  CTR_AUTO_FREQ_TAG 891-365-PMC-4000 ~ 4003 (4 rows)
--- 11 selectLatestRaw POI-8601  {'VALUE': '39.73125', 'TS': '2026-09-21 13:36:00'}
      ※ 조회 창을 매퍼의 5분이 아니라 7일(60*24*7분)로 넓혀 실행했다. 덤프 원시데이터의 최신이 2026-09-21 이라서다.
--- 12 selectTraceByCtrlIds (2 rows)
--- 15 selectPumpCtrHistoryList (오늘, 밸브 행 포함)
   {'PUMP_NM': '국가산단밸브', 'TAG': 'TEST-POC', 'ANLY_CD': '밸브 개도(40)', 'FLAG': '취소', ...}
   {'PUMP_NM': '국가산단밸브', 'TAG': 'TEST-VVK', 'ANLY_CD': '밸브 펄스', 'FLAG': '취소', ...}  (4 rows)
--- 16 selectPumpCtrHistoryCount (오늘)  2
      ※ 목록 4행(FREQ 2 + 밸브 2)과 개수 2(RUN/STOP 0 + 밸브 2)가 다른 것은 기존 개수 쿼리가 FREQ 를 세지 않기 때문이다.
=== ROLLBACK 완료
롤백 후 TB_CTRL_CMD_RST 행 수: 0
롤백 후 CtrlCmdTag 행 수: 0
롤백 후 CTRL: 대기열 행 수: 0
```

이력 쿼리 회귀 (2024-10-20):

```
old list rows 60 / new list rows 60
전체 행수 old/new 579 579 집합 동일 True
첫 페이지 ORDER_TIME 순서 동일 True
old count 0 / new count 0
```

같은 초에 찍힌 행끼리의 순서만 달랐다. 변경 전 쿼리도 그 순서를 보장하지 않는다. 개수 비교(0/0)는 그날 RUN/STOP 행이 없어 사실상 아무것도 확인하지 못했다. 회귀 비교는 군산 덤프에서만 했다.

벤더 최종본 dry-run:

```
CTRL_TS=2026-09-21 13:30:00 CMD=N PUMP=N nan->nan NATIONAL=N 39.73->39.73 REASON=RAW_DATA_MISSING|LEVEL_SENSOR_CHECK_NAUN|...
row keys: ['CMD_YN', 'CTRL_TS', 'NATIONAL_CMD_STATUS', 'NATIONAL_CMD_YN', 'NATIONAL_CUR_OPEN', 'NATIONAL_OBSERVE_UNTIL',
 'NATIONAL_TGT_OPEN', 'PRED_STALE_YN', 'PUMP_CMD_STATUS', 'PUMP_CMD_YN', 'PUMP_COMB', 'PUMP_CUR_HZ', 'PUMP_OBSERVE_UNTIL',
 'PUMP_TGT_HZ', 'REASON_CODE']
```

필수 계측 일부가 기준시각 전후로 없어(`RAW_DATA_MISSING`) 판단은 보류였다. 그래서 `CMD_YN='Y'` 행의 값 형식은 실측하지 못했다. 결과 행 컬럼 집합은 매퍼가 읽는 컬럼과 같고 `LOCAL_*` 은 없다. PMB 태그와 `PUMP_IDX` 의 대응(4017→1 … 4032→4)은 #10 출력의 `PMB_TAG` 로 확인된다.

프론트 (변경 파일 7개 린트):

```
 DONE  No lint errors found!
 DONE  Build complete.
```

### 실측 결과 — 리뷰 반영 후 재실행 (2026-09-23)

```
compileJava (JDK 11): COMPILE_EXIT=0
SQL 검증 재실행: EXIT=0, 전이 rowcount 1/0/0, discard 2, 롤백 후 0/0/0 (위와 같음, 13번은 CTRL_TS <= TO 로)
lint --no-fix 7개 파일: DONE  No lint errors found!
build: DONE  Build complete. BUILD_EXIT=0
```

### 실측 결과 — 13:28 드롭 대응 후 (2026-09-23)

```
compileJava (JDK 11): COMPILE_EXIT=0
lint --no-fix CtrlCmdApprove.vue: DONE  No lint errors found!
main_5min.py --ts "2024-11-12 10:00:00" --dry-run (개발 덤프, 13:28 판):
  row keys = CMD_YN, CTRL_TS, NATIONAL_CMD_STATUS, NATIONAL_CMD_YN, NATIONAL_CUR_OPEN, NATIONAL_OBSERVE_UNTIL,
             NATIONAL_TGT_OPEN, PRED_STALE_YN, PUMP_CMD_STATUS, PUMP_CMD_YN, PUMP_COMB, PUMP_CUR_HZ,
             PUMP_OBSERVE_UNTIL, PUMP_TGT_HZ, REASON_CODE   (LOCAL_* 없음, 매퍼가 읽는 컬럼 모두 있음)
  이 시각은 CMD_YN=N (REASON PRED_STALE|OSIK_PRE_HIGH|NATIONAL_RANGE_CHECK) — Y 행 생성 경로는 확인하지 못함
```

앱 기동 검증은 여전히 미실시다. 이번 변경(판정 단순화·적재 주기·남은 시간 계산)도 컴파일만 확인했다. (→ 2026-09-28 로컬 시나리오에서 기동·화면·송신까지 확인, 아래)

### 실측 결과 — 결정 2-3 판단 마감 (2026-09-23)

```
compileJava (JDK 11): COMPILE_EXIT=0
lint --no-fix CtrlCmdApprove.vue: DONE  No lint errors found!
개발 덤프 DB, 읽기 전용: TIMESTAMPDIFF(SECOND, CTRL_TS, NOW()) >= 5*60-20
  (279, 279, 0)  (280, 280, 1)  (290, 290, 1)    → 280초(:04:40)부터 마감
  NOW()=2026-09-23 14:17:39, @@session.time_zone=SYSTEM, @@system_time_zone=Asia/Seoul, CTRL_TS=datetime
```

### 실측 결과 — 드라이 테스트 `CtrlCmdServiceIT` (2026-09-23)

`be/src/test/java/kr/co/mindone/ems/pump/CtrlCmdServiceIT.java`. 실제 Spring 컨텍스트(MyBatis 매퍼 XML 로딩 포함)로 개발 덤프 DB 에 붙어 서비스 메서드를 호출하고, 테스트마다 롤백한다.

- 안전장치
  - 프로파일 `gu2` 로 띄운다. 스케줄러, Kafka 컨슈머·프로듀서가 모두 뜨지 않아 송신이 없다.
  - datasource 는 환경변수로만 받는다. 변수가 없으면 테스트를 건너뛴다.
  - `SELECT DATABASE()` 에 `dump` 가 들어 있어야 실행한다.
  - 추적 테이블은 `TEMPORARY` 로 만든다.
- 준비 데이터(롤백): 가짜 판단 행, `PumpStatus` 모드, 지금 시각의 PMB 운전 상태(2·3번 운전), 밸브 태그 행.

```
CTRL_CMD_IT_DB_URL=jdbc:mariadb://<internal-host>:3306/ems_db?serverTimezone=Asia/Seoul \
CTRL_CMD_IT_DB_USER=… CTRL_CMD_IT_DB_PASSWORD=… \
./gradlew test --tests kr.co.mindone.ems.pump.CtrlCmdServiceIT      (JDK 11)
→ tests=11 skipped=0 failures=0 errors=0, BUILD SUCCESSFUL
```

| 시나리오 | 확인한 것 |
|---|---|
| 운전 · 펌프 | 적재(PMC-4001·4002, VALUE 45, FLAG 0, AI_STATUS 0), FLAG 1 은 READY 유지, FLAG 2 → `APPLIED`, 추적 ENQUEUE·APPLY |
| 운전 · 대기열 혼잡 | `BUSY` 로 READY 유지, 마감(290초) 뒤 `EXPIRED STALE` |
| 운전 · 모드 전환 폐기 | FLAG 3 → `FAILED QUEUE_DISCARDED` |
| 운전 · 조합 변경 | `REJECTED PUMP_STATE_CHANGED`, 적재 없음 |
| 운전 · 밸브 | 태그 없으면 `REJECTED TAG_NOT_CONFIGURED`. 태그가 있으면 VOP(40) → VPL(1) 순서로 적재, FLAG 2 → `APPLIED`, DETAIL "목표 40 …" |
| 추천 · 승인 | 소비자는 `PENDING`(적재 없음), 팝업 목록 REMAIN_SEC 240~250, 승인 → 적재 + 추적 APPROVE(tester) → `APPLIED` |
| 추천 · 거절 | `REJECTED USER_REJECT`, 처리자 기록, 대기열 없음 |
| 추천 · 무응답 | 270초 READY 유지, 290초 팝업에서 빠지고 `REJECTED APPROVE_TIMEOUT`(ACTION EXPIRE, 처리자 없음) |
| 추천 · 마감 뒤 승인 | `REJECTED APPROVE_TIMEOUT`, 송신 없음 |
| 운전 중 승인 | `CONFLICT`, READY 유지 |
| 분석 | 펌프·밸브 모두 `REJECTED ANALYZE_MODE`, 대기열 없음 |

여전히 확인하지 못한 것: Kafka 송신(`pumpTask`), SCADA 반영, 컨트롤러 HTTP 계층(`/ai/ctrl/*`), 스케줄러 cron 연결. (→ SCADA 반영을 뺀 나머지는 아래 2026-09-28 시나리오에서 확인)

### 실측 결과 — 로컬 gu BE + 로컬 Kafka 시나리오 (2026-09-28)

AI 추천 모드에서 `main_5min.py` 가 펌프 Hz·밸브 개도를 냈다고 가정하고, 팝업 → 승인·거절·무응답 → 대기열 → Kafka → 송신 로그 → `APPLIED` 까지 실제 앱으로 돌렸다.

**조건**

- DB: 개발 덤프 `<internal-host> / ems_db`. 개발 서버 `ems-java-api` 는 `dev` 프로파일이라(연계 꺼짐, `CtrlCmdScheduler`·`PumpScheduler` 없음) 쓰지 않았다.
- BE: 로컬 `gradlew bootRun`(JDK 11), 인자 `--spring.profiles.active=gu --server.port=9000`, datasource 를 개발 덤프로, `spring.kafka.bootstrap-servers`(`-1`·`-2` 포함)를 `localhost:9092` 로 덮어썼다. 기동 로그에 `10.105.` 0건, Kafka 는 로컬 클러스터 1노드에 붙었다.
- Kafka: docker `apache/kafka:3.8.0` 단일 노드, `ems_result` 토픽을 `kafka-console-consumer.sh --from-beginning` 로 수신.
- FE: 로컬 `npm run serve`(3000 사용 중이라 3105). 프록시 `/ems-api` → `localhost:9000`. 사용자 `defaultUser`.
- DB 준비: `docs/sql/gunsan_ctrl_cmd.sql` 1·2절(TRACE 테이블·밸브 태그 행 — 개발 덤프에 둘 다 없었다), 밸브 태그를 후보값 `891-365-POC-8603`/`891-365-VVK-8606` 로, `PumpStatus` 0 → 1, 더미 계측 `seed_dummy.py --follow --pumps-on 1,3`(PMB-4017·4027 = 1). `TestMode`·`CtrTestMode` 는 원래 1.
- 판단 행: `main_5min.py` 대신 5분 경계 2초 뒤에 `TB_CTRL_CMD_RST` 에 직접 INSERT(`REASON_CODE='SCENARIO_TEST'`, `PUMP_COMB='1,3'`).

**결과**

| 주기 | 판단 (CTRL_ID) | 조작 | 결과 |
|---|---|---|---|
| 13:15 | 41: 펌프 41→43Hz, 밸브 40→45% | 팝업 2항목·마감 04:01. 펌프 승인 13:15:42, 밸브 거절 13:15:45 | 펌프: 대기열 PMC-4000·4002 = 43 `FREQ` → Kafka 13:16:00·13:17:00 → `APPLIED` 13:17:15. 밸브: `REJECTED USER_REJECT`, 대기열 없음 |
| 13:20 | 42: 펌프 43→44Hz, 밸브 40→45% | 펌프 승인 13:20:40, 밸브 승인 13:20:42 (같은 판단이라 `BUSY` 없음, 결정 7) | Kafka PMC-4000 = 44(13:21) → PMC-4002 = 44(13:22) → POC-8603 = 45(13:23) → VVK-8606 = 1(13:24:00) → **5초 뒤** VVK-8606 = 0(13:24:05). 펌프 `APPLIED` 13:22:15, 밸브 `APPLIED` 13:24:15 (다음 판단 :25 전), TRACE DETAIL "목표 45 / 계측 35.87981 @2026-09-28 13:24:00" |
| 13:25 | 43: 펌프 44→42Hz (밸브 N) | 팝업이 떴고 "닫기(나중에)" 로만 숨김 | 13:29:45 judge 에서 `REJECTED APPROVE_TIMEOUT`, TRACE `EXPIRE`(처리자 없음), 대기열 0행 |

Kafka 수신 (제어 태그만 발췌):

```
CreateTime:1790568960036  {"tag":"891-365-PMC-4000","value":43,"time":"2026-09-28 13:13:43.0"}
CreateTime:1790569020036  {"tag":"891-365-PMC-4002","value":43,"time":"2026-09-28 13:13:43.0"}
CreateTime:1790569260037  {"tag":"891-365-PMC-4000","value":44,"time":"2026-09-28 13:18:41.0"}
CreateTime:1790569320038  {"tag":"891-365-PMC-4002","value":44,"time":"2026-09-28 13:18:41.0"}
CreateTime:1790569380050  {"tag":"891-365-POC-8603","value":45,"time":"2026-09-28 13:18:43.0"}
CreateTime:1790569440044  {"tag":"891-365-VVK-8606","value":1,"time":"2026-09-28 13:18:43.0"}
CreateTime:1790569445096  {"tag":"891-365-VVK-8606","value":0,"time":"2026-09-28 13:22:05"}
```

추적 `TB_CTRL_CMD_TRACE` (8행):

```
41 PUMP     APPROVE  defaultUser  FREQ 891-365-PMC-4000=43; FREQ 891-365-PMC-4002=43;   13:15:42
41 NATIONAL REJECT   USER_REJECT  defaultUser                                           13:15:45
41 PUMP     APPLY                                                                       13:17:13
42 PUMP     APPROVE  defaultUser  FREQ ...=44 (2행)                                     13:20:40
42 NATIONAL APPROVE  defaultUser  VOP 891-365-POC-8603=45; VPL 891-365-VVK-8606=1;      13:20:42
42 PUMP     APPLY                                                                       13:22:13
42 NATIONAL APPLY    목표 45 / 계측 35.87981 @2026-09-28 13:24:00                        13:24:13
43 PUMP     EXPIRE   APPROVE_TIMEOUT  (처리자 없음)                                      13:29:43
```

송신 로그 `TB_HMI_CTR_LOG`: 송신한 태그마다 FLAG 0(송신 직전)·FLAG 2(완료) 2행씩, 모두 12행. VPL 은 1(FLAG 0)·0(FLAG 2). `DCS` 는 모두 NULL(알려진 한계).

**확인한 것**

- 추천 모드 팝업: 30초 조회로 떠서 장치별 현재 → 목표, 판단 시각, 사유, 마감 카운트다운을 보여 준다. 승인하면 Swal "제어 명령이 대기열에 등록되었습니다." 가 뜬다(확인창 없이 즉시 적재). "닫기" 는 서버 상태를 바꾸지 않고, 그 판단은 무응답으로 마감된다.
- `/ai/ctrl/pending`·`latest` 응답 구조, 승인·거절 200.
- `pumpTask` 는 추천 모드에서 1분에 대기열 1행씩 보낸다. 송신 후 약 8초에 `FLAG=2`.
- 결정 2-1 계산과 같다: 운전 펌프 2대 + 밸브 2행 = 4행이 :21~:24 에 나가 `APPLIED` 가 :24:15 로 다음 판단(:25) 전에 들어왔다. 펌프 4대면 넘친다.
- 추천 모드에서 기존 조합 생성기는 적재하지 않았다. 13시 이후 `TB_HMI_CTR_TAG` 에 `CTRL:%` 외 행이 없다. `PumpService.changePumpList` 의 `DEBUG` 로그는 5분마다 `TB_HMI_CTR_LOG` 에 남았다(84행, 정리 때 삭제).

**정리**

테스트 행 삭제(`TB_CTRL_CMD_RST` 3, `TB_HMI_CTR_TAG` 6, `TB_HMI_CTR_LOG` 96 — 제어 태그 12 + 로컬 BE 가 남긴 `DEBUG` 84, `TB_CTRL_CMD_TRACE` 8), `PumpStatus` 1 → 0 복원. `TB_CTRL_CMD_TRACE` 테이블과 `CtrlCmdTag` 밸브 태그 2행(후보값)은 다음 시험용으로 남겼다. 더미 계측(`DUMMY_SIM`)은 남아 있다(`seed_dummy.py --purge` 로 지운다). 로컬 gu BE 의 다른 스케줄러(운전현황 `DrvnConfig` 등)가 이 구간에 개발 DB 에 쓴 행은 정리하지 않았다.

재시험 — 최근 판단 카드 제거 후 (2026-09-28 13:36~13:48, 같은 조건):

- `/PumpDrvnAnly` 에 "제어 판단" 카드가 없고 차트 아래에 바로 "성능 및 저항곡선" 이 온다(화면 텍스트 검사·캡처). 승인 팝업은 그대로 떴다.
- 13:40 판단(44, 펌프 41→43Hz·밸브 40→45%) 둘 다 승인 → Kafka PMC-4000=43, PMC-4002=43, POC-8603=45, VVK-8606=1 → 5초 뒤 0. 펌프 `APPLIED` 13:42:15, 밸브 `APPLIED` 13:44:15(DETAIL "목표 45 / 계측 36.23589").
- 13:45 판단(45, 펌프 43→42Hz) 승인 → Kafka PMC-4000·4002=42, `APPLIED` 13:47:15. 무응답 마감은 이번에 다시 보지 않았다(화면 변경과 무관한 서버 판정, 위 13:25 주기에서 확인).
- 정리: `TB_CTRL_CMD_RST` 2, `TB_HMI_CTR_TAG` 6, `TB_HMI_CTR_LOG` 48, `TB_CTRL_CMD_TRACE` 6행 삭제, `PumpStatus` 0 복원.

재현 시 주의:

- 판단 행은 5분 경계 직후에 넣는다. `CTRL_TS` 부터 280초가 지나면 팝업에 오르지 않는다.
- 로컬 FE 를 `/` 로 열면 토큰이 없어 SSO 포털 `:10021/login` 으로 넘어간다. `/PumpDrvnAnly` 처럼 경로를 붙여 들어가면 `defaultUser` 로 진행된다.

### 실측 결과 — 지방산단 LOCAL 확장 (2026-09-30)

```
compileJava + compileTestJava (JDK 11): COMPILE_EXIT=0
vue-cli-service lint --no-fix CtrlCmdHistory_list.vue CtrlCmdLatestCard.vue: DONE  No lint errors found!
CtrlCmdServiceIT: 실행 못 함 — 개발 덤프 DB(<internal-host>:3306) 연결 시간 초과. LOCAL 4케이스는 컴파일만 확인.
```

DB 가 살아나면 기존 명령 그대로 `./gradlew test --tests kr.co.mindone.ems.pump.CtrlCmdServiceIT` 를 돌려 15케이스(기존 11 + LOCAL 4)를 확인한다.
새 케이스는 국가산단 3케이스의 복제라 매퍼 `<choose>` 분기와 `DEVICE == "LOCAL"` 문자열 비교가 실제로 도는지가 핵심이다.

## 다음 단계

### 적용 순서

1. 벤더에 공유: Java 가 `APPLIED` 외에 `REJECTED`·`FAILED`·`EXPIRED` 도 쓴다는 점, 추천 대기 중 5분마다 새 명령·`SUPERSEDED` 만료, 다음 판단 직전 승인의 이중 제어 가능성. (P2 자체는 13:28 판 코드로 확인됨.) 군산 설정은 `ctrl.cmd.consumer.enabled=true` 라 배포 직후부터 모드와 무관하게 판단 행 상태를 되돌려 쓴다.
2. 서비스 검증은 드라이 테스트로 완료(`CtrlCmdServiceIT`, 벤더 드롭·코드 변경 때마다 다시 돌린다). HTTP 계층·팝업·송신 경로는 로컬 Kafka 시나리오로 확인했다(2026-09-28). 배포 뒤에는 운영 브로커·SCADA 반영을 추천 모드에서 1건씩 확인한다.
3. 커밋. `main_5min.py` 는 벤더 드롭이라 별도로 판단한다.
4. 운영 DB 에 `docs/sql/gunsan_ctrl_cmd.sql` 1·2절 실행(추적 테이블, 빈 밸브 태그 행. 멱등).
5. **배포 전에 AI 운전모드를 분석(2) 또는 추천(1)으로 둔다**(결정 3-1). 그다음 BE·FE 배포.
6. `deploy/gunsan` 에 `ems-ctrl-5min` 컨테이너 추가(P8). `ems-epa-pre` 를 본뜨고 `TZ=Asia/Seoul`. 배포 설정 변경이라 착수 전 확인.
7. 현장 태그 확인·입력(워크플로우 15.1~15.2), 켜는 순서(15.3): 추천에서 펌프·밸브 1건씩 승인 → 운전 전환. 멈출 때는 분석으로.

### 필요한 정보

| 출처 | 항목 | 현재 |
|---|---|---|
| 벤더 | P2 상태 컬럼 UPDATE 허용 | ✅ 13:28 판 코드가 Java 의 `APPLIED` 기록을 전제 |
| 벤더 | P14 지방산단 컬럼 향후 | ✅ 2026-09-30 드롭에서 fallback 제어로 부활, 같은 날 제어 대상 확정(결정 9). 태그 `POC-8602` / `VVK-8601` / `VVK-8602`. 운영 DB 에 `LOCAL_*` 태그 행 3개 입력 필요(`docs/sql/gunsan_ctrl_cmd.sql` 2·3절) |
| 벤더 | 2026-09-30 드롭 선행조건 | `TB_CTRL_RULE_CFG` 의 `LOCAL_*` 규칙 8키 값, `TB_CTRL_CMD_RST(_SH)` 의 `LOCAL_*` 5컬럼, `TB_RAWDATA` 의 `891-365-FRI-8653`(오식도 유출) 적재 — 셋 다 **미확정**(개발 DB 연결 불가로 확인 못 함, `docs/gunsan-ctrl-5min-drop-review.md` §5 SQL) |
| 벤더 | 추천 승인 지연 시 `SUPERSEDED` 만료, 다음 판단 직전 승인 | 공유 필요 |
| 벤더 | 5분 판단 1회 실행 시간 | 미확인. 적재 :40 이 충분한지 근거 |
| 현장 | P3 펌프 주파수 쓰기 태그 | ✅ `CTR_AUTO_FREQ_TAG` 에 정의됨(2026-09-23 확인). 덤프 `891-365-PMC-4000~4003`, 운영 DB 값만 대조 |
| 현장 | P4 국가산단 개도 설정·OPENC/CLOSEC 펄스 태그, 순서, 펄스 폭 | 확정(2026-09-30): `891-365-POC-8603`, `891-365-VVK-8606`(상향), `891-365-VVK-8607`(하향), 개도값 → 펄스, 3초. 운영 DB 에 `NATIONAL_CLOSE_PULSE` 행 입력 필요(`docs/sql/gunsan_ctrl_cmd.sql` 2·3절) |
| 현장 | P5 태그 표기 형식 | `Fix32.GSSCADA.` 접두 여부. 기존 FREQ 로그와 대조 |
| 현장 | P6 게이트웨이 쓰기 허용 | **운전 전 필수**. 되읽기가 없어 허용이 없으면 `APPLIED` 여도 안 움직인다 |
| 현장 | P7 운영 DB 의 벤더 테이블 | `tb_ctrl_cmd_rst`, `tb_ctrl_rule_cfg` 존재 확인 |
| 현장 | 소수 주파수 수용 여부, 개도 계측 태그 | 정수 반올림 송신 중, `891-365-POI-8601`(기록용) |

### 남은 작업

- P13 승인자 식별: `localStorage.user` 를 그대로 기록한다. 세션 인증과 대조할지 결정.
- 밸브 확정 뒤 송신 시간 제약(결정 2-1) 재계산, 필요하면 군산 전용 송신 주기 프로퍼티화.
- 다음 벤더 드롭 때 워크플로우 14.1 대조.
