import datetime

from django.utils import timezone
from rest_framework import serializers

from .models import Event, EventRegistration, EventSeries


class EventSeriesSerializer(serializers.ModelSerializer):
    occurrence_count = serializers.SerializerMethodField()

    class Meta:
        model = EventSeries
        fields = ["id", "title", "recurrence_pattern", "created_at", "occurrence_count"]
        read_only_fields = ["id", "created_at"]

    def get_occurrence_count(self, obj):
        return obj.occurrences.count()


class EventSeriesCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    location = serializers.CharField(required=False, default="", allow_blank=True)
    visibility = serializers.ChoiceField(
        choices=["public", "members_only"], default="public"
    )
    capacity = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    recurrence_pattern = serializers.ChoiceField(choices=["weekly", "fortnightly"])
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    time = serializers.TimeField()

    def validate(self, data):
        if data["end_date"] < data["start_date"]:
            raise serializers.ValidationError(
                {"end_date": "end_date must be on or after start_date."}
            )
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        series = EventSeries.objects.create(
            title=validated_data["title"],
            recurrence_pattern=validated_data["recurrence_pattern"],
            created_by=user,
        )

        step = datetime.timedelta(
            days=7 if validated_data["recurrence_pattern"] == "weekly" else 14
        )
        current_date = validated_data["start_date"]
        end_date = validated_data["end_date"]
        event_time = validated_data["time"]

        events = []
        while current_date <= end_date:
            naive_dt = datetime.datetime.combine(current_date, event_time)
            aware_dt = timezone.make_aware(naive_dt)
            events.append(
                Event(
                    title=validated_data["title"],
                    description=validated_data.get("description", ""),
                    date_time=aware_dt,
                    location=validated_data.get("location", ""),
                    visibility=validated_data.get("visibility", "public"),
                    capacity=validated_data.get("capacity"),
                    status="upcoming",
                    created_by=user,
                    series=series,
                )
            )
            current_date += step

        Event.objects.bulk_create(events)
        return series


class EventSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(
        source="created_by.email", read_only=True
    )
    registration_count = serializers.SerializerMethodField()
    series_id = serializers.IntegerField(source="series.id", read_only=True, allow_null=True)
    series_title = serializers.CharField(source="series.title", read_only=True, allow_null=True)

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
            "series_id",
            "series_title",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
            "registration_count",
        ]
        read_only_fields = ["id", "created_by", "created_by_email", "series_id", "series_title", "created_at", "updated_at"]

    def get_registration_count(self, obj):
        return obj.registrations.count()


class PublicEventSerializer(serializers.ModelSerializer):
    spots_remaining = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()
    registration_count = serializers.SerializerMethodField()
    series_id = serializers.IntegerField(source="series.id", read_only=True, allow_null=True)
    series_title = serializers.CharField(source="series.title", read_only=True, allow_null=True)

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
            "series_id",
            "series_title",
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
