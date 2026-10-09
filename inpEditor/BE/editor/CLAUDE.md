# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 이 저장소의 문서/주석/커밋 메시지는 한국어로 작성합니다. (변수명·함수명은 영어)

## 프로젝트 개요

EPANET 상수도 관망 모델 파일(`.inp`)을 업로드·파싱·표출·편집·저장하는 백엔드 API.
상위 모노레포 `inp-simulator`(BE / FE / PY) 중 `BE/editor` 단일 Gradle 모듈이다.
프론트(Vue)는 상세조회 응답을 지도에 렌더링하고, 편집 결과를 다시 저장 API로 보낸다.

- **Java 21**, **Spring Boot 4.1.0**, Gradle
- MariaDB + Spring Data JPA (스키마는 Flyway 관리, JPA 는 `ddl-auto: validate`)
- 라이브러리: JTS(공간 기하), JGraphT(위상), juniversalchardet(인코딩 자동판별), MapStruct, Lombok, springdoc(Swagger)

## 자주 쓰는 명령어

Windows 기준 `gradlew.bat`(Git Bash 에서는 `./gradlew`).

```bash
./gradlew.bat build          # 전체 빌드(테스트 포함)
./gradlew.bat test           # 테스트만 실행
./gradlew.bat bootRun        # 로컬 실행 (기본 포트 8080)
./gradlew.bat bootJar        # 실행 JAR 생성 → build/libs/api.jar

# 단일 테스트 클래스 / 메서드
./gradlew.bat test --tests "com.mindone.editor.inp.network.InpNetworkParsingTest"
./gradlew.bat test --tests "*InpNetworkParsingTest.combinesIntoLayers"

# 환경(지자체)별 프로파일 빌드: src/main/resources-env/<profile>/ 가 base resources 를 오버라이드
./gradlew.bat bootJar -Pprofile=dev     # 미지정 시 'common'(오버라이드 없음)
```

- 테스트는 build.gradle 이 `spring.profiles.active=test` 를 강제해 `application-test.yaml`(저장소 경로를 `build/test-storage` 로 변경)을 적용한다 → 개발/운영 절대경로(D:) 의존 제거.
- 파싱/결합 단위 테스트(`InpNetworkParsingTest`, `InpComposeWriteTest` 등)는 **Spring 컨텍스트 없이** 컴포넌트를 직접 `new` 해서 검증한다. DB·컨텍스트 없이 빠르게 돈다.
- Swagger UI: 실행 후 `/swagger-ui.html` (dev 프로파일은 context-path `/api` 하위).

## 핵심 아키텍처: INP 처리 파이프라인

이 코드베이스의 본질은 **읽기 ↔ 쓰기가 대칭인 INP 변환 파이프라인**이다. 패키지 `com.mindone.editor.inp.network` 에 집중돼 있다.

> 📖 **사양 근거(필독)**: INP 섹션 포맷·객체 속성·해석 옵션·단위·오류 메시지의 의미는 `doc/manual/`(EPANET 2.2 공식 매뉴얼 한국어 정리)을 **1차 근거**로 참조한다. INP 입력 파일 포맷은 `doc/manual/appendix_back_matter.md`(부록 C)가 기준(SSOT)이며, 섹션↔코드↔매뉴얼 매핑은 `doc/manual/README.md` 의 매핑표를 본다. 파싱/결합/작성 동작이 매뉴얼과 어긋나면 매뉴얼을 따른다.

### 정방향 — 상세조회 (`GET /inp-files/{id}/network`, `NetworkService`)

```
파일 바이트
  → InpFileReader(intake)      인코딩 자동판별(CP949/UTF-8, BOM) 후 라인 디코딩
  → InpParser(parser)          [SECTION] 단위 구조화 → ParsedInp (무손실, UNKNOWN 섹션도 보존)
  → NetworkAssembler(combiner) ParsedInp → NetworkModel (타입드 노드/링크/라벨 + 좌표 결합)
  → GeoJsonCombiner            NetworkModel → 레이어별 GeoJSON (nodeLayer/linkLayer/labelLayer)
  → NonVisualSectionCombiner   비가시 섹션(CURVES/PATTERNS/CONTROLS/LABELS …) → 의미 키-밸류
                               ※ CONTROLS/RULES 는 sections.CONTROLS = {simple, rule} 한 키로 묶임
  → OptionsCombiner            OPTIONS/TIMES/REACTIONS/ENERGY → 5범주(hydraulics/quality/reactions/times/energy)
                               ※ 결과는 sections.OPTIONS 키로 합류(최상위 options 키 없음)
  → NetworkDetailResponse(meta + layers + sections)
```

### 역방향 — 저장 (`PUT .../network` 덮어쓰기, `POST .../network/save-as` 다른 이름 저장, `NetworkComposeService`)

