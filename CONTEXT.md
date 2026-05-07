# Context: Multi-tenant Sports Club Platform

## Glossary

### Platform

The system as a whole. Managed by one or more Platform Admins (super-admins) who have visibility across all Tenants. The Platform Admin dashboard provides: Tenant listing/monitoring, support escalation, and platform-level billing oversight. Platform Admin is a separate role from Tenant Admin — a Platform Admin operates above the Tenant boundary.

### Platform Billing

How the platform monetises. Tiered plans: a free tier with limits (e.g. member cap) for onboarding and proving value, and paid tiers that unlock higher limits or premium features (e.g. custom domains). Tenants pay a predictable monthly fee — no percentage cut on membership payments. Platform billing is managed separately from Tenant-level membership payments (both via Stripe, but distinct).

### Brand Kit

The set of visual and content customisations an Admin configures for their Tenant. Applied to a fixed themed template — clubs cannot change layout or structure, only their branding within it. Fields: **logo** (uploaded image), **primary colour** (buttons, links, header), **accent colour** (highlights, hover states), **hero image** (homepage banner), **club description** (About section text), **contact info** (address, email, phone, social media links). Configured during Onboarding and editable later.

### Tenant Routing

How the platform resolves which Tenant a request belongs to. The default is **subdomain-based**: `riverside-fc.clubplatform.com` — a wildcard DNS entry routes all subdomains to the platform, and middleware extracts the subdomain to resolve the Tenant. Custom domains (e.g. `www.riversidefc.co.uk`) are a future premium feature, not in scope for v1.

### Tenant Schema

A dedicated database schema provisioned for each Tenant within a shared database. All Tenant-specific tables (Users, Memberships, Events, etc.) live inside the Tenant's schema, providing data isolation at the database level. Schema creation is automated as part of Onboarding. Database migrations run across all Tenant schemas automatically.

### Onboarding

The self-service flow by which a new club joins the platform. A club representative signs up, creates a Tenant, and completes a setup wizard (club name, logo, brand colours, basic info). No manual intervention required from a Platform Admin — clubs go live immediately after completing the wizard.

### Tenant

A single sports club (e.g. "Riverside FC") that has signed up to the platform. Each Tenant gets its own branded space with isolated data. One club = one Tenant. Umbrella organisations or leagues are not modelled as Tenants — if a league manages multiple clubs, each club is a separate Tenant.

### User

A person with a login on the platform, scoped to a Tenant. A User has a role within the Tenant: **Admin** (can configure branding, manage events, memberships, etc.) or **non-Admin** (standard access). A User with zero active Memberships is effectively a guest — "Guest" is not a separate role, it's the absence of an active Membership.

**Member experience (v1):** Four core areas — (1) **Dashboard** showing active Memberships and upcoming registered events, (2) **Events** to browse and register for public and members-only events, (3) **My Memberships** to view status, renewal dates, manage payment method, and see Dependents' memberships, (4) **Profile** to update personal details and manage Dependents.

### Membership Type

A template defined by a Tenant's Admin that describes a category of membership the club offers (e.g. "Adult Annual", "Junior Monthly", "Social Membership"). Each Membership Type specifies: name, price, billing frequency (monthly or annual), and whether it is rolling (auto-renews) or one-off (expires at end of period). Membership Types are fully customisable per Tenant.

### Membership

An instance of a Membership Type, linking a User to a Tenant. The User is the **owner** (they manage and pay for it), but the **subject** may be a different person — typically a Dependent. A User can own multiple Memberships (e.g. one for themselves, one for each child). A Membership has a lifecycle: active, lapsed (payment missed or expired), or cancelled. Lifecycle transitions trigger Notifications.

### Tech Stack

- **Backend:** Django + Django REST Framework + PostgreSQL
- **Frontend:** Next.js + React + Tailwind CSS
- **Auth:** Django's built-in auth (custom User model), session-based for server-side, JWT/token-based for API
- **Payments:** Stripe via the Python SDK
- **Admin UI:** Custom-built admin interface (not Django's default admin) — the Platform Admin and Tenant Admin dashboards are part of the Next.js frontend, consuming Django API endpoints

### Payment

Handled via Stripe. Each Tenant connects their own Stripe account via Stripe Connect (platform mode), so club finances are separate from platform finances. Stripe manages both recurring subscriptions (rolling Memberships) and one-off payments. The platform does not store card details — Stripe handles all PCI-sensitive data.

### Notification

A message sent to a User via email (only channel for v1). Key triggers: membership approaching renewal, payment failed, membership lapsed, event reminders. Uses fixed platform-defined templates with the Tenant's Brand Kit (logo, colours) automatically applied. Admins cannot customise email copy — consistency is enforced across the platform.

### Event

Something organised by a Tenant — e.g. a training session, match, social night, or open day. Created by an Admin. An Event has a visibility: **public** (shown on the club's public site, visible to anyone) or **members-only** (visible only to logged-in Users with an active Membership). Events support optional registration with a capacity limit. Each Event has a **detail page** with a rich text content area (for describing schedules, rules, what to bring, etc.) — this serves as the Event's dedicated page on the club's site. Events are displayed in two views: a **calendar view** (monthly grid) and a **list view** (chronological). Events can be **recurring** — an Admin defines a pattern (weekly or fortnightly) with a start and end date, and the system generates individual occurrences. Each occurrence can be independently cancelled or edited after generation. Events do not have their own payment — payments are handled through Memberships only (per-event ticketing is out of scope for v1). Lifecycle transitions (e.g. event approaching, registration full) can trigger Notifications.

### Dependent

A person (typically a child) who is the subject of a Membership but does not have their own User account. All interactions are managed through the parent/guardian's User account. When a Dependent reaches adulthood, they can be promoted to a full User with their own login, and their Membership is transferred to be self-owned.
