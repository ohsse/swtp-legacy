---
name: gunsan-epa-dummy
description: 군산 관망해석(EPANET MO 5분 모니터링·PRE 예측해석) 시뮬레이션을 돌릴 수 있도록 대상 DB 에 더미 계측값(TB_RAWDATA)·수요예측(TB_CTR_TNK_RST)·예측 매핑(TB_NODE_TAG)을 생성·적재·삭제한다. 기본 대상은 군산 개발서버 DB 이고 접속 JSON·키로 다른 DB 를 지정할 수 있다. "더미데이터 만들어줘", "개발서버에서 관망해석 돌게 데이터 채워줘", "해석이 계측값 없음으로 실패해", "시뮬레이션용 가짜 데이터", "TB_RAWDATA 비어서 MO 안 돌아", "더미 지워줘/연장해줘" 같은 요청에 사용. 운영 DB 적재·실측 이관·수요예측 모델 학습 데이터 생성에는 쓰지 말 것.
---

# 군산 관망해석 더미데이터 생성기

군산 개발서버 DB 는 계측 수집이 끊겨(2026-08-24 이후) 관망해석이 "해석에 필요한 계측값이 없습니다"로
실패한다. 이 스킬은 해석 엔진이 **DB 에서 읽는 것만** 그럴듯한 값으로 채워, MO(5분 모니터링)와
PRE(수요예측 기반 해석)가 끝까지 돌게 만든다.

도구는 `scripts/seed_dummy.py` 하나다. 새 스크립트를 짜지 말고 이것을 옵션으로 조절한다.
엔진이 무엇을 왜 요구하는지는 `references/engine-inputs.md` 에 있다 — 해석이 여전히 실패하거나
엔진 코드가 바뀌었을 때 읽는다.

## 1. 대상 DB 정하기

접속은 엔진과 같은 JSON 형식(`{키: {host, port, user, password, db}}`)을 쓴다.

| 상황 | 옵션 |
|---|---|
| 군산 개발서버 (기본) | 생략 → `epa/connections.gunsan.json` 의 `maria-ems-db-gu-test` (<internal-host> / ems_db) |
| 다른 DB | `--conn <json 경로> --conn-key <키>` |

사용자가 대상을 말하지 않았으면 기본(군산 개발서버)으로 진행한다. 다른 DB 를 원하면 접속 JSON 에
키를 하나 추가하도록 안내한다 — 비밀번호를 대화나 명령줄에 쓰게 하지 않는다.

운영 DB(<internal-host> 또는 db 이름 `EMS_DB`)는 스크립트가 거부한다. 더미가 실측과 섞이면 해석·예측·
제어 판단이 전부 오염되기 때문이다. `--allow-prod` 는 사용자가 운영 DB 임을 알고 명시적으로 요구할
때만 쓴다.

## 2. 실행

리포 루트에서 실행한다. 요청이 모호하면 먼저 `--dry-run` 으로 무엇이 들어갈지 보여준 뒤 적재한다.

```powershell
# 미리보기 (DB 에 쓰지 않음)
python .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py --dry-run

# 최근 3시간 채우고 MO·PRE 를 저장 없이 한 번 돌려 확인 — 가장 흔한 요청
python .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py --verify

# 특정 구간
python .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py --from "2026-09-28 08:00" --to "2026-09-28 12:00"

# 계속 흘려보내기 (5분 스케줄러를 켜 두고 볼 때). Ctrl+C 로 종료
python .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py --follow

# 지우기 (구간 지정)
python .claude/skills/gunsan-epa-dummy/scripts/seed_dummy.py --purge --from "2026-09-01"
```

주요 옵션: `--hours`(기본 3), `--pumps-on 1,3`(운전 펌프, 기본값이 실측 운전 조합), `--seed`(같으면 같은 값),
`--only raw|pred|mapping`, `--replace-pred`, `--marker`(기본 `DUMMY_SIM`).

`--follow` 는 끝나지 않는 프로세스다. 에이전트에서 돌릴 때는 백그라운드로 실행하고, 사용자에게
멈추는 방법을 알려준다.

## 3. 무엇이 들어가나