```
편집된 상세조회 응답(NetworkSaveRequest)
  → InpComposer(compose)   응답 → InpDocument (전 섹션 복원, EPANET/WNTR 표준 순서)
  → InpWriter(writer)      InpDocument → CP949 텍스트/바이트
```

`InpComposer.compose()` 의 섹션 호출 순서가 곧 출력 INP 의 섹션 순서다. Combiner 의 정확한 역연산이어야 라운드트립이 보존된다.

### 반드시 알아야 할 설계 결정

- **온디맨드**: 상세조회는 매 요청 파일을 다시 읽어 파싱한다. 파싱 결과를 DB에 영속화하지 않는다.
- **무손실 완전 파싱**: 모든 섹션을 보존하며, 표준에 없는 섹션은 `UNKNOWN` 으로 원본 헤더명과 함께 보관. `NetworkModel.parsed` 에 전체 `ParsedInp` 가 들어있다.
- **객체 속성 병합**: EPANET 속성편집기(매뉴얼 6.4)처럼, 한 객체의 속성이 여러 섹션(TAGS/DEMANDS/STATUS/EMITTERS/QUALITY/SOURCES/MIXING/REACTIONS/ENERGY)에 흩어져 있다. `NetworkAssembler` 가 이를 ID 로 join 해 노드/링크의 `properties` 로 합치고, `InpComposer` 가 다시 각 섹션으로 분리한다.
- **인코딩**: 읽기는 자동판별(주로 CP949), 쓰기는 항상 CP949(한글 보존). 소스 컴파일 인코딩은 build.gradle 에서 UTF-8 로 고정(주석/리터럴 한글 보존).
- **좌표계**: INP 좌표는 한국 투영좌표(미터). EPSG 는 파일마다 달라 기본값 미지정 → 응답 `meta.crs` 가 `UNKNOWN`. `EDITOR_NETWORK_COORDINATE_CRS` 로 지정(예: `EPSG:5186`).

## 영속화 & 파일 저장 패턴 (리비전 이력 기반)

> 📖 상세 설계·**파이썬 공유 DB 계약**은 `doc/design/inp-file-revision.md` 참조(필독).

- **마스터 + 리비전 분리**: 한 파일 = 마스터(`inp_file_m`, `InpFile`) 1건 + 리비전(`inp_file_rev_h`, `InpFileRevision`) N건. 마스터는 파일 단위 불변 정보 + **현재 적용 리비전 포인터(`curr_rev_no`)** 만 갖고, 저장 파일명·크기 등 버전별 정보는 리비전 테이블에 append-only 로 쌓인다.
- `InpFile` UUID 는 **애플리케이션에서 생성**(DB 아님) — 물리 파일 쓰기 전에 저장 파일명을 확정해야 하기 때문. `Persistable<String>` + `isNew` transient 플래그로 Spring Data 가 merge 가 아닌 INSERT 를 타도록 강제한다.
- 물리 파일: `{editor.storage.base-path}/originals/{uuid}_r{rev_no}.{확장자}` (리비전마다 별도 파일, in-place 덮어쓰기 없음). `stor_file_nm` 컬럼이 SSOT.
- **조회/다운로드는 항상 현재 적용 리비전** 기준(`NetworkService`/`InpFileService` 가 `curr_rev_no` → 리비전 join). 과거 리비전은 `{revNo}` 지정 시 열람.
- 라이프사이클: 업로드→rev0(`ORIGIN`) / 덮어쓰기→rev(max+1, `EDIT`)+포인터이동 / 새로쓰기→새 마스터 rev0(`EDIT`) / 롤백→**포인터만 이동**(파일·행 추가 없음). 채번은 항상 `max(rev_no)+1`, `UNIQUE(inp_file_id, rev_no)` 로 동시 추가 충돌 차단.
- **OPTIMIZE 리비전은 파이썬 모듈이 공유 DB·스토리지에 직접 기록**(BE 는 OPTIMIZE 쓰기 엔드포인트 없음). 채번/파일명/포인터 규칙은 위 설계 문서의 계약을 따른다.
- 저장: **메타(리비전 행 + 포인터) 저장 → 물리 파일 기록** 순서. 물리 저장 실패 시 예외 전파로 트랜잭션 롤백(스트레이 파일 없음).
- 삭제: 리비전 이력 일괄 삭제 → 마스터 삭제 → **커밋 성공 후** `afterCommit` 에서 **모든 리비전 물리 파일** 삭제(best-effort). 롤백 시 파일 보존, 실패 시 고아 파일로 남고 로깅만.
- **적용(`PUT /inp-files/{id}/apply`)**: 리비전 관리와 별개로, 현재 적용 리비전의 물리 파일을 `originals/` 가 아닌 **base-path 루트**의 고정 대상 파일명(`editor.apply.target-file-names`, 기본 `gs_inp_si.inp`/`gs_inp_mo.inp`)으로 복사한다. 같은 디렉터리를 EPANET 해석엔진(`epa` 컨테이너)이 `/app/inp` 로 함께 보고 **매 요청마다 다시 읽으므로** 재기동 없이 반영된다. 교체는 같은 디렉터리에 `.tmp` 로 전부 복사한 뒤 `ATOMIC_MOVE` 리네임하는 2단계(복사 실패 시 실제 적용본 무손상). 시뮬레이션(si)과 모니터링(mo)은 항상 같은 모델이어야 해 한 리비전을 두 대상에 함께 쓴다.
- **`mntr_yn` 은 "적용중" 플래그**다(전체에서 한 건만 `Y`). 컬럼명은 모니터링 여부지만 실제 의미는 "현재 해석엔진에 올라간 모델"이며, 적용 리비전 번호는 따로 저장하지 않는다(적용 = 그 시점 `curr_rev_no`). 그래서 적용 후 **덮어쓰기 시 플래그를 자동 해제**한다. 파이썬 OPTIMIZE 는 BE 를 거치지 않아 해제되지 않으므로, 최적화 후에는 적용을 다시 눌러야 한다.

