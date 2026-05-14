"""
Tests for email notification triggers and template rendering.
Email sending is mocked via Django's in-memory email backend.
"""

import datetime

from django.core import mail
from django.db import connection
from django.test import TestCase, override_settings
from django.utils import timezone

from django_tenants.utils import tenant_context

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser
from memberships.models import Membership, MembershipType
from events.models import Event, EventRegistration


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    NOTIFICATIONS_SEND_ASYNC=False,
    DEFAULT_FROM_EMAIL="noreply@clubkit.com",
)
class NotificationTriggerTest(TestCase):
    """Tests for notification trigger logic: correct lifecycle points fire emails."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(
            schema_name="test_notifications",
            name="Notify Club",
            slug="test-notifications",
        )
        self.tenant.save()
        TenantDomain.objects.create(
            domain="test-notifications.lvh.me",
            tenant=self.tenant,
            is_primary=True,
        )

        with tenant_context(self.tenant):
            self.user = CustomUser.objects.create_user(
                username="member@test.com",
                email="member@test.com",
                password="MemberPass123!",
                role="member",
                first_name="Alice",
            )
            self.membership_type = MembershipType.objects.create(
                name="Adult Annual",
                price="120.00",
                billing_frequency="annual",
                renewal_mode="rolling",
            )

    def test_membership_lapsed_sends_email(self):
        """Transitioning a Membership to 'lapsed' triggers a lapsed notification."""
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
            )
            membership.transition_to("lapsed")

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("member@test.com", email.to)
        self.assertIn("lapsed", email.subject.lower())

    def test_membership_lapsed_email_contains_club_name(self):
        """The lapsed email body includes the club name."""
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
            )
            membership.transition_to("lapsed")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Notify Club", mail.outbox[0].alternatives[0][0])

    def test_membership_cancelled_does_not_send_lapsed_email(self):
        """Transitioning to 'cancelled' does NOT fire the lapsed email."""
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
            )
            membership.transition_to("cancelled")

        self.assertEqual(len(mail.outbox), 0)

    def test_send_renewal_reminder_email_directly(self):
        """send_renewal_reminder_email sends email with correct fields."""
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
            )
            from notifications.services import send_renewal_reminder_email
            send_renewal_reminder_email(membership)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("member@test.com", email.to)
        self.assertIn("renew", email.subject.lower())
        self.assertIn("Adult Annual", email.alternatives[0][0])

    def test_send_event_reminder_email_directly(self):
        """send_event_reminder_email sends email with event details."""
        future_dt = timezone.now() + timezone.timedelta(days=1)
        with tenant_context(self.tenant):
            admin = CustomUser.objects.create_user(
                username="admin@test.com",
                email="admin@test.com",
                password="AdminPass123!",
                role="admin",
            )
            event = Event.objects.create(
                title="Tuesday Training",
                date_time=future_dt,
                location="Main Pitch",
                visibility="public",
                status="upcoming",
                created_by=admin,
            )
            registration = EventRegistration.objects.create(event=event, user=self.user)

            from notifications.services import send_event_reminder_email
            send_event_reminder_email(registration)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("member@test.com", email.to)
        self.assertIn("Tuesday Training", email.subject)
        self.assertIn("Tuesday Training", email.alternatives[0][0])

    def test_send_payment_failed_email_directly(self):
        """send_payment_failed_email sends email with payment failure message."""
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
            )
            from notifications.services import send_payment_failed_email
            send_payment_failed_email(membership)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("member@test.com", email.to)
        self.assertIn("payment", email.subject.lower())

    def test_template_renders_with_brand_kit_colours(self):
        """Email templates include the tenant's primary colour from Brand Kit."""
        from tenancy.models import BrandKit
        connection.set_schema_to_public()
        BrandKit.objects.update_or_create(
            tenant=self.tenant,
            defaults={"primary_colour": "#cc3300"},
        )

        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
            )
            from notifications.services import send_renewal_reminder_email
            send_renewal_reminder_email(membership)

        self.assertEqual(len(mail.outbox), 1)
        html_body = mail.outbox[0].alternatives[0][0]
        self.assertIn("#cc3300", html_body)

    def test_template_renders_without_brand_kit(self):
        """Email templates render gracefully when no Brand Kit is configured."""
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
            )
            from notifications.services import send_membership_lapsed_email
            send_membership_lapsed_email(membership)

        self.assertEqual(len(mail.outbox), 1)
        # Should not raise, and should contain fallback content
        html_body = mail.outbox[0].alternatives[0][0]
        self.assertIn("Notify Club", html_body)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    NOTIFICATIONS_SEND_ASYNC=False,
    DEFAULT_FROM_EMAIL="noreply@clubkit.com",
)
class RenewalReminderCommandTest(TestCase):
    """Tests for the send_renewal_reminders management command."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(
            schema_name="test_renewals",
            name="Renewal Club",
            slug="test-renewals",
        )
        self.tenant.save()
        TenantDomain.objects.create(
            domain="test-renewals.lvh.me",
            tenant=self.tenant,
            is_primary=True,
        )

        with tenant_context(self.tenant):
            self.user = CustomUser.objects.create_user(
                username="member@renewal.com",
                email="member@renewal.com",
                password="Pass123!",
                role="member",
            )
            self.membership_type = MembershipType.objects.create(
                name="Annual",
                price="100.00",
                billing_frequency="annual",
                renewal_mode="rolling",
            )

    def test_command_sends_reminder_for_membership_expiring_in_7_days(self):
        """Management command sends email to members expiring in exactly 7 days."""
        target_date = timezone.now().date() + datetime.timedelta(days=7)
        with tenant_context(self.tenant):
            Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
                end_date=target_date,
            )

        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("send_renewal_reminders", "--days", "7", stdout=out)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("member@renewal.com", mail.outbox[0].to)

    def test_command_skips_memberships_with_different_end_date(self):
        """Management command does not send reminders for wrong-date memberships."""
        wrong_date = timezone.now().date() + datetime.timedelta(days=14)
        with tenant_context(self.tenant):
            Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
                end_date=wrong_date,
            )

        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("send_renewal_reminders", "--days", "7", stdout=out)

        self.assertEqual(len(mail.outbox), 0)
