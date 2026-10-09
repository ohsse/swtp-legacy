# /app/scheduler.py (수정 완료)

from datetime import datetime, timedelta # [수정] timedelta 임포트
import traceback
from apscheduler.schedulers.background import BackgroundScheduler

# [핵심 수정] DbManager와 get_db_connection 임포트
from app.models.db import DbManager, get_db_connection
from app.services.engine import get_engine

scheduler = BackgroundScheduler(daemon=True)

def _scheduled_mo_job_wrapper(app):
    """
    [수정] 5분마다 'mo' 시뮬레이션을 실행하고, DB 연결에 커넥션 풀을 사용합니다.
    """
    with app.app_context():
        print(f"[{datetime.now()}] 스케줄러 'mo' 작업 실행 시작...")
        db = None # DbManager 객체를 담을 변수
        try:
            # [핵심 수정] 풀(Pool)에서 커넥션을 가져옴
            conn_key = app.config['DEFAULT_CONN_KEY']
            pool_conn = get_db_connection(conn_key) 
            db = DbManager(pool_conn) # 가져온 연결로 DbManager 생성

            # [수정] 생성한 db 객체를 서비스 함수에 db_session 인자로 전달
            result = get_engine().run_mo_simulation(db_session=db)
            print(f"[{datetime.now()}] 스케줄러 'mo' 작업 성공: {result}")
        
        except Exception as e:
            # 트랜잭션 롤백
            if db:
                try:
                    db.conn.rollback()
                except Exception as rollback_e:
                    print(f"DB 롤백 중 오류 발생: {rollback_e}")
            print(f"[{datetime.now()}] 스케줄링 작업 중 오류 발생: {e}")
            traceback.print_exc()
            
        finally:
            # [핵심 수정] 작업이 끝나면 반드시 DB 연결을 풀에 반환
            if db:
                db.close()
                print(f"[{datetime.now()}] 스케줄러 'mo' DB 연결 (풀에) 반환.")

# --- [신규 추가] 데이터 정리 작업 ---
def _scheduled_cleanup_job_wrapper(app):
    """
    매일 오전 1시에 실행되며, 3일보다 오래된 'mo' 플래그 데이터를 삭제합니다.
    """
    with app.app_context():
        print(f"[{datetime.now()}] 스케줄러 '데이터 정리' 작업 실행 시작...")
        db = None
        try:
            # 커넥션 풀에서 연결 가져오기
            conn_key = app.config['DEFAULT_CONN_KEY']
            pool_conn = get_db_connection(conn_key)
            db = DbManager(pool_conn)

            # 테이블 이름 설정
            node_table = app.config['NODE_TABLE'] # TB_FP_SI_VAL
            link_table = app.config['LINK_TABLE'] # TB_FR_SI_VAL
            
            # 3일 전 시각 (이 시각 "미만" 데이터 삭제)
            cutoff_time = datetime.now() - timedelta(days=3)
            print(f" - 3일 이전 'mo' 데이터 삭제 (기준 시각: {cutoff_time})")

            sql_node = f"DELETE FROM {node_table} WHERE FLG = 'mo' AND RGSTR_TIME < %s"
            sql_link = f"DELETE FROM {link_table} WHERE FLG = 'mo' AND RGSTR_TIME < %s"
            
            deleted_nodes = 0
            deleted_links = 0
            
            # 쿼리 실행 및 커밋
            with db.conn.cursor() as cursor:
                cursor.execute(sql_node, (cutoff_time,))
                deleted_nodes = cursor.rowcount
                cursor.execute(sql_link, (cutoff_time,))
                deleted_links = cursor.rowcount
                
            db.commit()
            
            print(f"[{datetime.now()}] 스케줄러 '데이터 정리' 작업 성공. 삭제: [Nodes: {deleted_nodes}건, Links: {deleted_links}건]")

        except Exception as e:
            if db:
                try: db.conn.rollback()
                except Exception: pass
            print(f"[{datetime.now()}] 데이터 정리 작업 중 오류 발생: {e}")
            traceback.print_exc()
            
        finally:
            # 작업이 끝나면 반드시 DB 연결을 풀에 반환
            if db:
                db.close()
                print(f"[{datetime.now()}] 스케줄러 '데이터 정리' DB 연결 (풀에) 반환.")
# --- [신규 추가] 여기까지 ---


def init_scheduler(app):
    """
    스케줄러를 초기화하고 'mo' 시뮬레이션 및 '데이터 정리' 작업을 등록합니다.

    config 의 SCHEDULER_ENABLED 가 False 면 아무 작업도 등록하지 않고 즉시 반환한다.
    (군산 운영처럼 관망 INP 모델이 아직 사이트와 맞지 않아 5분 주기 시뮬 결과를
     실 DB 에 쓰면 안 되는 환경을 위한 스위치. 기본값 True 라 기존 동작은 그대로다.)
    """
    if not app.config.get('SCHEDULER_ENABLED', True):
        print(" * Background scheduler disabled by config (SCHEDULER_ENABLED=False).")
        return

    if not scheduler.running:
        
        # [기존] 5분 주기 'mo' 시뮬레이션 작업
        scheduler.add_job(
            func=lambda: _scheduled_mo_job_wrapper(app),
            trigger='cron',
            minute='*/5', 
            second='30',
            id='mo_simulation_job',
            name='5분 주기 모니터링 시뮬레이션'
        )
        
        # [신규] 매일 01:00 'mo' 데이터 정리 작업
        scheduler.add_job(
            func=lambda: _scheduled_cleanup_job_wrapper(app),
            trigger='cron',
            hour='1',  # 오전 1시
            minute='0', # 0분
            id='cleanup_mo_data_job',
            name='오래된 MO 데이터 정리'
        )
        
        scheduler.start()
        print(" * Background scheduler for 'mo' job started (cron trigger: */5 minutes).")
        print(" * Background scheduler for 'cleanup' job started (cron trigger: daily at 01:00).")