import random
from typing import Any, cast

from django.core.management.base import BaseCommand
from faker import Faker

from apps.games.models import Category, Game, Genre

GENRES = ["SF 공상 과학", "가족", "게임 시스템", "경제", "고대", "고양이", "공포", "과학", "광산", "교육", "궁궐"]
CATEGORIES = ["전략게임", "추상게임", "켈렉터블 게임", "가족게임", "어린이게임", "파티게임", "테마게임", "워게임"]


class Command(BaseCommand):

    help = "디버깅을 위한 테스트용 게임, 장르, 카테고리 데이터를 대량으로 생성합니다."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.SUCCESS("테스트 데이터 생성을 시작합니다."))

        # Faker 인스턴스 생성 (한국어 설정)
        fake = Faker("ko_KR")

        genres = [Genre.objects.get_or_create(name=name)[0] for name in GENRES]
        categories = [Category.objects.get_or_create(name=name)[0] for name in CATEGORIES]
        self.stdout.write(f"{len(genres)}개의 장르와 {len(categories)}개의 카테고리를 준비했습니다.")

        games_to_create = []
        for i in range(50):
            title = f"{fake.word()}의 {fake.word()} 모험 {i + 1}"

            game_data = {
                "title": title,
                "description": fake.paragraph(nb_sentences=3),
                "age": random.choice([8, 10, 12, 14]),
                "min_players": random.randint(1, 4),
                "max_players": random.randint(2, 8),
                "playtime_min_minutes": random.choice([15, 30, 45, 60]),
                "playtime_max_minutes": random.choice([60, 90, 120, 180]),
                "difficulty": round(random.uniform(1.0, 5.0), 2),
                "average_rating": round(random.uniform(2.5, 5.0), 2),
                "like_count": random.randint(0, 200),
                "reviews_count": random.randint(0, 50),
                "thumbnail_url": f"https://placehold.co/400x300/E5E5E5/000000?text=Game+{i + 1}",
            }
            min_p = cast(int, game_data["min_players"])
            max_p = cast(int, game_data["max_players"])
            if min_p > max_p:
                game_data["max_players"] = min_p + random.randint(1, 8)

            min_t = cast(int, game_data["playtime_min_minutes"])
            max_t = cast(int, game_data["playtime_max_minutes"])
            if min_t > max_t:
                game_data["playtime_max_minutes"] = min_t + 30

            games_to_create.append(Game(**game_data))

        Game.objects.bulk_create(games_to_create)
        self.stdout.write(f"{len(games_to_create)}개의 게임 데이터를 생성했습니다.")

        all_games = Game.objects.filter(title__in=[g.title for g in games_to_create])
        for game in all_games:
            genres_to_add = random.sample(genres, k=random.randint(1, 3))
            game.genres.set(genres_to_add)

            categories_to_add = random.sample(categories, k=random.randint(1, 3))
            game.categories.set(categories_to_add)

        self.stdout.write(self.style.SUCCESS(" 모든 테스트 데이터 생성이 완료되었습니다."))
