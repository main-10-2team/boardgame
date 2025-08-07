from django.urls import path

from apps.games.views.admin_genre_views import (
    AdminGenreRegisterView,
    AdminGenreUpdateView,
)
from apps.games.views.admin_review_management_view import (
    AdminReviewDeleteView,
    AdminReviewListview,
)
from apps.games.views.game_detail_view import GameDetailView
from apps.games.views.game_filter_view import GameFilterView
from apps.games.views.game_list_view import GameListView
from apps.games.views.game_review_create_view import GameReviewCreateView
from apps.games.views.game_review_delete_view import GameReviewDeleteAPIView
from apps.games.views.game_review_patch_view import GameReviewPatchAPIView
from apps.games.views.game_reviewlist_views import GameReviewListView
from apps.games.views.game_search_view import GameSearchView
from apps.games.views.likes_remove_views import LikeRemoveView
from apps.games.views.likes_views import LikeListView, LikeView
from apps.games.views.my_review_list_view import MyReviewListView

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/search", GameSearchView.as_view(), name="game-search"),
    path("games/filter", GameFilterView.as_view(), name="game-filter"),
    path("games/<int:game_id>", GameDetailView.as_view(), name="game-detail"),
    path("games/<int:game_id>/reviews", GameReviewListView.as_view(), name="game-review-list"),
    path("reviews/<int:review_id>patch", GameReviewPatchAPIView.as_view(), name="game-review-patch"),
    path("reviews/<int:review_id>delete", GameReviewDeleteAPIView.as_view(), name="game-review-delete"),
    path("games/<int:game_id>/reviews/", GameReviewCreateView.as_view(), name="game-review-create"),
    path("users/reviews/", MyReviewListView.as_view(), name="user-review-list"),
    path("admin/reviews/", AdminReviewListview.as_view(), name="admin-review-list"),
    path("admin/reviews/<int:review_id>/", AdminReviewDeleteView.as_view(), name="admin_review_delete"),
    path("admin/genres", AdminGenreRegisterView.as_view(), name="admin-genre-register"),
    path("admin/genres/<int:genre_id>", AdminGenreUpdateView.as_view(), name="admin-genre-update"),
    path("likes/", LikeView.as_view(), name="like"),
    path("likes/list/", LikeListView.as_view(), name="like-list"),
    path("likes/remove/", LikeRemoveView.as_view(), name="like_remove"),
    path("admin/genres/<int:genre_id>", AdminGenreUpdateView.as_view(), name="admin-genre-update"),
]
