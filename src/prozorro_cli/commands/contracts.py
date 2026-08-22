from __future__ import annotations

import argparse
import json
import sys

from prozorro_cli.services.contracts import (
    download_contracts_for_tender,
    fetch_contract,
    save_contract,
)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "contracts",
        help="отримати контракт або всі контракти тендера",
    )
    parser.add_argument(
        "reference",
        nargs="?",
        metavar="CONTRACT_REF",
        help="GUID, UUID або посилання Public API на контракт",
    )
    parser.add_argument(
        "--tender",
        dest="tender_reference",
        metavar="TENDER_REF",
        help="завантажити тендер і всі його контракти",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="файл для одного контракту або каталог для --tender",
    )
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    has_contract = args.reference is not None
    has_tender = args.tender_reference is not None
    if has_contract == has_tender:
        args.root_parser.error(
            "вкажіть CONTRACT_REF або --tender TENDER_REF, але не обидва варіанти"
        )

    if has_tender:
        if args.output is None:
            args.root_parser.error("--tender потребує --output DIRECTORY")
        paths = download_contracts_for_tender(
            args.tender_reference,
            args.output,
        )
        for path in paths:
            print(path)
        print(f"Завантажено JSON: {len(paths)}")
        return 0

    payload = fetch_contract(args.reference)
    if args.output is None:
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    destination = save_contract(payload, args.output)
    print(destination)
    return 0
