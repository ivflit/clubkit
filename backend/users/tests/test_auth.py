from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

from django_tenants.utils import tenant_context

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser


class AuthEndpointsTest(TestCase):
    """Test registration, login, me, and role update endpoints."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(schema_name="auth_club", name="Auth Club", slug="auth-club")
        self.tenant.save()
        TenantDomain.objects.create(
            domain="auth-club.lvh.me", tenant=self.tenant, is_primary=True
        )

        self.client = APIClient()
        self.host = "auth-club.lvh.me"

    def test_register_creates_user_in_tenant_schema(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "newuser@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "newuser@test.com")
        self.assertEqual(response.data["role"], "member")

        with tenant_context(self.tenant):
            self.assertTrue(CustomUser.objects.filter(email="newuser@test.com").exists())

    def test_register_duplicate_email_rejected(self):
        with tenant_context(self.tenant):
            CustomUser.objects.create_user(
                username="existing@test.com", email="existing@test.com", password="pass123!"
            )

        response = self.client.post(
            "/api/auth/register/",
            {"email": "existing@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 400)

    def test_login_returns_jwt_tokens(self):
        with tenant_context(self.tenant):
            CustomUser.objects.create_user(
                username="login@test.com", email="login@test.com", password="StrongPass123!"
            )

        response = self.client.post(
            "/api/auth/login/",
            {"username": "login@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password_rejected(self):
        with tenant_context(self.tenant):
            CustomUser.objects.create_user(
                username="user@test.com", email="user@test.com", password="StrongPass123!"
            )

        response = self.client.post(
            "/api/auth/login/",
            {"username": "user@test.com", "password": "WrongPassword!"},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 401)

    def test_me_returns_authenticated_user(self):
        with tenant_context(self.tenant):
            CustomUser.objects.create_user(
                username="me@test.com", email="me@test.com", password="StrongPass123!",
                first_name="Test", last_name="User",
            )

        # Login first
        login_res = self.client.post(
            "/api/auth/login/",
            {"username": "me@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST=self.host,
        )
        token = login_res.data["access"]

        # Call /me/
        response = self.client.get(
            "/api/auth/me/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "me@test.com")
        self.assertEqual(response.data["first_name"], "Test")

    def test_me_unauthenticated_returns_401(self):
        response = self.client.get(
            "/api/auth/me/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 401)

    def test_admin_can_change_user_role(self):
        with tenant_context(self.tenant):
            admin = CustomUser.objects.create_user(
                username="admin@test.com", email="admin@test.com",
                password="StrongPass123!", role="admin",
            )
            member = CustomUser.objects.create_user(
                username="member@test.com", email="member@test.com",
                password="StrongPass123!", role="member",
            )
            member_id = member.pk

        # Login as admin
        login_res = self.client.post(
            "/api/auth/login/",
            {"username": "admin@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST=self.host,
        )
        token = login_res.data["access"]

        # Promote member to admin
        response = self.client.patch(
            f"/api/auth/role/{member_id}/",
            {"role": "admin"},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "admin")

    def test_non_admin_cannot_change_roles(self):
        with tenant_context(self.tenant):
            member = CustomUser.objects.create_user(
                username="member@test.com", email="member@test.com",
                password="StrongPass123!", role="member",
            )
            other = CustomUser.objects.create_user(
                username="other@test.com", email="other@test.com",
                password="StrongPass123!", role="member",
            )
            other_id = other.pk

        # Login as non-admin
        login_res = self.client.post(
            "/api/auth/login/",
            {"username": "member@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST=self.host,
        )
        token = login_res.data["access"]

        response = self.client.patch(
            f"/api/auth/role/{other_id}/",
            {"role": "admin"},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)


class CrossTenantAuthIsolationTest(TestCase):
    """Verify Users in one Tenant cannot authenticate against another."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant_a = Tenant(schema_name="iso_a", name="Club A", slug="iso-a")
        self.tenant_a.save()
        TenantDomain.objects.create(
            domain="iso-a.lvh.me", tenant=self.tenant_a, is_primary=True
        )

        self.tenant_b = Tenant(schema_name="iso_b", name="Club B", slug="iso-b")
        self.tenant_b.save()
        TenantDomain.objects.create(
            domain="iso-b.lvh.me", tenant=self.tenant_b, is_primary=True
        )

        # Create user in tenant A only
        with tenant_context(self.tenant_a):
            CustomUser.objects.create_user(
                username="user@test.com", email="user@test.com",
                password="StrongPass123!",
            )

        self.client = APIClient()

    def test_user_in_tenant_a_cannot_login_to_tenant_b(self):
        """User registered in Club A cannot authenticate against Club B."""
        response = self.client.post(
            "/api/auth/login/",
            {"username": "user@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST="iso-b.lvh.me",
        )
        self.assertEqual(response.status_code, 401)

    def test_user_in_tenant_a_can_login_to_tenant_a(self):
        """User registered in Club A can authenticate against Club A."""
        response = self.client.post(
            "/api/auth/login/",
            {"username": "user@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST="iso-a.lvh.me",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_jwt_from_tenant_a_rejected_in_tenant_b(self):
        """JWT token obtained from Tenant A cannot access Tenant B endpoints."""
        # Get token from tenant A
        login_res = self.client.post(
            "/api/auth/login/",
            {"username": "user@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST="iso-a.lvh.me",
        )
        token = login_res.data["access"]

        # Try to access /me/ on tenant B
        response = self.client.get(
            "/api/auth/me/",
            HTTP_HOST="iso-b.lvh.me",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        # Should fail because the user doesn't exist in tenant B's schema
        self.assertIn(response.status_code, [401, 404])


class OnboardingAdminCreationTest(TestCase):
    """Verify that onboarding creates the first Admin user."""

    def setUp(self):
        connection.set_schema_to_public()
        if not Tenant.objects.filter(schema_name="public").exists():
            public = Tenant(schema_name="public", name="Platform", slug="platform")
            public.save()
            TenantDomain.objects.create(domain="lvh.me", tenant=public, is_primary=True)
        self.client = APIClient()

    def test_onboarding_creates_admin_user(self):
        response = self.client.post(
            "/api/onboarding/",
            {
                "club_name": "Admin Test Club",
                "subdomain": "admin-test",
                "admin_email": "founder@test.com",
                "admin_password": "StrongPass123!",
                "admin_first_name": "Jane",
                "admin_last_name": "Doe",
            },
            format="json",
            HTTP_HOST="lvh.me",
        )
        self.assertEqual(response.status_code, 201)

        # Verify admin user exists in the new tenant's schema
        tenant = Tenant.objects.get(slug="admin-test")
        with tenant_context(tenant):
            user = CustomUser.objects.get(email="founder@test.com")
            self.assertEqual(user.role, "admin")
            self.assertTrue(user.is_tenant_admin)
            self.assertEqual(user.first_name, "Jane")

    def test_onboarding_admin_can_login(self):
        self.client.post(
            "/api/onboarding/",
            {
                "club_name": "Login Test Club",
                "subdomain": "login-test",
                "admin_email": "admin@test.com",
                "admin_password": "StrongPass123!",
            },
            format="json",
            HTTP_HOST="lvh.me",
        )

        # Login as the admin
        login_res = self.client.post(
            "/api/auth/login/",
            {"username": "admin@test.com", "password": "StrongPass123!"},
            format="json",
            HTTP_HOST="login-test.lvh.me",
        )
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("access", login_res.data)


class PasswordResetTest(TestCase):
    """Test password reset flow."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(schema_name="reset_club", name="Reset Club", slug="reset-club")
        self.tenant.save()
        TenantDomain.objects.create(
            domain="reset-club.lvh.me", tenant=self.tenant, is_primary=True
        )

        with tenant_context(self.tenant):
            CustomUser.objects.create_user(
                username="reset@test.com", email="reset@test.com",
                password="OldPassword123!",
            )

        self.client = APIClient()
        self.host = "reset-club.lvh.me"

    def test_password_reset_request(self):
        response = self.client.post(
            "/api/auth/password-reset/",
            {"email": "reset@test.com"},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("uid", response.data)
        self.assertIn("token", response.data)

    def test_password_reset_confirm(self):
        # Request reset
        reset_res = self.client.post(
            "/api/auth/password-reset/",
            {"email": "reset@test.com"},
            format="json",
            HTTP_HOST=self.host,
        )
        uid = reset_res.data["uid"]
        token = reset_res.data["token"]

        # Confirm reset
        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "NewPassword456!"},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)

        # Login with new password
        login_res = self.client.post(
            "/api/auth/login/",
            {"username": "reset@test.com", "password": "NewPassword456!"},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(login_res.status_code, 200)

    def test_password_reset_nonexistent_email_doesnt_reveal(self):
        response = self.client.post(
            "/api/auth/password-reset/",
            {"email": "nonexistent@test.com"},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        # Should not reveal whether the email exists
        self.assertNotIn("uid", response.data)
