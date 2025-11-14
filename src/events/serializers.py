from rest_framework import serializers
from .models import Event, EventRegistration


class EventSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source="venue.name", read_only=True)

    class Meta:
        model = Event
        fields = ("id", "name", "event_time", "status", "venue", "venue_name")


class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = ["full_name", "email"]

    def validate(self, attrs):
        event = self.context["event"]

        if event.status != "open":
            raise serializers.ValidationError("Registration is closed for this event.")

        if EventRegistration.objects.filter(event=event, email=attrs["email"]).exists():
            raise serializers.ValidationError("This email is already registered for this event.")

        return attrs
