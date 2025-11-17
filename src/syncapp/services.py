import logging
import time
from typing import Iterable, Optional

import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = getattr(settings, "EVENTS_PROVIDER_TIMEOUT", 10)
MAX_RETRIES = getattr(settings, "EVENTS_PROVIDER_MAX_RETRIES", 3)
BASE_URL = getattr(
    settings,
    "EVENTS_PROVIDER_API",
    "https://events.k3scluster.tech/api/events/"
    )


def _get_with_retries(url: str, params: dict = None) -> requests.Response:
    session = requests.Session()
    attempt = 0
    while True:
        try:
            attempt += 1
            resp = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            if attempt >= MAX_RETRIES:
                logger.exception(
                    "Failed to fetch %s after %d attempts",
                    url,
                    attempt
                )
                raise
            backoff = 2 ** (attempt - 1)
            logger.warning(
                "Request to %s failed (attempt %d). Backoff %ds. Error: %s",
                url,
                attempt,
                backoff,
                exc
            )
            time.sleep(backoff)


def _iter_events_from_provider(
        start_url: str,
        params: Optional[dict] = None
     ) -> Iterable[dict]:
    url = start_url
    local_params = dict(params or {})
    while url:
        resp = _get_with_retries(url, params=local_params)
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            for item in data.get("results", []):
                yield item
            url = data.get("next")
            local_params = None
        elif isinstance(data, list):
            for item in data:
                yield item
            url = None
        else:
            found = False
            for v in data.values() if isinstance(data, dict) else []:
                if isinstance(v, list):
                    for item in v:
                        yield item
                    found = True
                    break
            if found:
                url = None
            else:
                raise ValueError(
                    "Unknown payload format from provider: expected list or "
                    "{'results': [...]}."
                )


def _parse_event_payload(payload: dict) -> dict:
    item = {}
    item["id"] = payload.get("id")
    item["name"] = payload.get("name") or payload.get("title") or ""
    ev_time_raw = (
        payload.get("event_time")
        or payload.get("date")
        or payload.get("start")
    )
    if ev_time_raw:
        item["event_time"] = parse_datetime(ev_time_raw)
    else:
        item["event_time"] = None
    item["status"] = payload.get("status", "open")
    venue = payload.get("venue")
    if isinstance(venue, dict):
        item["venue"] = {"id": venue.get("id"), "name": venue.get("name")}
    elif isinstance(venue, str):
        item["venue"] = {"id": None, "name": venue}
    else:
        item["venue"] = None
    item["_raw"] = payload
    return item
