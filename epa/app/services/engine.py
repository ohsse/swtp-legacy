# /app/services/engine.py
"""
해석 엔진 선택기.

epa 는 앱 한 벌로 여러 현장을 돌리고, 현장 구분은 config.py 마운트 교체로만 한다
(docs/tenant-bundle-guide.md 참조). 이 모듈은 그 config 값을 보고 요청을 처리할
해석 엔진 모듈을 고른다.

- 'gosan'(기본) : app.services.epa_service        — 기존 고산 구현. 무변경.
- 'gunsan'      : app.services.epa_service_gunsan — epa/epanet_gunsan CLI 어댑터.

두 모듈은 같은 함수 이름·같은 시그니처를 노출하므로 호출부는 어느 쪽인지 몰라도 된다.
"""

from flask import current_app


class EngineBusyError(RuntimeError):
    """
    해석 엔진이 다른 요청을 처리 중이라 제한 시간 안에 자리를 얻지 못했다.

    군산 엔진은 EPANET 에 한글 경로를 숨기려고 os.chdir 를 쓰는데 그것이
    프로세스 전역 상태라, 동시에 두 해석을 돌릴 수 없다. 여기서는 대기 대신
    503 으로 빨리 돌려주고 재시도를 유도한다.
    """


class EngineRequestError(ValueError):
    """
    요청 자체가 엔진이 감당할 수 없는 값이다. 서버 잘못이 아니므로 400 으로 돌려준다.

    고산 경로는 이 예외를 절대 던지지 않는다 — 라우트에 핸들러를 추가해도
    고산 동작은 바뀌지 않는다.
    """


def get_engine():
    """
    config 의 EPA_ENGINE 에 따라 해석 엔진 모듈을 돌려준다.

    키가 없으면 'gosan' 으로 본다. 기존 현장 설정(deploy/*/conf/epa/config.py)에는
    이 키가 없으므로, 그쪽은 손대지 않아도 지금까지와 똑같이 동작한다.

    import 를 함수 안에서 하는 이유: 고산 배포에서는 군산 모듈이 아예 로드되지
    않게 하려는 것이다. 군산 어댑터는 epanet_gunsan 스크립트를 sys.path 에 얹는데,
    고산 컨테이너에서 그 부작용을 만들 이유가 없다.
    """
    if current_app.config.get('EPA_ENGINE', 'gosan') == 'gunsan':
        from app.services import epa_service_gunsan as engine
    else:
        from app.services import epa_service as engine
    return engine
