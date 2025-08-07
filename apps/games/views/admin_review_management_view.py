from typing import Any  # *args, **kwargs에 Any 타입을 사용하려면 임포트해야 합니다.

from django.db.models import Q
from django.db.models.query import QuerySet
from drf_spectacular.types import OpenApiTypes  # OpenApiTypes 임포트가 되어있는지 확인해주세요!
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.games.models import Game, Review
from apps.games.serializers.admin_review_management_serializers import ReviewSerializer
from apps.users.models import User


@extend_schema(
    # API 그룹을 나타내는 태그 (문서 UI에서 그룹화됩니다)
    tags=["[Admin]"],
    # API의 간략한 요약
    summary="관리자 리뷰 목록 조회",
    # API에 대한 상세 설명
    description="관리자가 게임 ID, 작성자 ID, 리뷰 내용 키워드 등의 조건으로 리뷰를 검색하고 목록을 조회합니다. 페이징을 이용하여 조회합니다.",
    parameters=[  # <-- 이 부분이 누락되었을 수 있으니 꼭 포함해주세요!
        OpenApiParameter(
            name="game_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="특정 게임의 리뷰를 조회할 경우 게임 ID",
            required=False,
        ),
        OpenApiParameter(
            name="user_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="특정 작성자의 리뷰를 조회할 경우 사용자 ID",
            required=False,
        ),
        OpenApiParameter(
            name="content",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="리뷰 내용에 포함된 키워드 (Review 모델의 content 필드)",
            required=False,
        ),
        OpenApiParameter(
            name="min_rating",
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description="최소 평점 (0.0~5.0) (Review 모델의 rating 필드)",
            required=False,
        ),
        OpenApiParameter(
            name="max_rating",
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            description="최대 평점 (0.0~5.0) (Review 모델의 rating 필드)",
            required=False,
        ),
        OpenApiParameter(
            name="page",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="조회할 페이지 번호 (기본값: 1)",
            required=False,
        ),
        OpenApiParameter(
            name="size",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="페이지당 리뷰 개수 (기본값: 20)",
            required=False,
        ),
        OpenApiParameter(
            name="sort",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="정렬 기준 (예: created_at_desc, rating_asc, rating_desc)",
            required=False,
        ),
        OpenApiParameter(
            name="status",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="리뷰 상태 (ACTIVE, DELETED, HIDDEN)",
            required=False,
        ),
    ],
)
class AdminReviewListview(generics.ListAPIView[Review]):

    serializer_class = ReviewSerializer
    permission_classes = [IsAdminUser, IsAuthenticated]
    queryset = Review.objects.all().select_related("user", "game")

    def get_queryset(self) -> QuerySet[Review]:

        queryset = super().get_queryset()

        # 쿼리 파라미터를 models.py 필드명 및 API 명세와 일치하는 스네이크 케이스로 가져옵니다.
        game_id_str = self.request.query_params.get("game_id", None)
        user_id_str = self.request.query_params.get("user_id", None)
        content = self.request.query_params.get("content", None)  # 변수명 'content'
        min_rating_str = self.request.query_params.get("min_rating", None)
        max_rating_str = self.request.query_params.get("max_rating", None)
        status_param = self.request.query_params.get("status", None)

        filters = Q()  # Q 객체를 올바르게 초기화합니다.

        # 각 파라미터를 원하는 타입으로 변환하고, None 값 처리 및 예외 처리를 포함합니다.
        if game_id_str is not None:
            try:
                game_id = int(game_id_str)
                filters &= Q(game__game_id=game_id)
            except ValueError:
                raise ValueError("game_id must be an integer.")

        if user_id_str is not None:
            try:
                user_id = int(user_id_str)
                filters &= Q(user__id=user_id)  # users.User 모델의 PK가 'id'임을 가정하여 'user__id' 사용
            except ValueError:
                raise ValueError("user_id must be an integer.")

        if content is not None:  # 'content' 변수 사용
            filters &= Q(content__icontains=content)

        if min_rating_str is not None:
            try:
                min_rating = float(min_rating_str)
                if not (0.0 <= min_rating <= 5.0):
                    raise ValueError("min_rating must be between 0.0 and 5.0.")
                filters &= Q(rating__gte=min_rating)
            except ValueError as e:
                raise ValueError(f"min_rating must be a valid number and between 0.0 and 5.0. Original error: {e}")

        if max_rating_str is not None:
            try:
                max_rating = float(max_rating_str)
                if not (0.0 <= max_rating <= 5.0):
                    raise ValueError("max_rating must be between 0.0 and 5.0.")
                filters &= Q(rating__lte=max_rating)
            except ValueError as e:
                raise ValueError(f"max_rating must be a valid number and between 0.0 and 5.0. Original error: {e}")

        # 'status' 파라미터 필터링 로직 추가 및 유효성 검사
        if status_param is not None:
            valid_statuses = ["ACTIVE", "DELETED", "HIDDEN"]
            if status_param.upper() not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of {', '.join(valid_statuses)}.")
            filters &= Q(status=status_param.upper())

        queryset = queryset.filter(filters)

        # 정렬 기준은 필터링 후에 적용됩니다.
        sort_by = self.request.query_params.get("sort", "created_at_desc")

        if sort_by == "created_at_desc":
            queryset = queryset.order_by("-created_at")
        elif sort_by == "rating_asc":
            queryset = queryset.order_by("rating")
        elif sort_by == "rating_desc":
            queryset = queryset.order_by("-rating")
        # 필요에 따라 다른 정렬 기준 추가

        return queryset

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:

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


@extend_schema(
    tags=["[Admin]"],
    summary="관리자 리뷰 삭제",
    description="review_id에 해당하는 리뷰 레코드를 시스템에서 삭제합니다. 관리자만 접근 가능합니다.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="리뷰 삭제 성공", response={"message": "리뷰가 성공적으로 삭제되었습니다."}
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="유효성 검사 실패",
            response={"error": "VALIDATION_ERROR", "message": "review_id는 정수여야 합니다."},
        ),
        status.HTTP_404_NOT_FOUND: OpenApiResponse(
            description="리뷰를 찾을 수 없을 때",
            response={"error": "NOT_FOUND", "message": "해당 ID의 리뷰를 찾을 수 없습니다."},
        ),
    },
)
class AdminReviewDeleteView(generics.DestroyAPIView[Review]):

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer  # 시리얼라이저는 필수 속성이므로 추가했습니다.
    permission_classes = [IsAdminUser, IsAuthenticated]
    lookup_field = "review_id"

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            # URL 파라미터 유효성 검사
            try:
                review_id = int(self.kwargs.get(self.lookup_field))
            except (ValueError, TypeError):
                return Response(
                    {"error": "VALIDATION_ERROR", "message": "review_id는 유효한 정수여야 합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # DRF의 기본 get_object() 메서드를 사용해 객체 가져오기
            instance = self.get_object()

            # 객체 삭제
            self.perform_destroy(instance)

            # 성공 응답
            return Response(
                {"message": "리뷰가 성공적으로 삭제되었습니다."},
                status=status.HTTP_200_OK,
            )

        except self.queryset.model.DoesNotExist:
            # get_object()에서 객체를 찾지 못했을 때의 예외 처리
            return Response(
                {"error": "NOT_FOUND", "message": "해당 ID의 리뷰를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception:
            # 예상치 못한 기타 서버 오류 처리
            return Response(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
