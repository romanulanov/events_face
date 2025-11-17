import uuid

import requests
from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from outbox.models import OutboxMessage

from .models import Event, EventRegistration
from .serializers import EventRegistrationSerializer, EventSerializer

NOTIFICATIONS_API_URL = (
    "https://notifications.k3scluster.tech/api/notifications"
    )
OWNER_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa7"


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
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    search_fields = ["name"]
    ordering_fields = ["event_time"]
    ordering = ["event_time"]

    def get_queryset(self):
        qs = (
            Event.objects
            .filter(status=Event.Status.OPEN)
            .select_related("venue")
        )
        return qs


class EventRegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        serializer = EventRegistrationSerializer(
            data=request.data, context={"event": event}
        )
        serializer.is_valid(raise_exception=True)

        full_name = serializer.validated_data["full_name"]
        email = serializer.validated_data["email"]

        if EventRegistration.objects.filter(event=event, email=email).exists():
            return Response(
                {"error": "This email is already registered for this event."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        confirmation_code = uuid.uuid4().hex[:6].upper()

        payload = {
            "owner_id": OWNER_ID,
            "email": email,
            "subject": f"Регистрация на мероприятие: {event.name}",
            "message": (
                f"Здравствуйте, {full_name}!\n\nВаш код подтверждения: "
                f"{confirmation_code}\n\nСпасибо за регистрацию!"
            ),
        }
        try:
            resp = requests.post(NOTIFICATIONS_API_URL, json=payload)
            if resp.status_code != 200:
                return Response(
                    {"error": "Failed to send confirmation email."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
        except requests.RequestException:
            return Response(
                {"error": "Failed to connect to notification service."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {"message": "Registration successful, confirmation code sent."},
            status=status.HTTP_201_CREATED,
        )
