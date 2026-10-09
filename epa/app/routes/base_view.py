from flask.views import MethodView
from app.utils.response import api_success, api_error

class BaseView(MethodView):
    """
    모든 API 뷰의 기반이 되는 클래스.
    공통 응답 메서드를 제공합니다.
    """
    def make_success_response(self, data=None, message="Success", code=200):
        """성공 응답을 생성하는 헬퍼 메서드"""
        return api_success(data=data, message=message, code=code)
    
    def make_error_response(self, message="Error", code=400):
        """실패 응답을 생성하는 헬퍼 메서드"""
        return api_error(message=message, code=code)