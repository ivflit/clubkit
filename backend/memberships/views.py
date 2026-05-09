from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import MembershipType
from .serializers import MembershipTypeSerializer, PublicMembershipTypeSerializer


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
