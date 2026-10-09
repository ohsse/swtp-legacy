# 현장(테넌트)별 반출본 만들기

군산 반출본(`deploy/gunsan`, `deploy/gunsan-dev`)을 본으로 삼아 다른 지자체 현장의
반출본을 만드는 절차다. 군산에서 이미 검증된 것만 적었고, 아직 해보지 않은 부분은
그렇다고 표시했다.

> **먼저 읽을 것**: 이 문서는 "빈 서버에 새 현장을 올리는 법"이다.
> - 이미 만들어 둔 현장을 다시 말아 내보내는 반복 작업 → **§7**
> - **서비스 하나만 고쳐** 올리는 경우(프런트 한 곳 수정 등) → **§7 「서비스 하나만 고칠 때」**
> - **이미 돌고 있는 시스템을 컨테이너 스택으로 대체**하는 경우 → **부록 A**
>   (포트·DB·Kafka 를 가동 중인 앱과 공유하게 되어 위험의 종류가 다르다)
> - **가동 중인 스택을 살려둔 채 새 버전을 나란히 올려 비교**하는 경우 → **부록 B**
>   (대체보다 위험이 낮지만, 같은 DB 에 양쪽이 쓰지 않도록 막는 것이 핵심이다)

---

## 1. 반출본 한 벌의 구성

`build-and-save.ps1` 이 만드는 `dist\<현장>-<TAG>.tar.gz` 안에는 이것들이 들어간다.

| 항목 | 내용 | 출처 |
|---|---|---|
| `images.tar` | 앱 이미지를 한 tar 로 save (군산 운영·섀도우 7종, 개발서버 6종) | 빌드 |
| `images.txt` | 적재 대조용 태그 목록 (BOM 금지) | 스크립트 생성 |
| `docker-compose.*.yml` | 현장 스택 정의 | `deploy/<현장>/` |
| `.env` | 태그·DB·포트. 빌드에 쓴 값으로 자동 고정 | `deploy/<현장>/.env` + 치환 |
| `load-and-up.sh` / `.ps1` | 서버 적용 스크립트 | `deploy/<현장>/` |
| `conf/` | epa·inp-opt 설정 (마운트됨) | 운영=번들 보관 / 개발=리포 원본 |
| `conf/epa/inp/*.inp` | EPANET 기준 관망 모델 | `epa/inp/` |
| `conf/predict/db_*connections.json` | (군산만) 수요예측 읽기·쓰기 DB 접속정보 | `deploy/<현장>/conf/predict/` |
| `conf/predict/{models,runs}/` | (군산만) 수요예측 학습 산출물 | `ems_gu_predict/` |
| `seed/originals/*.inp` | (개발서버만) DB 레코드가 가리키는 물리 INP | `.data/files/originals/` |

> **수요예측(`ems-predict`)은 군산 전용이다.** 다른 현장 반출본에는 넣지 않는다 —
> 모델·태그리스트(`ems_gu_predict/taglist/GU_taglist.xlsx`)·적재 테이블이 전부 군산
> 관망에 맞춰져 있어 그대로는 다른 현장에서 의미가 없다. `$Profiles.<대상>.IncludePredict`
> 로 대상별 포함 여부가 갈린다(군산 `prod`/`shadow` 만 `$true`).

배경지도 타일은 **이 번들에 들어가지 않는다.** `-TilesOnly` 로 따로 뽑아
최초 1회만 이관한다. 앱은 매번 다시 말지만 타일은 몇 달 그대로여서, 한 tar 에 담으면
반출할 때마다 수백 MB~수십 GB를 다시 옮기게 되기 때문이다.

---

## 2. 현장마다 갈리는 값 — 전체 목록

바꾸는 **비용**에 따라 네 계층으로 나뉜다. 위로 갈수록 비싸다.

### 2-1. 빌드 타임에 이미지에 박힌다 (바꾸려면 이미지를 다시 말아야 한다)

| 값 | 위치 | 무엇을 정하나 |
|---|---|---|
| `$area` | `fe/src/main.js:88` | 대시보드 컴포넌트(`router/Route.js`)와 자율운영 포털 포트(`router/index.js` 의 `getServerPort`) |
| `EMS_API_UPSTREAM_PORT` | `build-and-save.ps1 -EmsApiPort` → `fe/Dockerfile.gunsan-prod` | 프런트 nginx 가 프록시할 **컨테이너** 포트. 스프링 프로파일이 정한다 |
| `INP_EDITOR_PORT` | `build-and-save.ps1 -InpEditorPort` | 새 탭으로 여는 inpEditor 의 **호스트** 포트. 브라우저가 직접 붙는다 |
| `SSO_BYPASS` | `$Profiles` 의 `SsoBypass` | 자율운영 포털이 없는 환경에서 루트 진입 리다이렉트 우회 |
| `VITE_PROFILE` | `build-and-save.ps1` 의 `$Images` | inpEditor 배경지도. `dev` 면 vworld(인터넷), 그 외는 `/newEMap/`(타일서버) |
| `PROFILE` | 같은 곳, inp-editor-be | `resources-env/<profile>` 오버레이. 현재 `dev`/`gosan`/`ubuntu` 3종만 있다 |

**서버 IP 는 여기 없다.** 상대경로 전환(`$apiURL="/ems-api"`, `$pythonURL="/epa"`) 이후
프런트는 자기 오리진을 부르고 컨테이너 안 nginx 가 서비스명으로 넘긴다. IP 가 바뀌어도
다시 말 필요가 없다.

### 2-2. 마운트로 주입한다 (파일만 바꾸고 컨테이너 재생성)

| 파일 | 컨테이너 경로 | 담긴 현장 종속 값 |
|---|---|---|
| `conf/epa/config.py` | `/app/config.py` | **해석 엔진 선택(`EPA_ENGINE`)**, INP 파일명 3종, `DEFAULT_CONN_KEY`, 테이블명, 스케줄러 on/off |
| `conf/epa/connections.json` | `/app/connections.json` | EPA 가 붙을 DB 접속 정보 |
| `conf/inp-opt/config.json` | `/app/conf/config.json` | 최적화 엔진 DB·경로, **펌프 성능곡선 엔진 선택(`pump_curve.engine`)** |
| `conf/epa/inp/*.inp` | `data/files` 경유 | 현장 관망 모델 |
| `conf/predict/db_connections.json` | `/app/configs/db_connections.json` | (군산) 수요예측이 **읽는** DB |
| `conf/predict/db_upload_connections.json` | `/app/configs/db_upload_connections.json` | (군산) 수요예측이 **쓰는** DB + `table` |
| `conf/predict/{models,runs}/` | `/app/models`, `/app/runs` | (군산) 학습 산출물 |

epa 는 환경변수 설정을 지원하지 않는다(파일을 CWD 상대경로로 읽는다). 그래서 마운트가
유일한 수단이고, 이 두 파일이 **현장 종속 설정의 단일 교체 지점**이다.

`ems-predict` 가 마운트를 쓰는 이유는 epa 와 다르다. 이쪽은 환경변수도 CLI 인자도 다 되지만,
(1) 비밀번호를 이미지에 굽지 않기 위해서고 (2) 모델을 바꿀 때 1.8GB 이미지를 다시 말지
않기 위해서다. 폐쇄망에서는 후자가 특히 크다 — 4MB 파일 교체와 tar 재반출의 차이다.
실제로 `ems_gu_predict/.dockerignore` 가 `configs/db*connections*.json`, `models/`, `runs/`,
`logs/` 를 전부 이미지에서 제외한다.

> **`conf/predict/db_connections.json` 에는 `${VAR}` 를 못 쓴다.** 짝인
> `db_upload_connections.json` 은 되는데 이쪽만 안 되는 비대칭이 있다 —
> `config.db_connection_params()` 가 JSON 값을 그대로 가져다 쓰기 때문이다.
> `.env` 를 참조하려다 `"${DB_PASSWORD}"` 라는 문자열로 접속을 시도하게 된다.

### 2-3. `.env` 로 준다 (재기동이면 된다)

`TAG`, `DB_HOST`/`DB_PORT`/`DB_NAME`/`DB_USER`/`DB_PASSWORD`,
호스트 포트 6종, `FLYWAY_ENABLED`, `TILE_TAG`/`TILE_PORT`.

호스트 포트는 `EDITOR_FE_PORT` **하나만 예외**다. 그 값이 프런트 이미지에 박히므로
바꾸려면 `-InpEditorPort` 로 다시 말아야 한다. 나머지는 자유롭게 바꿔도 된다.

### 2-4. compose 에 박혀 있다 (파일을 고쳐야 한다)

| 값 | 예 | 비고 |
|---|---|---|
| `SPRING_PROFILES_ACTIVE` | `"gu"` | 운영 compose. 개발서버는 `"dev"`. **재빌드 불필요** — 12개 프로파일이 war 에 다 들어 있다 (§4-2) |
| `DSTRB_RESISTANCE_LINKID` / `DSTRB_RESISTANCE_NODEID` | `"45"` / `"Bks-2496"` | **개발서버 전용.** 운영(`gu`)은 프로퍼티에 있어 불필요 — 아래 주 참고 |
| `name:` | `swtp-gunsan` | 프로젝트명. 한 서버에 두 현장을 올릴 때 반드시 달라야 한다 |
| `container_name:` | `swtp-gunsan-ems-front` | 7곳 (타일 포함) |
| 네트워크명 | `gunsan-net` | |
| 이미지 네임스페이스 | `swtp-gunsan/...` | compose · `load-and-up` · `build-and-save` 세 곳 |

> **`DSTRB_RESISTANCE_*` 를 개발서버에만 주는 이유**
>
> 운전현황분석의 성능곡선은 관망해석 결과에서 링크 1개·노드 1개를 읽는다
> (`DrvnService.systemResistanceCurves` → `TB_FR_SI_VAL` / `TB_FP_SI_VAL`).
> 그 ID 는 현장마다 다르고, 값은 `dstrb.resistance.linkId` / `dstrb.resistance.nodeId`
> 프로퍼티에서 온다. 코드 기본값은 고산(`10` / `고산(정)유출`)이고
> 군산 운영값 `45` / `Bks-2496` 은 `application-gu.properties` 에 있다.
>
> 문제는 **개발서버가 `gu` 가 아니라 `dev` 프로파일로 뜬다**는 점이다(스케줄러·Kafka 를
> 끄기 위한 의도적 선택, §2-4 첫 줄). `application-dev.properties` 는 고산 설정이고,
> 루트 `docker-compose.yml` 이 같은 `dev` 로 고산 덤프를 보기 때문에 그 파일을 군산 값으로
> 바꿀 수도 없다. 그래서 개발서버 compose 에서만 환경변수로 덮는다.
> Spring Boot 완화 바인딩이 `DSTRB_RESISTANCE_LINKID` → `dstrb.resistance.linkId` 로 이어준다.
>
> 새 현장에 개발서버를 둘 때도 같은 판단이 필요하다 — **프로파일이 `dev` 면
> `dstrb.*` 는 전부 고산 값**이라는 점을 먼저 확인할 것.

---

## 3. 현장 대조표

"현장"이 세 가지 표기로 갈린다. 새 현장을 넣을 때 **셋을 모두** 채워야 한다.
아래는 리포에 실제로 있는 값이다(`be/src/main/resources/application-*.properties`,
`fe/src/router/index.js` 의 `getServerPort`).

| 현장 | `$area` (프런트) | 스프링 프로파일 | 포털 포트 | 운영 DB |
|---|---|---|---|---|
| 고산 | `gosan` | `gs` | 10011 | <internal-host> |
| 군산 | `gunsan` | `gu` | 10021 | <internal-host> |
| 산성 | `sanseong` | `ss` | 10031 | <internal-host> |
| 부안 | `buan` | `ba` | 10041 | <internal-host> |
| 구미 | `gumi` | `gm2` | 10111 | <internal-host> |
| 해평 | `haepyeong` | `hp2` | 10121 | <internal-host> |
| 학야 | `hakya` | `hy2` | 10131 | <internal-host> |
| 고령 | `goryeong` | `gr` / `gr1` | 10141 | <internal-host> / <internal-host> |
| 자인 | `jain` | `ji2` | 10151 | <internal-host> |
| 운문 | `unmun` | `wm` | 10161 | <internal-host> |
| (개발) | — | `dev` | — | 9000 포트 |

**주의할 점 두 가지.**

- **운영 프로파일의 `server.port` 는 전부 `10014` 다.** `dev` 만 `9000` 이다.
  따라서 `-EmsApiPort` 는 운영이면 10014, 개발서버면 9000 으로 사실상 고정이다.
- **고령은 `gr` 과 `gr1` 두 벌이 있고 properties 상으로는 DB IP 만 다르다.** 그런데
  **동작이 같지 않다** — `gr` 은 신버전 Kafka 화이트리스트에 있고 `gr1` 은 두 목록
  어디에도 없어 구버전 Kafka 로 떨어진다(§4-2). 어느 쪽이 현행인지 코드로는 판단이
  안 되니 고령 반출본을 만들 때 담당자에게 확인할 것.
  구미도 `application-gm2.properties` 의 DB(`<internal-host>`)와 `fe/src/main.js` 주석의
  API 주소(`<internal-host>`)가 다르다 — 주석이 오래된 것으로 보이나 확인이 필요하다.

---

## 4. 새 현장 반출본 만들기 — 체크리스트

부안(`buan` / `ba`)을 예로 든다. 순서대로 하면 된다.

### 4-1. 현장 코드 3종 확정

