# Generated manually for issue #2: Tenant Onboarding with Brand Kit

import django.db.models.deletion
from django.db import migrations, models

import tenancy.models


class Migration(migrations.Migration):

    dependencies = [
        ("tenancy", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tenant",
            name="slug",
            field=models.SlugField(
                max_length=63,
                unique=True,
                validators=[tenancy.models.validate_subdomain_slug],
            ),
        ),
        migrations.CreateModel(
            name="BrandKit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "logo",
                    models.FileField(
                        blank=True, default="", upload_to="brand_kits/logos/"
                    ),
                ),
                (
                    "primary_colour",
                    models.CharField(default="#1a73e8", max_length=7),
                ),
                (
                    "accent_colour",
                    models.CharField(default="#ff6d00", max_length=7),
                ),
                (
                    "hero_image",
                    models.FileField(
                        blank=True, default="", upload_to="brand_kits/heroes/"
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "contact_email",
                    models.EmailField(blank=True, default="", max_length=254),
                ),
                (
                    "contact_phone",
                    models.CharField(blank=True, default="", max_length=30),
                ),
                ("contact_address", models.TextField(blank=True, default="")),
                (
                    "social_facebook",
                    models.URLField(blank=True, default=""),
                ),
                (
                    "social_twitter",
                    models.URLField(blank=True, default=""),
                ),
                (
                    "social_instagram",
                    models.URLField(blank=True, default=""),
                ),
                (
                    "tenant",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="brand_kit",
                        to="tenancy.tenant",
                    ),
                ),
            ],
        ),
    ]
