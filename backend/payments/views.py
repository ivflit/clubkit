import stripe
from django.conf import settings
from django.db import connection
from django_tenants.utils import schema_context
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from memberships.models import Membership, MembershipType
from payments import stripe_connect

stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------------------------------------------------------------------------
# #8 — Stripe Connect (Tenant Admin connects their Stripe account)
# ---------------------------------------------------------------------------


class StripeConnectInitiateView(APIView):
    """Admin initiates Stripe Express account onboarding."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_tenant_admin:
            return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)

        tenant = request.tenant

        # If the tenant doesn't have an account yet, create one
        if not tenant.stripe_account_id:
            try:
                account_id = stripe_connect.create_connect_account()
            except stripe.StripeError as e:
                return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

            # Save to public schema
            with schema_context("public"):
                from tenancy.models import Tenant as TenantModel
                TenantModel.objects.filter(pk=tenant.pk).update(stripe_account_id=account_id)
                tenant.stripe_account_id = account_id

        try:
            url = stripe_connect.create_account_link(
                account_id=tenant.stripe_account_id,
                return_url=settings.STRIPE_CONNECT_RETURN_URL,
                refresh_url=settings.STRIPE_CONNECT_REFRESH_URL,
            )
        except stripe.StripeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"url": url})


class StripeConnectStatusView(APIView):
    """Return Stripe connection status for the current Tenant."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_tenant_admin:
            return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)

        tenant = request.tenant

        if not tenant.stripe_account_id:
            return Response({"connected": False, "stripe_account_id": None})

        try:
            account = stripe_connect.retrieve_account(tenant.stripe_account_id)
            charges_enabled = account.charges_enabled
            details_submitted = account.details_submitted
        except stripe.StripeError:
            charges_enabled = False
            details_submitted = False

        return Response({
            "connected": charges_enabled,
            "details_submitted": details_submitted,
            "stripe_account_id": tenant.stripe_account_id,
        })


