---
name: rawdata-csv-import
description: 태그별 CSV 파일(파일명 `접두.태그번호.접미.csv`, 내용 `TS,VALUE[,QUALITY]`)을 지정한 MariaDB/MySQL 의 TB_RAWDATA 에 INSERT IGNORE 로 적재한다. 파일명에서 태그를 뽑아 TAGNAME 으로 쓰고, 이관분을 SERVER 마커로 표시해 되돌릴 수 있게 한다. "csv 를 TB_RAWDATA 에 넣어줘", "dump 폴더 csv import 해줘", "태그 csv 적재", "SCADA/히스토리안에서 뽑은 계측 파일 DB 에 올려줘", "GSSCADA.~.F_CV.csv 넣어줘", "과거 실측 이관" 같은 요청이면 테이블명을 말하지 않아도 이 스킬을 쓴다. 관망해석용 가짜 데이터 생성(gunsan-epa-dummy)이나 TB_RAWDATA 가 아닌 테이블 적재에는 쓰지 말 것.
---

# 태그별 CSV → TB_RAWDATA 적재

도구는 `scripts/import_csv.py` 하나다. 새 스크립트를 짜지 말고 옵션으로 조절한다.

## 입력 규칙

- **파일명**: `<접두>.<태그번호>.<접미>.csv` → `.` 로 나눈 두 번째 조각이 TAGNAME 이 된다.
  `GSSCADA.891-260-CBB-1312.F_CV.csv` → `891-260-CBB-1312`. 이 형식이 아닌 파일은 경고만 내고 건너뛴다.
- **내용**: 헤더 없는 CSV. 1열 TS(`YYYY-MM-DD HH:MM:SS`), 2열 VALUE, 3열(있으면) QUALITY. 첫 행이 헤더면 자동으로 건너뛴다.
- **적재 행**: `(TS, TAGNAME, VALUE, QUALITY, SERVER=마커)`. 대상 테이블에 QUALITY·SERVER 컬럼이 없으면 그 컬럼은 빼고 넣는다.

## 절차

1. **경로와 대상 DB 를 확인한다.** 필요한 값은 CSV 경로(파일 또는 폴더), host, port(기본 3306), user, password, database 명이다.
   사용자가 이미 말한 것은 다시 묻지 말고, 빠진 것만 묻는다.
2. **먼저 `--dry-run` 을 돌린다.** 태그·행 수·TS 범위·샘플이 나오고, 접속 정보를 함께 주면 파티션 점검까지 한다.
   이 결과를 사용자에게 보여준다. 태그가 기대와 다르거나 불량 행이 많으면 적재하기 전에 여기서 멈춘다.
3. **실제로 적재한다.** 깨끗한 파일은 `LOAD DATA LOCAL INFILE … IGNORE` 로 넣는다. 불량 행·빈 줄이 있는 파일이나
   서버가 LOAD DATA LOCAL 을 막은 경우에는 행 단위 `INSERT IGNORE` 로 자동 전환되는데, 이 경로는 훨씬 느리다.
   - **소요 시간은 dry-run 의 "예상 소요" 줄로 판단한다.** PK 가 `(TS, TAGNAME)` 이라, 같은 기간을 다른 태그가 이미
     채우고 있으면 새 행을 기존 페이지 사이에 끼워 넣어야 해서 느려진다. 빈 기간은 초당 약 16만 행이지만, 태그 10개가 채워진
     기간은 초당 약 2,600행이다(파일 하나 200만 행이면 약 13분). 트랜잭션 크기와는 관계가 없다(10만·50만 행의 속도가 같았다).
   - **에이전트 백그라운드 실행은 2시간에서 강제 종료된다.** 예상 소요가 100분을 넘으면 파일을 몇 개씩 나눠 여러 번 실행한다.
     강제 종료되면 넣던 파일만 롤백되고 커밋된 파일은 남는다. 남은 파일만 다시 넣으면 되고, 같은 파일을 다시 넣어도 IGNORE 라 안전하다.
   - 출력은 줄 단위로 바로 기록되므로, 백그라운드 로그 파일을 읽으면 어느 파일까지 끝났는지 볼 수 있다.
