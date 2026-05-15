from django.urls import path

from payments.views import (
    CustomerPortalView,
    MembershipCheckoutView,
    PlatformPlanUpgradeView,
    PlatformWebhookView,
    StripeConnectDisconnectView,
    StripeConnectInitiateView,
    StripeConnectStatusView,
    StripeWebhookView,
)

urlpatterns = [
    # #8 — Stripe Connect
    path("stripe/connect/", StripeConnectInitiateView.as_view(), name="stripe-connect-initiate"),
    path("stripe/connect/status/", StripeConnectStatusView.as_view(), name="stripe-connect-status"),
    path("stripe/connect/disconnect/", StripeConnectDisconnectView.as_view(), name="stripe-connect-disconnect"),
    # #9 — Membership payments
    path("checkout/", MembershipCheckoutView.as_view(), name="membership-checkout"),
    path("webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("portal/", CustomerPortalView.as_view(), name="customer-portal"),
    # #17 — Platform billing
    path("platform/upgrade/", PlatformPlanUpgradeView.as_view(), name="platform-plan-upgrade"),
    path("platform/webhook/", PlatformWebhookView.as_view(), name="platform-webhook"),
]
