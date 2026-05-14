from django.urls import path
from django.http import JsonResponse

from tenancy.views import (
    OnboardingView,
    PlatformAdminLoginView,
    PlatformAdminCreateView,
    PlatformAdminTenantListView,
    PlatformAdminTenantDetailView,
    PlatformAdminStatsView,
)

urlpatterns = [
    path("api/health/", lambda request: JsonResponse({"status": "ok"})),
    path("api/onboarding/", OnboardingView.as_view(), name="onboarding"),

    # Platform Admin
    path("api/platform-admin/login/", PlatformAdminLoginView.as_view(), name="platform-admin-login"),
    path("api/platform-admin/admins/", PlatformAdminCreateView.as_view(), name="platform-admin-create"),
    path("api/platform-admin/tenants/", PlatformAdminTenantListView.as_view(), name="platform-admin-tenants"),
    path("api/platform-admin/tenants/<int:tenant_id>/", PlatformAdminTenantDetailView.as_view(), name="platform-admin-tenant-detail"),
    path("api/platform-admin/stats/", PlatformAdminStatsView.as_view(), name="platform-admin-stats"),
]
