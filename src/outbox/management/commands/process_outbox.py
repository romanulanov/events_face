import json
import logging
import time

from django.core.management.base import BaseCommand
from django.db import transaction

from outbox.models import OutboxMessage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send unsent messages from Outbox (Transactional Outbox pattern)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Outbox Relay..."))

        while True:
            with transaction.atomic():
                messages = (
                    OutboxMessage.objects
                    .filter(sent=False)
                    .select_for_update(skip_locked=True)
                    .order_by("created_at")[:100]
                )

                for msg in messages:
                    try:
                        print(
                            f"Sending topic={msg.topic} payload="
                            f"{json.dumps(msg.payload, ensure_ascii=False)}"
                        )

                        msg.mark_as_sent()
                    except Exception as e:
                        logger.error(f"Failed to process {msg.id}: {e}")

            time.sleep(1)
