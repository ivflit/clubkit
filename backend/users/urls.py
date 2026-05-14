from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import (
    DashboardView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    RoleUpdateView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="user-register"),
    path("login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="user-me"),
    path("role/<int:user_id>/", RoleUpdateView.as_view(), name="user-role-update"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("dashboard/", DashboardView.as_view(), name="user-dashboard"),
]
