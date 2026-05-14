from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from tenancy.models import BrandKit, PlatformAdmin, Tenant
from tenancy.platform_admin_auth import IsPlatformAdmin, PlatformAdminAuthentication
from tenancy.serializers import (
    BrandKitSerializer,
    OnboardingSerializer,
    PlatformAdminCreateSerializer,
    PlatformAdminLoginSerializer,
    TenantDetailSerializer,
    TenantListSerializer,
)


class OnboardingView(generics.CreateAPIView):
    """Self-service Tenant creation. No auth required."""

    serializer_class = OnboardingSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant = serializer.save()
        response_serializer = TenantDetailSerializer(tenant)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class BrandKitDetailView(generics.RetrieveAPIView):
    """Retrieve the Brand Kit for the current Tenant (public, no auth)."""

    serializer_class = BrandKitSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        tenant = self.request.tenant
        brand_kit, _ = BrandKit.objects.get_or_create(tenant=tenant)
        return brand_kit


class BrandKitUpdateView(generics.UpdateAPIView):
    """Update the Brand Kit for the current Tenant. Admin only."""

    serializer_class = BrandKitSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        tenant = self.request.tenant
        brand_kit, _ = BrandKit.objects.get_or_create(tenant=tenant)
        return brand_kit

    def check_permissions(self, request):
        super().check_permissions(request)
        if not request.user.is_tenant_admin:
            self.permission_denied(request, message="Only Admins can update the Brand Kit.")


# ---------------------------------------------------------------------------
# Platform Admin views (public schema)
# ---------------------------------------------------------------------------

def _get_tenant_schema_stats(tenant):
    """Return member count and active membership count for a Tenant via cross-schema query."""
    from memberships.models import Membership

    User = get_user_model()
    with schema_context(tenant.schema_name):
        member_count = User.objects.count()
        active_memberships = Membership.objects.filter(status="active").count()
    return member_count, active_memberships


class PlatformAdminLoginView(APIView):
    """Issue a JWT for a PlatformAdmin account. No Tenant context required."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PlatformAdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            admin = PlatformAdmin.objects.get(email__iexact=email, is_active=True)
        except PlatformAdmin.DoesNotExist:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not admin.check_password(password):
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = AccessToken()
        token["platform_admin_id"] = admin.id
        token["email"] = admin.email

        return Response({"access": str(token)})


class PlatformAdminCreateView(generics.CreateAPIView):
    """Bootstrap: create the first (or additional) Platform Admin accounts."""

    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]
    serializer_class = PlatformAdminCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        return Response({"id": admin.id, "email": admin.email}, status=status.HTTP_201_CREATED)


class PlatformAdminTenantListView(APIView):
    """List all Tenants with name, subdomain, status, plan, and creation date."""

    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        tenants = Tenant.objects.exclude(schema_name="public").order_by("-created_at")
        serializer = TenantListSerializer(tenants, many=True)
        return Response(serializer.data)


class PlatformAdminTenantDetailView(APIView):
    """Tenant detail: member count, active memberships, Stripe connection status."""

    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request, tenant_id):
        try:
            tenant = Tenant.objects.exclude(schema_name="public").get(pk=tenant_id)
        except Tenant.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        member_count, active_memberships = _get_tenant_schema_stats(tenant)
        base_data = TenantListSerializer(tenant).data
        return Response({
            **base_data,
            "member_count": member_count,
            "active_memberships": active_memberships,
            "stripe_connected": False,  # placeholder until Stripe Connect (#8) is done
        })


class PlatformAdminStatsView(APIView):
    """Aggregate stats: total Tenants, total Users, total active Memberships."""

    authentication_classes = [PlatformAdminAuthentication]
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        from memberships.models import Membership

        User = get_user_model()
        tenants = Tenant.objects.exclude(schema_name="public")
        total_tenants = tenants.count()
        total_users = 0
        total_active_memberships = 0

        for tenant in tenants:
            with schema_context(tenant.schema_name):
                total_users += User.objects.count()
                total_active_memberships += Membership.objects.filter(status="active").count()

        return Response(
            {
                "total_tenants": total_tenants,
                "total_users": total_users,
                "total_active_memberships": total_active_memberships,
            }
        )
