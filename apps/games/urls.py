from django.urls import path

from apps.games.views.admin_boardgame_views import (
    AdminGameDeleteView,
    AdminGameRegisterView,
    AdminGameUpdateView,
)
from apps.games.views.admin_category_views import (
    AdminCategoryCreateView,
    AdminCategoryDeleteView,
    AdminCategoryListView,
    AdminCategoryUpdateView,
)
from apps.games.views.admin_genre_views import (
    AdminGenreDeleteView,
    AdminGenreListView,
    AdminGenreRegisterView,
    AdminGenreUpdateView,
)
from apps.games.views.admin_review_management_view import (
    AdminReviewDeleteView,
    AdminReviewListview,
)
from apps.games.views.game_detail_view import GameDetailView
from apps.games.views.game_list_view import GameListView
from apps.games.views.game_ranking_view import GameRankListView
from apps.games.views.game_review_create_view import GameReviewCreateView
from apps.games.views.game_review_delete_view import GameReviewDeleteAPIView
from apps.games.views.game_review_patch_view import GameReviewPatchAPIView
from apps.games.views.game_reviewlist_views import GameReviewListView
from apps.games.views.likes_remove_views import LikeRemoveView
from apps.games.views.likes_views import LikeListView, LikeView
from apps.games.views.my_review_list_view import MyReviewListView
from apps.games.views.review_preview_view import ReviewPreviewView

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/<int:game_id>", GameDetailView.as_view(), name="game-detail"),
    path("games/<int:game_id>/reviews", GameReviewListView.as_view(), name="game-review-list"),
    path("reviews/<int:review_id>patch", GameReviewPatchAPIView.as_view(), name="game-review-patch"),
    path("reviews/<int:review_id>delete", GameReviewDeleteAPIView.as_view(), name="game-review-delete"),
    path("games/<int:game_id>/reviews/", GameReviewCreateView.as_view(), name="game-review-create"),
    path("games/ranking/", GameRankListView.as_view(), name="game-rank"),
    path("reviews/preview/", ReviewPreviewView.as_view(), name="review-preview"),
    path("users/reviews/", MyReviewListView.as_view(), name="user-review-list"),
    path("admin/reviews/", AdminReviewListview.as_view(), name="admin-review-list"),
    path("admin/reviews/<int:review_id>/", AdminReviewDeleteView.as_view(), name="admin_review_delete"),
    path("admin/genres/list", AdminGenreListView.as_view(), name="admin-genre-list"),
    path("admin/genres/", AdminGenreRegisterView.as_view(), name="admin-genre-register"),
    path("admin/genres/<int:genre_id>", AdminGenreUpdateView.as_view(), name="admin-genre-update"),
    path("admin/genres/delete<int:genre_id>", AdminGenreDeleteView.as_view(), name="admin-genre-delete"),
    path("likes/", LikeView.as_view(), name="like"),
    path("likes/list/", LikeListView.as_view(), name="like-list"),
    path("likes/remove/", LikeRemoveView.as_view(), name="like_remove"),
    path("admin/games/register/", AdminGameRegisterView.as_view(), name="admin-game-register"),
    path("admin/games/<int:game_id>/", AdminGameUpdateView.as_view(), name="admin-game-update"),
    path("admin/games/<int:game_id>/delete/", AdminGameDeleteView.as_view(), name="admin-game-delete"),
    path("admin/categories/Create", AdminCategoryCreateView.as_view(), name="admin-category-create"),
    path("admin/categories/List", AdminCategoryListView.as_view(), name="admin-category-list"),
    path("admin/categories/Update/<int:category_id>", AdminCategoryUpdateView.as_view(), name="admin-category-update"),
    path("admin/categories/Delete/<int:category_id>", AdminCategoryDeleteView.as_view(), name="admin-category-delete"),
]
