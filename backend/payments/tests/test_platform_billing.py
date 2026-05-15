"""Tests for #17 — Platform billing: plan limits and plan upgrade flow."""
import json

from django.db import connection
from django.test import TestCase
from django_tenants.utils import tenant_context
from rest_framework.test import APIClient

from memberships.models import Membership, MembershipType
from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser


class PlanLimitsTest(TestCase):
    """Free plan limits: max 50 active members."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(schema_name="test_limits", name="Limits Club", slug="limits-club")
        self.tenant.save()
        TenantDomain.objects.create(domain="limits-club.lvh.me", tenant=self.tenant, is_primary=True)

        self.client = APIClient()
        self.host = "limits-club.lvh.me"

        with tenant_context(self.tenant):
            self.user = CustomUser.objects.create_user(
                username="buyer@limits.com", email="buyer@limits.com",
                password="BuyerPass123!", role="member",
            )
            self.mt = MembershipType.objects.create(
                name="Basic", price="10.00",
                billing_frequency="monthly", renewal_mode="one_off",
            )

    def _token(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "buyer@limits.com", "password": "BuyerPass123!"},
            format="json", HTTP_HOST=self.host,
        )
        return resp.data["access"]

    def test_free_plan_purchase_within_limit_succeeds(self):
        token = self._token()
        resp = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.mt.id},
            format="json", HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(resp.status_code, 201)

    def test_free_plan_purchase_at_limit_is_blocked(self):
        # Fill up to limit
        with tenant_context(self.tenant):
            other_users = []
            for i in range(50):
                u = CustomUser.objects.create_user(
                    username=f"filler{i}@test.com",
                    email=f"filler{i}@test.com",
                    password="Filler123!",
                )
                Membership.objects.create(owner=u, membership_type=self.mt, status="active")

        token = self._token()
        resp = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.mt.id},
            format="json", HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("limit", resp.data["detail"])

    def test_pro_plan_has_no_member_cap(self):
        connection.set_schema_to_public()
        from tenancy.models import Tenant as TM
        TM.objects.filter(pk=self.tenant.pk).update(plan="pro")
        self.tenant.plan = "pro"

        # Fill well over the free limit
        with tenant_context(self.tenant):
            for i in range(51):
                u = CustomUser.objects.create_user(
                    username=f"pro{i}@test.com", email=f"pro{i}@test.com", password="Pro123!",
                )
                Membership.objects.create(owner=u, membership_type=self.mt, status="active")

        token = self._token()
        resp = self.client.post(
            "/api/membership-types/memberships/purchase/",
            {"membership_type_id": self.mt.id},
            format="json", HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(resp.status_code, 201)


class PlatformWebhookTest(TestCase):
    """Platform webhook downgrades tenant on subscription cancellation."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(schema_name="test_planbilling", name="Pro Club", slug="pro-club")
        self.tenant.save()
        TenantDomain.objects.create(domain="pro-club.lvh.me", tenant=self.tenant, is_primary=True)

        connection.set_schema_to_public()
        from tenancy.models import Tenant as TM
        TM.objects.filter(pk=self.tenant.pk).update(plan="pro")

        self.client = APIClient()
        self.host = "pro-club.lvh.me"

    def test_subscription_cancelled_downgrades_to_free(self):
        payload = json.dumps({
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test",
                    "metadata": {"tenant_schema": "test_planbilling"},
                }
            }
        })
        resp = self.client.post(
            "/api/payments/platform/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(resp.status_code, 200)

        connection.set_schema_to_public()
        from tenancy.models import Tenant as TM
        tenant = TM.objects.get(pk=self.tenant.pk)
        self.assertEqual(tenant.plan, "free")
