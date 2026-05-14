"""
Management command: send renewal reminder emails.

Run via cron: python manage.py send_renewal_reminders --days 7

Iterates all Tenant schemas and sends reminder emails to Users whose active Membership
ends within N days.
"""

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import tenant_context

from tenancy.models import Tenant


class Command(BaseCommand):
    help = "Send renewal reminder emails to Members whose Membership renews in N days."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days before renewal to send the reminder (default: 7).",
        )

    def handle(self, *args, **options):
        days = options["days"]
        today = timezone.now().date()
        target_date = today + datetime.timedelta(days=days)

        tenants = Tenant.objects.exclude(schema_name="public")
        sent = 0
        skipped = 0

        for tenant in tenants:
            with tenant_context(tenant):
                from memberships.models import Membership
                from notifications.services import send_renewal_reminder_email

                memberships = Membership.objects.filter(
                    status="active", end_date=target_date
                ).select_related("owner", "membership_type")

                for membership in memberships:
                    try:
                        send_renewal_reminder_email(membership)
                        sent += 1
                    except Exception as e:
                        self.stderr.write(
                            f"Error sending renewal reminder for membership {membership.id}: {e}"
                        )
                        skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Renewal reminders: sent={sent}, skipped={skipped} (days={days})"
            )
        )
