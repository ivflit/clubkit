from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

from django_tenants.utils import tenant_context

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser

from memberships.models import Membership, MembershipType


class MembershipLifecycleTest(TestCase):
    """Tests for Membership purchase, lifecycle transitions, and permission checks."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(
            schema_name="test_memberships_lc",
            name="Lifecycle Club",
            slug="test-memberships-lc",
        )
        self.tenant.save()
        TenantDomain.objects.create(
            domain="test-memberships-lc.lvh.me",
            tenant=self.tenant,
            is_primary=True,
        )

        self.client = APIClient()
        self.host = "test-memberships-lc.lvh.me"

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
            self.membership_type = MembershipType.objects.create(
                name="Adult Annual",
                description="Full membership",
                price="120.00",
                billing_frequency="annual",
                renewal_mode="rolling",
            )
            self.inactive_type = MembershipType.objects.create(
                name="Old Type",
                price="50.00",
                billing_frequency="monthly",
                renewal_mode="one_off",
                is_active=False,
            )

    def _get_token(self, email, password):
        response = self.client.post(
            "/api/auth/login/",
            {"username": email, "password": password},
            format="json",
            HTTP_HOST=self.host,
        )
        return response.data["access"]

    def _get_admin_token(self):
        return self._get_token("admin@test.com", "AdminPass123!")

    def _get_member_token(self):
        return self._get_token("member@test.com", "MemberPass123!")

    # --- Purchase ---

    def test_user_can_purchase_membership(self):
        token = self._get_member_token()
        response = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "active")
        self.assertEqual(response.data["membership_type"], self.membership_type.id)
        self.assertIsNotNone(response.data["start_date"])
        self.assertIsNotNone(response.data["end_date"])

    def test_cannot_purchase_inactive_type(self):
        token = self._get_member_token()
        response = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.inactive_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_cannot_purchase(self):
        response = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 401)

    # --- My Memberships ---

    def test_user_can_list_own_memberships(self):
        token = self._get_member_token()
        # Purchase a membership
        self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        response = self.client.get(
            "/api/membership-types/memberships/mine/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["membership_type_name"], "Adult Annual")

    def test_user_only_sees_own_memberships(self):
        # Admin purchases a membership
        admin_token = self._get_admin_token()
        self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )

        # Member should see zero
        member_token = self._get_member_token()
        response = self.client.get(
            "/api/membership-types/memberships/mine/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    # --- Cancel ---

    def test_user_can_cancel_active_membership(self):
        token = self._get_member_token()
        purchase = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        pk = purchase.data["id"]

        response = self.client.post(
            f"/api/membership-types/memberships/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "cancelled")

    def test_cannot_cancel_already_cancelled(self):
        token = self._get_member_token()
        purchase = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        pk = purchase.data["id"]

        # Cancel once
        self.client.post(
            f"/api/membership-types/memberships/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        # Try again
        response = self.client.post(
            f"/api/membership-types/memberships/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_cancel_another_users_membership(self):
        # Member purchases
        member_token = self._get_member_token()
        purchase = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        pk = purchase.data["id"]

        # Admin tries to cancel via the user cancel endpoint
        admin_token = self._get_admin_token()
        response = self.client.post(
            f"/api/membership-types/memberships/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(response.status_code, 404)

    # --- Lifecycle transitions ---

    def test_active_to_lapsed(self):
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
            )
            membership.transition_to("lapsed")
            self.assertEqual(membership.status, "lapsed")

    def test_active_to_cancelled(self):
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
            )
            membership.transition_to("cancelled")
            self.assertEqual(membership.status, "cancelled")

    def test_lapsed_to_active(self):
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
                status="lapsed",
            )
            membership.transition_to("active")
            self.assertEqual(membership.status, "active")

    def test_cancelled_cannot_transition(self):
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
                status="cancelled",
            )
            with self.assertRaises(ValueError):
                membership.transition_to("active")

    def test_invalid_transition_raises(self):
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
            )
            with self.assertRaises(ValueError):
                membership.transition_to("cancelled_invalid")

    # --- has_active_membership ---

    def test_user_with_active_membership(self):
        with tenant_context(self.tenant):
            Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
            )
            self.assertTrue(self.member.has_active_membership)

    def test_user_without_active_membership_is_guest(self):
        with tenant_context(self.tenant):
            self.assertFalse(self.member.has_active_membership)

    def test_user_with_only_cancelled_membership_is_guest(self):
        with tenant_context(self.tenant):
            Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
                status="cancelled",
            )
            self.assertFalse(self.member.has_active_membership)

    # --- Admin membership list ---

    def test_admin_can_list_all_memberships(self):
        token = self._get_admin_token()
        # Create a membership for member
        member_token = self._get_member_token()
        self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )

        response = self.client.get(
            "/api/membership-types/memberships/admin/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_admin_can_filter_by_status(self):
        token = self._get_admin_token()
        member_token = self._get_member_token()
        # Create and cancel a membership
        purchase = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        pk = purchase.data["id"]
        self.client.post(
            f"/api/membership-types/memberships/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )

        # Filter active — should be empty
        response = self.client.get(
            "/api/membership-types/memberships/admin/?status=active",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        # Filter cancelled — should have 1
        response = self.client.get(
            "/api/membership-types/memberships/admin/?status=cancelled",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_member_cannot_list_all_memberships(self):
        token = self._get_member_token()
        response = self.client.get(
            "/api/membership-types/memberships/admin/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

    # --- Admin transition ---

    def test_admin_can_transition_membership(self):
        member_token = self._get_member_token()
        purchase = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        pk = purchase.data["id"]

        admin_token = self._get_admin_token()
        response = self.client.post(
            f"/api/membership-types/memberships/{pk}/transition/",
            {"status": "lapsed"},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "lapsed")

    def test_member_cannot_transition_membership(self):
        member_token = self._get_member_token()
        purchase = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.membership_type.id},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        pk = purchase.data["id"]

        response = self.client.post(
            f"/api/membership-types/memberships/{pk}/transition/",
            {"status": "lapsed"},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 403)

    # --- End date calculation ---

    def test_monthly_membership_end_date(self):
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.member,
                membership_type=MembershipType.objects.create(
                    name="Monthly",
                    price="10.00",
                    billing_frequency="monthly",
                    renewal_mode="rolling",
                ),
            )
            days_diff = (membership.end_date - membership.start_date).days
            self.assertEqual(days_diff, 30)

    def test_annual_membership_end_date(self):
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
            )
            days_diff = (membership.end_date - membership.start_date).days
            self.assertEqual(days_diff, 365)
