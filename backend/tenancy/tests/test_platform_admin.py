"""
Tests for Platform Admin dashboard (issue #16).

Covers:
- PlatformAdmin model creation and password hashing
- Login endpoint: success, wrong password, inactive account
- All platform admin API endpoints reject non-platform-admin requests
- Tenant listing returns all non-public tenants
- Tenant detail returns cross-schema member/membership counts
- Platform-wide stats aggregate across all tenant schemas
"""

from django.db import connection
from rest_framework.test import APIClient
from django.test import TestCase
from django_tenants.utils import schema_context

from tenancy.models import BrandKit, PlatformAdmin, Tenant, TenantDomain


def _setup_public_tenant():
    connection.set_schema_to_public()
    if not Tenant.objects.filter(schema_name="public").exists():
        public = Tenant(schema_name="public", name="Platform", slug="platform")
        public.save()
        TenantDomain.objects.create(domain="lvh.me", tenant=public, is_primary=True)


def _create_tenant(client, club_name, subdomain):
    """Helper: onboard a tenant and return the Tenant instance."""
    client.post(
        "/api/onboarding/",
        {
            "club_name": club_name,
            "subdomain": subdomain,
            "admin_email": f"admin@{subdomain}.com",
            "admin_password": "StrongPass123!",
        },
        format="json",
        HTTP_HOST="lvh.me",
    )
    return Tenant.objects.get(slug=subdomain)


def _platform_admin_token(client, email, password):
    """Helper: log in as platform admin and return the access token."""
    resp = client.post(
        "/api/platform-admin/login/",
        {"email": email, "password": password},
        format="json",
        HTTP_HOST="lvh.me",
    )
    return resp.json().get("access")


class PlatformAdminModelTest(TestCase):
    def setUp(self):
        _setup_public_tenant()

    def test_password_hashed_on_set(self):
        admin = PlatformAdmin(email="super@platform.com")
        admin.set_password("MySecret123")
        self.assertNotEqual(admin.password, "MySecret123")
        self.assertTrue(admin.check_password("MySecret123"))

    def test_wrong_password_rejected(self):
        admin = PlatformAdmin(email="super@platform.com")
        admin.set_password("CorrectPass")
        self.assertFalse(admin.check_password("WrongPass"))

    def test_str_returns_email(self):
        admin = PlatformAdmin(email="super@platform.com")
        self.assertEqual(str(admin), "super@platform.com")


class PlatformAdminLoginTest(TestCase):
    def setUp(self):
        _setup_public_tenant()
        self.client = APIClient()
        self.admin = PlatformAdmin(email="sa@platform.com")
        self.admin.set_password("AdminPass123!")
        self.admin.save()

    def _login(self, email, password):
        return self.client.post(
            "/api/platform-admin/login/",
            {"email": email, "password": password},
            format="json",
            HTTP_HOST="lvh.me",
        )

    def test_login_success_returns_token(self):
        resp = self._login("sa@platform.com", "AdminPass123!")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.json())

    def test_login_wrong_password(self):
        resp = self._login("sa@platform.com", "WrongPass!")
        self.assertEqual(resp.status_code, 401)

    def test_login_nonexistent_email(self):
        resp = self._login("nobody@platform.com", "AdminPass123!")
        self.assertEqual(resp.status_code, 401)

    def test_login_inactive_admin(self):
        self.admin.is_active = False
        self.admin.save()
        resp = self._login("sa@platform.com", "AdminPass123!")
        self.assertEqual(resp.status_code, 401)

    def test_login_case_insensitive_email(self):
        resp = self._login("SA@PLATFORM.COM", "AdminPass123!")
        self.assertEqual(resp.status_code, 200)


class PlatformAdminPermissionTest(TestCase):
    """Verify platform admin endpoints reject requests without a valid token."""

    def setUp(self):
        _setup_public_tenant()
        self.client = APIClient()

    def test_tenant_list_requires_auth(self):
        resp = self.client.get("/api/platform-admin/tenants/", HTTP_HOST="lvh.me")
        self.assertEqual(resp.status_code, 403)

    def test_stats_requires_auth(self):
        resp = self.client.get("/api/platform-admin/stats/", HTTP_HOST="lvh.me")
        self.assertEqual(resp.status_code, 403)

    def test_tenant_detail_requires_auth(self):
        resp = self.client.get("/api/platform-admin/tenants/999/", HTTP_HOST="lvh.me")
        self.assertEqual(resp.status_code, 403)

    def test_regular_jwt_rejected(self):
        """A tenant user JWT should not grant platform admin access."""
        # Onboard a tenant and get a tenant JWT
        _create_tenant(self.client, "Test Club", "test-perm")
        login_resp = self.client.post(
            "/api/auth/login/",
            {"username": "admin@test-perm.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST="test-perm.lvh.me",
        )
        tenant_token = login_resp.json().get("access")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tenant_token}")
        resp = self.client.get("/api/platform-admin/tenants/", HTTP_HOST="lvh.me")
        self.assertEqual(resp.status_code, 403)


