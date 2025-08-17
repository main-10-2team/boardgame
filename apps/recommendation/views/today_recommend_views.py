from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recommendation.constants.today_constants import QUESTIONS_DATA
from apps.recommendation.serializers.today_recommend_serializers import (
    GameQuestionStepSerializer,
)


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
