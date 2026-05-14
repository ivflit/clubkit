from django.urls import path

from .views import (
    AdminEventCancelView,
    AdminEventDetailView,
    AdminEventListCreateView,
    AdminEventRegistrationsView,
    AdminEventSeriesCancelView,
    AdminEventSeriesListCreateView,
    EventCancelRegistrationView,
    EventDetailView,
    EventRegisterView,
    MemberEventListView,
    MyRegisteredEventsView,
    PublicEventListView,
)

urlpatterns = [
    # Admin CRUD
    path("", AdminEventListCreateView.as_view(), name="admin-event-list-create"),
    path("<int:pk>/", AdminEventDetailView.as_view(), name="admin-event-detail"),
    path("<int:pk>/cancel/", AdminEventCancelView.as_view(), name="admin-event-cancel"),
    path("<int:pk>/registrations/", AdminEventRegistrationsView.as_view(), name="admin-event-registrations"),
    # Admin Series
    path("series/", AdminEventSeriesListCreateView.as_view(), name="admin-event-series"),
    path("series/<int:pk>/cancel/", AdminEventSeriesCancelView.as_view(), name="admin-event-series-cancel"),
    # Public
    path("public/", PublicEventListView.as_view(), name="public-event-list"),
    path("detail/<int:pk>/", EventDetailView.as_view(), name="event-detail"),
    # Member
    path("mine/", MemberEventListView.as_view(), name="member-event-list"),
    # Registration
    path("<int:pk>/register/", EventRegisterView.as_view(), name="event-register"),
    path("<int:pk>/unregister/", EventCancelRegistrationView.as_view(), name="event-unregister"),
    path("my-registrations/", MyRegisteredEventsView.as_view(), name="my-registered-events"),
]
