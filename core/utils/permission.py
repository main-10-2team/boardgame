from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


# 사용자 모델의 'role' 필드를 기반으로 관리자 권한을 확인하는 커스텀 권한 클래스입니다.
class IsAdminRole(BasePermission):

    def has_permission(self, request: Request, view: APIView) -> bool:
        # request.user가 None이거나 인증되지 않았다면 False를 반환합니다.
        if not request.user or not request.user.is_authenticated:
            return False

        # 'role' 필드는 User 모델에 명시적으로 정의되어 있으므로 hasattr 검사는 필요하지 않습니다.
        # MyPy 호환성을 위해 getattr를 사용하는 것이 더 안전할 수 있습니다.
        return request.user.role == "admin"
