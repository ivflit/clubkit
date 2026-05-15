"""Stripe Connect helpers — Express account onboarding for Tenants."""
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_connect_account():
    """Create a new Stripe Express account for a Tenant."""
    account = stripe.Account.create(type="express")
    return account.id


def create_account_link(account_id, return_url, refresh_url):
    """Generate a one-time Account Link URL for completing Express onboarding."""
    link = stripe.AccountLink.create(
        account=account_id,
        return_url=return_url,
        refresh_url=refresh_url,
        type="account_onboarding",
    )
    return link.url


def retrieve_account(account_id):
    """Retrieve a Stripe account to check onboarding status."""
    return stripe.Account.retrieve(account_id)


def delete_account(account_id):
    """Delete (disconnect) a Stripe Express account."""
    stripe.Account.delete(account_id)
