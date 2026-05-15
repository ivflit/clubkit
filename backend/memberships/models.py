import datetime
from datetime import timedelta

from django.conf import settings
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
    stripe_price_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Membership(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("lapsed", "Lapsed"),
        ("cancelled", "Cancelled"),
    ]

    VALID_TRANSITIONS = {
        "active": ["lapsed", "cancelled"],
        "lapsed": ["active", "cancelled"],
        "cancelled": [],
    }

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    membership_type = models.ForeignKey(
        MembershipType,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.owner} — {self.membership_type.name} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self._calculate_end_date()
        super().save(*args, **kwargs)

    def _calculate_end_date(self):
        start = self.start_date
        if self.membership_type.billing_frequency == "monthly":
            return start + timedelta(days=30)
        return start + timedelta(days=365)

    def transition_to(self, new_status):
        allowed = self.VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{self.status}' to '{new_status}'."
            )
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])
