# /config.gunsan.py — 군산 테스트 스택 전용 설정
#
# docker-compose.gunsan.yml에서 컨테이너의 /app/config.py 자리에 마운트된다.
# 원본 config.py를 대체하는 독립 파일이라 상속하지 않고 전체를 담는다.
# 관망해석(EPANET) 군산 이식 작업에서 손댈 값이 모두 여기에 모여 있다.

class Config:
    """
    _summary_ :
    Flask 애플리케이션 설정 클래스 (군산 테스트용)
    1. 서버 설정: 포트 및 디버그 모드 설정
    2. 파일 경로 설정: INP 및 연결 파일 경로 지정
    3. 데이터베이스 테이블 이름: 테이블 이름 지정
    4. 시뮬레이션 설정: 폴백 시간 설정
    5. 스케줄러 설정: 작업 간격 및 활성 여부
    6. 기본 DB 접속 키: 기본 데이터베이스 접속 키 지정
    """
    # 서버 설정
    SERVER_PORT = 5000
    DEBUG = True

    # JSON 설정 (한글 깨짐 방지)
    JSON_AS_ASCII = False

    # 해석 엔진 선택 — 'gosan' | 'gunsan'.  app/services/engine.py 가 읽는다.
    # 'gunsan' 이면 si/mo 요청이 epa/epanet_gunsan 의 군산 엔진으로 간다.
    EPA_ENGINE = 'gunsan'

    # 파일 경로 설정
    CONN_FILE_PATH = './connections.json'
    # 아래 INP_* 3종은 고산 엔진(app/services/epa_service.py)만 읽는다.
    # EPA_ENGINE='gunsan' 인 동안에는 쓰이지 않는다. 엔진을 되돌릴 때를 위해 남겨 둔다.
    # 군산 관망 모델은 아래 GUNSAN_INP_PATH 가 가리킨다.
    INP_FILE_PATH = './inp/gs_inp.inp'
    INP_SI_FILE_PATH = './inp/gs_inp_si.inp'
    INP_MO_FILE_PATH = './inp/gs_inp_mo.inp'

    # 지도에 그릴 관망 형상(/api/web/network)의 좌표계.  좌표는 재투영하지 않고 INP 원본을
    # 그대로 내려보내며, 이 값이 프런트(MapComponent.vue)의 dataProjection 이 된다.
    # 이 프로젝트의 표준은 EPSG:5186(중부원점 2010)이다. 5181 INP 가 들어오면 좌표계를
    # 바꾸지 말고 INP 쪽을 Y+100,000 으로 5186 이관해서 쓴다.
    NETWORK_CRS = 'EPSG:5186'

    # 데이터베이스 테이블 이름
    NODE_TABLE = 'TB_FP_SI_VAL'
    LINK_TABLE = 'TB_FR_SI_VAL'
    TOT_TABLE = 'TB_TOT_ALG'

    # 시뮬레이션 설정
    FALLBACK_SEC = 86400

    # 스케줄러 설정
    SCHEDULER_MINUTES = 5
    # [군산 전용] 5분 주기 mo 시뮬레이션 + 매일 01:00 정리 작업을 끈다.
    # 켜면 군산 엔진의 mo 해석이 5분마다 돌아 TB_FP_SI_VAL / TB_FR_SI_VAL /
    # TB_TOT_ALG 에 FLG='mo' 로 쌓이고, 01:00 에 3일 이전 행이 삭제된다.
    # 켜기 전에 GUNSAN_INP_PATH 의 관망 모델이 실제로 마운트돼 있는지 확인할 것.
    SCHEDULER_ENABLED = False

    # 기본 DB 접속 키 — connections.gunsan.json의 군산 항목
    DEFAULT_CONN_KEY = 'maria-ems-db-gu-test'

    # 시뮬레이션 변수
    SI_DEMANDS_FROM_RAWDATA_ONLY = False

    # --- 군산 엔진 설정 (EPA_ENGINE='gunsan' 일 때만 쓰인다) ---
    # 값을 읽는 곳: app/services/epa_service_gunsan.py
    #
    # 관망 모델. 컨테이너의 /app/inp 는 볼륨/바인드로 덮이므로, 여기 적은 경로에
    # 실제 파일이 오도록 마운트를 맞춰야 한다. INP 는 .dockerignore 와 .gitignore
    # 양쪽에서 제외되므로 이미지에도 커밋에도 들어가지 않는다.
    GUNSAN_INP_PATH = './inp/epa_model.inp'
    # 국가산단밸브 개도율->저항 보정곡선. 이미지에 함께 복사된다.
    GUNSAN_VALVE_MODEL_PATH = './epanet_gunsan/gunsan_valve_model.json'
    # 밸브 처리 방식. opening=개도율 곡선(기본) | measured | open | inp
    GUNSAN_VALVE_MODE = 'opening'
    # 압력 저장 단위. 고산의 '저장 시 /10'(app/models/epa_models.py:518)과 같은
    # 규칙이며, 밸브 보정파일의 pressure_units_per_head_m(0.1)과 일치해야
    # load_valve_model 이 통과한다. 바꾸면 보정파일도 같이 다시 만들어야 한다.
    GUNSAN_PRESSURE_UNIT = 'legacy_div10'
    # INP 펌프 성능곡선의 기준 Hz
    GUNSAN_REFERENCE_HZ = 60.0
    # 계측값 과거 허용 범위(초)
    GUNSAN_FALLBACK_SEC = 86400
    # 엔진은 한 번에 하나만 돈다(EPANET 실행 중 os.chdir 가 프로세스 전역이라).
    # 이 시간 안에 자리를 못 잡으면 503 으로 돌려준다.
    GUNSAN_LOCK_TIMEOUT_SEC = 86400
    # mo 배치 1회 요청의 최대 스텝 수(5분 단위). gunicorn --timeout 900 대비 안전값.
    GUNSAN_MO_BATCH_MAX_STEPS = 24

    # TB_EPA_SIM_RESV_FLOW 조회 시 허용 시간 범위 (초)
    SI_RESV_WINDOW_SEC = 120

    # DB 원본 데이터의 유량 단위
    RAW_FLOW_UNIT = "CMH"

    # TB_TOT_ALG 결과 저장을 위한 설정
    # 아래 세 값은 고산 엔진(app/services/epa_service.py)만 읽는다.
    # 군산 엔진은 TB_TOT_ALG 행을 스스로 만든다 — 대표 절점 Bks-2496 의 압력과
    # LINK 45 의 유량을 쓰므로(epanet_si_gs.py:1151-1152) 이 값들이 필요 없다.
    # EPA_ENGINE 을 'gosan' 으로 되돌릴 때를 위해 참고용으로 남겨 둔다.
    #            군산 후보 태그는 ems-java-api/src/main/resources/application-gu.properties의
    #            dstrb.prdct.dstrbId 참조:
    #              flowTag  : 891-365-FRI-8950 / -8602 / -8800 / -8600 / -8303
    #              level_tag: 891-365-LEI-8600 / -8652
    #            (압력 태그는 gu 프로파일에 정의가 없어 군산 DB의 태그 테이블에서 확인 필요)
    TOT_NODE_ID = "13"
    TOT_SUM_FLOW_TAGS = "701-367-FRI-4004,701-367-FRI-4001"
    TOT_SUM_PRESS_TAGS = "701-367-PRI-4019,701-367-PRI-4010"
