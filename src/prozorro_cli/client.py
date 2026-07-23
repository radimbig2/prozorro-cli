from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen


SUMMARY_URL = "https://prozorro.gov.ua/api/tenders/{tender_id}/summary"
PUBLIC_API_URL = "https://public-api.prozorro.gov.ua/api/2.5/tenders/{guid}"
TENDER_PAGE_URL = "https://prozorro.gov.ua/tender/{tender_id}"

TENDER_ID_PATTERN = re.compile(r"^UA-\d{4}-\d{2}-\d{2}-\d{6}-[a-z]$")
GUID_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")
NORMAL_GUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
SUPPORTED_HOSTS = {
    "prozorro.gov.ua",
    "www.prozorro.gov.ua",
    "public-api.prozorro.gov.ua",
}
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED_FILENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class ProzorroError(RuntimeError):
    """A user-facing error returned by Prozorro or the network."""


@dataclass(frozen=True)
class TenderReference:
    tender_id: str | None = None
    guid: str | None = None


def validate_tender_id(tender_id: str) -> str:
    if not TENDER_ID_PATTERN.fullmatch(tender_id):
        raise ProzorroError(
            "Некоректний номер тендера. Очікується формат "
            "UA-YYYY-MM-DD-NNNNNN-x."
        )
    return tender_id


def compact_guid(guid: str) -> str:
    if GUID_PATTERN.fullmatch(guid):
        return guid.lower()
    if NORMAL_GUID_PATTERN.fullmatch(guid):
        return guid.replace("-", "").lower()
    raise ProzorroError("Некоректний внутрішній id Prozorro.")


def parse_tender_reference(value: str) -> TenderReference:
    candidate = value.strip()
    if TENDER_ID_PATTERN.fullmatch(candidate):
        return TenderReference(tender_id=candidate)
    if GUID_PATTERN.fullmatch(candidate) or NORMAL_GUID_PATTERN.fullmatch(candidate):
        return TenderReference(guid=compact_guid(candidate))

    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in SUPPORTED_HOSTS:
        raise ProzorroError(
            "Очікується UA-ID, GUID, UUID або посилання на тендер Prozorro."
        )

    parts = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
    if len(parts) == 2 and parts[0] == "tender":
        return TenderReference(tender_id=validate_tender_id(parts[1]))
    if len(parts) == 3 and parts[0] in {"uk", "en"} and parts[1] == "tender":
        return TenderReference(tender_id=validate_tender_id(parts[2]))
    if (
        len(parts) == 4
        and parts[0:2] == ["api", "tenders"]
        and parts[3] == "summary"
    ):
        return TenderReference(tender_id=validate_tender_id(parts[2]))
    if (
        len(parts) == 4
        and parts[0:3] == ["api", "2.5", "tenders"]
    ):
        return TenderReference(guid=compact_guid(parts[3]))

    raise ProzorroError("Посилання не веде на підтримуваний тендер Prozorro.")


def tender_link(reference: str, *, timeout: float = 30.0) -> str:
    tender_id = resolve_tender_id(reference, timeout=timeout)
    return TENDER_PAGE_URL.format(tender_id=quote(tender_id, safe=""))


def public_api_link(reference: str, *, timeout: float = 30.0) -> str:
    guid = resolve_guid(reference, timeout=timeout)
    return PUBLIC_API_URL.format(guid=guid)


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


def resolve_guid(reference: str, *, timeout: float = 30.0) -> str:
    parsed = parse_tender_reference(reference)
    if parsed.guid is not None:
        return parsed.guid

    tender_id = parsed.tender_id
    if tender_id is None:
        raise ProzorroError("Не вдалося визначити номер тендера.")
    url = SUMMARY_URL.format(tender_id=quote(tender_id, safe=""))
    summary = fetch_json(url, timeout=timeout)
    guid = summary.get("id")

    if not isinstance(guid, str) or not GUID_PATTERN.fullmatch(guid):
        raise ProzorroError("У відповіді Prozorro немає коректного внутрішнього id.")
    return guid.lower()


