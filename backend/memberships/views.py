from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Membership, MembershipType
from .serializers import (
    MembershipPurchaseSerializer,
    MembershipSerializer,
    MembershipTypeSerializer,
    PublicMembershipTypeSerializer,
)


class IsAdminUser:
    """Mixin that checks the requesting user is a Tenant Admin."""

    def check_admin(self, request):
        if not request.user.is_authenticated or not request.user.is_tenant_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only Admins can perform this action.")


class MembershipTypeListCreateView(generics.ListCreateAPIView):
    """Admin: list all Membership Types or create a new one."""

    serializer_class = MembershipTypeSerializer

    def get_queryset(self):
        return MembershipType.objects.all()

    def perform_create(self, serializer):
        if not self.request.user.is_tenant_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only Admins can create Membership Types.")
        serializer.save()

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        # GET (list) is also admin-only for the admin endpoint
        return [IsAuthenticated()]


class MembershipTypeDetailView(generics.RetrieveUpdateAPIView):
    """Admin: retrieve or update a Membership Type."""

    serializer_class = MembershipTypeSerializer

    def get_queryset(self):
        return MembershipType.objects.all()

    def perform_update(self, serializer):
        if not self.request.user.is_tenant_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only Admins can update Membership Types.")
        serializer.save()


class MembershipTypeDeactivateView(generics.GenericAPIView):
    """Admin: deactivate a Membership Type (sets is_active=False)."""

    serializer_class = MembershipTypeSerializer

    def get_queryset(self):
        return MembershipType.objects.all()

    def post(self, request, pk):
        if not request.user.is_tenant_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only Admins can deactivate Membership Types.")
        membership_type = self.get_object()
        membership_type.is_active = False
        membership_type.save(update_fields=["is_active"])
        return Response(MembershipTypeSerializer(membership_type).data)


class PublicMembershipTypeListView(generics.ListAPIView):
    """Public: list active Membership Types for the Join page."""

    serializer_class = PublicMembershipTypeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return MembershipType.objects.filter(is_active=True)


# ── Membership views ──────────────────────────────────────────────


class MembershipPurchaseView(generics.CreateAPIView):
    """Authenticated User purchases a Membership."""

    serializer_class = MembershipPurchaseSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(
            MembershipSerializer(membership).data, status=status.HTTP_201_CREATED
        )


class MyMembershipsView(generics.ListAPIView):
    """Authenticated User: list their own Memberships."""

    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Membership.objects.filter(owner=self.request.user).select_related(
            "membership_type"
        )


class MembershipCancelView(generics.GenericAPIView):
    """Authenticated User cancels one of their own Memberships."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            membership = Membership.objects.get(pk=pk, owner=request.user)
        except Membership.DoesNotExist:
            return Response(
                {"detail": "Membership not found."}, status=status.HTTP_404_NOT_FOUND
            )
        try:
            membership.transition_to("cancelled")
        except ValueError as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(MembershipSerializer(membership).data)


class AdminMembershipListView(generics.ListAPIView):
    """Admin: list all Memberships in the Tenant, with optional status filter."""

    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_tenant_admin:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only Admins can view all memberships.")
        qs = Membership.objects.all().select_related("membership_type", "owner")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class AdminMembershipTransitionView(generics.GenericAPIView):
    """Admin: transition a Membership's status (e.g. lapsed → active)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_tenant_admin:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only Admins can transition membership status.")
        try:
            membership = Membership.objects.get(pk=pk)
        except Membership.DoesNotExist:
            return Response(
                {"detail": "Membership not found."}, status=status.HTTP_404_NOT_FOUND
            )
        new_status = request.data.get("status")
        if not new_status:
            return Response(
                {"detail": "Status is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            membership.transition_to(new_status)
        except ValueError as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(MembershipSerializer(membership).data)
