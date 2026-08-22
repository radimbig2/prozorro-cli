from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prozorro_cli.client import fetch_json
from prozorro_cli.errors import ProzorroError
from prozorro_cli.services.references import (
    CONTRACT_PUBLIC_API_URL,
    GUID_PATTERN,
    TENDER_CONTRACTS_PUBLIC_API_URL,
    resolve_contract_guid,
    resolve_guid,
)
from prozorro_cli.services.tenders import fetch_tender


def contract_api_url(reference: str) -> str:
    return CONTRACT_PUBLIC_API_URL.format(guid=resolve_contract_guid(reference))


def fetch_contract(reference: str, *, timeout: float = 30.0) -> dict[str, Any]:
    return fetch_json(contract_api_url(reference), timeout=timeout)


def fetch_tender_contracts(
    reference: str,
    *,
    timeout: float = 30.0,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tender_payload = fetch_tender(reference, timeout=timeout)
    data = tender_payload.get("data")
    contracts = data.get("contracts") if isinstance(data, dict) else None

    if isinstance(contracts, list):
        return tender_payload, _validate_contract_list(contracts)

    tender_guid = data.get("id") if isinstance(data, dict) else None
    if not isinstance(tender_guid, str) or not GUID_PATTERN.fullmatch(tender_guid):
        tender_guid = resolve_guid(reference, timeout=timeout)

    collection_url = TENDER_CONTRACTS_PUBLIC_API_URL.format(guid=tender_guid)
    collection_payload = fetch_json(collection_url, timeout=timeout)
    collection = collection_payload.get("data")
    if not isinstance(collection, list):
        raise ProzorroError(
            "У відповіді Prozorro немає масиву контрактів тендера."
        )
    return tender_payload, _validate_contract_list(collection)


def download_contracts_for_tender(
    reference: str,
    output: str | Path,
    *,
    timeout: float = 30.0,
) -> list[Path]:
    tender_payload, contract_summaries = fetch_tender_contracts(
        reference,
        timeout=timeout,
    )
    output_directory = _ensure_directory(output)
    contracts_directory = _ensure_directory(output_directory / "contracts")

    paths = [output_directory / "tender.json"]
    _write_json(paths[0], tender_payload)

    for summary in contract_summaries:
        contract_id = summary["id"]
        contract_payload = fetch_contract(contract_id, timeout=timeout)
        destination = contracts_directory / f"{contract_id}.json"
        _write_json(destination, contract_payload)
        paths.append(destination)

    return paths


def save_contract(
    payload: dict[str, Any],
    output: str | Path,
) -> Path:
    destination = Path(output).expanduser()
    if destination.exists() and destination.is_dir():
        raise ProzorroError(f"Шлях «{destination}» є каталогом, а не файлом.")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ProzorroError(
            f"Не вдалося створити каталог «{destination.parent}»: {error}"
        ) from error
    _write_json(destination, payload)
    return destination


def _validate_contract_list(value: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ProzorroError(
                f"Контракт #{index} у відповіді Prozorro має некоректний формат."
            )
        contract_id = item.get("id")
        if not isinstance(contract_id, str) or not GUID_PATTERN.fullmatch(contract_id):
            raise ProzorroError(
                f"Контракт #{index} у відповіді Prozorro не містить коректного id."
            )
        result.append(item)
    return result


def _ensure_directory(output: str | Path) -> Path:
    directory = Path(output).expanduser()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ProzorroError(
            f"Не вдалося створити каталог «{directory}»: {error}"
        ) from error
    if not directory.is_dir():
        raise ProzorroError(f"Шлях «{directory}» не є каталогом.")
    return directory


def _write_json(destination: Path, payload: dict[str, Any]) -> None:
    try:
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        raise ProzorroError(
            f"Не вдалося зберегти JSON «{destination}»: {error}"
        ) from error
