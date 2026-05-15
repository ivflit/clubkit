"""
Seed script — creates a demo club with realistic data so you can explore ClubKit locally.

Usage:
    cd backend
    source venv/bin/activate
    python seed.py

What it creates:
    Tenant:           demo-club.lvh.me
    Admin user:       admin@demo.com / Admin123!
    Member users:     alice@demo.com, bob@demo.com, carol@demo.com  (password: Member123!)
    Membership Types: Adult Annual (£120), Junior Monthly (£15), Family Annual (£200)
    Memberships:      alice and bob have active Adult Annual memberships
    Events:           3 upcoming public + 1 members-only, 1 past
    Registrations:    alice registered for 2 upcoming events
"""
import os
import sys
import django

# Bootstrap Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clubkit.settings.base")
django.setup()

from django.db import connection
from django_tenants.utils import tenant_context
from tenancy.models import Tenant, TenantDomain, BrandKit

# ── helpers ────────────────────────────────────────────────────────────────

def info(msg):
    print(f"  ✓ {msg}")

def section(msg):
    print(f"\n{msg}")
    print("─" * len(msg))

# ── 1. Tenant ───────────────────────────────────────────────────────────────

section("1. Creating Tenant")
connection.set_schema_to_public()

tenant, created = Tenant.objects.get_or_create(
    slug="demo-club",
    defaults={"name": "Riverside FC", "schema_name": "demo_club"},
)
if created:
    info("Created tenant: Riverside FC (demo-club.lvh.me)")
else:
    info("Tenant already exists — skipping creation")

TenantDomain.objects.get_or_create(
    domain="demo-club.lvh.me",
    defaults={"tenant": tenant, "is_primary": True},
)
info("Domain: demo-club.lvh.me")

# ── 2. Brand Kit ────────────────────────────────────────────────────────────

section("2. Brand Kit")
brand_kit, _ = BrandKit.objects.get_or_create(tenant=tenant)
brand_kit.primary_colour = "#1a3c5e"
brand_kit.accent_colour  = "#e87722"
brand_kit.description    = "Riverside FC is a friendly community football club welcoming players of all ages and abilities."
brand_kit.contact_email  = "hello@riversidefc.example.com"
brand_kit.contact_phone  = "+44 7700 900123"
brand_kit.contact_address = "Riverside Park, 12 River Lane, Bristol, BS1 4AA"
brand_kit.save()
info("Brand Kit: primary=#1a3c5e accent=#e87722")

# ── 3. Users ────────────────────────────────────────────────────────────────

section("3. Users (inside tenant schema)")
with tenant_context(tenant):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    admin, _ = User.objects.get_or_create(
        email="admin@demo.com",
        defaults={"username": "admin@demo.com", "first_name": "Alex", "last_name": "Admin", "role": "admin"},
    )
    admin.set_password("Admin123!")
    admin.save()
    info("Admin:  admin@demo.com / Admin123!")

    alice, _ = User.objects.get_or_create(
        email="alice@demo.com",
        defaults={"username": "alice@demo.com", "first_name": "Alice", "last_name": "Johnson", "role": "member"},
    )
    alice.set_password("Member123!")
    alice.save()
    info("Member: alice@demo.com / Member123!")

    bob, _ = User.objects.get_or_create(
        email="bob@demo.com",
        defaults={"username": "bob@demo.com", "first_name": "Bob", "last_name": "Smith", "role": "member"},
    )
    bob.set_password("Member123!")
    bob.save()
    info("Member: bob@demo.com / Member123!")

    carol, _ = User.objects.get_or_create(
        email="carol@demo.com",
        defaults={"username": "carol@demo.com", "first_name": "Carol", "last_name": "Williams", "role": "member"},
    )
    carol.set_password("Member123!")
    carol.save()
    info("Member: carol@demo.com / Member123! (no membership — guest)")

# ── 4. Membership Types ──────────────────────────────────────────────────────

section("4. Membership Types")
with tenant_context(tenant):
    from memberships.models import MembershipType

    adult, _ = MembershipType.objects.get_or_create(
        name="Adult Annual",
        defaults={"description": "Full adult membership for the season.", "price": "120.00",
                  "billing_frequency": "annual", "renewal_mode": "rolling", "is_active": True},
    )
    info("Adult Annual — £120/year (rolling)")

    junior, _ = MembershipType.objects.get_or_create(
        name="Junior Monthly",
        defaults={"description": "Monthly membership for under-18s.", "price": "15.00",
                  "billing_frequency": "monthly", "renewal_mode": "rolling", "is_active": True},
    )
    info("Junior Monthly — £15/month (rolling)")

    family, _ = MembershipType.objects.get_or_create(
        name="Family Annual",
        defaults={"description": "Covers up to 2 adults and 3 children.", "price": "200.00",
                  "billing_frequency": "annual", "renewal_mode": "one_off", "is_active": True},
    )
    info("Family Annual — £200/year (one-off)")

