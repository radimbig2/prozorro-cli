from __future__ import annotations

import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from prozorro_cli.client import (
    ProzorroError,
    compact_guid,
    download_document,
    download_documents,
    fetch_tender,
    normal_guid,
    parse_tender_reference,
    public_api_link,
    resolve_guid,
    resolve_tender_id,
    safe_document_filename,
    tender_link,
)


TENDER_ID = "UA-2026-06-15-003439-a"
GUID = "5d2590ef8a1b455f8d09ceeae474b21f"
NORMAL_GUID = "5d2590ef-8a1b-455f-8d09-ceeae474b21f"


class ClientTests(unittest.TestCase):
    def test_tender_link(self) -> None:
        self.assertEqual(
            tender_link(TENDER_ID),
            f"https://prozorro.gov.ua/tender/{TENDER_ID}",
        )

    @patch("prozorro_cli.client.fetch_json")
    def test_public_api_link_from_tender_id(self, fetch_json_mock) -> None:
        fetch_json_mock.return_value = {"id": GUID, "tenderID": TENDER_ID}

        self.assertEqual(
            public_api_link(TENDER_ID),
            f"https://public-api.prozorro.gov.ua/api/2.5/tenders/{GUID}",
        )

    @patch("prozorro_cli.client.fetch_json")
    def test_public_api_link_from_uuid_skips_network(self, fetch_json_mock) -> None:
        self.assertEqual(
            public_api_link(NORMAL_GUID),
            f"https://public-api.prozorro.gov.ua/api/2.5/tenders/{GUID}",
        )
        fetch_json_mock.assert_not_called()

    def test_invalid_reference_is_rejected(self) -> None:
        with self.assertRaisesRegex(ProzorroError, "Очікується UA-ID"):
            tender_link("not-a-tender")

    def test_normal_guid(self) -> None:
        self.assertEqual(normal_guid(GUID), NORMAL_GUID)

    def test_compact_guid_accepts_normal_uuid(self) -> None:
        self.assertEqual(compact_guid(NORMAL_GUID), GUID)

    def test_parse_tender_page_links(self) -> None:
        for url in (
            f"https://prozorro.gov.ua/tender/{TENDER_ID}",
            f"https://prozorro.gov.ua/uk/tender/{TENDER_ID}",
            f"https://prozorro.gov.ua/en/tender/{TENDER_ID}?source=test",
        ):
            with self.subTest(url=url):
                self.assertEqual(parse_tender_reference(url).tender_id, TENDER_ID)

    def test_parse_summary_link(self) -> None:
        reference = parse_tender_reference(
            f"https://prozorro.gov.ua/api/tenders/{TENDER_ID}/summary"
        )
        self.assertEqual(reference.tender_id, TENDER_ID)

    def test_parse_public_api_links(self) -> None:
        for guid in (GUID, NORMAL_GUID):
            url = f"https://public-api.prozorro.gov.ua/api/2.5/tenders/{guid}"
            with self.subTest(url=url):
                self.assertEqual(parse_tender_reference(url).guid, GUID)

    def test_unsupported_link_is_rejected(self) -> None:
        with self.assertRaisesRegex(ProzorroError, "підтримуваний тендер"):
            parse_tender_reference("https://prozorro.gov.ua/plans/example")

    @patch("prozorro_cli.client.fetch_json")
    def test_resolve_guid_uses_summary_endpoint(self, fetch_json_mock) -> None:
        fetch_json_mock.return_value = {"id": GUID, "tenderID": TENDER_ID}

        self.assertEqual(resolve_guid(TENDER_ID), GUID)
        fetch_json_mock.assert_called_once_with(
            f"https://prozorro.gov.ua/api/tenders/{TENDER_ID}/summary",
            timeout=30.0,
        )

    @patch("prozorro_cli.client.fetch_json")
    def test_resolve_guid_from_uuid_does_not_call_network(
        self, fetch_json_mock
    ) -> None:
        self.assertEqual(resolve_guid(NORMAL_GUID), GUID)
        fetch_json_mock.assert_not_called()

    @patch("prozorro_cli.client.fetch_json")
    def test_resolve_guid_rejects_missing_id(self, fetch_json_mock) -> None:
        fetch_json_mock.return_value = {"tenderID": TENDER_ID}

        with self.assertRaisesRegex(ProzorroError, "внутрішнього id"):
            resolve_guid(TENDER_ID)

    @patch("prozorro_cli.client.fetch_json")
    def test_fetch_tender_uses_resolved_guid(self, fetch_json_mock) -> None:
        fetch_json_mock.side_effect = [
            {"id": GUID, "tenderID": TENDER_ID},
            {"data": {"id": GUID, "tenderID": TENDER_ID}},
        ]

        payload = fetch_tender(TENDER_ID)

        self.assertEqual(payload["data"]["id"], GUID)
        self.assertEqual(
            fetch_json_mock.call_args_list[1].args[0],
            f"https://public-api.prozorro.gov.ua/api/2.5/tenders/{GUID}",
        )

    @patch("prozorro_cli.client.fetch_json")
    def test_fetch_tender_by_guid_skips_summary(self, fetch_json_mock) -> None:
        fetch_json_mock.return_value = {
            "data": {"id": GUID, "tenderID": TENDER_ID}
        }

        payload = fetch_tender(NORMAL_GUID)

        self.assertEqual(payload["data"]["id"], GUID)
        fetch_json_mock.assert_called_once_with(
            f"https://public-api.prozorro.gov.ua/api/2.5/tenders/{GUID}",
            timeout=30.0,
        )

    @patch("prozorro_cli.client.fetch_json")
    def test_resolve_tender_id_from_guid(self, fetch_json_mock) -> None:
        fetch_json_mock.return_value = {
            "data": {"id": GUID, "tenderID": TENDER_ID}
        }

        self.assertEqual(resolve_tender_id(GUID), TENDER_ID)

    @patch("prozorro_cli.client.fetch_json")
    def test_tender_link_from_guid(self, fetch_json_mock) -> None:
        fetch_json_mock.return_value = {
            "data": {"id": GUID, "tenderID": TENDER_ID}
        }

        self.assertEqual(
            tender_link(GUID),
            f"https://prozorro.gov.ua/tender/{TENDER_ID}",
        )

    def test_safe_document_filename(self) -> None:
        self.assertEqual(
            safe_document_filename('contract: final?.pdf', fallback="document-1"),
            "contract_ final_.pdf",
        )
        self.assertEqual(
            safe_document_filename("CON", fallback="document-1"),
            "_CON",
        )

    @patch("prozorro_cli.client.urlopen")
    def test_download_document_writes_response_bytes(self, urlopen_mock) -> None:
        response = BytesIO(b"document contents")
        urlopen_mock.return_value.__enter__.return_value = response

        with TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "document.pdf"

            download_document(
                "https://public-docs.prozorro.gov.ua/document",
                destination,
            )

            self.assertEqual(destination.read_bytes(), b"document contents")

    @patch("prozorro_cli.client.download_document")
    @patch("prozorro_cli.client.fetch_tender")
    def test_download_documents_uses_data_documents(
        self,
        fetch_tender_mock,
        download_document_mock,
    ) -> None:
        download_document_mock.side_effect = (
            lambda _url, destination, **_kwargs: destination.touch()
        )
        fetch_tender_mock.return_value = {
            "data": {
                "documents": [
                    {
                        "id": "first-id",
                        "title": "specification.pdf",
                        "url": "https://public-docs.prozorro.gov.ua/specification",
                    },
                    {
                        "id": "second-id",
                        "title": "specification.pdf",
                        "url": "https://public-docs.prozorro.gov.ua/contract",
                    },
                ]
            }
        }

        with TemporaryDirectory() as temporary_directory:
            first_existing = Path(temporary_directory) / "specification.pdf"
            first_existing.write_bytes(b"existing")

            result = download_documents(TENDER_ID, temporary_directory)

        self.assertEqual(
            [path.name for path in result],
            ["specification (2).pdf", "specification (3).pdf"],
        )
        self.assertEqual(download_document_mock.call_count, 2)

    @patch("prozorro_cli.client.fetch_tender")
    def test_download_documents_requires_document_url(
        self,
        fetch_tender_mock,
    ) -> None:
        fetch_tender_mock.return_value = {
            "data": {"documents": [{"title": "missing-url.pdf"}]}
        }

        with TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ProzorroError, "не містить url"):
                download_documents(TENDER_ID, temporary_directory)


if __name__ == "__main__":
    unittest.main()
