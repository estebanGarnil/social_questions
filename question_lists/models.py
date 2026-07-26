import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class TimeStampedUUIDModel(models.Model):
    """Shared UUID and timestamp fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class QuestionList(TimeStampedUUIDModel):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Publique"
        PRIVATE = "private", "Privée"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_question_lists",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("visibility", "is_active")),
            models.Index(fields=("owner", "is_active")),
        ]

    def __str__(self) -> str:
        return self.name

    def role_for(self, user) -> str | None:
        if not user or not user.is_authenticated:
            return None
        if self.owner_id == user.id:
            return "owner"
        return self.collaborations.filter(user=user).values_list("role", flat=True).first()

    def can_view(self, user) -> bool:
        if not self.is_active:
            return False
        if self.visibility == self.Visibility.PUBLIC:
            return True
        return self.role_for(user) is not None

    def can_contribute(self, user) -> bool:
        return self.role_for(user) in {
            "owner",
            Collaboration.Role.CONTRIBUTOR,
            Collaboration.Role.ADMINISTRATOR,
        }

    def can_administer(self, user) -> bool:
        return self.role_for(user) in {
            "owner",
            Collaboration.Role.ADMINISTRATOR,
        }

    def soft_delete(self) -> None:
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=("is_active", "deleted_at", "updated_at"))


class Collaboration(TimeStampedUUIDModel):
    class Role(models.TextChoices):
        CONTRIBUTOR = "contributor", "Contributeur"
        ADMINISTRATOR = "administrator", "Administrateur"

    question_list = models.ForeignKey(
        QuestionList,
        on_delete=models.CASCADE,
        related_name="collaborations",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="list_collaborations",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CONTRIBUTOR,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("question_list", "user"),
                name="unique_collaborator_per_list",
            )
        ]
        ordering = ("created_at",)

    def clean(self) -> None:
        if self.question_list_id and self.user_id:
            if self.question_list.owner_id == self.user_id:
                raise ValidationError(
                    "Le propriétaire ne doit pas être ajouté comme collaborateur."
                )


class Subscription(TimeStampedUUIDModel):
    question_list = models.ForeignKey(
        QuestionList,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="list_subscriptions",
    )
    notifications_enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("question_list", "user"),
                name="unique_subscription_per_list",
            )
        ]
        ordering = ("-created_at",)


class Question(TimeStampedUUIDModel):
    question_list = models.ForeignKey(
        QuestionList,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_questions",
    )
    text = models.TextField()
    image = models.ImageField(
        upload_to="questions/%Y/%m/",
        null=True,
        blank=True,
    )
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("position", "created_at")
        indexes = [
            models.Index(fields=("question_list", "is_active", "position")),
        ]

    def __str__(self) -> str:
        return self.text[:80]

    def soft_delete(self) -> None:
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=("is_active", "deleted_at", "updated_at"))


class Exploration(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "En cours"
        COMPLETED = "completed", "Terminé"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="list_explorations",
    )
    question_list = models.ForeignKey(
        QuestionList,
        on_delete=models.CASCADE,
        related_name="explorations",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    question_count_at_completion = models.PositiveIntegerField(default=0)
    cycle_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    question_limit = models.PositiveSmallIntegerField(default=20)
    list_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "question_list"),
                condition=Q(status="in_progress"),
                name="unique_active_exploration_per_user_list",
            )
        ]
        indexes = [
            models.Index(fields=("user", "question_list", "status")),
        ]

    def complete(self, question_count: int, *, list_completed: bool = False) -> None:
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.question_count_at_completion = question_count
        self.list_completed = list_completed
        self.save(
            update_fields=(
                "status",
                "completed_at",
                "question_count_at_completion",
                "list_completed",
                "updated_at",
            )
        )


class QuestionView(TimeStampedUUIDModel):
    exploration = models.ForeignKey(
        Exploration,
        on_delete=models.CASCADE,
        related_name="question_views",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="view_history",
    )
    shown_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("shown_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("exploration", "question"),
                name="unique_question_per_exploration",
            )
        ]
        indexes = [
            models.Index(fields=("exploration", "shown_at")),
        ]

    def clean(self) -> None:
        if self.exploration_id and self.question_id:
            if self.exploration.question_list_id != self.question.question_list_id:
                raise ValidationError("La question doit appartenir à la liste du parcours.")
