from django.db import connection
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from django_tenants.utils import tenant_context

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser
from memberships.models import Membership, MembershipType
from events.models import Event, EventRegistration


class DashboardTest(TestCase):
    """Tests for the member dashboard endpoint: data aggregation and empty states."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(
            schema_name="test_dashboard",
            name="Dashboard Club",
            slug="test-dashboard",
        )
        self.tenant.save()
        TenantDomain.objects.create(
            domain="test-dashboard.lvh.me",
            tenant=self.tenant,
            is_primary=True,
        )

        self.client = APIClient()
        self.host = "test-dashboard.lvh.me"

        with tenant_context(self.tenant):
            self.user = CustomUser.objects.create_user(
                username="member@test.com",
                email="member@test.com",
                password="MemberPass123!",
                role="member",
            )
            self.other_user = CustomUser.objects.create_user(
                username="other@test.com",
                email="other@test.com",
                password="OtherPass123!",
                role="member",
            )
            self.membership_type = MembershipType.objects.create(
                name="Adult Annual",
                price="120.00",
                billing_frequency="annual",
                renewal_mode="rolling",
            )

    def _get_token(self, email="member@test.com", password="MemberPass123!"):
        response = self.client.post(
            "/api/auth/login/",
            {"username": email, "password": password},
            format="json",
            HTTP_HOST=self.host,
        )
        return response.data["access"]

    def test_dashboard_requires_authentication(self):
        response = self.client.get(
            "/api/auth/dashboard/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 401)

    def test_empty_dashboard(self):
        """User with no memberships and no registrations gets empty lists."""
        token = self._get_token()
        response = self.client.get(
            "/api/auth/dashboard/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_memberships"], [])
        self.assertEqual(response.data["upcoming_events"], [])

    def test_dashboard_shows_active_memberships(self):
        """Active memberships are included; lapsed and cancelled are not."""
        with tenant_context(self.tenant):
            active = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
            )
            lapsed = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="lapsed",
            )
            cancelled = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="cancelled",
            )

        token = self._get_token()
        response = self.client.get(
            "/api/auth/dashboard/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        membership_ids = [m["id"] for m in response.data["active_memberships"]]
        self.assertIn(active.id, membership_ids)
        self.assertNotIn(lapsed.id, membership_ids)
        self.assertNotIn(cancelled.id, membership_ids)

    def test_dashboard_membership_fields(self):
        """Dashboard memberships include expected fields."""
        with tenant_context(self.tenant):
            membership = Membership.objects.create(
                owner=self.user,
                membership_type=self.membership_type,
                status="active",
            )

        token = self._get_token()
        response = self.client.get(
            "/api/auth/dashboard/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        m = response.data["active_memberships"][0]
        self.assertEqual(m["id"], membership.id)
        self.assertEqual(m["membership_type_name"], "Adult Annual")
        self.assertEqual(m["status"], "active")
        self.assertIn("end_date", m)

    def test_dashboard_shows_upcoming_registered_events(self):
        """Upcoming events the user is registered for appear on the dashboard."""
        future_dt = timezone.now() + timezone.timedelta(days=7)
        with tenant_context(self.tenant):
            admin = CustomUser.objects.create_user(
                username="admin@test.com",
                email="admin@test.com",
                password="AdminPass123!",
                role="admin",
            )
            event = Event.objects.create(
                title="Training Session",
                date_time=future_dt,
                location="Main Pitch",
                visibility="public",
                status="upcoming",
                created_by=admin,
            )
            EventRegistration.objects.create(event=event, user=self.user)

        token = self._get_token()
        response = self.client.get(
            "/api/auth/dashboard/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["upcoming_events"]), 1)
        ev = response.data["upcoming_events"][0]
        self.assertEqual(ev["id"], event.id)
        self.assertEqual(ev["title"], "Training Session")
        self.assertIn("date_time", ev)
        self.assertIn("location", ev)

    def test_dashboard_excludes_past_events(self):
        """Events in the past (or with status 'past') are excluded even if registered."""
        past_dt = timezone.now() - timezone.timedelta(days=1)
        with tenant_context(self.tenant):
            admin = CustomUser.objects.create_user(
                username="admin2@test.com",
                email="admin2@test.com",
                password="AdminPass123!",
                role="admin",
            )
            past_event = Event.objects.create(
                title="Past Event",
                date_time=past_dt,
                location="Pitch",
                visibility="public",
                status="upcoming",
                created_by=admin,
            )
            EventRegistration.objects.create(event=past_event, user=self.user)

        token = self._get_token()
        response = self.client.get(
            "/api/auth/dashboard/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["upcoming_events"], [])

    def test_dashboard_excludes_other_users_data(self):
        """Dashboard only returns data belonging to the authenticated user."""
        future_dt = timezone.now() + timezone.timedelta(days=7)
        with tenant_context(self.tenant):
            admin = CustomUser.objects.create_user(
                username="admin3@test.com",
                email="admin3@test.com",
                password="AdminPass123!",
                role="admin",
            )
            # other_user has a membership and event registration
            Membership.objects.create(
                owner=self.other_user,
                membership_type=self.membership_type,
                status="active",
            )
            event = Event.objects.create(
                title="Other Event",
                date_time=future_dt,
                visibility="public",
                status="upcoming",
                created_by=admin,
            )
            EventRegistration.objects.create(event=event, user=self.other_user)

        token = self._get_token()
        response = self.client.get(
            "/api/auth/dashboard/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["active_memberships"], [])
        self.assertEqual(response.data["upcoming_events"], [])

    def test_dashboard_events_ordered_by_date(self):
        """Upcoming events are returned in ascending date order."""
        now = timezone.now()
        with tenant_context(self.tenant):
            admin = CustomUser.objects.create_user(
                username="admin4@test.com",
                email="admin4@test.com",
                password="AdminPass123!",
                role="admin",
            )
            event_later = Event.objects.create(
                title="Later Event",
                date_time=now + timezone.timedelta(days=14),
                visibility="public",
                status="upcoming",
                created_by=admin,
            )
            event_sooner = Event.objects.create(
                title="Sooner Event",
                date_time=now + timezone.timedelta(days=3),
                visibility="public",
                status="upcoming",
                created_by=admin,
            )
            EventRegistration.objects.create(event=event_later, user=self.user)
            EventRegistration.objects.create(event=event_sooner, user=self.user)

        token = self._get_token()
        response = self.client.get(
            "/api/auth/dashboard/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        events = response.data["upcoming_events"]
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["title"], "Sooner Event")
        self.assertEqual(events[1]["title"], "Later Event")
