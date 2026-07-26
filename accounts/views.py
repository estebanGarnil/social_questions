from django.contrib.auth import get_user_model
from django.db.models import Count
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from question_lists.serializers import QuestionListSerializer

from .models import UserFollow
from .serializers import (
    LogoutSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        tags=["Authentification"],
        summary="Créer un compte",
    )
)
class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


@extend_schema_view(
    get=extend_schema(tags=["Authentification"], summary="Consulter mon profil"),
    patch=extend_schema(tags=["Authentification"], summary="Modifier mon profil"),
    put=extend_schema(tags=["Authentification"], summary="Remplacer mon profil"),
    delete=extend_schema(tags=["Authentification"], summary="Désactiver mon compte"),
)
class MeView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return User.objects.annotate(
            follower_count=Count("follower_relations", distinct=True),
            following_count=Count("following_relations", distinct=True),
        ).get(pk=self.request.user.pk)

    def perform_destroy(self, instance) -> None:
        instance.is_active = False
        instance.save(update_fields=("is_active",))


@extend_schema_view(
    post=extend_schema(
        tags=["Authentification"],
        summary="Se déconnecter",
        responses={204: None},
    )
)
class LogoutView(generics.GenericAPIView):
    """Blacklist the supplied refresh token."""

    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Authentification"], summary="Obtenir les tokens JWT")
class TaggedTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(tags=["Authentification"], summary="Rafraîchir les tokens JWT")
class TaggedTokenRefreshView(TokenRefreshView):
    pass


@extend_schema_view(
    list=extend_schema(
        tags=["Utilisateurs"],
        summary="Rechercher des utilisateurs",
        parameters=[
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Recherche partielle sur le nom affiché.",
            )
        ],
    ),
    retrieve=extend_schema(
        tags=["Utilisateurs"],
        summary="Consulter un utilisateur",
    ),
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        if self.request.user.is_authenticated and self.action in {"list", "following"}:
            queryset = queryset.exclude(pk=self.request.user.pk)
        queryset = queryset.annotate(
            follower_count=Count("follower_relations", distinct=True),
            following_count=Count("following_relations", distinct=True),
        ).order_by("display_name")
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(display_name__icontains=search)
        return queryset

    @extend_schema(
        tags=["Utilisateurs"],
        summary="Suivre ou ne plus suivre un utilisateur",
        responses={200: UserProfileSerializer},
    )
    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def follow(self, request, pk=None):
        target = self.get_object()
        if target.pk == request.user.pk:
            return Response(
                {"detail": "Vous ne pouvez pas vous suivre vous-même."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.method == "DELETE":
            UserFollow.objects.filter(
                follower=request.user,
                followed=target,
            ).delete()
        else:
            UserFollow.objects.get_or_create(
                follower=request.user,
                followed=target,
            )

        refreshed_target = self.get_queryset().get(pk=target.pk)
        return Response(
            self.get_serializer(
                refreshed_target,
                context={"request": request},
            ).data
        )

    @extend_schema(
        tags=["Utilisateurs"],
        summary="Lister les utilisateurs que je suis",
        responses={200: UserProfileSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=("get",),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def following(self, request):
        followed_ids = request.user.following_relations.values_list(
            "followed_id",
            flat=True,
        )
        queryset = self.get_queryset().filter(id__in=followed_ids)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Utilisateurs"],
        summary="Lister les listes publiques d'un utilisateur",
        responses={200: QuestionListSerializer(many=True)},
    )
    @action(
        detail=True,
        methods=("get",),
        url_path="lists",
        permission_classes=(permissions.AllowAny,),
    )
    def public_lists(self, request, pk=None):
        from question_lists.views import lists_with_metrics

        target = self.get_object()
        queryset = (
            lists_with_metrics().filter(owner=target, visibility="public").order_by("-created_at")
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = QuestionListSerializer(
                page,
                many=True,
                context={"request": request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = QuestionListSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)