§3 표에서 `$area`, 스프링 프로파일, 포털 포트를 확인한다. 표에 없는 신규 현장이면
`be/src/main/resources/application-<코드>.properties` 와
`fe/src/views/DashBoard/MainDashBoard_<area>.vue` 를 먼저 만들어야 한다.
**대시보드 컴포넌트가 없으면 `Route.js` 의 `default` 로 빠져 고산 화면이 뜬다** —
빌드는 통과하고 화면에서야 드러나는 종류의 실수다.

### 4-2. 백엔드 프로파일 — 먼저 "새로 만들 것인가"를 정한다

이 리포에는 프로파일 메커니즘이 **두 가지**이고 비용이 정반대다. 헷갈리지 말 것.

| | `be` (EMS 백엔드) | `inpEditor/BE` |
|---|---|---|
| 방식 | 12개 프로파일이 war 에 전부 구워져 있고 런타임에 고른다 | Gradle 이 `resources-env/<profile>/` 을 `resources/` 위에 덮어써 jar 를 만든다 |
| 고르는 곳 | compose 의 `SPRING_PROFILES_ACTIVE` | `build-and-save.ps1` 의 `PROFILE=ubuntu` |
| 바꾸는 비용 | **재빌드 없음.** compose 고치고 재기동 | **재빌드 필요** |
| 현재 종류 | `ba gm2 gr gr1 gs gu hp2 hy2 ji2 ss wm dev` | `dev` / `gosan` / `ubuntu` (반출본은 전부 `ubuntu`) |

`be` 는 `application.properties:1` 의 `spring.profiles.active=dev` 가 기본값이고,
compose 의 환경변수가 그것을 이긴다.

```yaml
# deploy/gunsan/docker-compose.prod.yml:35
SPRING_PROFILES_ACTIVE: "gu"
```

#### 먼저 판단: 새 프로파일이 정말 필요한가

**DB 주소·계정만 다르다면 새로 만들지 말 것.** 기존 프로파일을 그대로 쓰고 환경변수로
덮어쓰는 편이 안전하다. 개발서버 스택이 이미 이 방식이다.

```yaml
SPRING_PROFILES_ACTIVE: "dev"
SPRING_DATASOURCE_URL: "jdbc:mariadb://${DB_HOST}:${DB_PORT}/${DB_NAME}"
SPRING_DATASOURCE_USERNAME: "${DB_USER}"
SPRING_DATASOURCE_PASSWORD: "${DB_PASSWORD}"
```

**운전 상수까지 다르면** 새 프로파일이 필요하다. `application-gu.properties` 를 열어 보면
DB·Kafka 뿐 아니라 펌프 가동 대수(`dstrb.pump.level`), 예측 전력 계수
(`dstrb.prdct.pwrCal.idx`), 수두 손실 상수(`dstrb.headLoss.cal`), 분기 태그 목록
(`dstrb.prdct.dstrbId`) 이 전부 들어 있다. 현장 도메인 데이터라 복사로 해결되지 않고
담당자에게 받아야 한다.

#### 새 프로파일을 만들 때 — `@Profile` 게이트 13곳을 반드시 검토

**properties 파일만 만들면 끝나지 않는다.** 자바 코드가 프로파일 이름을 직접 나열하고
있고, 대부분이 블랙리스트(`!a & !b & ...`)라서 **새 이름은 모든 게이트를 "켜짐"으로
통과한다.**

| 대상 | 표현식 형태 | 새 이름의 기본값 |
|---|---|---|
| `common/SchedulerService` | `!dev` | **켜짐** ⚠ |
| `pump/PumpScheduler` | `!dev && !gm & !hp & …` | **켜짐** |
| `drvn/Drvn{Config,Controller,Mapper,Service}` | `!gm & !hp & …` | **켜짐** (자율운영) |
| `kafka/{KafkaConfig,KafkaConsumerService,KafkaProducerTasks}` (구버전) | `!dev & !gm2 & … & !ss` | **켜짐** ⚠ |
| `kafka/consumer/*`, `kafka/producer/*` (신버전) | 화이트리스트 `{gm2,hy2,hp2,ji2,gr,wm,gs,gu,ba,ss}` | **꺼짐** |

실제 사고로 이어지는 것이 둘이다.

- **`SchedulerService` 가 자정에 데이터를 지운다.** `oldDataDeleteTask` 3종이
  `00:00:00` / `00:00:10` / `00:00:20` 에 raw 데이터와 EPANET FP·FR 을 삭제한다
  (`SchedulerService.java:115-139`). 새 프로파일로 개발 덤프 DB 에 붙이면 하루 뒤
  데이터가 사라진다. **`dev` 만 이게 꺼져 있고**, 개발서버 compose 가 `dev` 를 쓰는
  이유가 바로 이것이다.
- **Kafka 구현이 두 벌이고 신·구가 정확히 상보 관계다.** 새 이름은 신버전 화이트리스트에
  없으니 구버전으로 떨어지는데, 구버전 `KafkaConfig` 는
  `@Value("${spring.kafka.bootstrap-servers}")` 를 요구한다. 그 키가 properties 에
  없으면 **기동 자체가 실패한다.**

> **`gr1` 은 두 목록 어디에도 없다.** `gr` 은 신버전 Kafka 인데 `gr1` 은 구버전으로
> 떨어진다. 같은 고령인데 구현이 갈리는 셈이라, §3 의 "어느 쪽이 현행인지 확인" 과
> 함께 짚어야 한다.

#### 그 밖에 알아둘 것

- **`SPRING_PROFILES_ACTIVE` 에 콤마로 여러 개를 주면 안 된다.** 여러 클래스에
  `@PropertySource("classpath:application-${spring.profiles.active}.properties")` 가
  붙어 있어 경로가 깨지고 기동에 실패한다. 항상 한 개만.
- **운영 프로파일의 `server.port` 는 전부 `10014`, `dev` 만 `9000`** 이다. 이 값이
  `-EmsApiPort`(프런트 nginx 의 프록시 대상)와 compose `ports:` 오른쪽과 **세 곳 모두**
  같아야 한다.
- `.env` 의 `DB_*` 는 운영 스택에서 `inp-editor-be` 전용이다. `be` 는 프로파일에 박힌
  값을 쓴다(위 환경변수 오버라이드를 넣지 않는 한).

#### `inpEditor/BE` 오버레이를 새로 만들 때

```gradle
# inpEditor/BE/editor/build.gradle:99-107
ext.profile = (!project.hasProperty('profile') || !profile) ? 'common' : profile
sourceSets.main.resources.srcDirs "src/main/resources-env/${profile}"
```

`resources-env/<profile>/application.yaml` 이 `resources/application.yaml` 을 덮어쓴다
(`duplicatesStrategy = INCLUDE`). 새로 만들었다면 `build-and-save.ps1` 의
`Args=@('PROFILE=ubuntu')` 를 함께 바꿔야 한다. 미지정 시 `common` 으로 가는데 그
디렉터리가 없어 기본 `resources/` 만 쓰인다.

### 4-3. 프런트 `$area` 교체

`fe/src/main.js:88` 한 줄이다.

```js
app.config.globalProperties.$area = 'buan';
```

`fe/Dockerfile.gunsan-prod:38` 의 검증 문구도 함께 바꿔야 빌드가 통과한다.

```dockerfile
grep -qF "area = 'buan'" src/main.js || { echo "ERROR: ..."; exit 1; }
```

> 이 검증은 일부러 넣어 둔 것이다. 예전에는 sed 로 주소를 박아 넣었는데,
> sed 가 빗나가도 빌드가 통과해 서버에서야 증상이 나타났다. 지금은 "기대한 소스가
> 맞는지"만 확인하고 즉시 깨뜨린다.
>
> **한 리포에서 두 현장을 동시에 말 수 없다는 뜻이기도 하다.** `$area` 가 전역 상수
> 한 줄이라 현장을 바꿔 가며 순차로 빌드해야 한다. 이걸 피하려면 §8 을 볼 것.

### 4-4. EPA 설정 2종 만들기

`epa/config.gunsan.py` 와 `epa/connections.gunsan.json` 을 복사해 부안본을 만든다.

```bash
cp epa/config.gunsan.py        epa/config.buan.py
cp epa/connections.gunsan.json epa/connections.buan.json
```

`config.buan.py` 에서 고칠 것:

- `INP_FILE_PATH` / `INP_SI_FILE_PATH` / `INP_MO_FILE_PATH` — 부안 관망 INP 파일명
- `DEFAULT_CONN_KEY` — `connections.buan.json` 의 키와 **글자까지 같아야 한다**
- `SCHEDULER_ENABLED` — 운영은 `True`, 검토 단계는 `False`
- `NODE_TABLE` / `LINK_TABLE` / `TOT_TABLE` — 보통 그대로

`INP_SI_FILE_PATH` / `INP_MO_FILE_PATH` 의 **파일명은 inp-editor-be 의
`editor.apply.target-file-names` 설정과 반드시 일치해야 한다.** inpEditor 의 "적용"
버튼이 그 이름으로 덮어써야 해석엔진에 반영되기 때문이다. 이름이 어긋나면 적용해도
아무 일이 일어나지 않는다(에러도 안 난다).

BE 쪽 설정은 환경변수 `EDITOR_APPLY_SI_FILE_NAME` / `EDITOR_APPLY_MO_FILE_NAME` 으로
현장별 오버라이드가 가능하다(기본값은 고산의 `gs_inp_si.inp` / `gs_inp_mo.inp`).
파일명만 바꾸는 것이라면 `resources-env/<profile>` 을 새로 만들 필요가 없다 — 이미지는
한 벌(`ubuntu`)로 두고 `.env` 만 현장별로 관리한다.

**맞출 대상은 엔진에 따라 다르다.** BE 의 "적용"은 언제나 `target-file-names` 에 적힌
이름으로 덮어쓰므로, 그 이름이 *지금 켜져 있는 엔진이 읽는 파일*이어야 한다.

| `EPA_ENGINE` | 해석엔진이 읽는 설정 | BE 가 써야 할 이름 |
|---|---|---|
| `'gosan'` | `INP_SI_FILE_PATH` / `INP_MO_FILE_PATH` (두 파일) | 두 환경변수에 각각 그 파일명 |
| `'gunsan'` | `GUNSAN_INP_PATH` **한 파일**(`INP_*` 3종은 안 읽는다) | **두 환경변수 모두 그 한 파일명** |

군산처럼 한 파일로 운영하는 현장은 두 환경변수에 **같은 값**을 넣으면 된다. 중복은 BE 가
하나로 접어 그 파일 하나만 교체한다(`InpFileService.requireApplyTargets`). 예를 들어
`GUNSAN_INP_PATH = './inp/epa_model.inp'` 라면:

```properties
EDITOR_APPLY_SI_FILE_NAME=epa_model.inp
EDITOR_APPLY_MO_FILE_NAME=epa_model.inp
```

> 군산 설정의 `INP_SI_FILE_PATH` / `INP_MO_FILE_PATH` 가 아직 `gs_inp_*.inp` 인 것은
> 엔진을 `'gosan'` 으로 되돌릴 때를 위한 참고값이다. **여기에 BE 를 맞추면 적용은
> 성공하는데 군산 엔진은 `epa_model.inp` 를 계속 읽어 아무 변화가 없다.**

#### 해석 엔진 고르기 — `EPA_ENGINE`

`epa/` 안에는 관망해석 구현이 **두 벌**이고, `config.py` 의 `EPA_ENGINE` 한 줄이
둘 중 어느 쪽이 요청을 처리할지 정한다(`epa/app/services/engine.py`).

| 값 | 구현 | 성격 |
|---|---|---|
| `'gosan'` (기본) | `epa/app/services/epa_service.py` | 고산 전용. 펌프 태그·관말 보정계수가 코드에 박혀 있다 |
| `'gunsan'` | `epa/app/services/epa_service_gunsan.py` → `epa/epanet_gunsan/` | 군산 전용. 밸브 개도율 보정·한글 ID 새니타이즈가 들어 있다 |

**키가 없으면 `'gosan'` 으로 본다.** 기존 현장 설정에 이 줄을 넣지 않아도 지금까지와
똑같이 동작한다. 새 현장을 만들 때도 고산 계열이면 건드릴 필요가 없다.

`'gunsan'` 으로 둘 때만 아래 `GUNSAN_*` 값이 쓰인다. 전부
`deploy/gunsan/conf/epa/config.py` 에 주석과 함께 들어 있다.

| 키 | 뜻 |
|---|---|
| `GUNSAN_INP_PATH` | 군산 관망 모델. `/app/inp` 아래여야 한다 (아래 함정 참조) |
| `GUNSAN_VALVE_MODEL_PATH` | 국가산단밸브 개도율→저항 보정곡선. 이미지에 함께 복사된다 |
| `GUNSAN_PRESSURE_UNIT` | `legacy_div10` 고정. 보정곡선의 `pressure_units_per_head_m` 과 **불일치하면 기동이 아니라 요청이 실패한다** |
| `GUNSAN_VALVE_MODE` | `opening`(기본) / `measured` / `open` / `inp` |
| `GUNSAN_REFERENCE_HZ`, `GUNSAN_FALLBACK_SEC` | 펌프 기준 Hz, 계측값 과거 허용 초 |
| `GUNSAN_LOCK_TIMEOUT_SEC` | 군산 엔진은 한 번에 하나만 돈다. 대기 상한(초), 초과 시 503 |
| `GUNSAN_MO_BATCH_MAX_STEPS` | `mo/batch` 1회 요청의 최대 스텝 수 |

> **왜 하나만 도는가**: 군산 엔진은 EPANET 에 한글 경로를 숨기려고 `os.chdir` 를 쓰는데
> 그것이 프로세스 전역 상태다. 앱은 `--threads 4` 로 도므로 어댑터가 락으로 직렬화한다.
> 고산 구현에는 없던 제약이다.

