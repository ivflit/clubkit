"""
Platform Admin authentication: a separate JWT-based auth flow
for PlatformAdmin accounts (public schema, not Tenant-scoped).
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


class PlatformAdminAuthentication(BaseAuthentication):
    """
    Authenticates requests that carry a Bearer token with a
    `platform_admin_id` claim — issued by PlatformAdminLoginView.
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None

        raw_token = auth_header[len("Bearer "):]
        try:
            token = AccessToken(raw_token)
        except TokenError:
            raise AuthenticationFailed("Token is invalid or expired.")

        if "platform_admin_id" not in token.payload:
            return None

        from tenancy.models import PlatformAdmin

        admin_id = token.payload["platform_admin_id"]
        try:
            admin = PlatformAdmin.objects.get(pk=admin_id, is_active=True)
        except PlatformAdmin.DoesNotExist:
            raise AuthenticationFailed("Platform admin account not found or inactive.")

        return (admin, token)

    def authenticate_header(self, request):
        return "Bearer"


class IsPlatformAdmin(BasePermission):
    """Allows access only to authenticated PlatformAdmin instances."""

    def has_permission(self, request, view):
        from tenancy.models import PlatformAdmin

        return (
            request.user is not None
            and isinstance(request.user, PlatformAdmin)
            and request.user.is_active
        )
