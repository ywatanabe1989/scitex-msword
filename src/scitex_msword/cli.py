#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: src/scitex_msword/cli.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""
Click-based command-line interface for scitex-msword.

This module is the thin orchestrator: it defines the root ``main_group``
plus universal flags (``-V``/``--version``, ``--help-recursive``,
``--json``) and delegates each subcommand group to a focused module
under ``scitex_msword._cli`` so file size stays under the 512-line
policy and each command lives next to the verb it implements.

Canonical subcommands (audit-§1a compliant):

    scitex-msword insert-table       Insert a Word table at a paragraph anchor.
    scitex-msword list-python-apis   Enumerate the public Python API surface.
    scitex-msword mcp start          Start the MCP server (stdio).
    scitex-msword mcp list-tools     Enumerate registered MCP tools.

The CLI is a thin wrapper around the public Python API — every
mutating verb takes ``--path`` (input) and ``--out`` (output) and
never edits in place. Run ``scitex-msword --help-recursive`` for the
full tree.
"""

from __future__ import annotations

import sys
from typing import Optional, Sequence

import click

from . import __version__
from ._cli import _insert_table, _list_apis, _mcp, _skills


# =========================================================================
# Helpers
# =========================================================================


def _print_help_recursive(ctx: click.Context, _param, value):
    """Eager callback for ``--help-recursive`` — dumps help for every subcommand."""
    if not value or ctx.resilient_parsing:
        return
    cmd = ctx.command
    click.echo(cmd.get_help(ctx))

    def walk(group, ancestry):
        if not isinstance(group, click.Group):
            return
        for name in sorted(group.commands):
            sub = group.commands[name]
            sub_ctx = click.Context(sub, info_name=name, parent=ctx)
            click.echo("\n---\n")
            click.echo(f"$ {' '.join(ancestry + [name])} --help\n")
            click.echo(sub.get_help(sub_ctx))
            walk(sub, ancestry + [name])

    walk(cmd, ["scitex-msword"])
    ctx.exit(0)


# =========================================================================
# Root group
# =========================================================================


_ROOT_HELP = f"""scitex-msword (v{__version__}) — MS Word (.docx) reader/writer with
journal-style profiles and Track-Changes-aware edits.

\b
Configuration precedence (highest -> lowest):
  1. Explicit CLI flags
  2. ./pyproject.toml [tool.scitex_msword]
  3. ./config.yaml (project-local)
  4. $SCITEX_MSWORD_CONFIG (path to a YAML file)
  5. ~/.scitex/msword/config.yaml (user-wide)
  6. Built-in defaults

\b
Example:
    $ scitex-msword insert-table --path d.docx --out o.docx \\
        --paragraph-index 17 --rows '[["A","B"],["a","b"]]'
    $ scitex-msword list-python-apis --json
    $ scitex-msword mcp list-tools
"""


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=_ROOT_HELP,
)
@click.version_option(__version__, "-V", "--version", prog_name="scitex-msword")
@click.option(
    "--help-recursive",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_help_recursive,
    help="Show help for the root command and every subcommand.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit machine-readable JSON output where supported.",
)
@click.pass_context
def main_group(ctx, as_json):
    ctx.ensure_object(dict)
    ctx.obj["as_json"] = as_json
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Attach each subcommand group. Importing the submodules above already
# brings the `register` symbols into scope; calling them now wires the
# Click decorators onto `main_group`.
_insert_table.register(main_group)
_list_apis.register(main_group)
_mcp.register(main_group)
_skills.register(main_group)

# §1a: install-shell-completion + print-shell-completion (canonical leaves)
# Provided by the shared scitex-dev helper. If scitex-dev is not installed
# (end-user runtime where it's not pulled in), silently skip — the audit
# itself runs in the dev environment where scitex-dev IS available, so the
# check fires there.
try:
    from scitex_dev._cli._completion import attach_shell_completion

    attach_shell_completion(main_group, prog_name="scitex-msword")
except ImportError:
    pass


# =========================================================================
# Entry point
# =========================================================================


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Top-level entry — returns process exit code (0 on success).

    Wraps Click so callers (and tests) that pass argv lists keep
    working. Click's own ``SystemExit`` semantics are flattened to an
    int return value for the ``__main__`` shim and for
    ``[project.scripts]`` consumption.
    """
    raw = list(sys.argv[1:]) if argv is None else list(argv)
    try:
        main_group.main(args=raw, prog_name="scitex-msword", standalone_mode=False)
        return 0
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        return code
    except click.exceptions.UsageError as e:
        click.echo(f"Error: {e.format_message()}", err=True)
        return 2
    except click.exceptions.Abort:
        click.echo("Aborted.", err=True)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["main", "main_group"]
