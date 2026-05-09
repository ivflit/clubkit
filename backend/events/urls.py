from django.urls import path

from .views import (
    AdminEventCancelView,
    AdminEventDetailView,
    AdminEventListCreateView,
    EventDetailView,
    MemberEventListView,
    PublicEventListView,
)

urlpatterns = [
    # Admin CRUD
    path("", AdminEventListCreateView.as_view(), name="admin-event-list-create"),
    path("<int:pk>/", AdminEventDetailView.as_view(), name="admin-event-detail"),
    path("<int:pk>/cancel/", AdminEventCancelView.as_view(), name="admin-event-cancel"),
    # Public
    path("public/", PublicEventListView.as_view(), name="public-event-list"),
    path("detail/<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    # Member
    path("mine/", MemberEventListView.as_view(), name="member-event-list"),
]
