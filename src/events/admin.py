from django.contrib import admin

from .models import Event, Venue


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "event_time", "status", "venue")
    list_filter = ("status", "event_time", "venue")
    search_fields = ("name",)
    raw_id_fields = ("venue",)
    ordering = ("-event_time",)
