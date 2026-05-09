from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MembershipType",
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
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "price",
                    models.DecimalField(decimal_places=2, max_digits=8),
                ),
                (
                    "billing_frequency",
                    models.CharField(
                        choices=[("monthly", "Monthly"), ("annual", "Annual")],
                        max_length=10,
                    ),
                ),
                (
                    "renewal_mode",
                    models.CharField(
                        choices=[
                            ("rolling", "Rolling (auto-renew)"),
                            ("one_off", "One-off (expires)"),
                        ],
                        max_length=10,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