> **함정 — 군산 INP 는 세 관문을 통과해야 한다.**
> 1. `epa/.dockerignore` 가 `inp/` 밖의 `*.inp` 를 이미지에서 뺀다 →
>    `epa/epanet_gunsan/` 에 두면 **컨테이너 안에 없다.**
> 2. compose 가 `data/files` 를 `/app/inp` 에 덮어쓴다 → 이미지에 넣어도 **가려진다.**
> 3. 결국 실물이 놓여야 할 곳은 `data/files/` 다. 운영은 `load-and-up.sh` 가
>    `conf/epa/inp/` 에서 복사하고, 그 `conf/epa/inp/` 는 `build-and-save.ps1:301-305`
>    가 `epa/inp/` 에서 복사한다. **따라서 리포 쪽 기준 위치는 `epa/inp/` 다.**
>
> 개발서버 스택은 `./.data/files` 가 `/app/inp` 이므로 거기에도 같은 파일을 둔다.
> 파일이 없으면 요청 시 `군산 관망 INP 파일을 찾을 수 없습니다` 로 즉시 드러난다
> (EPANET 오류로 둔갑하지 않게 어댑터가 미리 확인한다).

### 4-5. 최적화 엔진 설정

`inpEditor/PY/roughness_ga_optimizer/config.<현장>.json` 을 만든다.
현재 있는 것은 `dev` / `gosan` / `local` / `prob` 4종이다.

#### 펌프 성능곡선 엔진 고르기 — `pump_curve.engine`

`EPA_ENGINE` 과 같은 구조가 성능곡선에도 있다. 현장마다 펌프 태그·대수·유량 태그 구성이
달라 구현이 두 벌이고, 설정 한 줄이 어느 쪽을 쓸지 정한다.

| 값 | 모듈 | 현장 |
|---|---|---|
| 없음 / `gosan` | `pump_curve_update.py` | 고산 (11대, `701-367-*`, 유량 2태그 합산) |
| `gunsan` | `pump_curve_update_gunsan.py` | 군산 (4대, `891-365-*`, 유량 단일 태그, 주파수 필터) |

```json
"pump_curve": {
  "engine": "gunsan",
  "rawdata_table": "TB_RAWDATA",
  "power_price_table": "TB_POWER_PRICE"
}
```

**키가 없으면 고산이다.** 기존 현장 설정은 손대지 않아도 지금까지와 똑같이 동작한다.
아는 값이 아니면(오타 등) `api_server` 가 **기동 시점에 죽는다** — 군산 현장에 고산 엔진이
조용히 떠서 엉뚱한 태그를 조회하면 결과 숫자만 보고는 알아채기 어렵기 때문이다.
선택된 엔진은 기동 로그에 `[pump-curve] engine=... module=...` 로 한 줄 남는다.

선택은 `pump_curve_engine.py` 가 하고, 두 모듈은 같은 함수 이름·같은 시그니처를 노출하므로
`api_server` 는 어느 쪽인지 모른다(`epa/app/services/engine.py` 와 같은 방식).

#### 목표 주파수(Hz) — 가변속 펌프 현장

군산 엔진은 펌프별 목표 주파수 ±0.5Hz 안의 데이터만 회귀에 쓴다. 이 값은 사용자가 입력하는
것이 아니라 **`TB_PUMP_CAL` 의 `C_ORD=2` 행 `PUMP_COMB`** 에 이미 들어 있다(가변속
`PUMP_TYP=2` 펌프에만 순서대로 대응, 정속은 자리를 차지하지 않는다).

경로는 이렇게 이어진다.

1. `PumpCombStatRepository.buildPumpHz` 가 `PUMP_TYP` 과 짝지어 `"2:27,3:29"` 로 조립
2. 운영 현황 응답(`GET /pump-combinations/operation-stats`)의 `pumpHz`
3. 프런트(`inpEditor/FE/front/src/web/pages/perFromCurveManage/PerformCurveManage.jsx`)가
   그리드는 기존대로 그리고, 갱신/추출 호출 때 이 값을 **그대로 되돌려 보냄**
   (갱신은 쿼리 `?pumpHz=`, 추출은 본문 `pumpHz`)
4. BE 가 파이썬으로 전달 → 군산 엔진이 ±0.5Hz 필터

프런트가 값을 해석하지 않고 되돌려 보내기만 하는 이유는, 펌프번호를 붙이는 규칙
(가변속만 순서대로)이 `PUMP_TYP` 을 아는 BE 한 곳에만 있게 하려는 것이다.

값이 없으면(미입력 조합, 정속 전용 현장) 주파수 조건 없이 분석한다 — 오류가 아니다.

> ⚠️ `C_ORD=2` 의 `PUMP_COMB` 을 **지우면 안 된다.** 과거 이 값을 "잔재 값"으로 보고 비우는
> 정리 스크립트를 준비했다가 회수했다. 경위는
> `inpEditor/BE/editor/doc/sql/TB_PUMP_CAL_normalize_cord2_pump_comb.sql` 상단 참조.

#### 군산 펌프곡선 엔진 재드롭 체크리스트

군산 성능곡선 모듈은 벤더가 통째로 새로 준다. 새 파일을 받으면 아래를 **매번 다시** 적용한다
(드롭마다 같은 자리가 되돌아온다).

| 확인할 것 | 벤더 원본 상태 | 적용할 교정 |
|---|---|---|
| 파일명 | `pump_curve_update_gs.py` | `pump_curve_update_gunsan.py` (이 저장소에서 `gs` 는 **고산**이다) |
| 설정 로딩 | `connections.json` + `DEFAULT_CONN_KEY` | `from config_path import load_config, resolve_config_path` |
| `apply_table_config()` | 없음 | 복원 — **없으면 `api_server` 가 기동 즉시 `AttributeError`** |
| `build_result` 계수 키 | `P_SQRT_MUL_VAL=a`, `P_ADD_VAL=c` (뒤집힘) | `P_ADD_VAL`=2차항 a, `P_MUL_VAL`=1차항 b, `P_SQRT_MUL_VAL`=상수항 c |
| `coef_to_str()` | 없음 (number 반환) | 복원 — 자바가 BigDecimal 로 받는다. 반올림하면 작은 2차항이 `-0` 으로 뭉개진다 |
| `round_digits` | 있음 | 제거 (같은 이유로 원값을 내보낸다) |
| `parse_manual_points` | `[[q,p]]` 배열만 | `{"flow":..,"head":..}` 객체도 수용 (BE 가 보내는 형식) |
| `--pump-hz` | 필수 | 선택 — 미입력 조합에서도 돌아야 한다 |
| CLI | `--conn` / `--conn-key` | `--config` |

교정 뒤 두 모듈의 공개 계약이 일치하는지 확인한다(불일치면 리졸버가 런타임에 깨진다):

```bash
cd inpEditor/PY/roughness_ga_optimizer
python -c "
import inspect, importlib
gs = importlib.import_module('pump_curve_update')
gu = importlib.import_module('pump_curve_update_gunsan')
for n in ['apply_table_config','DbManager','parse_pump_combination','run_auto','run_manual','ScriptError']:
    a, b = getattr(gs, n), getattr(gu, n)
    if inspect.isfunction(a):
        assert str(inspect.signature(a)) == str(inspect.signature(b)), n
print('contract matched')
"
```

### 4-6. 관망 INP 모델 배치

`epa/inp/` 에 부안 INP 를 둔다. `build-and-save.ps1` 이 여기서 `conf/epa/inp/` 로
복사한다. 파일이 하나도 없으면 스크립트가 예외로 멈춘다.

### 4-7. `deploy/buan/` 만들기

`deploy/gunsan/` 을 통째로 복사한 뒤 고친다.

```bash
cp -r deploy/gunsan deploy/buan
```

| 파일 | 고칠 것 |
|---|---|
| `docker-compose.prod.yml` | `name:`, `container_name:` 7곳, 네트워크명, 이미지 네임스페이스, `SPRING_PROFILES_ACTIVE: "ba"`, 포트 |
| `.env` | `DB_*`(inp-editor-be 용), `TAG`, `TILE_TAG` |
| `load-and-up.sh` | 이미지 네임스페이스 2곳(`BE_IMAGE`, `TILE_IMAGE`), 안내 문구의 번들명 |
| `conf/epa/config.py` | §4-4 의 부안본으로 교체 |
| `conf/epa/connections.json` | 같음 |
| `conf/inp-opt/config.json` | §4-5 의 부안본으로 교체 |
| `README.md` | 현장명·주소·포트 |

`.gitignore` 는 그대로 둔다(`conf/epa/inp/` 와 `data/` 를 막는다).

> **개발서버용도 만들 것인가?** 군산은 `deploy/gunsan`(운영/Linux)과
> `deploy/gunsan-dev`(개발서버/Windows) 두 벌이다. 둘은 OS·프로파일·포트·DB 가 전부
> 달라 compose 를 공유하지 않는다. 다른 현장에 개발서버가 없다면 운영본 한 벌만
> 만들면 된다.

### 4-8. `build-and-save.ps1` 에 현장 추가

현재 스크립트는 `$Profiles` 해시에 `prod` / `dev` 두 항목만 있고, 이미지 네임스페이스
`swtp-gunsan/` 이 고정이다. 부안을 추가하려면 두 가지 중 하나를 고른다.

**(a) 스크립트를 복사한다** — 가장 빠르고, 군산 운영본의 검증된 동작을 건드리지 않는다.

```bash
cp deploy/gunsan/build-and-save.ps1 deploy/buan/build-and-save.ps1
```

복사본에서 고칠 곳:

- `$Profiles.prod.BundleDir` → `deploy\buan`
- `$Profiles.prod.DefaultHost` → 부안 서버 IP
- `$Profiles.prod.StagePrefix` → `swtp-buan`
- `swtp-gunsan/` 네임스페이스 2곳(앱 `$Refs`, 타일 `$tileRef`)
- `$Images` 의 `VITE_PROFILE=gunsan` → `buan`

단점은 스크립트가 현장 수만큼 늘어나고, 버그를 고치면 전부에 반영해야 한다는 것이다.

**(b) 스크립트를 다현장화한다** — §8 참조. 현장이 3곳을 넘어가면 이쪽이 낫다.

### 4-9. 배경지도 타일

현장 타일셋을 `tile-server/newEMap/` 에 둔다. 디렉터리 구조는
`newEMap/L05_1~L17_1/{x}/{y}.png` 여야 한다(FE 두 벌이 그 형식으로 요청한다).

```powershell
.\deploy\buan\build-and-save.ps1 -TilesOnly -Tag 20260911
```

이름 형식이 다른 타일셋이라면 FE 를 고치지 말고 `tile-server/nginx.conf` 에
`rewrite` 한 줄로 흡수한다. `tile-server/newEMap/` 은 `.gitignore` 대상이라
**현장 타일을 바꿔 끼우는 방식**이 된다 — 두 현장 타일을 동시에 보관하려면
리포 밖에 두고 `-TilesRoot` 로 경로를 준다.

### 4-10. 빌드

```powershell
.\deploy\buan\build-and-save.ps1 -Tag 20260911
```

---

## 5. 만든 뒤 검증 (반출 전에 로컬에서)

서버에 가서 틀린 걸 알면 비싸다. 이관 전에 로컬에서 확인한다.

```powershell
# 1) 프런트 nginx 가 프록시할 대상 포트가 맞는지
docker run --rm swtp-buan/ems-front:20260911 cat /etc/nginx/conf.d/default.conf |
  Select-String "ems-java-api|ems-py-api"

# 2) 번들에 IP 가 새어 들어가지 않았는지 (상대경로 전환이 유지되는지)
docker run --rm swtp-buan/ems-front:20260911 sh -c "grep -rhoE 'https?://(192\.168\.[0-9]+\.[0-9]+|10\.[0-9]+\.[0-9]+\.[0-9]+)(:[0-9]+)?' /usr/share/nginx/html/js/*.js | sort -u"
#    → 아래 "알려진 3건" 말고는 나오지 않아야 정상. 세 건보다 적게 나와도 안심하지 말 것 —
#      패턴이 빗나가면 검사가 조용히 비어서 나온다.
#      '192\.168\|10\.1' 같은 느슨한 패턴을 쓰면 10.16/10.1054 같은 숫자가 걸려
#      오탐에 묻힌다. 스킴까지 붙여 실제 주소만 남긴다.
#      반대로 교대 분기를 '(192\.168|10)\.N\.N\.N' 처럼 묶으면 192.168 쪽이 옥테트 하나를
#      더 요구받아 <internal-host> 가 **조용히 누락된다**(실제로 겪음). 분기별로 옥테트 수를 따로 적는다.

# 3) $area 가 맞는지 — 현장 문자열이 번들 JS 에 있어야 한다
docker run --rm swtp-buan/ems-front:20260911 sh -c "grep -rlo 'buan' /usr/share/nginx/html/js/*.js | head"
#    → app.*.js 가 나와야 정상. 컴포넌트 이름(MainDashBoard_buan)으로 찾으면 안 된다 —
#      webpack 이 지역 식별자를 뭉개서 .map 에만 남으므로 정상 번들에서도 .js 에는 없다.
#      $area 값은 문자열 리터럴이라 난독화 후에도 그대로 남는다.

# 4) nginx 문법 (Dockerfile 이 이미 하지만 한 번 더)
docker run --rm swtp-buan/ems-front:20260911 nginx -t

# 5) 자바 이미지의 glibc 가 2.34 미만인지 (자바 이미지 2종 모두)
docker run --rm swtp-buan/ems-java-api:20260911 sh -c 'ldd --version | head -1'
docker run --rm swtp-buan/inp-editor-be:20260911 sh -c 'ldd --version | head -1'
#    → 2.34 이상이면 현장 서버에서 pthread_create (EPERM) 로 기동 즉시 죽는다(§9).
#      ems-java-api 는 2.31(focal)이어야 하고, inp-editor-be 는 2.35 라 compose 의
#      security_opt: seccomp:unconfined 가 반드시 함께 있어야 한다.
```

