from django.db import connection
from django.test import TestCase, TransactionTestCase

from tenancy.models import Tenant, TenantDomain


class SchemaProvisioningTest(TestCase):
    """Verify that creating a Tenant automatically provisions a schema."""

    def setUp(self):
        connection.set_schema_to_public()

    def _schema_exists(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = %s)",
                [schema_name],
            )
            return cursor.fetchone()[0]

    def _create_tenant(self, slug, schema_name=None, domain=None):
        schema_name = schema_name or slug.replace("-", "_")
        domain = domain or f"{slug}.lvh.me"
        tenant = Tenant(schema_name=schema_name, name=f"{slug} FC", slug=slug)
        tenant.save()
        TenantDomain.objects.create(domain=domain, tenant=tenant, is_primary=True)
        return tenant

    def test_schema_created_on_tenant_save(self):
        tenant = self._create_tenant("riverside")
        self.assertTrue(self._schema_exists(tenant.schema_name))

    def test_tenant_schema_has_user_table(self):
        tenant = self._create_tenant("parkside")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_schema = %s AND table_name = 'users_customuser'"
                ")",
                [tenant.schema_name],
            )
            self.assertTrue(cursor.fetchone()[0])


class SchemaCleanupTest(TransactionTestCase):
    """Schema deletion requires TransactionTestCase because DROP SCHEMA
    cannot run inside the implicit transaction that TestCase uses."""

    def _schema_exists(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = %s)",
                [schema_name],
            )
            return cursor.fetchone()[0]

    def test_schema_dropped_on_tenant_delete(self):
        connection.set_schema_to_public()
        tenant = Tenant(schema_name="deleteme", name="Delete Me FC", slug="deleteme")
        tenant.save()
        TenantDomain.objects.create(domain="deleteme.lvh.me", tenant=tenant, is_primary=True)
        self.assertTrue(self._schema_exists("deleteme"))
        tenant.delete()
        self.assertFalse(self._schema_exists("deleteme"))
