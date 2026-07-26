import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q

from .managers import UserManager


class User(AbstractUser):
    """Application user authenticated with an email address."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=150)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.display_name or self.email


class UserFollow(models.Model):
    """One-way relationship between two users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following_relations",
    )
    followed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower_relations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("follower", "followed"),
                name="unique_user_follow",
            ),
            models.CheckConstraint(
                condition=~Q(follower=F("followed")),
                name="prevent_self_follow",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.follower} suit {self.followed}"
