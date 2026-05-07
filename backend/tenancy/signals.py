from django.db import connection
from django.db.models.signals import post_delete
from django.dispatch import receiver

from tenancy.models import Tenant


@receiver(post_delete, sender=Tenant)
def drop_tenant_schema(sender, instance, **kwargs):
    schema = instance.schema_name
    if schema and schema != "public":
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = %s)",
                [schema],
            )
            exists = cursor.fetchone()[0]
            if exists:
                cursor.execute(f'DROP SCHEMA "{schema}" CASCADE')
