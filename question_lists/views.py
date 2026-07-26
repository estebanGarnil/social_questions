from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Collaboration, Exploration, Question, Subscription
from .permissions import QuestionListPermission
from .selectors import accessible_question_lists
from .serializers import (
    CollaborationInputSerializer,
    CollaborationSerializer,
    ExplorationDetailSerializer,
    ExplorationSerializer,
    GlobalSearchSerializer,
    HomeDiscoverySerializer,
    PickRandomQuestionInputSerializer,
    PickRandomQuestionResponseSerializer,
    QuestionListSerializer,
    QuestionSerializer,
    SubscriptionSerializer,
)
from .services import (
    EmptyQuestionListError,
    pick_random_question,
    user_list_progress,
)

User = get_user_model()


def lists_with_metrics(user=None):
    """Return accessible lists with the counters required by discovery pages."""
    return (
        accessible_question_lists(user)
        .select_related("owner")
        .annotate(
            question_count=Count(
                "questions",
                filter=Q(questions__is_active=True),
                distinct=True,
            ),
            subscriber_count=Count("subscriptions", distinct=True),
            visitor_count=Count("explorations__user", distinct=True),
        )
    )


def public_lists_with_metrics():
    """Return non-empty public lists with the discovery counters."""
    return lists_with_metrics().filter(
        visibility="public",
        question_count__gt=0,
    )


