from django.contrib import admin

from apps.games.models import (
    Category,
    Game,
    GameCategory,
    GameGenre,
    GameImage,
    GameViewLog,
    Genre,
    Like,
    Review,
)


# Genre 모델 등록
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):  # type: ignore
    list_display = ("genre_id", "name", "created_at")
    search_fields = ("name",)


# Game 모델 등록
@admin.register(Game)
class GameAdmin(admin.ModelAdmin):  # type: ignore
    list_display = ("game_id", "title", "min_players", "max_players", "difficulty", "average_rating")
    list_filter = ("difficulty", "min_players", "max_players")
    search_fields = ("title", "description")
    readonly_fields = ("like_count", "reviews_count", "average_rating")


# GameGenre 모델 등록
@admin.register(GameGenre)
class GameGenreAdmin(admin.ModelAdmin):  # type: ignore
    list_display = ("game", "genre", "created_at")
    search_fields = ("game__title", "genre__name")


# GameImage 모델 등록
@admin.register(GameImage)
class GameImageAdmin(admin.ModelAdmin):  # type: ignore
    list_display = ("game", "game_des_img_url")
    search_fields = ("game__title",)


# Review 모델 등록
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):  # type: ignore
    list_display = ("review_id", "user", "game", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("user__email", "game__title", "content")
    raw_id_fields = ("user", "game")  # ID로 사용자를 검색할 수 있게 함


# Like 모델 등록
@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):  # type: ignore
    list_display = ("like_id", "user", "game", "created_at")
    search_fields = ("user__email", "game__title")
    raw_id_fields = ("user", "game")


# GameViewLog 모델 등록
@admin.register(GameViewLog)
class GameViewLogAdmin(admin.ModelAdmin):  # type: ignore
    list_display = ("view_id", "user", "game", "viewed_at")
    list_filter = ("viewed_at",)
    search_fields = ("user__email", "game__title")
    raw_id_fields = ("user", "game")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):# type: ignore
    list_display = ("category_id", "name", "created_at")
    search_fields = ("name",)


@admin.register(GameCategory)
class GameCategoryAdmin(admin.ModelAdmin):# type: ignore
    list_display = ("game", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("game__title", "category__name")