4. **보고한다.** 대상(host/db), 파일별 신규·중복 무시·불량 건수, 합계, 스크립트가 출력한 되돌리기 SQL 을 전한다.

리포 루트에서 PowerShell 로 실행한다. Git Bash 는 경로와 한글 출력이 깨질 수 있다.

```powershell
# 미리보기 (DB 에 쓰지 않음, 접속 정보를 주면 파티션 점검 포함)
python .claude/skills/rawdata-csv-import/scripts/import_csv.py dump --dry-run `
  --host <internal-host> --port 3306 --user USER --password PASS --db ems_db

# 적재 (파일·폴더 여러 개 가능)
python .claude/skills/rawdata-csv-import/scripts/import_csv.py dump `
  --host <internal-host> --port 3306 --user USER --password PASS --db ems_db
```

옵션: `--marker`(SERVER 값, 기본 `CSV_IMPORT`), `--no-bulk`(LOAD DATA 를 쓰지 않음), `--batch`(행 단위 경로의 배치, 기본 5000), `--allow-prod`.

## 알아둘 것

- **중복은 덮어쓰지 않는다.** PK 가 `(TS, TAGNAME)` 이라서 같은 시각·태그의 행이 이미 있으면 그 행(실측 포함)이 그대로 남고
  CSV 값은 버려진다. 같은 명령을 다시 실행해도 안전하다. 값을 바꿔야 하는 상황이면 이 스킬이 맞지 않으니 사용자와 상의한다.
- **파티션이 없는 시각의 행은 조용히 사라진다.** `TB_RAWDATA` 는 월 단위 RANGE 파티션이다. MariaDB 의 `INSERT IGNORE` 는
  "파티션 없음"도 경고로 바꾸고 행을 버리므로, 결과만 보면 중복 무시와 구분할 수 없다. 스크립트는 이를 두 겹으로 막는다.
  쓰기 전에 최대 TS 를 마지막 파티션 경계와 비교하고, 적재 중에도 중복(1062)이 아닌 경고가 나오면 그 자리에서 멈춘다.
  이 오류가 나면 파티션 추가는 DBA 의 일이므로 사용자에게 알린다.
- **LOAD DATA 는 형식 오류를 거부하지 않는다.** IGNORE 를 붙이면 잘못된 TS 를 `0000-00-00` 으로 넣어 버린다. 그래서 스크립트는
  먼저 파이썬으로 전체를 훑고, 불량 행이 하나라도 있으면 그 파일을 행 단위 경로로 보낸다. LOAD DATA 뒤에도 서버 응답의
  `Warnings` 가 `Skipped`(중복)보다 많으면 그 파일을 롤백하고 멈춘다. 이 오류는 우회하지 말고 원인 경고를 사용자에게 보여준다.
- **히스토리안 CSV 는 UTF-8 BOM 으로 시작한다.** 파이썬은 BOM 을 눈치채지 못하지만, LOAD DATA 에서는 첫 행 TS 가 깨진다.
  스크립트가 BOM 을 감지해 서버에서 떼어 내니, "Data truncated for column 'TS' at row 1" 이 다시 보이면 이 부분부터 확인한다.
- **운영 DB 가드.** host `<internal-host>` 또는 db `EMS_DB` 는 거부한다. 사용자가 운영 DB 라는 걸 알고 명시적으로 요구할 때만
  `--allow-prod` 를 붙인다.
- **되돌리기와 조회에는 TS 범위를 꼭 넣는다.** PK 가 TS 로 시작하므로 `WHERE TAGNAME=…` 만 걸면 전체를 스캔해서 시간 초과가 난다.
  스크립트가 출력하는 DELETE 문은 TS 범위·태그·마커를 모두 포함한다. 마커로 지우므로 IGNORE 로 보존된 기존 행은 지워지지 않는다.
- **`--password` 는 셸 기록에 남는다.** 사용자가 이 방식을 선택했다. 공유 PC 라면 실행 뒤 기록을 지우라고 한 줄 안내한다.
