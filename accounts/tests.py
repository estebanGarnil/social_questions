from django.core.cache import cache
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


class AuthenticationThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_registration_is_throttled_after_five_requests(self):
        url = reverse("register")

        for index in range(5):
            response = self.client.post(
                url,
                {
                    "email": f"register-{index}@example.com",
                    "display_name": f"Register {index}",
                    "password": "A-secure-password-2026!",
                    "password_confirm": "A-secure-password-2026!",
                },
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        blocked_response = self.client.post(
            url,
            {
                "email": "register-blocked@example.com",
                "display_name": "Blocked",
                "password": "A-secure-password-2026!",
                "password_confirm": "A-secure-password-2026!",
            },
            format="json",
        )
        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    def test_login_is_throttled_after_ten_requests(self):
        User.objects.create_user(
            email="login-throttle@example.com",
            password="A-secure-password-2026!",
            display_name="Login throttle",
        )
        url = reverse("token-obtain-pair")

        for _ in range(10):
            response = self.client.post(
                url,
                {
                    "email": "login-throttle@example.com",
                    "password": "incorrect-password",
                },
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        blocked_response = self.client.post(
            url,
            {
                "email": "login-throttle@example.com",
                "password": "incorrect-password",
            },
            format="json",
        )
        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    def test_token_refresh_is_throttled_after_thirty_requests(self):
        url = reverse("token-refresh")

        for _ in range(30):
            response = self.client.post(
                url,
                {"refresh": "invalid-refresh-token"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        blocked_response = self.client.post(
            url,
            {"refresh": "invalid-refresh-token"},
            format="json",
        )
        self.assertEqual(
            blocked_response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )


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
