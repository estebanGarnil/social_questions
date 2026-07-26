from django.urls import path

from .views import (
    LogoutView,
    MeView,
    RegisterView,
    TaggedTokenObtainPairView,
    TaggedTokenRefreshView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", TaggedTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TaggedTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
