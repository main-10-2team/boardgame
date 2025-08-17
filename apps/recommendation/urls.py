from django.urls import path

from apps.recommendation.views.recommend_views import RecommendationView
from apps.recommendation.views.today_recommend_views import GameQuestionView

urlpatterns = [
    path("recommendations", RecommendationView.as_view(), name="user-recommendations"),
    path("today/game/questions/<int:step>/", GameQuestionView.as_view(), name="game-questions-step"),
]