def normal_guid(guid: str) -> str:
    normalized = compact_guid(guid)
    return (
        f"{normalized[0:8]}-{normalized[8:12]}-{normalized[12:16]}-"
        f"{normalized[16:20]}-{normalized[20:32]}"
    )


def fetch_tender(reference: str, *, timeout: float = 30.0) -> dict[str, Any]:
    guid = resolve_guid(reference, timeout=timeout)
    url = PUBLIC_API_URL.format(guid=guid)
    return fetch_json(url, timeout=timeout)


def safe_document_filename(value: str, *, fallback: str) -> str:
    filename = INVALID_FILENAME_CHARS.sub("_", value).strip().rstrip(". ")
    if not filename:
        filename = fallback

    stem = filename.split(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED_FILENAMES:
        filename = f"_{filename}"
    return filename


def available_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    suffix = candidate.suffix
    stem = candidate.name[: -len(suffix)] if suffix else candidate.name
    number = 2
    while True:
        candidate = directory / f"{stem} ({number}){suffix}"
        if not candidate.exists():
            return candidate
        number += 1


def download_document(
    url: str,
    destination: Path,
    *,
    timeout: float = 30.0,
) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ProzorroError("Документ містить некоректне посилання.")

    request = Request(
        url,
        headers={"User-Agent": "prozorro-cli/0.1 (+https://prozorro.gov.ua)"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            with destination.open("xb") as output:
                shutil.copyfileobj(response, output)
    except HTTPError as error:
        destination.unlink(missing_ok=True)
        raise ProzorroError(
            f"Не вдалося завантажити документ: HTTP {error.code}."
        ) from error
    except URLError as error:
        destination.unlink(missing_ok=True)
        reason = getattr(error, "reason", error)
        raise ProzorroError(
            f"Не вдалося завантажити документ: {reason}"
        ) from error
    except OSError as error:
        destination.unlink(missing_ok=True)
        raise ProzorroError(
            f"Не вдалося зберегти документ «{destination.name}»: {error}"
        ) from error


def download_documents(
    reference: str,
    output: str | Path,
    *,
    timeout: float = 30.0,
) -> list[Path]:
    payload = fetch_tender(reference, timeout=timeout)
    data = payload.get("data")
    documents = data.get("documents") if isinstance(data, dict) else None
    if not isinstance(documents, list):
        raise ProzorroError("У відповіді Prozorro немає масиву data.documents.")

    output_directory = Path(output).expanduser()
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ProzorroError(
            f"Не вдалося створити каталог «{output_directory}»: {error}"
        ) from error
    if not output_directory.is_dir():
        raise ProzorroError(f"Шлях «{output_directory}» не є каталогом.")

    downloaded: list[Path] = []
    for index, document in enumerate(documents, start=1):
        if not isinstance(document, dict):
            raise ProzorroError(
                f"Документ #{index} у data.documents має некоректний формат."
            )

        url = document.get("url")
        if not isinstance(url, str) or not url.strip():
            raise ProzorroError(
                f"Документ #{index} у data.documents не містить url."
            )

        document_id = document.get("id")
        fallback = (
            document_id
            if isinstance(document_id, str) and document_id.strip()
            else f"document-{index}"
        )
        title = document.get("title")
        filename = safe_document_filename(
            title if isinstance(title, str) else "",
            fallback=fallback,
        )
        destination = available_path(output_directory, filename)
        download_document(url, destination, timeout=timeout)
        downloaded.append(destination)

    return downloaded


def resolve_tender_id(reference: str, *, timeout: float = 30.0) -> str:
    parsed = parse_tender_reference(reference)
    if parsed.tender_id is not None:
        return parsed.tender_id

    guid = parsed.guid
    if guid is None:
        raise ProzorroError("Не вдалося визначити внутрішній id Prozorro.")
    payload = fetch_json(PUBLIC_API_URL.format(guid=guid), timeout=timeout)
    data = payload.get("data")
    tender_id = data.get("tenderID") if isinstance(data, dict) else None
    if not isinstance(tender_id, str):
        raise ProzorroError("У відповіді Prozorro немає номера тендера.")
    return validate_tender_id(tender_id)
