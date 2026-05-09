from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

from tenancy.models import BrandKit, Tenant, TenantDomain


class TenantRoutingTest(TestCase):
    """Verify subdomain-based Tenant Routing resolves the correct tenant
    and returns the right Brand Kit data."""

    def setUp(self):
        connection.set_schema_to_public()
        if not Tenant.objects.filter(schema_name="public").exists():
            public = Tenant(schema_name="public", name="Platform", slug="platform")
            public.save()
            TenantDomain.objects.create(domain="lvh.me", tenant=public, is_primary=True)

        self.client = APIClient()

        # Create two tenants
        self.client.post(
            "/api/onboarding/",
            {
                "club_name": "Alpha FC",
                "subdomain": "alpha",
                "admin_email": "admin@alpha.com",
                "admin_password": "StrongPass123!",
                "primary_colour": "#111111",
                "description": "Alpha club",
            },
            format="json",
            HTTP_HOST="lvh.me",
        )
        self.client.post(
            "/api/onboarding/",
            {
                "club_name": "Beta United",
                "subdomain": "beta",
                "admin_email": "admin@beta.com",
                "admin_password": "StrongPass123!",
                "primary_colour": "#222222",
                "description": "Beta club",
            },
            format="json",
            HTTP_HOST="lvh.me",
        )

    def test_subdomain_resolves_correct_brand_kit(self):
        """Each subdomain returns its own Brand Kit, proving tenant isolation."""
        resp_alpha = self.client.get("/api/brand-kit/", HTTP_HOST="alpha.lvh.me")
        resp_beta = self.client.get("/api/brand-kit/", HTTP_HOST="beta.lvh.me")

        self.assertEqual(resp_alpha.status_code, 200)
        self.assertEqual(resp_beta.status_code, 200)
        self.assertEqual(resp_alpha.json()["primary_colour"], "#111111")
        self.assertEqual(resp_alpha.json()["description"], "Alpha club")
        self.assertEqual(resp_beta.json()["primary_colour"], "#222222")
        self.assertEqual(resp_beta.json()["description"], "Beta club")

    def test_unknown_subdomain_returns_404(self):
        """Requests to a non-existent subdomain get a 404."""
        resp = self.client.get("/api/brand-kit/", HTTP_HOST="nonexistent.lvh.me")
        self.assertEqual(resp.status_code, 404)

    def test_schema_search_path_switches_per_request(self):
        """Consecutive requests to different subdomains switch schema correctly."""
        # Request Alpha
        resp1 = self.client.get("/api/brand-kit/", HTTP_HOST="alpha.lvh.me")
        self.assertEqual(resp1.json()["description"], "Alpha club")

        # Immediately request Beta — schema must switch
        resp2 = self.client.get("/api/brand-kit/", HTTP_HOST="beta.lvh.me")
        self.assertEqual(resp2.json()["description"], "Beta club")

        # Back to Alpha — schema must switch back
        resp3 = self.client.get("/api/brand-kit/", HTTP_HOST="alpha.lvh.me")
        self.assertEqual(resp3.json()["description"], "Alpha club")

    def test_health_endpoint_on_tenant_subdomain(self):
        """The health endpoint works on tenant subdomains too."""
        resp = self.client.get("/api/health/", HTTP_HOST="alpha.lvh.me")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")
