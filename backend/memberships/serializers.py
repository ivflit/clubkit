from rest_framework import serializers

from .models import MembershipType


class MembershipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipType
        fields = [
            "id",
            "name",
            "description",
            "price",
            "billing_frequency",
            "renewal_mode",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PublicMembershipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipType
        fields = ["id", "name", "description", "price", "billing_frequency", "renewal_mode"]
