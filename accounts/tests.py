from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User, UserFollow


class AuthenticationTests(APITestCase):
    def test_user_can_register_login_refresh_and_read_profile(self):
        register_response = self.client.post(
            reverse("register"),
            {
                "email": "esteban@example.com",
                "display_name": "Esteban",
                "password": "A-secure-password-2026!",
                "password_confirm": "A-secure-password-2026!",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="esteban@example.com").exists())

        token_response = self.client.post(
            reverse("token-obtain-pair"),
            {
                "email": "esteban@example.com",
                "password": "A-secure-password-2026!",
            },
            format="json",
        )
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", token_response.data)
        self.assertIn("refresh", token_response.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")
        profile_response = self.client.get(reverse("me"))
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["email"], "esteban@example.com")

        refresh_response = self.client.post(
            reverse("token-refresh"),
            {"refresh": token_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)
        self.assertIn("refresh", refresh_response.data)


class UserFollowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first_user = User.objects.create_user(
            email="first-follow@example.com",
            password="A-secure-password-2026!",
            display_name="First",
        )
        cls.second_user = User.objects.create_user(
            email="second-follow@example.com",
            password="A-secure-password-2026!",
            display_name="Second",
        )

    def test_user_can_follow_and_unfollow_another_user(self):
        self.client.force_authenticate(user=self.first_user)
        url = reverse("user-follow", kwargs={"pk": self.second_user.id})

        follow_response = self.client.post(url)
        self.assertEqual(follow_response.status_code, status.HTTP_200_OK)
        self.assertTrue(follow_response.data["is_following"])
        self.assertTrue(
            UserFollow.objects.filter(
                follower=self.first_user,
                followed=self.second_user,
            ).exists()
        )

        unfollow_response = self.client.delete(url)
        self.assertEqual(unfollow_response.status_code, status.HTTP_200_OK)
        self.assertFalse(unfollow_response.data["is_following"])
        self.assertFalse(
            UserFollow.objects.filter(
                follower=self.first_user,
                followed=self.second_user,
            ).exists()
        )
