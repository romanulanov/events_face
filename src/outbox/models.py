import uuid
from django.db import models
from django.utils import timezone


class OutboxMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.CharField(max_length=255)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["sent", "created_at"]),
        ]

    def mark_as_sent(self):
        self.sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=["sent", "sent_at"])