**이 검사는 로컬에서 끝나지 않는다.** glibc 2.34 계열 사고는 개발 PC(Docker Desktop, 최신
libseccomp)에서는 멀쩡히 뜨고 **현장 서버에서만** 죽는다. 그래서 반입 직후, `compose up` 전에
현장에서 10초짜리 판정을 한 번 더 한다.

```bash
docker run --rm                                  <이미지> java -version   # ①
docker run --rm --security-opt seccomp=unconfined <이미지> java -version   # ②
```

①이 죽고 ②가 살면 **seccomp/`clone3` 확정**이다. 그 이미지는 베이스를 glibc 2.34 미만으로
내리거나(`-focal`), compose 에 `seccomp:unconfined` 를 주어야 한다. 둘 다 죽으면 seccomp 가
아니므로 덤프 머리의 시그널로 다시 판단한다.

`.env` 와 이미지가 어긋나는 것이 가장 흔한 사고다. **프런트가 없는 포트를 부르면
화면이 조용히 죽는다** — 에러 로그도 안 남는다. 스크립트가 `.env` 를 빌드에 쓴 값으로
자동 고정하는 이유가 이것이지만, 손으로 `.env` 를 고쳤다면 다시 대조할 것.

---

## 6. 서버 적용

```bash
tar xzf swtp-buan-20260911.tar.gz
cd swtp-buan-20260911
./load-and-up.sh
```

`load-and-up` 은 타일 이미지가 적재돼 있지 않으면 `tile-server` 를 **조용히 건너뛴다.**
앱은 정상 기동하고 배경도만 빠진다. 타일을 올린 뒤에는 `.env` 의 `TILE_TAG` 를
타일 이미지의 태그와 맞추고 다시 실행한다.

> **자주 밟는 함정**: `.env` 의 `TAG` 는 스크립트가 자동으로 채우지만 `TILE_TAG` 는
> `latest` 그대로다. 타일 이미지가 `:20260911` 이면 태그가 어긋나 타일이 안 뜬다.
> 앱은 멀쩡한데 배경지도만 비면 여기부터 본다.

---

## 7. 2회차부터 (같은 현장 다시 말기)

앱만 바꾸는 경우다. 대부분 이것만 하면 된다.

```powershell
.\deploy\buan\build-and-save.ps1 -Tag 20260912
```

서버에서:

```bash
tar xzf swtp-buan-20260912.tar.gz
cd swtp-buan-20260912
# 이전 번들의 data/ 를 가져온다 — DB 레코드가 가리키는 물리 INP 가 여기 있다
cp -r ../swtp-buan-20260911/data ./
./load-and-up.sh
```

**`data/` 를 옮기는 것을 빠뜨리지 말 것.** `data/files` 는 번들 디렉터리 기준
상대경로라 새 번들에서는 비어 있다. DB 의 모델 레코드는 그대로 남아 있으므로,
파일이 없으면 모델 상세조회가 `FILE_NOT_FOUND` 로 깨진다.

타일은 다시 옮기지 않는다(`TILE_TAG` 만 유지).
이미지를 이미 빌드해 뒀다면 `-SkipBuild` 로 패키징만 다시 할 수 있다.

### 서비스 하나만 고칠 때 — 이미지 한 종만 교체

전체를 다시 말 필요는 없다. 프런트 한 곳 고쳤다고 1GB 짜리 번들을 다시 옮기는 것은 낭비다
(`ems-front` 이미지 하나는 194MB). 다만 **`restart` 로는 새 이미지가 반영되지 않는다** —
(4) 를 반드시 읽을 것.

#### (1) 고친 소스가 어느 이미지인지 고른다

| 고친 곳 | 이미지 | 컨텍스트 / Dockerfile | build-arg |
|---|---|---|---|
| `fe/src/**`, `fe/default.conf` | `ems-front` | `fe` / `Dockerfile.gunsan-prod` | **대상별로 갈린다 — (2)** |
| `be/**` | `ems-java-api` | `be` / `Dockerfile_new` | 없음 |
| `epa/app/**`, `epa/Dockerfile` | `ems-py-api` | `epa` / `Dockerfile` | 없음 |
| `inpEditor/FE/**` | `inp-editor-fe` | `inpEditor/FE` / `Dockerfile` | `VITE_PROFILE=gunsan` |
| `inpEditor/BE/editor/**` | `inp-editor-be` | `inpEditor/BE/editor` / `Dockerfile.multistage` | `PROFILE=ubuntu` |
| `inpEditor/PY/roughness_ga_optimizer/**` | `inp-editor-py-opt` | `inpEditor/PY/roughness_ga_optimizer` / `Dockerfile` | 없음 |

**"프런트"가 둘이라는 점에 주의한다.** EMS 화면은 `fe/`(→`ems-front`), 관망편집기 화면은
`inpEditor/FE/`(→`inp-editor-fe`) 다. 서로 다른 이미지이고 서로 다른 포트로 뜬다.

소스가 아니라 **설정**을 고쳤다면 이 절이 아니다. `conf/` 의 세 파일과 관망 INP 는 마운트라
재빌드가 없다 — 아래 "설정을 바꾼 뒤"로 간다.

#### (2) 로컬에서 그 이미지만 빌드한다

`build-and-save.ps1` 은 6종을 한 벌로 다루므로 여기서는 쓰지 않는다. `docker build` 를 직접
부르되 **그 스크립트의 `$Images` 표와 같은 인자**를 준다. 어긋나면 서버에서야 드러난다.

6종 중 `ems-front` 만 build-arg 가 대상별로 갈린다. 나머지 5종은 env·마운트·nginx 프록시로
환경이 결정되므로 어느 대상이든 명령이 같다.

| 대상 | `EMS_API_UPSTREAM_PORT` | `SSO_BYPASS` | `INP_EDITOR_PORT` |
|---|---|---|---|
| prod | `10014` | `false` | `30090` |
| shadow | `10014` | `false` | `30090` |
| dev | `9000` | `true` | `30090` |

`EMS_API_UPSTREAM_PORT` 는 **컨테이너 내부** 포트다(스프링 프로파일이 정한다). `.env` 의
`EMS_API_PORT`(호스트 포트)와 혼동하면 nginx 가 없는 포트로 프록시해 화면 전체가 502 가 된다.

```powershell
# 예 1) 운영용 ems-front 만 다시 만든다
docker build --platform linux/amd64 -t swtp-gunsan/ems-front:20260914 `
  -f fe\Dockerfile.gunsan-prod `
  --build-arg EMS_API_UPSTREAM_PORT=10014 `
  --build-arg INP_EDITOR_PORT=30090 `
  --build-arg SSO_BYPASS=false `
  fe
docker save -o dist\ems-front-20260914.tar swtp-gunsan/ems-front:20260914

# 예 2) build-arg 가 없는 서비스
docker build --platform linux/amd64 -t swtp-gunsan/ems-py-api:20260914 -f epa\Dockerfile epa
docker save -o dist\ems-py-api-20260914.tar swtp-gunsan/ems-py-api:20260914
```

`--platform linux/amd64` 를 빠뜨리지 말 것. 운영·섀도우는 Linux amd64 이고, 빌드 PC 의
아키텍처가 그대로 따라가면 서버에서 `exec format error` 로 죽는다.

**빌드 직후 바로 save 한다.** 운영과 개발서버는 태그가 같을 수 있는데(둘 다 날짜 태그),
그러면 두 대상의 `ems-front` 가 로컬에서 **같은 이름**을 두고 다툰다. 나중 빌드가 앞 빌드를
덮어쓰므로, 두 대상 것을 연달아 만들 때 save 를 미루면 앞의 것이 사라진다. 섀도우는 태그에
접미사(`-sh`)가 붙어 이 문제가 없다.

#### (3) 서버로 옮겨 교체한다

```bash
cd <번들 디렉터리>        # .env 와 compose 가 있는 곳

# 롤백용 태그를 먼저 붙인다 — 같은 태그로 load 하면 옛 이미지가 이름을 잃는다
docker tag swtp-gunsan/ems-front:20260914 swtp-gunsan/ems-front:20260914-prev

docker load -i ems-front-20260914.tar

# restart 가 아니라 up -d. --no-deps 로 의존 서비스는 건드리지 않는다
docker compose -f docker-compose.prod.yml --env-file .env up -d --no-deps ems-front
```

개발서버(Windows)는 compose 파일명만 다르다.

```powershell
docker compose -f docker-compose.dev-server.yml --env-file .env up -d --no-deps ems-front
```

`--no-deps` 는 `ems-front` 의 `depends_on`(`ems-java-api`, `ems-py-api`)까지 딸려 올라가는
것을 막는다. 지금 잘 떠 있는 백엔드를 건드릴 이유가 없다.

되돌릴 때는 태그를 원위치시키고 다시 `up -d` 한다. `load` 한 이미지를 지울 필요가 없다.

```bash
docker tag swtp-gunsan/ems-front:20260914-prev swtp-gunsan/ems-front:20260914
docker compose -f docker-compose.prod.yml --env-file .env up -d --no-deps ems-front
```

#### (4) `restart` 를 쓰면 안 되는 이유

**`docker compose restart` 로는 새 이미지가 반영되지 않는다.** 컨테이너는 생성 시점에 해석된
**이미지 ID** 를 붙잡고 있어서, 같은 태그로 새 이미지를 `load` 해도 옛 ID 를 계속 쓴다.
컨테이너는 Up 이고 에러 로그도 없는데 화면만 옛 코드다 — 이 계열에서 가장 잡기 어려운 증상이다.

`up -d` 는 태그가 **지금 가리키는** 이미지 ID 와 컨테이너의 이미지 ID 를 비교해, 다르면
컨테이너를 재생성한다. 그래서 이미지 교체에는 `up -d` 다.

반대로 마운트한 설정 파일만 고쳤다면 `restart` 가 맞다. 기준은 아래
"`restart` 와 `up -d` 를 가르는 기준"에 정리돼 있다.

#### (5) 교체 후 확인

```bash
# 컨테이너가 새 이미지 ID 를 보고 있는가 — 이것이 진짜 확인이다
docker inspect --format '{{.Image}}' swtp-gunsan-ems-front
docker image inspect --format '{{.Id}}' swtp-gunsan/ems-front:20260914
#   → 두 값이 같아야 한다. 다르면 up -d 가 재생성을 하지 않은 것이다(restart 만 했을 때 그렇다)

docker compose -f docker-compose.prod.yml --env-file .env ps
docker compose -f docker-compose.prod.yml --env-file .env logs --tail 30 ems-front
```

프런트를 교체했는데 화면이 그대로면 브라우저 캐시를 의심하기 전에 번들 파일명을 본다.
webpack 이 내용 해시를 파일명에 넣으므로(`app.<해시>.js`), 코드가 바뀌었으면 파일명이 바뀐다.

```bash
docker exec swtp-gunsan-ems-front ls /usr/share/nginx/html/js/ | grep '^app\.'
```

#### (6) 이 경로를 쓰면 안 되는 경우

| 상황 | 대신 할 일 |
|---|---|
| `.env` 나 compose 도 함께 바뀐다 | 번들 전체를 다시 만다. 이미지와 `.env` 가 어긋나면 화면이 조용히 죽는다 |
| 서비스 서넛을 동시에 고쳤다 | 한 tar 에 담으면 공통 베이스 레이어가 dedupe 된다. 따로 옮길수록 총량이 커진다 |
| 포트·`$area`·스프링 프로파일이 바뀐다 | 2-1 계층이라 이미지뿐 아니라 `.env`·compose 가 함께 움직인다 (§2-1) |
| 현장을 새로 세팅한다 | §4 로 간다 |

#### 전체를 내렸다 올릴 때

```bash
# 타일을 제외한 전부 — 서비스명을 명시해야 한다
docker compose -f docker-compose.prod.yml --env-file .env stop \
  ems-java-api ems-py-api ems-front inp-editor-be inp-editor-fe inp-editor-py-opt
