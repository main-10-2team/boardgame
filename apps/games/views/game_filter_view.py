from typing import Any, Dict, List, Optional

from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game
from apps.games.serializers.game_filter_serializer import GameFilterSerializer


class GameFilterView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="게임 필터링",
        description="플레이어 수, 플레이 시간, 난이도 등을 기준으로 게임 목록을 필터링합니다.",
        tags=["게임"],
        parameters=[
            OpenApiParameter(name="players", type=OpenApiTypes.STR, description="예: 2, 3-4"),
            OpenApiParameter(name="playtime_min_minutes", type=OpenApiTypes.INT, description="최소 플레이 시간(분)"),
            OpenApiParameter(name="playtime_max_minutes", type=OpenApiTypes.INT, description="최대 플레이 시간(분)"),
            OpenApiParameter(name="difficulty", type=OpenApiTypes.STR, description="예: '쉬움', '중급', '어려움' "),
            OpenApiParameter(name="page", type=OpenApiTypes.INT, description="페이지 번호"),
            # OpenApiParameter(name="page_size", type=OpenApiTypes.INT, description="페이지 당 개수"),
        ],
        responses={200: GameFilterSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        serializer = GameFilterSerializer(context={"request": request})
        queryset, filters = serializer.filter_queryset()

        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"
        paginated_qs: Optional[List[Game]] = paginator.paginate_queryset(queryset, request)

        serializer = GameFilterSerializer(paginated_qs, many=True)
        response_data = {
            "total_results": queryset.count(),
            "page": int(request.query_params.get("page", 1)),
            "limit": paginator.page_size,
            "applied_filters": filters,
            "games": serializer.data,
        }
        return paginator.get_paginated_response(response_data)
