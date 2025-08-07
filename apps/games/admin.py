from django.contrib import admin

from apps.games.models import PlaytimeCategory, Genre, Game, GameGenre, GameImage, Review, Like, GameViewLog


@admin.register(PlaytimeCategory)
class PlaytimeCategoryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("playtime_id", "name", "min_minutes", "max_minutes")
    search_fields = ("name",)
    ordering = ("min_minutes",)

# Genre 모델 등록
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('genre_id', 'name', 'created_at')
    search_fields = ('name',)

# Game 모델 등록
@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('game_id', 'title', 'min_players', 'max_players', 'difficulty', 'average_rating')
    list_filter = ('difficulty', 'min_players', 'max_players')
    search_fields = ('title', 'description')
    readonly_fields = ('like_count', 'reviews_count', 'average_rating')

# GameGenre 모델 등록
@admin.register(GameGenre)
class GameGenreAdmin(admin.ModelAdmin):
    list_display = ('game', 'genre', 'created_at')
    search_fields = ('game__title', 'genre__name')

# GameImage 모델 등록
@admin.register(GameImage)
class GameImageAdmin(admin.ModelAdmin):
    list_display = ('game', 'game_des_img_url')
    search_fields = ('game__title',)

# Review 모델 등록
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'user', 'game', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('user__email', 'game__title', 'content')
    raw_id_fields = ('user', 'game') # ID로 사용자를 검색할 수 있게 함

# Like 모델 등록
@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('like_id', 'user', 'game', 'created_at')
    search_fields = ('user__email', 'game__title')
    raw_id_fields = ('user', 'game')


# GameViewLog 모델 등록
@admin.register(GameViewLog)
class GameViewLogAdmin(admin.ModelAdmin):
    list_display = ('view_id', 'user', 'game', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('user__email', 'game__title')
    raw_id_fields = ('user', 'game')
