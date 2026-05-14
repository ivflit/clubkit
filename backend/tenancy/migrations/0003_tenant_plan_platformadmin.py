# Generated manually for issue #16: Platform Admin dashboard

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenancy", "0002_brandkit_alter_tenant_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="plan",
            field=models.CharField(
                choices=[("free", "Free"), ("pro", "Pro")],
                default="free",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="PlatformAdmin",
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
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password", models.CharField(max_length=128)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "app_label": "tenancy",
            },
        ),
    ]
