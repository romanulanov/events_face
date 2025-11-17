from django.urls import path

from .views import EventListAPIView, EventRegisterAPIView

urlpatterns = [
    path("events", EventListAPIView.as_view(), name="api-events-list"),
    path(
        "events/<uuid:event_id>/register",
        EventRegisterAPIView.as_view(),
        name="api-events-register"
    ),
]
