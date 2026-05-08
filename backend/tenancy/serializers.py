from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from tenancy.models import BrandKit, Tenant, TenantDomain, validate_subdomain_slug


class BrandKitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandKit
        fields = [
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
    """Accepts Tenant + Brand Kit fields and creates both."""

    # Tenant fields
    club_name = serializers.CharField(max_length=255)
    subdomain = serializers.SlugField(max_length=63)

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
        brand_kit = BrandKit.objects.create(tenant=tenant, **brand_kit_fields)

        return tenant


class TenantDetailSerializer(serializers.ModelSerializer):
    brand_kit = BrandKitSerializer(read_only=True)

    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "status", "created_at", "brand_kit"]
        read_only_fields = fields
