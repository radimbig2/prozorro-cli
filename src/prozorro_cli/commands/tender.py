from __future__ import annotations

import argparse
import json
import sys
import webbrowser

from prozorro_cli.errors import ProzorroError
from prozorro_cli.services.references import normal_guid, resolve_guid
from prozorro_cli.services.tenders import fetch_tender, public_api_link, tender_link


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "tender",
        help="отримати посилання, GUID або повний JSON тендера",
    )
    parser.add_argument(
        "reference",
        metavar="REFERENCE",
        help="UA-ID, GUID, UUID або посилання на тендер Prozorro",
    )

    output_group = parser.add_mutually_exclusive_group()
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
    parser.add_argument(
        "--open",
        action="store_true",
        help="відкрити посилання з --link або --link-html у браузері",
    )
    parser.set_defaults(handler=handle)


def print_link(url: str, *, open_in_browser: bool) -> None:
    print(url)
    if open_in_browser and not webbrowser.open(url, new=2):
        raise ProzorroError("Не вдалося відкрити посилання у браузері.")


def handle(args: argparse.Namespace) -> int:
    if args.open and not (args.link or args.link_html):
        args.root_parser.error("--open потребує --link або --link-html.")

    if args.link:
        print_link(public_api_link(args.reference), open_in_browser=args.open)
        return 0

    if args.link_html:
        print_link(tender_link(args.reference), open_in_browser=args.open)
        return 0

    if args.guid or args.guid_normal:
        guid = resolve_guid(args.reference)
        print(normal_guid(guid) if args.guid_normal else guid)
        return 0

    payload = fetch_tender(args.reference)
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0