class StripeConnectDisconnectView(APIView):
    """Admin disconnects (removes) the Tenant's Stripe account."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_tenant_admin:
            return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)

        tenant = request.tenant

        if not tenant.stripe_account_id:
            return Response({"detail": "No Stripe account connected."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            stripe_connect.delete_account(tenant.stripe_account_id)
        except stripe.StripeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        with schema_context("public"):
            from tenancy.models import Tenant as TenantModel
            TenantModel.objects.filter(pk=tenant.pk).update(stripe_account_id="")
            tenant.stripe_account_id = ""

        return Response({"detail": "Stripe account disconnected."})


# ---------------------------------------------------------------------------
# #9 — Membership payments (Checkout + webhooks + Customer Portal)
# ---------------------------------------------------------------------------


def _get_or_create_stripe_price(membership_type, connected_account_id):
    """
    Ensure a Stripe Price exists for this MembershipType on the connected account.
    Stores the price ID on the MembershipType for reuse.
    """
    if membership_type.stripe_price_id:
        return membership_type.stripe_price_id

    # Create a Product then a Price on the connected account
    product = stripe.Product.create(
        name=membership_type.name,
        description=membership_type.description or membership_type.name,
        stripe_account=connected_account_id,
    )

    interval = "month" if membership_type.billing_frequency == "monthly" else "year"

    if membership_type.renewal_mode == "rolling":
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(membership_type.price * 100),  # pence/cents
            currency="gbp",
            recurring={"interval": interval},
            stripe_account=connected_account_id,
        )
    else:
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(membership_type.price * 100),
            currency="gbp",
            stripe_account=connected_account_id,
        )

    membership_type.stripe_price_id = price.id
    membership_type.save(update_fields=["stripe_price_id"])
    return price.id


class MembershipCheckoutView(APIView):
    """
    Create a Stripe Checkout session for a Membership purchase.
    Returns the checkout URL for the frontend to redirect to.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = request.tenant

        if not tenant.stripe_account_id:
            return Response(
                {"detail": "This club has not connected a payment account yet."},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        membership_type_id = request.data.get("membership_type_id")
        if not membership_type_id:
            return Response({"detail": "membership_type_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            membership_type = MembershipType.objects.get(pk=membership_type_id, is_active=True)
        except MembershipType.DoesNotExist:
            return Response({"detail": "Membership type not found or inactive."}, status=status.HTTP_404_NOT_FOUND)

        try:
            price_id = _get_or_create_stripe_price(membership_type, tenant.stripe_account_id)
        except stripe.StripeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        success_url = request.data.get("success_url", f"http://{request.get_host()}/join/success?session_id={{CHECKOUT_SESSION_ID}}")
        cancel_url = request.data.get("cancel_url", f"http://{request.get_host()}/join")

        mode = "subscription" if membership_type.renewal_mode == "rolling" else "payment"

        try:
            session = stripe.checkout.Session.create(
                mode=mode,
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=request.user.email,
                metadata={
                    "membership_type_id": str(membership_type.id),
                    "user_id": str(request.user.id),
                    "tenant_schema": request.tenant.schema_name,
                },
                stripe_account=tenant.stripe_account_id,
            )
        except stripe.StripeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"checkout_url": session.url, "session_id": session.id})


class StripeWebhookView(APIView):
    """
    Stripe webhook endpoint. Handles payment/subscription events for Tenant accounts.
    Use AllowAny — auth is via webhook signature verification.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        import json as json_module
        if webhook_secret:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
                event_dict = json_module.loads(payload)
            except (ValueError, stripe.SignatureVerificationError):
                return Response({"detail": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Dev mode: skip signature verification
            event_dict = json_module.loads(payload)

        self._handle_event(event_dict)
        return Response({"received": True})

    def _handle_event(self, event):
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type in ("checkout.session.completed", "payment_intent.succeeded"):
            self._activate_membership(data)
        elif event_type == "invoice.payment_failed":
            self._lapse_membership(data)
        elif event_type == "customer.subscription.deleted":
            self._cancel_membership(data)

    def _activate_membership(self, session):
        metadata = session.get("metadata", {})
        self._transition_or_create_membership(metadata, "active")

    def _lapse_membership(self, invoice):
        subscription_id = invoice.get("subscription")
        if not subscription_id:
            return
        self._transition_by_subscription(subscription_id, "lapsed")

    def _cancel_membership(self, subscription):
        self._transition_by_subscription(subscription["id"], "cancelled")

    def _transition_or_create_membership(self, metadata, new_status):
        schema = metadata.get("tenant_schema")
        user_id = metadata.get("user_id")
        membership_type_id = metadata.get("membership_type_id")

        if not all([schema, user_id, membership_type_id]):
            return

        try:
            with schema_context(schema):
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(pk=user_id)
                membership_type = MembershipType.objects.get(pk=membership_type_id)

                # Create or activate the membership
                membership, created = Membership.objects.get_or_create(
                    owner=user,
                    membership_type=membership_type,
                    defaults={"status": new_status},
                )
                if not created and membership.status != new_status:
                    membership.status = new_status
                    membership.save(update_fields=["status", "updated_at"])
        except Exception:
            pass  # Log in production

    def _transition_by_subscription(self, subscription_id, new_status):
        # In a full implementation, store subscription_id on Membership and look it up here
        # For now, this is a placeholder that would be completed with that field
        pass


class CustomerPortalView(APIView):
    """Generate a Stripe Customer Portal session for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = request.tenant

        if not tenant.stripe_account_id:
            return Response(
                {"detail": "No payment account configured."},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        customer_email = request.user.email
        return_url = request.data.get("return_url", f"http://{request.get_host()}/my-memberships")

        try:
            # Look up the customer by email on the connected account
            customers = stripe.Customer.list(
                email=customer_email,
                limit=1,
                stripe_account=tenant.stripe_account_id,
            )
            if not customers.data:
                return Response(
                    {"detail": "No billing account found for this user."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            portal_session = stripe.billing_portal.Session.create(
                customer=customers.data[0].id,
                return_url=return_url,
                stripe_account=tenant.stripe_account_id,
            )
        except stripe.StripeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"url": portal_session.url})


# ---------------------------------------------------------------------------
# #17 — Platform billing (plan limits + platform Stripe subscriptions)
# ---------------------------------------------------------------------------


class PlatformPlanUpgradeView(APIView):
    """
    Admin upgrades/downgrades their Tenant's platform plan.
    For paid plans, creates a Stripe Subscription on the platform's Stripe account.
    """

    permission_classes = [IsAuthenticated]

    PLAN_PRICES = {
        # In production these would be real Price IDs from the platform's Stripe account
        "pro": "price_pro_monthly",
    }

    def post(self, request):
        if not request.user.is_tenant_admin:
            return Response({"detail": "Admin only."}, status=status.HTTP_403_FORBIDDEN)

        new_plan = request.data.get("plan")
        if new_plan not in ("free", "pro"):
            return Response({"detail": "Plan must be 'free' or 'pro'."}, status=status.HTTP_400_BAD_REQUEST)

        tenant = request.tenant

        if new_plan == "pro" and settings.STRIPE_SECRET_KEY:
            # Create a platform-level Stripe Subscription for the tenant
            try:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    metadata={"tenant_schema": tenant.schema_name},
                )
                stripe.Subscription.create(
                    customer=customer.id,
                    items=[{"price": self.PLAN_PRICES["pro"]}],
                    metadata={"tenant_schema": tenant.schema_name},
                )
            except stripe.StripeError as e:
                return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        with schema_context("public"):
            from tenancy.models import Tenant as TenantModel
            TenantModel.objects.filter(pk=tenant.pk).update(plan=new_plan)

        return Response({"plan": new_plan})


class PlatformWebhookView(APIView):
    """
    Stripe webhook for platform-level billing events
    (plan subscription success/failure for the platform's own Stripe account).
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET

        import json as json_module
        if webhook_secret:
            try:
                stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            except (ValueError, stripe.SignatureVerificationError):
                return Response({"detail": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)

        event = json_module.loads(payload)
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "customer.subscription.deleted":
            # Downgrade tenant to free if their platform subscription is cancelled
            schema = data.get("metadata", {}).get("tenant_schema")
            if schema:
                with schema_context("public"):
                    from tenancy.models import Tenant as TenantModel
                    TenantModel.objects.filter(schema_name=schema).update(plan="free")

        return Response({"received": True})
