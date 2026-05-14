from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Event, EventRegistration, EventSeries
from .serializers import (
    EventRegistrationSerializer,
    EventSerializer,
    EventSeriesCreateSerializer,
    EventSeriesSerializer,
    PublicEventSerializer,
)


# ── Admin views ──────────────────────────────────────────────────


class AdminEventListCreateView(generics.ListCreateAPIView):
    """Admin: list all Events or create a new one."""

    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_tenant_admin:
            raise PermissionDenied("Only Admins can manage Events.")
        return Event.objects.all()

    def perform_create(self, serializer):
        if not self.request.user.is_tenant_admin:
            raise PermissionDenied("Only Admins can create Events.")
        serializer.save(created_by=self.request.user)


class AdminEventDetailView(generics.RetrieveUpdateAPIView):
    """Admin: retrieve or update an Event."""

    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_tenant_admin:
            raise PermissionDenied("Only Admins can manage Events.")
        return Event.objects.all()

    def perform_update(self, serializer):
        if not self.request.user.is_tenant_admin:
            raise PermissionDenied("Only Admins can update Events.")
        serializer.save()


class AdminEventCancelView(generics.GenericAPIView):
    """Admin: cancel an Event (sets status to 'cancelled')."""

    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Event.objects.all()

    def post(self, request, pk):
        if not request.user.is_tenant_admin:
            raise PermissionDenied("Only Admins can cancel Events.")
        event = self.get_object()
        if event.status == "cancelled":
            return Response(
                {"detail": "Event is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event.status = "cancelled"
        event.save(update_fields=["status"])
        return Response(EventSerializer(event).data)


class AdminEventRegistrationsView(generics.ListAPIView):
    """Admin: list all registrations for a specific Event."""

    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_tenant_admin:
            raise PermissionDenied("Only Admins can view registrations.")
        event_pk = self.kwargs["pk"]
        return EventRegistration.objects.filter(event_id=event_pk).select_related(
            "user", "event"
        )


# ── Public views ─────────────────────────────────────────────────


class PublicEventListView(generics.ListAPIView):
    """Public: list upcoming public Events."""

    serializer_class = PublicEventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Event.objects.filter(visibility="public", status="upcoming")


class EventDetailView(generics.RetrieveAPIView):
    """Public or member: view an Event's detail page.

    Public Events are visible to anyone.
    Members-only Events require an authenticated User with an active Membership.
    """

    serializer_class = PublicEventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Event.objects.all()

    def retrieve(self, request, *args, **kwargs):
        event = self.get_object()

        if event.visibility == "members_only":
            if not request.user.is_authenticated:
                return Response(
                    {"detail": "Authentication required for members-only Events."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not request.user.has_active_membership:
                return Response(
                    {"detail": "Active Membership required to view this Event."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = self.get_serializer(event)
        return Response(serializer.data)


class MemberEventListView(generics.ListAPIView):
    """Authenticated member: list all Events visible to them.

    Members with an active Membership see both public and members-only Events.
    Authenticated Users without a Membership see only public Events.
    """

    serializer_class = PublicEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Event.objects.filter(status="upcoming")
        if not self.request.user.has_active_membership:
            qs = qs.filter(visibility="public")
        return qs


# ── Registration views ───────────────────────────────────────────


class EventRegisterView(generics.GenericAPIView):
    """Register the authenticated User for an Event."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {"detail": "Event not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if event.status != "upcoming":
            return Response(
                {"detail": "Cannot register for a cancelled or past Event."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Members-only visibility check
        if event.visibility == "members_only" and not request.user.has_active_membership:
            return Response(
                {"detail": "Active Membership required to register for this Event."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Duplicate check
        if EventRegistration.objects.filter(event=event, user=request.user).exists():
            return Response(
                {"detail": "Already registered for this Event."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Capacity check
        if event.is_full:
            return Response(
                {"detail": "This Event is full."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registration = EventRegistration.objects.create(
            event=event, user=request.user
        )
        serializer = EventRegistrationSerializer(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventCancelRegistrationView(generics.GenericAPIView):
    """Cancel the authenticated User's registration for an Event."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            registration = EventRegistration.objects.get(
                event_id=pk, user=request.user
            )
        except EventRegistration.DoesNotExist:
            return Response(
                {"detail": "You are not registered for this Event."},
                status=status.HTTP_404_NOT_FOUND,
            )

        registration.delete()
        return Response(
            {"detail": "Registration cancelled."},
            status=status.HTTP_200_OK,
        )


class MyRegisteredEventsView(generics.ListAPIView):
    """List Events the authenticated User is registered for."""

    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            EventRegistration.objects.filter(user=self.request.user)
            .select_related("event", "user")
        )


# ── Series views ─────────────────────────────────────────────────


class AdminEventSeriesListCreateView(generics.GenericAPIView):
    """Admin: list all Event series or create a new recurring series with occurrences."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_tenant_admin:
            raise PermissionDenied("Only Admins can view series.")
        series = EventSeries.objects.all()
        return Response(EventSeriesSerializer(series, many=True).data)

    def post(self, request):
        if not request.user.is_tenant_admin:
            raise PermissionDenied("Only Admins can create recurring Events.")
        serializer = EventSeriesCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        series = serializer.save()
        return Response(
            EventSeriesSerializer(series).data, status=status.HTTP_201_CREATED
        )


class AdminEventSeriesCancelView(generics.GenericAPIView):
    """Admin: cancel all future occurrences of a series."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_tenant_admin:
            raise PermissionDenied("Only Admins can cancel series.")
        try:
            series = EventSeries.objects.get(pk=pk)
        except EventSeries.DoesNotExist:
            return Response(
                {"detail": "Series not found."}, status=status.HTTP_404_NOT_FOUND
            )
        now = timezone.now()
        cancelled_count = series.occurrences.filter(
            status="upcoming", date_time__gte=now
        ).update(status="cancelled")
        return Response(
            {"detail": f"Cancelled {cancelled_count} upcoming occurrences."}
        )
