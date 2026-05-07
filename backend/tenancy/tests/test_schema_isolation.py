from django.db import connection
from django.test import TestCase

from django_tenants.utils import tenant_context

from tenancy.models import Tenant, TenantDomain
from users.models import CustomUser


class SchemaIsolationTest(TestCase):
    """Verify that data in one Tenant schema is not visible from another."""

    def setUp(self):
        connection.set_schema_to_public()

        self.tenant_a = Tenant(schema_name="club_a", name="Club A", slug="club-a")
        self.tenant_a.save()
        TenantDomain.objects.create(
            domain="club-a.lvh.me", tenant=self.tenant_a, is_primary=True
        )

        self.tenant_b = Tenant(schema_name="club_b", name="Club B", slug="club-b")
        self.tenant_b.save()
        TenantDomain.objects.create(
            domain="club-b.lvh.me", tenant=self.tenant_b, is_primary=True
        )

    def test_user_in_tenant_a_not_visible_in_tenant_b(self):
        with tenant_context(self.tenant_a):
            CustomUser.objects.create_user(
                username="alice", email="alice@cluba.com", password="testpass123"
            )
            self.assertEqual(CustomUser.objects.count(), 1)

        with tenant_context(self.tenant_b):
            self.assertEqual(CustomUser.objects.count(), 0)

    def test_users_isolated_both_directions(self):
        with tenant_context(self.tenant_a):
            CustomUser.objects.create_user(
                username="alice", email="alice@cluba.com", password="testpass123"
            )

        with tenant_context(self.tenant_b):
            CustomUser.objects.create_user(
                username="bob", email="bob@clubb.com", password="testpass123"
            )

        with tenant_context(self.tenant_a):
            users = list(CustomUser.objects.values_list("username", flat=True))
            self.assertEqual(users, ["alice"])

        with tenant_context(self.tenant_b):
            users = list(CustomUser.objects.values_list("username", flat=True))
            self.assertEqual(users, ["bob"])

    def test_same_username_allowed_across_tenants(self):
        with tenant_context(self.tenant_a):
            CustomUser.objects.create_user(
                username="admin", email="admin@cluba.com", password="testpass123"
            )

        with tenant_context(self.tenant_b):
            user = CustomUser.objects.create_user(
                username="admin", email="admin@clubb.com", password="testpass123"
            )
            self.assertIsNotNone(user.pk)
