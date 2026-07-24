from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from prozorro_cli.errors import ProzorroError


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
