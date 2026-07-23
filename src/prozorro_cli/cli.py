from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from collections.abc import Sequence

from prozorro_cli.client import (
    ProzorroError,
    download_documents,
    fetch_tender,
    normal_guid,
    public_api_link,
    resolve_guid,
    tender_link,
)


def configure_windows_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def print_link(url: str, *, open_in_browser: bool) -> None:
    print(url)
    if open_in_browser and not webbrowser.open(url, new=2):
        raise ProzorroError("Не вдалося відкрити посилання у браузері.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prozorro-cli",
        description="Отримання публічних даних про тендери Prozorro.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    tender_parser = subparsers.add_parser(
        "tender",
        help="отримати посилання, GUID або повний JSON тендера",
    )
    tender_parser.add_argument(
        "reference",
        metavar="REFERENCE",
        help="UA-ID, GUID, UUID або посилання на тендер Prozorro",
    )

    output_group = tender_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--link",
        action="store_true",
        help="вивести посилання на повний JSON у Public API",
    )
    output_group.add_argument(
        "--link-html",
        "--linkhtml",
        dest="link_html",
        action="store_true",
        help="вивести посилання на HTML-сторінку тендера",
    )
    output_group.add_argument(
        "--guid",
        action="store_true",
        help="вивести внутрішній id Prozorro без дефісів",
    )
    output_group.add_argument(
        "--guid-normal",
        action="store_true",
        help="вивести внутрішній id у стандартному форматі UUID",
    )
    tender_parser.add_argument(
        "--open",
        action="store_true",
        help="відкрити посилання з --link або --link-html у браузері",
    )

    documents_parser = subparsers.add_parser(
        "documents",
        help="завантажити всі файли з data.documents тендера",
    )
    documents_parser.add_argument(
        "reference",
        metavar="REFERENCE",
        help="UA-ID, GUID, UUID або посилання на тендер Prozorro",
    )
    documents_parser.add_argument(
        "--output",
        required=True,
        metavar="DIRECTORY",
        help="каталог для завантажених документів",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_windows_streams()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "tender":
            if args.open and not (args.link or args.link_html):
                parser.error("--open потребує --link або --link-html.")

            if args.link:
                print_link(
                    public_api_link(args.reference),
                    open_in_browser=args.open,
                )
                return 0

            if args.link_html:
                print_link(
                    tender_link(args.reference),
                    open_in_browser=args.open,
                )
                return 0

            if args.guid or args.guid_normal:
                guid = resolve_guid(args.reference)
                print(normal_guid(guid) if args.guid_normal else guid)
                return 0

            payload = fetch_tender(args.reference)
            json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
            return 0

        if args.command == "documents":
            downloaded = download_documents(args.reference, args.output)
            for path in downloaded:
                print(path)
            print(f"Завантажено документів: {len(downloaded)}")
            return 0
    except ProzorroError as error:
        parser.exit(1, f"Помилка: {error}\n")

    parser.error("Невідома команда.")
    return 2
