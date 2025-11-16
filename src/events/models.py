import uuid

from django.core.validators import EmailValidator, MaxLengthValidator
from django.db import models


class Venue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Площадка"
        verbose_name_plural = "Площадки"

    def __str__(self):
        return self.name


class Event(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "open"
        CLOSED = "closed", "closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(verbose_name="название", max_length=255)
    event_time = models.DateTimeField(verbose_name="дата проведения \
                                      мероприятия")
    status = models.CharField(
        verbose_name="статус",
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN
    )
    venue = models.ForeignKey(
        Venue,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ["event_time"]

    def __str__(self):
        return f"{self.name} @ {self.event_time.isoformat()}"


class EventRegistration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations"
    )
    full_name = models.CharField(
        max_length=128,
        validators=[MaxLengthValidator(128)]
    )
    email = models.EmailField(validators=[EmailValidator()])
    confirmation_code = models.CharField(max_length=12)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("event", "email")
