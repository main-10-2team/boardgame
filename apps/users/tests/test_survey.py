from typing import Dict, List, cast

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.games.models import Game, Like
from apps.games.tests.game_samples import make_survey
from apps.users.models import User


class SurveyAPITestCase(TestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        survey = make_survey(game_count=30, liked_indices=range(5))

        users = cast(Dict[str, User], survey["users"])
        self.normal_user = users["normal_user"]
        self.suspended_user = users["suspended_user"]
        self.deleted_user = users["deleted_user"]

        self.user = self.normal_user
        self.client.force_authenticate(user=self.user)

        self.games = cast(List[Game], survey["games"])
        self.likes = cast(List[Like], survey["likes"])

    def test_survey_choice_returns_game_list(self) -> None:
        url = reverse("user-survey-choices")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("games", data)
        self.assertIsInstance(data["games"], list)
        self.assertLessEqual(len(data["games"]), 10)

        for game in data["games"]:
            self.assertIn("game_id", game)
            self.assertIn("title", game)
            self.assertIn("thumbnail_url", game)
            self.assertIn("average_rating", game)
            self.assertIsInstance(game["average_rating"], float)

    def test_survey_choice_excludes_already_liked_games(self) -> None:
        url = reverse("user-survey-choices")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        returned_ids = {g["game_id"] for g in data["games"]}
        already_liked_ids = set(Like.objects.filter(user=self.user).values_list("game__game_id", flat=True))
        self.assertTrue(returned_ids.isdisjoint(already_liked_ids))

    def test_survey_submit_creates_likes(self) -> None:
        choices_url = reverse("user-survey-choices")
        choices_res = self.client.get(choices_url)
        self.assertEqual(choices_res.status_code, 200)
        choices = choices_res.json()["games"]
        self.assertGreaterEqual(len(choices), 3, "테스트를 위해 최소 3개 후보가 필요합니다.")

        liked_game_ids = [g["game_id"] for g in choices[:3]]

        submit_url = reverse("user-survey-submit")
        response = self.client.post(submit_url, {"liked_games": liked_game_ids}, format="json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["new_like_count"], 3)
        self.assertEqual(set(data["liked_game_ids"]), set(liked_game_ids))

        self.assertEqual(Like.objects.filter(user=self.user).count(), 5 + 3)

    def test_survey_submit_with_invalid_ids(self) -> None:
        url = reverse("user-survey-submit")
        response = self.client.post(url, {"liked_games": [999999]}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("liked_games", response.json())

    def test_survey_submit_with_duplicates(self) -> None:
        url = reverse("user-survey-submit")
        duplicate_id = self.games[6].game_id
        response = self.client.post(url, {"liked_games": [duplicate_id, duplicate_id]}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("liked_games", response.json())

    def test_unauthenticated_user_cannot_access_survey(self) -> None:
        self.client.force_authenticate(user=None)
        url = reverse("user-survey-choices")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_deleted_user_gets_403(self) -> None:
        self.client.force_authenticate(user=self.deleted_user)
        url = reverse("user-survey-choices")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_suspended_user_gets_403(self) -> None:
        self.client.force_authenticate(user=self.suspended_user)
        url = reverse("user-survey-choices")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
