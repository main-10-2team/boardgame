from typing import Sequence, Iterable, Dict
from apps.games.models import (
    Game, Genre, Category, GameGenre, GameCategory, GameImage, Like
)
from apps.users.tests.user_samples import create_all_user_types


def ensure_genres(genre_names: Sequence[str]):
    genres = []
    for name in genre_names:
        g, _ = Genre.objects.get_or_create(name=name)
        genres.append(g)
    return genres


def ensure_categories(category_names: Sequence[str]):
    categories = []
    for name in category_names:
        c, _ = Category.objects.get_or_create(name=name)
        categories.append(c)
    return categories


def create_test_game(
    *,
    title: str,
    min_players: int = 2,
    max_players: int = 4,
    playtime_min_minutes: int = 30,
    playtime_max_minutes: int = 60,
    difficulty: float = 2.5,
    age: int | None = None,
    description: str | None = "게임 설명",
    thumbnail_url: str | None = "https://example.com/thumb.jpg",
    rules_url: str | None = "https://example.com/rules.pdf",
    like_count: int = 0,
    reviews_count: int = 0,
    average_rating: float = 0.0,
    genre_names=("Strategy", "Family"),
    category_names=("Card Game",),
    detail_image_urls=(),
) -> Game:
    game = Game.objects.create(
        title=title,
        age=age,
        description=description,
        min_players=min_players,
        max_players=max_players,
        playtime_min_minutes=playtime_min_minutes,
        playtime_max_minutes=playtime_max_minutes,
        difficulty=difficulty,
        thumbnail_url=thumbnail_url,
        rules_url=rules_url,
        like_count=like_count,
        reviews_count=reviews_count,
        average_rating=average_rating,
    )

    for g in ensure_genres(genre_names):
        GameGenre.objects.get_or_create(game=game, genre=g)

    for c in ensure_categories(category_names):
        GameCategory.objects.get_or_create(game=game, category=c)

    for url in detail_image_urls:
        GameImage.objects.create(game=game, game_des_img_url=url)

    return game


def create_many_games(count: int = 30):
    games = []
    for i in range(count):
        games.append(
            create_test_game(
                title=f"Game {i}",
                min_players=2,
                max_players=6,
                playtime_min_minutes=15 + i,
                playtime_max_minutes=30 + i,
                difficulty=round(1.0 + (i % 9) * 0.4, 2),
                age=8 + (i % 5),
                description=f"Game {i} description",
                thumbnail_url=f"https://example.com/thumb{i}.jpg",
                rules_url=f"https://example.com/rules{i}.pdf",
                like_count=i,
                reviews_count=0,
                average_rating=round((i % 6) * 0.5, 1),
                genre_names=("Strategy", f"Genre{i % 3}"),
                category_names=("Card Game", f"Category{i % 4}"),
                detail_image_urls=(f"https://example.com/detail{i}_1.jpg", f"https://example.com/detail{i}_2.jpg"),
            )
        )
    return games


def seed_likes(user, games, like_indices):
    likes = [Like(user=user, game=games[idx]) for idx in like_indices]
    Like.objects.bulk_create(likes)
    return likes


def make_survey(game_count=20, liked_indices=range(5)) -> Dict[str, object]:
    users = create_all_user_types()
    games = create_many_games(game_count)
    likes = seed_likes(users["normal_user"], games, liked_indices)
    return {
        "users": users,  # dict
        "games": games,  # list[Game]
        "likes": likes  # list[Like]
    }