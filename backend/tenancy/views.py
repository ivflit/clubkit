from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from tenancy.models import BrandKit
from tenancy.serializers import (
    BrandKitSerializer,
    OnboardingSerializer,
    TenantDetailSerializer,
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
