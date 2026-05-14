from django.conf import settings
from django.db import models


class EventSeries(models.Model):
    """A recurring series that generates individual Event occurrences."""

    RECURRENCE_CHOICES = [
        ("weekly", "Weekly"),
        ("fortnightly", "Fortnightly"),
    ]

    title = models.CharField(max_length=255)
    recurrence_pattern = models.CharField(max_length=15, choices=RECURRENCE_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_series",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "event series"

    def __str__(self):
        return self.title


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
    series = models.ForeignKey(
        EventSeries,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="occurrences",
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

    @property
    def spots_remaining(self):
        if self.capacity is None:
            return None
        return max(0, self.capacity - self.registrations.count())

    @property
    def is_full(self):
        if self.capacity is None:
            return False
        return self.registrations.count() >= self.capacity


class EventRegistration(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_registrations",
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("event", "user")]
        ordering = ["-registered_at"]

    def __str__(self):
        return f"{self.user} → {self.event}"
