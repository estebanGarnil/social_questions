from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CollaborationCollectionView,
    CollaborationDetailView,
    ExplorationViewSet,
    GlobalSearchView,
    HomeDiscoveryView,
    QuestionCollectionView,
    QuestionDetailView,
    QuestionListViewSet,
)

router = DefaultRouter()
router.register("lists", QuestionListViewSet, basename="question-list")
router.register("history", ExplorationViewSet, basename="history")

urlpatterns = [
    path(
        "discovery/home/",
        HomeDiscoveryView.as_view(),
        name="home-discovery",
    ),
    path(
        "discovery/search/",
        GlobalSearchView.as_view(),
        name="global-search",
    ),
    path(
        "lists/<uuid:list_id>/questions/",
        QuestionCollectionView.as_view(),
        name="question-collection",
    ),
    path(
        "lists/<uuid:list_id>/questions/<uuid:question_id>/",
        QuestionDetailView.as_view(),
        name="question-detail",
    ),
    path(
        "lists/<uuid:list_id>/collaborators/",
        CollaborationCollectionView.as_view(),
        name="collaboration-collection",
    ),
    path(
        "lists/<uuid:list_id>/collaborators/<uuid:collaboration_id>/",
        CollaborationDetailView.as_view(),
        name="collaboration-detail",
    ),
    path("", include(router.urls)),
]
