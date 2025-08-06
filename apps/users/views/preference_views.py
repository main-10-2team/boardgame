from typing import cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Genre, PlaytimeCategory
from apps.users.models import User, UserPreferenceGenre, UserPreferencePlaytime
from apps.users.serializers.preference_serializers import PreferenceSubmitSerializer


@extend_schema(
    summary="성향 설문 제출",
    description="로그인한 사용자가 선호 장르 및 플레이타임 설문 결과를 제출합니다.",
    tags=["유저"],
    request=PreferenceSubmitSerializer,
    responses={
        200: OpenApiResponse(
            description="설문 결과 저장 성공",
            response={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "설문 결과가 성공적으로 저장되었습니다."},
                    "preferences": {
                        "type": "object",
                        "properties": {
                            "genres": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "genre_id": {"type": "integer", "example": 1},
                                        "name": {"type": "string", "example": "전략"},
                                    },
                                    "required": ["genre_id", "name"],
                                },
                            },
                            "playtimes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "playtime_id": {"type": "integer", "example": 3},
                                        "name": {"type": "string", "example": "60분 이상"},
                                        "min_minutes": {"type": "integer", "example": 60},
                                        "max_minutes": {"type": "integer", "example": 999},
                                    },
                                    "required": ["playtime_id", "name", "min_minutes", "max_minutes"],
                                },
                            },
                        },
                        "required": ["genres", "playtimes"],
                    },
                },
                "required": ["message", "preferences"],
            },
        ),
        400: OpenApiResponse(
            description="입력값 오류",
            response={
                "type": "object",
                "properties": {
                    "genres": {"type": "array", "items": {"type": "string", "example": "유효하지 않은 장르입니다."}},
                    "playtimes": {
                        "type": "array",
                        "items": {"type": "string", "example": "유효하지 않은 플레이타임 ID가 포함되어 있습니다."},
                    },
                },
            },
        ),
        401: OpenApiResponse(
            description="인증 실패",
            response={
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "자격 인증 헤더가 제공되지 않았습니다."}},
                "required": ["detail"],
            },
        ),
        500: OpenApiResponse(
            description="서버 내부 오류",
            response={
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "서버 내부 오류가 발생했습니다."}},
                "required": ["detail"],
            },
        ),
    },
)
class PreferenceSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:

        user = cast(User, request.user)

        if user.status == "deleted" or "suspended":
            return Response({"detail": "탈퇴한 계정이거나 활동 정지 계정입니다."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PreferenceSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        genre_ids = serializer.validated_data["genres"]
        playtime_ids = serializer.validated_data["playtimes"]

        # 기존 설문 결과 제거
        UserPreferenceGenre.objects.filter(user=user).delete()
        UserPreferencePlaytime.objects.filter(user=user).delete()

        # 새 장르 저장
        UserPreferenceGenre.objects.bulk_create([UserPreferenceGenre(user=user, genre_id=gid) for gid in genre_ids])

        # 새 플레이타임 저장
        UserPreferencePlaytime.objects.bulk_create(
            [UserPreferencePlaytime(user=user, playtime_category_id=pid) for pid in playtime_ids]
        )

        genre_objs = Genre.objects.filter(pk__in=genre_ids)
        playtime_objs = PlaytimeCategory.objects.filter(pk__in=playtime_ids)

        return Response(
            {
                "message": "설문 결과가 성공적으로 저장되었습니다.",
                "preferences": {
                    "genres": [{"genre_id": g.pk, "name": g.name} for g in genre_objs],
                    "playtimes": [
                        {
                            "playtime_id": p.pk,
                            "name": p.name,
                            "min_minutes": p.min_minutes,
                            "max_minutes": p.max_minutes,
                        }
                        for p in playtime_objs
                    ],
                },
            },
            status=status.HTTP_200_OK,
        )
