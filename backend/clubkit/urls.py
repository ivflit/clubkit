from django.urls import path
from django.http import JsonResponse

from tenancy.views import BrandKitDetailView, BrandKitUpdateView, OnboardingView

urlpatterns = [
    path("api/health/", lambda request: JsonResponse({"status": "ok"})),
    path("api/onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("api/brand-kit/", BrandKitDetailView.as_view(), name="brand-kit-detail"),
    path("api/brand-kit/update/", BrandKitUpdateView.as_view(), name="brand-kit-update"),
]
