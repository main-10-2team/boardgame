from django.urls import path

from apps.recommendation.views.recommend_views import RecommendationView
from apps.recommendation.views.today_recommend_views import (
    GameQuestionView,
    TodayGameRecommendationView,
)

urlpatterns = [
    path("recommendations", RecommendationView.as_view(), name="user-recommendations"),
    path("today/game/questions/<int:step>/", GameQuestionView.as_view(), name="today-questions-step"),
    path("today/game/results/", TodayGameRecommendationView.as_view(), name="today-game-results"),
]
