from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from prozorro_cli.errors import ProzorroError
from prozorro_cli.services.contracts import (
    contract_api_url,
    download_contracts_for_tender,
    fetch_contract,
    fetch_tender_contracts,
)
from prozorro_cli.services.documents import download_contract_documents
from prozorro_cli.services.references import (
    parse_contract_reference,
    resolve_contract_guid,
)


TENDER_ID = "UA-2026-06-15-003439-a"
TENDER_GUID = "5d2590ef8a1b455f8d09ceeae474b21f"
CONTRACT_ID = "a4264fee0db34423808f12f17d8e46ed"
CONTRACT_UUID = "a4264fee-0db3-4423-808f-12f17d8e46ed"
CONTRACT_URL = (
    "https://public-api.prozorro.gov.ua/api/2.5/contracts/"
    f"{CONTRACT_ID}"
)


class ContractReferenceTests(unittest.TestCase):
    def test_parse_contract_guid_and_uuid(self) -> None:
        self.assertEqual(parse_contract_reference(CONTRACT_ID).guid, CONTRACT_ID)
        self.assertEqual(parse_contract_reference(CONTRACT_UUID).guid, CONTRACT_ID)
        self.assertEqual(resolve_contract_guid(CONTRACT_UUID), CONTRACT_ID)

    def test_parse_contract_public_api_url(self) -> None:
        self.assertEqual(parse_contract_reference(CONTRACT_URL).guid, CONTRACT_ID)

    def test_rejects_non_contract_reference(self) -> None:
        with self.assertRaisesRegex(ProzorroError, "підтримуваний контракт"):
            parse_contract_reference(
                "https://public-api.prozorro.gov.ua/api/2.5/tenders/"
                f"{TENDER_GUID}"
            )


class ContractServiceTests(unittest.TestCase):
    @patch("prozorro_cli.services.contracts.fetch_json")
    def test_fetch_contract_uses_contract_endpoint(self, fetch_json_mock) -> None:
        payload = {"data": {"id": CONTRACT_ID, "status": "active"}}
        fetch_json_mock.return_value = payload

        result = fetch_contract(CONTRACT_UUID)

        self.assertEqual(result, payload)
        fetch_json_mock.assert_called_once_with(CONTRACT_URL, timeout=30.0)
        self.assertEqual(contract_api_url(CONTRACT_ID), CONTRACT_URL)

    @patch("prozorro_cli.services.contracts.fetch_tender")
    @patch("prozorro_cli.services.contracts.fetch_json")
    def test_fetch_tender_contracts_uses_data_contracts(
        self,
        fetch_json_mock,
        fetch_tender_mock,
    ) -> None:
        summaries = [
            {"id": CONTRACT_ID, "status": "cancelled"},
            {
                "id": "b4264fee0db34423808f12f17d8e46ed",
                "status": "pending",
            },
        ]
        fetch_tender_mock.return_value = {
            "data": {"id": TENDER_GUID, "contracts": summaries}
        }

        tender_payload, contracts = fetch_tender_contracts(TENDER_ID)

        self.assertEqual(tender_payload["data"]["id"], TENDER_GUID)
        self.assertEqual(contracts, summaries)
        fetch_json_mock.assert_not_called()

    @patch("prozorro_cli.services.contracts.fetch_tender")
    @patch("prozorro_cli.services.contracts.fetch_json")
    def test_fetch_tender_contracts_falls_back_to_collection(
        self,
        fetch_json_mock,
        fetch_tender_mock,
    ) -> None:
        collection_url = (
            "https://public-api.prozorro.gov.ua/api/2.5/tenders/"
            f"{TENDER_GUID}/contracts"
        )
        collection = {"data": [{"id": CONTRACT_ID, "status": "active"}]}
        fetch_tender_mock.return_value = {"data": {"id": TENDER_GUID}}
        fetch_json_mock.return_value = collection

        _, contracts = fetch_tender_contracts(TENDER_ID)

        self.assertEqual(contracts, collection["data"])
        fetch_json_mock.assert_called_once_with(collection_url, timeout=30.0)

    @patch("prozorro_cli.services.contracts.fetch_contract")
    @patch("prozorro_cli.services.contracts.fetch_tender_contracts")
    def test_download_contracts_saves_tender_and_all_statuses(
        self,
        fetch_tender_contracts_mock,
        fetch_contract_mock,
    ) -> None:
        cancelled_id = CONTRACT_ID
        pending_id = "b4264fee0db34423808f12f17d8e46ed"
        tender_payload = {"data": {"id": TENDER_GUID, "tenderID": TENDER_ID}}
        summaries = [
            {"id": cancelled_id, "status": "cancelled"},
            {"id": pending_id, "status": "pending"},
        ]
        fetch_tender_contracts_mock.return_value = (tender_payload, summaries)
        fetch_contract_mock.side_effect = lambda contract_id, **_: {
            "data": {"id": contract_id, "status": "cancelled" if contract_id == cancelled_id else "pending"}
        }

        with TemporaryDirectory() as temporary_directory:
            paths = download_contracts_for_tender(TENDER_ID, temporary_directory)
            output = Path(temporary_directory)

            self.assertEqual(
                [path.relative_to(output).as_posix() for path in paths],
                [
                    "tender.json",
                    f"contracts/{cancelled_id}.json",
                    f"contracts/{pending_id}.json",
                ],
            )
            self.assertEqual(
                json.loads((output / "tender.json").read_text(encoding="utf-8")),
                tender_payload,
            )
            self.assertEqual(
                json.loads(
                    (output / "contracts" / f"{cancelled_id}.json").read_text(
                        encoding="utf-8"
                    )
                )["data"]["status"],
                "cancelled",
            )

        fetch_contract_mock.assert_any_call(cancelled_id, timeout=30.0)
        fetch_contract_mock.assert_any_call(pending_id, timeout=30.0)

    @patch("prozorro_cli.services.documents.download_document")
    @patch("prozorro_cli.services.documents.fetch_contract")
    def test_download_contract_documents_uses_top_level_document_urls(
        self,
        fetch_contract_mock,
        download_document_mock,
    ) -> None:
        contract_document_url = "https://public-docs.prozorro.gov.ua/contract"
        change_document_url = "https://public-docs.prozorro.gov.ua/change"
        fetch_contract_mock.return_value = {
            "data": {
                "documents": [
                    {
                        "id": "document-id",
                        "title": "contract.pdf",
                        "url": contract_document_url,
                    }
                ],
                "changes": [
                    {
                        "documents": [
                            {
                                "title": "change.pdf",
                                "url": change_document_url,
                            }
                        ]
                    }
                ],
            }
        }
        download_document_mock.side_effect = (
            lambda _url, destination, **_: destination.touch()
        )

        with TemporaryDirectory() as temporary_directory:
            paths = download_contract_documents(CONTRACT_ID, temporary_directory)

        self.assertEqual([path.name for path in paths], ["contract.pdf"])
        download_document_mock.assert_called_once()
        self.assertEqual(download_document_mock.call_args.args[0], contract_document_url)

    @patch("prozorro_cli.services.documents.fetch_contract")
    def test_contract_documents_require_document_url(self, fetch_contract_mock) -> None:
        fetch_contract_mock.return_value = {"data": {"documents": [{"title": "x.pdf"}]}}

        with TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ProzorroError, "не містить url"):
                download_contract_documents(CONTRACT_ID, temporary_directory)


if __name__ == "__main__":
    unittest.main()
