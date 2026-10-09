# /app/__init__.py (수정 완료)

import os
import logging.config
import yaml
from flask import Flask, g, current_app # [수정] current_app 임포트
from flask_cors import CORS
from config import Config

# [핵심 수정] init_db_pool, get_db_connection 임포트
from .models.db import DbManager, load_db_config, init_db_pool, get_db_connection

def create_app(config_class=Config):
    """
    Application Factory 함수.
    ...
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app) 

    # ... (logs, temp 디렉토리 생성 및 로깅 설정 ... 기존 코드와 동일) ...
    
    with open('logging_config.yaml', 'r', encoding='utf-8') as f:
        logging_config = yaml.safe_load(f)
        logging.config.dictConfig(logging_config)
    
    app.json.ensure_ascii = False 

    # [핵심 추가] 앱 시작 시 DB 커넥션 풀을 초기화 (단 한 번 실행)
    init_db_pool(app)

    @app.before_request
    def before_request():
        """[수정] 모든 요청이 시작되기 전에 DB 커넥션을 '풀'에서 가져옵니다."""
        if 'db' not in g:
            # [수정] config에서 키를 가져옴
            conn_key = current_app.config['DEFAULT_CONN_KEY']
            
            # [수정] 풀에서 커넥션을 가져옴 (연결 생성 오버헤드 없음)
            pool_conn = get_db_connection(conn_key)
            
            # [수정] 가져온 커넥션을 DbManager에 전달
            g.db = DbManager(pool_conn)
            app.logger.debug("DB connection retrieved from pool for request.")

    @app.teardown_request
    def teardown_request(exception=None):
        """[수정] 요청이 끝난 후 DB 커넥션을 '풀'에 반환합니다."""
        db = g.pop('db', None)
        if db is not None:
            db.close() # DbManager.close()가 이제 풀에 반환하는 역할을 함
            app.logger.debug("DB connection returned to pool for request.")

    # 스케줄러 초기화 및 시작
    from . import scheduler
    # [수정] 스케줄러 초기화 전에 풀이 먼저 생성되어야 함 (순서 중요)
    scheduler.init_scheduler(app)
    
    # ... (블루프린트 등록, 헬스체크 ... 기존 코드와 동일) ...
    from .routes import bp as api_blueprint
    app.register_blueprint(api_blueprint)

    @app.route('/health')
    def health_check():
        """서버 상태를 확인하는 간단한 엔드포인트"""
        return "OK"

    return app