```

`docker compose down` 은 `profiles:` 를 **무시하고** 프로젝트의 모든 컨테이너를
내린다. 타일을 살려 둔 채 나머지만 내리려면 위처럼 서비스명을 나열해야 한다.

### 설정을 바꾼 뒤 — 무엇을 다시 해야 하나

반출본을 다시 마는 일은 생각보다 드물다. §2 의 네 계층 중 **다시 말아야 하는 것은 2-1 뿐**이고
나머지는 서버에서 끝난다. 바꾼 것이 어느 계층인지만 알면 된다.

| 바꾼 것 | 계층 | 해야 할 일 |
|---|---|---|
| `$area` · 프록시 포트 · `SSO_BYPASS` · `VITE_PROFILE` · `PROFILE` · `EDITOR_FE_PORT` | 2-1 | **재빌드**. 다른 길이 없다 (§4-10). 한 서비스만이면 이미지 한 종만 교체한다(위) |
| `conf/epa/config.py` · `conf/epa/connections.json` · `conf/inp-opt/config.json` | 2-2 | 파일 교체 → 해당 서비스 **재기동**(`restart`) |
| 관망 INP (`data/files` 의 모델 파일) | 2-2 | 파일 교체만. **재기동 불필요** — epa 가 매 요청마다 읽는다 |
| `.env` (`TAG` · DB 접속 · 호스트 포트 · `TILE_TAG`) | 2-3 | **컨테이너 재생성**(`up -d`). `restart` 로는 반영되지 않는다 |
| compose 파일 | 2-4 | **컨테이너 재생성**(`up -d`) |

INP 만 예외다. 파일 *내용* 이 아니라 `config.py` 의 **파일명·경로**를 바꿨다면 그건 설정 변경이라
`ems-py-api` 재기동 대상이다. 내용만 갈아끼우는 것은 에디터의 "적용" 경로와 같아 즉시 반영된다
(`deploy/gunsan/README.md` §4).

마운트 파일을 읽는 서비스는 둘뿐이다. 재기동 대상을 여기서 고른다.

| 파일 | 컨테이너 경로 | 읽는 서비스 |
|---|---|---|
| `conf/epa/config.py` | `/app/config.py` | `ems-py-api` |
| `conf/epa/connections.json` | `/app/connections.json` | `ems-py-api` |
| `conf/inp-opt/config.json` | `/app/conf/config.json` | `inp-editor-py-opt` |

```bash
# 운영(Linux) — 번들 디렉터리에서
docker compose -f docker-compose.prod.yml --env-file .env restart ems-py-api          # 2-2
docker compose -f docker-compose.prod.yml --env-file .env up -d ems-py-api             # 2-3 / 2-4
```

```powershell
# 개발서버(Windows) — compose 파일명이 다르다
docker compose -f docker-compose.dev-server.yml --env-file .env restart ems-py-api     # 2-2
docker compose -f docker-compose.dev-server.yml --env-file .env up -d ems-py-api       # 2-3 / 2-4
```

#### `restart` 와 `up -d` 를 가르는 기준

한 줄로: **파일 내용이 바뀌었으면 `restart`, 컨테이너의 정의가 바뀌었으면 `up -d`.**

- 마운트된 파일의 *내용* 은 컨테이너가 이미 보고 있다. 앱이 기동 시 한 번만 읽을 뿐이라
  프로세스만 새로 뜨면 된다 — `restart` 로 충분하다.
- `.env` 와 compose 는 **컨테이너를 만들 때** 반영된다. `restart` 는 기존 컨테이너를 그대로
  다시 띄우므로 바뀐 값이 들어가지 않는다. 조용히 옛 값으로 도는 것이 이 함정의 고약한 점이다.
  `up -d` 는 정의가 바뀐 서비스만 재생성하고, 확실히 하려면 `--force-recreate` 를 붙인다.
- **`TAG` 를 바꿨으면 `docker load` 가 먼저다.** 없는 이미지를 가리킨 채 `up -d` 하면
  compose 가 pull 을 시도하고, 폐쇄망에서는 그대로 실패한다.

#### 사례 — EPA 5분 스케줄러 켜기/끄기

반출본은 스케줄러를 **꺼서** 내보낸다(`epa/config.gunsan.py` 의 `SCHEDULER_ENABLED = False`).
관망 INP 가 아직 현장과 맞지 않는 동안 5분마다 실 DB 에 결과가 쌓이는 것을 막기 위해서다
(`epa/app/scheduler.py:104-109`). 모델 검증이 끝나면 켠다 — 2-2 계층이라 **재반출이 아니다.**

> 이 리포에는 스케줄러가 둘이다. 여기서 말하는 것은 `epa` 파이썬 쪽(5분 MO 해석)이고,
> `be` 의 자바 `SchedulerService` 는 별개다 — 그쪽은 `@Profile` 이 가르므로 이 절이 아니라
> 2-4 계층(`SPRING_PROFILES_ACTIVE`)이다. 부록 A (4) 참조.

```powershell
# 개발서버 번들 디렉터리에서 conf\epa\config.py 의 SCHEDULER_ENABLED 를 True 로 고친 뒤
docker compose -f docker-compose.dev-server.yml --env-file .env restart ems-py-api
docker compose -f docker-compose.dev-server.yml --env-file .env logs --tail 30 ems-py-api
```

로그로 확인한다. 켜져 있으면 이 줄이 나온다.

```
 * Background scheduler for 'mo' job started (cron trigger: */5 minutes).
```

꺼져 있으면 대신 이 줄이 나온다 — 둘 중 하나는 반드시 찍히므로 설정 반영 여부를 여기서 판정한다.

```
 * Background scheduler disabled by config (SCHEDULER_ENABLED=False).
```

리포 쪽에서 켠 채로 내보내고 싶으면 `epa/config.gunsan.py` 를 고치고 다시 만다. 패키징이
그 파일을 `conf/epa/config.py` 로 복사하므로 번들이 켜진 채로 나간다(§4-4).

**켜기 전에 둘을 확인한다.**

- **워커 수를 늘리지 말 것.** `epa/Dockerfile:37` 이 `--workers 1 --threads 4` 다. 워커를 늘리면
  스케줄러가 워커마다 하나씩 떠서 같은 시각 해석이 중복 실행된다. 군산 엔진의 동시 실행 차단은
  `threading.Lock`(프로세스 내부)이라 이것을 막지 못한다.
- **PRE 루프(`ems-epa-pre`)가 이 스위치에 매달려 있다.** 2026-09-16 부터 PRE 는 사람이 띄우는
  벤더 스크립트가 아니라 compose 서비스다(`deploy/gunsan/docker-compose.prod.yml` 의
  `ems-epa-pre` — `ems-py-api` 와 같은 이미지를 `command` 만 바꿔 띄운다).
  PRE 는 매 회차 직전 MO 결과를 `FLG='CUR'` 로 복사하고 `verify_mo_source()` 가 그 원본을
  요구하므로, **`SCHEDULER_ENABLED=False` 인 동안에는 PRE 를 띄워도 한 회차도 저장되지 않는다.**
  순서는 "이 스위치 → MO 적재 확인 → PRE 기동" 이다.
- **켰다면 세 루프의 간격을 본다.** 스케줄러 MO 는 `*/5` 의 `:30` 초에 시작해 `RGSTR_TIME` 을
  5분 경계로 내림해 저장하고(`epa/app/scheduler.py:118-119`,
  `epa/app/services/epa_service_gunsan.py:250`), 수요예측(`ems-predict`)도 같은 `:30` 에 깨어난다.
  PRE 는 그 뒤 슬롯에서 **둘 다** 요구한다(직전 MO + "예측 origin ≥ 직전 5분 경계").
  기본값 `+1분` 이면 여유가 30초뿐이라 어느 한쪽이 늦으면 그 회차가 통째로 빈다. 그래서
  번들 compose 에 `--schedule-offset-min 2`(= 90초)를 박아 두었고, `[SKIP] ... 수요예측 미갱신`
  이 반복되면 `3` 으로 올린다. 코드 변경 없이 인자만이다.

---

---

## 8. 스크립트를 다현장화하려면 (현장이 3곳을 넘으면)

지금 구조는 현장 하나를 전제로 한다. 현장별 복사본은 3곳까지는 견딜 만하지만
그 이상이면 관리 비용이 복사 비용을 넘는다. 손볼 곳은 넷이다.

| 대상 | 현재 | 바꿀 방향 |
|---|---|---|
| 이미지 네임스페이스 | `swtp-gunsan/` 고정 (3개 파일) | `-Site` 인자로 `swtp-<site>/` |
| `$Profiles` 해시 | `prod` / `dev` 2항목 | 현장×환경, 또는 `deploy/<site>/site.json` 에서 읽기 |
| `$area` | `main.js` 소스 한 줄 + Dockerfile 검증 | `ARG SITE` → sed 로 주입 → **주입 결과를 다시 검증** |
| compose | 현장별 파일 | 유지 권장 — §2-4 의 값이 현장마다 전부 달라 파라미터화하면 검증된 운영본의 동작을 건드린다 |

`$area` 만 조금 설명이 필요하다. 예전에는 sed 로 박았고, 지금은 검증만 한다.
다현장화하면 sed 가 돌아와야 하는데, **sed 만 두고 검증을 빼면 예전 상태로 돌아간다**
(sed 가 빗나가도 빌드가 통과한다). 둘 다 두는 형태가 맞다.

```dockerfile
ARG SITE=gunsan
RUN set -eu; \
    sed -i "s#\$area = '[a-z]*'#\$area = '${SITE}'#" src/main.js; \
    grep -qF "area = '${SITE}'" src/main.js \
      || { echo "ERROR: \$area 주입 실패 (${SITE})"; exit 1; }
```

compose 를 파라미터화하지 않는 쪽을 권하는 이유는 군산 운영/개발서버 두 벌을 나눌 때와
같다. OS·프로파일·포트·DB 가 모두 달라, 하나로 합치면 조건 분기가 파일을 채우고
검증된 운영본의 동작을 건드리게 된다. 이미지를 만드는 스크립트만 공유하는 편이 낫다.

---

## 9. 알려진 제약

- **프런트 번들에 남아 있는 하드코딩 주소는 3건이다.** 상대경로 전환으로 API 호출의 IP 는
  걷어냈지만, **다른 앱으로 브라우저를 보내는** 링크는 남아 있다. §5 의 검사에서 이 셋만
  나오면 정상이고, 넷째가 나오면 새로 생긴 것이다.

  | 주소 | 위치 | 영향 |
  |---|---|---|
  | `http://<internal-host>:10015` | `fe/src/router/index.js:12` (`pmsURL`, 고산) | PMS 가 없는 현장에서 `/pms` 계열 메뉴가 죽은 링크. 고산 자신에게는 정상값이다(부록 A-1) |
  | `http://<internal-host>:11111` | `fe/src/views/Common/sub/EmsSubMenu.vue:158` (`goPump`, **구미**) | 송수펌프 제어 계열·태그/배수지/Q-Table 관리 등 **메뉴 10곳**이 구미 서버로 이동한다 |
  | `http://<internal-host>:8080` | `fe/src/store/DashBoardStore.js:14` | 개발 PC 주소. 실패해도 화면에는 영향이 없으나 폐쇄망에서는 매번 타임아웃을 기다린다 |

  `goPump` 는 같은 문제를 이미 푼 이웃이 있다. `router/index.js:6-10` 은 자율운영 포털을
  `` autoURL = `http://${window.location.hostname}` `` + `getServerPort(area)` 로 바꿔
  **접속한 호스트를 따라가게** 해서 IP 하드코딩을 걷어냈다. `goPump` 만 그 전환에서 빠졌다.
  포트는 재사용할 수 없다 — `getServerPort('gumi')` 는 10111 인데 `goPump` 는 11111 이라
  **다른 앱**이다. 그 앱을 함께 올리는 현장이면 `` `http://${window.location.hostname}:11111/` ``
  로 바꾸고, 안 올리는 현장이면 메뉴 자체를 `$area` 로 가리는 편이 맞다.
- **inp-editor-be 의 빌드 프로파일은 `dev` / `gosan` / `ubuntu` 3종뿐이다.**
  현장별 오버레이가 필요해지면 `resources-env/<profile>/application.yaml` 을 추가한다.
  현재 모든 반출본이 `ubuntu` 를 쓴다.
- **번들의 텍스트 파일은 LF 로 나가야 한다 — 특히 `images.txt`.**
  `load-and-up.sh` 가 `while IFS= read -r ref` 로 한 줄씩 읽어 그대로 `docker image inspect` 에
  넘기므로, CRLF 면 `ref` 끝에 `\r` 이 남아 **6개 전부 MISS** 로 판정된다. 적재는 멀쩡히
  끝났는데 대조만 실패해서 이 메시지로 배포가 멈춘다:

  ```
  ERROR: 적재되지 않은 이미지가 있습니다. 반출본을 다시 만드세요.
  ```

  **이 메시지를 곧이곧대로 믿고 반출본을 다시 말면 안 된다** — 다시 말아도 똑같다.
  MISS 가 6개 전부면 CRLF 를 의심하고, 일부만이면 진짜 적재 실패다. 서버에서 바로 푸는 법:

  ```bash
  sed -i 's/\r$//' images.txt && ./load-and-up.sh
  ```

  `docker load` 는 이미 끝나 있으므로 두 번째 실행은 금방 지나간다.
  생성 측(`build-and-save.ps1`)과 소비 측(`load-and-up.sh` 2벌) 모두 2026-09-16 에 고쳤다.
  **개발서버용 `load-and-up.ps1` 은 `Get-Content` 가 개행을 걷어내 이 문제가 드러나지 않는다** —
  Windows 에서 검증하면 통과하고 현장(Linux)에서만 멈추는 종류다.

