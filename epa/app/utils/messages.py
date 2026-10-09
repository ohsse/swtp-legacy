# /app/utils/messages.py
"""
API 응답에 사용될 모든 메시지를 상수로 관리하는 모듈.
"""

# 에러 메시지
BAD_REQUEST = "요청에 문제가 있습니다."
METHOD_NOT_ALLOWED = "허락되지 않은 요청 방법입니다."
FORBIDDEN = "사용권한이 없습니다."
NOT_FOUND = "요청 URL이 존재하지 않습니다."
NO_CONTENT = "데이터가 존재하지 않습니다."
INTERNAL_SERVER_ERROR = "서버 내부 오류입니다."

# 로그인 관련
USER_NOT_EXIST = "사용자가 존재하지 않습니다."
UNAUTHORIZED = "잘못된 토큰입니다."
EXPIRED_TOKEN = "만료된 토큰입니다."
PASSWORD_NOT_CORRECT = "비밀번호가 일치하지 않습니다."
LOGIN_SUCCESS = "로그인에 성공했습니다."
LOGOUT_SUCCESS = "로그아웃 되었습니다."

# CUD 관련
SELECT_SUCCESS = "정상적으로 조회되었습니다."
INSERT_SUCCESS = "정상적으로 등록되었습니다."
SAVE_SUCCESS = "정상적으로 저장되었습니다."
DELETE_SUCCESS = "정상적으로 삭제되었습니다."
INSERT_FAILURE = "데이터를 등록하는데 문제가 발생했습니다."
SAVE_FAILURE = "데이터를 저장하는데 문제가 발생했습니다."
DELETE_FAILURE = "데이터를 삭제하는데 문제가 발생했습니다."