#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: src/scitex_msword/_cli/_mcp.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""``scitex-msword mcp`` group — start the server / list MCP tools."""

from __future__ import annotations

import json as _json
import sys
from typing import List

import click


def _mcp_tool_names() -> List[str]:
    """Best-effort enumeration of MCP tool names registered by ``build_server()``.

    Works whether the underlying SDK exposes tools via FastMCP's
    ``_tool_manager._tools`` dict or via a ``list_tools()`` method —
    falls back to ``[]`` if the optional ``mcp`` extra is not installed.
    """
    try:
        from ..mcp_server import build_server

        server = build_server()
    except Exception:
        return []
    tool_manager = getattr(server, "_tool_manager", None)
    if tool_manager is not None:
        tools_attr = getattr(tool_manager, "_tools", None)
        if isinstance(tools_attr, dict):
            return sorted(tools_attr)
    list_tools = getattr(server, "list_tools", None)
    if callable(list_tools):
        try:
            tools = list_tools()
            return sorted(t.name for t in tools)
        except Exception:
            return []
    return []


def register(main_group: click.Group) -> None:
    """Attach the ``mcp`` noun group + its verbs to the top-level CLI group."""

    @main_group.group("mcp", invoke_without_command=True)
    @click.pass_context
    def mcp_group(ctx):
        """MCP (Model Context Protocol) server management.

        \b
        Example:
            $ scitex-msword mcp list-tools
            $ scitex-msword mcp start
        """
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @mcp_group.command("start")
    @click.option(
        "--dry-run",
        is_flag=True,
        default=False,
        help="Show what would happen without starting the server.",
    )
    @click.option(
        "--yes",
        "-y",
        is_flag=True,
        default=False,
        help="Skip confirmation prompts (no-op; serve is non-destructive).",
    )
    @click.option(
        "--json", "as_json", is_flag=True, default=False, help="Output as JSON."
    )
    def mcp_start_cmd(dry_run, yes, as_json):
        """Start the scitex-msword MCP server over stdio.

        \b
        Example:
            $ scitex-msword mcp start
            $ scitex-msword mcp start --dry-run
        """
        del yes  # accepted for §2; serve is non-destructive
        if dry_run:
            if as_json:
                click.echo(_json.dumps({"action": "start", "dry_run": True}))
            else:
                click.echo("Would start scitex-msword MCP server (stdio).")
            return
        try:
            from ..mcp_server import serve

            serve()
        except ImportError as e:
            click.echo(
                "MCP scaffold requires the 'mcp' package. "
                "Install with: pip install scitex-msword[mcp]\n"
                f"(underlying error: {e})",
                err=True,
            )
            sys.exit(1)

    @mcp_group.command("list-tools")
    @click.option(
        "-v",
        "--verbose",
        count=True,
        default=0,
        help="Verbosity: -v names, -vv +descriptions, -vvv full schemas.",
    )
    @click.option(
        "--json", "as_json", is_flag=True, default=False, help="Output as JSON."
    )
    def mcp_list_tools_cmd(verbose, as_json):
        """Enumerate the MCP tools registered by scitex_msword.mcp_server.

        \b
        Example:
            $ scitex-msword mcp list-tools
            $ scitex-msword mcp list-tools --json
        """
        del verbose  # reserved for §1a -v/-vv/-vvv ladder
        names = _mcp_tool_names()
        if as_json:
            click.echo(_json.dumps({"tools": names}, indent=2))
            return
        if not names:
            click.echo(
                "scitex-msword MCP — no tools enumerated (install scitex-msword[mcp] "
                "to introspect the live server).",
                err=True,
            )
            return
        click.echo(f"scitex-msword MCP\nTools: {len(names)}\n")
        for n in names:
            click.echo(f"  {n}")


__all__ = ["register"]
