# Separate schemas for Tenant data isolation

We use a shared database with a separate schema per Tenant (rather than a shared schema with `tenant_id` filtering, or fully separate databases). This gives us hard data isolation — a query running in one Tenant's schema cannot accidentally access another Tenant's data — without the operational cost of managing separate database instances. The trade-off is that schema provisioning must be automated during Onboarding and database migrations must run across all Tenant schemas, but these are one-time automation problems rather than ongoing risks.

## Considered Options

- **Shared schema with `tenant_id`** — simplest to build, but every query must include a `tenant_id` filter. A single missed WHERE clause leaks data across Tenants. Rejected because data isolation was a primary concern.
- **Separate databases per Tenant** — strongest isolation, but operationally expensive (connection management, backups, monitoring per database). Overkill for the data sensitivity level of sports club information.
- **Separate schemas (chosen)** — middle ground. Isolation at the database level, shared infrastructure at the server level. Requires automated schema provisioning and cross-schema migration tooling.

## Consequences

- Onboarding must automatically provision a new schema with all current tables when a Tenant is created.
- Migration tooling must iterate over all Tenant schemas and apply changes to each one.
- The Platform Admin dashboard must query across schemas to aggregate data (e.g. total Tenants, active Memberships across the platform).
