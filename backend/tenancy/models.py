from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Tenant(TenantMixin):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=63, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("suspended", "Suspended"),
        ],
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    auto_create_schema = True
    auto_drop_schema = True

    def __str__(self):
        return self.name


class TenantDomain(DomainMixin):
    pass
