from rest_framework import serializers

from .models import Membership, MembershipType


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


class MembershipSerializer(serializers.ModelSerializer):
    membership_type_name = serializers.CharField(
        source="membership_type.name", read_only=True
    )
    owner_email = serializers.CharField(source="owner.email", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id",
            "owner",
            "owner_email",
            "membership_type",
            "membership_type_name",
            "status",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "status",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        ]


class MembershipPurchaseSerializer(serializers.Serializer):
    membership_type_id = serializers.IntegerField()

    def validate_membership_type_id(self, value):
        try:
            mt = MembershipType.objects.get(pk=value, is_active=True)
        except MembershipType.DoesNotExist:
            raise serializers.ValidationError(
                "Membership Type not found or is inactive."
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        membership_type = MembershipType.objects.get(
            pk=validated_data["membership_type_id"]
        )
        return Membership.objects.create(
            owner=user,
            membership_type=membership_type,
        )
