from django.db import connection
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from django_tenants.utils import tenant_context

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser

from events.models import Event, EventRegistration
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


class EventRegistrationTest(TestCase):
    """Tests for Event registration, capacity enforcement, and cancellation."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant = Tenant(
            schema_name="test_reg",
            name="Reg Club",
            slug="test-reg",
        )
        self.tenant.save()
        TenantDomain.objects.create(
            domain="test-reg.lvh.me",
            tenant=self.tenant,
            is_primary=True,
        )

        self.client = APIClient()
        self.host = "test-reg.lvh.me"

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
            self.member2 = CustomUser.objects.create_user(
                username="member2@test.com",
                email="member2@test.com",
                password="MemberPass123!",
                role="member",
            )
            self.membership_type = MembershipType.objects.create(
                name="Adult Annual",
                price="120.00",
                billing_frequency="annual",
                renewal_mode="rolling",
            )
            # Give member an active membership
            Membership.objects.create(
                owner=self.member,
                membership_type=self.membership_type,
            )
            Membership.objects.create(
                owner=self.member2,
                membership_type=self.membership_type,
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

    def _member2_token(self):
        return self._get_token("member2@test.com", "MemberPass123!")

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

    # ── Registration ─────────────────────────────────────────────

    def test_member_can_register_for_event(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        member_token = self._member_token()
        response = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["event"], pk)

    def test_unauthenticated_cannot_register(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        response = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 401)

    def test_duplicate_registration_rejected(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        member_token = self._member_token()
        self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        response = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Already registered", response.data["detail"])

    # ── Capacity enforcement ─────────────────────────────────────

    def test_capacity_enforced(self):
        """Registration rejected when event is full."""
        admin_token = self._admin_token()
        created = self._create_event(admin_token, capacity=1)
        pk = created.data["id"]

        # First registration succeeds
        member_token = self._member_token()
        r1 = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(r1.status_code, 201)

        # Second registration rejected — event is full
        member2_token = self._member2_token()
        r2 = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member2_token}",
        )
        self.assertEqual(r2.status_code, 400)
        self.assertIn("full", r2.data["detail"])

    def test_unlimited_capacity_allows_registration(self):
        """Events with no capacity limit always allow registration."""
        admin_token = self._admin_token()
        created = self._create_event(admin_token, capacity=None)
        pk = created.data["id"]

        member_token = self._member_token()
        response = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 201)

    # ── Event detail shows spots remaining and registration status ──

    def test_event_detail_shows_spots_remaining(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token, capacity=10)
        pk = created.data["id"]

        # Register one user
        member_token = self._member_token()
        self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )

        response = self.client.get(
            f"/api/events/detail/{pk}/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["spots_remaining"], 9)
        self.assertTrue(response.data["is_registered"])
        self.assertEqual(response.data["registration_count"], 1)

    def test_event_detail_shows_not_registered(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        member_token = self._member_token()
        response = self.client.get(
            f"/api/events/detail/{pk}/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_registered"])

    def test_event_detail_unauthenticated_shows_not_registered(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        response = self.client.get(
            f"/api/events/detail/{pk}/",
            HTTP_HOST=self.host,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_registered"])

    # ── Cancel registration ──────────────────────────────────────

    def test_member_can_cancel_registration(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        member_token = self._member_token()
        self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        response = self.client.post(
            f"/api/events/{pk}/unregister/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 200)

        # Verify registration is gone
        with tenant_context(self.tenant):
            self.assertEqual(EventRegistration.objects.filter(event_id=pk).count(), 0)

    def test_cancel_unregistered_returns_404(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        member_token = self._member_token()
        response = self.client.post(
            f"/api/events/{pk}/unregister/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 404)

    def test_cancelling_frees_spot(self):
        """After cancelling, another user can register for a full event."""
        admin_token = self._admin_token()
        created = self._create_event(admin_token, capacity=1)
        pk = created.data["id"]

        # Fill the event
        member_token = self._member_token()
        self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        # Cancel
        self.client.post(
            f"/api/events/{pk}/unregister/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        # Another user can now register
        member2_token = self._member2_token()
        response = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member2_token}",
        )
        self.assertEqual(response.status_code, 201)

    # ── My registered events ─────────────────────────────────────

    def test_my_registered_events(self):
        admin_token = self._admin_token()
        ev1 = self._create_event(admin_token, title="Event 1")
        ev2 = self._create_event(admin_token, title="Event 2")

        member_token = self._member_token()
        self.client.post(
            f"/api/events/{ev1.data['id']}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.client.post(
            f"/api/events/{ev2.data['id']}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )

        response = self.client.get(
            "/api/events/my-registrations/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    # ── Admin registrations view ─────────────────────────────────

    def test_admin_can_view_event_registrations(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        # Register two members
        member_token = self._member_token()
        self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        member2_token = self._member2_token()
        self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member2_token}",
        )

        response = self.client.get(
            f"/api/events/{pk}/registrations/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_member_cannot_view_admin_registrations(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        member_token = self._member_token()
        response = self.client.get(
            f"/api/events/{pk}/registrations/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 403)

    # ── Members-only registration enforcement ────────────────────

    def test_guest_cannot_register_for_members_only_event(self):
        """User without active Membership cannot register for members-only Event."""
        admin_token = self._admin_token()
        created = self._create_event(admin_token, visibility="members_only")
        pk = created.data["id"]

        # Create a user with no membership
        with tenant_context(self.tenant):
            CustomUser.objects.create_user(
                username="guest@test.com",
                email="guest@test.com",
                password="GuestPass123!",
                role="member",
            )
        guest_token = self._get_token("guest@test.com", "GuestPass123!")
        response = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {guest_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_member_can_register_for_members_only_event(self):
        """User with active Membership CAN register for members-only Event."""
        admin_token = self._admin_token()
        created = self._create_event(admin_token, visibility="members_only")
        pk = created.data["id"]

        member_token = self._member_token()
        response = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 201)

    # ── Cannot register for cancelled events ─────────────────────

    def test_cannot_register_for_cancelled_event(self):
        admin_token = self._admin_token()
        created = self._create_event(admin_token)
        pk = created.data["id"]

        # Cancel the event
        self.client.post(
            f"/api/events/{pk}/cancel/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )

        member_token = self._member_token()
        response = self.client.post(
            f"/api/events/{pk}/register/",
            HTTP_HOST=self.host,
            HTTP_AUTHORIZATION=f"Bearer {member_token}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("cancelled or past", response.data["detail"])
