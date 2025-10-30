from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from ...models import SyncResult
from ...services import _iter_events_from_provider, _parse_event_payload
from events.models import Event, Venue
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Synchronize events from events-provider. Use --all for full sync or --date=YYYY-MM-DD to sync from date."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Full sync: fetch all events from provider")
        parser.add_argument("--date", type=str, help="Start changed_at date (YYYY-MM-DD or ISO) to sync from (inclusive)")
        parser.add_argument("--provider-url", type=str, help="Override provider URL for this run")

    def handle(self, *args, **options):
        full = options["all"]
        date_arg = options.get("date")
        provider_url = options.get("provider_url") or getattr(settings, "EVENTS_PROVIDER_API", None)
        if not provider_url:
            raise CommandError("EVENTS_PROVIDER_API is not configured in settings and --provider-url not provided.")

        if full:
            changed_from = None
        elif date_arg:
            try:
                changed_from = datetime.fromisoformat(date_arg)
            except Exception:
                from django.utils.dateparse import parse_datetime, parse_date
                changed_from = parse_datetime(date_arg) or (parse_date(date_arg) and datetime.combine(parse_date(date_arg), datetime.min.time()))
                if changed_from is None:
                    raise CommandError("Cannot parse date. Use YYYY-MM-DD or ISO datetime.")
        else:
            last_sync = SyncResult.objects.order_by("-finished_at").first()
            if last_sync and last_sync.changed_to:
                changed_from = last_sync.changed_to
            else:
                changed_from = None

        self.stdout.write(f"Starting sync. full={full} changed_from={changed_from} provider_url={provider_url}")

        sync = SyncResult(full_sync=full, changed_from=changed_from)
        sync.save()
        added = 0
        updated = 0
        latest_changed_to = None

        params = {}
        if changed_from:
            params["changed_at"] = changed_from.date().isoformat()

        try:
            batch_count = 0
            with transaction.atomic():
                for payload in _iter_events_from_provider(provider_url, params=params):
                    parsed = _parse_event_payload(payload)
                    possible_ts = payload.get("changed_at") or payload.get("updated_at") or payload.get("event_time")
                    if possible_ts:
                        try:
                            # prefer ISO parsing
                            from django.utils.dateparse import parse_datetime
                            parsed_ts = parse_datetime(possible_ts)
                            if parsed_ts:
                                if (latest_changed_to is None) or (parsed_ts > latest_changed_to):
                                    latest_changed_to = parsed_ts
                        except Exception:
                            pass

                    v = None
                    if parsed["venue"]:
                        v_data = parsed["venue"]
                        if v_data.get("id"):
                            try:
                                v_uuid = v_data.get("id")
                                UUID(str(v_uuid))
                                v, _ = Venue.objects.get_or_create(id=v_uuid, defaults={"name": v_data.get("name") or ""})
                                if v.name != (v_data.get("name") or ""):
                                    v.name = v_data.get("name") or ""
                                    v.save()
                            except Exception:
                                v, _ = Venue.objects.get_or_create(name=v_data.get("name") or "")
                        else:
                            v, _ = Venue.objects.get_or_create(name=v_data.get("name") or "")
                    e_kwargs = {}
                    if parsed["id"]:
                        e_kwargs["id"] = parsed["id"]
                    else:
                        if parsed["name"] and parsed["event_time"]:
                            e_kwargs["name"] = parsed["name"]
                            e_kwargs["event_time"] = parsed["event_time"]

                    if not e_kwargs:
                        logger.warning("Skipping malformed event payload: %s", payload)
                        continue

                    defaults = {
                        "name": parsed["name"],
                        "event_time": parsed["event_time"],
                        "status": parsed["status"],
                        "venue": v
                    }

                    obj, created = Event.objects.update_or_create(defaults=defaults, **e_kwargs)
                    if created:
                        added += 1
                    else:
                        changed = False
                        if obj.name != defaults["name"]:
                            obj.name = defaults["name"]; changed = True
                        if obj.event_time != defaults["event_time"]:
                            obj.event_time = defaults["event_time"]; changed = True
                        if obj.status != defaults["status"]:
                            obj.status = defaults["status"]; changed = True
                        if obj.venue_id != (v.id if v else None):
                            obj.venue = v; changed = True
                        if changed:
                            obj.save()
                            updated += 1
                    batch_count += 1

            sync.added = added
            sync.updated = updated
            sync.changed_to = latest_changed_to
            sync.finished_at = timezone.now()
            sync.raw_response_summary = f"processed_items={batch_count}"
            sync.save()
            self.stdout.write(self.style.SUCCESS(f"Sync finished: added={added} updated={updated}"))
        except Exception as exc:
            logger.exception("Sync failed")
            sync.raw_response_summary = f"failed: {str(exc)}"
            sync.finished_at = timezone.now()
            sync.save()
            raise CommandError(f"Sync failed: {exc}")
