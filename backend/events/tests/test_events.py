from django.db import connection
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from django_tenants.utils import tenant_context

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser

from events.models import Event
from memberships.models import Membership, MembershipType


class EventCRUDTest(TestCase):
    """Tests for Event admin CRUD, public listing, and visibility enforcement."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(
            schema_name="test_events",
            name="Events Club",
            slug="test-events",
        )
        self.tenant.save()
        TenantDomain.objects.create(
            domain="test-events.lvh.me",
            tenant=self.tenant,
            is_primary=True,
        )

        self.client = APIClient()
        self.host = "test-events.lvh.me"

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
            self.membership_type = MembershipType.objects.create(
                name="Adult Annual",
                price="120.00",
                billing_frequency="annual",
                renewal_mode="rolling",
            )

        self.future_dt = (timezone.now() + timezone.timedelta(days=7)).isoformat()

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

    def _create_event(self, token, **overrides):
        data = {
            "title": "Training Session",
            "description": "<p>Weekly training</p>",
            "date_time": self.future_dt,
            "location": "Main Pitch",
            "visibility": "public",
            "capacity": 30,
        }
        data.update(overrides)
        return self.client.post(
            "/api/events/",
            data,
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

    # ── Admin CRUD ──────────────────────────────────────────────

    def test_admin_can_create_event(self):
        token = self._admin_token()
        response = self._create_event(token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Training Session")
        self.assertEqual(response.data["visibility"], "public")
        self.assertEqual(response.data["capacity"], 30)
        self.assertEqual(response.data["status"], "upcoming")
        self.assertIsNotNone(response.data["created_by"])

    def test_admin_can_list_events(self):
        token = self._admin_token()
        self._create_event(token)
        self._create_event(token, title="Match Day")

        response = self.client.get(
            "/api/events/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_admin_can_retrieve_event(self):
        token = self._admin_token()
        created = self._create_event(token)
        pk = created.data["id"]

        response = self.client.get(
            f"/api/events/{pk}/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Training Session")

    def test_admin_can_update_event(self):
        token = self._admin_token()
        created = self._create_event(token)
        pk = created.data["id"]

        response = self.client.patch(
            f"/api/events/{pk}/",
            {"title": "Updated Training", "location": "Indoor Hall"},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Updated Training")
        self.assertEqual(response.data["location"], "Indoor Hall")

    def test_admin_can_cancel_event(self):
        token = self._admin_token()
        created = self._create_event(token)
        pk = created.data["id"]

        response = self.client.post(
            f"/api/events/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "cancelled")

    def test_cancel_already_cancelled_returns_400(self):
        token = self._admin_token()
        created = self._create_event(token)
        pk = created.data["id"]

        self.client.post(
            f"/api/events/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        response = self.client.post(
            f"/api/events/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 400)

    # ── Permission checks ───────────────────────────────────────

    def test_member_cannot_create_event(self):
        token = self._member_token()
        response = self._create_event(token)
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_update_event(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        member_token = self._member_token()
        response = self.client.patch(
            f"/api/events/{pk}/",
            {"title": "Hacked"},
            format="json",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_cancel_event(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        member_token = self._member_token()
        response = self.client.post(
            f"/api/events/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_create_event(self):
        response = self.client.post(
            "/api/events/",
            {"title": "Anon Event", "date_time": self.future_dt},
            format="json",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 401)

    # ── Public event list ───────────────────────────────────────

    def test_public_list_shows_public_events(self):
        admin_token = self._admin_token()
        self._create_event(admin_token, title="Public Match", visibility="public")
        self._create_event(admin_token, title="Private Training", visibility="members_only")

        response = self.client.get(
            "/api/events/public/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Public Match")

    def test_public_list_excludes_cancelled(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]
        self.client.post(
            f"/api/events/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )

        response = self.client.get(
            "/api/events/public/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    # ── Event detail + visibility enforcement ───────────────────

    def test_public_event_visible_to_anyone(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token, visibility="public")
        pk = created.data["id"]

        response = self.client.get(
            f"/api/events/detail/{pk}/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Training Session")

    def test_members_only_event_returns_403_for_unauthenticated(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token, visibility="members_only")
        pk = created.data["id"]

        response = self.client.get(
            f"/api/events/detail/{pk}/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 403)

    def test_members_only_event_returns_403_for_guest(self):
        """User without active Membership cannot view members-only Events."""
        admin_token = self._admin_token()
        created = self._create_event(admin_token, visibility="members_only")
        pk = created.data["id"]

        member_token = self._member_token()
        response = self.client.get(
            f"/api/events/detail/{pk}/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_members_only_event_visible_to_active_member(self):
        """User with active Membership CAN view members-only Events."""
        admin_token = self._admin_token()
        created = self._create_event(admin_token, visibility="members_only")
        pk = created.data["id"]

        # Give member an active membership
        with tenant_context(self.tenant):
            Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
            )

        member_token = self._member_token()
        response = self.client.get(
            f"/api/events/detail/{pk}/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Training Session")

    # ── Member event list ───────────────────────────────────────

    def test_member_with_membership_sees_all_events(self):
        admin_token = self._admin_token()
        self._create_event(admin_token, title="Public Event", visibility="public")
        self._create_event(admin_token, title="Members Only Event", visibility="members_only")

        with tenant_context(self.tenant):
            Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
            )

        member_token = self._member_token()
        response = self.client.get(
            "/api/events/mine/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_guest_user_sees_only_public_events(self):
        admin_token = self._admin_token()
        self._create_event(admin_token, title="Public Event", visibility="public")
        self._create_event(admin_token, title="Members Only", visibility="members_only")

        member_token = self._member_token()
        response = self.client.get(
            "/api/events/mine/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Public Event")

    # ── Rich text description ───────────────────────────────────

    def test_event_stores_rich_text_description(self):
        admin_token = self._admin_token()
        html = "<h2>Schedule</h2><ul><li>Warm-up</li><li>Drills</li></ul>"
        created = self._create_event(admin_token, description=html)
        pk = created.data["id"]

        response = self.client.get(
            f"/api/events/detail/{pk}/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["description"], html)
