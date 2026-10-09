# routes 폴더를 파이썬 패키지로 인식시키는 역할.
from flask import Blueprint

# 1. 블루프린트 객체를 여기서 생성합니다.
bp = Blueprint('api', __name__, url_prefix='/api')

from . import epa_routes, web_routes 