from decimal import Decimal

from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

from django_tenants.utils import tenant_context

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser

from memberships.models import MembershipType


class MembershipTypeCRUDTest(TestCase):
    """Tests for Membership Type CRUD operations and permission enforcement."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(schema_name="test_memberships", name="Test Club", slug="test-memberships")
        self.tenant.save()
        TenantDomain.objects.create(
            domain="test-memberships.lvh.me",
            tenant=self.tenant,
            is_primary=True,
        )

        self.client = APIClient()
        self.host = "test-memberships.lvh.me"

        with tenant_context(self.tenant):
            self.admin = CustomUser.objects.create_user(
                username="admin@test.com",
                email="admin@test.com",
                password="AdminPass123!",
                role="admin",
            )
            self.member = CustomUser.objects.create_user(
                username="member@test.com",
                email="member@test.com",
                password="MemberPass123!",
                role="member",
            )

    def _get_admin_token(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "admin@test.com", "password": "AdminPass123!"},
            format="json",
            HTTP_HOST=self.host,
        )
        return response.data["access"]

    def _get_member_token(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "member@test.com", "password": "MemberPass123!"},
            format="json",
            HTTP_HOST=self.host,
        )
        return response.data["access"]

    def _create_membership_type(self, token, **overrides):
        data = {
            "name": "Adult Annual",
            "description": "Full adult membership for the year",
            "price": "120.00",
            "billing_frequency": "annual",
            "renewal_mode": "rolling",
        }
        data.update(overrides)
        return self.client.post(
            "/api/membership-types/",
            data,
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

    # --- Create ---

    def test_admin_can_create_membership_type(self):
        token = self._get_admin_token()
        response = self._create_membership_type(token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Adult Annual")
        self.assertEqual(response.data["price"], "120.00")
        self.assertEqual(response.data["billing_frequency"], "annual")
        self.assertEqual(response.data["renewal_mode"], "rolling")
        self.assertTrue(response.data["is_active"])

    def test_member_cannot_create_membership_type(self):
        token = self._get_member_token()
        response = self._create_membership_type(token)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_create_membership_type(self):
        response = self.client.post(
            "/api/membership-types/",
            {"name": "Test", "price": "10.00", "billing_frequency": "monthly", "renewal_mode": "rolling"},
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 401)

    # --- List ---

    def test_admin_can_list_membership_types(self):
        token = self._get_admin_token()
        self._create_membership_type(token, name="Adult Annual")
        self._create_membership_type(token, name="Junior Monthly", price="25.00", billing_frequency="monthly")

        response = self.client.get(
            "/api/membership-types/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    # --- Retrieve ---

    def test_admin_can_retrieve_membership_type(self):
        token = self._get_admin_token()
        create_response = self._create_membership_type(token)
        pk = create_response.data["id"]

        response = self.client.get(
            f"/api/membership-types/{pk}/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Adult Annual")

    # --- Update ---

    def test_admin_can_update_membership_type(self):
        token = self._get_admin_token()
        create_response = self._create_membership_type(token)
        pk = create_response.data["id"]

        response = self.client.patch(
            f"/api/membership-types/{pk}/",
            {"name": "Adult Annual (Updated)", "price": "150.00"},
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Adult Annual (Updated)")
        self.assertEqual(response.data["price"], "150.00")

    def test_member_cannot_update_membership_type(self):
        admin_token = self._get_admin_token()
        create_response = self._create_membership_type(admin_token)
        pk = create_response.data["id"]

        member_token = self._get_member_token()
        response = self.client.patch(
            f"/api/membership-types/{pk}/",
            {"name": "Hacked"},
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    # --- Deactivate ---

    def test_admin_can_deactivate_membership_type(self):
        token = self._get_admin_token()
        create_response = self._create_membership_type(token)
        pk = create_response.data["id"]

        response = self.client.post(
            f"/api/membership-types/{pk}/deactivate/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_active"])

    def test_member_cannot_deactivate_membership_type(self):
        admin_token = self._get_admin_token()
        create_response = self._create_membership_type(admin_token)
        pk = create_response.data["id"]

        member_token = self._get_member_token()
        response = self.client.post(
            f"/api/membership-types/{pk}/deactivate/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_deactivated_type_hidden_from_public_list(self):
        admin_token = self._get_admin_token()
        self._create_membership_type(admin_token, name="Active Type")
        create_response = self._create_membership_type(admin_token, name="Inactive Type")
        pk = create_response.data["id"]

        # Deactivate one
        self.client.post(
            f"/api/membership-types/{pk}/deactivate/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )

        # Public endpoint should only show active
        response = self.client.get(
            "/api/membership-types/public/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Active Type")

    # --- Public list ---

    def test_public_list_shows_active_types(self):
        admin_token = self._get_admin_token()
        self._create_membership_type(admin_token, name="Adult Annual")
        self._create_membership_type(admin_token, name="Junior Monthly", price="25.00", billing_frequency="monthly")

        response = self.client.get(
            "/api/membership-types/public/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        # Public serializer should not expose is_active field
        self.assertNotIn("is_active", response.data[0])

    def test_public_list_no_auth_required(self):
        response = self.client.get(
            "/api/membership-types/public/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
