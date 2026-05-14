"""
Notification services: compose and dispatch emails to Tenant Users.

Emails are sent asynchronously via a background thread (NOTIFICATIONS_SEND_ASYNC=True,
the default). Set NOTIFICATIONS_SEND_ASYNC=False in test settings for synchronous dispatch.

All email templates apply the Tenant's Brand Kit (logo, primary colour) automatically.
"""

import threading

from django.conf import settings
from django.core.mail import send_mail
from django.db import connection
from django.template.loader import render_to_string


DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@clubkit.com")


def _get_brand_kit():
    """Fetch BrandKit for the current Tenant (must be called within a tenant schema context)."""
    from tenancy.models import BrandKit

    try:
        return BrandKit.objects.get(tenant=connection.tenant)
    except Exception:
        return None


def _do_send(to_email, subject, html_body):
    """Actually send the email (called directly or from a thread)."""
    send_mail(
        subject=subject,
        message="",  # plain-text fallback (empty — HTML-only)
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        html_message=html_body,
        fail_silently=True,
    )


def _send(to_email, subject, html_body):
    """Dispatch an email — async in production, sync when NOTIFICATIONS_SEND_ASYNC=False."""
    if getattr(settings, "NOTIFICATIONS_SEND_ASYNC", True):
        t = threading.Thread(
            target=_do_send, args=(to_email, subject, html_body), daemon=True
        )
        t.start()
    else:
        _do_send(to_email, subject, html_body)


def _render(template_name, context):
    return render_to_string(f"notifications/{template_name}", context)


def _base_context():
    brand_kit = _get_brand_kit()
    tenant = connection.tenant
    return {
        "brand_kit": brand_kit,
        "club_name": tenant.name if tenant else "Your Club",
        "primary_colour": brand_kit.primary_colour if brand_kit else "#1a73e8",
        "logo_url": brand_kit.logo.url if (brand_kit and brand_kit.logo) else None,
    }


# ── Public notification functions ─────────────────────────────────────────────


def send_renewal_reminder_email(membership):
    """Send a membership renewal reminder to the owner."""
    ctx = _base_context()
    ctx.update(
        {
            "user": membership.owner,
            "membership": membership,
            "membership_type_name": membership.membership_type.name,
            "end_date": membership.end_date,
        }
    )
    html = _render("renewal_reminder.html", ctx)
    subject = f"[{ctx['club_name']}] Your {ctx['membership_type_name']} membership renews soon"
    _send(membership.owner.email, subject, html)


def send_membership_lapsed_email(membership):
    """Send a lapsed membership notification to the owner."""
    ctx = _base_context()
    ctx.update(
        {
            "user": membership.owner,
            "membership": membership,
            "membership_type_name": membership.membership_type.name,
        }
    )
    html = _render("membership_lapsed.html", ctx)
    subject = f"[{ctx['club_name']}] Your membership has lapsed"
    _send(membership.owner.email, subject, html)


def send_payment_failed_email(membership):
    """Send a payment failure notification. Called from Stripe webhook handler (#8)."""
    ctx = _base_context()
    ctx.update(
        {
            "user": membership.owner,
            "membership": membership,
            "membership_type_name": membership.membership_type.name,
        }
    )
    html = _render("payment_failed.html", ctx)
    subject = f"[{ctx['club_name']}] Payment failed — action required"
    _send(membership.owner.email, subject, html)


def send_event_reminder_email(registration):
    """Send an event reminder to a registered user."""
    ctx = _base_context()
    ctx.update(
        {
            "user": registration.user,
            "event": registration.event,
        }
    )
    html = _render("event_reminder.html", ctx)
    subject = f"[{ctx['club_name']}] Reminder: {registration.event.title} is tomorrow"
    _send(registration.user.email, subject, html)
