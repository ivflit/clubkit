from django.urls import path

from .views import (
    AdminMembershipListView,
    AdminMembershipTransitionView,
    MembershipCancelView,
    MembershipPurchaseView,
    MembershipTypeDeactivateView,
    MembershipTypeDetailView,
    MembershipTypeListCreateView,
    MyMembershipsView,
    PublicMembershipTypeListView,
)

urlpatterns = [
    # Membership Types (existing)
    path("", MembershipTypeListCreateView.as_view(), name="membership-type-list-create"),
    path("<int:pk>/", MembershipTypeDetailView.as_view(), name="membership-type-detail"),
    path("<int:pk>/deactivate/", MembershipTypeDeactivateView.as_view(), name="membership-type-deactivate"),
    path("public/", PublicMembershipTypeListView.as_view(), name="membership-type-public-list"),
    # Memberships
    path("memberships/purchase/", MembershipPurchaseView.as_view(), name="membership-purchase"),
    path("memberships/mine/", MyMembershipsView.as_view(), name="my-memberships"),
    path("memberships/<int:pk>/cancel/", MembershipCancelView.as_view(), name="membership-cancel"),
    path("memberships/admin/", AdminMembershipListView.as_view(), name="admin-membership-list"),
    path("memberships/<int:pk>/transition/", AdminMembershipTransitionView.as_view(), name="admin-membership-transition"),
]
