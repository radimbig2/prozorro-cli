from __future__ import annotations

import unittest
from unittest.mock import patch

from prozorro_cli.client import (
    ProzorroError,
    fetch_tender,
    normal_guid,
    resolve_guid,
    tender_link,
)


TENDER_ID = "UA-2026-06-15-003439-a"
GUID = "5d2590ef8a1b455f8d09ceeae474b21f"


class ClientTests(unittest.TestCase):
    def test_tender_link(self) -> None:
        self.assertEqual(
            tender_link(TENDER_ID),
            f"https://prozorro.gov.ua/tender/{TENDER_ID}",
        )

    def test_invalid_tender_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(ProzorroError, "Некоректний номер"):
            tender_link("not-a-tender")

    def test_normal_guid(self) -> None:
        self.assertEqual(
            normal_guid(GUID),
            "5d2590ef-8a1b-455f-8d09-ceeae474b21f",
        )

    @patch("prozorro_cli.client.fetch_json")
    def test_resolve_guid_uses_summary_endpoint(self, fetch_json_mock) -> None:
        fetch_json_mock.return_value = {"id": GUID, "tenderID": TENDER_ID}

        self.assertEqual(resolve_guid(TENDER_ID), GUID)
        fetch_json_mock.assert_called_once_with(
            f"https://prozorro.gov.ua/api/tenders/{TENDER_ID}/summary",
            timeout=30.0,
        )

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


if __name__ == "__main__":
    unittest.main()
