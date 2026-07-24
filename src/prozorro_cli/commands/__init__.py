from __future__ import annotations

import argparse

from prozorro_cli.commands import documents, tender


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    for command in (tender, documents):
        command.register(subparsers)
