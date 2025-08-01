from typing import Any, Dict
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.exceptions import ValidationError

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
            OpenApiParameter(name="difficulty", type=OpenApiTypes.STR, description="예: 3.0, 4.5, 5.0 "),
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
                playtime_min_minutes = int(playtime_min_minutes)
                queryset = queryset.filter(playtime_min_minutes__gte=playtime_min_minutes)
            except ValueError:
                return Response({"detail": "최소 플레이 시간이 유효하지 않습니다."}, status=400)

        if playtime_max_minutes is not None:
            try:
                playtime_max_minutes = int(playtime_max_minutes)
                queryset = queryset.filter(playtime_max_minutes__lte=playtime_max_minutes)
            except ValueError:
                return Response({"detail": "최대 플레이 시간이 유효하지 않습니다."}, status=400)


        if difficulty_param:
            try:
                difficulty = float(difficulty_param)

                if 0.0 <= difficulty <= 5.0:
                    lower = round(difficulty - 0.5, 1)
                    upper = round(difficulty + 0.5, 1)

                    queryset = queryset.filter(difficulty__gte=lower, difficulty__lt=upper)
                else:
                    return Response(
                        {"detail": "난이도는 0.0부터 5.0 사이의 숫자여야 합니다."},
                        status=400
                    )
            except ValueError:
                return Response(
                    {"detail": "난이도는 숫자로 입력해야 합니다. 예: 3, 2.5, 4.0"},
                    status=400
                )

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