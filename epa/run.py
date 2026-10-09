# /run.py

from app import create_app


# app/__init__.py의 create_app 함수를 호출하여 Flask 앱 인스턴스 생성
app = create_app()

if __name__ == '__main__':
    # config.py에 정의된 설정으로 서버 실행
    app.run(
        host='0.0.0.0', 
        port=app.config['SERVER_PORT'], 
        debug=app.config['DEBUG'], 
        use_reloader=False # 디버그 모드에서 스케줄러가 두 번 실행되는 것을 방지
    )