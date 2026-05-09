from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Event
from .serializers import EventSerializer, PublicEventSerializer


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
