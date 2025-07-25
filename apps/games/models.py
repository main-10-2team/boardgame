from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    age = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255, unique=True, null=False)
    like_count = models.IntegerField(default=0)
    reviews_count = models.IntegerField(default=0)
    description = models.TextField(null=True, blank=True)
    min_players = models.IntegerField(null=False)
    max_players = models.IntegerField(null=False)
    playtime_min_minutes = models.IntegerField(null=False)
    playtime_max_minutes = models.IntegerField(null=False)
    difficulty = models.FloatField(
        null=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="0-5 stars for difficulty (0=easiest, 5=hardest, two decimal places)",
    )
    image_url = models.CharField(max_length=255, null=True, blank=True)
    rules_url = models.CharField(max_length=255, null=True, blank=True)
    average_rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game"
        verbose_name = "게임"
        verbose_name_plural = "게임 목록"


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=False)
    rating = models.FloatField(
        null=False,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="0-5 in 0.5 increments (e.g., 0, 0.5, 1, ..., 5)",
    )
    content = models.CharField(max_length=500, null=True, blank=True, help_text="Max 500 chars")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "review"
        verbose_name = "리뷰"
        verbose_name_plural = "리뷰 목록"
        unique_together = ("user", "game")


class Like(models.Model):
    like_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "like"
        verbose_name = "좋아요"
        verbose_name_plural = "좋아요 목록"
        unique_together = ("user", "game")


class Genre(models.Model):
    genre_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "genre"
        verbose_name = "장르"
        verbose_name_plural = "장르 목록"


class GameGenre(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=False)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_genre"
        verbose_name = "게임 장르"
        verbose_name_plural = "게임 장르"
        unique_together = ("game", "genre")


class PlaytimeCategory(models.Model):
    playtime_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    min_minutes = models.IntegerField(null=False)
    max_minutes = models.IntegerField(null=False)

    class Meta:
        db_table = "playtime_category"
        verbose_name = "게임 시간 카테고리"
        verbose_name_plural = "게임 시간 카테고리 목록"


class GameViewLog(models.Model):
    view_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # User can be null if not logged in
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, null=True, blank=True
    )  # Game can be null if the game is deleted
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "game_view_log"
        verbose_name = "게임 조회 로그"
        verbose_name_plural = "게임 조회 로그 목록"
