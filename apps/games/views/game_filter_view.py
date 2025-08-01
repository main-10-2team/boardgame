from typing import Any, Dict

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
        players_param = request.query_params.get("players")
        playtime_min_minutes = request.query_params.get("playtime_min_minutes")
        playtime_max_minutes = request.query_params.get("playtime_max_minutes")
        difficulty_param = request.query_params.get("difficulty")

        players = None
        play_time = None
        difficulty = None

        queryset = Game.objects.all()

        from rest_framework.exceptions import ValidationError

        if players_param:
            try:
                players = int(players_param)
                if players < 0:
                    raise ValidationError({"detail": "플레이어 수는 1 이상이어야 합니다."})
                queryset = queryset.filter(min_players__lte=players, max_players__gte=players)
            except ValueError:
                raise ValidationError({"detail": "플레이어 수는 숫자여야 합니다. 예: 2, 4, 6 등"})

        if playtime_min_minutes is not None:
            try:
                playtime_min = int(playtime_min_minutes)
                queryset = queryset.filter(playtime_min_minutes__gte=playtime_min)
            except ValueError:
                return Response({"detail": "최소 플레이 시간이 유효하지 않습니다."}, status=400)

        if playtime_max_minutes is not None:
            try:
                playtime_max = int(playtime_max_minutes)
                queryset = queryset.filter(playtime_max_minutes__lte=playtime_max)
            except ValueError:
                return Response({"detail": "최대 플레이 시간이 유효하지 않습니다."}, status=400)

        difficulty_map = {
            "쉬움": (0.0, 2.0),
            "중급": (2.0, 4.0),
            "어려움": (4.0, 5.0),
        }

        if difficulty_param:
            if difficulty_param in difficulty_map:
                lower, upper = difficulty_map[difficulty_param]
                difficulty = difficulty_param
                queryset = queryset.filter(difficulty__gte=lower, difficulty__lt=upper)
            else:
                try:
                    difficulty_float = float(difficulty_param)
                    if 0.0 <= difficulty_float <= 5.0:
                        lower = round(difficulty_float - 0.5, 1)
                        upper = round(difficulty_float + 0.5, 1)
                        difficulty = str(difficulty_float)
                        queryset = queryset.filter(difficulty__gte=lower, difficulty__lt=upper)
                    else:
                        raise ValueError
                except ValueError:
                    return Response({"detail": "난이도는 '쉬움', '중급', '어려움' 중 하나여야합니다."}, status=400)

        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"
        paginated_qs = paginator.paginate_queryset(queryset, request)

        serializer = GameFilterSerializer(paginated_qs, many=True)
        response_data: Dict[str, Any] = {
            "total_results": queryset.count(),
            "page": int(request.query_params.get("page", 1)),
            "limit": paginator.page_size,
            "applied_filters": {
                "players": players,
                "play_time": play_time,
                "difficulty": difficulty,
            },
            "games": serializer.data,
        }

        return paginator.get_paginated_response(response_data)
