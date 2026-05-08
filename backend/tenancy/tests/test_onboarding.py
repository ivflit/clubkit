from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

from tenancy.models import BrandKit, Tenant, TenantDomain


class OnboardingAPITest(TestCase):
    """Test the Onboarding endpoint (Tenant + BrandKit creation)."""

    def setUp(self):
        connection.set_schema_to_public()
        # Ensure the public tenant exists so middleware resolves lvh.me
        if not Tenant.objects.filter(schema_name="public").exists():
            public = Tenant(schema_name="public", name="Platform", slug="platform")
            public.save()
            TenantDomain.objects.create(domain="lvh.me", tenant=public, is_primary=True)
        self.client = APIClient()

    def _onboard(self, data):
        return self.client.post(
            "/api/onboarding/", data, format="json", HTTP_HOST="lvh.me"
        )

    def test_successful_onboarding(self):
        resp = self._onboard({
            "club_name": "Riverside FC",
            "subdomain": "riverside-fc",
            "primary_colour": "#ff0000",
            "accent_colour": "#00ff00",
            "description": "A great club",
            "contact_email": "info@riverside.com",
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["name"], "Riverside FC")
        self.assertEqual(data["slug"], "riverside-fc")
        self.assertIn("brand_kit", data)
        self.assertEqual(data["brand_kit"]["primary_colour"], "#ff0000")
        self.assertEqual(data["brand_kit"]["contact_email"], "info@riverside.com")

    def test_tenant_and_domain_created(self):
        self._onboard({"club_name": "Parkside", "subdomain": "parkside"})
        tenant = Tenant.objects.get(slug="parkside")
        self.assertEqual(tenant.name, "Parkside")
        self.assertEqual(tenant.schema_name, "parkside")
        domain = TenantDomain.objects.get(tenant=tenant)
        self.assertEqual(domain.domain, "parkside.lvh.me")
        self.assertTrue(domain.is_primary)

    def test_brand_kit_created(self):
        self._onboard({
            "club_name": "Hillside",
            "subdomain": "hillside",
            "description": "Hillside sports club",
        })
        tenant = Tenant.objects.get(slug="hillside")
        brand_kit = BrandKit.objects.get(tenant=tenant)
        self.assertEqual(brand_kit.description, "Hillside sports club")
        self.assertEqual(brand_kit.primary_colour, "#1a73e8")  # default

    def test_schema_provisioned_on_onboarding(self):
        self._onboard({"club_name": "Schema Test", "subdomain": "schema-test"})
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = %s)",
                ["schema_test"],
            )
            self.assertTrue(cursor.fetchone()[0])

    def test_duplicate_subdomain_rejected(self):
        self._onboard({"club_name": "First", "subdomain": "unique-slug"})
        resp = self._onboard({"club_name": "Second", "subdomain": "unique-slug"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("subdomain", resp.json())


class SubdomainSlugValidationTest(TestCase):
    """Test slug validation rules."""

    def setUp(self):
        connection.set_schema_to_public()
        if not Tenant.objects.filter(schema_name="public").exists():
            public = Tenant(schema_name="public", name="Platform", slug="platform")
            public.save()
            TenantDomain.objects.create(domain="lvh.me", tenant=public, is_primary=True)
        self.client = APIClient()

    def _onboard(self, data):
        return self.client.post(
            "/api/onboarding/", data, format="json", HTTP_HOST="lvh.me"
        )

    def test_reserved_subdomain_rejected(self):
        resp = self._onboard({"club_name": "Admin Club", "subdomain": "admin"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("subdomain", resp.json())

    def test_hyphen_start_rejected(self):
        resp = self._onboard({"club_name": "Bad Slug", "subdomain": "-bad"})
        self.assertEqual(resp.status_code, 400)

    def test_uppercase_normalised_to_lowercase(self):
        resp = self._onboard({"club_name": "Upper FC", "subdomain": "Upper-FC"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["slug"], "upper-fc")

    def test_missing_club_name_rejected(self):
        resp = self._onboard({"subdomain": "no-name"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("club_name", resp.json())

    def test_missing_subdomain_rejected(self):
        resp = self._onboard({"club_name": "No Subdomain"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("subdomain", resp.json())


class BrandKitEditAPITest(TestCase):
    """Test Brand Kit retrieval and update endpoints."""

    def setUp(self):
        connection.set_schema_to_public()
        if not Tenant.objects.filter(schema_name="public").exists():
            public = Tenant(schema_name="public", name="Platform", slug="platform")
            public.save()
            TenantDomain.objects.create(domain="lvh.me", tenant=public, is_primary=True)
        self.client = APIClient()
        # Create a tenant via onboarding
        self.client.post(
            "/api/onboarding/",
            {"club_name": "Edit Test FC", "subdomain": "edit-test"},
            format="json",
            HTTP_HOST="lvh.me",
        )
        self.tenant = Tenant.objects.get(slug="edit-test")

    def test_brand_kit_retrievable(self):
        resp = self.client.get(
            "/api/brand-kit/",
            HTTP_HOST="edit-test.lvh.me",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["primary_colour"], "#1a73e8")
