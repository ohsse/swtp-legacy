# INP 파일 리비전(이력) 관리 설계

INP 파일의 편집/최적화 이력을 보존하기 위한 리비전 관리 설계와, **백엔드(BE)·파이썬(PY) 공유 DB 계약**을 정리한 문서다.
파싱/결합/작성 파이프라인과 무관한 "파일 메타·저장" 계층의 변경이며, 코드 진입점은 `inp.service.InpFileService` 와 `inp.domain.InpFile`/`InpFileRevision` 이다.

> 용어: **마스터** = 파일 단위 레코드(`inp_file_m`), **리비전** = 파일의 한 버전(`inp_file_rev_h`).

---

## 1. 개요

- 한 INP 파일은 **마스터 1건 + 리비전 N건**으로 관리된다.
- 마스터는 파일 단위 불변 정보(원본 파일명·확장자)와 **현재 적용 리비전 포인터(`curr_rev_no`)** 만 가진다.
- 저장 파일명·크기·작업구분 등 **버전별 정보는 리비전 테이블에 append-only** 로 쌓인다.
- **조회/다운로드는 항상 현재 적용 리비전**을 본다(과거 리비전은 명시 지정 시 열람).
- 물리 파일은 리비전마다 별도 파일로 보존한다(in-place 덮어쓰기 없음).

## 2. 데이터 모델

### `inp_file_m` (마스터)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `inp_file_id` | VARCHAR(36) PK | INP 파일 ID(UUID, 애플리케이션 생성) |
| `orgnl_file_nm` | VARCHAR(255) | 원본 파일명(표시용) |
| `file_xtns` | VARCHAR(20) | 확장자(예: inp) |
| `curr_rev_no` | INT | **현재 적용 리비전 번호(이력 포인터)** |
| `rgst_dttm` / `mdf_dttm` | DATETIME(6) | 등록/수정 일시 |

> 기존 `stor_file_nm`/`file_sz`/`file_hash` 컬럼은 리비전 테이블로 이전됐다. 안전한 롤아웃을 위해 **2단계 마이그레이션**으로 제거한다: **V2** 에서 NULL 허용으로 완화(엔티티 매핑 제거, 신규 INSERT 통과) → 운영 안정화 후 **V3** 에서 실제 DROP.

### `inp_file_rev_h` (리비전 이력)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `rev_id` | BIGINT PK (auto) | 리비전 대리키 |
| `inp_file_id` | VARCHAR(36) FK | 마스터 참조 |
| `rev_no` | INT | 리비전 번호(0부터, `max+1` 채번) |
| `stor_file_nm` | VARCHAR(255) | **저장 파일명(SSOT)** |
| `file_sz` | BIGINT | 파일 크기(byte) |
| `file_hash` | VARCHAR(64) | SHA-256(선택) |
| `work_type` | VARCHAR(20) | 작업 구분(아래) |
| `rgst_dttm` | DATETIME(6) | 등록일시(불변) |

제약: `UNIQUE(inp_file_id, rev_no)` — 동시 리비전 추가 충돌을 DB 레벨에서 차단.

### work_type (작업 구분)

리비전 내용이 **어떻게 만들어졌는가**(내용 출처)를 나타낸다. `rev_no`(순서)와 독립적이다.

| 값 | 의미 | 생성 주체 |
| --- | --- | --- |
| `ORIGIN` | 최초 업로드한 원본 파일 그대로 | BE(업로드) |
| `EDIT` | 웹 에디터 편집 결과 | BE(덮어쓰기/새로쓰기) |
| `OPTIMIZE` | 파이썬 알고리즘 최적화 결과 | **PY(직접 기록)** |

## 3. 라이프사이클 (BE 담당)

| 동작 | 마스터 | 리비전 | 물리 파일 |
| --- | --- | --- | --- |
| 업로드 | INSERT(`curr_rev_no=0`) | rev0 INSERT(`ORIGIN`) | `_r0` 기록 |
| 새로쓰기(save-as) | 새 마스터 INSERT(`curr_rev_no=0`) | rev0 INSERT(`EDIT`) | 새 `_r0` |
| 덮어쓰기 | `curr_rev_no = max+1` | rev(max+1) INSERT(`EDIT`) | 새 `_r{n}` |
| 롤백 | `curr_rev_no = 대상` | (추가 없음) | (추가 없음) |
| 삭제 | 마스터 삭제 | 이력 전체 삭제 | 모든 리비전 파일 삭제(afterCommit) |

핵심 규칙:

