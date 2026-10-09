================================================================================
  EMS_GS  MAIN(XGBoost)  —  파일 설명 및 실행 가이드
  작성일: 2026-06-29
================================================================================

--------------------------------------------------------------------------------
1. 프로젝트 개요
--------------------------------------------------------------------------------

고산정수장(Gosan) 유량(Q) 및 압력(P) 예측 시스템.
XGBoost 모델을 사용하여 10분 / 20분 / 30분 / 40분 / 50분 /
60분 / 120분 / 180분 / 360분 후 값을 실시간 예측하고,
결과를 운영 DB(tag_pred_l 테이블)에 저장한다.

예측 대상 변수: P_GS_NEW, P_GS_OLD, Q_GS_NEW, Q_GS_OLD


--------------------------------------------------------------------------------
2. 파일별 설명
--------------------------------------------------------------------------------

[ MAIN_2026.py ]
  - 역할: 운영 서버에서 실행되는 실시간 예측 메인 스크립트
  - 동작:
      1) 프로세스 시작 시 saved_model/xgb 에서 XGBoost 모델 일괄 로드
      2) 매 10분(정각·10분·20분·...) schedule 라이브러리로 자동 실행
      3) DB(TB_RAWDATA)에서 최근 2160분(36시간) 원시데이터 조회
      4) 10분 리샘플링 → lag/rmean 피처 생성 → XGBoost 예측
      5) 예측 결과를 DB(tag_pred_l) 및 TB_PUMP_RST에 저장
  - 실행: python MAIN_2026.py  (종료: Ctrl+C)

[ TEST_MAIN_2026_DB.py ]
  - 역할: 운영 DB 데이터를 사용한 오프라인 정확도 테스트 스크립트
  - 동작:
      1) 설정된 테스트 기간(SIM_START ~ SIM_END)의 데이터를 DB에서 일괄 조회
      2) CHUNK_DAYS 단위로 분할하여 슬라이딩 윈도우 시뮬레이션 수행
      3) 예측값 vs 실측값 비교 → MAE / RMSE / sMAPE / R² 출력
      4) 예측 결과를 tag_pred_l 테이블에 INSERT (테스트 업로드)
      5) SAVE_RESULTS=True 설정 시 Excel + 시계열/산점도 그래프 저장
  - 실행: python TEST_MAIN_2026_DB.py

[ TEST_MAIN_2026.py ]
  - 역할: 로컬 pickle 데이터를 사용한 오프라인 정확도 테스트 스크립트
            (DB 접속 없이 로컬에서 빠르게 모델 성능 확인 가능)
  - 동작: TEST_MAIN_2026_DB.py 와 동일하나, 데이터 소스가 로컬 pickle 파일
  - 실행: python TEST_MAIN_2026.py

[ utils.py ]
  - 역할: 공통 유틸리티 함수 모음
  - 주요 함수:
      check_path()                 : 디렉토리 생성
      check_date_continuity()      : 날짜 연속성 검사
      IQR_scale()                  : IQR 기반 이상값 필터링
      Holding_filter()             : Holding(연속 동일값) 필터링

[ requirements.txt ]
  - 역할: Python 패키지 의존성 목록
  - 주요 패키지: xgboost, pandas, numpy, pymysql, scikit-learn,
                 schedule, sqlalchemy, matplotlib, openpyxl, tqdm

[ setup_venv.ps1 ]
  - 역할: 가상환경(.venv) 자동 생성 및 requirements.txt 패키지 설치 스크립트
  - 실행: PowerShell 에서 .\setup_venv.ps1

[ GS_taglist_250904.xlsx ]
  - 역할: 고산정수장 태그 메타 정보 (DB 태그명 ↔ 변수명 매핑, 사용 여부 등)
  - 시트: Gosan
  - 컬럼: 태그명, 변수명, 비고(target/NU), 사용(Y/N)

[ libs/connections.json ]
  - 역할: DB 접속 정보 파일 (운영 DB 호스트·포트·계정 등)
  - 키:   maria-ems-db-gs  (고산정수장 운영 DB)

[ saved_model/xgb/ ]
  - 역할: 학습 완료된 XGBoost 모델 파일 저장 디렉토리
  - 구조: Gosan_{horizon}/{target}.json
  - 예시: Gosan_10min/P_GS_NEW.json
  - 지원 horizon: 10min, 20min, 30min, 40min, 50min,
                  60min, 120min, 180min, 360min
  - 피처 구성: {변수명}_lag{1,2,3,6,12,24}  +  {변수명}_rmean12
               + sin_hour, cos_hour, dayofweek, is_weekend  (총 74개)

[ log/log_2026.txt ]
  - 역할: MAIN_2026.py 실행 로그 (예측 성공/실패, DB 오류 등)
  - 형식: RotatingFileHandler (최대 5MB × 3개 백업)


--------------------------------------------------------------------------------
3. 실행 순서
--------------------------------------------------------------------------------

  [최초 환경 설정]

  Step 1.  PowerShell 에서 가상환경 생성 및 패키지 설치
           > .\setup_venv.ps1

  Step 2.  가상환경 활성화
           > .\.venv\Scripts\Activate.ps1

  Step 3.  libs/connections.json 에 DB 접속 정보 입력 (최초 1회)
           {
             "maria-ems-db-gs": {
               "host": "...", "port": 3306,
               "user": "...", "password": "...", "db": "..."
             }
           }

  ─────────────────────────────────────────────────

  [모델 성능 검증 (선택)]

  Step 4a. 운영 DB 데이터로 오프라인 테스트
           > python TEST_MAIN_2026_DB.py
           (TEST_MAIN_2026_DB.py 상단 SIM_START / SIM_END / CHUNK_DAYS 조정)

  Step 4b. 로컬 pickle 데이터로 오프라인 테스트
           > python TEST_MAIN_2026.py

  ─────────────────────────────────────────────────

  [운영 실행]

  Step 5.  실시간 예측 서비스 시작
           > python MAIN_2026.py
           (매 10분마다 자동 예측 실행, Ctrl+C 로 종료)


--------------------------------------------------------------------------------
4. 주요 설정값 (MAIN_2026.py)
--------------------------------------------------------------------------------

  DB_FETCH_LIMIT    = 2160   # DB 조회 최근 분 수 (36시간)
  UPLOAD_BATCH_SIZE = 500    # tag_pred_l INSERT 배치 크기
  MODEL_DIR         = saved_model/xgb
  LOG_PATH          = log/log_2026.txt


--------------------------------------------------------------------------------
5. 주요 설정값 (TEST_MAIN_2026_DB.py)
--------------------------------------------------------------------------------

  SIM_START    = '2025-11-01 00:10:00'   # 테스트 시작 시각
  SIM_END      = '2026-06-29 23:00:00'   # 테스트 종료 시각
  WINDOW_MIN   = 2160                    # 슬라이딩 창 크기 (분)
  STEP_EVERY   = 1                       # 예측 간격 (1 = 10분마다)
  MAX_STEPS    = None                    # None = 전체 시뮬레이션
  SAVE_RESULTS = False                   # True: Excel/그래프 저장
  CHUNK_DAYS   = 21                      # 분할 단위 (일)

================================================================================
