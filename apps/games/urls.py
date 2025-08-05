from django.urls import path

from apps.games.views.admin_review_management_view import (
    AdminReviewDeleteView,
    AdminReviewListview,
)
from apps.games.views.game_detail_view import GameDetailView
from apps.games.views.game_filter_view import GameFilterView
from apps.games.views.game_list_view import GameListView
from apps.games.views.game_review_create_view import GameReviewCreateView
from apps.games.views.game_review_patch_view import GameReviewPatchAPIView
from apps.games.views.game_reviewlist_views import GameReviewListView
from apps.games.views.game_search_view import GameSearchView

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/search", GameSearchView.as_view(), name="game-search"),
    path("games/filter", GameFilterView.as_view(), name="game-filter"),
    path("games/<int:game_id>", GameDetailView.as_view(), name="game-detail"),
    path("games/<int:game_id>/reviews", GameReviewListView.as_view(), name="game-review-list"),
    path("games/<int:game_id>/reviews/", GameReviewCreateView.as_view(), name="game-review-create"),
    path("reviews/<int:review_id>", GameReviewPatchAPIView.as_view(), name="game-review-patch"),
    path("admin/reviews/", AdminReviewListview.as_view(), name="admin-review-list"),
    path("admin/reviews/<int:review_id>/", AdminReviewDeleteView.as_view(), name="admin_review_delete"),
]
