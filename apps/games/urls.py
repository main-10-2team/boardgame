from django.urls import path

from apps.games.views.game_search import GameSearchView
from apps.games.views.games import GameListView

from apps.games.views.admin_review_management_view import AdminReviewListview

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("admin/reviews/", AdminReviewListview.as_view(), name="admin-review-list"),
]
