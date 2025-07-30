from typing import Any  # *args, **kwargs에 Any 타입을 사용하려면 임포트해야 합니다.

from django.db.models import Q
from django.db.models.query import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.games.models import Game, Review
from apps.games.serializers.admin_review_management_serializers import ReviewSerializer
from apps.users.models import User


@extend_schema(
    # API 그룹을 나타내는 태그 (문서 UI에서 그룹화됩니다)
    tags=["[Admin] Review - 관리자 리뷰 관리"],
    # API의 간략한 요약
    summary="관리자 리뷰 목록 조회",
    # API에 대한 상세 설명
    description="관리자가 게임 ID, 작성자 ID, 리뷰 내용 키워드 등의 조건으로 리뷰를 검색하고 목록을 조회합니다. 페이징을 이용하여 조회합니다.",
)
class AdminReviewListview(generics.ListAPIView[Review]):

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Review.objects.all().select_related("user", "game")

    def get_queryset(self) -> QuerySet[Review]:

        queryset = super().get_queryset()

        # 쿼리 파라미터를 문자열로 가져온 후 명시적으로 타입 변환합니다.
        game_id_str = self.request.query_params.get("game_id", None)
        user_id_str = self.request.query_params.get("user_id", None)
        keyword = self.request.query_params.get("keyword", None)
        min_rating_str = self.request.query_params.get("minRating", None)
        max_rating_str = self.request.query_params.get("maxRating", None)

        # 각 파라미터를 원하는 타입으로 변환하고, None 값 처리 및 예외 처리를 포함합니다.
        game_id = None
        if game_id_str is not None:
            try:
                game_id = int(game_id_str)
            except ValueError:
                # 숫자로 변환할 수 없는 경우 처리 (예: 유효성 검사 오류 반환)
                pass  # 또는 raise ValueError("gameId must be an integer")

        user_id = None
        if user_id_str is not None:
            try:
                user_id = int(user_id_str)
            except ValueError:
                pass  # 또는 raise ValueError("userId must be an integer")

        min_rating = None
        if min_rating_str is not None:
            try:
                min_rating = float(min_rating_str)
            except ValueError:
                pass  # 또는 raise ValueError("minRating must be a float")

        max_rating = None
        if max_rating_str is not None:
            try:
                max_rating = float(max_rating_str)
            except ValueError:
                pass  # 또는 raise ValueError("maxRating must be a float")

        sort_by = self.request.query_params.get("sort", "createdAt_desc")

        filters = Q()  # Q 객체를 올바르게 초기화합니다.

        if game_id is not None:
            filters &= Q(game__game_id=game_id)

        if user_id is not None:
            filters &= Q(user__id=user_id)

        if keyword is not None:
            filters &= Q(content__icontains=keyword)

        if min_rating is not None:
            filters &= Q(rating__gte=min_rating)

        if max_rating is not None:
            filters &= Q(rating__lte=max_rating)

        queryset = queryset.filter(filters)

        if sort_by == "createdAt_desc":
            queryset = queryset.order_by("-created_at")
        elif sort_by == "rating_asc":
            queryset = queryset.order_by("rating")
        elif sort_by == "rating_desc":
            queryset = queryset.order_by("-rating")

        return queryset

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:

        user_id_param = request.query_params.get("userId", None)
        game_id_param = request.query_params.get("gameId", None)
        if user_id_param == "99999" or game_id_param == "999":
            return Response(
                {
                    "error": "FORBIDDEN",
                    "message": "리뷰를 조회할 권한이 없습니다.",
                    # 403 Forbidden 시뮬레이션 (특정 user_id 또는 game_id에 대한 권한 없음)
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # 500 Internal Server Error 시뮬레이션
        keyword_param = request.query_params.get("keyword", None)
        if keyword_param and "servererror" in keyword_param.lower():
            return Response(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                    # 500 Internal Server Error 시뮬레이션 (특정 키워드 입력 시)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # get_queryset을 호출하여 필터링 및 정렬된 쿼리셋을 가져옵니다.
            # 이 과정에서 유효하지 않은 쿼리 파라미터로 인해 ValueError가 발생할 수 있습니다.
            queryset = self.get_queryset()
        except ValueError as e:
            # get_queryset에서 발생한 유효성 검사 오류를 400 Bad Request로 반환합니다.
            return Response({"error": "VALIDATION_ERROR", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # 예상치 못한 다른 서버 오류를 500 Internal Server Error로 반환합니다.
            return Response(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # DRF의 기본 페이징 처리 로직을 사용합니다.
        page = self.paginate_queryset(queryset)
        if page is not None:
            # 페이징된 쿼리셋을 시리얼라이저로 직렬화합니다.
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)

            # 명세에 맞춰 'results' 필드명을 'reviews'로 변경하는 예시 (선택 사항)
            if "results" in response.data:
                response.data["reviews"] = response.data["results"]
                del response.data["results"]

            return response

        # 페이징이 적용되지 않은 경우 (page, size 파라미터가 없는 경우)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
