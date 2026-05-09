from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")

    def __str__(self):
        return self.email or self.username

    @property
    def is_tenant_admin(self):
        return self.role == "admin"

    @property
    def has_active_membership(self):
        return self.memberships.filter(status="active").exists()
