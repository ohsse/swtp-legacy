# configs/db_connections.json 에서 db 접속 정보 수정 필수

# TB_CTR_TNK_RST 테이블 스키마 변경 필수 (DBA/운영 조치)
# 코드는 테이블을 만들지도 바꾸지도 않음. 아래 스키마로 미리 있어야 하고, 없으면
# 첫 사이클 업로드에서 죽음 (2026-09-15 ensure_table 제거).
#
# [중요] PRDCT_VALUE 컬럼을 지우지 말 것.
#   이 컬럼을 읽는 쪽이 둘 남아 있음:
#     - 군산 PRE 관망해석 (epa/epanet_gunsan/main_epa_gs.py) — EPANET 수요 입력
#     - BE 운전현황 화면 (be/.../sqlmapper/mysql/drvn_mssql.xml)
#   업로드가 REPLACE INTO(= DELETE 후 INSERT)라 컬럼만 있고 안 채우면 매 사이클
#   0 으로 덮임. 그래서 upload.py 가 db_upload_connections.json 의
#   prdct_value_from(기본 VALUE_1min)에 따라 이 컬럼도 같이 채움.
#
# 기존 테이블이 있으면 DROP 하지 말고 ALTER 로 없는 컬럼만 추가할 것
# (1분 주기 전환 2026-09-28 — VALUE_1min/5min/15min/30min 네 개를 씀).
# 이미 있는 컬럼은 빼고 실행:

ALTER TABLE TB_CTR_TNK_RST
    ADD COLUMN VALUE_1min FLOAT NULL,
    ADD COLUMN VALUE_5min FLOAT NULL,
    ADD COLUMN VALUE_15min FLOAT NULL,
    ADD COLUMN VALUE_30min FLOAT NULL;

# 예전 컬럼(VALUE_10min, VALUE_1h~VALUE_6h)이 있으면 그대로 둬도 됨(NULL 로 남음).
# 테이블이 아예 없을 때만 아래로 새로 만듦:

CREATE TABLE TB_CTR_TNK_RST (
    DSTRB_ID VARCHAR(100) NOT NULL,
    RGSTR_TIME DATETIME NOT NULL,
    PRDCT_VALUE FLOAT DEFAULT 0,
    VALUE_1min FLOAT,
    VALUE_5min FLOAT,
    VALUE_15min FLOAT,
    VALUE_30min FLOAT,
    PRIMARY KEY (DSTRB_ID, RGSTR_TIME)
);

# 적용 후 확인 (PRDCT_VALUE 가 VALUE_1min 과 같고 0 이 아니어야 정상):
# SELECT DSTRB_ID, RGSTR_TIME, PRDCT_VALUE, VALUE_1min FROM TB_CTR_TNK_RST
#  ORDER BY RGSTR_TIME DESC LIMIT 5;

# 실행 방법
powershell or cmd 창에서
cd 'DeepEMS_GU 경로' 입력

python scripts\harness\schedule.py --mode prod `
  --stage1-run-dir .\runs\gu_db_1min_h30 `
  --source-cfg configs\gu_db_1min_h30.yaml `
  --offline-artifacts models\offline_artifacts_1min.joblib `
입력

python scripts\harness\schedule.py --mode dev `
>>   --stage1-run-dir .\runs\gu_db_noq8_h6 `
>>   --source-cfg configs\gu_db_noq8_h6.yaml `
>>   --offline-artifacts models\offline_artifacts.joblib `
>>   --backtest-start 2025-06-01 --backtest-end 2025-06-02 `
>>   --stride-minutes 60 `
>>   --out-csv backtest_dev.csv `
>>   --tnk-rst-csv tnk_rst_preview.csv
(테스트용일 경우)

# 패키지 버전이 안맞을 때는
pip install -r requirements.txt (외부망일때)