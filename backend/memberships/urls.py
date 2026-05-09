from django.urls import path

from .views import (
    MembershipTypeDeactivateView,
    MembershipTypeDetailView,
    MembershipTypeListCreateView,
    PublicMembershipTypeListView,
)

urlpatterns = [
    path("", MembershipTypeListCreateView.as_view(), name="membership-type-list-create"),
    path("<int:pk>/", MembershipTypeDetailView.as_view(), name="membership-type-detail"),
    path("<int:pk>/deactivate/", MembershipTypeDeactivateView.as_view(), name="membership-type-deactivate"),
    path("public/", PublicMembershipTypeListView.as_view(), name="membership-type-public-list"),
]
