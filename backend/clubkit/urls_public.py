from django.urls import path
from django.http import JsonResponse

from tenancy.views import OnboardingView

urlpatterns = [
    path("api/health/", lambda request: JsonResponse({"status": "ok"})),
    path("api/onboarding/", OnboardingView.as_view(), name="onboarding"),
]