- **bind 마운트 경로를 Docker 가 만들게 두면 `inp-editor-be` 의 업로드만 막힌다.**
  호스트 디렉터리가 **없을 때만** Docker 데몬이 `root:root` 로 만든다. 이미 있으면 소유권을
  그대로 쓰므로 **일회성**이다 — "새 서버·새 디렉터리에 처음 올릴 때"만 나고, 한 번 고치면
  그 뒤로는 compose 를 직접 돌려도 재발하지 않는다.

  이 스택에서 `/app/files` 를 공유하는 셋 중 **`inp-editor-be` 만 비루트(app, uid 999)** 다.
  `epa`·`inp-editor-py-opt` 는 root 라 멀쩡히 돌아간다. 그래서 "스택은 정상인데 업로드
  기능만 고장난" 것처럼 보인다. 실패는 BE 로그에만 남는다.

  ```
  java.nio.file.AccessDeniedException: /app/files/originals
  ```

  **화면에는 이 문구가 뜨지 않는다.** `InpFileStorage.store` 가 `IOException` 을 잡아
  `RestApiException(FILE_UPLOAD_ERROR)` 로 바꾸기 때문이다
  (`inpEditor/BE/editor/.../storage/InpFileStorage.java:47-56`). 화면 문구로 원인을 찾으려
  하면 헛돈다. 봐야 할 곳은 여기다.

  ```bash
  docker logs <be 컨테이너> 2>&1 | grep -A 15 "INP 파일 저장 실패"
  ```

  **예외가 가리키는 대상으로 한 번 더 갈린다.** `store()` 의 첫 줄이
  `Files.createDirectories(dir)` 라, 메시지가 **`originals` 디렉터리**를 가리키면 상위
  `/app/files` 가 root 소유인 것이고, **업로드 파일명**을 가리키면 디렉터리는 만들어졌고
  그 안의 쓰기만 막힌 것이다.

  **막는 장치는 두 겹이다.**

  1. `load-and-up.sh` 가 이미지에서 uid/gid 를 읽어(`docker run --entrypoint id`) `chown -R` 한다.
     숫자를 하드코딩하지 않으므로 베이스가 바뀌어 uid 가 달라져도 따라간다.
  2. compose 의 **`inp-storage-init`** 서비스(2026-09-16 추가)가 같은 일을 한다.
     `inp-editor-be` 이미지를 `user: "0:0"` 으로 재사용해 `mkdir` + `chown -R app:app` 만
     하고 끝나는 1회성 컨테이너이며, `inp-editor-be` 가
     `condition: service_completed_successfully` 로 기다린다.
     **1번만으로는 부족해서 넣었다** — `docker compose up -d <서비스>` 로 하나만 재생성하는
     경로에서는 `load-and-up.sh` 를 거치지 않기 때문이다.
     실패해도 경고만 남기고 통과시킨다(스택을 막지 않는다). 새 이미지가 아니라 반출 크기도
     늘지 않는다.

  수동 복구가 필요하면:

  ```bash
  TAG=$(grep '^TAG=' .env | cut -d= -f2)
  BE_UID=$(docker run --rm --entrypoint id "swtp-gunsan/inp-editor-be:$TAG" -u)
  BE_GID=$(docker run --rm --entrypoint id "swtp-gunsan/inp-editor-be:$TAG" -g)
  sudo mkdir -p data/files/originals data/files/published
  sudo chown -R "$BE_UID:$BE_GID" data/files
  ```

  재기동은 필요 없다 — bind 마운트는 호스트 디렉터리를 실시간으로 본다.

- **`VITE_PROFILE` 은 값이 `dev` 인지 아닌지만 의미가 있다**
  (`inpEditor/FE/front/src/consts/map.js:19-20`). 현장명을 넣는 것은 가독성을 위한 관례이고,
  폐쇄망 반출본은 `dev` 가 **아니기만** 하면 타일서버를 본다.
- **자바 이미지의 베이스 glibc 가 2.34 이상이면 군산 서버에서 JVM 이 기동 즉시 죽는다.**
  자바 코드가 한 줄도 실행되기 전에 죽어 `hs_err` 덤프만 남기고 재시작 루프에 빠진다.
  소스 diff 는 깨끗하고 로컬(Docker Desktop)에서는 잘 떠서 원인을 코드에서 찾게 되는 함정이다.
  이 종류는 **현장 서버에서만** 재현된다.

  기전은 `clone3` 와 seccomp 다. glibc **2.34부터** `pthread_create` 가 `clone3` syscall 을 쓴다.
  구버전 libseccomp/Docker 는 모르는 syscall 에 `ENOSYS` 가 아니라 **`EPERM`** 을 돌려주는데,
  glibc 는 `ENOSYS` 일 때만 구식 `clone` 으로 후퇴하므로 `EPERM` 이면 그대로 실패한다.
  군산 호스트 커널이 `5.4.0-162`(Ubuntu 20.04 계열)로 정확히 그 세대다.

  | 태그 | OS | glibc | JDK | 군산에서 |
  |---|---|---|---|---|
  | `eclipse-temurin:11-jre` (접미사 없음) | 26.04 | 2.43 | 11.0.32 | ✗ |
  | `eclipse-temurin:11-jre-jammy` | 22.04 | 2.35 | 11.0.32 | ✗ |
  | `eclipse-temurin:11-jre-focal` | 20.04 | **2.31** | 11.0.27 | ✓ `be` 를 여기로 고정 |
  | `eclipse-temurin:21-jre-jammy` | 22.04 | 2.35 | 21 | △ `seccomp:unconfined` 로만 뜬다 |

  **두 서비스가 서로 다른 방식으로 푼다.** `ems-java-api` 는 베이스를 focal 로 내려 경계 아래로
  가고(seccomp 보호 유지), `inp-editor-be` 는 JDK 21 에 focal 태그가 없어 compose 의
  `security_opt: seccomp:unconfined` 로 우회한다. compose 3종의 해당 줄에 주석이 붙어 있다 —
  **지우면 즉시 깨진다.** 근본 해결은 호스트의 Docker/libseccomp 갱신이고, 그 뒤에는 양쪽 다
  풀 수 있다.

  실패는 이렇게 보인다. **JVM 이 `EPERM` 을 "insufficient memory" 로 번역해 출력하므로
  메모리 문제로 오해하기 쉽다.** 봐야 할 것은 첫 줄이다.

  ```
  [warning][os,thread] Failed to start thread "GC Thread#0" - pthread_create failed (EPERM)
  # There is insufficient memory for the Java Runtime Environment to continue.
  ```

  덤프의 `NPROC infinity` · `maximum number of tasks: unlimited` · `MemAvailable` 이 넉넉한데도
  이 메시지가 나오면 **자원이 아니라 권한 문제**다. 판정은 10초면 된다 — §5-5) 참조.

  덧붙여 **런타임 `FROM` 에는 반드시 OS 접미사를 붙인다.** 접미사가 없으면 업스트림이 기본
  배포판을 올릴 때 따라 올라가, 같은 Dockerfile·같은 소스인데도 빌드 날짜에 따라 베이스가
  달라진다. 2026-09-14 사고가 정확히 이것으로, `11-jre` 가 focal 에서 26.04 로 표류하면서
  glibc 2.34 경계를 넘었다. `build-and-save.ps1` 이 `--pull` 을 일부러 빼서 베이스 재현성을
  챙기고 있는데, `FROM` 태그 자체가 안 잠겨 있으면 그 노력이 무력화된다 — 캐시가 없는 PC 에서
  처음 빌드하는 순간 그날의 최신 베이스를 집어온다.

  반출 경로 **밖**인 `pms-back/Dockerfile`(`openjdk:11-jdk`, 이미 EOL)·`pms-back/Dockerfile.local`
  (`eclipse-temurin:11-jre`)에는 같은 결함이 남아 있다. `build-and-save.ps1` 의 `$Images` 에 없어
  현재 반출본에는 영향이 없지만, 반출 대상에 넣게 되면 먼저 고정해야 한다.


- **파이썬 이미지도 같은 호스트에서 막히지만 증상이 다르다 — 죽지 않고 "펜딩"으로 보인다.**
  `ems-py-api`(epa)·`inp-editor-py-opt`(al) 는 numpy/pandas 를 쓴다. numpy 가 끌고 오는
  **OpenBLAS 는 import 시점에 호스트 코어 수만큼**(군산 = 32개) 워커 스레드를 미리 띄우고,
  그중 하나라도 `pthread_create` 에 실패하면 **`EAGAIN` 이 아닌 오류에는 후퇴 없이 `exit(1)`** 한다.

  ```
  OpenBLAS blas_thread_init: pthread_create failed for thread 27 of 32: Operation not permitted
  OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
  ```

  `epa/app/services/web_service.py` 가 **모듈 최상단에서** pandas 를 import 하므로 gunicorn
  워커가 `run:app` 적재 단계에서 죽고 마스터가 재기동을 반복한다. 컨테이너는 `Up` 으로 보이고
  **요청은 응답 없이 pending 으로 남는다** — 자바 쪽처럼 재시작 루프가 눈에 띄지 않는다.
  판별점은 **`/web/nodes` 같은 순수 DB 조회까지 같이 걸리는지**다. 걸리면 해석 엔진·INP 문제가
  아니라 워커가 뜨지 못한 것이다.

  `RLIMIT_NPROC -1 current, -1 max` 는 ulimit 이 무제한이라는 뜻이므로 **자원 문제가 아니다.**
  원인은 위 자바 항목과 **같은 seccomp/`clone3`** 이다. 2026-09-16 군산 섀도우에서 확정했다.

  **PID 상한과 가르는 판별점은 실패의 연속성이다.** 로그에 `thread 1..32` 가 **연속으로 전부**
  실패하면 seccomp 전면 차단이고, 앞쪽 몇 개는 성공하다가 특정 번호에서 걸리면 PID 상한이다.
  로그 한 줄만 보고 "thread 27 에서 걸렸다"고 읽으면 후자로 오진한다 — 가운데 한 줄일 뿐이다.

  **조치는 compose 두 가지를 같이 넣는 것이고, 순서가 있다.**

  1. **`security_opt: seccomp:unconfined`** — 이것이 실제 해결책이다. `inp-editor-be` 와
     같은 줄, 같은 이유다.

     ```yaml
     security_opt:
       - seccomp:unconfined
     ```

  2. **BLAS 스레드 고정** — 해결책이 아니라 위생 조치다.

     ```yaml
     OPENBLAS_NUM_THREADS: "1"
     OMP_NUM_THREADS: "1"
     MKL_NUM_THREADS: "1"
     NUMEXPR_NUM_THREADS: "1"
     ```

  **2번만으로는 못 고친다 — 한 번 이 함정에 빠졌으니 적어 둔다.** `-e OPENBLAS_NUM_THREADS=1`
  을 주면 `import pandas` 가 통과하기 때문에 다 풀린 것처럼 보이지만, 그건 numpy 적재 경로만
  스레드를 안 쓰게 된 것이고 **스레드 생성 자체는 여전히 막혀 있다.** gunicorn 이 `gthread`
  워커로 `--threads 4` 를 띄우므로(`epa/Dockerfile` 의 CMD) 워커가 여전히 못 뜬다.
  확인은 이 한 줄이다.

  ```bash
  docker exec <컨테이너> python -c "import threading; threading.Thread(target=lambda: 0).start(); print('ok')"
  # RuntimeError: can't start new thread → 1번이 반드시 필요하다
  ```

  그래도 2번을 같이 두는 이유: BLAS 32 스레드는 gunicorn 스레드 4개와 코어를 놓고 다투기만
  하고 **관망해석 속도에는 기여하지 않는다** — EPANET 은 wntr 의 C 엔진이 돌리고 BLAS 를
  타지 않는다. 로그 노이즈도 사라진다.

  **둘 다 이미지 재빌드가 필요 없다.** compose 텍스트만 고치고
  `docker compose up -d ems-py-api` 로 서비스 하나만 재생성하면 된다(§2-4 범주).
  새 반출본을 말 이유가 없다 — 서버의 compose 를 직접 고쳐도 되고, 다음 반출본이 자동으로
  따라간다.

  **`al`(inp-editor-py-opt) 도 같은 의존성(`scipy`/`pandas`/`numpy`)을 갖지만 아직 적용돼
  있지 않다** — 최적화 요청이 같은 식으로 펜딩되면 같은 두 가지를 넣는다.

  판정은 이미지에서 바로 된다(컨테이너가 죽어 있어도 된다).

  ```bash
  docker run --rm --security-opt seccomp=unconfined <이미지> python -c "import pandas; print('ok')"
  docker run --rm                                    <이미지> python -c "import pandas; print('ok')"
  # 앞만 성공 → seccomp/clone3 확정 (호스트 Docker/libseccomp 갱신이 근본 해결)
  ```

---

## 부록 A. 가동 중인 현장을 대체할 때 — 고산 사례

§4 는 빈 서버에 새로 올리는 절차다. **이미 돌고 있는 시스템을 컨테이너 스택으로
갈아끼우는 것은 위험의 종류가 다르다.** 포트·DB·Kafka 를 현재 가동 중인 앱과
공유하게 되기 때문이다. 고산을 예로 정리한다(2026-09-11 조사 기준).

### A-1. 고산은 준비가 가장 잘 돼 있다

군산에서 새로 만들어야 했던 것들이 고산엔 대부분 이미 있다.

| 항목 | 상태 |
|---|---|
| 스프링 프로파일 `gs` | 있음. **신버전 Kafka 화이트리스트에도 포함**(§4-2) |
| `resources-env/gosan/` | 있음 — inpEditor 가 이미 고산에 배포된 흔적 |
| `config.gosan.json` (최적화) | 있음 |
| 관망 INP | `epa/inp/gs_inp{,_si,_mo}.inp` — **리포 기본값이 고산이다** |
| `epa/config.py` | 기본값이 이미 고산 (`DEFAULT_CONN_KEY = 'maria-ems-db-gs-'`, `config.py:40`) |
| `MainDashBoard_gosan.vue` | 있음 (`Route.js` 의 `default` 도 고산) |
| PMS 링크 | `fe/src/router/index.js:12` 의 `<internal-host>:10015` 가 **고산 기준으로 이미 정확하다** (§9 에서 "고산 하드코딩"이라 적은 그 줄이, 고산에서는 정상값이다) |
| 자율운영 포털 | 10011 실재 → `SSO_BYPASS=false` 그대로 |

군산 작업 때 `config.gunsan.py` 가 고산 INP 를 그대로 참조한 것도 이 때문이다.

### A-2. 충돌하는 것 — 위험 순서

