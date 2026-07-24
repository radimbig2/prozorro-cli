from __future__ import annotations

import re
from pathlib import Path

from prozorro_cli.client import download_document
from prozorro_cli.errors import ProzorroError
from prozorro_cli.services.tenders import fetch_tender


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED_FILENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


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
