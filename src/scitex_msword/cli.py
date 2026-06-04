#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: src/scitex_msword/cli.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""
Command-line interface for scitex-msword.

Provides a thin subcommand-style wrapper around the public Python API.
The CLI is intentionally minimal — Python remains the primary
interface — but the subcommands let agents and shell scripts exercise
the same edits used by the dogfood pipelines without writing Python.

Usage::

    scitex-msword <subcommand> [options]

Subcommands (initial set, more to follow as they accrete from the
dogfood loops):

- ``insert-table``  Insert a Word table after a target paragraph.
                    Mirrors :func:`scitex_msword.insert_table_after_paragraph`.

Subcommands return exit code 0 on success and 1 on error; ``--help``
on the top level lists subcommands; ``--help`` on a subcommand
documents its arguments.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Sequence


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse Parser with all subcommands wired."""
    parser = argparse.ArgumentParser(
        prog="scitex-msword",
        description=(
            "scitex-msword command-line interface — Word .docx edit "
            "operations from the SciTeX manuscript pipeline."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="subcommand",
        metavar="<subcommand>",
        required=True,
    )

    _add_insert_table_subparser(subparsers)

    return parser


def _add_insert_table_subparser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",
) -> None:
    """Wire the ``insert-table`` subcommand."""
    sp = subparsers.add_parser(
        "insert-table",
        help="Insert a Word table after a target paragraph.",
        description=(
            "Insert a Word table immediately after the paragraph at "
            "PARAGRAPH_INDEX in PATH, writing the result to OUT. Rows "
            "are provided as a JSON array-of-arrays via --rows or "
            "--rows-file (one JSON document, no shell quoting headaches "
            "for Japanese cell text). When the source document has "
            "Track Changes enabled, each inserted row is marked as a "
            "tracked insertion (overridable with --track-changes / "
            "--no-track-changes)."
        ),
    )
    sp.add_argument("--path", required=True, help="Input .docx path.")
    sp.add_argument("--out", required=True, help="Output .docx path.")
    sp.add_argument(
        "--paragraph-index",
        type=int,
        required=True,
        help="0-based index of the anchor paragraph.",
    )
    rows_group = sp.add_mutually_exclusive_group(required=True)
    rows_group.add_argument(
        "--rows",
        help=(
            "JSON array-of-arrays of strings, e.g. "
            '\'[["役割","モジュール"],["論文執筆","scitex-writer"]]\'.'
        ),
    )
    rows_group.add_argument(
        "--rows-file",
        type=Path,
        help="Path to a JSON file containing the array-of-arrays.",
    )
    sp.add_argument(
        "--col-widths-dxa",
        help=(
            "Comma-separated column widths in dxa (twentieths of a "
            "point). Default '3000,6000' (2-col 1:2)."
        ),
        default="3000,6000",
    )
    sp.add_argument(
        "--no-header-row",
        dest="header_row",
        action="store_false",
        help="Disable header styling on row 0 (default: header on).",
    )
    sp.set_defaults(header_row=True)
    sp.add_argument("--body-font", default="MS 明朝", help="Body row font.")
    sp.add_argument("--header-font", default="MS ゴシック", help="Header row font.")
    sp.add_argument(
        "--font-size-pt",
        type=float,
        default=10.5,
        help="Run font size in points (default 10.5).",
    )
    tc_group = sp.add_mutually_exclusive_group()
    tc_group.add_argument(
        "--track-changes",
        dest="track_changes",
        action="store_true",
        help="Force track-changes row markers on.",
    )
    tc_group.add_argument(
        "--no-track-changes",
        dest="track_changes",
        action="store_false",
        help="Force track-changes row markers off.",
    )
    sp.set_defaults(track_changes=None)
    sp.add_argument(
        "--track-changes-author",
        default="agent",
        help="Author string for the row-ins markers (default 'agent').",
    )
    sp.add_argument(
        "--track-changes-date",
        default=None,
        help="ISO-8601 timestamp for the row-ins markers (default: now UTC).",
    )
    sp.set_defaults(func=_cmd_insert_table)


def _parse_rows(args: argparse.Namespace) -> List[List[str]]:
    """Decode the ``--rows`` / ``--rows-file`` argument into list-of-lists-of-str."""
    if args.rows_file is not None:
        raw = Path(args.rows_file).read_text(encoding="utf-8")
    else:
        raw = args.rows
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"insert-table: invalid JSON for --rows: {e}") from e
    if not isinstance(parsed, list) or not all(isinstance(r, list) for r in parsed):
        raise SystemExit(
            "insert-table: --rows / --rows-file must decode to a JSON "
            "array-of-arrays-of-strings"
        )
    return [[str(c) for c in r] for r in parsed]


def _parse_col_widths(arg: str) -> List[int]:
    """Decode the comma-separated ``--col-widths-dxa`` arg into ``List[int]``."""
    parts = [p.strip() for p in arg.split(",") if p.strip()]
    if not parts:
        raise SystemExit("insert-table: --col-widths-dxa cannot be empty")
    try:
        return [int(p) for p in parts]
    except ValueError as e:
        raise SystemExit(
            f"insert-table: --col-widths-dxa entries must be integers ({e})"
        ) from e


def _cmd_insert_table(args: argparse.Namespace) -> int:
    """Run the ``insert-table`` subcommand."""
    import docx as _docx

    from .tables import insert_table_after_paragraph

    rows = _parse_rows(args)
    col_widths = _parse_col_widths(args.col_widths_dxa)

    doc = _docx.Document(args.path)
    insert_table_after_paragraph(
        doc,
        paragraph_index=args.paragraph_index,
        rows=rows,
        col_widths_dxa=col_widths,
        header_row=args.header_row,
        body_font=args.body_font,
        header_font=args.header_font,
        font_size_pt=args.font_size_pt,
        track_changes=args.track_changes,
        track_changes_author=args.track_changes_author,
        track_changes_date=args.track_changes_date,
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.out)
    print(args.out)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point — returns process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["main"]
