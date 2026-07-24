from __future__ import annotations

import argparse

from prozorro_cli.services.documents import download_documents


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "documents",
        help="завантажити всі файли з data.documents тендера",
    )
    parser.add_argument(
        "reference",
        metavar="REFERENCE",
        help="UA-ID, GUID, UUID або посилання на тендер Prozorro",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="DIRECTORY",
        help="каталог для завантажених документів",
    )
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    downloaded = download_documents(args.reference, args.output)
    for path in downloaded:
        print(path)
    print(f"Завантажено документів: {len(downloaded)}")
    return 0
