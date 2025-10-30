from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event
from .serializers import EventSerializer

class EventListAPIView(generics.ListAPIView):
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["event_time"]
    ordering = ["event_time"]

    def get_queryset(self):
        qs = Event.objects.filter(status=Event.Status.OPEN).select_related("venue")
        return qs
