from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from prozorro_cli.commands import register_commands
from prozorro_cli.errors import ProzorroError


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
    subparsers = parser.add_subparsers(required=True)
    register_commands(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_windows_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    args.root_parser = parser

    try:
        return args.handler(args)
    except ProzorroError as error:
        parser.exit(1, f"Помилка: {error}\n")
