from django.urls import path

from apps.games.views.admin_review_management_view import (
    AdminReviewDeleteView,
    AdminReviewListview,
)
from apps.games.views.game_search import GameSearchView
from apps.games.views.games import GameListView

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/search", GameSearchView.as_view(), name="game-search"),
    path("admin/reviews/", AdminReviewListview.as_view(), name="admin-review-list"),
    path("api/v1/Admin/reviews/<int:review_id>/", AdminReviewDeleteView.as_view(), name="admin_review_delete"),
]
