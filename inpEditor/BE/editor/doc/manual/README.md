# EPANET 2.2 매뉴얼 (한국어 정리)

EPANET 2.2 공식 온라인 매뉴얼([usepa.github.io/EPANET2.2](https://usepa.github.io/EPANET2.2/))의 내용을
이 저장소(INP 에디터 백엔드) 개발에 활용하기 위해 한국어로 정리한 문서 모음입니다.

- **정리 범위**: 백엔드(INP 파싱·표출·편집·저장) 구현에 직접 관련되는 **핵심 장 위주**로 본문을 충실히 번역했습니다.
  나머지 장은 아래 목차에 요약과 공식 링크만 제공합니다.
- **언어 정책**: 산문·설명은 한국어. **INP 섹션 키워드(`[JUNCTIONS]` 등)·속성/옵션 이름·밸브 약어(PRV/PSV/…)·수식·변수기호·코드 예제**는 원문(영어)을 그대로 유지합니다.
- **이미지·하이퍼링크**: 원문 사이트의 절대경로를 그대로 사용하므로, 인터넷 연결 상태에서 그림이 표시됩니다.

> ⚠️ 이 정리본은 원문의 보조 자료입니다. 구현 시 모호한 부분은 항상 [공식 매뉴얼](https://usepa.github.io/EPANET2.2/)을 1차 근거로 확인하세요.

---

## 📌 핵심 정리 문서 (본문 번역 완료)

| 파일 | 장 | 주요 내용 |
| --- | --- | --- |
| [03_network_model.md](03_network_model.md) | 3. 네트워크 모델 | 물리적 구성요소(절점·저수지·탱크·관·펌프·밸브·이미터), 비물리적 구성요소(곡선·시간패턴·제어), 수리/수질 모의 모델 |
| [06_objects.md](06_objects.md) | 6. 객체 다루기 | 객체 종류, 추가·선택·편집·복사·삭제·이동, 가시/비가시 객체 편집, 그룹 편집 (속성편집기 매뉴얼 6.4의 근거) |
| [11_importing_exporting.md](11_importing_exporting.md) | 11. 가져오기와 내보내기 | 시나리오·부분 네트워크·지도 가져오기/내보내기, 텍스트(.inp) 내보내기 |
| [12_analysis_algorithms.md](12_analysis_algorithms.md) | 12. 해석 알고리즘 | 수리 해석(Global Gradient Algorithm, DDA/PDA), 수질 해석(이송·반응·물질전달) 수식 |
| [appendix_back_matter.md](appendix_back_matter.md) | 부록 A/B/C | **A. 측정 단위 · B. 오류 메시지 · C. 커맨드라인 EPANET + INP 입력 파일 포맷 명세** |

### 핵심 문서 세부 목차

- **3. 네트워크 모델** — 3.1 물리적 구성요소 · 3.2 비물리적 구성요소 · 3.3 수리 모의 모델 · 3.4 수질 모의 모델
- **6. 객체 다루기** — 6.1 객체의 종류 · 6.2 추가 · 6.3 선택 · 6.4 가시 객체 편집 · 6.5 비가시 객체 편집 · 6.6 복사/붙여넣기 · 6.7 링크 형태 변경/방향 반전 · 6.8 삭제 · 6.9 이동 · 6.10 그룹 선택 · 6.11 그룹 편집
- **11. 가져오기와 내보내기** — 11.1 프로젝트 시나리오 · 11.2 시나리오 내보내기 · 11.3 시나리오 가져오기 · 11.4 부분 네트워크 가져오기 · 11.5 네트워크 지도 가져오기 · 11.6 네트워크 지도 내보내기 · 11.7 텍스트 파일로 내보내기
- **12. 해석 알고리즘** — 12.1 수리(Hydraulics) · 12.2 수질(Water Quality)
- **부록** — A. 측정 단위 · B. 오류 메시지 · C. 커맨드라인 EPANET 및 입력 파일 포맷(일반 지침 / **입력 파일 형식(27개 INP 섹션 명세)** / 보고서 파일 형식 / 이진 출력 파일 형식)

---

## 📖 전체 장 목차 (나머지 장은 요약 + 공식 링크)

| 장 | 한국어 제목 | 요약 | 링크 |
| --- | --- | --- | --- |
| 1 | 소개 | EPANET의 목적과 수리·수질 모델링 기능, 매뉴얼 구성 개요 | [원문](https://usepa.github.io/EPANET2.2/1_introduction.html) |
| 2 | 빠른 시작 튜토리얼 | 간단한 예제 네트워크를 직접 만들고 해석·결과 확인까지 따라 하는 입문 실습 | [원문](https://usepa.github.io/EPANET2.2/2_quickstart.html) |
| **3** | **네트워크 모델** | 물리/비물리 구성요소와 수리·수질 모의 모델 | [정리본](03_network_model.md) · [원문](https://usepa.github.io/EPANET2.2/3_network_model.html) |
| 4 | EPANET 작업 환경 | 메뉴 바·툴바·지도 창·브라우저(데이터/지도) 창·속성 편집기·상태 표시줄 등 UI 구성 | [원문](https://usepa.github.io/EPANET2.2/4_EPANET_workspace.html) |
| 5 | 프로젝트 다루기 | 프로젝트 생성·열기·저장, 기본값(Defaults) 설정, 보정(calibration) 데이터 등록, 지도 환경설정 | [원문](https://usepa.github.io/EPANET2.2/5_projects.html) |
| **6** | **객체 다루기** | 객체 추가·선택·편집·그룹 편집 | [정리본](06_objects.md) · [원문](https://usepa.github.io/EPANET2.2/6_objects.html) |
| 7 | 지도 다루기 | 지도 확대/축소/이동, 표시 옵션, 범례, 배경도(backdrop), 객체 검색·오버뷰 맵 | [원문](https://usepa.github.io/EPANET2.2/7_map.html) |
| 8 | 네트워크 해석 | 해석 옵션(수리/수질/반응/시간/에너지) 설정, 해석 실행, 결과 진단·문제 해결 | [원문](https://usepa.github.io/EPANET2.2/8_analyzing_network.html) |
| 9 | 결과 보기 | 지도 테마, 그래프(시계열/프로파일/등치선/빈도), 표, 보고서(반응·에너지·보정·전체) | [원문](https://usepa.github.io/EPANET2.2/9_viewing_results.html) |
| 10 | 인쇄와 복사 | 인쇄 미리보기·페이지 설정·인쇄, 클립보드/파일로 복사 | [원문](https://usepa.github.io/EPANET2.2/10_printing_copying.html) |
| **11** | **가져오기와 내보내기** | 시나리오·지도·텍스트(.inp) 입출력 | [정리본](11_importing_exporting.md) · [원문](https://usepa.github.io/EPANET2.2/11_importing_exporting.html) |
| **12** | **해석 알고리즘** | 수리·수질 해석의 수학적 알고리즘 | [정리본](12_analysis_algorithms.md) · [원문](https://usepa.github.io/EPANET2.2/12_analysis_algorithms.html) |
| 13 | 자주 묻는 질문 | 모델링·해석 관련 FAQ | [원문](https://usepa.github.io/EPANET2.2/13_questions.html) |
| 14 | 참고문헌 | 인용된 문헌 목록 | [원문](https://usepa.github.io/EPANET2.2/references.html) |
| 부록 | 측정 단위 / 오류 메시지 / 커맨드라인 | 단위표, 오류 코드, **INP 입력 파일 포맷 명세** | [정리본](appendix_back_matter.md) · [원문](https://usepa.github.io/EPANET2.2/back_matter.html) |

---

## 🔧 백엔드 개발자를 위한 참고

- **INP 파서/컴포저 구현의 1차 근거**는 [appendix_back_matter.md](appendix_back_matter.md)의 **부록 C — 입력 파일 형식**입니다.
  여기에 `[JUNCTIONS]`, `[PIPES]`, `[OPTIONS]` 등 **27개 INP 섹션의 컬럼·포맷·예제**가 정의되어 있습니다.
  (코드의 `com.mindone.editor.inp.network` 파이프라인이 다루는 섹션들과 직접 대응됩니다.)
- **객체 속성이 여러 섹션에 분산**되는 구조(한 절점/관의 속성이 `TAGS`/`DEMANDS`/`STATUS`/`EMITTERS`/`QUALITY`/`SOURCES`/`MIXING`/`REACTIONS`/`ENERGY` 등에 흩어짐)는
  [06_objects.md](06_objects.md)의 속성편집기 설명과 [03_network_model.md](03_network_model.md)의 구성요소 정의를 함께 보면 이해가 빠릅니다.
- **단위계**는 `[OPTIONS]`의 `Units`(CFS/GPM/LPS/CMH 등)에 따라 결정됩니다. 단위별 의미는 부록 A를 참조하세요.

### INP 섹션 ↔ 코드 ↔ 매뉴얼 매핑

기능 구현 시 아래 표로 "어떤 INP 섹션을 / 어느 컴포넌트가 / 매뉴얼 어디를 근거로" 다루는지 빠르게 찾으세요.
(코드 컴포넌트는 `com.mindone.editor.inp.network` 패키지 기준이며, 자세한 흐름은 루트 `CLAUDE.md`의 파이프라인 설명 참조.)

| 대상 | INP 섹션 | 주요 코드 컴포넌트 | 매뉴얼 근거 |
| --- | --- | --- | --- |
| 노드 본체 | `[JUNCTIONS]` `[RESERVOIRS]` `[TANKS]` | `InpParser` → `NetworkAssembler` ↔ `InpComposer` | [3장 §3.1](03_network_model.md) · [부록 C](appendix_back_matter.md) · [6장 속성](06_objects.md) |
| 링크 본체 | `[PIPES]` `[PUMPS]` `[VALVES]` | `NetworkAssembler` ↔ `InpComposer` | [3장 §3.1](03_network_model.md) · [부록 C](appendix_back_matter.md) |
| 객체 속성 병합(여러 섹션 분산) | `[TAGS]` `[DEMANDS]` `[STATUS]` `[EMITTERS]` `[QUALITY]` `[SOURCES]` `[MIXING]` `[REACTIONS]` `[ENERGY]` | `NetworkAssembler`(ID join) ↔ `InpComposer`(섹션 분리) | [6장 §6.4 속성편집기](06_objects.md) · [3장 §3.1·§3.4](03_network_model.md) · [부록 C](appendix_back_matter.md) |
| 좌표·도형·라벨(가시) | `[COORDINATES]` `[VERTICES]` `[LABELS]` `[BACKDROP]` | `GeoJsonCombiner` (레이어) | [부록 C](appendix_back_matter.md) · [7장 지도](https://usepa.github.io/EPANET2.2/7_map.html) |
| 비가시 정보 객체 | `[CURVES]` `[PATTERNS]` `[CONTROLS]` `[RULES]` | `NonVisualSectionCombiner` ↔ `InpComposer` | [3장 §3.2](03_network_model.md) · [부록 C](appendix_back_matter.md) |
| 해석 옵션(5범주) | `[OPTIONS]` `[TIMES]` `[REACTIONS]` `[ENERGY]` | `OptionsCombiner` ↔ `InpComposer` | [부록 C](appendix_back_matter.md) · [8장 해석](https://usepa.github.io/EPANET2.2/8_analyzing_network.html) · [`doc/images/`](../images) |
| 단위계 | `[OPTIONS]` `Units`/`Headloss` | `OptionsCombiner` | [부록 A 측정 단위](appendix_back_matter.md) |
| 인코딩/읽기·쓰기 | (전 섹션) | `InpFileReader`(읽기) · `InpWriter`(CP949 쓰기) | [11장 입출력](11_importing_exporting.md) |
| 해석 거동/알고리즘(검증·이해용) | — | (해석은 PY 모듈 담당) | [12장 해석 알고리즘](12_analysis_algorithms.md) |
| 오류 처리/메시지 참고 | — | `InpNetworkErrorCode` 등 | [부록 B 오류 메시지](appendix_back_matter.md) |

> 라운드트립(읽기→쓰기) 보존이 핵심이므로, 어떤 섹션을 새로 처리할 때는 **Combiner(정방향)와 InpComposer(역방향)를 항상 짝으로** 수정하고, 해당 섹션의 컬럼/포맷은 부록 C 명세와 1:1로 맞추세요.

---

*출처: U.S. EPA, EPANET 2.2 documentation (https://usepa.github.io/EPANET2.2/). 본 문서는 해당 매뉴얼을 한국어로 정리한 2차 자료입니다.*
