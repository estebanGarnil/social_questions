from django.contrib.auth import get_user_model
from django.db.models import Max
from rest_framework import serializers

from accounts.serializers import PublicUserSerializer, UserProfileSerializer

from .models import (
    Collaboration,
    Exploration,
    Question,
    QuestionList,
    QuestionView,
    Subscription,
)
from .services import user_list_progress

User = get_user_model()


class QuestionListSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionList
        fields = ("id", "name", "visibility")


class QuestionListSerializer(serializers.ModelSerializer):
    owner = PublicUserSerializer(read_only=True)
    question_count = serializers.SerializerMethodField()
    subscriber_count = serializers.SerializerMethodField()
    visitor_count = serializers.SerializerMethodField()
    current_user_role = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = QuestionList
        fields = (
            "id",
            "owner",
            "name",
            "description",
            "visibility",
            "question_count",
            "subscriber_count",
            "visitor_count",
            "current_user_role",
            "is_subscribed",
            "progress",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "question_count",
            "subscriber_count",
            "visitor_count",
            "current_user_role",
            "is_subscribed",
            "progress",
            "created_at",
            "updated_at",
        )

    def get_question_count(self, obj: QuestionList) -> int:
        annotated = getattr(obj, "question_count", None)
        return annotated if annotated is not None else obj.questions.filter(is_active=True).count()

    def get_subscriber_count(self, obj: QuestionList) -> int:
        annotated = getattr(obj, "subscriber_count", None)
        return annotated if annotated is not None else obj.subscriptions.count()

    def get_visitor_count(self, obj: QuestionList) -> int:
        annotated = getattr(obj, "visitor_count", None)
        if annotated is not None:
            return annotated
        return obj.explorations.values("user_id").distinct().count()

    def get_current_user_role(self, obj: QuestionList) -> str | None:
        request = self.context.get("request")
        return obj.role_for(request.user) if request else None

    def get_is_subscribed(self, obj: QuestionList) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.subscriptions.filter(user=request.user).exists()

    def get_progress(self, obj: QuestionList) -> dict | None:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        return user_list_progress(user=request.user, question_list=obj)


class QuestionSerializer(serializers.ModelSerializer):
    author = PublicUserSerializer(read_only=True)
    question_list_id = serializers.UUIDField(source="question_list.id", read_only=True)

    class Meta:
        model = Question
        fields = (
            "id",
            "question_list_id",
            "author",
            "text",
            "image",
            "position",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "question_list_id",
            "author",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data: dict) -> Question:
        question_list = self.context["question_list"]
        if "position" not in validated_data:
            maximum = (
                question_list.questions.filter(is_active=True)
                .aggregate(maximum=Max("position"))
                .get("maximum")
            )
            validated_data["position"] = (maximum if maximum is not None else -1) + 1

        return Question.objects.create(
            question_list=question_list,
            author=self.context["request"].user,
            **validated_data,
        )


class CollaborationSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = Collaboration
        fields = ("id", "user", "role", "created_at", "updated_at")
        read_only_fields = ("id", "user", "created_at", "updated_at")


class CollaborationInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Collaboration.Role.choices)

    def validate_email(self, value: str) -> str:
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Aucun utilisateur ne possède cet e-mail.")
        return value.lower()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = (
            "id",
            "question_list",
            "notifications_enabled",
            "created_at",
        )
        read_only_fields = ("id", "question_list", "created_at")


class ProgressSerializer(serializers.Serializer):
    viewed_count = serializers.IntegerField()
    total_count = serializers.IntegerField()
    percentage = serializers.FloatField()


class PickRandomQuestionInputSerializer(serializers.Serializer):
    restart_session = serializers.BooleanField(required=False, default=False)


class PickRandomQuestionResponseSerializer(serializers.Serializer):
    question = QuestionSerializer()
    exploration_id = serializers.UUIDField()
    progress = ProgressSerializer()
    list_progress = ProgressSerializer()
    session_completed = serializers.BooleanField()
    list_completed = serializers.BooleanField()


class HomeDiscoverySerializer(serializers.Serializer):
    followed_lists = QuestionListSerializer(many=True)
    followed_users = UserProfileSerializer(many=True)
    discover = QuestionListSerializer(many=True)


class GlobalSearchSerializer(serializers.Serializer):
    query = serializers.CharField()
    lists = QuestionListSerializer(many=True)
    users = UserProfileSerializer(many=True)


class QuestionViewSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = QuestionView
        fields = ("id", "question", "shown_at")


class ExplorationSerializer(serializers.ModelSerializer):
    question_list = QuestionListSummarySerializer(read_only=True)
    viewed_count = serializers.IntegerField(
        source="question_views.count",
        read_only=True,
    )

    class Meta:
        model = Exploration
        fields = (
            "id",
            "question_list",
            "status",
            "viewed_count",
            "question_limit",
            "list_completed",
            "question_count_at_completion",
            "created_at",
            "completed_at",
        )


class ExplorationDetailSerializer(ExplorationSerializer):
    question_views = QuestionViewSerializer(many=True, read_only=True)

    class Meta(ExplorationSerializer.Meta):
        fields = ExplorationSerializer.Meta.fields + ("question_views",)