| 테이블 | 내용 | 기존 데이터와 겹치면 |
|---|---|---|
| `TB_RAWDATA` | 엔진 태그 전부(약 33개) × 1분. `SERVER='DUMMY_SIM'`, `QUALITY='100'` | **실측 행은 보존**, 우리 마커 행만 갱신 |
| `TB_CTR_TNK_RST` | 5분 경계마다 `Q2_Predict`·`Q7_Predict` (같은 RGSTR_TIME). 테이블에 있는 컬럼만 쓴다 — 개발서버는 `VALUE_5min~6h` 가 없는 옛 스키마 | 건너뜀 (`--replace-pred` 면 덮어씀) |
| `TB_NODE_TAG` | 나운(배)→Q2_Predict, 오식도(배)공업→Q7_Predict | 비어 있을 때만 채움. 다른 값이면 경고만 |

값은 개발서버 DB 실측(2026-08-23) 평균 수준에 하루 주기 변동과 노이즈를 얹는다. dev DB 에 아예
없는 태그 몇 개는 추정값이며 스크립트 `PROFILES` 에 `(추정)` 으로 표시돼 있다. `(seed, 태그, 시각)` 으로만 정해지므로
구간을 나눠 넣거나 다시 돌려도 같은 값이 나온다. 태그 목록은 엔진 모듈에서 import 하므로 엔진에
태그가 늘면 자동으로 따라가되, 값 모양(`PROFILES`)이 없는 태그는 경고 후 건너뛴다 — 그 경고가
나오면 `PROFILES` 에 한 줄 추가한다.

## 4. 결과 확인과 보고

스크립트가 끝에 "적재 확인"으로 엔진과 같은 창(기준시각 − 600초)에서 태그가 몇 개 잡히는지 찍는다.
`--verify` 를 줬으면 MO·PRE 엔진을 `--snapshot --no-save-db` 로 돌린 결과(exit 코드와 마지막 줄)도 나온다.
검증은 로컬 파이썬에서 엔진을 돌리므로 `pymysql`·`wntr` 가 필요하고, 엔진이
`epa/epanet_gunsan/logs/{mo,pre}_YYYYMMDD.txt` 를 남긴다(추적 대상 아님). 사용자가 원치 않으면 지운다.
`wntr` 의 "Not all curves were used" 경고는 무해하다.

사용자에게는 다음을 짧게 보고한다.
- 대상 DB(호스트/DB명), 구간, 적재 행 수
- 태그 커버리지(n/n)와 검증 결과(MO/PRE 성공 여부, 실패면 마지막 오류 줄)
- 해석을 실제로 돌리는 방법 — 화면의 해석 버튼, 또는 dev 서버에서 `conf/epa/config.py` 의
  `SCHEDULER_ENABLED=True` 후 `ems-py-api` 재기동(`restart`)
- 더미 유효기간: 엔진은 기준시각 이전 600초만 본다(dev 서버 설정은 86400초). 더미의 마지막 시각을
  지나 그 창을 벗어나면 다시 "계측값 없음"이 된다 → 재실행하거나 `--follow`
- 지우는 명령

## 5. 알아둘 함정

- **PRE 는 MO 결과를 요구한다.** 루프 모드 PRE 는 같은 5분 경계의 MO 결과(`TB_TOT_ALG FLG='mo'`)가
  있어야 저장한다. 더미만으로는 부족하고 MO 가 먼저 한 번 저장돼야 한다. `--verify` 는 저장하지 않는
  snapshot 이라 이 조건을 우회한다.
- **파티션.** `TB_RAWDATA` 는 월 단위 RANGE 파티션이다. 해당 월 파티션이 없으면 삽입이 실패하고
  스크립트가 안내 메시지를 낸다. 파티션 추가는 DBA 몫이니 사용자에게 알린다.
- **나운(배) 태그가 엔진마다 다르다.** MO 는 `FRI-8600`, PRE·SI 는 `FRI-8601`. 둘 다 넣는다.
- **삭제는 태그+시각 조건으로.** `WHERE SERVER='DUMMY_SIM'` 만 걸면 인덱스가 없어 수 분씩 걸린다.
  `--purge` 는 이미 그렇게 한다. `TB_CTR_TNK_RST` 는 마커 컬럼이 없어 구간 안의 Q2/Q7 예측을 전부
  지운다 — 개발서버엔 예측 서비스가 없어 문제없지만, 다른 DB 면 구간을 좁게 준다.
- 기존 `SERVER='DUMMY_DEV'` 행(2026-09-21 수동 주입, 4개 태그)은 다른 마커라 건드리지 않는다.