# ── 5. Memberships ───────────────────────────────────────────────────────────

section("5. Memberships")
with tenant_context(tenant):
    from memberships.models import Membership

    m1, _ = Membership.objects.get_or_create(
        owner=alice, membership_type=adult,
        defaults={"status": "active"},
    )
    info(f"Alice → Adult Annual (active, expires {m1.end_date})")

    m2, _ = Membership.objects.get_or_create(
        owner=bob, membership_type=adult,
        defaults={"status": "active"},
    )
    info(f"Bob   → Adult Annual (active, expires {m2.end_date})")

# ── 6. Events ────────────────────────────────────────────────────────────────

section("6. Events")
with tenant_context(tenant):
    from events.models import Event
    import datetime, pytz

    tz = pytz.UTC
    today = datetime.datetime.now(tz)

    e1, _ = Event.objects.get_or_create(
        title="Summer Tournament 2026",
        defaults={
            "description": "<p>Our biggest event of the year! Open to all members and guests. BBQ and refreshments provided.</p>",
            "date_time": today + datetime.timedelta(days=14),
            "location": "Riverside Park Main Pitch",
            "visibility": "public",
            "capacity": 60,
            "status": "upcoming",
        },
    )
    info(f"Public:        Summer Tournament 2026 (in 14 days, capacity 60)")

    e2, _ = Event.objects.get_or_create(
        title="Weekly Training — Adults",
        defaults={
            "description": "<p>Regular Tuesday evening training session for adult members. All abilities welcome.</p>",
            "date_time": today + datetime.timedelta(days=7),
            "location": "Riverside Park Training Ground",
            "visibility": "public",
            "capacity": 30,
            "status": "upcoming",
        },
    )
    info(f"Public:        Weekly Training — Adults (in 7 days, capacity 30)")

    e3, _ = Event.objects.get_or_create(
        title="Club AGM",
        defaults={
            "description": "<p>Annual General Meeting. All members are encouraged to attend. Votes on committee and next season plans.</p>",
            "date_time": today + datetime.timedelta(days=21),
            "location": "Riverside FC Clubhouse",
            "visibility": "public",
            "capacity": None,
            "status": "upcoming",
        },
    )
    info(f"Public:        Club AGM (in 21 days, no capacity limit)")

    e4, _ = Event.objects.get_or_create(
        title="Members-Only Social Night",
        defaults={
            "description": "<p>An exclusive social evening for members. Food, drinks and prizes!</p>",
            "date_time": today + datetime.timedelta(days=10),
            "location": "The Riverside Arms, Bristol",
            "visibility": "members_only",
            "capacity": 40,
            "status": "upcoming",
        },
    )
    info(f"Members-only:  Members-Only Social Night (in 10 days)")

    e5, _ = Event.objects.get_or_create(
        title="Pre-Season Kickabout",
        defaults={
            "description": "<p>Friendly pre-season match — everyone welcome.</p>",
            "date_time": today - datetime.timedelta(days=30),
            "location": "Riverside Park Main Pitch",
            "visibility": "public",
            "capacity": 50,
            "status": "past",
        },
    )
    info(f"Past:          Pre-Season Kickabout (30 days ago)")

# ── 7. Event Registrations ───────────────────────────────────────────────────

section("7. Event Registrations")
with tenant_context(tenant):
    from events.models import EventRegistration

    r1, _ = EventRegistration.objects.get_or_create(user=alice, event=e1)
    info("Alice → Summer Tournament 2026")

    r2, _ = EventRegistration.objects.get_or_create(user=alice, event=e2)
    info("Alice → Weekly Training — Adults")

    r3, _ = EventRegistration.objects.get_or_create(user=bob, event=e1)
    info("Bob   → Summer Tournament 2026")

# ── Done ─────────────────────────────────────────────────────────────────────

print("\n" + "═" * 50)
print("  Seed complete!")
print("═" * 50)
print("""
Backend:   cd backend && source venv/bin/activate && python manage.py runserver
Frontend:  cd frontend && npm run dev

Then visit:
  Public site:      http://demo-club.lvh.me:3000/
  Login:            http://demo-club.lvh.me:3000/login
  Admin panel:      http://demo-club.lvh.me:3000/admin/membership-types
  Platform admin:   http://localhost:3000/platform-admin/login
  Join page:        http://demo-club.lvh.me:3000/join
  Events:           http://demo-club.lvh.me:3000/events

Accounts:
  Admin:   admin@demo.com  /  Admin123!
  Member:  alice@demo.com  /  Member123!  (has active membership)
  Member:  bob@demo.com    /  Member123!  (has active membership)
  Guest:   carol@demo.com  /  Member123!  (no membership)

API (backend on port 8000):
  http://demo-club.lvh.me:8000/api/health/
""")
