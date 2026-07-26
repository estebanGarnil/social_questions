from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, UserFollow

from .models import (
    Collaboration,
    Exploration,
    Question,
    QuestionList,
    QuestionView,
    Subscription,
)


class QuestionListApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="A-secure-password-2026!",
            display_name="Owner",
        )
        cls.contributor = User.objects.create_user(
            email="contributor@example.com",
            password="A-secure-password-2026!",
            display_name="Contributor",
        )
        cls.admin = User.objects.create_user(
            email="admin@example.com",
            password="A-secure-password-2026!",
            display_name="Administrator",
        )
        cls.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="A-secure-password-2026!",
            display_name="Outsider",
        )
        cls.private_list = QuestionList.objects.create(
            owner=cls.owner,
            name="Private questions",
            visibility=QuestionList.Visibility.PRIVATE,
        )
        cls.public_list = QuestionList.objects.create(
            owner=cls.owner,
            name="Public questions",
            visibility=QuestionList.Visibility.PUBLIC,
        )
        Collaboration.objects.create(
            question_list=cls.private_list,
            user=cls.contributor,
            role=Collaboration.Role.CONTRIBUTOR,
        )
        Collaboration.objects.create(
            question_list=cls.private_list,
            user=cls.admin,
            role=Collaboration.Role.ADMINISTRATOR,
        )

    def authenticate(self, user: User) -> None:
        self.client.force_authenticate(user=user)

    def test_private_list_is_only_visible_to_members(self):
        detail_url = reverse(
            "question-list-detail",
            kwargs={"pk": self.private_list.id},
        )

        outsider_response = self.client.get(detail_url)
        self.assertEqual(outsider_response.status_code, status.HTTP_404_NOT_FOUND)

        self.authenticate(self.contributor)
        member_response = self.client.get(detail_url)
        self.assertEqual(member_response.status_code, status.HTTP_200_OK)

    def test_contributor_can_only_modify_own_questions(self):
        owner_question = Question.objects.create(
            question_list=self.private_list,
            author=self.owner,
            text="Owner question",
        )
        self.authenticate(self.contributor)

        create_response = self.client.post(
            reverse(
                "question-collection",
                kwargs={"list_id": self.private_list.id},
            ),
            {"text": "Contributor question"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        own_update_response = self.client.patch(
            reverse(
                "question-detail",
                kwargs={
                    "list_id": self.private_list.id,
                    "question_id": create_response.data["id"],
                },
            ),
            {"text": "Updated contributor question"},
            format="json",
        )
        self.assertEqual(own_update_response.status_code, status.HTTP_200_OK)

        owner_update_response = self.client.patch(
            reverse(
                "question-detail",
                kwargs={
                    "list_id": self.private_list.id,
                    "question_id": owner_question.id,
                },
            ),
            {"text": "Forbidden update"},
            format="json",
        )
        self.assertEqual(owner_update_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_administrator_can_modify_another_authors_question(self):
        question = Question.objects.create(
            question_list=self.private_list,
            author=self.contributor,
            text="Original text",
        )
        self.authenticate(self.admin)

        response = self.client.patch(
            reverse(
                "question-detail",
                kwargs={
                    "list_id": self.private_list.id,
                    "question_id": question.id,
                },
            ),
            {"text": "Administrator update"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question.refresh_from_db()
        self.assertEqual(question.text, "Administrator update")

    def test_only_owner_can_delete_list(self):
        detail_url = reverse(
            "question-list-detail",
            kwargs={"pk": self.private_list.id},
        )
        self.authenticate(self.admin)
        admin_response = self.client.delete(detail_url)
        self.assertEqual(admin_response.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate(self.owner)
        owner_response = self.client.delete(detail_url)
        self.assertEqual(owner_response.status_code, status.HTTP_204_NO_CONTENT)
        self.private_list.refresh_from_db()
        self.assertFalse(self.private_list.is_active)

    def test_user_can_subscribe_to_accessible_list(self):
        self.authenticate(self.outsider)
        response = self.client.post(
            reverse(
                "question-list-subscribe",
                kwargs={"pk": self.public_list.id},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Subscription.objects.filter(
                question_list=self.public_list,
                user=self.outsider,
            ).exists()
        )


class UserScopedHistoryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner-history@example.com",
            password="A-secure-password-2026!",
            display_name="Owner",
        )
        cls.first_user = User.objects.create_user(
            email="first@example.com",
            password="A-secure-password-2026!",
            display_name="First user",
        )
        cls.second_user = User.objects.create_user(
            email="second@example.com",
            password="A-secure-password-2026!",
            display_name="Second user",
        )
        cls.question_list = QuestionList.objects.create(
            owner=cls.owner,
            name="History test",
            visibility=QuestionList.Visibility.PUBLIC,
        )
        cls.questions = [
            Question.objects.create(
                question_list=cls.question_list,
                author=cls.owner,
                text=f"Question {number}",
                position=number,
            )
            for number in range(2)
        ]

    def pick_url(self) -> str:
        return reverse(
            "question-list-pick-random",
            kwargs={"pk": self.question_list.id},
        )

    def test_random_pick_does_not_share_history_between_users(self):
        self.client.force_authenticate(user=self.first_user)
        first_pick = self.client.post(self.pick_url())
        second_pick = self.client.post(self.pick_url())

        self.assertEqual(first_pick.status_code, status.HTTP_200_OK)
        self.assertEqual(second_pick.status_code, status.HTTP_200_OK)
        self.assertNotEqual(
            first_pick.data["question"]["id"],
            second_pick.data["question"]["id"],
        )
        self.assertFalse(first_pick.data["list_completed"])
        self.assertTrue(second_pick.data["list_completed"])

        first_exploration = Exploration.objects.get(
            user=self.first_user,
            question_list=self.question_list,
        )
        self.assertEqual(first_exploration.status, Exploration.Status.COMPLETED)
        self.assertEqual(
            QuestionView.objects.filter(exploration=first_exploration).count(),
            2,
        )

        self.client.force_authenticate(user=self.second_user)
        progress_response = self.client.get(
            reverse(
                "question-list-progress",
                kwargs={"pk": self.question_list.id},
            )
        )
        self.assertEqual(progress_response.status_code, status.HTTP_200_OK)
        self.assertEqual(progress_response.data["viewed_count"], 0)
        self.assertEqual(progress_response.data["completed_count"], 0)

        other_user_pick = self.client.post(self.pick_url())
        self.assertEqual(other_user_pick.status_code, status.HTTP_200_OK)
        self.assertEqual(other_user_pick.data["progress"]["viewed_count"], 1)
        self.assertEqual(
            Exploration.objects.filter(
                user=self.second_user,
                question_list=self.question_list,
            ).count(),
            1,
        )

    def test_new_cycle_starts_after_completed_list(self):
        self.client.force_authenticate(user=self.first_user)
        self.client.post(self.pick_url())
        self.client.post(self.pick_url())
        third_pick = self.client.post(self.pick_url())

        self.assertEqual(third_pick.status_code, status.HTTP_200_OK)
        self.assertFalse(third_pick.data["list_completed"])
        self.assertEqual(
            Exploration.objects.filter(
                user=self.first_user,
                question_list=self.question_list,
            ).count(),
            2,
        )

    def test_session_stops_after_twenty_questions_and_next_session_continues_cycle(self):
        long_list = QuestionList.objects.create(
            owner=self.owner,
            name="Long party list",
            visibility=QuestionList.Visibility.PUBLIC,
        )
        Question.objects.bulk_create(
            [
                Question(
                    question_list=long_list,
                    author=self.owner,
                    text=f"Party question {number}",
                    position=number,
                )
                for number in range(25)
            ]
        )
        pick_url = reverse(
            "question-list-pick-random",
            kwargs={"pk": long_list.id},
        )
        self.client.force_authenticate(user=self.first_user)

        first_session_ids = set()
        twentieth_pick = None
        for _ in range(20):
            twentieth_pick = self.client.post(pick_url)
            first_session_ids.add(twentieth_pick.data["question"]["id"])

        self.assertEqual(len(first_session_ids), 20)
        self.assertTrue(twentieth_pick.data["session_completed"])
        self.assertFalse(twentieth_pick.data["list_completed"])
        self.assertEqual(twentieth_pick.data["progress"]["viewed_count"], 20)
        self.assertEqual(twentieth_pick.data["progress"]["total_count"], 20)
        self.assertEqual(twentieth_pick.data["list_progress"]["viewed_count"], 20)

        next_session_pick = self.client.post(pick_url)

        self.assertNotIn(next_session_pick.data["question"]["id"], first_session_ids)
        self.assertFalse(next_session_pick.data["session_completed"])
        self.assertEqual(next_session_pick.data["progress"]["total_count"], 20)
        self.assertEqual(next_session_pick.data["list_progress"]["viewed_count"], 21)
        self.assertEqual(
            Exploration.objects.filter(
                user=self.first_user,
                question_list=long_list,
            ).count(),
            2,
        )

    def test_returning_to_the_page_starts_a_new_series(self):
        long_list = QuestionList.objects.create(
            owner=self.owner,
            name="Restarted party list",
            visibility=QuestionList.Visibility.PUBLIC,
        )
        Question.objects.bulk_create(
            [
                Question(
                    question_list=long_list,
                    author=self.owner,
                    text=f"Restart question {number}",
                    position=number,
                )
                for number in range(30)
            ]
        )
        self.client.force_authenticate(user=self.first_user)
        pick_url = reverse(
            "question-list-pick-random",
            kwargs={"pk": long_list.id},
        )

        first_response = self.client.post(
            pick_url,
            {"restart_session": True},
            format="json",
        )
        second_response = self.client.post(
            pick_url,
            {"restart_session": False},
            format="json",
        )
        first_exploration = Exploration.objects.get(
            id=first_response.data["exploration_id"],
        )
        first_question_ids = {
            first_response.data["question"]["id"],
            second_response.data["question"]["id"],
        }

        returned_response = self.client.post(
            pick_url,
            {"restart_session": True},
            format="json",
        )

        first_exploration.refresh_from_db()
        returned_exploration = Exploration.objects.get(
            id=returned_response.data["exploration_id"],
        )
        self.assertEqual(first_exploration.status, Exploration.Status.COMPLETED)
        self.assertEqual(first_exploration.question_count_at_completion, 2)
        self.assertFalse(first_exploration.list_completed)
        self.assertNotEqual(returned_exploration.id, first_exploration.id)
        self.assertEqual(returned_exploration.cycle_id, first_exploration.cycle_id)
        self.assertNotIn(returned_response.data["question"]["id"], first_question_ids)
        self.assertEqual(returned_response.data["progress"]["viewed_count"], 1)
        self.assertEqual(returned_response.data["progress"]["total_count"], 20)

    def test_series_uses_seen_questions_only_when_unseen_questions_are_insufficient(self):
        short_list = QuestionList.objects.create(
            owner=self.owner,
            name="Fallback party list",
            visibility=QuestionList.Visibility.PUBLIC,
        )
        questions = [
            Question.objects.create(
                question_list=short_list,
                author=self.owner,
                text=f"Fallback question {number}",
                position=number,
            )
            for number in range(5)
        ]
        historical_exploration = Exploration.objects.create(
            user=self.first_user,
            question_list=short_list,
            question_limit=5,
        )
        QuestionView.objects.bulk_create(
            [
                QuestionView(
                    exploration=historical_exploration,
                    question=question,
                )
                for question in questions[:4]
            ]
        )
        historical_exploration.complete(4, list_completed=False)
        self.client.force_authenticate(user=self.first_user)
        pick_url = reverse(
            "question-list-pick-random",
            kwargs={"pk": short_list.id},
        )

        responses = [
            self.client.post(
                pick_url,
                {"restart_session": index == 0},
                format="json",
            )
            for index in range(5)
        ]

        returned_ids = [response.data["question"]["id"] for response in responses]
        self.assertTrue(all(response.status_code == status.HTTP_200_OK for response in responses))
        self.assertEqual(returned_ids[0], str(questions[4].id))
        self.assertEqual(len(set(returned_ids)), 5)
        self.assertEqual(set(returned_ids), {str(question.id) for question in questions})
        self.assertTrue(responses[-1].data["session_completed"])
        self.assertTrue(responses[-1].data["list_completed"])
        self.assertEqual(responses[-1].data["progress"]["viewed_count"], 5)
        self.assertEqual(responses[-1].data["progress"]["total_count"], 5)

    def test_pick_endpoint_validates_restart_session(self):
        self.client.force_authenticate(user=self.first_user)

        response = self.client.post(
            self.pick_url(),
            {"restart_session": "not-a-boolean"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("restart_session", response.data)


class HomeDiscoveryTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="discovery@example.com",
            password="A-secure-password-2026!",
            display_name="Discovery user",
        )
        cls.followed_user = User.objects.create_user(
            email="followed@example.com",
            password="A-secure-password-2026!",
            display_name="Followed user",
        )
        cls.other_user = User.objects.create_user(
            email="other-discovery@example.com",
            password="A-secure-password-2026!",
            display_name="Other user",
        )
        UserFollow.objects.create(
            follower=cls.user,
            followed=cls.followed_user,
        )

        cls.followed_list = QuestionList.objects.create(
            owner=cls.followed_user,
            name="Followed list",
            visibility=QuestionList.Visibility.PUBLIC,
        )
        Question.objects.create(
            question_list=cls.followed_list,
            author=cls.followed_user,
            text="A followed question",
        )
        Subscription.objects.create(
            question_list=cls.followed_list,
            user=cls.user,
        )
        cls.other_list = QuestionList.objects.create(
            owner=cls.other_user,
            name="Other list",
            visibility=QuestionList.Visibility.PUBLIC,
        )
        Question.objects.create(
            question_list=cls.other_list,
            author=cls.other_user,
            text="Another question",
        )
        cls.private_list = QuestionList.objects.create(
            owner=cls.other_user,
            name="Private list",
            visibility=QuestionList.Visibility.PRIVATE,
        )
        Question.objects.create(
            question_list=cls.private_list,
            author=cls.other_user,
            text="Private question",
        )

    def test_home_sections_only_contain_public_lists(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("home-discovery"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        all_lists = [*response.data["followed_lists"], *response.data["discover"]]
        self.assertNotIn(
            str(self.private_list.id),
            {str(item["id"]) for item in all_lists},
        )
        self.assertIn(
            str(self.followed_list.id),
            {str(item["id"]) for item in response.data["followed_lists"]},
        )
        self.assertIn(
            str(self.followed_user.id),
            {str(item["id"]) for item in response.data["followed_users"]},
        )

    def test_started_list_is_excluded_from_recommendations(self):
        Exploration.objects.create(
            user=self.user,
            question_list=self.other_list,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("home-discovery"))

        discover_ids = {str(item["id"]) for item in response.data["discover"]}
        self.assertNotIn(str(self.other_list.id), discover_ids)


class GlobalSearchTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="searcher@example.com",
            password="A-secure-password-2026!",
            display_name="Search player",
        )
        cls.creator = User.objects.create_user(
            email="party-creator@example.com",
            password="A-secure-password-2026!",
            display_name="Party Creator",
        )
        cls.public_list = QuestionList.objects.create(
            owner=cls.creator,
            name="Jeux de soirée",
            description="Des questions pour une soirée entre amis.",
            visibility=QuestionList.Visibility.PUBLIC,
        )
        Question.objects.create(
            question_list=cls.public_list,
            author=cls.creator,
            text="Une question publique",
        )
        cls.private_list = QuestionList.objects.create(
            owner=cls.creator,
            name="Soirée privée",
            visibility=QuestionList.Visibility.PRIVATE,
        )

    def test_public_search_returns_matching_users_and_public_lists(self):
        response = self.client.get(reverse("global-search"), {"q": "Party"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            str(self.creator.id),
            {str(user["id"]) for user in response.data["users"]},
        )

        list_response = self.client.get(reverse("global-search"), {"q": "soirée"})
        returned_ids = {str(item["id"]) for item in list_response.data["lists"]}
        self.assertIn(str(self.public_list.id), returned_ids)
        self.assertNotIn(str(self.private_list.id), returned_ids)

    def test_authenticated_owner_can_find_accessible_private_list(self):
        self.client.force_authenticate(user=self.creator)

        response = self.client.get(reverse("global-search"), {"q": "privée"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            str(self.private_list.id),
            {str(item["id"]) for item in response.data["lists"]},
        )

    def test_public_profile_lists_only_return_public_lists(self):
        profile_response = self.client.get(reverse("user-detail", kwargs={"pk": self.creator.id}))
        lists_response = self.client.get(
            reverse("user-public-lists", kwargs={"pk": self.creator.id})
        )

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(lists_response.status_code, status.HTTP_200_OK)
        returned_ids = {str(item["id"]) for item in lists_response.data["results"]}
        self.assertIn(str(self.public_list.id), returned_ids)
        self.assertNotIn(str(self.private_list.id), returned_ids)
