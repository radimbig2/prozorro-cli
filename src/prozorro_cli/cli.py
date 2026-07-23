from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from prozorro_cli.client import (
    ProzorroError,
    fetch_tender,
    normal_guid,
    resolve_guid,
    tender_link,
)


def configure_windows_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


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
        "tender_id",
        metavar="UA-ID",
        help="номер тендера, наприклад UA-2026-06-15-003439-a",
    )

    output_group = tender_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--link",
        action="store_true",
        help="вивести посилання на сторінку тендера",
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_windows_streams()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "tender":
            if args.link:
                print(tender_link(args.tender_id))
                return 0

            if args.guid or args.guid_normal:
                guid = resolve_guid(args.tender_id)
                print(normal_guid(guid) if args.guid_normal else guid)
                return 0

            payload = fetch_tender(args.tender_id)
            json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
            return 0
    except ProzorroError as error:
        parser.exit(1, f"Помилка: {error}\n")

    parser.error("Невідома команда.")
    return 2
