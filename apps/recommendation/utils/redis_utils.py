import logging
import os
from typing import Any, Optional, Set, Union, cast

import numpy as np
from django.core.cache import cache
from redis import Redis
from redis.commands.search.query import Query

from apps.games.models import Category, Genre

logger = logging.getLogger(__name__)


# 벡터 검색을 위한 Redis 커넥션
def get_vector_redis_connection() -> Optional[Redis]:
    try:
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        redis_conn: Redis = Redis(host=host, port=port, db=0, decode_responses=False)
        redis_conn.ping()
        return redis_conn
    except Exception:
        logger.error("벡터 검색용 Redis 연결에 실패했습니다.", exc_info=True)
        return None


# 벡터와 유사한 게임 목록 Redis에서 검색 후 반환
def find_similar_games(redis_conn: Redis, user_vector: np.ndarray, exclude_ids: Set[int], k: int = 10) -> list[int]:
    index_name = "game_index"
    num_to_request = k + len(exclude_ids)

    q = Query("*=>[KNN $K @vector $user_vec AS vector_score]").sort_by("vector_score").return_fields("id").dialect(2)
    query_params: dict[str, Any] = {
        "K": num_to_request,
        "user_vec": user_vector.astype(np.float32).tobytes(),
    }

    try:
        search_results = redis_conn.ft(index_name).search(q, query_params)
    except Exception:
        logger.error("Redis 벡터 검색에 실패했습니다.", exc_info=True)
        return []

    recommended_ids = [
        int(doc.id.split(":")[1]) for doc in search_results.docs if int(doc.id.split(":")[1]) not in exclude_ids
    ]
    return recommended_ids[:k]


# 카테고리 목록 저장
def get_all_categories() -> list[str]:
    cached_categories = cache.get("all_categories_list")
    if cached_categories is not None:
        return cast(list[str], cached_categories)

    categories = list(Category.objects.order_by("name").values_list("name", flat=True))

    cache.set("all_categories_list", categories, timeout=3600)
    return categories


# 장르 목록 저장
def get_all_genres() -> list[str]:
    cached_genres = cache.get("all_genres_list")
    if cached_genres is not None:
        return cast(list[str], cached_genres)

    genres = list(Genre.objects.order_by("name").values_list("name", flat=True))
    cache.set("all_genres_list", genres, timeout=3600)
    return genres


# 수치형 데이터 mix/max 범위 저장
def get_numerical_bounds() -> dict[str, tuple[Union[int, float], Union[int, float]]]:
    cached_bounds = cache.get("numerical_feature_bounds")
    if cached_bounds:
        return cast(dict[str, tuple[Union[int, float], Union[int, float]]], cached_bounds)

    return {
        "age": (3, 20),
        "players": (1, 10),
        "playtime": (10, 999),
        "difficulty": (1.0, 5.0),
    }
