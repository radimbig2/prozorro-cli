from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from prozorro_cli.cli import build_parser, main


TENDER_ID = "UA-2026-06-15-003439-a"
GUID = "5d2590ef8a1b455f8d09ceeae474b21f"
NORMAL_GUID = "5d2590ef-8a1b-455f-8d09-ceeae474b21f"
CONTRACT_ID = "a4264fee0db34423808f12f17d8e46ed"


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> tuple[int, str]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(list(arguments))
        return exit_code, stdout.getvalue()

    @patch(
        "prozorro_cli.commands.tender.public_api_link",
        return_value=(
            "https://public-api.prozorro.gov.ua/api/2.5/tenders/"
            f"{GUID}"
        ),
    )
    def test_link(self, public_api_link_mock) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--link")

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output,
            "https://public-api.prozorro.gov.ua/api/2.5/tenders/"
            f"{GUID}\n",
        )
        public_api_link_mock.assert_called_once_with(TENDER_ID)

    def test_link_html(self) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--link-html")

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output,
            f"https://prozorro.gov.ua/tender/{TENDER_ID}\n",
        )

    def test_linkhtml_alias(self) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--linkhtml")

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output,
            f"https://prozorro.gov.ua/tender/{TENDER_ID}\n",
        )

    @patch("prozorro_cli.commands.tender.webbrowser.open", return_value=True)
    @patch(
        "prozorro_cli.commands.tender.public_api_link",
        return_value=(
            "https://public-api.prozorro.gov.ua/api/2.5/tenders/"
            f"{GUID}"
        ),
    )
    def test_link_open(
        self,
        public_api_link_mock,
        browser_open_mock,
    ) -> None:
        exit_code, output = self.run_cli(
            "tender",
            TENDER_ID,
            "--link",
            "--open",
        )

        api_url = (
            "https://public-api.prozorro.gov.ua/api/2.5/tenders/"
            f"{GUID}"
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(output, f"{api_url}\n")
        public_api_link_mock.assert_called_once_with(TENDER_ID)
        browser_open_mock.assert_called_once_with(api_url, new=2)

    @patch("prozorro_cli.commands.tender.webbrowser.open", return_value=True)
    def test_link_html_open(self, browser_open_mock) -> None:
        exit_code, output = self.run_cli(
            "tender",
            TENDER_ID,
            "--linkhtml",
            "--open",
        )

        html_url = f"https://prozorro.gov.ua/tender/{TENDER_ID}"
        self.assertEqual(exit_code, 0)
        self.assertEqual(output, f"{html_url}\n")
        browser_open_mock.assert_called_once_with(html_url, new=2)

    def test_stream_configuration_is_safe_with_string_io(self) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--link-html")

        self.assertEqual(exit_code, 0)
        self.assertIn(TENDER_ID, output)

    @patch("prozorro_cli.commands.tender.resolve_guid", return_value=GUID)
    def test_guid(self, resolve_guid_mock) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--guid")

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, f"{GUID}\n")
        resolve_guid_mock.assert_called_once_with(TENDER_ID)

    @patch("prozorro_cli.commands.tender.resolve_guid", return_value=GUID)
    def test_guid_normal(self, resolve_guid_mock) -> None:
        exit_code, output = self.run_cli("tender", TENDER_ID, "--guid-normal")

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "5d2590ef-8a1b-455f-8d09-ceeae474b21f\n")
        resolve_guid_mock.assert_called_once_with(TENDER_ID)

    @patch("prozorro_cli.commands.tender.fetch_tender")
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

    @patch("prozorro_cli.commands.tender.fetch_tender")
    def test_default_passes_normal_uuid_to_client(self, fetch_tender_mock) -> None:
        fetch_tender_mock.return_value = {
            "data": {"id": GUID, "tenderID": TENDER_ID}
        }

        exit_code, output = self.run_cli("tender", NORMAL_GUID)

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output)["data"]["id"], GUID)
        fetch_tender_mock.assert_called_once_with(NORMAL_GUID)

    @patch("prozorro_cli.commands.documents.download_documents")
    def test_documents_downloads_to_output(self, download_documents_mock) -> None:
        download_documents_mock.return_value = [
            "/temp/specification.pdf",
            "/temp/contract.docx",
        ]

        exit_code, output = self.run_cli(
            "documents",
            TENDER_ID,
            "--output",
            "/temp",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            output,
            "/temp/specification.pdf\n"
            "/temp/contract.docx\n"
            "Завантажено документів: 2\n",
        )
        download_documents_mock.assert_called_once_with(TENDER_ID, "/temp")

    @patch("prozorro_cli.commands.contracts.fetch_contract")
    def test_contracts_prints_full_json(self, fetch_contract_mock) -> None:
        fetch_contract_mock.return_value = {
            "data": {"id": CONTRACT_ID, "status": "active"}
        }

        exit_code, output = self.run_cli("contracts", CONTRACT_ID)

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output)["data"]["id"], CONTRACT_ID)
        fetch_contract_mock.assert_called_once_with(CONTRACT_ID)

    @patch("prozorro_cli.commands.contracts.fetch_contract")
    def test_contracts_save_json_to_output_file(self, fetch_contract_mock) -> None:
        payload = {"data": {"id": CONTRACT_ID, "status": "active"}}
        fetch_contract_mock.return_value = payload

        with TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "contract.json"
            exit_code, output = self.run_cli(
                "contracts",
                CONTRACT_ID,
                "--output",
                str(destination),
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(output, f"{destination}\n")
            self.assertEqual(
                json.loads(destination.read_text(encoding="utf-8")),
                payload,
            )

    @patch("prozorro_cli.commands.contracts.download_contracts_for_tender")
    def test_contracts_batch_downloads_to_output(self, download_mock) -> None:
        download_mock.return_value = [
            Path("/temp/tender.json"),
            Path(f"/temp/contracts/{CONTRACT_ID}.json"),
        ]

        exit_code, output = self.run_cli(
            "contracts",
            "--tender",
            TENDER_ID,
            "--output",
            "/temp",
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("tender.json", output)
        self.assertIn(f"{CONTRACT_ID}.json", output)
        self.assertIn("Завантажено JSON: 2", output)
        download_mock.assert_called_once_with(TENDER_ID, "/temp")

    @patch("prozorro_cli.commands.documents.download_contract_documents")
    def test_documents_downloads_contract_documents(self, download_mock) -> None:
        download_mock.return_value = ["/temp/contract.pdf"]

        exit_code, output = self.run_cli(
            "documents",
            "--contract",
            CONTRACT_ID,
            "--output",
            "/temp",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, "/temp/contract.pdf\nЗавантажено документів: 1\n")
        download_mock.assert_called_once_with(CONTRACT_ID, "/temp")

    def test_root_help_lists_contracts(self) -> None:
        help_text = build_parser().format_help()

        self.assertIn("contracts", help_text)
        self.assertIn("документи", help_text)

    def test_contracts_help_lists_tender_and_output(self) -> None:
        parser = build_parser()
        contracts_parser = next(
            action.choices["contracts"]
            for action in parser._actions
            if hasattr(action, "choices") and action.choices and "contracts" in action.choices
        )

        help_text = contracts_parser.format_help()

        self.assertIn("--tender", help_text)
        self.assertIn("--output", help_text)

    def test_contracts_batch_requires_output(self) -> None:
        with self.assertRaises(SystemExit):
            main(["contracts", "--tender", TENDER_ID])


if __name__ == "__main__":
    unittest.main()
