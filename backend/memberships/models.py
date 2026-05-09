from django.db import models


class MembershipType(models.Model):
    BILLING_FREQUENCY_CHOICES = [
        ("monthly", "Monthly"),
        ("annual", "Annual"),
    ]

    RENEWAL_MODE_CHOICES = [
        ("rolling", "Rolling (auto-renew)"),
        ("one_off", "One-off (expires)"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    billing_frequency = models.CharField(
        max_length=10, choices=BILLING_FREQUENCY_CHOICES
    )
    renewal_mode = models.CharField(max_length=10, choices=RENEWAL_MODE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
