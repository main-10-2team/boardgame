from django.urls import path

from apps.games.views.games import GameListView

urlpatterns = [
    path("games/", GameListView.as_view(), name="game-list"),
]