@extend_schema_view(
    list=extend_schema(
        tags=["Listes"],
        summary="Lister les listes accessibles",
        parameters=[
            OpenApiParameter(
                name="scope",
                type=str,
                enum=("owned", "collaborating", "subscribed"),
                location=OpenApiParameter.QUERY,
                description="Restreint les résultats pour l'utilisateur connecté.",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Recherche dans le nom, la description et le créateur.",
            ),
        ],
    ),
    create=extend_schema(tags=["Listes"], summary="Créer une liste"),
    retrieve=extend_schema(tags=["Listes"], summary="Consulter une liste"),
    update=extend_schema(tags=["Listes"], summary="Remplacer une liste"),
    partial_update=extend_schema(tags=["Listes"], summary="Modifier une liste"),
    destroy=extend_schema(tags=["Listes"], summary="Supprimer une liste"),
)
class QuestionListViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionListSerializer
    permission_classes = [QuestionListPermission]

    def get_queryset(self):
        queryset = (
            accessible_question_lists(self.request.user)
            .select_related("owner")
            .annotate(
                question_count=Count(
                    "questions",
                    filter=Q(questions__is_active=True),
                    distinct=True,
                ),
                subscriber_count=Count("subscriptions", distinct=True),
                visitor_count=Count("explorations__user", distinct=True),
            )
        )
        scope = self.request.query_params.get("scope")
        if self.request.user.is_authenticated:
            if scope == "owned":
                queryset = queryset.filter(owner=self.request.user)
            elif scope == "collaborating":
                queryset = queryset.filter(collaborations__user=self.request.user)
            elif scope == "subscribed":
                queryset = queryset.filter(subscriptions__user=self.request.user)
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(owner__display_name__icontains=search)
            ).distinct()
        return queryset

    def perform_create(self, serializer) -> None:
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance) -> None:
        instance.soft_delete()

    @extend_schema(
        tags=["Abonnements"],
        summary="S'abonner ou se désabonner d'une liste",
        responses={200: SubscriptionSerializer},
    )
    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, pk=None):
        question_list = self.get_object()
        if request.method == "DELETE":
            Subscription.objects.filter(
                question_list=question_list,
                user=request.user,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        subscription, _ = Subscription.objects.get_or_create(
            question_list=question_list,
            user=request.user,
        )
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Questions"],
        summary="Tirer la prochaine question d'une série",
        request=PickRandomQuestionInputSerializer,
        responses={200: PickRandomQuestionResponseSerializer},
        description=(
            "Tire et enregistre une question pour l'utilisateur authentifié. "
            "Envoyer `restart_session: true` au premier appel de la page de jeu "
            "pour abandonner une éventuelle série précédente et en commencer une nouvelle."
        ),
    )
    @action(
        detail=True,
        methods=("post",),
        url_path="pick-random-question",
        permission_classes=(permissions.IsAuthenticated,),
    )
    def pick_random(self, request, pk=None):
        question_list = self.get_object()
        input_serializer = PickRandomQuestionInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        try:
            result = pick_random_question(
                user=request.user,
                question_list=question_list,
                restart_session=input_serializer.validated_data["restart_session"],
            )
        except EmptyQuestionListError:
            return Response(
                {"detail": "Cette liste ne contient aucune question active."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "question": QuestionSerializer(
                    result.question,
                    context={"request": request},
                ).data,
                "exploration_id": result.exploration.id,
                "progress": {
                    "viewed_count": result.session_viewed_count,
                    "total_count": result.session_target_count,
                    "percentage": round(
                        (result.session_viewed_count / result.session_target_count) * 100,
                        2,
                    ),
                },
                "list_progress": {
                    "viewed_count": result.list_viewed_count,
                    "total_count": result.total_count,
                    "percentage": round(
                        (result.list_viewed_count / result.total_count) * 100,
                        2,
                    ),
                },
                "session_completed": result.session_completed,
                "list_completed": result.list_completed,
            }
        )

    @extend_schema(
        tags=["Historique"],
        summary="Consulter ma progression dans une liste",
    )
    @action(
        detail=True,
        methods=("get",),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def progress(self, request, pk=None):
        question_list = self.get_object()
        return Response(
            user_list_progress(
                user=request.user,
                question_list=question_list,
            )
        )


@extend_schema(
    tags=["Découverte"],
    summary="Charger les sections de la page d'accueil",
    responses={200: HomeDiscoverySerializer},
)
class HomeDiscoveryView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = HomeDiscoverySerializer

    def get(self, request):
        followed_lists = []
        followed_users = []
        if request.user.is_authenticated:
            followed_lists = list(
                lists_with_metrics(request.user)
                .filter(subscriptions__user=request.user)
                .order_by("-updated_at")[:8]
            )
            followed_ids = request.user.following_relations.values_list("followed_id", flat=True)
            followed_users = list(
                User.objects.filter(id__in=followed_ids, is_active=True)
                .annotate(
                    follower_count=Count("follower_relations", distinct=True),
                    following_count=Count("following_relations", distinct=True),
                )
                .order_by("display_name")[:12]
            )

        discover = public_lists_with_metrics()
        if request.user.is_authenticated:
            discover = discover.exclude(explorations__user=request.user)
        discover = list(
            discover.order_by(
                "-visitor_count",
                "-subscriber_count",
                "-created_at",
            )[:12]
        )

        serializer = self.get_serializer(
            {
                "followed_lists": followed_lists,
                "followed_users": followed_users,
                "discover": discover,
            }
        )
        return Response(serializer.data)


@extend_schema(
    tags=["Découverte"],
    summary="Rechercher des listes et des utilisateurs",
    parameters=[
        OpenApiParameter(
            name="q",
            type=str,
            required=True,
            location=OpenApiParameter.QUERY,
            description="Au moins deux caractères.",
        )
    ],
    responses={200: GlobalSearchSerializer},
)
class GlobalSearchView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GlobalSearchSerializer

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"query": query, "lists": [], "users": []})

        lists = (
            lists_with_metrics(request.user)
            .filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(owner__display_name__icontains=query)
            )
            .distinct()
            .order_by("-visitor_count", "-subscriber_count", "-created_at")[:12]
        )
        users = User.objects.filter(
            is_active=True,
            display_name__icontains=query,
        )
        if request.user.is_authenticated:
            users = users.exclude(pk=request.user.pk)
        users = users.annotate(
            follower_count=Count("follower_relations", distinct=True),
            following_count=Count("following_relations", distinct=True),
        ).order_by("display_name")[:12]

        serializer = self.get_serializer({"query": query, "lists": lists, "users": users})
        return Response(serializer.data)


class QuestionListMixin:
    question_list = None

    def get_question_list(self):
        if self.question_list is None:
            self.question_list = get_object_or_404(
                accessible_question_lists(self.request.user),
                pk=self.kwargs["list_id"],
            )
        return self.question_list


