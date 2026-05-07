# Learnings

Captured during implementation — insights, gotchas, and ideas for future work.

## Gotchas

- **Schema deletion in tests**: `DROP SCHEMA CASCADE` cannot run inside Django's `TestCase` implicit transaction. Use `TransactionTestCase` for tests that delete Tenants/schemas.
- **`django.contrib.auth` in TENANT_APPS**: Since auth lives in per-Tenant schemas, there is no superuser in the public schema. `createsuperuser` must be run within a Tenant context. Platform Admin auth will need a separate model in the public schema (see issue #16).
- **Local subdomain routing**: Standard `localhost` doesn't support subdomains. Use `*.lvh.me` (resolves to `127.0.0.1`) for local development, e.g. `test-club.lvh.me:8000`.
- **`migrate_schemas` not `migrate`**: Always use `python manage.py migrate_schemas` to apply migrations. The standard `migrate` only runs against the default schema.

## Post-v1 Ideas

- Custom domains for Tenants (e.g. `www.riversidefc.co.uk`) with automated SSL provisioning
- Dependents and child Memberships (deferred from v1 — issue #8 in design, data model supports owner/subject separation)
- Per-event ticketing/payments
- SMS and push notifications
- Member directory (opt-in)
- Club document storage
- Mobile app (React Native, sharing frontend components)
- GoCardless integration for Direct Debit alongside Stripe
- Customisable email templates for Admins
- Complex recurrence rules (monthly, "every third Thursday", etc.)

## Technical Debt

(None yet — capture items here as they arise during implementation)
