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

- Rich text editor upgrade: the Events admin currently uses a plain `<textarea>` for HTML content. A proper WYSIWYG editor (Tiptap, TipTap, or similar) would improve the admin experience. The backend stores raw HTML in a TextField which is rendered via `dangerouslySetInnerHTML` — sanitisation (e.g. DOMPurify) should be added before rendering user-supplied HTML in production.

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

- **Race condition on capacity enforcement**: The current EventRegistration capacity check (count registrations, compare to capacity, then create) is not atomic. Under high concurrency, two users could both pass the check and exceed capacity. For production, consider using `select_for_update()` on the Event row or a database constraint.

- **Cancelling registration after event starts**: Currently no time-based restriction on registration cancellation. A user could cancel their registration after the event has already started. Consider adding a cutoff time for cancellations.

- Schema names cannot contain hyphens (PostgreSQL limitation), so `schema_name` uses `slug.replace("-", "_")`. If a slug is `a-b` and another is `a_b`, they'd collide on schema_name. The slug uniqueness constraint prevents this indirectly, but it's worth noting.

## Public Site / Theming

- **CSS custom properties on `<html>`**: Setting `--brand-primary` and `--brand-accent` on the root `<html>` element via the Next.js root layout is the cleanest way to provide tenant branding without a client-side theme provider. The root layout runs server-side on every request, so the CSS vars are injected into the initial HTML — no flash of unstyled content.
- **BrandKit serializer includes `club_name`**: Added as a `read_only` SerializerMethodField reading `tenant.name`. This avoids a separate endpoint just for the club name. Existing tests checking specific fields pass unchanged.
- **Next.js fetch deduplication**: When the same URL is fetched multiple times within one server render (e.g. brand kit in root layout + brand kit in page), Next.js automatically deduplicates the underlying fetch calls. No explicit cache layer is needed for this pattern.
- **Mobile nav**: The current PublicHeader doesn't collapse to a hamburger menu on small screens. A mobile-friendly nav (e.g. hidden menu toggle) would improve the experience on phones. Acceptable for v1 given fixed nav links fit in a single row, but should be addressed before launch.

## Platform Admin

- **Separate JWT flow for Platform Admins**: Platform Admin tokens are standard `AccessToken` objects (from simplejwt) but carry a custom `platform_admin_id` claim instead of `user_id`. A custom `PlatformAdminAuthentication` class decodes the token, checks for this claim, and resolves the `PlatformAdmin` instance. Views set `authentication_classes = [PlatformAdminAuthentication]` to opt into this flow — tenant endpoints are unaffected.
- **Cross-schema stats are sequential, not parallel**: Aggregating stats across tenant schemas iterates all tenants and runs a `schema_context(...)` query per tenant. This is O(n) database round-trips and will be slow at scale. For production, consider materialised views, caching, or a background job that pre-computes stats.
- **Stripe connection status is a placeholder**: `stripe_connected` always returns `False` until Stripe Connect (#8) is implemented. The field is included in the API response now so the frontend shape is established.
- **PlatformAdmin bootstrap**: There's no in-app way to create the very first PlatformAdmin (a chicken-and-egg problem — all create endpoints require an existing PlatformAdmin token). In production, use a Django management command to bootstrap the first account.

## Recurring Events

- **EventSeries as a lightweight parent**: The series model holds only `title`, `recurrence_pattern`, and `created_by`. All event-specific data (description, location, visibility, etc.) is duplicated across occurrences at generation time. This means editing the "series" data doesn't retroactively update all occurrences — each occurrence is fully independent after creation. This is the desired behaviour (edit one → don't affect others).
- **`bulk_create` for occurrence generation**: Using `Event.objects.bulk_create(events)` generates all occurrences in a single SQL statement instead of N inserts. For large recurrence ranges (e.g. weekly for 2 years = 104 events), this is meaningfully faster.
- **Series cancel only affects future occurrences**: The series cancel endpoint filters `date_time__gte=now()` so past occurrences are not touched — this is intentional, matching the acceptance criterion "cancel all future occurrences".
- **No occurrence limit enforced**: The API doesn't cap the number of occurrences that can be generated. A malicious admin could set a 100-year weekly series = 5200 events. For production, consider enforcing a max occurrence count (e.g. 52 weeks = 1 year).

## Member Dashboard

- **Dashboard aggregates across apps**: The dashboard view imports `Membership` from `memberships` and `EventRegistration` from `events` inside the method body to avoid circular imports at module level in `users/views.py`.
- **Profile page link is a forward reference**: The dashboard includes a quick link to `/profile` which doesn't exist yet (no profile issue implemented in v1). The link is present to satisfy the acceptance criterion and will resolve once the profile page is built.
- **Filter by date AND status for upcoming events**: To exclude past events from the dashboard, the query filters on both `event__status="upcoming"` AND `event__date_time__gte=timezone.now()`. Status alone isn't enough — a stale "upcoming" event with a past date would still show without the datetime filter.

## Technical Debt

- BrandKit uses `FileField` (not `ImageField`) to avoid requiring Pillow as a dependency. This means uploaded files are not validated as images at the Django level.
- JWT tokens are stored in `localStorage` — suitable for SPA but not httpOnly. Consider moving to httpOnly cookies if XSS attack surface grows.
- Password reset returns token+uid directly in the API response (for dev). Production must send these via email only to avoid exposing reset tokens.
- Membership end dates use simple day arithmetic (30/365 days) rather than calendar-month precision. Production should use `dateutil.relativedelta` for accurate month/year calculations (e.g. Feb 28 + 1 month = Mar 28, not Mar 30).
- `DateField` default must use `datetime.date.today` not `timezone.now` — DRF's `DateField` serializer refuses to coerce datetime to date to avoid losing timezone info.
