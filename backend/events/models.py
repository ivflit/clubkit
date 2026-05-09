from django.conf import settings
from django.db import models


class Event(models.Model):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("members_only", "Members Only"),
    ]

    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("past", "Past"),
        ("cancelled", "Cancelled"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    date_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, default="")
    visibility = models.CharField(
        max_length=20, choices=VISIBILITY_CHOICES, default="public"
    )
    capacity = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="upcoming"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date_time"]

    def __str__(self):
        return self.title
