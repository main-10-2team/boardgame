from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game
from apps.games.serializers.game_search_serializer import GameSearchSerializer


class GameSearchView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    serializer_class = GameSearchSerializer

    @extend_schema(
        summary="게임 검색 API",
        description="게임 제목으로 키워드를 포함하는 게임을 검색합니다. 검색 결과는 관련도 순으로 정렬됩니다.",
        tags=["게임"],
        parameters=[
            OpenApiParameter(
                name="keyword",
                description="검색할 게임 제목 키워드 (필수)",
                required=True,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(name="page", description="페이지 번호", required=False, type=OpenApiTypes.INT, default=1),
            OpenApiParameter(
                name="page_size", description="페이지당 항목 수", required=False, type=OpenApiTypes.INT, default=20
            ),
        ],
        responses={200: GameSearchSerializer(many=True), 400: OpenApiTypes.OBJECT},
    )
    def get(self, request: Request) -> Response:
        keyword = request.query_params.get("keyword", "").strip()

        if not keyword:
            return Response({"detail": "검색 키워드는 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Game.objects.filter(title__icontains=keyword).order_by("-like_count")

        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"
        paginator.page_size = 20
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        if paginated_queryset is None:
            return paginator.get_paginated_response([])

        serializer = self.serializer_class(
            paginated_queryset,
            many=True,
            context={"request": request},
        )

        return paginator.get_paginated_response(serializer.data)
