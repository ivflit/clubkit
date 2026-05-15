import re

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


def validate_subdomain_slug(value):
    """Validate that slug is URL-safe for subdomain use."""
    if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", value):
        raise ValidationError(
            "Slug must contain only lowercase letters, numbers, and hyphens. "
            "It cannot start or end with a hyphen."
        )
    reserved = {"www", "api", "admin", "mail", "ftp", "public", "static", "media"}
    if value in reserved:
        raise ValidationError(f"'{value}' is a reserved subdomain and cannot be used.")


class Tenant(TenantMixin):
    PLAN_CHOICES = [
        ("free", "Free"),
        ("pro", "Pro"),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=63, unique=True, validators=[validate_subdomain_slug]
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("suspended", "Suspended"),
        ],
        default="active",
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="free")
    stripe_account_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    auto_create_schema = True
    auto_drop_schema = True

    def __str__(self):
        return self.name


class TenantDomain(DomainMixin):
    pass


class BrandKit(models.Model):
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="brand_kit"
    )
    logo = models.FileField(upload_to="brand_kits/logos/", blank=True, default="")
    primary_colour = models.CharField(max_length=7, default="#1a73e8")
    accent_colour = models.CharField(max_length=7, default="#ff6d00")
    hero_image = models.FileField(
        upload_to="brand_kits/heroes/", blank=True, default=""
    )
    description = models.TextField(blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=30, blank=True, default="")
    contact_address = models.TextField(blank=True, default="")
    social_facebook = models.URLField(blank=True, default="")
    social_twitter = models.URLField(blank=True, default="")
    social_instagram = models.URLField(blank=True, default="")

    def __str__(self):
        return f"BrandKit for {self.tenant.name}"


class PlatformAdmin(models.Model):
    """Super-admin account scoped to the public schema, not any Tenant."""

    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "tenancy"

    def __str__(self):
        return self.email

    def set_password(self, raw_password: str) -> None:
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)
