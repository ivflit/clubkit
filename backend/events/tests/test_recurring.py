from django.db import connection
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from django_tenants.utils import tenant_context

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser
from events.models import Event, EventSeries


class RecurringEventsTest(TestCase):
    """Tests for recurring Event series: generation, individual editing, and series cancellation."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(
            schema_name="test_recurring",
            name="Recurring Club",
            slug="test-recurring",
        )
        self.tenant.save()
        TenantDomain.objects.create(
            domain="test-recurring.lvh.me",
            tenant=self.tenant,
            is_primary=True,
        )

        self.client = APIClient()
        self.host = "test-recurring.lvh.me"

        with tenant_context(self.tenant):
            self.admin = CustomUser.objects.create_user(
                username="admin@test.com",
                email="admin@test.com",
                password="AdminPass123!",
                role="admin",
            )
            self.member = CustomUser.objects.create_user(
                username="member@test.com",
                email="member@test.com",
                password="MemberPass123!",
                role="member",
            )

    def _get_token(self, email, password):
        response = self.client.post(
            "/api/auth/login/",
            {"username": email, "password": password},
            format="json",
            HTTP_HOST=self.host,
        )
        return response.data["access"]

    def _admin_token(self):
        return self._get_token("admin@test.com", "AdminPass123!")

    def _member_token(self):
        return self._get_token("member@test.com", "MemberPass123!")

    def test_create_weekly_series_generates_occurrences(self):
        """Creating a weekly series from Mon to Mon+3weeks generates 4 occurrences."""
        token = self._admin_token()
        response = self.client.post(
            "/api/events/series/",
            {
                "title": "Tuesday Training",
                "description": "Weekly session",
                "location": "Main Pitch",
                "visibility": "public",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-02",
                "end_date": "2026-06-23",
                "time": "19:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 201)
        series_id = response.data["id"]
        self.assertEqual(response.data["title"], "Tuesday Training")

        with tenant_context(self.tenant):
            series = EventSeries.objects.get(pk=series_id)
            occurrences = list(series.occurrences.all())
        self.assertEqual(len(occurrences), 4)

    def test_create_fortnightly_series_generates_correct_occurrences(self):
        """Fortnightly series generates occurrences every 14 days."""
        token = self._admin_token()
        response = self.client.post(
            "/api/events/series/",
            {
                "title": "Fortnightly Match",
                "recurrence_pattern": "fortnightly",
                "start_date": "2026-06-01",
                "end_date": "2026-06-29",
                "time": "14:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 201)
        series_id = response.data["id"]

        with tenant_context(self.tenant):
            series = EventSeries.objects.get(pk=series_id)
            occurrences = list(series.occurrences.order_by("date_time"))
        # 2026-06-01 and 2026-06-15 (2026-06-29 would be the third, included)
        self.assertEqual(len(occurrences), 3)

    def test_create_series_requires_admin(self):
        """Non-admin users cannot create series."""
        token = self._member_token()
        response = self.client.post(
            "/api/events/series/",
            {
                "title": "Training",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-02",
                "end_date": "2026-06-09",
                "time": "19:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_create_series_requires_authentication(self):
        """Unauthenticated requests cannot create series."""
        response = self.client.post(
            "/api/events/series/",
            {
                "title": "Training",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-02",
                "end_date": "2026-06-09",
                "time": "19:00",
            },
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 401)

    def test_end_date_before_start_date_rejected(self):
        """Series with end_date before start_date returns 400."""
        token = self._admin_token()
        response = self.client.post(
            "/api/events/series/",
            {
                "title": "Bad Dates",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-15",
                "end_date": "2026-06-01",
                "time": "19:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_each_occurrence_is_standalone_event(self):
        """Each generated occurrence is an independent Event that can be edited."""
        token = self._admin_token()
        create_response = self.client.post(
            "/api/events/series/",
            {
                "title": "Weekly Training",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-02",
                "end_date": "2026-06-09",
                "time": "19:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(create_response.status_code, 201)
        series_id = create_response.data["id"]

        with tenant_context(self.tenant):
            series = EventSeries.objects.get(pk=series_id)
            occurrences = list(series.occurrences.order_by("date_time"))
        self.assertEqual(len(occurrences), 2)

        # Edit only the first occurrence
        first_id = occurrences[0].id
        second_id = occurrences[1].id

        edit_response = self.client.patch(
            f"/api/events/{first_id}/",
            {"title": "Special Session", "location": "Away Ground"},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(edit_response.status_code, 200)
        self.assertEqual(edit_response.data["title"], "Special Session")

        # Second occurrence is unchanged
        with tenant_context(self.tenant):
            second = Event.objects.get(pk=second_id)
        self.assertEqual(second.title, "Weekly Training")

    def test_editing_occurrence_does_not_affect_siblings(self):
        """Editing one occurrence title/location does not change other occurrences."""
        token = self._admin_token()
        create_response = self.client.post(
            "/api/events/series/",
            {
                "title": "Sunday Run",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-07",
                "end_date": "2026-06-21",
                "time": "08:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        series_id = create_response.data["id"]

        with tenant_context(self.tenant):
            series = EventSeries.objects.get(pk=series_id)
            ids = list(series.occurrences.order_by("date_time").values_list("id", flat=True))
        self.assertEqual(len(ids), 3)

        # Cancel only the first occurrence
        cancel_response = self.client.post(
            f"/api/events/{ids[0]}/cancel/",
            {},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(cancel_response.status_code, 200)

        with tenant_context(self.tenant):
            statuses = list(
                Event.objects.filter(pk__in=ids).order_by("date_time").values_list("status", flat=True)
            )
        self.assertEqual(statuses[0], "cancelled")
        self.assertEqual(statuses[1], "upcoming")
        self.assertEqual(statuses[2], "upcoming")

    def test_cancel_series_cancels_all_future_occurrences(self):
        """Cancelling the series cancels all future occurrences via the series cancel endpoint."""
        token = self._admin_token()
        create_response = self.client.post(
            "/api/events/series/",
            {
                "title": "Friday Fitness",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-05",
                "end_date": "2026-06-26",
                "time": "18:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        series_id = create_response.data["id"]

        with tenant_context(self.tenant):
            count_before = EventSeries.objects.get(pk=series_id).occurrences.filter(
                status="upcoming"
            ).count()
        self.assertEqual(count_before, 4)

        cancel_response = self.client.post(
            f"/api/events/series/{series_id}/cancel/",
            {},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(cancel_response.status_code, 200)
        self.assertIn("Cancelled", cancel_response.data["detail"])

        with tenant_context(self.tenant):
            remaining_upcoming = EventSeries.objects.get(pk=series_id).occurrences.filter(
                status="upcoming"
            ).count()
        self.assertEqual(remaining_upcoming, 0)

    def test_cancel_series_requires_admin(self):
        """Non-admin cannot cancel a series."""
        token = self._admin_token()
        create_response = self.client.post(
            "/api/events/series/",
            {
                "title": "Mon Training",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-01",
                "end_date": "2026-06-08",
                "time": "17:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        series_id = create_response.data["id"]

        member_token = self._member_token()
        response = self.client.post(
            f"/api/events/series/{series_id}/cancel/",
            {},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_occurrence_serializer_includes_series_info(self):
        """Event serializer includes series_id and series_title for recurring events."""
        token = self._admin_token()
        create_response = self.client.post(
            "/api/events/series/",
            {
                "title": "Recurring Series",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-01",
                "end_date": "2026-06-08",
                "time": "10:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        series_id = create_response.data["id"]

        # Get the events list as admin
        list_response = self.client.get(
            "/api/events/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(list_response.status_code, 200)
        recurring_events = [e for e in list_response.data if e.get("series_id") == series_id]
        self.assertTrue(len(recurring_events) >= 1)
        self.assertEqual(recurring_events[0]["series_title"], "Recurring Series")

    def test_list_series_as_admin(self):
        """Admin can list all series."""
        token = self._admin_token()
        self.client.post(
            "/api/events/series/",
            {
                "title": "Series A",
                "recurrence_pattern": "weekly",
                "start_date": "2026-06-01",
                "end_date": "2026-06-08",
                "time": "09:00",
            },
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        response = self.client.get(
            "/api/events/series/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Series A")
        self.assertEqual(response.data[0]["occurrence_count"], 2)
