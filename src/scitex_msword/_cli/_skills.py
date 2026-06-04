#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: 2026-06-04 12:00:00
# File: src/scitex_msword/_cli/_skills.py
#
# Part of scitex-msword (AGPL-3.0-only). See LICENSE at the repo root.

"""``scitex-msword skills`` — list / get / install this package's skill leaves.

Operates on the package-local ``src/scitex_msword/_skills/scitex-msword/``
tree only. Cross-ecosystem skill aggregation lives in
``scitex-dev skills`` (this group is the sxm-only mirror for audit-§1a
compliance + agent self-discovery).
"""

from __future__ import annotations

import json as _json
import shutil
import sys
from pathlib import Path
from typing import List, Optional

import click


_SKILLS_PACKAGE_NAME = "scitex-msword"


def _skills_dir() -> Path:
    """Return the absolute path to this package's _skills/scitex-msword/ tree."""
    from pathlib import Path as _Path

    return _Path(__file__).resolve().parent.parent / "_skills" / _SKILLS_PACKAGE_NAME


def _skill_leaves() -> List[Path]:
    """Return ``.md`` files in the package's skill tree, sorted alphabetically."""
    d = _skills_dir()
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("*.md") if p.is_file())


def _resolve_leaf(name: str) -> Optional[Path]:
    """Resolve ``name`` (with or without ``.md``) to an absolute leaf path."""
    d = _skills_dir()
    if not d.is_dir():
        return None
    candidate = d / (name if name.endswith(".md") else f"{name}.md")
    if candidate.is_file():
        return candidate
    upper = d / (
        f"{name.upper()}.md" if not name.upper().endswith(".MD") else name.upper()
    )
    if upper.is_file():
        return upper
    return None


def register(main_group: click.Group) -> None:
    """Attach the ``skills`` noun group + its verbs to the top-level CLI group."""

    @main_group.group("skills", invoke_without_command=True)
    @click.pass_context
    def skills_group(ctx):
        """Manage scitex-msword's bundled skill leaves.

        \b
        Example:
            $ scitex-msword skills list
            $ scitex-msword skills get 04_cli-reference
            $ scitex-msword skills install --dest ~/.scitex/dev/skills/scitex-msword/
        """
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @skills_group.command("list")
    @click.option(
        "--json", "as_json", is_flag=True, default=False, help="Output as JSON."
    )
    def skills_list_cmd(as_json):
        """List the skill leaves bundled with scitex-msword.

        \b
        Example:
            $ scitex-msword skills list
            $ scitex-msword skills list --json
        """
        leaves = _skill_leaves()
        names = [p.stem for p in leaves]
        if as_json:
            click.echo(_json.dumps({"package": _SKILLS_PACKAGE_NAME, "skills": names}))
            return
        if not leaves:
            click.echo(f"No skill leaves bundled in {_SKILLS_PACKAGE_NAME}.")
            return
        click.echo(f"{_SKILLS_PACKAGE_NAME} skills ({len(leaves)}):")
        for p in leaves:
            click.echo(f"  {p.stem}")

    @skills_group.command("get")
    @click.argument("name")
    @click.option(
        "--json", "as_json", is_flag=True, default=False, help="Emit as JSON envelope."
    )
    def skills_get_cmd(name, as_json):
        """Print a single skill leaf's content to stdout.

        \b
        Example:
            $ scitex-msword skills get SKILL
            $ scitex-msword skills get 04_cli-reference
            $ scitex-msword skills get 04_cli-reference --json
        """
        leaf = _resolve_leaf(name)
        if leaf is None:
            click.echo(
                f"Skill '{name}' not found in {_SKILLS_PACKAGE_NAME}.",
                err=True,
            )
            sys.exit(1)
        content = leaf.read_text(encoding="utf-8")
        if as_json:
            click.echo(
                _json.dumps(
                    {"package": _SKILLS_PACKAGE_NAME, "name": leaf.stem, "content": content}
                )
            )
        else:
            click.echo(content)

    @skills_group.command("install")
    @click.option(
        "--dest",
        type=click.Path(),
        default=None,
        help=(
            "Target directory. Default: ~/.scitex/dev/skills/scitex-msword/ "
            "(canonical store; peer to other ~/.scitex/<pkg>/skills/ trees)."
        ),
    )
    @click.option(
        "--dry-run", is_flag=True, default=False, help="Preview without copying."
    )
    @click.option(
        "--yes",
        "-y",
        is_flag=True,
        default=False,
        help="Skip confirmation (accepted for §2; install is non-destructive).",
    )
    @click.option(
        "--json", "as_json", is_flag=True, default=False, help="Output as JSON."
    )
    def skills_install_cmd(dest, dry_run, yes, as_json):
        """Install scitex-msword's skill leaves into DEST.

        \b
        Example:
            $ scitex-msword skills install
            $ scitex-msword skills install --dest /tmp/sxm-skills/
            $ scitex-msword skills install --dry-run --json
        """
        del yes  # accepted for §2; install is non-destructive on --dry-run
        leaves = _skill_leaves()
        if dest:
            target_dir = Path(dest)
        else:
            target_dir = (
                Path.home() / ".scitex" / "dev" / "skills" / _SKILLS_PACKAGE_NAME
            )
        if dry_run:
            payload = {
                "dest": str(target_dir),
                "files": [p.name for p in leaves],
            }
            if as_json:
                click.echo(_json.dumps(payload, indent=2))
            else:
                click.echo(
                    f"Would install {len(leaves)} files to {target_dir}/"
                )
                for p in leaves:
                    click.echo(f"  + {p.name}")
            return
        target_dir.mkdir(parents=True, exist_ok=True)
        written: List[Path] = []
        for src_leaf in leaves:
            dst = target_dir / src_leaf.name
            shutil.copy2(src_leaf, dst)
            written.append(dst)
        if as_json:
            click.echo(
                _json.dumps(
                    {"dest": str(target_dir), "written": [str(p) for p in written]},
                    indent=2,
                )
            )
        else:
            click.echo(f"Installed {len(written)} files at {target_dir}/")
            for p in written:
                click.echo(f"  + {p.name}")


__all__ = ["register"]