#### ⚠⚠ (1) Kafka 컨슈머 그룹 충돌

`application-gs.properties:25-29` 의 group.id 를 그대로 쓰면 새 컨테이너가 **기존 앱과
같은 컨슈머 그룹에 조인한다.** 파티션이 갈려 양쪽이 각각 절반씩만 받는다.
**에러가 나지 않는다** — SCADA 데이터가 조용히 반쪽이 된다.

병행 기동을 위해 group.id 를 새로 주면, `auto-offset-reset=earliest` 때문에 **토픽을
처음부터 다시 읽는다.** 대량 재처리와 중복 적재가 따라온다. 어느 쪽도 공짜가 아니므로
A-3 의 섀도우 구성(Kafka 자체를 끄는 방법)을 쓰는 편이 낫다.

#### ⚠⚠ (2) DB 호스트가 둘로 갈려 있다 — **미해결, 착수 전 확인 필요**

| 구성요소 | DB |
|---|---|
| EMS 백엔드 (`application-gs.properties:9`) | **<internal-host>**/EMS_DB |
| EPA (`epa/connections.json` 의 `maria-ems-db-gs-`) | **<internal-host>**/EMS_DB |
| inpEditor (`resources-env/gosan/application.yaml:19`) | **<internal-host>**/EMS_DB |
| 최적화 (`config.gosan.json`) | **<internal-host>**/EMS_DB |

DB 이름(`EMS_DB`)도 계정(`ems_user`/`CHANGE_ME`)도 같고 호스트만 다르다. 리플리카인지
한쪽이 낡은 설정인지 **코드로는 판단이 안 된다.** 잘못 잡으면 화면과 해석 결과가 서로
다른 DB 를 보게 된다. 담당자 확인이 1순위다.

#### (3) 포트 전면 충돌

우리 compose 가 쓰는 10013 / 10014 / 23002 / 25000 / 30090~30092 가 고산에서 **전부
이미 사용 중**이다. 곧 **포트를 그대로 두면 병행 검증이 불가능하다.**

#### (4) 스케줄러 이중 가동

`gs` 는 `@Profile("!dev")` 라 `SchedulerService` 가 켜진다. 기존 앱도 켜져 있으므로
병행 기동하면 자정 삭제 3종이 두 번, `savingDayCalculatorTask`(매분 30초)가 두 번 돈다.

#### (5) 타일서버가 이미 있다 — 오히려 유리하다

고산엔 `<internal-host>:25000` 에 운영 타일서버가 있다(`fe/default.conf` 의
`location /newEMap/` 주석이 그 근거). 우리 `tile-server` 도 25000 이라 충돌하지만,
**기존 것을 그대로 쓰면 타일 tar 를 아예 옮기지 않아도 된다.** `tiles` 프로파일을 빼고
`set $tile_server` 를 기존 주소로 두면 끝이다(§4-9 를 통째로 건너뛴다).

#### (6) inpEditor python-data 가 30093 에 따로 있다

고산은 30092(최적화)와 30093(데이터)이 분리돼 있는데 우리 compose 는
`inp-editor-py-opt:30092` 하나로 통합했다. compose 가 `EDITOR_PYTHON_DATA_BASE_URL` 을
덮어쓰므로 **동작은 된다.** 기존 30093 서비스를 정리할지는 별도 판단이 필요하다.

### A-3. `dev` 프로파일이 곧 고산 섀도우 구성이다

**`gs` 와 `dev` 의 운전 상수(`dstrb.*`)는 사실상 동일하다.** 두 블록을 diff 하면 차이가
4줄인데 그나마 `level_tag` 배열의 원소 순서 하나와 끝 개행뿐이고, 태그도 양쪽 다
`701-367-*`(고산)이다. `application-dev.properties` 자체가
`### 운전현황 변수 - 현재 고산만 있음 ###` 이라고 적고 있다.

그리고 `dev` 는 §4-2 의 게이트에서 **Kafka · SchedulerService · PumpScheduler 가 모두
꺼지는 유일한 프로파일**이다. 둘을 합치면 이런 구성이 나온다.

```yaml
SPRING_PROFILES_ACTIVE: "dev"                                     # 쓰기·Kafka 전부 꺼짐
SPRING_DATASOURCE_URL: "jdbc:mariadb://<internal-host>:3306/EMS_DB"  # 운영 DB 를 읽기만
```

포트를 시프트(10013→10113 등)해 병행 기동하면 **Kafka 그룹 충돌도 스케줄러 중복도 없이**
컨테이너 스택이 제대로 도는지 확인할 수 있다.

주의 두 가지.

- `dev` 의 `server.port` 는 9000 이다. 프런트를 `-EmsApiPort 9000` 으로 말아야 한다.
- **이건 읽기 검증용이지 최종 구성이 아니다.** 전환 시엔 `gs` 로 바꿔 다시 말아야 한다.

### A-4. 전환 순서

| 단계 | 할 일 |
|---|---|
| 0. 확인 | A-5 의 질문들. 특히 `.112`/`.113` 과 롤백 경로 |
| 1. 섀도우 | `dev` 프로파일 + 포트 시프트로 병행 기동 → 기존 화면과 숫자 대조 |
| 2. 준비 | `$area=gosan` 으로 프런트 재빌드(`gs`, `-EmsApiPort 10014`), `deploy/gosan/` 세트 작성. 타일은 기존 25000 재사용 → `tiles` 프로파일 제외 |
| 3. 전환 | 기존 앱 정지 → 포트 원복 → `docker compose up`. **여기서 Kafka·스케줄러가 넘어온다** |
| 4. 감시 | 자정 삭제가 한 번만 도는지, Kafka lag 정상인지 하루 관찰 |

**롤백 준비가 3단계의 전제다.** 기존 앱을 어떻게 되살리는지(서비스 등록 방식, WAR 위치)를
2단계에서 미리 확보해 둘 것.

### A-5. 착수 전 담당자 확인 목록

1. **`<internal-host>` 와 `<internal-host>` 중 EMS_DB 현행은 어느 쪽인가.** 리플리카라면
   쓰기는 어디로 가는가 (A-2 (2))
2. 기존 고산 앱의 기동 방식과 롤백 절차
3. Kafka 토픽 파티션 수 / 현재 컨슈머 그룹 lag
4. 30093 python-data 서비스를 우리 스택으로 흡수해도 되는지
5. `inp_file_m` 등 inpEditor 테이블이 이미 있는지 (`FLYWAY_ENABLED` 판단)

> 1번이 확정되면 이 부록의 A-2 (2) 표를 결론으로 교체할 것. 지금은 **미해결 상태로
> 남겨 둔 것이다** — 추정으로 채우면 전환 당일에 드러난다.

---

## 부록 B. 가동 중인 스택 옆에 나란히 올릴 때 — 군산 섀도우 사례

부록 A 는 기존 시스템을 **대체**하는 절차다. 이쪽은 기존을 **살려둔 채** 새 버전을 다른 포트로
함께 띄워 양측을 비교한다. 대체보다 위험이 낮지만 종류가 다르다 — 되돌릴 일이 없는 대신,
두 스택이 같은 DB·Kafka 에 동시에 쓰지 않도록 막는 것이 전부다.

군산에서 실제로 만든 세트가 `deploy/gunsan-shadow/` 다 (2026-09-14 기준).

> **검증 범위**: 반출본 생성과 산출물 검증까지 끝났다. **서버 기동은 아직 하지 않았다** —
> B-6 의 서버 절차와 B-7 의 "기동 후 검증"은 설계이지 실적이 아니다.

### B-1. 먼저 확인할 세 가지

이 세 가지 답에 따라 작업량이 크게 갈린다. 착수 전에 서버에서 받는다.

| 질문 | 확인 방법 | 왜 갈리나 |
|---|---|---|
| 기존이 compose 로 올라갔나 | `docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' $(docker ps -q)` | 프로젝트명이 같으면 **기존 컨테이너가 교체된다** |
| 새로 넣는 기능의 포트가 비었나 | `ss -lntp` | 비었으면 프런트 재빌드를 생략할 수 있다 |
| 새 기능의 DB 스키마가 있나 | `SHOW TABLES LIKE 'inp\_%'` | 없으면 기동 즉시 죽는다(`ddl-auto: validate`) |

군산에서는 각각 "compose 로 올라감 / inpEditor 포트는 비어 있음(기존에 없던 기능) / 직접 적용"
이었고, 덕분에 **프런트 build-arg 가 운영본과 완전히 같아졌다.**

### B-2. 충돌하는 것 — 위험 순서

#### ⚠⚠ (1) compose 프로젝트명

Compose 는 컨테이너를 `프로젝트명 + 서비스명` 으로 식별한다. 프로젝트명이 같으면
"같은 서비스의 설정이 바뀌었다"고 판단해 **가동 중인 컨테이너를 삭제하고 새것으로 교체한다.**
포트를 다르게 줘도 막히지 않는다 — 오히려 포트 변경이 재생성의 트리거가 된다.
`load-and-up.sh` 가 `--remove-orphans` 까지 붙이므로 더 확실히 지운다.

`name:` 이 없으면 compose 는 프로젝트명을 **compose 파일이 있는 디렉터리명**으로 정한다.
그 경우 새 번들을 다른 디렉터리에 풀면 자동으로 갈리지만, 명시하는 편이 안전하다.

`container_name:` 은 프로젝트와 무관하게 **데몬 전역에서 고유**해야 한다. 겹치면 기동이
실패하는데, 이건 에러로 멈추므로 오히려 안전한 실패다.

#### ⚠⚠ (2) 런타임 쓰기 — 에러 없이 조용히 망가진다

프로파일을 그대로 쓰면 세 가지가 동시에 벌어진다.

| 무엇 | 증상 |
|---|---|
| Kafka 컨슈머 그룹 분할 | 같은 group.id 로 조인해 파티션이 갈린다. **기존 앱이 SCADA 를 절반만 받는다.** 에러 로그가 없다 |
| 스케줄러 이중 가동 | 자정 삭제 3종·매분 집계·펌프 스케줄러가 두 번 돈다 |
| 같은 DB 쓰기 | 비교 목적상 **DB 공유는 의도한 것**이지만, 쓰기는 한쪽만 해야 한다 |

group.id 를 새로 주는 것도 답이 아니다. `auto-offset-reset=earliest` 라서 토픽을 처음부터
재처리하며 중복 적재한다. **쓰기 경로를 통째로 끄는 것이 유일한 안전한 답이다**(B-3).

#### (3) 이미지 태그

같은 태그로 `docker load` 하면 그 태그가 새 이미지를 가리키게 된다. 가동 중인 컨테이너는
이미지 ID 를 붙잡고 있어 당장은 멀쩡하지만, 기존 스택을 `up -d` 하거나 `docker image prune`
하는 순간 조용히 새 코드로 바뀌거나 이미지가 사라진다. 접미사를 붙인다(`20260914-sh`).

#### (4) 호스트 포트

가장 쉬운 부분이다. `.env` 만 고치면 된다. **예외는 하나** — inpEditor 의 호스트 포트는
`EmsSubMenu` 의 `window.open` 이 브라우저에서 도는 코드라 프런트 이미지에 빌드타임에 박힌다.
이 값을 바꾸면 `-InpEditorPort` 로 프런트를 다시 말아야 한다.

군산은 `+100` 규칙을 썼다 — 10013→10113, 10014→10114, 23002→23102.
**컨테이너 내부 포트는 건드리지 않는다.** nginx/gunicorn/Spring 설정을 손대지 않아도 되고
프런트 이미지도 운영본과 같은 build-arg 로 말 수 있다.

### B-3. 섀도우 프로파일 — `gu2` 설계

`dev` 프로파일을 쓰는 방법(부록 A-3 의 고산 방식)은 군산에 맞지 않았다. `dev` 의 운전 상수가
고산 기준이라 `dstrb.prdct.dstrbId`·`pumpComb.target.*`·`pwrCal.calVal` 같은 중괄호 맵을
환경변수로 덮을 수 없고, 그러면 비교 자체가 무의미해진다.

대신 **운영 프로파일을 통째로 복사한 쌍둥이**를 만들었다. `application-gu2.properties` 는
`gu` 와 본문이 바이트 단위로 같다. 다른 것은 이름 하나뿐이고, 그 이름이 쓰기 경로를 끊는다.

| 끄는 것 | 방식 | 코드 변경 |
|---|---|---|
| 신 Kafka (`kafka/consumer/*`, `kafka/producer/*`) | `@Profile` **화이트리스트**에 넣지 않음 | **없음** — 안 넣는 것이 곧 비활성화 |
| 구 Kafka (`kafka/*` 3종) | `@Profile` **블랙리스트**에 `& !gu2` | 3줄 |
| **모든** `@Scheduled` | `SchedulerConfig` 에 `@Profile("!gu2")` | 1줄 + 중복 제거 1줄 |

#### 함정 1 — Kafka 구현이 두 벌이고 게이트 방향이 반대다

`kafka/consumer/*` 와 `kafka/producer/*` 는 화이트리스트(`@Profile({"gs","gu",...})`)라
새 프로파일을 안 넣으면 저절로 꺼진다. 그런데 `kafka/*` 는 블랙리스트
(`@Profile("!dev & ... & !gu & ...")`)라 **새 프로파일이 목록에 없으면 오히려 켜진다.**
게다가 복사해 온 properties 에 `bootstrap-servers` 와 토픽명이 살아 있어 실소비를 시작한다.
한쪽만 보고 "Kafka 는 알아서 꺼진다"고 판단하면 여기서 당한다.

#### 함정 2 — `@Scheduled` 는 개별 클래스로 못 끈다

