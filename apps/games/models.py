from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Genre(models.Model):
    genre_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "genre"
        verbose_name = "장르"
        verbose_name_plural = "장르 목록"

    def __str__(self) -> str:
        return self.name


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "category"
        verbose_name = "카테고리"
        verbose_name_plural = "카테고리 목록"

    def str(self) -> str:
        return self.name


class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    age = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255, unique=True, null=False)
    genres = models.ManyToManyField("Genre", through="GameGenre", related_name="games")  # type: ignore
    categories = models.ManyToManyField("Category", through="GameCategory", related_name="games")  # type: ignore
    like_count = models.PositiveIntegerField(default=0)
    reviews_count = models.PositiveIntegerField(default=0)
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
    thumbnail_url = models.URLField(max_length=255, null=True, blank=True)
    rules_url = models.URLField(max_length=255, null=True, blank=True)
    average_rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game"
        verbose_name = "게임"
        verbose_name_plural = "게임 목록"
        indexes = [
            models.Index(fields=["-like_count", "-average_rating"]),
        ]

    def __str__(self) -> str:
        return self.title


class GameGenre(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=False, related_name="game_genres")
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, null=False, related_name="genre_games")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_genre"
        verbose_name = "게임 장르"
        verbose_name_plural = "게임 장르"
        unique_together = ("game", "genre")

    def __str__(self) -> str:
        return f"{self.game} - {self.genre}"


class GameImage(models.Model):
    game_img_id = models.BigAutoField(primary_key=True)
    game = models.ForeignKey(
        "Game",
        on_delete=models.CASCADE,
        related_name="detail_images",
    )
    game_des_img_url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "game_image"
        verbose_name = "게임 상세 이미지"
        verbose_name_plural = "게임 상세 이미지 목록"

    def __str__(self) -> str:
        return f"GameImage for {self.game.title}"


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, null=False, related_name="reviews")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=False, related_name="reviewed_by_users")
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

    def __str__(self) -> str:
        return f"Review({self.user}) on {self.game}"


class Like(models.Model):
    like_id = models.AutoField(primary_key=True)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, null=False, related_name="likes")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=False, related_name="liked_by_users")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "like"
        verbose_name = "좋아요"
        verbose_name_plural = "좋아요 목록"
        unique_together = ("user", "game")

    def __str__(self) -> str:
        return f"{self.user} likes {self.game}"


class GameViewLog(models.Model):
    view_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, null=True, blank=True, related_name="view_logs"
    )  # User can be null if not logged in
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, null=True, blank=True, related_name="view_logs"
    )  # Game can be null if the game is deleted
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "game_view_log"
        verbose_name = "게임 조회 로그"
        verbose_name_plural = "게임 조회 로그 목록"

    def __str__(self) -> str:
        return f"{self.user} viewed {self.game}"


class GameCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=False, related_name="game_categories")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=False, related_name="category_games")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_category"
        verbose_name = "게임 카테고리"
        verbose_name_plural = "게임 카테고리"
        unique_together = ("category", "game")

    def str(self) -> str:
        return f"{self.game} - {self.category}"
