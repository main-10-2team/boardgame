import logging
from typing import Any

import numpy as np
import redis
from django.core.management.base import BaseCommand
from redis import Redis
from redis.commands.search.field import TextField, VectorField
from sklearn.preprocessing import MinMaxScaler, MultiLabelBinarizer  # type: ignore

from apps.games.models import Category, Game, Genre
from apps.recommendation.utils.redis_utils import get_vector_redis_connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "게임 데이터를 벡터로 변환하여 Redis에 동기화하고, 검색 인덱스를 생성합니다."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.SUCCESS("Redis 데이터 동기화 시작"))
        logger.info("Redis 데이터 동기화를 시작합니다.")

        r = get_vector_redis_connection()
        if r is None:
            self.stdout.write(self.style.ERROR("Redis 연결 실패. 작업을 중단합니다."))
            return

        try:
            all_genres = list(Genre.objects.order_by('name').values_list("name", flat=True))
            all_categories = list(Category.objects.order_by('name').values_list("name", flat=True))
            games = Game.objects.prefetch_related("genres", "categories").all()

            if not games.exists():
                self.stdout.write(self.style.WARNING("게임 데이터가 없습니다. 동기화를 건너뜁니다."))
                logger.warning("데이터베이스에 동기화할 게임이 없습니다.")
                return

            genre_binarizer = MultiLabelBinarizer(classes=all_genres)
            category_binarizer = MultiLabelBinarizer(classes=all_categories)
            scaler = MinMaxScaler()

            numerical_features = np.array(
                [
                    [
                        g.age or 0,
                        g.min_players,
                        g.max_players,
                        g.playtime_min_minutes,
                        g.playtime_max_minutes,
                        g.difficulty,
                    ]
                    for g in games
                ]
            )
            scaled_numerical_features = scaler.fit_transform(numerical_features)

            vector_dimension = len(all_genres) + len(all_categories) + scaled_numerical_features.shape[1]

            pipeline = r.pipeline(transaction=False)
            for i, game in enumerate(games):
                genre_vector = genre_binarizer.fit_transform([list(game.genres.values_list("name", flat=True))])[0]
                category_vector = category_binarizer.fit_transform(
                    [list(game.categories.values_list("name", flat=True))]
                )[0]

                game_vector = (
                    np.concatenate([genre_vector, category_vector, scaled_numerical_features[i]])
                    .astype(np.float32)
                    .tobytes()
                )

                pipeline.hset(f"game:{game.game_id}", mapping={"title": game.title, "vector": game_vector})

            self.stdout.write(f"{len(games)}개 게임을 파이프라인으로 전송합니다.")
            logger.info(f"{len(games)}개 게임에 대한 Redis 파이프라인을 실행합니다.")

            pipeline.execute()

            self.stdout.write(self.style.SUCCESS("데이터 동기화 완료"))
            logger.info("게임 데이터 동기화가 성공적으로 완료되었습니다.")

            self.create_redis_search_index(r, vector_dimension)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"동기화 중 오류 발생: {e}"))
            logger.critical("게임 동기화 중 예상치 못한 오류가 발생했습니다.", exc_info=True)

    def create_redis_search_index(self, r: Redis, dim: int) -> None:
        schema = [
            TextField("title"),
            VectorField("vector", "HNSW", {"TYPE": "FLOAT32", "DIM": dim, "DISTANCE_METRIC": "COSINE"}),
        ]
        index_name = "game_index"

        try:
            r.ft(index_name).dropindex(delete_documents=True)
            self.stdout.write("기존 인덱스를 삭제했습니다.")
            logger.info(f"기존 검색 인덱스를 삭제했습니다: {index_name}")
        except redis.exceptions.ResponseError:
            self.stdout.write("새로운 인덱스를 생성합니다.")
            logger.info(f"검색 인덱스 '{index_name}'가 존재하지 않아 새로 생성합니다.")

        r.ft(index_name).create_index(schema)
        self.stdout.write(self.style.SUCCESS(f"'{index_name}' 인덱스 생성 완료."))
        logger.info(f"검색 인덱스 '{index_name}'가 성공적으로 생성되었습니다.")