- **저장 순서**: 메타(리비전 행 + 포인터) 먼저 저장 → 물리 파일 기록. 물리 실패 시 트랜잭션 롤백으로 메타도 취소되어 스트레이 파일이 남지 않는다.
- **포인터 이동**: 새 리비전(EDIT) 추가 시 `curr_rev_no` 를 그 리비전으로 이동. **롤백만 예외** — 기존 리비전으로 포인터만 이동(파일/행 추가 없음).
- **채번**: 다음 `rev_no = max(rev_no) + 1`. 롤백 후 덮어써도 충돌 없이 증가하며, 건너뛴 중간 리비전은 이력에 그대로 남아 열람 가능하다.
- **파일명 규약**: `{inp_file_id}_r{rev_no}.{확장자}`. 단, `stor_file_nm` 컬럼이 SSOT 이므로 실제 읽기/다운로드는 항상 컬럼값을 사용한다(기존 마이그레이션 데이터는 `{uuid}.inp` 그대로 rev0 보존).

## 4. 🐍 파이썬 공유 DB 계약 (OPTIMIZE)

최적화는 파이썬 모듈이 **모델링 + 물리 파일 저장 + DB 기록**까지 직접 수행한다. BE 는 OPTIMIZE 쓰기 엔드포인트를 제공하지 않으며, 파이썬은 아래 절차를 **한 트랜잭션**으로 수행해야 한다(BE 의 EDIT 흐름과 동일한 불변식 유지).

대상 파일 `inp_file_id` 의 최적화 결과를 새 리비전으로 추가할 때:

1. **다음 리비전 번호 채번**
   ```sql
   SELECT COALESCE(MAX(rev_no), -1) + 1 AS next_rev FROM inp_file_rev_h WHERE inp_file_id = :id;
   ```
2. **저장 파일명 결정**: `{inp_file_id}_r{next_rev}.inp` (스토리지의 `originals/` 하위).
3. **물리 파일 저장**: 최적화 결과 .inp 를 위 경로에 기록(인코딩은 BE 와 동일하게 **CP949** 권장 — 한글 보존).
4. **리비전 행 INSERT**
   ```sql
   INSERT INTO inp_file_rev_h
     (inp_file_id, rev_no, stor_file_nm, file_sz, file_hash, work_type, rgst_dttm)
   VALUES (:id, :next_rev, :stor_file_nm, :file_sz, NULL, 'OPTIMIZE', NOW(6));
   ```
5. **마스터 포인터 이동**
   ```sql
   UPDATE inp_file_m SET curr_rev_no = :next_rev WHERE inp_file_id = :id;
   ```

주의사항:

- **원자성**: 1~5 를 같은 트랜잭션으로 묶는다. 물리 파일 기록 실패 시 DB 도 롤백한다(순서는 BE 와 동일하게 INSERT/UPDATE 후 물리 기록 → 실패 시 롤백 권장).
- **동시성**: `UNIQUE(inp_file_id, rev_no)` 로 BE 편집과 PY 최적화가 동시에 같은 번호를 채번하면 한쪽이 실패한다. 실패 시 재채번 후 재시도.
- **스토리지 경로**: BE 의 `editor.storage.base-path` 와 동일 루트의 `originals/` 디렉터리를 공유해야 한다.
- **소유권**: 스키마(Flyway)와 컬럼 의미의 SSOT 는 BE 다. PY 는 이 계약을 준수만 한다(DDL 변경 금지).

## 5. API (BE 제공)

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `GET` | `/inp-files/{id}/network` | 현재 적용 리비전 상세조회 |
| `GET` | `/inp-files/{id}/revisions` | 리비전 목록(최신순, current 플래그 포함) |
| `GET` | `/inp-files/{id}/revisions/{revNo}/network` | 특정 리비전 상세조회 |
| `GET` | `/inp-files/{id}/revisions/{revNo}/download` | 특정 리비전 단건 다운로드 |
| `POST` | `/inp-files/revisions/download-zip` | 특정 리비전 다건 ZIP 다운로드(엔트리명 `_r{revNo}` 접미사로 구분) |
| `PUT` | `/inp-files/{id}/revisions/{revNo}/rollback` | 롤백(현재 포인터 이동) |
| `PUT` | `/inp-files/{id}/network` | 편집 결과로 덮어쓰기(EDIT 리비전 추가) |
| `POST` | `/inp-files/network/save-as` | 새 파일로 저장(EDIT rev0) |

응답 메타(`InpFileResponse`)에는 **`currRevNo`(현재 적용 리비전 번호)** 가 포함된다. 저장 파일명·크기는 현재 적용 리비전 기준 값이다.