@extend_schema_view(
    get=extend_schema(tags=["Questions"], summary="Lister les questions d'une liste"),
    post=extend_schema(tags=["Questions"], summary="Ajouter une question"),
)
class QuestionCollectionView(QuestionListMixin, generics.ListCreateAPIView):
    serializer_class = QuestionSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        question_list = self.get_question_list()
        return (
            question_list.questions.filter(is_active=True)
            .select_related("author")
            .order_by("position", "created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["question_list"] = self.get_question_list()
        return context

    def perform_create(self, serializer) -> None:
        question_list = self.get_question_list()
        if not question_list.can_contribute(self.request.user):
            raise PermissionDenied("Vous ne pouvez pas ajouter de question à cette liste.")
        serializer.save()


@extend_schema_view(
    get=extend_schema(tags=["Questions"], summary="Consulter une question"),
    patch=extend_schema(tags=["Questions"], summary="Modifier une question"),
    put=extend_schema(tags=["Questions"], summary="Remplacer une question"),
    delete=extend_schema(tags=["Questions"], summary="Supprimer une question"),
)
class QuestionDetailView(QuestionListMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuestionSerializer
    lookup_url_kwarg = "question_id"

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return self.get_question_list().questions.filter(is_active=True).select_related("author")

    def _can_modify(self, question: Question) -> bool:
        return question.author_id == self.request.user.id or question.question_list.can_administer(
            self.request.user
        )

    def perform_update(self, serializer) -> None:
        if not self._can_modify(self.get_object()):
            raise PermissionDenied("Vous ne pouvez modifier que vos propres questions.")
        serializer.save()

    def perform_destroy(self, instance: Question) -> None:
        if not self._can_modify(instance):
            raise PermissionDenied("Vous ne pouvez supprimer que vos propres questions.")
        instance.soft_delete()


@extend_schema_view(
    get=extend_schema(tags=["Collaborateurs"], summary="Lister les collaborateurs"),
    post=extend_schema(tags=["Collaborateurs"], summary="Ajouter un collaborateur"),
)
class CollaborationCollectionView(QuestionListMixin, generics.ListCreateAPIView):
    serializer_class = CollaborationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        question_list = self.get_question_list()
        if not question_list.can_contribute(self.request.user):
            raise PermissionDenied
        return question_list.collaborations.select_related("user")

    def create(self, request, *args, **kwargs):
        question_list = self.get_question_list()
        if not question_list.can_administer(request.user):
            raise PermissionDenied("Seul un administrateur peut ajouter un collaborateur.")

        input_serializer = CollaborationInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        user = User.objects.get(email__iexact=input_serializer.validated_data["email"])
        if user.id == question_list.owner_id:
            return Response(
                {"email": ["Le propriétaire possède déjà tous les droits."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        collaboration, created = Collaboration.objects.update_or_create(
            question_list=question_list,
            user=user,
            defaults={"role": input_serializer.validated_data["role"]},
        )
        output = CollaborationSerializer(collaboration)
        return Response(
            output.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(tags=["Collaborateurs"], summary="Consulter un collaborateur"),
    patch=extend_schema(tags=["Collaborateurs"], summary="Modifier un collaborateur"),
    put=extend_schema(tags=["Collaborateurs"], summary="Remplacer un collaborateur"),
    delete=extend_schema(tags=["Collaborateurs"], summary="Retirer un collaborateur"),
)
class CollaborationDetailView(QuestionListMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CollaborationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "collaboration_id"

    def get_queryset(self):
        question_list = self.get_question_list()
        if not question_list.can_administer(self.request.user):
            raise PermissionDenied("Seul un administrateur peut gérer les collaborateurs.")
        return question_list.collaborations.select_related("user")


@extend_schema_view(
    list=extend_schema(tags=["Historique"], summary="Lister mes parcours"),
    retrieve=extend_schema(tags=["Historique"], summary="Consulter un parcours"),
)
class ExplorationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Exploration.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Exploration.objects.filter(user=self.request.user)
            .select_related("question_list")
            .prefetch_related("question_views__question__author")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ExplorationDetailSerializer
        return ExplorationSerializer
