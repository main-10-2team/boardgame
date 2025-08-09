import random
from typing import Any, Dict, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game, Like
from apps.users.models import User
from apps.users.serializers.survey_serializers import (
    SurveyChoiceResponseSerializer,
    SurveySubmitSerializer,
)


@extend_schema(
    methods=["GET"],
    summary="설문용 게임 목록 조회",
    tags=["설문"],
    description="설문에 사용할 게임 목록을 제공합니다. 인기 게임 중 아직 좋아요하지 않은 10개 게임을 랜덤으로 반환합니다.",
    responses={
        200: OpenApiResponse(
            description="설문 게임 목록 조회 성공",
            response=SurveyChoiceResponseSerializer,
        ),
        401: OpenApiResponse(
            description="비로그인 유저",
            response={
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "example": "자격 인증 헤더가 제공되지 않았습니다."
                    }
                },
                "required": ["detail"]
            }
        ),
        403: OpenApiResponse(
            description="제재/탈퇴 유저 접근 차단",
            response={
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "example": "비활성화된 계정입니다. 관리자에게 문의하세요."
                    }
                },
                "required": ["detail"]
            }
        ),
        500: OpenApiResponse(
            description="서버 내부 오류",
            response={
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "example": "서버 내부 오류가 발생했습니다."
                    }
                },
                "required": ["detail"]
            }
        )
    }
)
class UserSurveyChoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = cast(User, request.user)

        if user.status != "active":
            return Response({"detail": "비활성화된 계정입니다. 관리자에게 문의하세요."}, status=403)

        excluded_ids = Like.objects.filter(user=user).values_list("game_id", flat=True)

        candidates = list(Game.objects.exclude(game_id__in=excluded_ids).order_by("-like_count")[:30])

        if len(candidates) < 10:
            recent = list(Game.objects.exclude(game_id__in=excluded_ids).order_by("-created_at")[:30])
            ordered_candidate_ids = list(
                dict.fromkeys([g.game_id for g in candidates] + [g.game_id for g in recent])
            )
        else:
            ordered_candidate_ids = [g.game_id for g in candidates]

        pick_ids = random.sample(ordered_candidate_ids, min(10, len(ordered_candidate_ids)))

        selected = Game.objects.filter(game_id__in=pick_ids)

        serializer = SurveyChoiceResponseSerializer({"games": selected})
        return Response(serializer.data)


@extend_schema(
    methods=["POST"],
    summary="설문 응답 제출",
    tags=["설문"],
    description="선택한 게임 ID 배열을 제출하면 해당 게임에 좋아요가 등록됩니다.",
    request=SurveySubmitSerializer,
    responses={
        200: OpenApiResponse(
            description="설문 저장 성공",
            response={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "설문이 저장되었습니다."},
                    "new_like_count": {"type": "integer", "example": 3},
                    "liked_game_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "example": [1, 2, 3]
                    }
                },
                "required": ["message", "new_like_count", "liked_game_ids"]
            }
        ),
        400: OpenApiResponse(
            description="중복 또는 존재하지 않는 게임 ID 제출",
            response={
                "type": "object",
                "properties": {
                    "liked_games": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["존재하지 않는 게임 ID: [9999]", "중복된 게임 ID가 포함되어 있습니다."]
                    }
                },
                "required": ["detail"]
            }
        ),
        401: OpenApiResponse(
            description="비로그인 유저",
            response={
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "example": "자격 인증 헤더가 제공되지 않았습니다."
                    }
                },
                "required": ["detail"]
            }
        ),
        403: OpenApiResponse(
            description="제재/탈퇴 유저 접근 차단",
            response={
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "example": "비활성화된 계정입니다. 관리자에게 문의하세요."
                    }
                },
                "required": ["detail"]
            }
        ),
        500: OpenApiResponse(
            description="서버 내부 오류",
            response={
                "type": "object",
                "properties": {
                    "detail": {
                        "type": "string",
                        "example": "서버 내부 오류가 발생했습니다."
                    }
                },
                "required": ["detail"]
            }
        )
    }
)
class UserSurveySubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user = cast(User, request.user)

        if user.status != "active":
            return Response({"detail": "비활성화된 계정입니다. 관리자에게 문의하세요."}, status=403)

        serializer = SurveySubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result: Dict[str, Any] = serializer.save(user=user)

        return Response(
            {
                "message": "설문이 저장되었습니다.",
                "new_like_count": result["new_like_count"],
                "liked_game_ids": result["liked_game_ids"],
            }
        )
