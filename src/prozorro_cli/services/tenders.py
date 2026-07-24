from __future__ import annotations

from typing import Any
from urllib.parse import quote

from prozorro_cli.client import fetch_json
from prozorro_cli.services.references import (
    PUBLIC_API_URL,
    resolve_guid,
    resolve_tender_id,
)


TENDER_PAGE_URL = "https://prozorro.gov.ua/tender/{tender_id}"


def tender_link(reference: str, *, timeout: float = 30.0) -> str:
    tender_id = resolve_tender_id(reference, timeout=timeout)
    return TENDER_PAGE_URL.format(tender_id=quote(tender_id, safe=""))


def public_api_link(reference: str, *, timeout: float = 30.0) -> str:
    guid = resolve_guid(reference, timeout=timeout)
    return PUBLIC_API_URL.format(guid=guid)


def fetch_tender(reference: str, *, timeout: float = 30.0) -> dict[str, Any]:
    guid = resolve_guid(reference, timeout=timeout)
    url = PUBLIC_API_URL.format(guid=guid)
    return fetch_json(url, timeout=timeout)
