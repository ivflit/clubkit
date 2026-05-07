# Use django-tenants library for multi-tenant schema infrastructure

We use the `django-tenants` library rather than building custom schema provisioning, migration routing, and middleware. The library implements exactly the separate-schema-per-Tenant strategy chosen in ADR-0001 — it handles schema creation on Tenant save, provides `migrate_schemas` for cross-schema migrations, ships middleware for subdomain-based `search_path` switching, and includes a database router for shared vs tenant app separation. Building this from scratch would reimplement well-tested functionality and introduce unnecessary risk in the data isolation layer.

## Consequences

- `django.contrib.auth` is in `TENANT_APPS` (not `SHARED_APPS`), so each Tenant schema has its own `auth_user` table. There is no global user table in the public schema. This means Platform Admin auth (issue #16) will need a separate model in the public schema.
- Migrations must be run via `python manage.py migrate_schemas` (not the standard `migrate`).
- Schema deletion tests require `TransactionTestCase` because `DROP SCHEMA CASCADE` cannot run inside the implicit transaction that Django's `TestCase` uses.
- Local development uses `*.lvh.me` for subdomain routing (resolves to `127.0.0.1`).