`@Scheduled` 를 가진 클래스는 5개다(`SchedulerService` / `AlarmService` / `DrvnConfig` /
`PumpScheduler` / `KafkaProducerTasks`). 이 중 **`AlarmService` 는 `@Profile` 이 아예 없고**
`AlarmController` · `AiService` 가 그 빈에 의존한다. 클래스를 끄면 알람 화면이 깨진다.

그래서 개별 클래스가 아니라 **`@EnableScheduling` 자체를 게이트**한다. 그러면 5개가 한꺼번에
멈추고, 빈은 그대로 떠서 조회 API 는 정상이다.

#### 함정 3 — `@EnableScheduling` 이 두 곳에 중복 선언돼 있었다

`EmsApplication` 과 `common/SchedulerConfig` 양쪽에 있었다. 하나만 게이트하면 나머지가
새어나가 스케줄러가 그대로 돈다. `SchedulerConfig` 만 남기고 `EmsApplication` 쪽을 지워
활성화 지점을 한 곳으로 모아야 `@Profile` 이 실제로 먹는다.
(`TaskScheduler` 빈을 주입받는 코드가 한 곳도 없어 `SchedulerConfig` 가 통째로 빠져도 무해하다.)

#### 함정 4 — 프로파일은 단일 값이어야 한다

여러 클래스가 `@PropertySource("classpath:application-${spring.profiles.active}.properties")` 로
**프로파일명과 같은 이름의 파일을 직접 읽는다.** 그래서 `SPRING_PROFILES_ACTIVE="gu,gu2"` 로
상속시킬 수 없다 — 파일명이 `application-gu,gu2.properties` 가 되어 기동이 깨진다.
프로파일을 통째로 복사하는 것이 유일한 길이고, 원본이 바뀌면 **복사본도 함께 고쳐야 한다.**

#### 파이썬 쪽

`epa` 는 `SCHEDULER_ENABLED = False` 로 이미 꺼져 반출된다(§7 사례 참조).
`inp-editor-py-opt` 에는 백그라운드 스케줄러가 아예 없다(요청 기반으로만 동작).
**손댈 것이 없다.**

### B-4. 반출본 세트

운영본(`deploy/gunsan/`)을 복사해 네 곳만 고친다.

| 파일 | 변경 |
|---|---|
| `docker-compose.shadow.yml` | `name:` / `container_name:` 7개 / `SPRING_PROFILES_ACTIVE` / 포트를 `.env` 변수로 |
| `.env` | 호스트 포트 6종 + `TAG` 충돌 경고 |
| `load-and-up.sh` | **기동 전 충돌 점검** 추가 (아래) |
| `build-and-save.ps1` | `$Profiles` 에 `shadow` 항목 추가 |

`data/files` 는 번들 디렉터리 기준 상대경로이고 named 볼륨·네트워크는 프로젝트명 접두사가
붙으므로, 프로젝트명만 바꾸면 **자동으로 격리된다.**

#### `load-and-up.sh` 의 충돌 점검

운영본에 없는 단계다. 옆에서 스택이 돌고 있으므로 컨테이너를 만들다 말고 어중간하게
실패하는 것을 막는다.

- 컨테이너 이름 7개가 이미 쓰이는지 (쓰이면 소유 프로젝트까지 표시)
- 호스트 포트가 점유됐는지 (`ss` 없으면 `netstat` 폴백)
- **2회차 재기동에서는 건너뛴다** — 자기 자신이 포트를 잡고 있는 게 정상이므로,
  `compose ps -q` 로 이미 떠 있는지 먼저 본다

#### 포트 변수명 함정

빌드 파라미터 `-EmsApiPort` 와 `.env` 의 `EMS_API_PORT` 는 **이름이 비슷하지만 다른 값**이다.

| 이름 | 군산 섀도우 값 | 의미 |
|---|---|---|
| `-EmsApiPort` | 10014 | 컨테이너 **내부** 포트. 프런트 nginx 의 프록시 대상 |
| `.env` 의 `EMS_API_PORT` | 10114 | **호스트** 포트. Swagger·curl 이 붙는 곳 |

`dev` 타깃은 둘이 우연히 같아서(9000=9000) 오래 드러나지 않았다. 섀도우에서 이 값을 섞으면
nginx 가 없는 포트로 프록시해 **화면 전체가 502** 가 된다 — 에러 페이지가 아니라 빈 화면이라
원인 찾기가 까다롭다.

### B-5. 빌드

```powershell
.\deploy\gunsan\build-and-save.ps1 -Target shadow -Tag 20260914-sh
```

기본값이 운영본과 같다(`-ServerHost <internal-host> -EmsApiPort 10014 -InpEditorPort 30090`).
`shadow` 분기는 `.env` 의 `DB_HOST` 와 `EDITOR_FE_PORT` 만 치환한다 — 나머지 포트는 서버 조사
결과에 맞춰 **사람이 정하는 값**이지 빌드가 정할 값이 아니기 때문이다.

### B-6. 서버 적용

```bash
tar xzf swtp-gunsan-sh-20260914-sh.tar.gz     # 기존 번들과 다른 디렉터리에
cd swtp-gunsan-sh-20260914-sh
ss -lntp | grep -E '10113|10114|23102'        # .env 포트가 비었는지 먼저
./load-and-up.sh
```

새 기능의 DB 스키마가 없으면 **기동 전에** 직접 적용한다. `FLYWAY_ENABLED` 는 `false` 로 둔다.

> **첫 기동에서 `ems-java-api` 가 실패했다 — 원인은 glibc 2.34 / `clone3` 였다.**
> 나머지 6종(프런트·py-api·inpEditor 3종·타일)은 정상이었고, `ems-java-api` 만 재시작 루프에
> 빠져 로그에 **JVM 크래시 덤프(`hs_err`)만** 찍혔다. `gu2` 도, 포트도, **메모리도 아니다.**
> 자세한 기전과 조치는 §9 의 "자바 이미지의 베이스 glibc" 항목에 있다.
>
> **덤프 읽는 법 — 이 사고가 진단을 세 번 빗나가게 했으니 순서를 그대로 따를 것.**
>
> ```bash
> docker logs swtp-gunsan-sh-ems-java-api 2>&1 | head -60
> ```
>
> 1. **꼬리가 아니라 머리부터 본다.** 꼬리(메모리 맵·CPU 플래그)만 보면 메모리 문제로 읽힌다.
> 2. 머리에서 이 한 줄을 찾는다 — 여기에 진짜 errno 가 있다:
>    `Failed to start thread "GC Thread#0" - pthread_create failed (EPERM)`
> 3. **`EPERM` 이면 자원이 아니라 권한이다.** 바로 아래 JVM 이 출력하는
>    "There is insufficient memory for the Java Runtime Environment to continue" 는
>    **오역이다.** 이 문구를 믿고 힙·RAM 을 뒤지면 며칠 날린다.
> 4. 자원 문제가 아니라는 반증은 덤프 안에 다 있다 — `NPROC infinity`,
>    `maximum number of tasks: unlimited`, `threads-max` 수백만, `MemAvailable` 수백 GB,
>    그런데 `memory_usage_in_bytes` 는 고작 7MB. 그리고 `current number of tasks: 1` 은
>    스레드를 하나도 못 만들고 죽었다는 뜻이라 Spring 도 war 도 프로파일도 **실행된 적이 없다**.
>
> 확정은 §5 의 10초 판정(`--security-opt seccomp=unconfined` 유무로 `java -version` 이 갈리는지)
> 으로 한다. 갈리지 않는다면 seccomp 가 아니므로 시그널로 다시 본다
> (`SIGILL`이면 CPU 명령어, `SIGSEGV`+`libc`/`ld-linux` 면 링커 단계).

### B-7. 검증

#### 산출물 검증 (반출 전, 로컬)

`@Profile` 은 컴파일된 클래스의 **상수 풀에 문자열로 남는다.** 소스가 아니라 산출물에서
확인할 수 있다는 뜻이다. 소스를 고쳤어도 Gradle 캐시가 옛 클래스를 재사용했다면 여기서 걸린다 —
"소스는 맞는데 이미지는 옛것"이 이 종류 배포에서 가장 흔한 사고다.

```bash
# war/jar 를 컨테이너에서 꺼내 zipfile 로 연다
cid=$(docker create swtp-gunsan/ems-java-api:<TAG>)
docker cp "$cid:/app/app.war" ./app.war
docker rm "$cid"
```

확인 항목:

| 대상 | 기대 |
|---|---|
| `WEB-INF/classes/application-gu2.properties` | 있음. `server.port` · DB · 운전 상수가 원본과 일치 |
| `SchedulerConfig.class` / 구 Kafka 3종 `.class` | `!gu2` 문자열 **있음** |
| `EmsApplication.class` | `EnableScheduling` 참조 **없음** |
| `kafka/consumer/*`, `kafka/producer/*` `.class` | `gu2` 문자열 **없음** (화이트리스트 미포함 확정) |
| 프런트 이미지 `default.conf` | `ems-java-api:10014` — **컨테이너** 포트여야 한다 |
| 프런트 번들 JS | inpEditor 호스트 포트가 인라인돼 있음 |
| 런타임 베이스 glibc (`ldd --version`) | **2.31** (focal). 2.34 이상이면 현장에서 기동 즉시 죽는다. §5-5) 로 확인 |

위 표는 마지막 행을 빼면 전부 war **안**만 본다. 군산 섀도우 사고는 war 는 완벽했는데
그것을 담은 베이스 이미지가 문제였다 — 그래서 마지막 행이 추가됐다. 산출물만 검증하고
**이미지가 그 서버에서 뜨는지**를 안 보면 같은 종류를 또 놓친다.

#### 기동 후 검증

```bash
docker compose ls -a     # 운영/섀도우 두 프로젝트가 모두 보여야 정상

# 먼저 "정말 떠 있는가". Up 표시만 믿지 말 것 — 재시작 루프도 잠깐씩 Up 으로 보인다.
docker inspect -f '{{.RestartCount}} {{.State.Status}}' swtp-gunsan-sh-ems-java-api
#   → RestartCount 가 계속 늘면 기동 실패다. B-6 의 덤프 읽는 법으로 간다.

docker logs <프로젝트>-ems-java-api 2>&1 | grep -iE "kafka|AdminClient|Scheduler"
```

세 번째 명령이 **아무것도 출력하지 않아야** 한다. 한 줄이라도 나오면 게이트가 새고 있다.
다만 기동 자체가 실패했을 때도 아무것도 안 나온다 — 그래서 `RestartCount` 를 **먼저** 본다.
"조용하다"를 "정상"으로 읽으면 안 되는 자리다.

```bash
docker logs <프로젝트>-ems-py-api 2>&1 | grep -i scheduler
# → "Background scheduler disabled by config (SCHEDULER_ENABLED=False)." 한 줄이 정상
```

### B-8. 검증 기간에 지킬 것

1. **섀도우에서 EPA 시뮬레이션을 호출하지 말 것.** 5분 스케줄러는 꺼져 있지만 화면에서
   부르면 `TB_FP_SI_VAL` / `TB_FR_SI_VAL` / `TB_TOT_ALG` 에 **실제로 쓴다.**
2. **inpEditor "적용"의 `mntr_yn` 은 DB 전체에서 1건인 전역 플래그다.** 로컬 검증 스택을
   동시에 띄우면 배지가 왔다갔다한다(`deploy/gunsan-dev/README.md` 의 "DB 는 공유, INP 파일은 각자").

### B-9. 전환 / 철수

| 결정 | 할 일 |
|---|---|
| 전환 | 기존 스택 `down` → `.env` 포트 원복 → `SPRING_PROFILES_ACTIVE` 를 운영 프로파일로 → `up -d`. **여기서 Kafka·스케줄러가 넘어온다.** 자정 삭제가 한 번만 도는지 하루 관찰 |
| 철수 | `docker compose -f docker-compose.shadow.yml --env-file .env down -v` — 프로젝트가 갈려 있어 기존 스택에 영향이 없다 |

전환하더라도 섀도우 프로파일은 리포에 남겨 둔다. 다음 검증 때 그대로 재사용한다.

### B-10. 다른 현장에 적용할 때

프로파일 이름만 바꾸면 그대로 쓸 수 있다. 순서는 이렇다.

1. `application-<현장>.properties` 를 복사해 `application-<현장>2.properties` 를 만든다
2. 구 Kafka 3종의 블랙리스트에 `& !<현장>2` 를 추가한다 (화이트리스트 쪽은 손대지 않는다)
3. `SchedulerConfig` 의 `@Profile` 에 `& !<현장>2` 를 추가한다
4. `deploy/<현장>-shadow/` 를 만들고 프로젝트명·컨테이너명·포트를 갈라 놓는다
5. `build-and-save.ps1` 의 `$Profiles` 에 항목을 추가한다

3번은 `@Profile("!gu2")` 를 `@Profile("!gu2 & !ba2")` 처럼 누적한다. 현장이 늘면 이 줄이
길어지므로, 그때는 `shadow` 라는 공통 프로파일을 하나 두고
`SPRING_PROFILES_ACTIVE` 에 단일 값만 준다는 제약(B-3 함정 4)을 어떻게 우회할지 다시 설계한다.

---

## 관련 문서

- `deploy/gunsan/README.md` — 군산 운영 폐쇄망 배포 (타일 커버리지, DB 스키마 생성, INP 공유)
- `deploy/gunsan-dev/README.md` — 군산 개발서버 배포 (Windows 권한, 문제 판단표)
- `deploy/gunsan-shadow/README.md` — 군산 섀도우 배포 (운영 병행 검증, `gu2` 프로파일)
