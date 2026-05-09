from rest_framework import serializers

from .models import Event, EventRegistration


class EventSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(
        source="created_by.email", read_only=True
    )
    registration_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "date_time",
            "location",
            "visibility",
            "capacity",
            "status",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
            "registration_count",
        ]
        read_only_fields = ["id", "created_by", "created_by_email", "created_at", "updated_at"]

    def get_registration_count(self, obj):
        return obj.registrations.count()


class PublicEventSerializer(serializers.ModelSerializer):
    spots_remaining = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()
    registration_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "date_time",
            "location",
            "visibility",
            "capacity",
            "status",
            "spots_remaining",
            "is_registered",
            "registration_count",
        ]

    def get_spots_remaining(self, obj):
        return obj.spots_remaining

    def get_is_registered(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.registrations.filter(user=request.user).exists()

    def get_registration_count(self, obj):
        return obj.registrations.count()


class EventRegistrationSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    event_date_time = serializers.DateTimeField(source="event.date_time", read_only=True)
    event_location = serializers.CharField(source="event.location", read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            "id",
            "event",
            "user",
            "user_email",
            "user_first_name",
            "user_last_name",
            "event_title",
            "event_date_time",
            "event_location",
            "registered_at",
        ]
        read_only_fields = ["id", "user", "registered_at"]
