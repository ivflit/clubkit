"""Tests for #9 — Membership payments via Stripe Checkout (mocked)."""
import json
from unittest.mock import MagicMock, patch

from django.db import connection
from django.test import TestCase
from django_tenants.utils import tenant_context
from rest_framework.test import APIClient

from memberships.models import Membership, MembershipType
from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser


class MembershipCheckoutTest(TestCase):
    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(schema_name="test_payments", name="Payment Club", slug="payment-club")
        self.tenant.save()
        TenantDomain.objects.create(domain="payment-club.lvh.me", tenant=self.tenant, is_primary=True)

        connection.set_schema_to_public()
        from tenancy.models import Tenant as TM
        TM.objects.filter(pk=self.tenant.pk).update(stripe_account_id="acct_testpay")
        self.tenant.stripe_account_id = "acct_testpay"

        self.client = APIClient()
        self.host = "payment-club.lvh.me"

        with tenant_context(self.tenant):
            self.user = CustomUser.objects.create_user(
                username="user@pay.com", email="user@pay.com",
                password="UserPass123!", role="member",
            )
            self.mt_oneoff = MembershipType.objects.create(
                name="One-Off Annual", price="100.00",
                billing_frequency="annual", renewal_mode="one_off",
            )
            self.mt_rolling = MembershipType.objects.create(
                name="Rolling Monthly", price="20.00",
                billing_frequency="monthly", renewal_mode="rolling",
            )

    def _token(self):
        resp = self.client.post(
            "/api/auth/login/",
            {"username": "user@pay.com", "password": "UserPass123!"},
            format="json", HTTP_HOST=self.host,
        )
        return resp.data["access"]

    @patch("payments.views.stripe.Product.create")
    @patch("payments.views.stripe.Price.create")
    @patch("payments.views.stripe.checkout.Session.create")
    def test_checkout_oneoff_creates_payment_session(self, mock_session, mock_price, mock_product):
        mock_product.return_value = MagicMock(id="prod_test")
        mock_price.return_value = MagicMock(id="price_test")
        mock_session.return_value = MagicMock(url="https://checkout.stripe.com/pay/cs_test", id="cs_test")

        token = self._token()
        resp = self.client.post(
            "/api/payments/checkout/",
            {"membership_type_id": self.mt_oneoff.id},
            format="json", HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("checkout_url", resp.data)

        # Should have created session in payment mode (one-off)
        call_kwargs = mock_session.call_args[1]
        self.assertEqual(call_kwargs["mode"], "payment")
        self.assertEqual(call_kwargs["stripe_account"], "acct_testpay")

    @patch("payments.views.stripe.Product.create")
    @patch("payments.views.stripe.Price.create")
    @patch("payments.views.stripe.checkout.Session.create")
    def test_checkout_rolling_creates_subscription_session(self, mock_session, mock_price, mock_product):
        mock_product.return_value = MagicMock(id="prod_test2")
        mock_price.return_value = MagicMock(id="price_test2")
        mock_session.return_value = MagicMock(url="https://checkout.stripe.com/pay/cs_sub", id="cs_sub")

        token = self._token()
        resp = self.client.post(
            "/api/payments/checkout/",
            {"membership_type_id": self.mt_rolling.id},
            format="json", HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(resp.status_code, 200)
        call_kwargs = mock_session.call_args[1]
        self.assertEqual(call_kwargs["mode"], "subscription")

    def test_checkout_invalid_membership_type_returns_404(self):
        token = self._token()
        resp = self.client.post(
            "/api/payments/checkout/",
            {"membership_type_id": 99999},
            format="json", HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(resp.status_code, 404)


class StripeWebhookTest(TestCase):
    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(schema_name="test_webhook", name="Webhook Club", slug="webhook-club")
        self.tenant.save()
        TenantDomain.objects.create(domain="webhook-club.lvh.me", tenant=self.tenant, is_primary=True)

        self.client = APIClient()
        self.host = "webhook-club.lvh.me"

        with tenant_context(self.tenant):
            self.user = CustomUser.objects.create_user(
                username="wh@test.com", email="wh@test.com",
                password="WebhookPass123!", role="member",
            )
            self.mt = MembershipType.objects.create(
                name="Annual", price="100.00",
                billing_frequency="annual", renewal_mode="one_off",
            )

    def _webhook_payload(self, event_type, metadata):
        return json.dumps({
            "type": event_type,
            "data": {
                "object": {
                    "metadata": metadata,
                }
            }
        })

    def test_webhook_checkout_completed_activates_membership(self):
        payload = self._webhook_payload("checkout.session.completed", {
            "tenant_schema": "test_webhook",
            "user_id": str(self.user.id),
            "membership_type_id": str(self.mt.id),
        })
        resp = self.client.post(
            "/api/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(resp.status_code, 200)

        with tenant_context(self.tenant):
            self.assertTrue(
                Membership.objects.filter(owner=self.user, membership_type=self.mt, status="active").exists()
            )

    def test_webhook_returns_200_for_unknown_events(self):
        payload = self._webhook_payload("some.unknown.event", {})
        resp = self.client.post(
            "/api/payments/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(resp.status_code, 200)
