#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: src/scitex_msword/_cli/_list_apis.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""``scitex-msword list-python-apis`` — enumerate the public Python API surface."""

from __future__ import annotations

import inspect
import json as _json
from typing import List, Tuple

import click


def _public_api_entries() -> List[Tuple[str, str, str, str]]:
    """Return one ``(kind, name, signature, first_doc_line)`` tuple per public name.

    ``kind`` is ``"F"`` (function), ``"C"`` (class), or ``"V"`` (value).
    Reads ``scitex_msword.__all__`` so the public surface stays the
    single source of truth.
    """
    import scitex_msword as _sxm

    names = getattr(_sxm, "__all__", [])
    entries: List[Tuple[str, str, str, str]] = []
    for name in names:
        obj = getattr(_sxm, name, None)
        if obj is None:
            entries.append(("V", name, "", ""))
            continue
        if inspect.isfunction(obj):
            kind = "F"
        elif inspect.isclass(obj):
            kind = "C"
        else:
            kind = "V"
        try:
            sig = str(inspect.signature(obj)) if kind in ("F", "C") else ""
        except (TypeError, ValueError):
            sig = ""
        doc = inspect.getdoc(obj) or ""
        first_line = doc.split("\n", 1)[0] if doc else ""
        entries.append((kind, name, sig, first_line))
    return entries


def register(main_group: click.Group) -> None:
    """Attach ``list-python-apis`` to the top-level CLI group."""

    @main_group.command("list-python-apis")
    @click.option(
        "-v",
        "--verbose",
        count=True,
        default=0,
        help="Verbosity: -v signatures, -vv +docstring summary, -vvv full docs.",
    )
    @click.option(
        "--json", "as_json", is_flag=True, default=False, help="Output as JSON."
    )
    def list_python_apis_cmd(verbose, as_json):
        """Enumerate the public Python API surface of scitex_msword.

        \b
        Example:
            $ scitex-msword list-python-apis
            $ scitex-msword list-python-apis -vv
            $ scitex-msword list-python-apis --json
        """
        from .. import __version__ as _v

        entries = _public_api_entries()
        if as_json:
            data = [
                {"kind": k, "name": n, "signature": s, "doc": d}
                for k, n, s, d in entries
            ]
            click.echo(_json.dumps(data, indent=2, ensure_ascii=False))
            return
        click.echo(f"scitex_msword v{_v} ({len(entries)} public names):")
        click.echo("Legend: [F]=Function [C]=Class [V]=Value")
        for kind, name, sig, doc in entries:
            if verbose == 0:
                click.echo(f"  [{kind}] {name}")
            else:
                sep = "" if sig.startswith("(") else " "
                click.echo(f"  [{kind}] {name}{sep}{sig}")
                if verbose >= 2 and doc:
                    click.echo(f"      {doc}")


__all__ = ["register"]
