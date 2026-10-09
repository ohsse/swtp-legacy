# /app/utils/response.py

from dataclasses import dataclass, asdict
from typing import Any, Generic, TypeVar
from flask import jsonify

# Java의 Generic <O>와 유사하게 타입 변수 선언
T = TypeVar('T')

@dataclass
class ResponseObject(Generic[T]):
    """
    표준 API 응답 구조를 위한 데이터클래스.
    """
    code: int
    message: str
    data: T | None = None


def api_success(data: Any = None, message: str = "Success", code: int = 200):
    """
    성공 API 응답 객체를 생성하고 Flask Response로 변환합니다.
    """
    # ResponseObject 인스턴스 생성
    response_obj = ResponseObject(code=code, message=message, data=data)
    # dataclass를 dict로 변환하여 jsonify
    return jsonify(asdict(response_obj))

def api_error(message: str = "Error", code: int = 400):
    """
    실패 API 응답 객체를 생성하고 Flask Response로 변환합니다.
    """
    response_obj = ResponseObject(code=code, message=message, data=None)
    # 에러 응답 시 HTTP 상태 코드도 함께 반환
    return jsonify(asdict(response_obj)), code