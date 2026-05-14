"""
Management command: send event reminder emails.

Run via cron: python manage.py send_event_reminders --hours 24

Iterates all Tenant schemas and sends reminder emails to Users registered for Events
starting within N hours.
"""

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_tenants.utils import tenant_context

from tenancy.models import Tenant


class Command(BaseCommand):
    help = "Send event reminder emails to Users registered for Events starting within N hours."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Hours before event to send the reminder (default: 24).",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        now = timezone.now()
        window_start = now + datetime.timedelta(hours=hours - 1)
        window_end = now + datetime.timedelta(hours=hours)

        tenants = Tenant.objects.exclude(schema_name="public")
        sent = 0
        skipped = 0

        for tenant in tenants:
            with tenant_context(tenant):
                from events.models import EventRegistration
                from notifications.services import send_event_reminder_email

                registrations = EventRegistration.objects.filter(
                    event__status="upcoming",
                    event__date_time__gte=window_start,
                    event__date_time__lt=window_end,
                ).select_related("event", "user")

                for registration in registrations:
                    try:
                        send_event_reminder_email(registration)
                        sent += 1
                    except Exception as e:
                        self.stderr.write(
                            f"Error sending event reminder for registration {registration.id}: {e}"
                        )
                        skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Event reminders: sent={sent}, skipped={skipped} (hours={hours})"
            )
        )