## API 응답 / 예외 규약

- 모든 응답은 `ResponseObject<T>` 로 감싼다: `code`(성공 `"SUCCESS"`, 실패 시 에러 코드 enum 명) + `data`.
- 컨트롤러는 `CommonController` 를 상속해 `getResponseEntity(...)` 로 성공 응답 생성.
- 예외는 `throw new RestApiException(에러코드)`. 도메인 에러 코드는 `ErrorCode` 인터페이스를 구현한 enum (`CommonErrorCode`, `InpFileErrorCode`, `InpNetworkErrorCode`). `enum.name()` 이 그대로 응답 `code` 가 된다.
- `RestApiAdvice`(@RestControllerAdvice) 가 전역 처리: `RestApiException` → 400(코드명), 그 외 → 500.
- 파일 CRUD(`InpFileController`) 와 네트워크 표출/저장(`InpNetworkController`) 은 관심사를 분리한 별도 컨트롤러다.

## 설정 / 환경

- **프로파일 오버레이**: `-Pprofile=<name>` 이 `src/main/resources-env/<name>/` 를 base `src/main/resources/` 위에 덮어쓴다(`processResources` 의 `duplicatesStrategy = INCLUDE`). 지자체별 환경 분기를 이렇게 처리한다.
- **DB 스키마는 Flyway 가 관리** (`src/main/resources/db/migration/V*.sql`). JPA 는 검증만 하므로, 스키마 변경은 JPA 매핑이 아니라 **새 Flyway 마이그레이션 파일**로 추가해야 한다.
- 주요 환경변수: `EDITOR_STORAGE_BASE_PATH`, `SPRING_DATASOURCE_URL/USERNAME/PASSWORD`, `EDITOR_NETWORK_COORDINATE_CRS`, `EDITOR_CORS_ALLOWED_ORIGINS`, `EDITOR_MULTIPART_MAX_FILE_SIZE`.

## Spring Boot 4.x / 빌드 주의점

- **Flyway 자동설정 분리**: Spring Boot 4.x 는 자동설정이 기술별 모듈로 쪼개져, Flyway 사용 시 `spring-boot-flyway` 의존성을 별도 추가해야 한다(이미 build.gradle 에 반영됨).
- **어노테이션 프로세서 순서**: Lombok → `lombok-mapstruct-binding` → MapStruct 순서를 유지해야 한다(build.gradle 의 `annotationProcessor` 선언 순서).
- `bootJar` 산출물명은 `api.jar`, 일반 `jar` 태스크는 비활성.

## doc/ 디렉터리

- `doc/manual/` 은 **EPANET 2.2 공식 매뉴얼을 한국어로 정리한 사양 참조 문서**다. INP 관련 기능(파싱·결합·작성, 객체/섹션/옵션 처리)을 구현·수정할 때 **이 문서를 1차 근거로 참조**한다. 진입점은 `doc/manual/README.md`(전체 목차 + 섹션↔코드 매핑표), INP 입력 파일 포맷 명세는 `doc/manual/appendix_back_matter.md`(부록 C)가 SSOT. 핵심 장(3 네트워크 모델 / 6 객체 / 11 입출력 / 12 해석 알고리즘 / 부록)만 본문 번역돼 있고 나머지는 README 에 요약·원문 링크.
- `doc/reference/api/` 는 **다른(이전) 프로젝트**(`com.hscmt`, 전체 시뮬레이션 플랫폼)의 소스로, 설계 참고용으로만 둔 것이다. **빌드 대상이 아니며**(settings.gradle 은 `editor` 단일 모듈) 수정·실행하지 말 것.
- `doc/images/` 는 EPANET Options 브라우저 스크린샷으로, `OptionsCombiner` 의 키 매핑 사양 근거다.
