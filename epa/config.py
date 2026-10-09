# /config.py

class Config:
    """
    _summary_ : 
    Flask 애플리케이션 설정 클래스
    1. 서버 설정: 포트 및 디버그 모드 설정
    2. 파일 경로 설정: INP 및 연결 파일 경로 지정 
    3. 데이터베이스 테이블 이름: 테이블 이름 지정
    4. 시뮬레이션 설정: 폴백 시간 설정
    5. 스케줄러 설정: 작업 간격 설정
    6. 기본 DB 접속 키: 기본 데이터베이스 접속 키 지정
    """
    # 서버 설정
    SERVER_PORT = 5000
    DEBUG = True

    # JSON 설정 추가
    JSON_AS_ASCII = False # <<< [수정] 이 라인을 추가하세요. (한글 깨짐 방지)

    # 해석 엔진 선택 — 'gosan'(기본) | 'gunsan'
    # 이 파일은 리포 기본값(고산)이라 'gosan' 이다. 군산 스택은 config.gunsan.py 나
    # deploy/gunsan/conf/epa/config.py 가 /app/config.py 자리에 마운트되어 대체한다.
    # 값을 읽는 곳: app/services/engine.py
    EPA_ENGINE = 'gosan'

    # 파일 경로 설정 (기존 명령어의 --inp, --conn 인수를 대체)
    # 윈도우 경로 사용 시: 'D:/smart/epanet/inp/gs_inp.inp' 와 같이 슬래시 사용 권장
    CONN_FILE_PATH = './connections.json'
    INP_FILE_PATH = './inp/gs_inp.inp'
    INP_SI_FILE_PATH = './inp/gs_inp_si.inp'
    INP_MO_FILE_PATH = './inp/gs_inp_mo.inp'

    # 지도에 그릴 관망 형상(/api/web/network)의 좌표계.  좌표는 재투영하지 않고 INP 원본을
    # 그대로 내려보내며, 이 값이 프런트(MapComponent.vue)의 dataProjection 이 된다.
    # 이 프로젝트의 표준은 EPSG:5186(중부원점 2010)이다. 5181 INP 가 들어오면 좌표계를
    # 바꾸지 말고 INP 쪽을 Y+100,000 으로 5186 이관해서 쓴다.
    NETWORK_CRS = 'EPSG:5186'

    # 데이터베이스 테이블 이름 (기존 명령어의 파라미터를 대체)
    NODE_TABLE = 'TB_FP_SI_VAL'
    LINK_TABLE = 'TB_FR_SI_VAL'
    TOT_TABLE = 'TB_TOT_ALG'
    
    # 시뮬레이션 설정
    FALLBACK_SEC = 600

    # 스케줄러 설정
    SCHEDULER_MINUTES = 5
    
    # 기본 DB 접속 키 (기존 명령어의 --conn-key 인수를 대체)
    DEFAULT_CONN_KEY = 'maria-ems-db-gs-'
    
    # 시뮬레이션 변수
    SI_DEMANDS_FROM_RAWDATA_ONLY = False

    # TB_EPA_SIM_RESV_FLOW 조회 시 허용 시간 범위 (초)
    SI_RESV_WINDOW_SEC = 120

    # DB 원본 데이터의 유량 단위
    RAW_FLOW_UNIT = "CMH"

    # TB_TOT_ALG 결과 저장을 위한 설정
    TOT_NODE_ID = "13"
    TOT_SUM_FLOW_TAGS = "701-367-FRI-4004,701-367-FRI-4001"
    TOT_SUM_PRESS_TAGS = "701-367-PRI-4019,701-367-PRI-4010"
    
    # 테이블 명
    NODE_TABLE = "TB_FP_SI_VAL"
    LINK_TABLE = "TB_FR_SI_VAL"
    TOT_TABLE = "TB_TOT_ALG"
    
    # 모니터링
    FALLBACK_SEC = 600
