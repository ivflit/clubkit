import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = "django-insecure-dev-only-change-in-production"

DEBUG = True

ALLOWED_HOSTS = [".localhost", ".lvh.me", "127.0.0.1"]

# --- Multi-tenancy (django-tenants) ---

TENANT_MODEL = "tenancy.Tenant"
TENANT_DOMAIN_MODEL = "tenancy.TenantDomain"

SHARED_APPS = [
    "django_tenants",
    "tenancy",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
]

TENANT_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "users",
    "memberships",
    "events",
    "payments",
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
] + [
    "rest_framework",
    "rest_framework_simplejwt",
    "notifications.apps.NotificationsConfig",
]

# --- Database ---

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": "clubkit",
        "USER": "ivan",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# --- Middleware ---

MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- URL config ---

ROOT_URLCONF = "clubkit.urls"
PUBLIC_SCHEMA_URLCONF = "clubkit.urls_public"

# --- Templates ---

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
]

WSGI_APPLICATION = "clubkit.wsgi.application"

# --- Auth ---

AUTH_USER_MODEL = "users.CustomUser"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- DRF ---

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# --- SimpleJWT ---

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- i18n ---

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static files ---

STATIC_URL = "static/"

# --- Media files (uploads) ---

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Email ---

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@clubkit.com"

# Set to False in tests to send emails synchronously (avoids thread/outbox race condition).
NOTIFICATIONS_SEND_ASYNC = True

# --- Stripe ---

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_CONNECT_RETURN_URL = os.environ.get("STRIPE_CONNECT_RETURN_URL", "http://localhost:3000/admin/stripe/return")
STRIPE_CONNECT_REFRESH_URL = os.environ.get("STRIPE_CONNECT_REFRESH_URL", "http://localhost:3000/admin/stripe/refresh")

# Platform plan limits
PLAN_LIMITS = {
    "free": {"max_members": 50},
    "pro": {"max_members": None},  # unlimited
}

# --- Misc ---

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
