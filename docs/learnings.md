# Learnings

Captured during implementation — insights, gotchas, and ideas for future work.

## Gotchas

- **Schema deletion in tests**: `DROP SCHEMA CASCADE` cannot run inside Django's `TestCase` implicit transaction. Use `TransactionTestCase` for tests that delete Tenants/schemas.
- **`django.contrib.auth` in TENANT_APPS**: Since auth lives in per-Tenant schemas, there is no superuser in the public schema. `createsuperuser` must be run within a Tenant context. Platform Admin auth will need a separate model in the public schema (see issue #16).
- **Local subdomain routing**: Standard `localhost` doesn't support subdomains. Use `*.lvh.me` (resolves to `127.0.0.1`) for local development, e.g. `test-club.lvh.me:8000`.
- **`migrate_schemas` not `migrate`**: Always use `python manage.py migrate_schemas` to apply migrations. The standard `migrate` only runs against the default schema.
- **`validate_subdomain_slug` raises Django `ValidationError`**, not DRF's `serializers.ValidationError`. The serializer must catch and re-raise to return proper API error responses.
- **BrandKit uses `FileField`** (not `ImageField`) to avoid requiring Pillow. Uploaded files are not validated as images at the Django level.

## Post-v1 Ideas

- Upgrade logo/hero_image from `FileField` to `ImageField` (with Pillow) for server-side image validation and thumbnail generation
- Add image dimension/size validation on upload (e.g. max 2MB, minimum logo dimensions)
- Configurable domain suffix — currently hardcoded to `.lvh.me` in onboarding; production will need a configurable base domain
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

## Edge Cases

- Schema names cannot contain hyphens (PostgreSQL limitation), so `schema_name` uses `slug.replace("-", "_")`. If a slug is `a-b` and another is `a_b`, they'd collide on schema_name. The slug uniqueness constraint prevents this indirectly, but it's worth noting.

## Technical Debt

- BrandKit uses `FileField` (not `ImageField`) to avoid requiring Pillow as a dependency. This means uploaded files are not validated as images at the Django level.
