"""Tests for #8 — Stripe Connect lifecycle (mocked Stripe API)."""
import json
from unittest.mock import MagicMock, patch

from django.db import connection
from django.test import TestCase
from django_tenants.utils import tenant_context
from rest_framework.test import APIClient

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser


class StripeConnectTest(TestCase):
    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(schema_name="test_stripe", name="Stripe Club", slug="stripe-club")
        self.tenant.save()
        TenantDomain.objects.create(domain="stripe-club.lvh.me", tenant=self.tenant, is_primary=True)

        self.client = APIClient()
        self.host = "stripe-club.lvh.me"

        with tenant_context(self.tenant):
            self.admin = CustomUser.objects.create_user(
                username="admin@stripe.com", email="admin@stripe.com",
                password="AdminPass123!", role="admin",
            )
            self.member = CustomUser.objects.create_user(
                username="member@stripe.com", email="member@stripe.com",
                password="MemberPass123!", role="member",
            )

    def _token(self, user_email, password):
        resp = self.client.post(
            "/api/auth/login/",
            {"username": user_email, "password": password},
            format="json", HTTP_HOST=self.host,
        )
        return resp.data["access"]

    # --- Initiate connect ---

    @patch("payments.stripe_connect.stripe.Account.create")
    @patch("payments.stripe_connect.stripe.AccountLink.create")
    def test_admin_can_initiate_connect(self, mock_link, mock_account):
        mock_account.return_value = MagicMock(id="acct_test123")
        mock_link.return_value = MagicMock(url="https://connect.stripe.com/onboard/acct_test123")

        token = self._token("admin@stripe.com", "AdminPass123!")
        resp = self.client.post("/api/payments/stripe/connect/", HTTP_HOST=self.host,
                                HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("url", resp.data)
        self.assertIn("stripe.com", resp.data["url"])

    def test_member_cannot_initiate_connect(self):
        token = self._token("member@stripe.com", "MemberPass123!")
        resp = self.client.post("/api/payments/stripe/connect/", HTTP_HOST=self.host,
                                HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(resp.status_code, 403)

    # --- Status ---

    def test_status_not_connected(self):
        token = self._token("admin@stripe.com", "AdminPass123!")
        resp = self.client.get("/api/payments/stripe/connect/status/", HTTP_HOST=self.host,
                               HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["connected"])

    @patch("payments.views.stripe_connect.retrieve_account")
    def test_status_connected(self, mock_retrieve):
        mock_retrieve.return_value = MagicMock(charges_enabled=True, details_submitted=True)

        connection.set_schema_to_public()
        from tenancy.models import Tenant as TM
        TM.objects.filter(pk=self.tenant.pk).update(stripe_account_id="acct_test123")
        self.tenant.stripe_account_id = "acct_test123"

        token = self._token("admin@stripe.com", "AdminPass123!")
        resp = self.client.get("/api/payments/stripe/connect/status/", HTTP_HOST=self.host,
                               HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["connected"])
        self.assertEqual(resp.data["stripe_account_id"], "acct_test123")

    # --- Disconnect ---

    @patch("payments.stripe_connect.stripe.Account.delete")
    def test_admin_can_disconnect(self, mock_delete):
        mock_delete.return_value = MagicMock()

        connection.set_schema_to_public()
        from tenancy.models import Tenant as TM
        TM.objects.filter(pk=self.tenant.pk).update(stripe_account_id="acct_test123")
        self.tenant.stripe_account_id = "acct_test123"

        token = self._token("admin@stripe.com", "AdminPass123!")
        resp = self.client.post("/api/payments/stripe/connect/disconnect/", HTTP_HOST=self.host,
                                HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(resp.status_code, 200)
        mock_delete.assert_called_once_with("acct_test123")

    def test_disconnect_when_not_connected_returns_400(self):
        token = self._token("admin@stripe.com", "AdminPass123!")
        resp = self.client.post("/api/payments/stripe/connect/disconnect/", HTTP_HOST=self.host,
                                HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(resp.status_code, 400)

    # --- Payment guard ---

    def test_checkout_blocked_without_stripe_account(self):
        token = self._token("admin@stripe.com", "AdminPass123!")
        resp = self.client.post(
            "/api/payments/checkout/",
            {"membership_type_id": 1},
            format="json", HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(resp.status_code, 402)
