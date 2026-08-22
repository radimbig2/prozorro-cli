from __future__ import annotations

import argparse

from prozorro_cli.services.documents import (
    download_contract_documents,
    download_documents,
)


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "documents",
        help="завантажити файли з data.documents тендера або контракту",
    )
    parser.add_argument(
        "reference",
        nargs="?",
        metavar="REFERENCE",
        help="UA-ID, GUID, UUID або посилання на тендер Prozorro",
    )
    parser.add_argument(
        "--contract",
        dest="contract_reference",
        metavar="CONTRACT_REF",
        help="завантажити data.documents конкретного контракту",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="DIRECTORY",
        help="каталог для завантажених документів",
    )
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    if (args.reference is None) == (args.contract_reference is None):
        args.root_parser.error(
            "вкажіть REFERENCE або --contract CONTRACT_REF, але не обидва варіанти"
        )

    if args.contract_reference is not None:
        downloaded = download_contract_documents(
            args.contract_reference,
            args.output,
        )
    else:
        downloaded = download_documents(args.reference, args.output)
    for path in downloaded:
        print(path)
    print(f"Завантажено документів: {len(downloaded)}")
    return 0
