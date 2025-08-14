from typing import cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User

from .serializers import RecommendationSerializer, RecommendationResponseSerializer, RecommendedGameSerializer


@extend_schema(
    summary="사용자 맞춤 게임 추천",
    description="로그인한 사용자의 활동 기록(좋아요, 높은 평점 리뷰 등)을 기반으로 개인화된 보드게임 목록을 추천합니다. 활동 기록이 없는 경우 인기 게임이나 최신 게임을 추천합니다.",
    tags=["추천"],
    responses={
        200: RecommendationResponseSerializer,
        401: OpenApiResponse(
            description="인증 실패. 유효하지 않거나 누락된 토큰.",
            response={"type": "object", "properties": {"detail": {"type": "string"}}},
        ),
        500: OpenApiResponse(
            description="서버 내부 오류",
            response={"type": "object", "properties": {"detail": {"type": "string"}}},
        ),
    },
)
class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = cast(User, request.user)

        if user.status != "active":
            return Response(
                {"detail": "비활성화된 계정입니다. 관리자에게 문의하세요."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RecommendationSerializer(user=request.user)
        try:
            recommendations = serializer.get_recommendations()

            if not recommendations:
                message = "새로운 추천 게임이 없습니다."
            else:
                message = "추천 목록을 성공적으로 불러왔습니다."

            response_data = {"message": message, "data": recommendations}
            response_serializer = RecommendationResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
