from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


SUMMARY_URL = "https://prozorro.gov.ua/api/tenders/{tender_id}/summary"
PUBLIC_API_URL = "https://public-api.prozorro.gov.ua/api/2.5/tenders/{guid}"
TENDER_PAGE_URL = "https://prozorro.gov.ua/tender/{tender_id}"

TENDER_ID_PATTERN = re.compile(r"^UA-\d{4}-\d{2}-\d{2}-\d{6}-[a-z]$")
GUID_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")


class ProzorroError(RuntimeError):
    """A user-facing error returned by Prozorro or the network."""


def validate_tender_id(tender_id: str) -> str:
    if not TENDER_ID_PATTERN.fullmatch(tender_id):
        raise ProzorroError(
            "Некоректний номер тендера. Очікується формат "
            "UA-YYYY-MM-DD-NNNNNN-x."
        )
    return tender_id


def tender_link(tender_id: str) -> str:
    validate_tender_id(tender_id)
    return TENDER_PAGE_URL.format(tender_id=quote(tender_id, safe=""))


def fetch_json(url: str, *, timeout: float = 30.0) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Language": "uk",
            "User-Agent": "prozorro-cli/0.1 (+https://prozorro.gov.ua)",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as error:
        if error.code == 404:
            raise ProzorroError("Тендер не знайдено.") from error
        raise ProzorroError(f"Prozorro повернув HTTP {error.code}.") from error
    except URLError as error:
        reason = getattr(error, "reason", error)
        raise ProzorroError(f"Не вдалося підключитися до Prozorro: {reason}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ProzorroError("Prozorro повернув некоректний JSON.") from error

    if not isinstance(payload, dict):
        raise ProzorroError("Prozorro повернув JSON неочікуваного формату.")
    return payload


def resolve_guid(tender_id: str, *, timeout: float = 30.0) -> str:
    validate_tender_id(tender_id)
    url = SUMMARY_URL.format(tender_id=quote(tender_id, safe=""))
    summary = fetch_json(url, timeout=timeout)
    guid = summary.get("id")

    if not isinstance(guid, str) or not GUID_PATTERN.fullmatch(guid):
        raise ProzorroError("У відповіді Prozorro немає коректного внутрішнього id.")
    return guid.lower()


def normal_guid(guid: str) -> str:
    if not GUID_PATTERN.fullmatch(guid):
        raise ProzorroError("Некоректний внутрішній id Prozorro.")
    normalized = guid.lower()
    return (
        f"{normalized[0:8]}-{normalized[8:12]}-{normalized[12:16]}-"
        f"{normalized[16:20]}-{normalized[20:32]}"
    )


def fetch_tender(tender_id: str, *, timeout: float = 30.0) -> dict[str, Any]:
    guid = resolve_guid(tender_id, timeout=timeout)
    url = PUBLIC_API_URL.format(guid=guid)
    return fetch_json(url, timeout=timeout)
