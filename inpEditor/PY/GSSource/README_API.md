# GSSource API / 스케줄러 사용법

## 1. 설정 파일

GSSource는 실행 시 아래 두 파일을 참조한다.

- `config.json`
  - 사용할 DB 연결 키를 선택한다.
  - API host/port를 설정한다.
  - 예측 결과 저장 테이블을 설정한다.
  - 개발 테스트 기준일 사용 여부를 설정한다.
- `libs/connections.json`
  - DB 접속 정보를 관리한다.
  - `config.json`의 `db_key` 값이 이 파일의 연결 키를 가리킨다.

주의: JSON 파일에는 주석을 넣을 수 없다. 설정 설명은 이 문서를 참고하고, JSON 파일에는 실제 값만 넣어야 한다.

## 2. config.json 예시

개발 테스트 예시:

```json
{
  "db_key": "maria-ems-db-gs-dev",
  "api": {
    "host": "0.0.0.0",
    "port": 30093
  },
  "prediction": {
    "table": "tag_pred_l_test",
    "rawdata_table": "TB_RAWDATA",
    "test_base_date": "2026-04-09",
    "db_fetch_limit": 2160,
    "upload_batch_size": 500
  },
  "pump_routing": {
    "enabled": true,
    "table": "tb_pump_rst"
  }
}
```

운영 예시:

```json
{
  "db_key": "maria-ems-db-gs",
  "api": {
    "host": "0.0.0.0",
    "port": 30093
  },
  "prediction": {
    "table": "tag_pred_l",
    "rawdata_table": "TB_RAWDATA",
    "test_base_date": null,
    "db_fetch_limit": 2160,
    "upload_batch_size": 500
  },
  "pump_routing": {
    "enabled": true,
    "table": "tb_pump_rst"
  }
}
```

## 3. 설정값 설명

| 설정 | 설명 |
| --- | --- |
| `db_key` | `libs/connections.json`에서 사용할 DB 연결 키 |
| `api.host` | API 서버 바인딩 주소. 보통 `0.0.0.0` |
| `api.port` | GSSource API 포트. 기본값은 `30093` |
| `prediction.table` | 예측 결과 저장 테이블. 예: `tag_pred_l`, `tag_pred_l_test` |
| `prediction.rawdata_table` | 원천 데이터 조회 테이블. 보통 `TB_RAWDATA` |
| `prediction.test_base_date` | 개발 테스트 기준일. 운영에서는 반드시 `null` |
| `prediction.db_fetch_limit` | 태그별로 조회할 1분 단위 원천 데이터 개수 |
| `prediction.upload_batch_size` | 예측 결과 insert 배치 크기 |
| `pump_routing.enabled` | 펌프 운전 추천 결과 저장 여부 |
| `pump_routing.table` | 펌프 운전 추천 결과 저장 테이블 |

## 4. 로컬 실행

패키지 설치:

```powershell
cd /d "GSSource 폴더 경로"
python -m pip install -r requirements.install.txt
```

자동 스케줄러 실행:

```powershell
python MAIN_2026.py
```

API 서버 실행:

```powershell
python api_server.py
```

상태 확인:

```text
GET http://127.0.0.1:30093/health
```

## 5. 과거 예측 재수집 API

재수집 시작:

```text
GET http://127.0.0.1:30093/predict/rebuild/260409/260410
```

지원하는 날짜 형식:

- `260409`
- `20260409`
- `2026-04-09`

작업 상태 조회:

```text
GET http://127.0.0.1:30093/predict/rebuild/status
```

재수집 API는 요청 날짜 범위를 10분 단위 기준시각으로 쪼개서 실행한다.

예를 들어:

```text
/predict/rebuild/260409/260409
```

을 호출하면 아래 기준시각들을 순서대로 처리한다.

```text
2026-04-09 00:00
2026-04-09 00:10
...
2026-04-09 23:50
```

예측 결과 저장은 `INSERT IGNORE`를 사용한다. 이미 존재하는 row는 유지되고, 누락된 row만 추가된다.

## 6. Docker 실행 예시

이미지 빌드:

```powershell
cd /d "프로젝트 상위 폴더"
docker build -t gssource:latest .\GSSource
```

API 컨테이너 실행:

```powershell
docker run -d --name gs-api -p 30093:30093 ^
  -v "%cd%\GSSource\config.json:/app/config.json:ro" ^
  -v "%cd%\GSSource\libs\connections.json:/app/libs/connections.json:ro" ^
  gssource:latest python api_server.py
```

스케줄러 컨테이너 실행:

```powershell
docker run -d --name gs-scheduler ^
  -v "%cd%\GSSource\config.json:/app/config.json:ro" ^
  -v "%cd%\GSSource\libs\connections.json:/app/libs/connections.json:ro" ^
  gssource:latest python MAIN_2026.py
```

Compose 샘플 실행:

```powershell
cd /d "프로젝트 상위 폴더"
docker compose -f docker-compose.gs-roughness.sample.yml up --build
```

## 7. 주의사항

- 운영에서는 `prediction.test_base_date`를 반드시 `null`로 설정해야 한다.
- 개발 테스트에서는 `prediction.table`을 `tag_pred_l_test`처럼 테스트 전용 테이블로 두는 것이 안전하다.
- 예측 실행이 느리면 원천 테이블 인덱스를 확인해야 한다. 현재 조회 패턴은 `(TAGNAME, TS)` 인덱스가 있으면 유리하다.
- `api_server.py`의 재수집 작업 상태는 메모리에만 저장된다. API 서버를 재시작하면 상태 스냅샷은 사라지지만, DB에 저장된 예측 결과는 유지된다.
