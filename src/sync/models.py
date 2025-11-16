from django.db import models


class SyncResult(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    full_sync = models.BooleanField(default=False)
    changed_from = models.DateTimeField(null=True, blank=True)
    changed_to = models.DateTimeField(null=True, blank=True)
    added = models.IntegerField(default=0)
    updated = models.IntegerField(default=0)
    raw_response_summary = models.TextField(blank=True)

    class Meta:
        ordering = ("-started_at",)

    def __str__(self):
        return (
            f"Sync {self.started_at.isoformat()} "
            f"added={self.added} updated={self.updated} full={self.full_sync}"
        )
