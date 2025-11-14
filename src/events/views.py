from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event
from .serializers import EventSerializer
from django.db import transaction
from outbox.models import OutboxMessage
import uuid


@transaction.atomic
def create_event(request):
    event = Event.objects.create(
        name=request.data["name"],
        event_time=request.data["event_time"],
        status="open",
        venue=request.data.get("venue"),
    )

    message_id = uuid.uuid4()
    OutboxMessage.objects.create(
        id=message_id,
        topic="event_created",
        payload={
            "message_id": str(message_id),
            "event_id": str(event.id),
            "name": event.name,
            "time": event.event_time.isoformat(),
        },
    )

    return Response({"status": "created", "event_id": event.id})


class EventListAPIView(generics.ListAPIView):
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["event_time"]
    ordering = ["event_time"]

    def get_queryset(self):
        qs = Event.objects.filter(status=Event.Status.OPEN).select_related("venue")
        return qs
