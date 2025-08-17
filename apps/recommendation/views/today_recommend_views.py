import logging
from typing import Any

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recommendation.constants.today_constants import QUESTIONS_DATA
from apps.recommendation.serializers.today_recommend_serializers import (
    GameQuestionStepSerializer,
    TodayGameRequestSerializer,
    TodayRecommendationResponseSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    summary="오늘 뭐하지 질문 API",
    description="설문의 각 단계(1~5)에 해당하는 질문과 보기 목록을 반환합니다.",
    tags=["추천"],
    parameters=[
        OpenApiParameter(
            name="step", description="질문 단계 (1~5)", required=True, type=int, location=OpenApiParameter.PATH
        ),
    ],
    # 응답(responses)에 대한 명세를 추가합니다.
    responses={
        200: OpenApiResponse(
            description="질문 조회 성공",
            examples=[
                OpenApiExample(
                    "2단계 질문 예시",
                    value={
                        "key": "categories",
                        "text": "1. 오늘은 어떤 게임이 끌리시나요?",
                        "type": "multi-select",
                        "options": [
                            {"id": 1, "label": "상상력을 자극하는 두뇌 퍼즐 같은 느낌", "value": "추상게임"},
                            {"id": 2, "label": "치열한 전략과 전술로 승부 보는 느낌", "value": "전략게임"},
                            {"id": 3, "label": "수집하고 조합하며 덱을 꾸리는 재미", "value": "컬렉터블 게임"},
                            {"id": 4, "label": "가볍게 배우고 모두가 함께 웃는 느낌", "value": "가족게임"},
                            {"id": 5, "label": "아이와 함께 쉽게 시작하는 따뜻한 느낌", "value": "어린이게임"},
                            {"id": 6, "label": "친구들과 모여 시끌벅적 즐기는 느낌", "value": "파티게임"},
                            {"id": 7, "label": "이야기에 몰입하며 세계관을 탐험하는 느낌", "value": "테마게임"},
                            {"id": 8, "label": "지휘관이 되어 전장을 읽는 밀도 높은 느낌", "value": "워게임"},
                            {"id": 9, "label": "아무거나 좋아요 / 잘 모르겠어요", "value": "상관없음"},
                        ],
                    },
                )
            ],
        ),
        400: OpenApiResponse(
            description="잘못된 요청: 유효하지 않은 질문 단계",
            response=GameQuestionStepSerializer,
        ),
        401: OpenApiResponse(
            description="인증 실패: 유효하지 않거나 누락된 토큰",
            response={"type": "object", "properties": {"detail": {"type": "string"}}},
        ),
    },
)
class GameQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, step: int) -> Response:
        serializer = GameQuestionStepSerializer(data={"step": step})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_step = serializer.validated_data["step"]
        question_data = QUESTIONS_DATA.get(validated_step)

        return Response(question_data, status=status.HTTP_200_OK)


@extend_schema(
    summary="오늘 할 게임 추천 (설문 기반)",
    description="로그인한 사용자가 설문에서 선택한 모든 답변을 받아, 조건에 맞는 보드게임 10개를 추천하여 반환합니다.",
    tags=["추천"],
    request=TodayGameRequestSerializer,
    responses={
        200: OpenApiResponse(description="추천 성공", response=TodayRecommendationResponseSerializer),
        400: OpenApiResponse(
            description="잘못된 요청: 전달된 설문 답변의 형식이 올바르지 않거나, 값이 유효하지 않습니다.",
            examples=[
                OpenApiExample(
                    "상세 오류 예시",
                    value={
                        "message": "입력값에 오류가 있습니다. 아래 내용을 확인해주세요.",
                        "errors": {
                            "categories": ["존재하지 않는 카테고리가 포함되어 있습니다: 없는카테고리"],
                            "players_range": ["인원수 범위에서 최소값은 최대값보다 클 수 없습니다."],
                        },
                    },
                )
            ],
        ),
        401: OpenApiResponse(
            description="인증 실패: 로그인이 필요하거나, 유효하지 않은 토큰입니다.",
            response={"type": "object", "properties": {"detail": {"type": "string"}}},
        ),
        503: OpenApiResponse(
            description="서비스 연결 불가: 추천 시스템(Redis)에 문제가 발생했습니다.",
            response={"type": "object", "properties": {"detail": {"type": "string"}}},
        ),
    },
)
class TodayGameRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            request_serializer = TodayGameRequestSerializer(data=request.data, context={"request": request})

            if not request_serializer.is_valid():
                logger.warning(
                    f"추천 API 유효성 검사 실패: {request_serializer.errors}", extra={"request_data": request.data}
                )
                return Response(
                    {"message": "입력값에 오류가 있습니다.", "errors": request_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            final_response_data = request_serializer.get_response()

            return Response(final_response_data, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            detail = e.detail
            error_payload: Any
            if isinstance(detail, dict):
                error_payload = detail.get("detail", detail)
            else:
                error_payload = detail
            logger.error(f"추천 API 처리 중 ValidationError 발생: {error_payload}", exc_info=True)
            if "시스템" in str(error_payload):
                return Response({"detail": error_payload}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            return Response({"detail": error_payload}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.critical(f"추천 API 처리 중 예상치 못한 오류 발생: {e}", exc_info=True)
            return Response(
                {"detail": "서버 내부에서 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
