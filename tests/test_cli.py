from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from prozorro_cli.cli import main


TENDER_ID = "UA-2026-06-15-003439-a"
GUID = "5d2590ef8a1b455f8d09ceeae474b21f"


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> tuple[int, str]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(list(arguments))
        return exit_code, stdout.getvalue()

    def test_link(self) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--link")

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output,
            f"https://prozorro.gov.ua/tender/{TENDER_ID}\n",
        )

    def test_stream_configuration_is_safe_with_string_io(self) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--link")

        self.assertEqual(exit_code, 0)
        self.assertIn(TENDER_ID, output)

    @patch("prozorro_cli.cli.resolve_guid", return_value=GUID)
    def test_guid(self, resolve_guid_mock) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--guid")

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, f"{GUID}\n")
        resolve_guid_mock.assert_called_once_with(TENDER_ID)

    @patch("prozorro_cli.cli.resolve_guid", return_value=GUID)
    def test_guid_normal(self, resolve_guid_mock) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--guid-normal")

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "5d2590ef-8a1b-455f-8d09-ceeae474b21f\n")
        resolve_guid_mock.assert_called_once_with(TENDER_ID)

    @patch("prozorro_cli.cli.fetch_tender")
    def test_default_prints_full_json(self, fetch_tender_mock) -> None:
        fetch_tender_mock.return_value = {
            "data": {
                "id": GUID,
                "tenderID": TENDER_ID,
                "title": "Електрична енергія",
            }
        }

        exit_code, output = self.run_cli("tender", TENDER_ID)

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output)["data"]["id"], GUID)
        self.assertIn("Електрична енергія", output)


if __name__ == "__main__":
    unittest.main()
