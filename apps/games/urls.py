from django.urls import path

from apps.games.views.game_filter_view import GameFilterView
from apps.games.views.game_list_view import GameListView
from apps.games.views.game_search_view import GameSearchView

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
    path("games/search", GameSearchView.as_view(), name="game-search"),
    path("games/filter", GameFilterView.as_view(), name="game-filter"),
]
