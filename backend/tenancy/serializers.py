from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django_tenants.utils import tenant_context
from rest_framework import serializers

from tenancy.models import BrandKit, PlatformAdmin, Tenant, TenantDomain, validate_subdomain_slug


class BrandKitSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = BrandKit
        fields = [
            "club_name",
            "logo",
            "primary_colour",
            "accent_colour",
            "hero_image",
            "description",
            "contact_email",
            "contact_phone",
            "contact_address",
            "social_facebook",
            "social_twitter",
            "social_instagram",
        ]


class OnboardingSerializer(serializers.Serializer):
    """Accepts Tenant + Brand Kit + Admin User fields and creates all three."""

    # Tenant fields
    club_name = serializers.CharField(max_length=255)
    subdomain = serializers.SlugField(max_length=63)

    # Admin user fields
    admin_email = serializers.EmailField()
    admin_password = serializers.CharField(write_only=True, min_length=8)
    admin_first_name = serializers.CharField(max_length=150, required=False, default="")
    admin_last_name = serializers.CharField(max_length=150, required=False, default="")

    # Brand Kit fields (all optional for onboarding)
    logo = serializers.FileField(required=False)
    primary_colour = serializers.CharField(max_length=7, default="#1a73e8")
    accent_colour = serializers.CharField(max_length=7, default="#ff6d00")
    hero_image = serializers.FileField(required=False)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    contact_email = serializers.EmailField(required=False, default="", allow_blank=True)
    contact_phone = serializers.CharField(
        max_length=30, required=False, default="", allow_blank=True
    )
    contact_address = serializers.CharField(
        required=False, default="", allow_blank=True
    )
    social_facebook = serializers.URLField(
        required=False, default="", allow_blank=True
    )
    social_twitter = serializers.URLField(
        required=False, default="", allow_blank=True
    )
    social_instagram = serializers.URLField(
        required=False, default="", allow_blank=True
    )

    def validate_subdomain(self, value):
        value = value.lower()
        try:
            validate_subdomain_slug(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message)
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                "This subdomain is already taken."
            )
        return value

    def create(self, validated_data):
        subdomain = validated_data.pop("subdomain")
        club_name = validated_data.pop("club_name")

        # Extract admin user fields
        admin_email = validated_data.pop("admin_email")
        admin_password = validated_data.pop("admin_password")
        admin_first_name = validated_data.pop("admin_first_name", "")
        admin_last_name = validated_data.pop("admin_last_name", "")

        # Separate brand kit fields
        brand_kit_fields = {}
        for field in BrandKitSerializer.Meta.fields:
            if field in validated_data:
                brand_kit_fields[field] = validated_data.pop(field)

        # Create Tenant (auto-creates schema)
        tenant = Tenant.objects.create(
            name=club_name,
            slug=subdomain,
            schema_name=subdomain.replace("-", "_"),
        )

        # Create domain for subdomain routing
        TenantDomain.objects.create(
            domain=f"{subdomain}.lvh.me",
            tenant=tenant,
            is_primary=True,
        )

        # Create Brand Kit
        BrandKit.objects.create(tenant=tenant, **brand_kit_fields)

        # Create the first Admin user within the Tenant's schema
        User = get_user_model()
        with tenant_context(tenant):
            User.objects.create_user(
                username=admin_email,
                email=admin_email,
                password=admin_password,
                first_name=admin_first_name,
                last_name=admin_last_name,
                role="admin",
            )

        return tenant


class TenantDetailSerializer(serializers.ModelSerializer):
    brand_kit = BrandKitSerializer(read_only=True)

    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "status", "created_at", "brand_kit"]
        read_only_fields = fields


# --- Platform Admin serializers ---


class PlatformAdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TenantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "status", "plan", "created_at"]
        read_only_fields = fields


class TenantAdminDetailSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    active_memberships = serializers.IntegerField(read_only=True)
    stripe_connected = serializers.BooleanField(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "status",
            "plan",
            "created_at",
            "member_count",
            "active_memberships",
            "stripe_connected",
        ]
        read_only_fields = fields


class PlatformAdminCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if PlatformAdmin.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A Platform Admin with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        admin = PlatformAdmin(email=validated_data["email"])
        admin.set_password(validated_data["password"])
        admin.save()
        return admin
