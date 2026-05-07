## Project structure

- `backend/` — Django + DRF (Python). Virtual env at `backend/venv/`.
- `frontend/` — Next.js + React + Tailwind CSS (TypeScript).
- `CONTEXT.md` — Domain glossary.
- `docs/adr/` — Architectural decision records.
- `docs/agents/` — Agent skill config.

## Development setup

### Backend
```bash
cd backend
source venv/bin/activate
python manage.py migrate_schemas   # NOT 'migrate' — this runs across all Tenant schemas
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Database
- PostgreSQL database: `clubkit`
- Multi-tenant via `django-tenants`: separate schema per Tenant (ADR-0001, ADR-0003)
- Public schema: Tenant registry. Per-Tenant schema: Users, Memberships, Events, etc.
- Use `migrate_schemas` (not `migrate`) to apply migrations across all schemas.

### Local subdomain routing
Use `*.lvh.me` which resolves to `127.0.0.1`. Example: `test-club.lvh.me:8000`.

### Testing
```bash
cd backend
source venv/bin/activate
python manage.py test
```

## Conventions

- `AUTH_USER_MODEL = "users.CustomUser"` — always use CustomUser, never Django's default User.
- Tenant models go in `TENANT_APPS`. Platform-wide models go in `SHARED_APPS`.
- Django's built-in admin is NOT used. All admin UIs are in the Next.js frontend.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues (via `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
