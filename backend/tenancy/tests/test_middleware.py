from django.db import connection
from django.http import Http404
from django.test import TestCase, RequestFactory

from django_tenants.middleware.main import TenantMainMiddleware

from tenancy.models import Tenant, TenantDomain


class TenantMiddlewareTest(TestCase):
    """Verify middleware resolves the correct Tenant from the subdomain."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(
            schema_name="middleware_test", name="Middleware Club", slug="middleware-test"
        )
        self.tenant.save()
        TenantDomain.objects.create(
            domain="middleware-test.lvh.me", tenant=self.tenant, is_primary=True
        )
        self.factory = RequestFactory()

    def _dummy_view(self, request):
        from django.http import JsonResponse
        return JsonResponse({"tenant": request.tenant.slug})

    def test_request_resolves_correct_tenant(self):
        request = self.factory.get("/api/health/", HTTP_HOST="middleware-test.lvh.me")
        middleware = TenantMainMiddleware(self._dummy_view)
        middleware(request)
        self.assertEqual(request.tenant.slug, "middleware-test")

    def test_unknown_subdomain_raises_404(self):
        request = self.factory.get("/api/health/", HTTP_HOST="nonexistent.lvh.me")
        middleware = TenantMainMiddleware(self._dummy_view)
        with self.assertRaises(Http404):
            middleware(request)