class PlatformAdminTenantListTest(TestCase):
    def setUp(self):
        _setup_public_tenant()
        self.client = APIClient()
        self.admin = PlatformAdmin(email="sa@platform.com")
        self.admin.set_password("AdminPass123!")
        self.admin.save()
        self.token = _platform_admin_token(self.client, "sa@platform.com", "AdminPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_empty_tenant_list(self):
        resp = self.client.get("/api/platform-admin/tenants/", HTTP_HOST="lvh.me")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_tenant_list_contains_onboarded_tenants(self):
        _create_tenant(self.client, "Riverside FC", "riverside-list")
        _create_tenant(self.client, "Lakeside SC", "lakeside-list")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        resp = self.client.get("/api/platform-admin/tenants/", HTTP_HOST="lvh.me")
        self.assertEqual(resp.status_code, 200)
        slugs = [t["slug"] for t in resp.json()]
        self.assertIn("riverside-list", slugs)
        self.assertIn("lakeside-list", slugs)

    def test_public_schema_excluded_from_list(self):
        resp = self.client.get("/api/platform-admin/tenants/", HTTP_HOST="lvh.me")
        slugs = [t["slug"] for t in resp.json()]
        self.assertNotIn("platform", slugs)

    def test_tenant_list_fields(self):
        _create_tenant(self.client, "Fields FC", "fields-test")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        resp = self.client.get("/api/platform-admin/tenants/", HTTP_HOST="lvh.me")
        tenant = next(t for t in resp.json() if t["slug"] == "fields-test")
        for field in ["id", "name", "slug", "status", "plan", "created_at"]:
            self.assertIn(field, tenant)
        self.assertEqual(tenant["plan"], "free")

    def test_tenant_list_default_plan_is_free(self):
        _create_tenant(self.client, "Free Tier Club", "free-tier")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        resp = self.client.get("/api/platform-admin/tenants/", HTTP_HOST="lvh.me")
        tenant = next(t for t in resp.json() if t["slug"] == "free-tier")
        self.assertEqual(tenant["plan"], "free")


class PlatformAdminTenantDetailTest(TestCase):
    def setUp(self):
        _setup_public_tenant()
        self.client = APIClient()
        self.admin = PlatformAdmin(email="sa@platform.com")
        self.admin.set_password("AdminPass123!")
        self.admin.save()
        self.token = _platform_admin_token(self.client, "sa@platform.com", "AdminPass123!")
        self.tenant = _create_tenant(self.client, "Detail FC", "detail-fc")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_tenant_detail_returns_correct_fields(self):
        resp = self.client.get(
            f"/api/platform-admin/tenants/{self.tenant.id}/",
            HTTP_HOST="lvh.me",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for field in ["id", "name", "slug", "status", "plan", "created_at",
                       "member_count", "active_memberships", "stripe_connected"]:
            self.assertIn(field, data)

    def test_tenant_detail_member_count(self):
        # The onboarding creates one admin user in the tenant schema
        resp = self.client.get(
            f"/api/platform-admin/tenants/{self.tenant.id}/",
            HTTP_HOST="lvh.me",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["member_count"], 1)

    def test_tenant_detail_active_memberships_zero(self):
        resp = self.client.get(
            f"/api/platform-admin/tenants/{self.tenant.id}/",
            HTTP_HOST="lvh.me",
        )
        self.assertEqual(resp.json()["active_memberships"], 0)

    def test_tenant_detail_stripe_connected_false(self):
        resp = self.client.get(
            f"/api/platform-admin/tenants/{self.tenant.id}/",
            HTTP_HOST="lvh.me",
        )
        self.assertFalse(resp.json()["stripe_connected"])

    def test_tenant_detail_404_for_unknown_id(self):
        resp = self.client.get(
            "/api/platform-admin/tenants/99999/",
            HTTP_HOST="lvh.me",
        )
        self.assertEqual(resp.status_code, 404)


class PlatformAdminStatsTest(TestCase):
    def setUp(self):
        _setup_public_tenant()
        self.client = APIClient()
        self.admin = PlatformAdmin(email="sa@platform.com")
        self.admin.set_password("AdminPass123!")
        self.admin.save()
        self.token = _platform_admin_token(self.client, "sa@platform.com", "AdminPass123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_stats_with_no_tenants(self):
        resp = self.client.get("/api/platform-admin/stats/", HTTP_HOST="lvh.me")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_tenants"], 0)
        self.assertEqual(data["total_users"], 0)
        self.assertEqual(data["total_active_memberships"], 0)

    def test_stats_with_tenants(self):
        _create_tenant(self.client, "Stats Club A", "stats-a")
        _create_tenant(self.client, "Stats Club B", "stats-b")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        resp = self.client.get("/api/platform-admin/stats/", HTTP_HOST="lvh.me")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_tenants"], 2)
        # Each onboarding creates 1 admin user in the tenant schema
        self.assertEqual(data["total_users"], 2)
        self.assertEqual(data["total_active_memberships"], 0)

    def test_stats_fields_present(self):
        resp = self.client.get("/api/platform-admin/stats/", HTTP_HOST="lvh.me")
        data = resp.json()
        for field in ["total_tenants", "total_users", "total_active_memberships"]:
            self.assertIn(field, data)
