from django.urls import path

from apps.games.views.admin_review_management_view import (
    AdminReviewDeleteView,
    AdminReviewListview,
)
from apps.games.views.game_detail_view import GameDetailView
from apps.games.views.game_filter_view import GameFilterView
from apps.games.views.game_list_view import GameListView
from apps.games.views.game_search_view import GameSearchView

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/search", GameSearchView.as_view(), name="game-search"),
    path("games/filter", GameFilterView.as_view(), name="game-filter"),
    path("games/<int:game_id>", GameDetailView.as_view(), name="game-detail"),
    path("admin/reviews/", AdminReviewListview.as_view(), name="admin-review-list"),
    path("users/<int:user_id>/", UserInfoRetrieveView.as_view(), name="user-info"),
]
